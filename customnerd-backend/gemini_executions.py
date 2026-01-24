import os
import time
import logging
from typing import Any, Dict, Optional
from google import genai

# Initialize Gemini client with API key from environment
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("Warning: GEMINI_API_KEY not found in environment variables")
    client = None
else:
    client = genai.Client()

MAX_RETRIES = 3            # network / rate-limit retries
BACKOFF_SECS = 2           # exponential back-off base

def reinitialize_gemini_client():
    """
    Reinitialize the Gemini client with the current environment variables.
    This is useful when the API key is updated through the web interface.
    """
    global client
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not found in environment variables")
        client = None
    else:
        client = genai.Client()
        print("Gemini client reinitialized successfully")

def _retryable_gemini_call(*, prompt, temperature=0.3) -> str:
    """
    Wrapper that retries transient Gemini errors.
    Always returns the raw `content` string; never raises upwards.
    """
    if not client:
        logging.error("Gemini client not initialized. Please check your GEMINI_API_KEY in the environment variables.")
        return ""
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text or ""
        except Exception as e:
            logging.warning(f"[Gemini attempt {attempt+1}/{MAX_RETRIES}] {e}")
            time.sleep(BACKOFF_SECS * (2 ** attempt))
    return ""  # give up but keep pipeline alive

def determine_question_validity_gemini(query, DETERMINE_QUESTION_VALIDITY_PROMPT):
    """
    Gemini implementation for determining question validity.
    """
    if not client:
        raise ValueError("Gemini client not initialized. Please check your GEMINI_API_KEY in the environment variables.")
    
    prompt = f"{DETERMINE_QUESTION_VALIDITY_PROMPT}\n\nUser Question: {query}"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def query_generation_gemini(query, GENERAL_QUERY_PROMPT, QUERY_CONTENTION_PROMPT, QUERY_CONTENTION_ENABLED):
    """
    Gemini implementation for query generation.
    """
    if not client:
        raise ValueError("Gemini client not initialized. Please check your GEMINI_API_KEY in the environment variables.")

    #### GENERAL QUERY
    general_prompt = f"{GENERAL_QUERY_PROMPT}\n\nUser Question: {query}"
    
    general_query_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=general_prompt
    )
    general_query = general_query_response.text
    
    if QUERY_CONTENTION_ENABLED:
        #### POINTS OF CONTENTION QUERIES
        contention_prompt = f"{QUERY_CONTENTION_PROMPT}\n\nUser Question: {query}"
        
        poc_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contention_prompt
        )
        query_contention = poc_response.text
        return general_query, query_contention
    else:
        # Skip contention queries when disabled
        query_contention = "Query contention disabled"
        return general_query, query_contention

def get_article_type_gemini(abstract, ARTICLE_TYPE_PROMPT):
    """
    Gemini implementation for determining article type.
    """
    if not client:
        raise ValueError("Gemini client not initialized. Please check your GEMINI_API_KEY in the environment variables.")
    
    prompt = f"{ARTICLE_TYPE_PROMPT}\n\nAbstract: {abstract}"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    article_type = response.text.strip().lower()
    return article_type

def generate_content_from_pdf_gemini(pdf_text, content_type="abstract", publication_type="study", 
                                   ABSTRACT_EXTRACTION_PROMPT=None, REVIEW_SUMMARY_PROMPT=None, STUDY_SUMMARY_PROMPT=None):
    """
    Gemini implementation for generating content from PDF.
    """
    if not client:
        raise ValueError("Gemini client not initialized. Please check your GEMINI_API_KEY in the environment variables.")
    
    # Select the appropriate prompt
    if content_type == "abstract":
        prompt = ABSTRACT_EXTRACTION_PROMPT
    elif content_type == "summary":
        if publication_type == "review":
            prompt = REVIEW_SUMMARY_PROMPT
        else:
            prompt = STUDY_SUMMARY_PROMPT
    else:
        raise ValueError("Invalid content_type. Choose 'abstract' or 'summary'.")

    full_prompt = f"{prompt}\n\nPaper: {pdf_text}"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )
    return response.text.strip()

def section_match_gemini(list_of_strings, RELEVANT_SECTIONS_PROMPT):
    """
    Gemini implementation for section matching.
    """
    if not client:
        raise ValueError("Gemini client not initialized. Please check your GEMINI_API_KEY in the environment variables.")
    
    list_of_strings_str = ', '.join(list_of_strings)
    prompt = f"{RELEVANT_SECTIONS_PROMPT}\n\nSections: {list_of_strings_str}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    relevant_sections = response.text
    return relevant_sections

def generate_final_response_gemini(all_relevant_articles, query, FINAL_RESPONSE_PROMPT, DISCLAIMER_TEXT):
    """
    Gemini implementation for generating final response.
    """
    if not client:
        raise ValueError("Gemini client not initialized. Please check your GEMINI_API_KEY in the environment variables.")

    # Human prompt for Gemini
    human_prompt_response = f"""
    Evidence and Claims: {all_relevant_articles}
    User Question: {query}
    """
    
    full_prompt = f"{FINAL_RESPONSE_PROMPT}\n\n{human_prompt_response}"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )
    output = response.text
    final_output = f"{output}\n\n{DISCLAIMER_TEXT}"
    
    return final_output

