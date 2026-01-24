from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional

import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import os
# env = 'ATT81274.env'
env= 'variables.env'
load_dotenv(env)

from generic_prompts import *

# Question to Query
import pandas as pd
import random
import time
import math
import numpy as np

import logging

# Database
import ast
import mysql.connector
from mysql.connector import Error
from scipy import spatial # for calculating vector similarities for search
import json
import itertools
import fitz
import re
import subprocess 
import html

# Information Retrieval
from Bio import Entrez
from Bio.Entrez import efetch, esearch
from metapub import PubMedFetcher
import re
import requests
from bs4 import BeautifulSoup
from openai_prompts import *

# Token Clean-Up
import tiktoken
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Summarizer
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import cycle
import string
from tenacity import retry # Exponential Backoff
# wait_random_exponential stop_after_attempt

# Output Synthesis
import textwrap
MAX_RETRIES = 3            # network / rate-limit retries
BACKOFF_SECS = 2           # exponential back-off base

# Import LLM execution modules
from openai_executions import (
    determine_question_validity_openai, query_generation_openai, get_article_type_openai,
    generate_content_from_pdf_openai, section_match_openai, generate_final_response_openai,
    generate_code_from_content_openai, generate_prompt_from_content_openai, _retryable_openai_call
)
from gemini_executions import (
    determine_question_validity_gemini, query_generation_gemini, get_article_type_gemini,
    generate_content_from_pdf_gemini, section_match_gemini, generate_final_response_gemini,
    generate_code_from_content_gemini, generate_prompt_from_content_gemini, _retryable_gemini_call
)

def get_llm_client():
    """
    Get the appropriate LLM client based on the LLM environment variable.
    Dynamically reads the LLM preference from environment variables.
    """
    # Reload environment variables to get the latest LLM setting
    from dotenv import load_dotenv
    load_dotenv('variables.env', override=True)
    
    # Get the current LLM preference from environment
    llm_preference = os.getenv('LLM', 'OpenAI').strip('"')
    
    if llm_preference.lower() == 'gemini':
        return 'gemini'
    else:
        return 'openai'

"""# Step1. Evaluate Question Validity
We do not answer questions related to meal-planning or recipe creation.
* This filter will return `FALSE` if it is not a valid question, in other words, it is a meal-planning/recipe creation question.
* This filter will return `TRUE` if it is a valid question that we will answer.
"""

def determine_question_validity(query):
    """
    Determines if the user's question is one that we can answer.

    Parameters:
    - query (str): The user's question.

    Returns:
    - question_validity (str): "True", "False - Recipe", or "False - Animal".
    """
    llm_client = get_llm_client()
    
    if llm_client == 'openai':
        return determine_question_validity_openai(query, DETERMINE_QUESTION_VALIDITY_PROMPT)
    else:
        return determine_question_validity_gemini(query, DETERMINE_QUESTION_VALIDITY_PROMPT)


"""# If Valid Question

## Step2. Query Generation
"""


def query_generation(query):
    """
    Generates a total of 5 PubMed queries that are aggregated together into a list:
    - 1 query built directly from the user's question that is meant to retrieve articles that provide general context
    - 4 queries to represent the top points of contention around the topic and retrieve articles that may provide more clarity

    Parameters:
    - query (str): The user's question.

    Returns:
    - general_query (str): The broad query that will retrieve articles related to a specific topic.
    - query_contention (str): A list of 4 queries to represent the top points of contention around the topic.
    - query_list (list): A list of all 5 queries generated.
    """
    llm_client = get_llm_client()
    
    # Check if query contention is enabled
    from openai_prompts import QUERY_CONTENTION_ENABLED
    
    if llm_client == 'openai':
        general_query, query_contention = query_generation_openai(query, GENERAL_QUERY_PROMPT, QUERY_CONTENTION_PROMPT, QUERY_CONTENTION_ENABLED)
    else:
        general_query, query_contention = query_generation_gemini(query, GENERAL_QUERY_PROMPT, QUERY_CONTENTION_PROMPT, QUERY_CONTENTION_ENABLED)

    if QUERY_CONTENTION_ENABLED:
        #### AGGREGATE ALL 5 QUERIES
        pattern = r"Query: (.*)"
        matches = re.findall(pattern, query_contention)
        query_list = matches + [general_query]
    else:
        # Skip contention queries when disabled
        query_contention = "Query contention disabled"
        query_list = [general_query]

    return general_query, query_contention, query_list


"""## Step3. Information Retrieval"""

def exponential_backoff(func, *args, **kwargs):
        retries = 5
        wait = 1 

        for i in range(retries):
            try:
                result = func(*args, **kwargs)
                if result:
                    return result
            except Exception as e:
                print(f"Attempt {i+1} failed: {str(e)}")
                time.sleep(wait)
                wait *= 2 ** i + (random.uniform(0, 1) * 0.1) 
        return None

# _retryable_openai_call moved to openai_executions.py

# --------------------------------------------------------------------------- #
# 1. helper
# --------------------------------------------------------------------------- #
def _flatten_authors(raw) -> str:
    """
    Accepts str · list[str] · list[dict] · dict  → returns a comma-separated
    author string or "".
    """
    if not raw:
        return ""

    # single string
    if isinstance(raw, str):
        return raw.strip()

    # single dict  ➜ wrap in list and recurse
    if isinstance(raw, dict):
        return _flatten_authors([raw])

    # list case
    if isinstance(raw, list):
        names = []
        for item in raw:
            if isinstance(item, str):
                names.append(item.strip())
            elif isinstance(item, dict):
                # grab the first plausible name-ish key
                for key in ("name", "full_name", "fullname", "author", "given", "family"):
                    if item.get(key):
                        names.append(str(item[key]).strip())
                        break
            else:
                # fallback – stringify whatever it is
                names.append(str(item).strip())
        return ", ".join([n for n in names if n])   # strip empties

    # anything else – stringify
    return str(raw).strip()


def _safe_json_loads(raw: str) -> Dict[str, Any]:
    """
    Attempts to parse a JSON string that may be wrapped in ``` fences,
    contain trailing commas, or be otherwise slightly malformed.
    Returns {} on failure.
    """
    if not raw:
        return {}

    # remove markdown fences and language hints
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw, flags=re.IGNORECASE).strip()

    # remove common trailing commas (very permissive)
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.warning("[safe_json_loads] JSON decode failed; returning empty dict.")
        return {}


