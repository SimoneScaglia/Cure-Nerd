import os
import time
import requests
from bs4 import BeautifulSoup

def clean_html(html_text):
    """Strip HTML tags but keep code blocks readable."""
    soup = BeautifulSoup(html_text, "html.parser")
    for code in soup.find_all("code"):
        code.replace_with(f"\n```\n{code.get_text()}\n```\n")
    return soup.get_text("\n").strip()

def collect_articles(query_list, answer_counter=50):
    """
    Fetches StackOverflow Q&A for a list of queries using the StackExchange API.
    Deduplicates by question_id and returns up to `answer_counter` total answers.
    """

    # --- API CONFIG ---
    stack_api_key = os.getenv("STACK_API_KEY")  # optional
    search_url = "https://api.stackexchange.com/2.3/search/advanced"
    answers_url = "https://api.stackexchange.com/2.3/questions/{ids}/answers"

    collected = []
    seen_questions = set()

    for query in query_list:
        query = str(query).strip()
        if not query:
            continue

        # --------- SEARCH QUESTIONS ---------
        try:
            params = {
                "order": "desc",
                "sort": "relevance",
                "q": query,
                "site": "stackoverflow",
                "pagesize": 10,
            }
            if stack_api_key:
                params["key"] = stack_api_key

            response = requests.get(search_url, params=params)
            response.raise_for_status()
            questions = response.json().get("items", [])

            for q in questions:
                qid = q.get("question_id")
                if qid in seen_questions:
                    continue
                seen_questions.add(qid)

                # --------- GET ANSWERS FOR QUESTION ---------
                try:
                    ans_params = {
                        "order": "desc",
                        "sort": "votes",
                        "site": "stackoverflow",
                        "filter": "withbody",
                        "pagesize": 5,
                    }
                    if stack_api_key:
                        ans_params["key"] = stack_api_key

                    ans_response = requests.get(answers_url.format(ids=qid), params=ans_params)
                    ans_response.raise_for_status()
                    answers = ans_response.json().get("items", [])

                    for ans in answers:
                        collected.append({
                            "question_title": q.get("title"),
                            "question_url": q.get("link"),
                            "answer_id": ans.get("answer_id"),
                            "is_accepted": ans.get("is_accepted", False),
                            "score": ans.get("score", 0),
                            "answer_body": clean_html(ans.get("body", "")),
                            "answer_url": f"https://stackoverflow.com/a/{ans.get('answer_id')}"
                        })

                except Exception as e:
                    print(f"[Answers] Error fetching answers for QID {qid}: {e}")

            time.sleep(1)  # be nice to API

        except Exception as e:
            print(f"[Search] Error for query '{query}': {str(e)}")

    # limit to answer_counter
    return collected[:answer_counter]
