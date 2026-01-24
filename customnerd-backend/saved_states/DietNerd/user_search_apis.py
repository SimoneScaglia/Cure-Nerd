import os
from helper_functions import *
from Bio import Entrez
from Bio.Entrez import efetch

def collect_articles(query_list):
    """
    Fetches and aggregates PubMed articles based on provided queries.
    Returns up to 10 most relevant articles per query, deduplicated by PMID.

    Parameters:
    - query_list (list): List of PubMed queries

    Returns:
    - articles_collected (list): List of article dictionaries
    """
    Entrez.email = os.getenv('ENTREZ_EMAIL')
    articles_collected = []
    seen_pmids = set()

    for query in query_list:
        try:
            search_results = exponential_backoff(Entrez.esearch, 
                                              db="pubmed", 
                                              term=query, 
                                              retmax=10, 
                                              sort="relevance")
            retrieved_ids = Entrez.read(search_results)["IdList"]
            if not retrieved_ids:
                continue

            articles = exponential_backoff(Entrez.efetch, 
                                        db="pubmed", 
                                        id=retrieved_ids, 
                                        rettype="xml")
            article_group = Entrez.read(articles)["PubmedArticle"]

            for article in article_group:
                pmid = article['MedlineCitation']['PMID']
                if pmid not in seen_pmids:
                    articles_collected.append(article)
                    seen_pmids.add(pmid)
        except Exception as e:
            print(f"Error collecting articles for query '{query}': {str(e)}")
            continue
    return articles_collected