def _coerce_to_str(val: Any, default: str = "") -> str:
    """Return `val` as str if truthy, else default."""
    return str(val).strip() if val else default


def _ensure_fields(d: Dict[str, Any], reference: Dict[str, Any]) -> Dict[str, Any]:
    """Guarantees all keys from `reference` exist in d, filling missing with blank / None."""
    return {k: d.get(k, v) for k, v in reference.items()}


# ---------- 2. canonical defaults -------------------------------------------- #


DEFAULT_ARTICLE: Dict[str, Any] = {
    "title": "",
    "publication_type": "",
    "url": "",
    "abstract": "",
    "citations": "",
    "author_name": "",
    "summary": "",
    "is_relevant": True,
    "id": "",
    "doi": "",
    "date": "",
    "journal": "",
}

# --------------------------------------------------------------------------- #
# 3.  Low-level helpers                                                       #
# --------------------------------------------------------------------------- #
# _retryable_openai_call moved to openai_executions.py


def _safe_json_loads(raw: str) -> Dict[str, Any]:
    """Parse possibly-malformed JSON; return {} on failure."""
    if not raw:
        return {}
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw, flags=re.I).strip()
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)  # rm trailing commas
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logging.warning("[safe_json_loads] JSON decode failed.")
        return {}


def _coerce_to_str(val: Any, default: str = "") -> str:
    """Return a stripped string or default."""
    return str(val).strip() if val else default


def _ensure_fields(d: Dict[str, Any],
                   reference: Dict[str, Any]) -> Dict[str, Any]:
    """Guarantee all keys from reference exist in d."""
    return {k: d.get(k, v) for k, v in reference.items()}


def _flatten_authors(raw: Any) -> str:
    """Robustly flatten author data into a comma-separated string."""
    if not raw:
        return ""
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        return _flatten_authors([raw])
    if isinstance(raw, list):
        names = []
        for item in raw:
            if isinstance(item, str):
                names.append(item.strip())
            elif isinstance(item, dict):
                for key in ("name", "full_name", "fullname",
                            "author", "given", "family"):
                    if item.get(key):
                        names.append(str(item[key]).strip())
                        break
            else:
                names.append(str(item).strip())
        return ", ".join(filter(None, names))
    return str(raw).strip()

# --------------------------------------------------------------------------- #
# 4.  Main orchestrator                                                       #
# --------------------------------------------------------------------------- #
def organize_database_articles(article: Any, user_query: str) -> Dict[str, Any]:
    """
    Extract & normalise metadata from an arbitrary article payload while never
    crashing.  Returns the full DEFAULT_ARTICLE schema with all non-bool fields
    stringified.
    """
    # 4.1  stringify the incoming payload ------------------------------------ #
    try:
        article_str = json.dumps(article, indent=2) if isinstance(article, dict) else str(article)
    except Exception:
        article_str = str(article) if article else ""
    if not article_str:
        logging.error("[organize] Empty article payload.")
        return DEFAULT_ARTICLE.copy()

    # 4.2  initial metadata extraction via LLM ------------------------------- #
    extraction_prompt = (
        "You are a strict JSON extractor for scientific records.\n"
        'Return ONLY a JSON object with keys: title, authors, abstract, journal, '
        'id, doi, url, date. Leave unknown fields null.'
    )
    llm_client = get_llm_client()
    if llm_client == 'openai':
        extraction_raw = _retryable_openai_call(
            messages=[
                {"role": "system", "content": extraction_prompt},
                {"role": "user",   "content": article_str},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
    else:
        # For Gemini, we need to use a different approach since it doesn't support JSON response format
        extraction_raw = _retryable_gemini_call(
            prompt=f"{extraction_prompt}\n\nArticle: {article_str}",
            temperature=0.1
        )
    meta = _safe_json_loads(extraction_raw)

    # 4.3  populate base record --------------------------------------------- #
    article_data = DEFAULT_ARTICLE.copy()
    article_data.update({
        "title":       _coerce_to_str(meta.get("title")),
        "author_name": _flatten_authors(meta.get("authors")),
        "abstract":    _coerce_to_str(meta.get("abstract")),
        "journal":     _coerce_to_str(meta.get("journal")),
        "id":          _coerce_to_str(meta.get("id")),
        "doi":         _coerce_to_str(meta.get("doi")),
        "url":         _coerce_to_str(meta.get("url")),
        "date":        _coerce_to_str(meta.get("date")),
    })

    # 4.4  classify publication type ---------------------------------------- #
    pub_type_prompt = (
        "Classify the text as either 'review' or 'study'. "
        "Respond with exactly one lowercase word: review / study."
    )
    if llm_client == 'openai':
        pub_type_raw = _retryable_openai_call(
            messages=[
                {"role": "system", "content": pub_type_prompt},
                {"role": "user",   "content": article_str},
            ],
            temperature=0.0,
        ).strip().lower()
    else:
        pub_type_raw = _retryable_gemini_call(
            prompt=f"{pub_type_prompt}\n\nArticle: {article_str}",
            temperature=0.0
        ).strip().lower()
    if pub_type_raw in {"review", "study"}:
        article_data["publication_type"] = pub_type_raw

    # 4.5  ensure abstract exists ------------------------------------------- #
    if len(article_data["abstract"]) < 40:
        abstract_prompt = (
            "Extract the abstract from the text. If absent, generate a concise "
            "abstract (≤150 words) covering objectives, methods, results, conclusion."
        )
        if llm_client == 'openai':
            article_data["abstract"] = _retryable_openai_call(
                messages=[
                    {"role": "system", "content": abstract_prompt},
                    {"role": "user",   "content": article_str},
                ],
                temperature=0.4,
            )[:4000]
        else:
            article_data["abstract"] = _retryable_gemini_call(
                prompt=f"{abstract_prompt}\n\nArticle: {article_str}",
                temperature=0.4
            )[:4000]

    # 4.6  user-tailored summary -------------------------------------------- #
    summary_prompt = (
        "Provide a 3-5 sentence summary tailored to the user query below. "
        "Emphasise study design & findings if this is a study, or themes if review.\n\n"
        f"User query: {user_query}"
    )
    if llm_client == 'openai':
        article_data["summary"] = _retryable_openai_call(
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user",   "content": article_data['abstract']},
            ],
            temperature=0.5,
        )
    else:
        article_data["summary"] = _retryable_gemini_call(
            prompt=f"{summary_prompt}\n\nAbstract: {article_data['abstract']}",
            temperature=0.5
        )

    # 4.7  fallback title / author extraction -------------------------------- #
    if not article_data["title"]:
        title_prompt = "Generate a concise, descriptive title for the article."
        if llm_client == 'openai':
            article_data["title"] = _retryable_openai_call(
                messages=[
                    {"role": "system", "content": title_prompt},
                    {"role": "user",   "content": article_str[:2000]},
                ],
                temperature=0.6,
            )[:300]
        else:
            article_data["title"] = _retryable_gemini_call(
                prompt=f"{title_prompt}\n\nArticle: {article_str[:2000]}",
                temperature=0.6
            )[:300]

    if not article_data["author_name"]:
        author_prompt = (
            "Extract author names from the text. If none discovered, return ''."
        )
        if llm_client == 'openai':
            article_data["author_name"] = _retryable_openai_call(
                messages=[
                    {"role": "system", "content": author_prompt},
                    {"role": "user",   "content": article_str},
                ],
                temperature=0.2,
            )[:500]
        else:
            article_data["author_name"] = _retryable_gemini_call(
                prompt=f"{author_prompt}\n\nArticle: {article_str}",
                temperature=0.2
            )[:500]

    # 4.8  final sanitation – **string-ify everything** ---------------------- #
    article_data = _ensure_fields(article_data, DEFAULT_ARTICLE)
    for k, v in article_data.items():
        if k != "is_relevant":                 # keep the bool as-is
            article_data[k] = _coerce_to_str(v)

    return article_data

#@title concurrent_organize_database_articles
def concurrent_organize_database_articles(articles, user_query):
    """
    Concurrently processes and classifies articles using multiple threads for improved performance.
    Uses ThreadPoolExecutor to parallelize the classification of articles into relevant and irrelevant categories.

    Parameters:
    - articles (list): List of article dictionaries to be classified
    - user_query (str): The user's search query used for relevance classification

    Returns:
    - all_articles (list): List of organized article dictionaries
    """
    all_articles = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(organize_database_articles, article, user_query) for article in articles]
        for future in as_completed(futures):
            try:
                article = future.result()
                all_articles.append(article)
            except Exception as e:
                print(f"Error processing article: {str(e)}")

    return all_articles