def generate_code_from_content_gemini(article_content, type, system_prompt_function_generator_list_search, system_prompt_function_generator_id_search):
    """
    Gemini implementation for generating code from content.
    """
    if not client:
        raise ValueError("Gemini client not initialized. Please check your GEMINI_API_KEY in the environment variables.")
    
    try:
        # Select the appropriate system prompt based on type
        if type == "list_search":
            system_prompt = system_prompt_function_generator_list_search
        elif type == "id_search":
            system_prompt = system_prompt_function_generator_id_search
        else:
            # Default to list_search for unknown types
            system_prompt = system_prompt_function_generator_list_search
        
        prompt = f"{system_prompt}\n\nCode/: {article_content}"
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

import json
import re

def generate_prompt_from_content_gemini(
    article_content,
    prompt_type,
    system_prompts,
    include_rationale=False
):
    """
    Gemini implementation for generating a domain-specific prompt.
    Mirrors OpenAI logic: adds public rationale, self-reflection, and structured JSON output.
    """
    if not client:
        raise ValueError("Gemini client not initialized. Please check GEMINI_API_KEY in env variables.")

    try:
        # Map prompt type → sample key
        prompt_map = {
            "abstract": "ABSTRACT_EXTRACTION_PROMPT_SAMPLE",
            "study_summary": "STUDY_SUMMARY_PROMPT_SAMPLE",
            "review_summary": "REVIEW_SUMMARY_PROMPT_SAMPLE",
            "relevance": "RELEVANCE_CLASSIFIER_PROMPT_SAMPLE",
            "article_type": "ARTICLE_TYPE_PROMPT_SAMPLE",
            "final_response": "FINAL_RESPONSE_PROMPT_SAMPLE",
            "relevant_sections": "RELEVANT_SECTIONS_PROMPT_SAMPLE",
            "question_validity": "DETERMINE_QUESTION_VALIDITY_PROMPT_SAMPLE",
            "general_query": "GENERAL_QUERY_PROMPT_SAMPLE",
            "query_contention": "QUERY_CONTENTION_PROMPT_SAMPLE",
        }

        sample_key = prompt_map.get(prompt_type)
        if not sample_key or sample_key not in system_prompts:
            raise ValueError(f"Invalid or missing example prompt for type '{prompt_type}'")

        example_prompt = system_prompts[sample_key].strip()

        # Public reasoning scaffold — safe “chain of thought style”
        RATIONALE_TEMPLATE = (
            "Public Rationale (2–4 bullets):\n"
            "- Identify domain & task solved by the example prompt.\n"
            "- Extract key structure (tone, required fields, examples, response format).\n"
            "- Map those structural elements to the new domain content.\n"
            "- Generate a complete, clearly structured prompt in the same style.\n"
        )

        # 🧠 System instruction identical to OpenAI version
        system_instruction = f"""
You are a professional Prompt Engineer building reusable expert prompts for the Nerd system.
Study the Example Prompt and its PUBLIC RATIONALE below. 
Use its style, tone, structure, and purpose to create a new prompt tailored to the user's DOMAIN CONTENT.

EXAMPLE PROMPT:
{example_prompt}

{RATIONALE_TEMPLATE}

REQUIRED OUTPUT (JSON only):
{{
  "rationale": ["short bullet 1","short bullet 2"], 
  "prompt": "<new prompt text exactly in same structure/format>"
}}

Rules:
1. Output must be **only valid JSON**. 
2. Prompt must mirror the structure, formatting, and tone of the example.
3. Include 2–4 rationale bullets (public reasoning).
4. Self-verify before output that:
   - JSON is valid
   - The prompt structurally matches example sections
   - No meta commentary remains
5. If checks fail, correct and output the fixed JSON.
"""

        # Compose final content sent to Gemini
        user_content = f"""
<DOMAIN_CONTENT>
{article_content.strip()}
</DOMAIN_CONTENT>

Generate the JSON output exactly as specified.
"""

        full_input = f"{system_instruction}\n\n{user_content}"

        # 🔥 Gemini API call (Google Generative Language client)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_input,
            # generation_config={
            #     "temperature": 0.2,
            #     "top_p": 0.95,
            # }
        )

        raw = response.text.strip()
        if not raw:
            raise ValueError("Empty response from Gemini API")

        # Clean Markdown wrappers
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

        # Attempt JSON parse
        try:
            parsed = json.loads(cleaned)
        except Exception:
            start, end = cleaned.find("{"), cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(cleaned[start:end+1])
                except Exception as e:
                    raise ValueError(f"Failed to parse Gemini JSON. Raw:\n{raw}\n\nErr:{e}")
            else:
                raise ValueError(f"Failed to parse Gemini JSON. Raw:\n{raw}")

        if "prompt" not in parsed:
            raise ValueError(f"Gemini output missing 'prompt' field. Parsed JSON:\n{parsed}")

        return parsed if include_rationale else parsed["prompt"]

    except Exception as e:
        print(f"❌ Gemini prompt generation error: {e}")
        raise
