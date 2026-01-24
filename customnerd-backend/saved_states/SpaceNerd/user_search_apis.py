import requests
import re
import os
from dotenv import load_dotenv
from helper_functions import *
# Load environment variables from variables.env
load_dotenv('variables.env')

def collect_articles(query, article_counter=30):
    page_limit=20
    results = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; mybot/0.1)"}
    
    # Handle different query input formats and split by newlines
    search_terms = []
    
    if isinstance(query, list):
        # If query is a list, process each item
        for item in query:
            if isinstance(item, str):
                if '\n' in item:
                    # Split by newlines and add each term
                    terms = [term.strip() for term in item.split('\n') if term.strip()]
                    search_terms.extend(terms)
                else:
                    # Add the item as a single term
                    if item.strip():
                        search_terms.append(item.strip())
    elif isinstance(query, str):
        # If query is a string, check for newlines
        if '\n' in query:
            search_terms = [term.strip() for term in query.split('\n') if term.strip()]
        else:
            search_terms = [query.strip()] if query.strip() else []
    else:
        # Fallback for other types
        search_terms = [str(query).strip()] if query else []
    
    print(f"Search terms: {search_terms}")
    
    # Process each search term
    for search_term in search_terms:
        if not search_term:
            continue
            
        print(f"Processing search term: '{search_term}'")

        # --- Wikipedia ---
        try:
            print("[Wikipedia] Searching:", search_term)
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
            search_res = requests.get(search_url, headers=headers).json()
            pages = search_res.get("query", {}).get("search", [])

            for p in pages[:page_limit]:
                title = p["title"]
                extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&explaintext&titles={title}&format=json"
                extract_res = requests.get(extract_url, headers=headers).json()
                page_data = list(extract_res.get("query", {}).get("pages", {}).values())[0]
                extract = clean_text(page_data.get("extract"))
                url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                results.append({
                    "source": "Wikipedia",
                    "title": title,
                    "all_information": extract,
                    "url": url
                })
        except Exception as e:
            print("Wikipedia error:", e)

        # --- NASA Images ---
        try:
            print("[NASA Images] Searching:", search_term)
            url = f"https://images-api.nasa.gov/search?q={search_term}"
            res = requests.get(url).json()
            items = res.get("collection", {}).get("items", [])

            for item in items[:page_limit]:
                data = item.get("data", [{}])[0]
                title = data.get("title", "No title")
                desc = clean_text(data.get("description"))
                href = item.get("links", [{}])[0].get("href", "No URL")
                results.append({
                    "source": "NASA Images",
                    "title": title,
                    "all_information": desc,
                    "url": href
                })
        except Exception as e:
            print("NASA Images error:", e)

        # --- arXiv ---
        try:
            print("[arXiv] Searching:", search_term)
            url = f"https://export.arxiv.org/api/query?search_query=all:{search_term}&start=0&max_results={page_limit}"
            res = requests.get(url, headers=headers).text
            entries = re.findall(r"<entry>(.*?)</entry>", res, re.DOTALL)
            for entry in entries:
                title = clean_text(re.search(r"<title>(.*?)</title>", entry, re.DOTALL).group(1))
                summary = clean_text(re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL).group(1))
                link_match = re.search(r"<id>(.*?)</id>", entry)
                link = link_match.group(1) if link_match else "No URL"
                results.append({
                    "source": "arXiv",
                    "title": title,
                    "all_information": summary,
                    "url": link
                })
        except Exception as e:
            print("arXiv error:", e)

        # --- NASA ADS ---
        ads_token = os.getenv('ADS_TOKEN')
        if ads_token:
            try:
                print("[NASA ADS] Searching:", search_term)
                ads_url = f"https://api.adsabs.harvard.edu/v1/search/query?q={search_term}&fl=title,author,bibcode&rows={page_limit}"
                ads_headers = {"Authorization": f"Bearer {ads_token}"}
                res = requests.get(ads_url, headers=ads_headers).json()
                docs = res.get("response", {}).get("docs", [])
                for doc in docs:
                    title = clean_text(" ".join(doc.get("title", [])))
                    authors = ", ".join(doc.get("author", []))
                    bibcode = doc.get("bibcode", "No bibcode")
                    url = f"https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"
                    results.append({
                        "source": "NASA ADS",
                        "title": title,
                        "all_information": f"Authors: {authors}",
                        "url": url
                    })
            except Exception as e:
                print("NASA ADS error:", e)
        else:
            print("[NASA ADS] Skipped (no API token provided)")

        # --- SIMBAD ---
        try:
            print("[SIMBAD] Searching:", search_term)
            simbad_url = "https://simbad.u-strasbg.fr/simbad/sim-id"
            params = {"Ident": search_term, "output.format": "VOTABLE"}
            res = requests.get(simbad_url, params=params, headers=headers).text
            title_match = re.search(r"<INFO name=\"OBJECT\" value=\"(.*?)\"/>", res)
            title = title_match.group(1) if title_match else search_term
            results.append({
                "source": "SIMBAD",
                "title": title,
                "all_information": "Basic astronomical object data from SIMBAD",
                "url": f"https://simbad.u-strasbg.fr/simbad/sim-basic?Ident={search_term.replace(' ', '+')}"
            })
        except Exception as e:
            print("SIMBAD error:", e)

        # --- VizieR ---
        try:
            print("[VizieR] Searching:", search_term)
            vizier_url = "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"
            params = {"-c": search_term, "-out.max": "3"}
            res = requests.get(vizier_url, params=params, headers=headers).text
            lines = res.strip().split("\n")
            for line in lines[1:page_limit]:
                cols = line.split("\t")
                if len(cols) > 1:
                    results.append({
                        "source": "VizieR",
                        "title": cols[0],
                        "all_information": " | ".join(cols[1:]),
                        "url": "https://vizier.cds.unistra.fr"
                    })
        except Exception as e:
            print("VizieR error:", e)

        # --- Minor Planet Center (MPC) ---
        try:
            print("[MPC] Searching:", search_term)
            mpc_url = "https://minorplanetcenter.net/mpcops/orbits"
            params = {"designation": search_term, "format": "json"}
            res = requests.get(mpc_url, params=params, headers=headers).json()
            if "orbits" in res:
                for orb in res["orbits"][:page_limit]:
                    desig = orb.get("desig", search_term)
                    results.append({
                        "source": "MPC",
                        "title": desig,
                        "all_information": str(orb),
                        "url": "https://minorplanetcenter.net/"
                    })
        except Exception as e:
            print("MPC error:", e)

    return results[:article_counter]


# # Example usage:
# if __name__ == "__main__":
#     data = search_space_apis("Hubble Telescope", page_limit=20)
#     print("\nCollected", len(data), "results\n")
#     for i, r in enumerate(data, 1):
#         print(f"{i}. Source: {r['source']}")
#         print(f"   Title: {r['title']}")
#         print("   All information:", r['all_information'], "...\n")
#         print("   URL:", r['url'], "\n")
