import os
import time
import logging
import json
import re
import threading
import collections
from typing import Any, Dict, Optional

from anthropic import (
    Anthropic,
    APIError,
    APIConnectionError,
    RateLimitError,
    APIStatusError,
)

# Initialize Anthropic client with API key from environment
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("Warning: ANTHROPIC_API_KEY not found in environment variables")
    client = None
else:
    client = Anthropic(api_key=api_key)

# Model: claude-sonnet-4-5 (balanced); alternatives: claude-haiku-4-5 (fast), claude-opus-4-5 (most capable)
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_RETRIES = 3
BACKOFF_SECS = 2
DEFAULT_MAX_TOKENS = 8192

# ---------------------------------------------------------------------------
# Token-rate limiter — sliding window, thread-safe
# ---------------------------------------------------------------------------
_TPM_LIMIT = 50_000   # tokens per minute hard cap
_TPM_WINDOW = 60.0    # seconds in the sliding window
_tpm_lock = threading.Lock()
_tpm_log: collections.deque = collections.deque()  # (timestamp, tokens) pairs


def _tpm_acquire(tokens: int) -> None:
    """
    Block until `tokens` can be consumed without exceeding _TPM_LIMIT.
    Sleeps automatically until capacity is available in the sliding window.
    """
    while True:
        with _tpm_lock:
            now = time.monotonic()
            # Evict entries older than the sliding window
            while _tpm_log and _tpm_log[0][0] <= now - _TPM_WINDOW:
                _tpm_log.popleft()
            used = sum(t for _, t in _tpm_log)
            if used + tokens <= _TPM_LIMIT:
                _tpm_log.append((now, tokens))
                return
            # Sleep until the oldest entry expires and frees up capacity
            oldest_ts = _tpm_log[0][0]
            sleep_for = max(0.05, (oldest_ts + _TPM_WINDOW) - now + 0.05)

        logging.info(
            f"[TPM] Window full ({used}/{_TPM_LIMIT} tokens used). "
            f"Sleeping {sleep_for:.1f}s …"
        )
        time.sleep(sleep_for)


def reinitialize_claude_client():
    """
    Reinitialize the Anthropic client with the current environment variables.
    This is useful when the API key is updated through the web interface.
    """
    global client
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not found in environment variables")
        client = None
    else:
        client = Anthropic(api_key=api_key)
        print("Claude client reinitialized successfully")