# Step 3.5: Process Reference Articles
def process_articles_by_url(articles):
    ref_articles = []
    for article in articles:
        if article['url'] is None:
            ref_articles.append(article)
        else:
            new_summary = url_to_summary(article['url'])
            new_summary = generate_summary(new_summary)
            ref_article = {
                'title': article.get('title', ''),
                'publication_type': article.get('publication_type', ''),
                'url': article.get('url', ''),
                'abstract': article.get('abstract', ''),
                'citations': article.get('citations', ''),
                'author_name': article.get('author_name', ''),
                'summary': new_summary,
                'is_relevant': article.get('is_relevant', ''),
                'id': article.get('id', ''),
                'doi': article.get('doi', ''),
                'date': article.get('date', ''),
                'journal': article.get('journal', ''),
            }
            ref_articles.append(ref_article)
    return ref_articles

def url_to_summary(url: str):
    result = subprocess.run(
        f'curl -sL "{url}" | lynx -stdin -dump',
        shell=True, capture_output=True, text=True, errors="replace"
    )
    text = result.stdout or ""
    if not text:
        return ""
    return clean_text(text)

# Helper function to clean text
def clean_text(raw) -> str:
    """
    Cleans raw HTML/text with escape sequences into readable plain text.
    Handles:
      - HTML tags (convert <br>, <p>, <li>, headings, etc.)
      - Escape sequences (\n, \t, \\uXXXX, etc.)
      - Removes URLs, reference markers, image tags
      - Cuts off common trailing sections (References, External Links, etc.)
      - Normalizes whitespace
    """
    # Handle non-string inputs by converting to string
    if not isinstance(raw, str):
        if isinstance(raw, (list, dict)):
            # For lists and dicts, convert to JSON string
            try:
                raw = json.dumps(raw, ensure_ascii=False)
            except (TypeError, ValueError):
                raw = str(raw)
        else:
            raw = str(raw)
    
    # Handle empty or None input
    if not raw:
        return ""
    
    # --- 1. Decode escape sequences ---
    try:
        raw = raw.encode("utf-8").decode("unicode_escape", errors="ignore")
    except (UnicodeEncodeError, UnicodeDecodeError):
        # If encoding/decoding fails, use the original string
        pass

    # --- 2. Convert HTML entities (like &amp;) ---
    text = html.unescape(raw)

    # --- 3. Replace key HTML tags with formatting ---
    replacements = {
        r"<br\s*/?>": "\n",
        r"</p>": "\n\n",
        r"<p[^>]*>": "",
        r"<li[^>]*>": "- ",
        r"</li>": "\n",
        r"<h[1-6][^>]*>": "\n# ",   # headings
        r"</h[1-6]>": "\n",
        r"<div[^>]*>": "\n",
        r"</div>": "\n",
        r"<tr[^>]*>": "\n",
        r"</tr>": "\n",
        r"<td[^>]*>": " ",
        r"</td>": " ",
        r"<th[^>]*>": " ",
        r"</th>": " ",
        r"<ul[^>]*>|</ul>|<ol[^>]*>|</ol>": "\n",
        r"<blockquote[^>]*>": "\n> ",
        r"</blockquote>": "\n",
        r"<pre[^>]*>|</pre>": "\n",
        r"<code[^>]*>|</code>": "",
    }
    for pat, repl in replacements.items():
        text = re.sub(pat, repl, text, flags=re.I)

    # --- 4. Remove all remaining HTML tags ---
    text = re.sub(r"<[^>]+>", "", text)

    # --- 5. Cut at common end sections ---
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if re.match(r"^\s*(references?|external links?|see also|gallery|media|further reading|notes)\s*:?\s*$", line, re.I):
            lines = lines[:idx]
            break
    text = "\n".join(lines)

    # --- 6. Remove URLs, ref markers, images, edit links, etc. ---
    text = re.sub(r"https?://\S+|\bwww\.\S+", "", text, flags=re.I)
    text = re.sub(r"\[\s*\d+\s*\]", "", text)  # [1], [2]
    text = re.sub(r"\^\[[^\]]+\]|\^{1,}", "", text)  # ^[note]
    text = re.sub(r"\[(?:edit|[a-z]{2})\]", "", text, flags=re.I)
    text = re.sub(r"\[(?:citation needed|when\?|update)\]", "", text, flags=re.I)
    text = re.sub(r"\[[^\]]+\.(?:jpg|jpeg|png|svg|gif)\]", "", text, flags=re.I)

    # --- 7. Remove lines with iframe/button/nav junk ---
    filtered = []
    for line in text.splitlines():
        s = line.strip()
        if (re.search(r"\b(iframe|button)\b", s, re.I) or
            re.match(r"^\s*\[\s*\d+\s*\]\s+\S+", s) or
            s.lower() in {"[edit]", "edit", "top view", "side view"} or
            s.upper().startswith("CAPTION:") or
            re.match(r"^(main article|see also):", s, re.I) or
            re.match(r"^[*\-]\s+\S+", s)):
            continue
        filtered.append(line)
    text = "\n".join(filtered)

    # --- 8. Normalize whitespace ---
    text = text.replace("\uFFFD", "").replace("�", "")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def generate_summary(text: str):
    summary_prompt = (
        "You are to write a comprehensive and highly descriptive review of the following text, "
        "which was fetched from a web page using curl and may contain some HTML tags or unnecessary words. "
        "Please ignore any HTML tags, formatting artifacts, or irrelevant words that may appear in the text. "
        "Focus on providing a thorough and insightful review: "
        "if the text is a study, discuss the study design, methodology, results, and implications in detail; "
        "if it is a review, elaborate on the main themes, arguments, and perspectives. "
        "Include relevant background, context, and your interpretation, ensuring the review is rich in detail and clarity.\n\n"
        # f"Text: {text}"
    )
    llm_client = get_llm_client()
    if llm_client == 'openai':
        summary = _retryable_openai_call(
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user",   "content": text},
            ],
            temperature=0.5,
        )
    else:
        summary = _retryable_gemini_call(
            prompt=f"{summary_prompt}\n\nText: {text}",
            temperature=0.5
        )

    return summary

