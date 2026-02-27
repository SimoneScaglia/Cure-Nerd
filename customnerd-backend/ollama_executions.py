from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError, NotFoundError
import os
import time
import logging
import json
import re
from typing import Dict, Optional

MAX_RETRIES = 3
BACKOFF_SECS = 2


def _get_ollama_model() -> str:
    model = os.getenv('OLLAMA_MODEL', 'llama3.2').strip('"').strip()
    return model if model else 'llama3.2'


def _get_ollama_base_url() -> str:
    base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').strip('"').strip()
    if not base_url:
        base_url = 'http://localhost:11434'
    if not base_url.endswith('/v1') and not base_url.endswith('/v1/'):
        base_url = base_url.rstrip('/') + '/v1/'
    return base_url


def _make_client() -> Optional[OpenAI]:
    try:
        return OpenAI(
            base_url=_get_ollama_base_url(),
            api_key='ollama',  # required by the SDK but ignored by Ollama
        )
    except Exception as e:
        logging.error(f"Failed to create Ollama client: {e}")
        return None


# Module-level client — rebuilt whenever reinitialize_ollama_client() is called
client = _make_client()


def reinitialize_ollama_client():
    """Rebuild the Ollama client from the current environment variables."""
    global client
    client = _make_client()
    if client:
        print(f"Ollama client reinitialized (model={_get_ollama_model()}, url={_get_ollama_base_url()})")
    else:
        print("Warning: Ollama client could not be initialized")


def _safe_create(**kwargs):
    """
    Thin wrapper around client.chat.completions.create that converts common
    Ollama errors into actionable ValueError messages instead of raw 500s.
    """
    if not client:
        raise ValueError(
            "Ollama client is not initialized. Make sure Ollama is running and "
            "OLLAMA_BASE_URL is correct in the environment configuration."
        )
    try:
        return client.chat.completions.create(**kwargs)
    except NotFoundError:
        model = kwargs.get('model', _get_ollama_model())
        raise ValueError(
            f"Ollama model '{model}' was not found on the local server. "
            f"Pull it first by running 'ollama pull {model}', or use the "
            "'Update Environment Configuration' button in the Config page to "
            "trigger the automated setup."
        )
    except APIConnectionError:
        raise ValueError(
            "Cannot connect to the Ollama server. Make sure 'ollama serve' is "
            "running on the configured base URL."
        )


def _retryable_ollama_call(*, messages, temperature=0.3, top_p=1.0,
                           response_format: Optional[Dict[str, str]] = None) -> str:
    """
    Wrapper that retries transient Ollama/network errors.
    Always returns the raw content string; never raises upwards.
    """
    if not client:
        logging.error("Ollama client not initialized.")
        return ""

    model = _get_ollama_model()
    kwargs = dict(model=model, messages=messages, temperature=temperature, top_p=top_p)
    if response_format:
        kwargs['response_format'] = response_format

    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            logging.warning(f"[Ollama attempt {attempt+1}/{MAX_RETRIES}] {e}")
            time.sleep(BACKOFF_SECS * (2 ** attempt))
        except Exception as e:
            logging.exception(f"[Ollama fatal] {e}")
            break
    return ""


