import os
import json
from helper_functions import *

def clean_query(query_list):
    """
    Cleans and normalizes a list of query inputs into a flat list of unique strings.
    
    Parameters:
    - query_list (list): A list that may contain nested lists, strings, and other objects.
    
    Returns:
    - list: A cleaned, flattened, and unique list of strings with extra spaces and newlines removed.
   Input: ['{ "expanded_queries": ["q1", "q2", ...] }']
    Output: ["q1", "q2", ...]
    """
    try:
        # grab the first element and load JSON
        data = json.loads(query_list[0])
        return [q.strip() for q in data.get("expanded_queries", []) if q]
    except Exception as e:
        print(f"[Error] Could not parse queries: {e}")
        return []