def relevance_classifier(article: Dict[str, Any], user_query: str) -> tuple[str, bool, Dict[str, Any]]:
    """
    Classifies a processed article as relevant or irrelevant based on its abstract.
    
    An article is considered relevant if:
    - It contains information that is helpful in answering the question.
    - It contains a safety aspect that would be important to include in the answer.
    - It is NOT an animal-based study.

    Parameters:
    - article (dict): A dictionary containing the fetched PubMed article data.
    - user_query (str): The user's original query.

    Returns:
    - pmid (str): PubMed ID of the article.
    - article_is_relevant (bool): Whether the article is relevant or not (True/False).
    - article (dict): The input article dictionary.
    """
    # 1. Safely get the ID, falling back to a default
    article_id = _coerce_to_str(article.get("id") or article.get("ID"), "Unknown ID")

    # 2. Safely get the abstract, with fallbacks to summary and title
    content_for_relevance = _coerce_to_str(article.get("abstract"))
    if not content_for_relevance or len(content_for_relevance) < 20:
        content_for_relevance = _coerce_to_str(article.get("summary"))
    if not content_for_relevance or len(content_for_relevance) < 20:
        content_for_relevance = _coerce_to_str(article.get("title"))
    if not content_for_relevance:
        content_for_relevance = "No content available."

    # 3. Classify relevance using the retryable OpenAI wrapper
    relevance_prompt = (
        "Based on the provided text, is this article relevant to the user's question? "
        "Consider that animal studies are NOT relevant. "
        "Answer with a single word: yes or no."
    )
    
    llm_client = get_llm_client()
    if llm_client == 'openai':
        relevance_raw = _retryable_openai_call(
            messages=[
                {"role": "system", "content": RELEVANCE_CLASSIFIER_PROMPT},
                {"role": "user",   "content": f"Question: {user_query}\n\nArticle Content: {content_for_relevance}"},
            ],
            temperature=0.1
        )
    else:
        relevance_raw = _retryable_gemini_call(
            prompt=f"{RELEVANCE_CLASSIFIER_PROMPT}\n\nQuestion: {user_query}\n\nArticle Content: {content_for_relevance}",
            temperature=0.1
        )

    # 4. Parse the response
    first_word = relevance_raw.split()[0].strip(string.punctuation).lower() if relevance_raw else ""
    article_is_relevant = first_word not in {"no", "n"}

    return article_id, article_is_relevant, article

#@title concurrent_relevance_classification
def concurrent_relevance_classification(articles, user_query):
  """
  Concurrent classification of articles as relevant or irrelevant using the relevance_classifier function.

  Parameters:
  - articles (list): A list of article dictionaries to classify.

  Returns:
  - relevant_articles (list): A list of dictionaries of relevant articles.
  - irrelevant_articles (list): A list of dictionaries of irrelevant articles.
  """
  relevant_articles = []
  irrelevant_articles = []
  print("Arctile classification")
  with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(relevance_classifier, article_tmp, user_query) for article_tmp in articles]
        for future in as_completed(futures):
            try:
                result = future.result()
                # Bucket articles as relevant vs irrelevant
                if result[1]:
                    relevant_articles.append(result[2])
                else:
                    irrelevant_articles.append(result[2])
            except Exception as e:
                print("Error processing article:", e)

  return relevant_articles, irrelevant_articles

"""## Step4. Research Processing
* Summarization
* Relevance Ranking
* Reliability Assessment

### RAG - Reliability Analysis Match

#### MySQL Connection
"""



"""#### Article Matching
* If there is an article match, store it into a list.
* If there is no match, process article and store it into relevant_articles list. Write it to MySQL database.
"""

#@title clean_extracted_text
def clean_extracted_text(text):
    """
    Cleans the extracted text to improve readability by removing unicode, markdown, and ASCII characters.

    Parameters:
    - text (str): The extracted text from the PDF.

    Returns:
    - cleaned_text (str): Cleaned up version of the extracted text.
    """
    # Replace newline characters with spaces
    cleaned_text = text.replace('\n', ' ')

    # Remove any strange unicode characters (like \u202f, \u2002, \xa0)
    cleaned_text = re.sub(r'[\u202f\u2002\xa0]', ' ', cleaned_text)

    # Fix hyphenated words at the end of lines
    cleaned_text = re.sub(r'-\s+', '', cleaned_text)

    # Replace multiple spaces with a single space
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    # Strip leading/trailing whitespace
    cleaned_text = cleaned_text.strip()

    return cleaned_text

