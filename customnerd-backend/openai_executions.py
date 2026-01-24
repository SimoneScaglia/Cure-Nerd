from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, OpenAIError
import os
import time
import logging
from typing import Any, Dict, Optional

# Initialize OpenAI client with API key from environment
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")
    client = None
else:
    client = OpenAI(api_key=api_key)

MAX_RETRIES = 3            # network / rate-limit retries
BACKOFF_SECS = 2           # exponential back-off base

def reinitialize_openai_client():
    """
    Reinitialize the OpenAI client with the current environment variables.
    This is useful when the API key is updated through the web interface.
    """
    global client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in environment variables")
        client = None
    else:
        client = OpenAI(api_key=api_key)
        print("OpenAI client reinitialized successfully")

def _retryable_openai_call(*, messages, temperature=0.3, top_p=1.0,
                           response_format: Optional[Dict[str, str]] = None) -> str:
    """
    Wrapper that retries transient OpenAI errors (RateLimitError, APIError, Timeout).
    Always returns the raw `content` string; never raises upwards.
    """
    if not client:
        logging.error("OpenAI client not initialized. Please check your OPENAI_API_KEY in the environment variables.")
        return ""
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                response_format=response_format,
            )
            return resp.choices[0].message.content or ""
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            logging.warning(f"[OpenAI attempt {attempt+1}/{MAX_RETRIES}] {e}")
            time.sleep(BACKOFF_SECS * (2 ** attempt))
        except Exception as e:
            logging.exception(f"[OpenAI fatal] {e}")
            break
    return ""  # give up but keep pipeline alive

def determine_question_validity_openai(query, DETERMINE_QUESTION_VALIDITY_PROMPT):
    """
    OpenAI implementation for determining question validity.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. Please check your OPENAI_API_KEY in the environment variables.")
    
    valid_question_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": DETERMINE_QUESTION_VALIDITY_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0.2,
        top_p=1,
    )

    return valid_question_response.choices[0].message.content

def query_generation_openai(query, GENERAL_QUERY_PROMPT, QUERY_CONTENTION_PROMPT, QUERY_CONTENTION_ENABLED):
    """
    OpenAI implementation for query generation.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. Please check your OPENAI_API_KEY in the environment variables.")

    #### GENERAL QUERY
    general_query_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": GENERAL_QUERY_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0.7,
        top_p=1,
    )

    general_query = general_query_response.choices[0].message.content
    
    if QUERY_CONTENTION_ENABLED:
        #### POINTS OF CONTENTION QUERIES
        poc_response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": QUERY_CONTENTION_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.6,
            top_p=1,
        )

        query_contention = poc_response.choices[0].message.content
        return general_query, query_contention
    else:
        # Skip contention queries when disabled
        query_contention = "Query contention disabled"
        return general_query, query_contention

def get_article_type_openai(abstract, ARTICLE_TYPE_PROMPT):
    """
    OpenAI implementation for determining article type.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. Please check your OPENAI_API_KEY in the environment variables.")
    
    article_type_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": ARTICLE_TYPE_PROMPT},
            {"role": "user", "content": f"Abstract: {abstract}"}
        ],
        temperature=0.1,
        top_p=1
    )

    article_type = article_type_response.choices[0].message.content.strip().lower()
    return article_type

def generate_content_from_pdf_openai(pdf_text, content_type="abstract", publication_type="study", 
                                   ABSTRACT_EXTRACTION_PROMPT=None, REVIEW_SUMMARY_PROMPT=None, STUDY_SUMMARY_PROMPT=None):
    """
    OpenAI implementation for generating content from PDF.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. Please check your OPENAI_API_KEY in the environment variables.")
    
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

    # Make OpenAI API call
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Paper: {pdf_text}"}
        ],
        temperature=0.6,
        top_p=1
    )

    return response.choices[0].message.content.strip()

def section_match_openai(list_of_strings, RELEVANT_SECTIONS_PROMPT):
    """
    OpenAI implementation for section matching.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. Please check your OPENAI_API_KEY in the environment variables.")
    
    list_of_strings_str = ', '.join(list_of_strings)

    relevant_sections_response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
                "role": "system",
                "content": RELEVANT_SECTIONS_PROMPT
            },
            {
                "role": "user",
                "content": list_of_strings_str
            }
        ],
        temperature=0.1,
        top_p=1
    )

    relevant_sections = relevant_sections_response.choices[0].message.content
    return relevant_sections

def generate_final_response_openai(all_relevant_articles, query, FINAL_RESPONSE_PROMPT, DISCLAIMER_TEXT):
    """
    OpenAI implementation for generating final response.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. Please check your OPENAI_API_KEY in the environment variables.")

    # Human prompt for OpenAI
    human_prompt_response = f"""
    Evidence and Claims: {all_relevant_articles}
    User Question: {query}
    """

    # Generate response from OpenAI API
    output_response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": FINAL_RESPONSE_PROMPT},
            {"role": "user", "content": human_prompt_response}
        ],
        temperature=0.5,
        top_p=1
    )

    # Extract response content
    output = output_response.choices[0].message.content
    final_output = f"{output}\n\n{DISCLAIMER_TEXT}"
    
    return final_output