def determine_question_validity_ollama(query, DETERMINE_QUESTION_VALIDITY_PROMPT):
    """Ollama implementation for determining question validity."""
    resp = _safe_create(
        model=_get_ollama_model(),
        messages=[
            {"role": "system", "content": DETERMINE_QUESTION_VALIDITY_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0.2,
        top_p=1,
    )
    return resp.choices[0].message.content


def query_generation_ollama(query, GENERAL_QUERY_PROMPT, QUERY_CONTENTION_PROMPT, QUERY_CONTENTION_ENABLED):
    """Ollama implementation for query generation."""
    model = _get_ollama_model()

    general_query_response = _safe_create(
        model=model,
        messages=[
            {"role": "system", "content": GENERAL_QUERY_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0.7,
        top_p=1,
    )
    general_query = general_query_response.choices[0].message.content

    if QUERY_CONTENTION_ENABLED:
        poc_response = _safe_create(
            model=model,
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
        return general_query, "Query contention disabled"


def get_article_type_ollama(abstract, ARTICLE_TYPE_PROMPT):
    """Ollama implementation for determining article type."""
    resp = _safe_create(
        model=_get_ollama_model(),
        messages=[
            {"role": "system", "content": ARTICLE_TYPE_PROMPT},
            {"role": "user", "content": f"Abstract: {abstract}"},
        ],
        temperature=0.1,
        top_p=1,
    )
    return resp.choices[0].message.content.strip().lower()


def generate_content_from_pdf_ollama(pdf_text, content_type="abstract", publication_type="study",
                                     ABSTRACT_EXTRACTION_PROMPT=None, REVIEW_SUMMARY_PROMPT=None,
                                     STUDY_SUMMARY_PROMPT=None):
    """Ollama implementation for generating content from PDF."""
    if content_type == "abstract":
        prompt = ABSTRACT_EXTRACTION_PROMPT
    elif content_type == "summary":
        prompt = REVIEW_SUMMARY_PROMPT if publication_type == "review" else STUDY_SUMMARY_PROMPT
    else:
        raise ValueError("Invalid content_type. Choose 'abstract' or 'summary'.")

    resp = _safe_create(
        model=_get_ollama_model(),
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Paper: {pdf_text}"},
        ],
        temperature=0.6,
        top_p=1,
    )
    return resp.choices[0].message.content.strip()


def section_match_ollama(list_of_strings, RELEVANT_SECTIONS_PROMPT):
    """Ollama implementation for section matching."""
    list_of_strings_str = ', '.join(list_of_strings)
    resp = _safe_create(
        model=_get_ollama_model(),
        messages=[
            {"role": "system", "content": RELEVANT_SECTIONS_PROMPT},
            {"role": "user", "content": list_of_strings_str},
        ],
        temperature=0.1,
        top_p=1,
    )
    return resp.choices[0].message.content


def generate_final_response_ollama(all_relevant_articles, query, FINAL_RESPONSE_PROMPT, DISCLAIMER_TEXT):
    """Ollama implementation for generating the final response."""
    human_prompt_response = f"""
    Evidence and Claims: {all_relevant_articles}
    User Question: {query}
    """

    resp = _safe_create(
        model=_get_ollama_model(),
        messages=[
            {"role": "system", "content": FINAL_RESPONSE_PROMPT},
            {"role": "user", "content": human_prompt_response},
        ],
        temperature=0.5,
        top_p=1,
    )
    output = resp.choices[0].message.content
    return f"{output}\n\n{DISCLAIMER_TEXT}"


def generate_code_from_content_ollama(article_content, type,
                                      system_prompt_function_generator_list_search,
                                      system_prompt_function_generator_id_search):
    """Ollama implementation for generating code from content."""
    try:
        if type == "id_search":
            system_prompt = system_prompt_function_generator_id_search
        else:
            system_prompt = system_prompt_function_generator_list_search

        resp = _safe_create(
            model=_get_ollama_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Code/: {article_content}"},
            ],
            temperature=0.6,
            top_p=1,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"Error generating code via Ollama: {e}")
        return None


def generate_prompt_from_content_ollama(
    article_content: str,
    prompt_type: str,
    system_prompts: dict,
    include_rationale: bool = False,
    max_self_retries: int = 1,
):
    """
    Ollama implementation for generating a domain-specific prompt.
    Returns: prompt_str, or dict {"prompt":..., "rationale":[...]} if include_rationale=True.
    """
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

    RATIONALE_TEMPLATE = (
        "Public Rationale (2-4 bullets):\n"
        "- Identify domain & main goal of the example prompt (what task it solves).\n"
        "- Extract the structural pieces we must replicate (tone, required fields, output format).\n"
        "- Map example pieces to the new domain content (which sections change, which stay).\n"
        "- Produce final prompt that mirrors example structure and enforces exact output rules.\n"
    )

    system_prompt = f"""
You are a professional Prompt Engineer building *reusable, expert-level prompts* for the Nerd system.
Study the Example Prompt and its PUBLIC RATIONALE below. Use that structure, tone, examples, and format exactly — but produce an original prompt tailored to the user's DOMAIN CONTENT provided.

EXAMPLE PROMPT (style + format reference):
{example_prompt}

{RATIONALE_TEMPLATE}

REQUIREMENTS for your OUTPUT:
1. Output MUST be valid JSON only (no surrounding commentary). The JSON schema:
   {{
     "rationale": ["short bullet 1", "short bullet 2"],
     "prompt": "<the new prompt text EXACTLY in the same style/format as the example>"
   }}
2. "prompt" MUST start with the new prompt text and match the example's structure (sections, examples, tone).
3. After composing the prompt, verify: format preserved, output is only JSON, prompt follows domain constraints.

Now read the user-supplied DOMAIN CONTENT and generate the JSON described above.
"""

    user_message = f"""
<DOMAIN_CONTENT>
{article_content.strip()}
</DOMAIN_CONTENT>

Return ONLY the JSON described in the system instructions.
"""

    resp = _safe_create(
        model=_get_ollama_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        top_p=0.95,
        presence_penalty=0,
        frequency_penalty=0,
    )

    raw = resp.choices[0].message.content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()

    parsed = None
    try:
        parsed = json.loads(cleaned)
    except Exception:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(cleaned[start:end + 1])
            except Exception as e:
                raise ValueError(f"Failed to parse JSON output from Ollama. Raw output:\n{raw}\n\nParse error: {e}")
        else:
            raise ValueError(f"Failed to parse JSON output from Ollama. Raw output:\n{raw}")

    if "prompt" not in parsed:
        raise ValueError(f"Ollama JSON missing required 'prompt' field. Parsed JSON:\n{parsed}")

    return parsed if include_rationale else parsed["prompt"]