#@title get_article_type
def get_article_type(abstract):
    """
    Determines whether an article is a study or a review.

    - If it is a study (e.g., observational study, randomized controlled trial), return "study".
    - If it is a review (e.g., literature review, systematic review, meta-analysis), return "review".

    Parameters:
    - abstract (str): The abstract of the article.

    Returns:
    - article_type (str): Either "study" or "review".
    """
    llm_client = get_llm_client()
    
    if llm_client == 'openai':
        return get_article_type_openai(abstract, ARTICLE_TYPE_PROMPT)
    else:
        return get_article_type_gemini(abstract, ARTICLE_TYPE_PROMPT)



def generate_content_from_pdf(pdf_text, content_type="abstract", publication_type="study"):
    """
    Extracts structured summaries from a research paper PDF.

    - If `content_type` is "abstract", extracts structured abstract details.
    - If `content_type` is "summary":
        - Uses a different summarization prompt based on whether the article is a study or a review.

    Parameters:
    - pdf_text (str): The full text extracted from a research paper PDF.
    - content_type (str): Either "abstract" or "summary".
    - publication_type (str): Either "study" or "review".

    Returns:
    - summary (str): A structured summary of the research paper.
    """
    llm_client = get_llm_client()
    
    if llm_client == 'openai':
        return generate_content_from_pdf_openai(pdf_text, content_type, publication_type, 
                                              ABSTRACT_EXTRACTION_PROMPT, REVIEW_SUMMARY_PROMPT, STUDY_SUMMARY_PROMPT)
    else:
        return generate_content_from_pdf_gemini(pdf_text, content_type, publication_type, 
                                              ABSTRACT_EXTRACTION_PROMPT, REVIEW_SUMMARY_PROMPT, STUDY_SUMMARY_PROMPT)


def process_pdf_article(file_info, pdf_counter):
    """
    Process a single PDF article and extract relevant data.

    Args:
        file_info (dict): File metadata and content.
        pdf_counter (int): Counter for naming articles.

    Returns:
        dict: Formatted article extracted from the PDF.
    """
    file_data = file_info['content']
    file_name = file_info['filename']
    content_type = file_info['content_type']

    if content_type not in ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        print(f"Skipping file {file_name}: unsupported content type {content_type}")
        return None

    pdf_text = ""
    metadata = {}

    if content_type == 'application/pdf':
        pdf_document = fitz.open(stream=file_data, filetype="pdf")
        for page in pdf_document:
            page_text = page.get_text()
            page_text = page_text.replace('\n', ' ')
            pdf_text += page_text + " "
        metadata = pdf_document.metadata
    elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        # TODO: Implement DOCX processing
        metadata = {}

    title = metadata.get('title', f'Upload PDF {pdf_counter}')
    if not title or title.strip() == '':
        title = f'Upload PDF {pdf_counter}'

    publication_type = get_article_type(pdf_text)
    abstract = generate_content_from_pdf(pdf_text, content_type="abstract")
    summary = generate_content_from_pdf(pdf_text, content_type="summary", publication_type=publication_type)
    # citation = generate_pdf_ama_citation(metadata, pdf_counter)  # TODO: Implement this function
    citation = f"PDF {pdf_counter}"  # Placeholder

    return {
        'title': title,
        'publication_type': publication_type,
        'url': 'nil',
        'abstract': abstract,
        'is_relevant': True,
        'citation': citation,
        'ID': None,
        'full_text': True,
        'summary': summary
    }


def section_match(list_of_strings, required_titles):
    """
    Capture only the most relevant sections from an article's full text to be cognizant of token size and context windows.
    Does a case-sensitive check to see which of the section titles provided of a given article best match the required section titles.
    This function is only used if the article's full text is available directly in PubMed.

    Parameters:
    - list_of_strings (list): A list of all of an article's section titles to search through.
    - required_titles (list): A list of titles that are deemed to be the most relevant and helpful to include.

    Returns:
    - sections_to_pull (list): A list of matched section titles.
    """
    # Convert all strings in the list to lowercase and keep original strings in a dictionary for lookup
    lower_to_original = {title.lower(): title for title in list_of_strings}

    # Check if all required titles are present (case-insensitively) in the list
    all_titles_present = all(title.lower() in lower_to_original for title in required_titles)

    if all_titles_present:
        # If all required titles are present, collect the matched titles from the list
        sections_to_pull = [lower_to_original[title.lower()] for title in required_titles if title.lower() in lower_to_original]
        return sections_to_pull
    else:
        ### Identify the most important columns
        list_of_strings_str = ', '.join(list_of_strings)

        llm_client = get_llm_client()
        
        if llm_client == 'openai':
            relevant_sections = section_match_openai(list_of_strings, RELEVANT_SECTIONS_PROMPT)
        else:
            relevant_sections = section_match_gemini(list_of_strings, RELEVANT_SECTIONS_PROMPT)

        # Split the text into lines
        lines = relevant_sections.split('\n')

        # Create a list to hold distinct values
        sections_to_pull = []

        # Iterate over each line
        for line in lines:
            # Check if line contains ':'
            if ':' in line:
                # Split the line at ':' and strip whitespace from the result
                value = line.split(':', 1)[1].strip()
                # Process and add the values
                # Split the value by '|' and strip whitespace
                split_values = [val.strip() for val in value.split('|')]
                # Add each trimmed value to the set of distinct values
                for val in split_values:
                    if val not in sections_to_pull:
                        sections_to_pull.append(val)

        return sections_to_pull


# #@title process_article
# def process_article(article):
#   """
#   Create the article JSON that includes the following information:
#   - title
#   - publication_type
#   - url
#   - abstract
#   - is_relevant
#   - citation
#   - PMID
#   - PMCID
#   - full_text
#   - reliability analysis

#   Full-text article will be pulled in if it is available via PubMed, Elsevier, Springer, JAMA, and Wiley. Otherwise, the abstract is used.
#   The reliability analysis pulls various attributes from the paper that can be used to deduce the strength of the article's claim.
#   This is the helper function for ThreadPoolExecutor.

#   Parameters:
#   - article (dict): A dictionary containing the article data.

#   Returns:
#   - article_json (dict): A dictionary containing the article information.
#   """

#   try:
#     ### Retrieve the abstract ###
#     abstract = article["MedlineCitation"]["Article"]["Abstract"]["AbstractText"]


#     ### Clean-Up Abstract ###
#     reconstructed_abstract = ""
#     for element in abstract:
#         label = element.attributes.get("Label", "")
#         if reconstructed_abstract:
#           reconstructed_abstract += "\n\n"
#         if label:
#           reconstructed_abstract += f"{label}:\n"
#         reconstructed_abstract += str(element)