def _retryable_claude_call(
    *,
    system: str = "",
    user: str = "",
    temperature: float = 0.3,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Wrapper that retries transient Anthropic errors.
    Acquires token budget via the sliding-window TPM limiter before each attempt.
    Always returns the raw text string; never raises upwards.
    """
    if not client:
        logging.error(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )
        return ""

    messages = [{"role": "user", "content": user}]
    for attempt in range(MAX_RETRIES):
        try:
            # Reserve tokens before making the call.
            # max_tokens is a conservative upper-bound; actual usage is usually lower.
            _tpm_acquire(max_tokens)

            response = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=max_tokens,
                system=system if system else None,
                messages=messages,
                temperature=temperature,
            )
            if response.content and len(response.content) > 0:
                return (response.content[0].text or "").strip()
            return ""
        except (RateLimitError, APIConnectionError) as e:
            logging.warning(f"[Claude attempt {attempt+1}/{MAX_RETRIES}] {e}")
            time.sleep(BACKOFF_SECS * (2 ** attempt))
        except (APIStatusError, APIError) as e:
            logging.warning(f"[Claude attempt {attempt+1}/{MAX_RETRIES}] {e}")
            time.sleep(BACKOFF_SECS * (2 ** attempt))
        except Exception as e:
            logging.exception(f"[Claude fatal] {e}")
            break
    return ""


def determine_question_validity_claude(query, DETERMINE_QUESTION_VALIDITY_PROMPT):
    """
    Claude implementation for determining question validity.
    """
    if not client:
        raise ValueError(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )
    return _retryable_claude_call(
        system=DETERMINE_QUESTION_VALIDITY_PROMPT,
        user=query,
        temperature=0.2,
    ).strip() or ""


def query_generation_claude(
    query, GENERAL_QUERY_PROMPT, QUERY_CONTENTION_PROMPT, QUERY_CONTENTION_ENABLED
):
    """
    Claude implementation for query generation.
    """
    if not client:
        raise ValueError(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )

    general_query = _retryable_claude_call(
        system=GENERAL_QUERY_PROMPT,
        user=query,
        temperature=0.7,
    ).strip()

    if QUERY_CONTENTION_ENABLED:
        query_contention = _retryable_claude_call(
            system=QUERY_CONTENTION_PROMPT,
            user=query,
            temperature=0.6,
        ).strip()
        return general_query, query_contention
    else:
        return general_query, "Query contention disabled"


def get_article_type_claude(abstract, ARTICLE_TYPE_PROMPT):
    """
    Claude implementation for determining article type.
    """
    if not client:
        raise ValueError(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )
    raw = _retryable_claude_call(
        system=ARTICLE_TYPE_PROMPT,
        user=f"Abstract: {abstract}",
        temperature=0.1,
    )
    return raw.strip().lower()


def generate_content_from_pdf_claude(
    pdf_text,
    content_type="abstract",
    publication_type="study",
    ABSTRACT_EXTRACTION_PROMPT=None,
    REVIEW_SUMMARY_PROMPT=None,
    STUDY_SUMMARY_PROMPT=None,
):
    """
    Claude implementation for generating content from PDF.
    """
    if not client:
        raise ValueError(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )

    if content_type == "abstract":
        prompt = ABSTRACT_EXTRACTION_PROMPT
    elif content_type == "summary":
        prompt = (
            REVIEW_SUMMARY_PROMPT
            if publication_type == "review"
            else STUDY_SUMMARY_PROMPT
        )
    else:
        raise ValueError("Invalid content_type. Choose 'abstract' or 'summary'.")

    return _retryable_claude_call(
        system=prompt,
        user=f"Paper: {pdf_text}",
        temperature=0.6,
    ).strip()


def section_match_claude(list_of_strings, RELEVANT_SECTIONS_PROMPT):
    """
    Claude implementation for section matching.
    """
    if not client:
        raise ValueError(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )
    list_of_strings_str = ", ".join(list_of_strings)
    return _retryable_claude_call(
        system=RELEVANT_SECTIONS_PROMPT,
        user=list_of_strings_str,
        temperature=0.1,
    ).strip()


def generate_final_response_claude(
    all_relevant_articles, query, FINAL_RESPONSE_PROMPT, DISCLAIMER_TEXT
):
    """
    Claude implementation for generating final response.
    """
    if not client:
        raise ValueError(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )
    user_content = f"""
Evidence and Claims: {all_relevant_articles}
User Question: {query}
"""
    output = _retryable_claude_call(
        system=FINAL_RESPONSE_PROMPT,
        user=user_content.strip(),
        temperature=0.5,
        max_tokens=16384,
    )
    return f"{output}\n\n{DISCLAIMER_TEXT}"


def generate_code_from_content_claude(
    article_content,
    type,
    system_prompt_function_generator_list_search,
    system_prompt_function_generator_id_search,
):
    """
    Claude implementation for generating code from content.
    """
    if not client:
        raise ValueError(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )
    try:
        if type == "list_search":
            system_prompt = system_prompt_function_generator_list_search
        elif type == "id_search":
            system_prompt = system_prompt_function_generator_id_search
        else:
            system_prompt = system_prompt_function_generator_list_search
        return _retryable_claude_call(
            system=system_prompt,
            user=f"Code/: {article_content}",
            temperature=0.6,
        ).strip() or None
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None


def generate_prompt_from_content_claude(
    article_content,
    prompt_type,
    system_prompts,
    include_rationale=False,
):
    """
    Claude implementation for generating a domain-specific prompt with optional rationale.
    Mirrors OpenAI/Gemini logic: JSON output with prompt and optional rationale.
    """
    if not client:
        raise ValueError(
            "Claude client not initialized. Please check your ANTHROPIC_API_KEY in the environment variables."
        )

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

    system_instruction = f"""
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
3. After composing the prompt, run a 1-line self-check that verifies format preserved, output is only the JSON object, and prompt follows domain constraints. If any check fails, revise and produce the corrected JSON.

Now read the user-supplied DOMAIN CONTENT and generate the JSON described above.
"""

    user_message = f"""
<DOMAIN_CONTENT>
{article_content.strip()}
</DOMAIN_CONTENT>

Return ONLY the JSON described in the system instructions.
"""

    raw = _retryable_claude_call(
        system=system_instruction,
        user=user_message.strip(),
        temperature=0.2,
        max_tokens=8192,
    )

    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE
    ).strip()
    parsed = None
    try:
        parsed = json.loads(cleaned)
    except Exception:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(cleaned[start : end + 1])
            except Exception as e:
                raise ValueError(
                    f"Failed to parse JSON output from LLM. Raw output:\n{raw}\n\nParse error: {e}"
                )
        else:
            raise ValueError(f"Failed to parse JSON output from LLM. Raw output:\n{raw}")

    if "prompt" not in parsed:
        raise ValueError(
            f"LLM JSON missing required 'prompt' field. Parsed JSON:\n{parsed}"
        )

    if include_rationale:
        return parsed
    return parsed["prompt"]
