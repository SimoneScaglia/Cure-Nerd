import os
from Bio import Entrez
from Bio.Entrez import efetch

def fetch_articles_by_ids(id_list):
    """
    Fetches articles from PubMed using a list of PMIDs.
    """
    Entrez.email = os.getenv('ENTREZ_EMAIL')
    articles = []
    for id in id_list:
        try:
            handle = efetch(db="pubmed", id=id, rettype="xml")
            article_data = Entrez.read(handle)["PubmedArticle"]
            articles.extend(article_data)
        except Exception as e:
            print(f"Error fetching article with PMID {id}: {e}")
            continue
    return articles