#     ### Citation ###
#     citation = generate_ama_citation(article)


#     ### Article JSON ###
#     title = article["MedlineCitation"]["Article"]["ArticleTitle"]
#     url = (f"https://pubmed.ncbi.nlm.nih.gov/"
#               f"{article['MedlineCitation']['PMID']}/")

#     types_html = article['MedlineCitation']['Article']['PublicationTypeList']
#     publication_types = []
#     for pub_type in types_html:
#       publication_types.append(str(pub_type))

#     pmc_id = next((element for element in article['PubmedData']['ArticleIdList'] if element.attributes.get('IdType') == 'pmc'), None)

#     article_json =  {
#                       "title": title,
#                       "publication_type": publication_types,
#                       "url": url,
#                       "abstract": reconstructed_abstract,
#                       "is_relevant": True,
#                       "citation": citation,
#                       "PMID": str(article['MedlineCitation']['PMID']),
#                       "PMCID": str(pmc_id)
#                     }

#     preferred_link = get_preferred_link(article_json['url'])

#     ### Bring in Full Text, if PMC text Available ###
#         ### Bring in Full Text, if PMC text Available ###
#     if (article_json['PMCID'] != None) & (article_json['PMCID'] != "None"):
#       article_content = get_full_text_pubmed(article_json)
#       article_json["full_text"] = True
#     elif preferred_link and "elsevier" in preferred_link:
#       pii = extract_pii(preferred_link)
#       article_data_json = get_full_text_elsevier(pii)
#       if 'full-text-retrieval-response' in article_data_json and 'coredata' in article_data_json['full-text-retrieval-response']:
#         if (article_data_json['full-text-retrieval-response']['coredata']['openaccess'] == 1) | (article_data_json['full-text-retrieval-response']['coredata']['openaccess'] == '1'):
#           article_content = clean_extracted_text(str(article_data_json['full-text-retrieval-response']['originalText']))
#           article_json["full_text"] = True
#         else:
#           article_content = article_json['abstract']
#           article_json["full_text"] = False
#       else:
#         article_content = article_json['abstract'] 
#         article_json["full_text"] = False
#     elif preferred_link and "springer" in preferred_link:
#       try:
#         article_content = clean_extracted_text(str(get_full_text_springer(preferred_link)))
#         article_json["full_text"] = True
#       except:
#         article_content = article_json['abstract']
#     elif preferred_link and "jamanetwork" in preferred_link:
#       try:
#         article_content = clean_extracted_text(str(get_full_text_jama(preferred_link)))
#         article_json["full_text"] = True
#       except:
#         article_content = article_json['abstract']
#     elif preferred_link and "wiley" in preferred_link:
#       try:
#         article_content = clean_extracted_text(str(get_full_text_wiley(preferred_link)))
#         article_json["full_text"] = True
#       except:
#         article_content = article_json['abstract']
#     else:
#       article_content = article_json['abstract']
#       article_json["full_text"] = False

#     if len(article_content) > 1048576:
#       article_content = article_content[:1044000]

#     ### Summarize only the relevant articles and assess strength of work ###
#     study_types = set(['Adaptive Clinical Trial',
#                     'Case Reports',
#                     'Clinical Study',
#                     'Clinical Trial',
#                     'Clinical Trial Protocol',
#                     'Clinical Trial, Phase I',
#                     'Clinical Trial, Phase II',
#                     'Clinical Trial, Phase III',
#                     'Clinical Trial, Phase IV',
#                     'Clinical Trial, Veterinary',
#                     'Comparative Study',
#                     'Controlled Clinical Trial',
#                     'Equivalence Trial',
#                     'Evaluation Study',
#                     # 'Journal Article',
#                     'Multicenter Study',
#                     'Observational Study',
#                     'Observational Study, Veterinary',
#                     'Pragmatic Clinical Trial',
#                     'Preprint',
#                     'Published Erratum',
#                     'Randomized Controlled Trial',
#                     'Randomized Controlled Trial, Veterinary',
#                     'Technical Report',
#                     'Twin Study',
#                     'Validation Study'])

#     article_type = set(article_json['publication_type'])

#     if article_type.isdisjoint(study_types):
#       # review type paper
#       system_prompt_summarize = REVIEW_SUMMARY_PROMPT
#     else:
#       # study type paper
#       system_prompt_summarize = STUDY_SUMMARY_PROMPT

#     reliability_analysis_response = client.chat.completions.create(
#         model="gpt-4-turbo",
#         messages = [
#             {
#                 "role": "system",
#                 "content": system_prompt_summarize
#             },
#             {
#                 "role": "user",
#                 "content": f"Paper: {article_content}"
#             }
#         ],
#         temperature=0.6,
#         top_p=1
#     )

#     # Extract the generated summary
#     answer_summary = reliability_analysis_response.choices[0].message.content
#     article_json["summary"] = answer_summary

#     return article_json
#   except KeyError:
#     print("No abstract provided")
    
# """### Reliability Analysis"""

# #@title process_article_with_retry
# def process_article_with_retry(article):
#   """
#   Include a retry decorator and buffer for the article processing function.

#   Parameters:
#   - article (dict): A dictionary containing the article data.

#   Returns:
#   - article_json (dict): A dictionary containing the article information.
#   """
#   try:
#       return process_article(article)
#   except Exception as e:
#       print("Error processing article:", e, "- waiting 10 secs")
#       time.sleep(10)
#       print("Trying again")
#       return process_article(article)


# def concurrent_article_processing(articles_to_process):
#   """
#   Concurrent article processing using ThreadPoolExecutor.

#   Parameters:
#   - articles_to_process (list): A list of articles to process.

#   Returns:
#   - relevant_article_summaries (list): A list of relevant article summaries.
#   """
#   relevant_article_summaries = []

#   with ThreadPoolExecutor(max_workers=8) as executor:
#       futures = [executor.submit(process_article_with_retry, article) for article in articles_to_process]
#       for future in as_completed(futures):
#           try:
#               result = future.result()
#               relevant_article_summaries.append(result)
#               print(result)
#               print('-----------------------------------------------------------')
#           except Exception as e:
#               print("Error processing article:", e)
#   return relevant_article_summaries


