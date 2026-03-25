import os
import time
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
from Bio import Entrez

from helper_functions import *

ARXIV_API_URL = "https://export.arxiv.org/api/query"
MAYO_SEARCH_URL = "https://www.mayoclinic.org/search/search-results"


def _normalize_queries(query_list):
    """Flatten and normalize incoming query values to a clean list of strings."""
    normalized = []

    if isinstance(query_list, str):
        query_list = [query_list]

    for item in query_list or []:
        if isinstance(item, list):
            for sub_item in item:
                normalized.extend(_normalize_queries([sub_item]))
            continue

        query = str(item).strip()
        if not query:
            continue

        for line in query.split("\n"):
            cleaned_line = line.strip()
            if cleaned_line:
                normalized.append(cleaned_line)

    # Keep order while deduplicating.
    seen = set()
    deduped = []
    for query in normalized:
        if query not in seen:
            deduped.append(query)
            seen.add(query)
    return deduped


def _collect_pubmed_articles(query_list, max_results=10):
    """Collect PubMed articles and keep native PubMed payloads."""
    Entrez.email = os.getenv("ENTREZ_EMAIL")
    collected = []
    seen_pmids = set()

    for query in query_list:
        try:
            search_results = exponential_backoff(
                Entrez.esearch,
                db="pubmed",
                term=query,
                retmax=max_results,
                sort="relevance",
            )
            if not search_results:
                continue

            retrieved_ids = Entrez.read(search_results).get("IdList", [])
            if not retrieved_ids:
                continue

            articles = exponential_backoff(
                Entrez.efetch,
                db="pubmed",
                id=retrieved_ids,
                rettype="xml",
            )
            if not articles:
                continue

            article_group = Entrez.read(articles).get("PubmedArticle", [])
            for article in article_group:
                pmid = str(article.get("MedlineCitation", {}).get("PMID", "")).strip()
                if pmid and pmid not in seen_pmids:
                    collected.append(article)
                    seen_pmids.add(pmid)
        except Exception as e:
            print(f"[PubMed] Error collecting query '{query}': {str(e)}")
            continue

    return collected


def _get_atom_text(entry, tag_name):
    namespace = "{http://www.w3.org/2005/Atom}"
    element = entry.find(f"{namespace}{tag_name}")
    return element.text.strip() if element is not None and element.text else ""


def _collect_arxiv_articles(query_list, max_results=10):
    """Collect arXiv entries via arXiv Atom API."""
    headers = {"User-Agent": "CureNerd/1.0 (+https://github.com)"}
    collected = []
    seen_ids = set()

    for query in query_list:
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            response = requests.get(ARXIV_API_URL, params=params, headers=headers, timeout=20)
            response.raise_for_status()

            root = ET.fromstring(response.text)
            atom_ns = "{http://www.w3.org/2005/Atom}"
            entries = root.findall(f"{atom_ns}entry")

            for entry in entries:
                article_id = _get_atom_text(entry, "id")
                title = clean_text(_get_atom_text(entry, "title"))
                summary = clean_text(_get_atom_text(entry, "summary"))
                published = _get_atom_text(entry, "published")

                author_names = []
                for author in entry.findall(f"{atom_ns}author"):
                    name = author.find(f"{atom_ns}name")
                    if name is not None and name.text:
                        author_names.append(name.text.strip())

                dedupe_key = article_id or title.lower()
                if not dedupe_key or dedupe_key in seen_ids:
                    continue

                collected.append(
                    {
                        "source": "arXiv",
                        "title": title,
                        "abstract": summary,
                        "summary": summary,
                        "author_name": ", ".join(author_names),
                        "url": article_id,
                        "id": article_id,
                        "date": published,
                        "journal": "arXiv",
                    }
                )
                seen_ids.add(dedupe_key)
        except Exception as e:
            print(f"[arXiv] Error collecting query '{query}': {str(e)}")
            continue

        # arXiv asks clients to avoid rapid request bursts.
        time.sleep(3)

    return collected


def _extract_mayo_candidates(search_html, max_results=10):
    """Parse Mayo search HTML and return normalized result dictionaries."""
    soup = BeautifulSoup(search_html, "html.parser")
    results = []
    seen_urls = set()

    allowed_sections = (
        "/diseases-conditions/",
        "/drugs-supplements/",
        "/tests-procedures/",
        "/healthy-lifestyle/",
        "/symptoms-causes/",
        "/diagnosis-treatment/",
        "/in-depth/",
    )

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        title = clean_text(anchor.get_text(" ", strip=True))
        if not href or not title:
            continue

        if href.startswith("/"):
            href = f"https://www.mayoclinic.org{href}"
        if "mayoclinic.org" not in href:
            continue
        if "/search/search-results" in href:
            continue
        if not any(section in href for section in allowed_sections):
            continue

        normalized_url = href.split("?")[0].strip().lower()
        if normalized_url in seen_urls:
            continue

        context_text = clean_text(anchor.parent.get_text(" ", strip=True))
        results.append(
            {
                "source": "Mayo Clinic",
                "title": title,
                "abstract": context_text,
                "summary": context_text,
                "url": href,
                "journal": "Mayo Clinic",
                "id": href,
            }
        )
        seen_urls.add(normalized_url)

        if len(results) >= max_results:
            break

    return results


def _collect_mayo_articles(query_list, max_results=10, page_limit=2):
    """Collect Mayo Clinic health content by scraping search result pages."""
    headers = {"User-Agent": "CureNerd/1.0 (+https://github.com)"}
    collected = []
    seen_urls = set()

    for query in query_list:
        for page in range(1, max(page_limit, 1) + 1):
            try:
                params = {"q": query}
                if page > 1:
                    params["page"] = page

                response = requests.get(MAYO_SEARCH_URL, params=params, headers=headers, timeout=20)
                response.raise_for_status()

                for item in _extract_mayo_candidates(response.text, max_results=max_results):
                    item_url = item.get("url", "").split("?")[0].strip().lower()
                    if item_url and item_url not in seen_urls:
                        collected.append(item)
                        seen_urls.add(item_url)

                # Keep request cadence respectful.
                time.sleep(0.4)
            except Exception as e:
                print(f"[Mayo Clinic] Error collecting query '{query}' page {page}: {str(e)}")
                continue

    return collected


def collect_articles(query_list):
    """
    Fetch and aggregate content from PubMed, arXiv, and Mayo Clinic.
    """
    queries = _normalize_queries(query_list)
    if not queries:
        return []

    max_results_per_source = int(os.getenv("CURENERD_MAX_RESULTS_PER_SOURCE", "5"))
    mayo_pages = int(os.getenv("MAYO_SEARCH_PAGES", "2"))
    max_total = int(os.getenv("ARTICLE_COUNTER", "15"))

    pubmed_articles = _collect_pubmed_articles(queries, max_results=max_results_per_source)
    arxiv_articles = _collect_arxiv_articles(queries, max_results=max_results_per_source)
    mayo_articles = _collect_mayo_articles(
        queries,
        max_results=max_results_per_source,
        page_limit=mayo_pages,
    )

    combined = pubmed_articles + arxiv_articles + mayo_articles
    return combined[:max_total]