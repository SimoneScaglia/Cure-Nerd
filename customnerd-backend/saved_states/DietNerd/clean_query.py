import os
from helper_functions import *

def refine_prompts(query_list):
    """
    Cleans and normalizes a list of query inputs into a flat list of unique strings.
    
    Parameters:
    - query_list (list): A list that may contain nested lists, strings, and other objects.
    
    Returns:
    - list: A cleaned, flattened, and unique list of strings with extra spaces and newlines removed.
    """
    def flatten_and_clean(item):
        if isinstance(item, list):
            result = []
            for subitem in item:
                result.extend(flatten_and_clean(subitem))
            return result
        else:
            if not isinstance(item, str):
                item = str(item)
            return [line.strip() for line in item.split('\n') if line.strip()]

    # Flatten and clean the list
    cleaned_list = []
    for element in query_list:
        cleaned_list.extend(flatten_and_clean(element))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_cleaned_list = []
    for item in cleaned_list:
        if item not in seen:
            seen.add(item)
            unique_cleaned_list.append(item)
    
    return unique_cleaned_list