def calculate_token_count(text: str, model: str = "gpt-4-turbo") -> int:
    """Calculate the number of tokens in a text string."""
    encoder = tiktoken.encoding_for_model(model)
    return len(encoder.encode(text))

def calculate_relevance_score(text: str, query: str, vectorizer) -> float:
    """Calculate relevance score using TF-IDF and cosine similarity."""
    vectors = vectorizer.transform([text, query])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])
    return float(similarity[0][0])

#Interim function to trim the list of relevant articles to fit within the token limit based on relevance to the user query.
def trim_relevant_articles_by_token_limit(all_relevant_articles, user_query, max_tokens: int = 100000):
    """
    Trim the list of relevant articles to fit within the token limit based on relevance to the user query.
    """
    # Convert articles to string for token counting
    article_strings = [json.dumps(article) for article in all_relevant_articles]
    
    # Initial token count with just the user query
    current_tokens = calculate_token_count(user_query)

    # Check total token count if we include everything
    total_tokens = calculate_token_count(" ".join(article_strings) + user_query)
    if total_tokens <= max_tokens:
        return all_relevant_articles

    # Fit TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    vectorizer.fit(article_strings + [user_query])
    
    # Score articles by relevance to user query
    article_scores = [
        (article, calculate_relevance_score(json.dumps(article), user_query, vectorizer))
        for article in all_relevant_articles
    ]

    # Sort articles by score (most relevant first)
    article_scores.sort(key=lambda x: x[1], reverse=True)

    # Select articles while staying within token limit
    selected_articles = []
    for article, score in article_scores:
        article_token_count = calculate_token_count(json.dumps(article))
        if current_tokens + article_token_count <= max_tokens:
            selected_articles.append(article)
            current_tokens += article_token_count
        else:
            break

    return selected_articles

"""## Step5. Final Output"""

def generate_final_response(all_relevant_articles, query):
    """
    Generate the final response to the user's question based on the strongest level of evidence in the provided article summaries.

    Parameters:
    - all_relevant_articles (list): List of all relevant article summaries.
    - query (str): User's question.

    Returns:
    - final_output (str): Final response to the user question.
    """
    llm_client = get_llm_client()
    
    if llm_client == 'openai':
        return generate_final_response_openai(all_relevant_articles, query, FINAL_RESPONSE_PROMPT, DISCLAIMER_TEXT)
    else:
        return generate_final_response_gemini(all_relevant_articles, query, FINAL_RESPONSE_PROMPT, DISCLAIMER_TEXT)


"""### Write Final Output to Database"""

def clean_citation(citation: str):
  """
  Removes the citation number from the citation.

  Parameters:
    - citation (str): The citation to be cleaned.

  Returns:
    - cleaned_citation (str): The cleaned citation.
  """
  # Remove the citation number (e.g., [1]) from the citation
  cleaned_citation = re.sub(r'^\[\d+\]\s*', '', str(citation)).strip()
  return cleaned_citation

def parse_str(input_string: str) -> str:
  """
  Clean string by removing double periods and unnecessary semicolons and parentheses.

  Parameters:
    - input_string (str): The input string to be cleaned.

  Returns:
    - cleaned_string (str): The cleaned string.
  """
  # Replace double periods with a single period
  cleaned_string = input_string.replace("..", ".")

  # Remove unnecessary semicolons and empty parentheses
  cleaned_string = re.sub(r';\s*', ' ', cleaned_string)
  cleaned_string = re.sub(r'\(\s*\)', '', cleaned_string)

  # Remove extra spaces that may result from the above replacements
  cleaned_string = re.sub(r'\s+', ' ', cleaned_string).strip()
  return cleaned_string


def normalize_title(title):
    """
    Normalize titles for comparison by handling all types of quotes and formatting issues
    
    Args:
        title (str): The title to normalize
        
    Returns:
        str: Normalized title
    """
    if not title:
        return ""
    
    # Remove HTML entities
    title = html.unescape(title)
    
    # Remove various types of quotes from beginning and end
    # Handle: "", '', "", '', ‚‛, „‟, etc.
    quote_chars = ['"', "'", '"', '"', ''', ''', '‚', '‛', '„', '‟', '«', '»', '‹', '›']
    
    # Strip whitespace first
    title = title.strip()
    
    # Remove quotes from beginning and end repeatedly until no more quotes
    changed = True
    while changed:
        changed = False
        original_title = title
        
        # Remove quotes from start and end
        for quote in quote_chars:
            if title.startswith(quote):
                title = title[len(quote):]
                changed = True
            if title.endswith(quote):
                title = title[:-len(quote)]
                changed = True
        
        # Remove escaped quotes
        title = title.replace('\\"', '').replace("\\'", '')
        
        # Strip whitespace after each iteration
        title = title.strip()
        
        # Check if anything changed
        if title == original_title:
            changed = False
    
    # Remove trailing punctuation that might cause mismatches
    title = title.rstrip('.,!?;:')
    
    # Remove extra whitespace
    title = ' '.join(title.split())
    
    return title