def generate_code_from_content_openai(article_content, type, system_prompt_function_generator_list_search, system_prompt_function_generator_id_search):
    """
    OpenAI implementation for generating code from content.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. Please check your OPENAI_API_KEY in the environment variables.")
    
    try:
        # Select the appropriate system prompt based on type
        if type == "list_search":
            system_prompt = system_prompt_function_generator_list_search
        elif type == "id_search":
            system_prompt = system_prompt_function_generator_id_search
        else:
            # Default to list_search for unknown types
            system_prompt = system_prompt_function_generator_list_search
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Code/: {article_content}"
                }
            ],
            temperature=0.6,
            top_p=1
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None

import json
import re
from typing import Optional

def generate_prompt_from_content_openai(
    article_content: str,
    prompt_type: str,
    system_prompts: dict,
    include_rationale: bool = False,
    max_self_retries: int = 1,
):
    """
    Enhanced OpenAI implementation for generating a domain-specific prompt with a public rationale.
    Returns: prompt_str or dict {"prompt":..., "rationale":[...]} if include_rationale True.
    """
    if not client:
        raise ValueError("OpenAI client not initialized. Please check your OPENAI_API_KEY.")

    # mapping of prompt types -> sample keys in system_prompts
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

    # Public rationale template that explains why the example has certain parts.
    # This is NOT internal chain-of-thought — it's a short, shareable plan the model can follow.
    RATIONALE_TEMPLATE = (
        "Public Rationale (2-4 bullets):\n"
        "- Identify domain & main goal of the example prompt (what task it solves).\n"
        "- Extract the structural pieces we must replicate (tone, required fields, output format).\n"
        "- Map example pieces to the new domain content (which sections change, which stay).\n"
        "- Produce final prompt that mirrors example structure and enforces exact output rules.\n"
    )

    # High-level system instruction that asks model to produce JSON only
    system_prompt = f"""
You are a professional Prompt Engineer building *reusable, expert-level prompts* for the Nerd system.
Study the Example Prompt and its PUBLIC RATIONALE below. Use that structure, tone, examples, and format exactly — but produce an original prompt tailored to the user's DOMAIN CONTENT provided.

EXAMPLE PROMPT (style + format reference):
{example_prompt}

{RATIONALE_TEMPLATE}

REQUIREMENTS for your OUTPUT:
1. Output MUST be valid JSON only (no surrounding commentary). The JSON schema:
   {{
     "rationale": ["short bullet 1", "short bullet 2"],   // optional; include up to 4 bullets (public, non-sensitive)
     "prompt": "<the new prompt text EXACTLY in the same style/format as the example>"
   }}
2. "prompt" MUST start with the new prompt text and match the example's structure (sections, examples, tone).
3. If include_rationale=False, you may still produce rationale inside the JSON but the caller will ignore it.
4. After composing the prompt, run a 1-line self-check inside the generation (model-internal) that verifies:
   - Format preserved (same sections),
   - Output is only the JSON object (no extra text),
   - Prompt follows the domain constraints.
   If any check fails, automatically revise and produce the corrected JSON.
5. Temperature should be low for determinism (we will pass low temperature from the client).

Now read the user-supplied DOMAIN CONTENT and generate the JSON described above.
"""

    # Build user message with domain content and caller preferences
    user_message = f"""
<DOMAIN_CONTENT>
{article_content.strip()}
</DOMAIN_CONTENT>

Return ONLY the JSON described in the system instructions.
"""

    # single-call self-revision approach; low temperature for repeatability
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        top_p=0.95,
        presence_penalty=0,
        frequency_penalty=0,
        # optionally set max_tokens to a limit you prefer
    )

    raw = response.choices[0].message.content.strip()

    # try to extract JSON robustly (some models add backticks — strip them)
    # remove leading/trailing backticks or markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    # Some models might escape quotes; attempt JSON loads with a couple heuristics
    parsed = None
    try:
        parsed = json.loads(cleaned)
    except Exception:
        # heuristic: find first '{' and last '}' and try to parse substring
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            substring = cleaned[start:end+1]
            try:
                parsed = json.loads(substring)
            except Exception as e:
                # give helpful debug (will be logged in server error)
                raise ValueError(f"Failed to parse JSON output from LLM. Raw output:\n{raw}\n\nParse error: {e}")
        else:
            raise ValueError(f"Failed to parse JSON output from LLM. Raw output:\n{raw}")

    # Validate minimal schema
    if "prompt" not in parsed:
        raise ValueError(f"LLM JSON missing required 'prompt' field. Parsed JSON:\n{parsed}")

    # Return depending on include_rationale
    if include_rationale:
        return parsed
    else:
        return parsed["prompt"]
