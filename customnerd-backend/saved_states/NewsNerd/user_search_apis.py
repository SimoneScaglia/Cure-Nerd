import os
import time
import requests
from newsapi import NewsApiClient

def collect_articles(query_list, article_counter=30):
    """
    Fetches and aggregates news articles based on provided queries 
    using GNews API, NewsAPI, and Guardian API. 
    Deduplicates by title and returns up to `article_counter` results.
    """

    # --- API KEYS ---
    gnews_api_key = os.getenv("GNEWS_API_KEY")  # fallback to hardcoded key
    news_api_key = os.getenv("NEWS_API_KEY")
    guardian_api_key = os.getenv("GUARDIAN_API_KEY")

    # --- API URLs ---
    gnews_url = "https://gnews.io/api/v4/search"
    guardian_url = "https://content.guardianapis.com/search"
    newsapi = NewsApiClient(api_key=news_api_key) if news_api_key else None

    articles_collected = []
    seen_titles = set()

    for query in query_list:
        query = str(query).strip()
        if not query:
            continue

        # --------- GNews API ---------
        try:
            gnews_params = {
                "q": query,
                "lang": "en",
                "sortby": "publishedAt",
                "max": article_counter,
                "token": gnews_api_key
            }
            response = requests.get(gnews_url, params=gnews_params)
            response.raise_for_status()
            gnews_data = response.json()

            for article in gnews_data.get("articles", []):
                title = article.get("title") or "Untitled"
                if isinstance(title, str) and title not in seen_titles:
                    articles_collected.append({
                        "title": title,
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                        "publishedAt": article.get("publishedAt", ""),
                        "source": (article.get("source") or {}).get("name", "")
                    })
                    seen_titles.add(title)

            time.sleep(1)  # avoid rate limits
        except Exception as e:
            print(f"[GNews] Error for query '{query}': {str(e)}")

        # --------- NewsAPI ---------
        if newsapi:
            try:
                newsapi_response = newsapi.get_everything(
                    q=query,
                    language="en",
                    sort_by="publishedAt",
                    page_size=article_counter
                )
                for article in newsapi_response.get("articles", []):
                    title = article.get("title")
                    if title and title not in seen_titles:
                        articles_collected.append({
                            "title": title,
                            "description": article.get("description", ""),
                            "url": article.get("url", ""),
                            "publishedAt": article.get("publishedAt", ""),
                            "source": (article.get("source") or {}).get("name", "")
                        })
                        seen_titles.add(title)
            except Exception as e:
                print(f"[NewsAPI] Error for query '{query}': {str(e)}")

        # --------- Guardian API ---------
        try:
            guardian_params = {
                "q": query,
                "api-key": guardian_api_key,
                "show-fields": "headline,trailText,byline,thumbnail,publication",
                "page-size": article_counter,
                "order-by": "newest"
            }
            
            guardian_response = requests.get(guardian_url, params=guardian_params)
            guardian_response.raise_for_status()
            guardian_data = guardian_response.json()

            for result in guardian_data.get("response", {}).get("results", []):
                title = result.get("webTitle")
                if title and title not in seen_titles:
                    articles_collected.append({
                        "title": title,
                        "description": result.get("fields", {}).get("trailText", ""),
                        "url": result.get("webUrl", ""),
                        "publishedAt": result.get("webPublicationDate", ""),
                        "source": "The Guardian",
                        "section": result.get("sectionName", ""),
                        "byline": result.get("fields", {}).get("byline", "")
                    })
                    seen_titles.add(title)

            time.sleep(1)  # avoid rate limits
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"[Guardian] API key is invalid or expired for query '{query}'")
            elif e.response.status_code == 429:
                print(f"[Guardian] Rate limit exceeded for query '{query}'")
            else:
                print(f"[Guardian] HTTP error for query '{query}': {str(e)}")
        except Exception as e:
            print(f"[Guardian] Error for query '{query}': {str(e)}")

    # limit to article_counter
    return articles_collected[:article_counter]