def print_referenced_articles(final_output, json_data):
    """
    Extracts references from final_output and returns corresponding JSON objects in order.
    Robust to heading style differences and supports DOI-first matching. Falls back to top articles when no matches.

    Args:
        final_output (str): The formatted output containing references
        json_data (list): List of article JSON objects

    Returns:
        list: List of matched articles with specified fields
    """

    # 1) Find references block (support 'References', 'References:', '### References') and stop at disclaimer
    try:
        header_match = re.search(r"(?im)^(#+\s*)?references\s*:?[\t ]*$", final_output)
        if header_match:
            tail = final_output[header_match.end():]
        else:
            tail = final_output.split("References:", 1)[1] if "References:" in final_output else final_output
        end_match = re.search(r"(?is)\n\s*\*\*Disclaimer:\*\*", tail)
        references_section = tail[: end_match.start()] if end_match else tail
    except Exception:
        references_section = final_output

    # 2) Collect numbered reference lines
    reference_lines = []
    for line in references_section.split('\n'):
        s = line.strip()
        if re.match(r"^\[\d+\]", s):
            reference_lines.append(s)

    if not reference_lines:
        for line in final_output.split('\n'):
            s = line.strip()
            if re.match(r"^\[\d+\]", s):
                reference_lines.append(s)

    matched_articles = []

    # Pre-normalize article fields
    pool = [{
        "article": a,
        "title_norm": normalize_title(a.get("title", "")),
        "doi_norm": (a.get("doi", "") or "").lower().strip(),
    } for a in json_data]

    def extract_title_and_doi(ref: str):
        doi_match = re.search(r"\b10\.\d{4,9}/\S+\b", ref, flags=re.I)
        doi_found = (doi_match.group(0).rstrip('.,);').lower() if doi_match else "")
        q = re.search(r'"([^"]+)"', ref)
        if q:
            return q.group(1).strip(), doi_found
        tmp = re.sub(r"^\[\d+\]\s*", "", ref).strip()
        parts = [p.strip() for p in re.split(r"\.(?:\s+|$)", tmp) if p.strip()]
        title_guess = parts[1] if len(parts) >= 2 else (parts[0] if parts else "")
        title_guess = re.sub(r"\bdoi\s*:\s*\S+", "", title_guess, flags=re.I).strip()
        return title_guess, doi_found

    for ref_line in reference_lines:
        print(f"Processing reference: {ref_line}")
        ref_title, ref_doi = extract_title_and_doi(ref_line)
        norm_ref_title = normalize_title(ref_title)

        found = None
        best = 0.0

        # Prefer DOI match
        if ref_doi:
            for item in pool:
                if item["doi_norm"] and item["doi_norm"] == ref_doi:
                    found = item["article"]
                    best = 100.0
                    print("✅ DOI MATCH FOUND!")
                    break

        # Title-based matching
        if not found and norm_ref_title:
            for item in pool:
                t = item["title_norm"]
                if not t:
                    continue
                if norm_ref_title.lower() == t.lower():
                    found = item["article"]
                    best = 100.0
                    print("✅ EXACT TITLE MATCH")
                    break
                if (norm_ref_title.lower() in t.lower() or t.lower() in norm_ref_title.lower()):
                    score = min(len(norm_ref_title), len(t)) / max(len(norm_ref_title), len(t)) * 90.0
                    if score > best:
                        best = score
                        found = item["article"]
                rw = set(norm_ref_title.lower().split())
                aw = set(t.lower().split())
                stop = {'a','an','the','and','or','but','in','on','at','to','for','of','with','by','is','are','was','were','be','been','being'}
                rw -= stop; aw -= stop
                if rw and aw:
                    inter = len(rw & aw)
                    union = len(rw | aw)
                    j = (inter / union) if union else 0.0
                    if inter >= 2 or j >= 0.3:
                        score = j * 80.0
                        if score > best:
                            best = score
                            found = item["article"]

        if found and best > 20.0:
            matched_articles.append({
                "title": found.get('title', ''),
                "url": found.get('url', ''),
                "abstract": found.get('abstract', ''),
                "author_name": found.get('author_name', ''),
                "summary": found.get('summary', ''),
                "id": found.get('id', ''),
                "doi": found.get('doi', ''),
                "date": found.get('date', ''),
                "journal": found.get('journal', ''),
            })
        else:
            print(f"❌ NO RELIABLE MATCH for: {ref_line}")

    # Fallback to first few articles if none matched, to avoid empty citations_obj
    if not matched_articles and json_data:
        for art in json_data[:min(8, len(json_data))]:
            matched_articles.append({
                "title": art.get('title', ''),
                "url": art.get('url', ''),
                "abstract": art.get('abstract', ''),
                "author_name": art.get('author_name', ''),
                "summary": art.get('summary', ''),
                "id": art.get('id', ''),
                "doi": art.get('doi', ''),
                "date": art.get('date', ''),
                "journal": art.get('journal', ''),
            })

    return matched_articles

# Function to recursively replace the invalid values with "Not Available"
def replace_invalid_values(obj):
    if isinstance(obj, dict):  # If the object is a dictionary
        return {key: replace_invalid_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):  # If the object is a list
        return [replace_invalid_values(item) for item in obj]
    elif isinstance(obj, str):  # If it's a string
        if obj.lower() == "none" or obj == "null" or obj == "NaN" or obj == "nan":
            return "Not Detected"
    elif isinstance(obj, float) and (math.isnan(obj)):  # If it's NaN
        return "Not Detected"
    elif obj is None:  # If it's None
        return "Not Detected"
    return obj  # Otherwise, return the value unchanged



def generate_code_from_content(article_content: str, type: str):
    """
    Generates a summary of an article using the configured LLM model.
    
    Parameters:
    - article_content (str): The content of the article to summarize
    
    Returns:
    - str: The generated summary of the article
    """
    llm_client = get_llm_client()
    
    try:
        if llm_client == 'openai':
            return generate_code_from_content_openai(article_content, type, system_prompt_function_generator_list_search, system_prompt_function_generator_id_search)
        else:
            return generate_code_from_content_gemini(article_content, type, system_prompt_function_generator_list_search, system_prompt_function_generator_id_search)
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None


def generate_prompt_from_content(article_content: str, prompt_type: str, include_rationale: bool = False):
    llm_client = get_llm_client()

    system_prompts = {
        "ABSTRACT_EXTRACTION_PROMPT_SAMPLE": ABSTRACT_EXTRACTION_PROMPT,     # <-- include your example + public rationale here
        "STUDY_SUMMARY_PROMPT_SAMPLE": STUDY_SUMMARY_PROMPT,
        "REVIEW_SUMMARY_PROMPT_SAMPLE": REVIEW_SUMMARY_PROMPT,
        "RELEVANCE_CLASSIFIER_PROMPT_SAMPLE": RELEVANCE_CLASSIFIER_PROMPT,
        "ARTICLE_TYPE_PROMPT_SAMPLE": ARTICLE_TYPE_PROMPT,
        "FINAL_RESPONSE_PROMPT_SAMPLE": FINAL_RESPONSE_PROMPT,
        "RELEVANT_SECTIONS_PROMPT_SAMPLE": RELEVANT_SECTIONS_PROMPT,
        "DETERMINE_QUESTION_VALIDITY_PROMPT_SAMPLE": DETERMINE_QUESTION_VALIDITY_PROMPT,
        "GENERAL_QUERY_PROMPT_SAMPLE": GENERAL_QUERY_PROMPT,
        "QUERY_CONTENTION_PROMPT_SAMPLE": QUERY_CONTENTION_PROMPT,
    }

    if llm_client == "openai":
        return generate_prompt_from_content_openai(
            article_content=article_content,
            prompt_type=prompt_type,
            system_prompts=system_prompts,
            include_rationale=include_rationale
        )
    else:
        # implement similar Gemini flow
        return generate_prompt_from_content_gemini(article_content, prompt_type, system_prompts, include_rationale)
