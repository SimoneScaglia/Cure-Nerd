import os
from Bio import Entrez
from Bio.Entrez import efetch

def fetch_articles_by_pmids(pmid_list):
    """
    Fetches articles from PubMed using a list of PMIDs.
    """
    Entrez.email = os.getenv('ENTREZ_EMAIL')
    articles = []
    for pmid in pmid_list:
        try:
            handle = efetch(db="pubmed", id=pmid, rettype="xml")
            article_data = Entrez.read(handle)["PubmedArticle"]
            articles.extend(article_data)
        except Exception as e:
            print(f"Error fetching article with PMID {pmid}: {e}")
            continue
    return articles


def fetch_articles_by_ids(id_list):
    """
    Compatibility wrapper used by main.py.
    In CureNerd IDs are expected to be PubMed PMIDs.
    """
    return fetch_articles_by_pmids(id_list)
