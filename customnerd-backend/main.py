from helper_functions import *
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, Query, Form, File
from fastapi.responses import StreamingResponse, Response
from starlette.responses import JSONResponse

import asyncio
from sse_starlette.sse import EventSourceResponse
from concurrent.futures import ThreadPoolExecutor
import math
import uuid
import json
from urllib.parse import unquote
import time

from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from helper_functions import * 
import heapq
import json
import json5  

import logging
import os
import shutil

#Sim search
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from collections import defaultdict
from openai_prompts import *

logging.basicConfig(level=logging.INFO)

# Global variable to track missing modules
missing_modules = {}
failed_imports = {}

# Global variable to track all warnings (modules, API keys, etc.)
all_warnings = {}

def safe_import_module(module_name, import_statement=None, description=None):
    """
    Safely import a module and track failures.
    
    Parameters:
    - module_name (str): Name of the module to import
    - import_statement (str): Optional custom import statement (e.g., "from X import *")
    - description (str): Optional description of what the module is used for
    
    Returns:
    - bool: True if import succeeded, False otherwise
    """
    try:
        if import_statement:
            # Execute custom import statement
            exec(import_statement, globals())
        else:
            # Standard import
            __import__(module_name)
        
        if module_name in missing_modules:
            del missing_modules[module_name]
        if module_name in failed_imports:
            del failed_imports[module_name]
        return True
    except ModuleNotFoundError as e:
        error_msg = str(e)
        missing_modules[module_name] = {
            "error": error_msg,
            "description": description or f"Module {module_name}",
            "module_name": error_msg.split("'")[1] if "'" in error_msg else module_name
        }
        failed_imports[module_name] = error_msg
        logging.error(f"⚠️ MODULE NOT FOUND: {module_name}")
        logging.error(f"   Error: {error_msg}")
        if description:
            logging.error(f"   Description: {description}")
        logging.error(f"   Application will continue, but functionality may be limited.")
        logging.error(f"   To install: pip install {missing_modules[module_name]['module_name']}")
        return False
    except Exception as e:
        error_msg = str(e)
        missing_modules[module_name] = {
            "error": error_msg,
            "description": description or f"Module {module_name}",
            "module_name": module_name
        }
        failed_imports[module_name] = error_msg
        logging.error(f"⚠️ IMPORT ERROR: {module_name}")
        logging.error(f"   Error: {error_msg}")
        if description:
            logging.error(f"   Description: {description}")
        logging.error(f"   Application will continue, but functionality may be limited.")
        return False

# Safely import user modules
safe_import_module("user_list_search", "from user_list_search import *", "ID-specific search functionality")
safe_import_module("user_search_apis", "from user_search_apis import *", "Normal search API functionality")

def check_missing_api_keys():
    """
    Check for missing API keys and add them to the warnings system.
    """
    import os
    from dotenv import load_dotenv
    load_dotenv('variables.env', override=True)
    
    # Get current LLM preference
    llm_preference = os.getenv('LLM', 'OpenAI').strip('"').strip()
    
    # Check required API keys based on LLM preference
    if llm_preference.lower() == 'gemini':
        gemini_key = os.getenv('GEMINI_API_KEY', '').strip('"').strip()
        if not gemini_key or gemini_key == '':
            all_warnings['GEMINI_API_KEY'] = {
                "type": "missing_api_key",
                "description": "Gemini API Key",
                "message": "GEMINI_API_KEY not found in environment variables",
                "solution": "Add GEMINI_API_KEY to variables.env file"
            }
        elif 'GEMINI_API_KEY' in all_warnings:
            del all_warnings['GEMINI_API_KEY']
    elif llm_preference.lower() == 'claude':
        anthropic_key = os.getenv('ANTHROPIC_API_KEY', '').strip('"').strip()
        if not anthropic_key or anthropic_key == '':
            all_warnings['ANTHROPIC_API_KEY'] = {
                "type": "missing_api_key",
                "description": "Anthropic API Key",
                "message": "ANTHROPIC_API_KEY not found in environment variables",
                "solution": "Add ANTHROPIC_API_KEY to variables.env file"
            }
        elif 'ANTHROPIC_API_KEY' in all_warnings:
            del all_warnings['ANTHROPIC_API_KEY']
    elif llm_preference.lower() == 'ollama':
        # Ollama runs locally — no API key required. Optionally warn if base URL looks unreachable.
        for key in ('OPENAI_API_KEY', 'GEMINI_API_KEY', 'ANTHROPIC_API_KEY'):
            if key in all_warnings and all_warnings[key].get('type') == 'missing_api_key':
                del all_warnings[key]
        ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').strip('"').strip()
        if not ollama_base_url:
            all_warnings['OLLAMA_BASE_URL'] = {
                "type": "missing_api_key",
                "description": "Ollama Base URL",
                "message": "OLLAMA_BASE_URL is not set; defaulting to http://localhost:11434",
                "solution": "Add OLLAMA_BASE_URL=http://localhost:11434 to variables.env, or leave unset for default"
            }
        elif 'OLLAMA_BASE_URL' in all_warnings:
            del all_warnings['OLLAMA_BASE_URL']
    else:
        openai_key = os.getenv('OPENAI_API_KEY', '').strip('"').strip()
        if not openai_key or openai_key == '':
            all_warnings['OPENAI_API_KEY'] = {
                "type": "missing_api_key",
                "description": "OpenAI API Key",
                "message": "OPENAI_API_KEY not found in environment variables",
                "solution": "Add OPENAI_API_KEY to variables.env file"
            }
        elif 'OPENAI_API_KEY' in all_warnings:
            del all_warnings['OPENAI_API_KEY']
    
    # Check for other optional but commonly used API keys
    optional_keys = {
        'ENTREZ_EMAIL': 'Entrez Email (required for PubMed)'
    }
    
    for key, description in optional_keys.items():
        key_value = os.getenv(key, '').strip('"').strip()
        if not key_value or key_value == '':
            all_warnings[key] = {
                "type": "missing_api_key",
                "description": description,
                "message": f"{key} not found in environment variables",
                "solution": f"Add {key} to variables.env file"
            }
        elif key in all_warnings:
            del all_warnings[key]

# Check for missing API keys on startup
check_missing_api_keys()

update_queues = defaultdict(asyncio.Queue)
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Log missing modules and API keys on application startup."""
    # Update all_warnings with missing modules
    for module_name, info in missing_modules.items():
        all_warnings[f"module_{module_name}"] = {
            "type": "missing_module",
            "description": info.get('description', module_name),
            "message": info.get('error', 'Module not found'),
            "solution": f"pip install {info.get('module_name', module_name)}"
        }
    
    # Check API keys again on startup
    check_missing_api_keys()
    
    if all_warnings:
        logging.warning("=" * 60)
        logging.warning("⚠️  WARNINGS DETECTED")
        logging.warning("=" * 60)
        for warning_key, warning_info in all_warnings.items():
            logging.warning(f"{warning_info.get('description', warning_key)}: {warning_info.get('message', 'N/A')}")
            logging.warning(f"  Solution: {warning_info.get('solution', 'N/A')}")
            logging.warning("-" * 60)
        logging.warning("Application will continue running, but some features may be unavailable.")
        logging.warning("Use /check_missing_modules endpoint to get detailed information.")
        logging.warning("Use /fetch_hard_backup_config endpoint to perform a hard reset if needed.")
        logging.warning("=" * 60)
    else:
        logging.info("✅ All required modules and API keys are available.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔥 Allows all origins (for local dev only)
    allow_credentials=True,
    allow_methods=["*"],  # ✅ Allows all HTTP methods
    allow_headers=["*"],  # ✅ Allows all headers
)


executor = ThreadPoolExecutor()

# Create a global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def run_in_executor(func, *args):
    return loop.run_in_executor(executor, func, *args)

def refine_prompts(query_list):
    """
    Refines and cleans a list of queries based on user needs.
    
    Parameters:
    - query_list (list): List of queries to refine
    
    Returns:
    - refined_prompt_list (list): List of refined queries
    """
    try:
        # Check if clean_query.py exists and has clean_query function
        import clean_query
        if hasattr(clean_query, 'clean_query'):
            refined_queries = []
            for query in query_list:
                try:
                    refined_query = clean_query.clean_query(query)
                    refined_queries.append(refined_query)
                except Exception as e:
                    print(f"Error refining query '{query}': {str(e)}")
                    refined_queries.append(query)  # Use original query if refinement fails
            return refined_queries
        else:
            print("clean_query function not found in clean_query.py")
            return query_list
    except ImportError:
        print("clean_query.py not found, returning original queries")
        return query_list
    except Exception as e:
        print(f"Error in refine_prompts: {str(e)}")
        return query_list

@app.get("/")
async def root():
    logging.info("Root route accessed")
    return "Hello! Go to /docs!'"

@app.get("/health")
def health_check():
    """Health check endpoint that reports application status, missing modules, and all warnings."""
    # Update warnings
    check_missing_api_keys()
    for module_name, info in missing_modules.items():
        all_warnings[f"module_{module_name}"] = {
            "type": "missing_module",
            "description": info.get('description', module_name),
            "message": info.get('error', 'Module not found'),
            "solution": f"pip install {info.get('module_name', module_name)}"
        }
    
    status = "healthy" if not all_warnings else "degraded"
    return {
        "status": status,
        "missing_modules": missing_modules,
        "warnings": all_warnings,
        "message": "Application is running" if not all_warnings else f"Application is running but {len(all_warnings)} warning(s) detected"
    }

@app.get("/check_missing_modules")
async def check_missing_modules():
    """Endpoint to check for missing modules, API keys, and all warnings."""
    # Update warnings with current state
    check_missing_api_keys()
    
    # Update all_warnings with missing modules
    for module_name, info in missing_modules.items():
        all_warnings[f"module_{module_name}"] = {
            "type": "missing_module",
            "description": info.get('description', module_name),
            "message": info.get('error', 'Module not found'),
            "solution": f"pip install {info.get('module_name', module_name)}"
        }
    
    if not all_warnings:
        return {
            "status": "success",
            "message": "All required modules and API keys are available",
            "missing_modules": {},
            "warnings": {}
        }
    
    result = {
        "status": "warning",
        "message": f"{len(all_warnings)} warning(s) detected",
        "missing_modules": missing_modules,
        "warnings": all_warnings,
        "installation_commands": []
    }
    
    # Generate installation commands for modules
    for module_name, info in missing_modules.items():
        install_cmd = f"pip install {info['module_name']}"
        result["installation_commands"].append({
            "module": module_name,
            "command": install_cmd,
            "description": info.get("description", ""),
            "error": info.get("error", ""),
            "type": "missing_module"
        })
    
    # Add API key warnings
    for warning_key, warning_info in all_warnings.items():
        if warning_info.get("type") == "missing_api_key":
            result["installation_commands"].append({
                "module": warning_key,
                "command": warning_info.get("solution", ""),
                "description": warning_info.get("description", ""),
                "error": warning_info.get("message", ""),
                "type": "missing_api_key"
            })
    
    return result

@app.get("/fetch_clean_query")
async def fetch_clean_query():
    """Fetch the content of clean_query.py file"""
    try:
        import os
        clean_query_path = os.path.join(os.path.dirname(__file__), "clean_query.py")
        
        if os.path.exists(clean_query_path):
            with open(clean_query_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(content=content, media_type="text/plain")
        else:
            return Response(status_code=404, content="File not found")
    except Exception as e:
        return Response(status_code=500, content=f"Error reading file: {str(e)}")

@app.post("/save_clean_query")
async def save_clean_query(content: str = Form(...)):
    """Save content to clean_query.py file"""
    try:
        import os
        clean_query_path = os.path.join(os.path.dirname(__file__), "clean_query.py")
        
        with open(clean_query_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return {"status": "success", "message": "clean_query.py updated successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error saving file: {str(e)}"}




@app.get("/check_valid/{question:str}")
async def check_valid(question:str):
   question_validity = determine_question_validity(question)
   if question_validity == 'False - Meal Plan/Recipe':
    final_output = ("I'm sorry, I cannot help you with this question. For any questions or advice around meal planning or recipes, please speak to a registered dietitian or registered dietitian nutritionist.\n"
                    "To find a local expert near you, use this website: https://www.eatright.org/find-a-nutrition-expert.")
    print(final_output)
   elif question_validity == 'False - Animal':
    final_output = ("I'm sorry, I cannot help you with this question. For any questions regarding an animal, please speak to a veterinarian.\n"
                   "To find a local expert near you, use this website: https://vetlocator.com/.")
   else:
    final_output = "good"
   return {"response" : final_output}

@app.get("/sse")
async def sse(session_id: str = Query(default=None)):
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    return EventSourceResponse(event_generator(session_id))

async def event_generator(session_id: str):
    queue = asyncio.Queue()
    update_queues[session_id] = queue
    try:
        while True:
            data = await queue.get()
            if isinstance(data, dict) and "final_output" in data:
                yield {"event": "message", "data": json.dumps(data)}
                break
            else:
                yield {"event": "message", "data": json.dumps({"update": data})}
    finally:
        del update_queues[session_id]

# Define the request model
class DetailedCombinedQueryRequest(BaseModel):
    user_query: str
    search_pubmed: bool
    search_pmid: bool
    pmids: Optional[str] = []
    search_pdf: bool

class ArticleInput(BaseModel):
    article_content: str

@app.post("/process_detailed_combined_query")
async def process_detailed_combined_query(
    background_tasks: BackgroundTasks,
     user_query: str = Form(...),  # Use Form for form fields
    search_pubmed: bool = Form(...),
    search_pmid: bool = Form(...),
    pmids: Optional[str] = Form(None),  # Optional, sent as a string (which we'll parse)
    search_pdf: bool = Form(...),
    files: List[UploadFile] = File(None)  # Handle files
):
    input_text = user_query
    search_db = search_pubmed
    search_id = search_pmid
    id_list = pmids
    search_doc = search_pdf
    input_files = files

    unique_id = str(uuid.uuid4())
    print(f"Session ID: {unique_id}")
    # Manually create the queue for this session ID
    update_queues[unique_id] = asyncio.Queue()

    # Parse the ID list string back into a list if provided
    parsed_ids = json.loads(id_list) if id_list else []

    # Process the uploaded files
    input_files = input_files if input_files else []
    file_metadata_list = []
    if search_doc and input_files:
        for file in input_files:
            file_content = await file.read()
            file_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "content": file_content
            }
            file_metadata_list.append(file_info)

    # Add the processing task to background tasks
    background_tasks.add_task(
        process_detailed_combined_logic,
        input_text,
        search_db,
        search_id,
        parsed_ids,
        search_doc,
        file_metadata_list,
        unique_id
    )

    return JSONResponse({"session_id": unique_id})

def process_detailed_combined_logic(input_text, search_db, search_id, id_list, search_doc, file_metadata_list: List[dict], unique_id):
    loop.run_until_complete(send_update(unique_id, "Creating a procedure..."))
    id_set = set()
    start_time = time.time()  # Start runtime tracking
    # Step 1: Collect Database Articles
    start_api = time.time()
    db_articles = []
    id_articles = []
    if search_db:
        print("Searching Article Database...")
        loop.run_until_complete(send_update(unique_id, "Generating Search Queries..."))
        _, _, query_list = query_generation(input_text)
        print("Generated Article Database queries:", query_list)
        # Refine queries using the refine_prompts function (only if enabled)
        # Check if query cleaning is enabled in the frontend configuration
        try:
            with open('../customnerd-website/user_env.js', 'r', encoding='utf-8') as file:
                frontend_content = file.read()
            
            # Extract the window.env object content
            start_idx = frontend_content.find('{')
            end_idx = frontend_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                config_str = frontend_content[start_idx:end_idx]
                import json5
                frontend_config = json5.loads(config_str)
                
                # Check if query cleaning is enabled
                query_cleaning_enabled = frontend_config.get('USER_FLOW', {}).get('query_cleaning', {}).get('visible', False)
                print("Query cleaning enabled:", query_cleaning_enabled)
                if query_cleaning_enabled:
                    # Check if clean_query.py file exists
                    clean_query_path = os.path.join(os.path.dirname(__file__), 'clean_query.py')
                    if os.path.exists(clean_query_path):
                        try:
                            import clean_query
                            query_list = clean_query.clean_query(query_list)
                            print("Refined queries:", query_list)
                        except Exception as import_error:
                            print(f"Error importing or using clean_query module: {import_error}, using original queries")
                    else:
                        print("clean_query.py file not found, using original queries")
                else:
                    print("Query refinement is disabled, using original queries")
            else:
                print("Could not parse frontend config, using original queries")
        except Exception as e:
            print(f"Error reading frontend config: {e}, using original queries")
        
        loop.run_until_complete(send_update(unique_id, "5 search queries generated. Collecting articles from Article Database..."))
        try:
            collect_articles_func = globals().get('collect_articles')
            if collect_articles_func and callable(collect_articles_func):
                db_articles = collect_articles_func(query_list)
            else:
                raise NameError("collect_articles function is not available")
        except (NameError, AttributeError) as e:
            error_msg = f"Error: collect_articles function is not available. Missing module: {missing_modules.get('user_search_apis', {}).get('module_name', 'unknown')}"
            logging.error(error_msg)
            loop.run_until_complete(send_update(unique_id, f"ERROR: {error_msg}. Please check /check_missing_modules for details."))
            db_articles = []
        except Exception as e:
            error_msg = f"Error collecting articles: {str(e)}"
            logging.error(error_msg)
            loop.run_until_complete(send_update(unique_id, f"ERROR: {error_msg}"))
            db_articles = []
        
        if search_id and id_list and db_articles:
            try:
                db_articles = [item for item in db_articles if item.get('MedlineCitation', {}).get('PMID') not in id_list]
            except (KeyError, AttributeError):
                # If structure is different, skip filtering
                pass
        print(f"Collected {len(db_articles)} articles from Database.")
        loop.run_until_complete(send_update(unique_id, f"Collected {len(db_articles)} articles..."))

    end_api = time.time()

    # Step 2: Fetch Additional Articles via IDs
    if search_id and id_list:
        loop.run_until_complete(send_update(unique_id, "Fetching articles by user passed IDs..."))
        try:
            fetch_articles_func = globals().get('fetch_articles_by_ids')
            if fetch_articles_func and callable(fetch_articles_func):
                id_articles = fetch_articles_func(list(id_list))
            else:
                raise NameError("fetch_articles_by_ids function is not available")
        except (NameError, AttributeError) as e:
            error_msg = f"Error: fetch_articles_by_ids function is not available. Missing module: {missing_modules.get('user_list_search', {}).get('module_name', 'unknown')}"
            logging.error(error_msg)
            loop.run_until_complete(send_update(unique_id, f"ERROR: {error_msg}. Please check /check_missing_modules for details."))
            id_articles = []
        except Exception as e:
            error_msg = f"Error fetching articles by IDs: {str(e)}"
            logging.error(error_msg)
            loop.run_until_complete(send_update(unique_id, f"ERROR: {error_msg}"))
            id_articles = []
        else:
            id_set.update(id_list)
            loop.run_until_complete(send_update(unique_id, f"Fetched {len(id_articles)} articles by user passed IDs..."))



    #Step 2.5: Process Database Articles
    if db_articles:
        # Create async wrapper for concurrent function with progress updates
        async def process_db_articles_with_progress():
            # Start the processing task
            processing_task = asyncio.get_event_loop().run_in_executor(
                None, concurrent_organize_database_articles, db_articles, input_text
            )
            
            # Progress messages to send during processing
            progress_messages = [
                "Looking at each article in detail to assess relevance...",
                "Analyzing article content and extracting key insights...",
                "Categorizing articles and seeing the details..."
            ]
            
            # Send progress updates while processing
            for i, message in enumerate(progress_messages):
                if not processing_task.done():
                    await send_update(unique_id, message)
                    # Wait 20 seconds between messages
                    await asyncio.sleep(20)
                else:
                    break
            
            # Wait for the processing to complete
            result = await processing_task
            await send_update(unique_id, "Looking into the articles in depth...")
            return result
        
        db_articles = loop.run_until_complete(process_db_articles_with_progress())
        print("Database Articles Processed:", db_articles)


    # Step 3: Process Documents (if enabled)¸
    doc_articles = []
    if search_doc:
        doc_articles = process_pdf_articles_parallel(file_metadata_list, unique_id)
        print("Document Articles Processed:", doc_articles)

    # Step 3.5: Process Reference Articles
    db_articles = process_articles_by_url(db_articles)
    

    # Step 4: Relevance Classification
    start_relevance_time = time.time()
    print("Classifying relevance of articles...")
    relevant_items, irrelevant_items = concurrent_relevance_classification(db_articles, input_text)
    end_relevance_time = time.time()
    print(f"Classified {len(relevant_items)} relevant, {len(irrelevant_items)} irrelevant articles.")
    relevant_items.extend(id_articles)

    if len(relevant_items)>0:
        loop.run_until_complete(send_update(unique_id, f"Classified {len(relevant_items)} relevant articles."))
    else:
        loop.run_until_complete(send_update(unique_id, f"Classified relevant articles. "))


    if search_doc and doc_articles:
        relevant_items.extend(doc_articles)

    # Step 6: Generate Final Response
    all_relevant_items = relevant_items
    # Write all relevant items to a file for debugging/inspection
    print(f"Synthesizing final response for {len(all_relevant_items)} articles...")
    loop.run_until_complete(send_update(unique_id, f"Synthesizing final response..."))
    all_relevant_items = trim_relevant_articles_by_token_limit(all_relevant_items, input_text)
    final_result = generate_final_response(all_relevant_items, input_text)
    loop.run_until_complete(send_update(unique_id, "Generated final response..."))
    print("Passing all relevant items to collect_referenced_articles...")
    citation_generation = print_referenced_articles(final_result, all_relevant_items)
    print("Citation Generation:", citation_generation)
    # Step 9: Validate Citations Output
    try:
        result_object = {
            "end_output": final_result,
            "citations_obj": replace_invalid_values(citation_generation)
        }
    except Exception as e:
        print(f"Error in result_object creation: {str(e)}")
        result_object = {
            "end_output": final_result,
            "citations_obj": ["Not Found"],
        }

    loop.run_until_complete(send_update(unique_id, result_object))

    # Append result to historical_answer.json if chat history is enabled in frontend config
    try:
        chat_history_enabled = False
        try:
            with open('../customnerd-website/user_env.js', 'r', encoding='utf-8') as file:
                frontend_content = file.read()
            start_idx = frontend_content.find('{')
            end_idx = frontend_content.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                config_str = frontend_content[start_idx:end_idx]
                frontend_config = json5.loads(config_str)
                chat_history_enabled = frontend_config.get('USER_FLOW', {}).get('chat_history', {}).get('visible', False)
        except Exception as e:
            print(f"Error reading frontend config for chat_history: {e}")

        if chat_history_enabled:
            history_path = "historical_answer.json"
            history_data = []
            if os.path.exists(history_path) and os.path.getsize(history_path) > 0:
                with open(history_path, 'r', encoding='utf-8') as f:
                    try:
                        history_data = json.load(f)
                        if not isinstance(history_data, list):
                            history_data = [history_data]
                    except Exception:
                        history_data = []

            entry = {
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "session_id": unique_id,
                "input_text": input_text,
                "result": result_object
            }
            history_data.append(entry)
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Could not append to historical_answer.json: {e}")

    return result_object


def process_pdf_articles_parallel(files_info, session_id, max_threads=5):
    """
    Process multiple PDF articles in parallel with dynamic thread allocation.

    Args:
        files_info (List[dict]): List of files with metadata and content.
        session_id (str): Session ID for updates.
        max_threads (int): Maximum number of threads to use (default is 5).

    Returns:
        List[dict]: List of all formatted articles extracted from PDFs.
    """
    # Update the session to indicate the start of parallel processing
    loop.run_until_complete(send_update(session_id, "Processing PDF articles..."))

    pdf_articles = []

    # Determine the number of threads to use
    num_threads = min(len(files_info), max_threads)

    with ThreadPoolExecutor(max_workers=max(num_threads,1)) as executor:
        # Submit all PDF processing tasks to the executor
        futures = {
            executor.submit(process_pdf_article, file_info, idx + 1): file_info['filename']
            for idx, file_info in enumerate(files_info)
        }

        # As each task completes, collect the result
        for future in as_completed(futures):
            filename = futures[future]
            try:
                result = future.result()
                if result:
                    pdf_articles.append(result)
                    print(f"Successfully processed {filename}.")
                else:
                    print(f"No data returned for {filename}.")
            except Exception as e:
                print(f"Error processing file {filename}: {str(e)}")

    # Update the session to indicate completion of parallel processing
    loop.run_until_complete(send_update(session_id, f"Processed {len(pdf_articles)+1} PDF article(s)..."))
    print("PDF Articles:", pdf_articles)
    return pdf_articles

@app.get("/fetch_frontend_config")
async def fetch_frontend_config():
    try:
        # Read the user_env.js file
        with open('../customnerd-website/user_env.js', 'r', encoding='utf-8') as file:
            content = file.read()

        # Extract the window.env object content
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("Could not find valid JSON object in config file")

        config_str = content[start_idx:end_idx]

        config = json5.loads(config_str)
        return config

    except Exception as e:
        logging.error(f"Error fetching frontend config: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch frontend configuration")

@app.post("/update_frontend_config")
async def update_frontend_config(
    config: str = Form(...),
    logo_file: UploadFile = File(None)
):
    try:
        # Parse the config JSON string
        config_dict = json.loads(config)
        
        # Handle logo file if provided
        if logo_file:
            # Create assets directory if it doesn't exist
            os.makedirs('../customnerd-website/assets', exist_ok=True)
            
            # Save the uploaded file
            file_location = f"../customnerd-website/assets/customnerd_logo{os.path.splitext(logo_file.filename)[1]}"
            with open(file_location, "wb+") as file_object:
                file_object.write(await logo_file.read())
            
            # Update the logo path in the config
            config_dict['FRONTEND_FLOW']['SITE_LOGO'] = f"assets/customnerd_logo{os.path.splitext(logo_file.filename)[1]}"
        elif 'FRONTEND_FLOW' in config_dict and 'SITE_LOGO' not in config_dict['FRONTEND_FLOW']:
            # If no logo is provided and no existing logo path, set default
            # Check if customnerd_logo.png exists, otherwise use fallback
            if os.path.exists("../customnerd-website/assets/customnerd_logo.png"):
                config_dict['FRONTEND_FLOW']['SITE_LOGO'] = "assets/customnerd_logo.png"
            else:
                config_dict['FRONTEND_FLOW']['SITE_LOGO'] = "assets/custom_nerd_default_logo.png"

        # Format the new config as a JavaScript object
        config_str = json.dumps(config_dict, indent=4, ensure_ascii=False)
        new_content = f"window.env = {config_str};"

        # Write the updated content back to the file
        with open('../customnerd-website/user_env.js', 'w', encoding='utf-8') as file:
            file.write(new_content)

        print(f"Configuration updated successfully: {config_dict}")
        return {"status": "success", "message": "Configuration updated successfully"}

    except Exception as e:
        logging.error(f"Error updating config: {str(e)}")
        print(f"Error updating config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not update configuration: {str(e)}")

@app.get("/fetch_env_config")
async def fetch_env_config():
    try:
        # Read the variables.env file
        with open('variables.env', 'r', encoding='utf-8') as file:
            content = file.readlines()

        # Parse the content into a dictionary
        config = {}
        optional_keys = []
        
        for line in content:
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle malformed lines by finding the first '=' sign
                if '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip().strip('"')
                        config[key] = value
                        
                        # Mark all API keys except OPENAI_API_KEY as optional
                        if key != 'OPENAI_API_KEY':
                            optional_keys.append(key)

        # Add metadata about which keys are optional
        config['_optional_keys'] = optional_keys
        config['_required_keys'] = ['OPENAI_API_KEY']

        return config

    except Exception as e:
        logging.error(f"Error fetching env config: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch env configuration")


@app.post("/update_env_config")
async def update_env_config(config: dict):
    try:
        # Remove metadata keys from the input config
        config = {k: v for k, v in config.items() if not k.startswith('_')}
        
        # Trim all the keys of white space in the input config
        trimmed_config = {key.strip(): value for key, value in config.items()}
        
        # Write the updated content directly to the variables.env file
        with open('variables.env', 'w', encoding='utf-8') as file:
            for key, value in trimmed_config.items():
                file.write(f'{key}="{value}"\n')
        
        # Reload environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv('variables.env', override=True)
            
            # Reinitialize OpenAI client
            from openai_executions import reinitialize_openai_client
            reinitialize_openai_client()
            
            # Also reinitialize Gemini client if available
            try:
                from gemini_executions import reinitialize_gemini_client
                reinitialize_gemini_client()
            except ImportError:
                print("Gemini client not available for reinitialization")
            # Reinitialize Claude client if available
            try:
                from claude_executions import reinitialize_claude_client
                reinitialize_claude_client()
            except ImportError:
                print("Claude client not available for reinitialization")
            # Reinitialize Ollama client if available
            try:
                from ollama_executions import reinitialize_ollama_client
                reinitialize_ollama_client()
            except ImportError:
                print("Ollama client not available for reinitialization")
            
            # Re-check for missing API keys after update
            check_missing_api_keys()
        except Exception as reload_error:
            print(f"Warning: Could not reload environment variables: {reload_error}")
        
        return {"status": "success", "message": "Environment configuration updated successfully"}

    except Exception as e:
        logging.error(f"Error updating environment config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not update environment configuration: {str(e)}")


@app.post("/generate_code_endpoint")
async def generate_code_endpoint(input: ArticleInput, type: str = Query(...)):
    """
    API endpoint that takes article content and returns a summary using OpenAI's GPT-4 model.
    
    Parameters:
    - article_content (str): The content of the article to summarize
    - type (str): The type of code generation (list_search or id_search)
    
    Returns:
    - dict: Contains the generated summary or error message
    """
    try:
        article_content = input.article_content
        print(f"Generating code with content length: {len(article_content)} and type: {type}")
        # Generate the summary using the OpenAI client
        summary = generate_code_from_content(article_content, type)
        # Check if summary contains Python code blocks
        if "```python" in summary:
            # Find the first Python code block
            start_idx = summary.find("```python")
            # Find the last closing code block
            end_idx = summary.rfind("```")
            if start_idx != -1 and end_idx != -1:
                # Extract only the code between the markers
                summary = summary[start_idx + 9:end_idx].strip()
        if summary:
            return {"status": "success", "summary": summary}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
            
    except Exception as e:
        logging.error(f"Error generating article summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not generate summary: {str(e)}")

class PromptInput(BaseModel):
    article_content: str
    prompt_type: str

@app.post("/generate_prompt_endpoint")
async def generate_prompt_endpoint(input: PromptInput):
    """
    API endpoint that takes article content and prompt type to generate a specialized prompt.
    
    Parameters:
    - article_content (str): The content of the article to generate a prompt from
    - prompt_type (str): The type of prompt to generate. Can be one of:
        - "final_response": For generating final response to user query
        - "relevant_sections": For identifying relevant sections in articles
        - "study_summary": For summarizing study-type articles
        - "review_summary": For summarizing review-type articles
        - "question_validity": For determining if a question is valid
        - "general_query": For generating general PubMed queries
        - "query_contention": For generating queries around points of contention
        - "relevance": For determining article relevance
        - "article_type": For determining if article is study or review
        - "abstract": For extracting structured abstract details
    
    Returns:
    - dict: Contains the generated prompt or error message
    """
    try:

        article_content = input.article_content
        prompt_type = input.prompt_type
        print(f"Generating prompt for {prompt_type} with content length: {len(article_content)}")
        # Map prompt types to their corresponding constants
        prompt_type_mapping = {
            "final_response": FINAL_RESPONSE_PROMPT,
            "relevant_sections": RELEVANT_SECTIONS_PROMPT,
            "study_summary": STUDY_SUMMARY_PROMPT,
            "review_summary": REVIEW_SUMMARY_PROMPT,
            "question_validity": DETERMINE_QUESTION_VALIDITY_PROMPT,
            "general_query": GENERAL_QUERY_PROMPT,
            "query_contention": QUERY_CONTENTION_PROMPT,
            "relevance": RELEVANCE_CLASSIFIER_PROMPT,
            "article_type": ARTICLE_TYPE_PROMPT,
            "abstract": ABSTRACT_EXTRACTION_PROMPT
        }
        
        # Validate prompt type
        if prompt_type not in prompt_type_mapping:
            valid_types = list(prompt_type_mapping.keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid prompt type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Generate the prompt using the OpenAI client
        generated_prompt = generate_prompt_from_content(article_content, prompt_type)
        
        if generated_prompt:
            return {
                "status": "success", 
                "prompt": generated_prompt,
                "prompt_type": prompt_type,
                "base_prompt": prompt_type_mapping[prompt_type]
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate prompt")
            
    except Exception as e:
        logging.error(f"Error generating prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not generate prompt: {str(e)}")

@app.get("/fetch_prompts_config")
async def fetch_prompts_config():
    try:
        # Import prompts from openai_prompts.py
        from openai_prompts import (
            DETERMINE_QUESTION_VALIDITY_PROMPT,
            GENERAL_QUERY_PROMPT,
            QUERY_CONTENTION_PROMPT,
            RELEVANCE_CLASSIFIER_PROMPT,
            ARTICLE_TYPE_PROMPT,
            ABSTRACT_EXTRACTION_PROMPT,
            REVIEW_SUMMARY_PROMPT,
            STUDY_SUMMARY_PROMPT,
            RELEVANT_SECTIONS_PROMPT,
            FINAL_RESPONSE_PROMPT,
            DISCLAIMER_TEXT,
            disclaimer,
            QUERY_CONTENTION_ENABLED
        )
        
        # Create a JSON object with all the prompts
        config = {
            "DETERMINE_QUESTION_VALIDITY_PROMPT": DETERMINE_QUESTION_VALIDITY_PROMPT,
            "GENERAL_QUERY_PROMPT": GENERAL_QUERY_PROMPT,
            "QUERY_CONTENTION_PROMPT": QUERY_CONTENTION_PROMPT,
            "RELEVANCE_CLASSIFIER_PROMPT": RELEVANCE_CLASSIFIER_PROMPT,
            "ARTICLE_TYPE_PROMPT": ARTICLE_TYPE_PROMPT,
            "ABSTRACT_EXTRACTION_PROMPT": ABSTRACT_EXTRACTION_PROMPT,
            "REVIEW_SUMMARY_PROMPT": REVIEW_SUMMARY_PROMPT,
            "STUDY_SUMMARY_PROMPT": STUDY_SUMMARY_PROMPT,
            "RELEVANT_SECTIONS_PROMPT": RELEVANT_SECTIONS_PROMPT,
            "FINAL_RESPONSE_PROMPT": FINAL_RESPONSE_PROMPT,
            "DISCLAIMER_TEXT": DISCLAIMER_TEXT,
            "disclaimer": disclaimer,
            "QUERY_CONTENTION_ENABLED": QUERY_CONTENTION_ENABLED
        }
        
        return config

    except Exception as e:
        logging.error(f"Error fetching prompts config: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch prompts configuration")

@app.get("/fetch_backend_config")
async def fetch_backend_config():
    try:
        # Read the content of user_list_search.py and user_search_apis.py
        with open("user_list_search.py", "r", encoding="utf-8") as file:
            id_specific_search_content = file.read()
            
        with open("user_search_apis.py", "r", encoding="utf-8") as file:
            normal_search_content = file.read()
        
        # Read the content of clean_query.py
        try:
            with open("clean_query.py", "r", encoding="utf-8") as file:
                query_cleaning_content = file.read()
        except FileNotFoundError:
            query_cleaning_content = ""
        
        # Create a JSON object with the backend configuration
        config = {
            "normal_search": normal_search_content,
            "id_specific_search": id_specific_search_content,
            "query_cleaning": query_cleaning_content
        }
        
        return config

    except Exception as e:
        logging.error(f"Error fetching backend config: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch backend configuration")

@app.post("/update_backend_config")
async def update_backend_config(config_data: dict):
    try:
        # Update user_search_apis.py (Normal Search)
        if "normal_search" in config_data:
            with open("user_search_apis.py", "w", encoding="utf-8") as file:
                file.write(config_data["normal_search"])
        
        # Update user_list_search.py (ID Specific Search)
        if "id_specific_search" in config_data:
            with open("user_list_search.py", "w", encoding="utf-8") as file:
                file.write(config_data["id_specific_search"])
        
        # Update clean_query.py (Query Cleaning)
        if "query_cleaning" in config_data:
            with open("clean_query.py", "w", encoding="utf-8") as file:
                file.write(config_data["query_cleaning"])
                
        print(f"Backend configuration updated successfully")
        return {"status": "success", "message": "Backend configuration updated successfully"}

    except Exception as e:
        logging.error(f"Error updating backend config: {str(e)}")
        print(f"Error updating backend config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not update backend configuration: {str(e)}")

@app.post("/update_prompts_config")
async def update_prompts_config(config_data: dict):
    try:
        # Import the module to modify
        import openai_prompts
        
        # Update each prompt in the module
        for key, value in config_data.items():
            if hasattr(openai_prompts, key):
                setattr(openai_prompts, key, value)
        
        # Write the updated prompts back to the file
        with open("openai_prompts.py", "w") as f:
            for key, value in config_data.items():
                if isinstance(value, str):
                    # Format string values with proper escaping and triple quotes
                    f.write(f"{key} = '''{value}'''\n\n")
                elif isinstance(value, bool):
                    # Format boolean values
                    f.write(f"{key} = {value}\n\n")
        
        print(f"Prompts configuration updated successfully")
        return {"status": "success", "message": "Prompts configuration updated successfully"}

    except Exception as e:
        logging.error(f"Error updating prompts config: {str(e)}")
        print(f"Error updating prompts config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Could not update prompts configuration: {str(e)}")
    

@app.get("/fetch_hard_backup_config")
async def fetch_hard_backup_config():
    try:
        # Get base directory (parent of customnerd-backend) for cross-platform path handling
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(backend_dir)
        hard_backup_dir = os.path.join(backend_dir, "hard_backup")
        
        # Create assets directory if it doesn't exist
        website_assets_dir = os.path.join(base_dir, "customnerd-website", "assets")
        os.makedirs(website_assets_dir, exist_ok=True)
            
        # Read the content from hard_backup files
        with open(os.path.join(hard_backup_dir, "user_list_search_backup.py"), "r", encoding="utf-8") as file:
            backup_id_specific_search_content = file.read()
        with open(os.path.join(hard_backup_dir, "user_search_apis_backup.py"), "r", encoding="utf-8") as file:
            backup_normal_search_content = file.read()
        with open(os.path.join(hard_backup_dir, "openai_prompts_backup.py"), "r", encoding="utf-8") as file:
            backup_prompts_content = file.read()
        with open(os.path.join(hard_backup_dir, "variables.env"), "r", encoding="utf-8") as file:
            backup_env_content = file.read()
        with open(os.path.join(hard_backup_dir, "user_env_backup.js"), "r", encoding="utf-8") as file:
            backup_user_env_content = file.read()
            
        # Write the backup content to the main files
        with open(os.path.join(backend_dir, "user_list_search.py"), "w", encoding="utf-8") as file:
            file.write(backup_id_specific_search_content)
        with open(os.path.join(backend_dir, "user_search_apis.py"), "w", encoding="utf-8") as file:
            file.write(backup_normal_search_content)
        with open(os.path.join(backend_dir, "openai_prompts.py"), "w", encoding="utf-8") as file:
            file.write(backup_prompts_content)
        with open(os.path.join(backend_dir, "variables.env"), "w", encoding="utf-8") as file:
            file.write(backup_env_content)
        with open(os.path.join(base_dir, "customnerd-website", "user_env.js"), "w", encoding="utf-8") as file:
            file.write(backup_user_env_content)
            
        # Copy the logo file from hard_backup to assets directory
        try:
            logo_src = os.path.join(hard_backup_dir, "customnerd_logo.png")
            logo_dst = os.path.join(website_assets_dir, "customnerd_logo.png")
            if os.path.exists(logo_src):
                shutil.copy2(logo_src, logo_dst)
        except Exception as e:
            logging.warning(f"Could not copy logo file: {str(e)}")
        
        # Copy historical_answer.json from hard_backup to backend directory
        try:
            history_src = os.path.join(hard_backup_dir, "historical_answer.json")
            history_dst = os.path.join(backend_dir, "historical_answer.json")
            if os.path.exists(history_src):
                shutil.copy2(history_src, history_dst)
                logging.info("Copied historical_answer.json from hard backup")
            else:
                # If backup doesn't exist, create empty history
                with open(history_dst, 'w', encoding='utf-8') as hf:
                    json.dump([], hf, ensure_ascii=False, indent=2)
                logging.info("Created empty historical_answer.json (backup not found)")
        except Exception as e:
            logging.warning(f"Could not copy historical_answer.json: {str(e)}")
            # Best effort - create empty history if copy fails
            try:
                history_dst = os.path.join(backend_dir, "historical_answer.json")
                with open(history_dst, 'w', encoding='utf-8') as hf:
                    json.dump([], hf, ensure_ascii=False, indent=2)
            except Exception:
                pass
            
        return {
            "status": "success",
            "message": "Configuration restored from hard backup successfully"
        }
    except Exception as e:
        logging.error(f"Error restoring from hard backup: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not restore from hard backup: {str(e)}")
            
async def send_update(session_id, data):
    if session_id in update_queues:
        print("Sending update ",data," to session_id:", session_id)
        await update_queues[session_id].put(data)

def calculate_similarity(sentences, source_sentence):
    # Combine source sentence with the list of sentences
    all_sentences = sentences + [source_sentence]
    
    # Create the TF-IDF vectorizer and transform the sentences
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_sentences)
    
    # Calculate the cosine similarity between the source sentence and all other sentences
    cosine_similarities = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1]).flatten()
    
    # Combine the similarity scores with the sentences
    similarity_scores = [(score, sentence) for score, sentence in zip(cosine_similarities, sentences)]
    
    return similarity_scores

@app.post("/save_state")
async def save_state(state_name: str = Form(...)):
    try:
        # Get base directory (parent of customnerd-backend)
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(backend_dir)
        
        # Use os.path.join for cross-platform path handling
        state_dir = os.path.join(backend_dir, "saved_states", state_name)
        os.makedirs(state_dir, exist_ok=True)
        
        # List of files to copy
        files_to_copy = [
            "customnerd_logo.png",
            "openai_prompts.py",
            "user_env.js",
            "user_list_search.py",
            "user_search_apis.py",
            "clean_query.py",
            "variables.env"
        ]
        
        # Copy each file if it exists
        for file in files_to_copy:
            source_path = None
            if file == "customnerd_logo.png":
                # Check if customnerd_logo.png exists, otherwise use fallback
                logo_path1 = os.path.join(base_dir, "customnerd-website", "assets", "customnerd_logo.png")
                logo_path2 = os.path.join(base_dir, "customnerd-website", "assets", "custom_nerd_default_logo.png")
                if os.path.exists(logo_path1):
                    source_path = logo_path1
                elif os.path.exists(logo_path2):
                    source_path = logo_path2
                else:
                    continue  # Skip if neither logo exists
            elif file == "user_env.js":
                source_path = os.path.join(base_dir, "customnerd-website", "user_env.js")
            else:
                # Files in backend directory
                source_path = os.path.join(backend_dir, file)
            
            if source_path and os.path.exists(source_path):
                try:
                    dest_path = os.path.join(state_dir, file)
                    shutil.copy2(source_path, dest_path)
                except Exception as file_error:
                    # Log individual file errors but continue with other files
                    logging.warning(f"Failed to copy {file}: {str(file_error)}")
                    continue

        # Handle historical_answer.json based on chat_history setting
        try:
            user_env_path = os.path.join(base_dir, "customnerd-website", "user_env.js")
            with open(user_env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            chat_enabled = False
            if start_idx != -1 and end_idx != 0:
                cfg = json5.loads(content[start_idx:end_idx])
                chat_enabled = cfg.get('USER_FLOW', {}).get('chat_history', {}).get('visible', False)
            # If chat history disabled, save empty history; else copy existing if present
            history_dest = os.path.join(state_dir, "historical_answer.json")
            if not chat_enabled:
                with open(history_dest, 'w', encoding='utf-8') as hf:
                    json.dump([], hf, ensure_ascii=False, indent=2)
            else:
                src_history = os.path.join(backend_dir, "historical_answer.json")
                if os.path.exists(src_history) and os.path.getsize(src_history) > 0:
                    shutil.copy2(src_history, history_dest)
                else:
                    with open(history_dest, 'w', encoding='utf-8') as hf:
                        json.dump([], hf, ensure_ascii=False, indent=2)
        except Exception as e:
            # Best effort; do not fail saving state due to config issues
            logging.warning(f"Failed to handle history: {str(e)}")
            try:
                history_dest = os.path.join(state_dir, "historical_answer.json")
                with open(history_dest, 'w', encoding='utf-8') as hf:
                    json.dump([], hf, ensure_ascii=False, indent=2)
            except Exception:
                pass
        
        return {"status": "success", "message": f"State '{state_name}' saved successfully"}
    except Exception as e:
        # Log the full error for debugging
        logging.error(f"Error saving state '{state_name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save state: {str(e)}")

@app.get("/list_saved_states")
async def list_saved_states():
    try:
        if not os.path.exists("saved_states"):
            return {"states": []}
        
        states = [d for d in os.listdir("saved_states") 
                 if os.path.isdir(os.path.join("saved_states", d))]
        return {"states": states}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load_state")
async def load_state(state_name: str = Form(...)):
    try:
        # Get base directory (parent of customnerd-backend)
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(backend_dir)
        
        # Use os.path.join for cross-platform path handling
        state_dir = os.path.join(backend_dir, "saved_states", state_name)
        if not os.path.exists(state_dir):
            raise HTTPException(status_code=404, detail=f"State '{state_name}' not found")
        
        # List of files to copy
        files_to_copy = [
            "customnerd_logo.png",
            "openai_prompts.py",
            "user_env.js",
            "user_list_search.py",
            "user_search_apis.py",
            "clean_query.py",
            "variables.env"
        ]
        
        # Copy each file if it exists
        for file in files_to_copy:
            source_path = os.path.join(state_dir, file)
            if os.path.exists(source_path):
                try:
                    if file == "customnerd_logo.png":
                        # Ensure assets directory exists
                        website_assets_dir = os.path.join(base_dir, "customnerd-website", "assets")
                        os.makedirs(website_assets_dir, exist_ok=True)
                        # Copy the logo from saved state
                        dest_path = os.path.join(website_assets_dir, "customnerd_logo.png")
                        shutil.copy2(source_path, dest_path)
                    elif file == "user_env.js":
                        website_dir = os.path.join(base_dir, "customnerd-website")
                        dest_path = os.path.join(website_dir, "user_env.js")
                        shutil.copy2(source_path, dest_path)
                    else:
                        # Copy to backend directory
                        dest_path = os.path.join(backend_dir, file)
                        shutil.copy2(source_path, dest_path)
                except Exception as file_error:
                    # Log individual file errors but continue with other files
                    logging.warning(f"Failed to copy {file}: {str(file_error)}")
                    continue
            elif file == "customnerd_logo.png":
                # If customnerd_logo.png not found in saved state, use fallback
                try:
                    website_assets_dir = os.path.join(base_dir, "customnerd-website", "assets")
                    os.makedirs(website_assets_dir, exist_ok=True)
                    fallback_logo = os.path.join(website_assets_dir, "custom_nerd_default_logo.png")
                    if os.path.exists(fallback_logo):
                        dest_path = os.path.join(website_assets_dir, "customnerd_logo.png")
                        shutil.copy2(fallback_logo, dest_path)
                        logging.info("Using fallback logo: custom_nerd_default_logo.png")
                except Exception as fallback_error:
                    logging.warning(f"Failed to use fallback logo: {str(fallback_error)}")

        # Ensure historical_answer.json exists; load from state if present, else create empty
        history_src = os.path.join(state_dir, "historical_answer.json")
        history_dst = os.path.join(backend_dir, "historical_answer.json")
        try:
            if os.path.exists(history_src):
                shutil.copy2(history_src, history_dst)
            else:
                with open(history_dst, 'w', encoding='utf-8') as hf:
                    json.dump([], hf, ensure_ascii=False, indent=2)
        except Exception as history_error:
            # Best effort - create empty history if copy fails
            logging.warning(f"Failed to copy history: {str(history_error)}")
            try:
                with open(history_dst, 'w', encoding='utf-8') as hf:
                    json.dump([], hf, ensure_ascii=False, indent=2)
            except Exception:
                pass
        
        return {"status": "success", "message": f"State '{state_name}' loaded successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Log the full error for debugging
        logging.error(f"Error loading state '{state_name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load state: {str(e)}")

@app.post("/delete_state")
async def delete_state(state_name: str = Form(...)):
    try:
        # Get backend directory for cross-platform path handling
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        state_dir = os.path.join(backend_dir, "saved_states", state_name)
        
        if not os.path.exists(state_dir):
            raise HTTPException(status_code=404, detail=f"State '{state_name}' not found")
        
        # Remove the entire state directory and all its contents
        shutil.rmtree(state_dir)
        
        return {"status": "success", "message": f"State '{state_name}' deleted successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Log the full error for debugging
        logging.error(f"Error deleting state '{state_name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete state: {str(e)}")

@app.post("/clear_chat_history")
async def clear_chat_history():
    try:
        history_path = "historical_answer.json"
        # Overwrite file with empty list JSON
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        return {"status": "success", "message": "Chat history cleared"}
    except Exception as e:
        logging.error(f"Error clearing chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not clear chat history")

@app.get("/history_recent")
async def history_recent(limit: int = 3, first: bool = False):
    try:
        history_path = "historical_answer.json"
        if not os.path.exists(history_path) or os.path.getsize(history_path) == 0:
            return {"items": []}
        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = [data]
        # Sort by timestamp. By default, latest first; if first=True, earliest first
        try:
            data.sort(key=lambda x: x.get("timestamp", ""), reverse=not first)
        except Exception:
            pass
        # Return only necessary fields
        items = []
        for entry in data[:max(0, limit)]:
            items.append({
                "timestamp": entry.get("timestamp"),
                "session_id": entry.get("session_id"),
                "input_text": entry.get("input_text"),
                "result": entry.get("result")
            })
        return {"items": items}
    except Exception as e:
        logging.error(f"Error fetching recent history: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch recent history")

@app.get("/similar_questions")
async def similar_questions(query: str, threshold: float = 0.2, limit: int = 3):
    try:
        history_path = "historical_answer.json"
        if not os.path.exists(history_path) or os.path.getsize(history_path) == 0:
            return {"items": []}

        with open(history_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = [data]

        # Extract questions
        questions = [entry.get('input_text', '') for entry in data if entry.get('input_text')]
        if not questions:
            return {"items": []}

        # Normalization + canonicalization helpers
        import re
        def normalize_text(t: str) -> str:
            t = (t or "").lower()
            t = re.sub(r"[^a-z0-9\s]", " ", t)
            t = re.sub(r"\s+", " ", t).strip()
            return t

        # Canonicalize common synonyms/variants to improve recall
        def canonicalize_text(t: str) -> str:
            t = normalize_text(t)
            # Phrase level
            t = re.sub(r"\bvitamin\s*b12\b", "vitamin b12", t)
            # Token level replacements
            synonyms = {
                "pros": "advantage",
                "pro": "advantage",
                "advantages": "advantage",
                "benefit": "advantage",
                "benefits": "advantage",
                "cons": "disadvantage",
                "con": "disadvantage",
                "disadvantages": "disadvantage",
                "drawbacks": "disadvantage",
                "downsides": "disadvantage",
                "deal": "manage",
                "handling": "manage",
                "handle": "manage",
                "handled": "manage",
                "managing": "manage",
                "management": "manage",
                "treat": "manage",
                "treatment": "manage",
                "treating": "manage",
                "pregnancies": "pregnancy",
                "pregnant": "pregnancy",
                "b12": "vitamin b12"
            }
            tokens = t.split()
            canonical_tokens = [synonyms.get(tok, tok) for tok in tokens]
            return " ".join(canonical_tokens)

        canonical_questions = [canonicalize_text(q) for q in questions]
        canonical_query = canonicalize_text(query)

        # Word n-gram TF-IDF (1,2)
        word_vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), lowercase=True)
        word_tfidf = word_vectorizer.fit_transform(canonical_questions + [canonical_query])
        word_sims = cosine_similarity(word_tfidf[-1], word_tfidf[:-1]).flatten()

        # Char n-gram TF-IDF (robust to word order/noise)
        char_vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), lowercase=True)
        char_tfidf = char_vectorizer.fit_transform(canonical_questions + [canonical_query])
        char_sims = cosine_similarity(char_tfidf[-1], char_tfidf[:-1]).flatten()

        # Token Jaccard similarity
        def jaccard(a: str, b: str) -> float:
            sa, sb = set(a.split()), set(b.split())
            if not sa or not sb:
                return 0.0
            inter = len(sa & sb)
            union = len(sa | sb)
            return inter / union if union else 0.0

        # Fuzzy ratio using difflib
        from difflib import SequenceMatcher
        def fuzzy_ratio(a: str, b: str) -> float:
            return SequenceMatcher(None, a, b).ratio()

        # Combine scores using maximum across methods
        min_heap = []
        for idx in range(len(canonical_questions)):
            combined = max(
                float(word_sims[idx]),
                float(char_sims[idx]),
                jaccard(canonical_query, canonical_questions[idx]),
                fuzzy_ratio(canonical_query, canonical_questions[idx])
            )
            if combined >= threshold:
                heapq.heappush(min_heap, (combined, idx))
                if len(min_heap) > max(1, limit):
                    heapq.heappop(min_heap)

        # Format top results, highest score first
        top = sorted(min_heap, key=lambda x: x[0], reverse=True)
        items = []
        for score, idx in top:
            entry = data[idx]
            items.append({
                "input_text": entry.get('input_text'),
                "score": float(score),
                "result": entry.get('result'),
                "timestamp": entry.get('timestamp'),
                "session_id": entry.get('session_id')
            })

        return {"items": items}
    except Exception as e:
        logging.error(f"Error computing similar questions: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not compute similar questions")

@app.get("/ollama_status")
async def ollama_status():
    """Check whether Ollama is installed and its server is reachable."""
    import shutil
    import platform as _platform
    import urllib.request as _urlreq

    is_installed = shutil.which('ollama') is not None
    is_running = False
    installed_models: list = []
    system = _platform.system()

    if is_installed:
        try:
            req = _urlreq.Request('http://localhost:11434/api/tags')
            with _urlreq.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    is_running = True
                    data = json.loads(resp.read())
                    installed_models = [m['name'] for m in data.get('models', [])]
        except Exception:
            pass

    # Manual installation: setup.py only (shown when not installed)
    manual_steps = [] if is_installed else [{"title": "Run setup.py", "commands": ["python3 setup.py"], "notes": ["Enter password when prompted. Installs Ollama and pulls the model."]}]

    return {
        "is_installed": is_installed,
        "is_running": is_running,
        "installed_models": installed_models,
        "platform": system,
        "manual_steps": manual_steps,
    }


async def _ollama_setup_generator(model: str):
    """
    Async generator that streams Ollama setup progress as SSE-compatible dicts.
    Steps: 1) check/install  2) start server  3) pull model  4) verify
    """
    import shutil
    import platform as _platform
    import asyncio
    import subprocess
    import urllib.request as _urlreq

    def _msg(message: str, step: int = 0, total: int = 4, msg_type: str = "progress"):
        payload = {"type": msg_type, "step": step, "total": total, "message": message}
        return {"event": "message", "data": json.dumps(payload)}

    # ── Step 1: check / install ──────────────────────────────────────────────
    yield _msg("Checking if Ollama is installed…", step=1)
    await asyncio.sleep(0.05)

    is_installed = shutil.which('ollama') is not None
    system = _platform.system()

    if is_installed:
        yield _msg("Ollama is already installed.", step=1, msg_type="success")
    else:
        yield _msg(f"Ollama not found on {system}. Starting installation…", step=1)

        # ── Windows ────────────────────────────────────────────────────────
        if system == 'Windows':
            # Method 1: official PowerShell script
            yield _msg("Method 1/2 — Running official install script via PowerShell…", step=1)
            ps_cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://ollama.com/install.ps1 | iex"'
            rc = None
            proc = await asyncio.create_subprocess_shell(
                ps_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            async for raw in proc.stdout:
                line = raw.decode(errors='replace').strip()
                if line:
                    yield _msg(line, step=1, msg_type="install_log")
            await proc.wait()
            rc = proc.returncode
            is_installed = shutil.which('ollama') is not None

            if not is_installed:
                # Method 2: winget
                yield _msg("Method 1 did not succeed. Trying Method 2/2 — winget install Ollama.Ollama…", step=1)
                winget = shutil.which('winget')
                if winget:
                    proc = await asyncio.create_subprocess_exec(
                        'winget', 'install', '--id', 'Ollama.Ollama', '--accept-source-agreements', '--accept-package-agreements',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                    async for raw in proc.stdout:
                        line = raw.decode(errors='replace').strip()
                        if line:
                            yield _msg(line, step=1, msg_type="install_log")
                    await proc.wait()
                    is_installed = shutil.which('ollama') is not None
                else:
                    yield _msg("winget not found — skipping Method 2.", step=1, msg_type="warning")

            if not is_installed:
                yield _msg(
                    "Automatic installation failed on Windows. "
                    "Please download the installer manually from https://ollama.com and re-run setup.",
                    step=1, msg_type="fatal"
                )
                return

        # ── macOS ──────────────────────────────────────────────────────────
        elif system == 'Darwin':
            # Method 1: official curl script
            yield _msg("Method 1/3 — Running official install script: curl -fsSL https://ollama.com/install.sh | sh", step=1)
            proc = await asyncio.create_subprocess_shell(
                'curl -fsSL https://ollama.com/install.sh | sh',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            async for raw in proc.stdout:
                line = raw.decode(errors='replace').strip()
                if line:
                    yield _msg(line, step=1, msg_type="install_log")
            await proc.wait()
            is_installed = shutil.which('ollama') is not None
            if is_installed:
                yield _msg("Ollama installed via official script.", step=1, msg_type="success")

            # Method 2: Homebrew
            if not is_installed:
                brew = shutil.which('brew')
                if brew:
                    yield _msg("Method 2/3 — Installing via Homebrew: brew install ollama…", step=1)
                    proc = await asyncio.create_subprocess_exec(
                        'brew', 'install', 'ollama',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                    )
                    async for raw in proc.stdout:
                        line = raw.decode(errors='replace').strip()
                        if line:
                            yield _msg(line, step=1, msg_type="install_log")
                    await proc.wait()
                    is_installed = shutil.which('ollama') is not None
                    if is_installed:
                        yield _msg("Ollama installed via Homebrew.", step=1, msg_type="success")
                else:
                    yield _msg("Homebrew not found — skipping Method 2.", step=1, msg_type="warning")

            # Method 3: direct binary download
            if not is_installed:
                yield _msg("Method 3/3 — Downloading macOS binary directly from GitHub releases…", step=1)
                arch = _platform.machine()
                asset = 'ollama-darwin' if 'arm' not in arch.lower() and 'aarch' not in arch.lower() else 'ollama-darwin'
                dl_cmd = (
                    f'curl -fsSL "https://github.com/ollama/ollama/releases/latest/download/{asset}" '
                    f'-o /usr/local/bin/ollama && chmod +x /usr/local/bin/ollama'
                )
                proc = await asyncio.create_subprocess_shell(
                    dl_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                async for raw in proc.stdout:
                    line = raw.decode(errors='replace').strip()
                    if line:
                        yield _msg(line, step=1, msg_type="install_log")
                await proc.wait()
                is_installed = shutil.which('ollama') is not None
                if is_installed:
                    yield _msg("Ollama installed via direct binary download.", step=1, msg_type="success")

            if not is_installed:
                yield _msg(
                    "All 3 installation methods failed on macOS. "
                    "Please install manually: brew install ollama  or visit https://ollama.com",
                    step=1, msg_type="fatal"
                )
                return

        # ── Linux ──────────────────────────────────────────────────────────
        else:
            # Method 1: official curl script
            yield _msg("Method 1/2 — Running official install script: curl -fsSL https://ollama.com/install.sh | sh", step=1)
            proc = await asyncio.create_subprocess_shell(
                'curl -fsSL https://ollama.com/install.sh | sh',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            async for raw in proc.stdout:
                line = raw.decode(errors='replace').strip()
                if line:
                    yield _msg(line, step=1, msg_type="install_log")
            await proc.wait()
            is_installed = shutil.which('ollama') is not None
            if is_installed:
                yield _msg("Ollama installed via official script.", step=1, msg_type="success")
                # Try to enable and start the systemd service silently
                try:
                    await asyncio.create_subprocess_shell(
                        'sudo systemctl enable ollama && sudo systemctl start ollama',
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL,
                    )
                    yield _msg("systemd service enabled and started.", step=1, msg_type="install_log")
                except Exception:
                    pass

            # Method 2: direct binary to ~/.local/bin
            if not is_installed:
                yield _msg("Method 2/2 — Downloading Linux binary to ~/.local/bin…", step=1)
                arch = _platform.machine().lower()
                if 'aarch64' in arch or 'arm64' in arch:
                    asset = 'ollama-linux-arm64'
                else:
                    asset = 'ollama-linux-amd64'
                dl_cmd = (
                    'mkdir -p ~/.local/bin && '
                    f'curl -fsSL "https://github.com/ollama/ollama/releases/latest/download/{asset}" '
                    f'-o ~/.local/bin/ollama && chmod +x ~/.local/bin/ollama && '
                    'export PATH="$HOME/.local/bin:$PATH"'
                )
                proc = await asyncio.create_subprocess_shell(
                    dl_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                async for raw in proc.stdout:
                    line = raw.decode(errors='replace').strip()
                    if line:
                        yield _msg(line, step=1, msg_type="install_log")
                await proc.wait()
                # Also check ~/.local/bin/ollama directly in case it's not on PATH yet
                import os as _os
                local_bin = _os.path.expanduser('~/.local/bin/ollama')
                is_installed = shutil.which('ollama') is not None or _os.path.isfile(local_bin)
                if is_installed:
                    yield _msg("Ollama binary installed to ~/.local/bin.", step=1, msg_type="success")

            if not is_installed:
                yield _msg(
                    "All installation methods failed on Linux. "
                    "Please install manually: curl -fsSL https://ollama.com/install.sh | sh",
                    step=1, msg_type="fatal"
                )
                return

        yield _msg("Ollama installed successfully.", step=1, msg_type="success")

    # ── Step 2: ensure server is running ────────────────────────────────────
    yield _msg("Checking Ollama server status…", step=2)
    await asyncio.sleep(0.05)

    def _server_running() -> bool:
        try:
            with _urlreq.urlopen('http://localhost:11434/api/tags', timeout=3) as r:
                return r.status == 200
        except Exception:
            return False

    if _server_running():
        yield _msg("Ollama server is already running.", step=2, msg_type="success")
    else:
        yield _msg("Starting Ollama server (ollama serve)…", step=2)
        subprocess.Popen(
            ['ollama', 'serve'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        started = False
        for _ in range(15):
            await asyncio.sleep(1)
            if _server_running():
                started = True
                break
        if started:
            yield _msg("Ollama server started.", step=2, msg_type="success")
        else:
            yield _msg(
                "Server may still be starting — continuing with model pull. "
                "If issues persist, run 'ollama serve' in a terminal.",
                step=2, msg_type="warning"
            )

    # ── Step 3: pull model ───────────────────────────────────────────────────
    yield _msg(f"Pulling model '{model}' — this can take several minutes for large models…", step=3)
    await asyncio.sleep(0.05)

    pull_proc = await asyncio.create_subprocess_exec(
        'ollama', 'pull', model,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for raw in pull_proc.stdout:
        line = raw.decode(errors='replace').strip()
        if line:
            yield _msg(line, step=3, msg_type="pull_log")
    await pull_proc.wait()

    if pull_proc.returncode == 0:
        yield _msg(f"Model '{model}' pulled successfully.", step=3, msg_type="success")
    else:
        yield _msg(
            f"Pull failed for '{model}'. Check the model name and your internet connection.",
            step=3, msg_type="error"
        )
        return

    # ── Step 4: verify ───────────────────────────────────────────────────────
    yield _msg("Verifying setup…", step=4)
    await asyncio.sleep(0.5)

    try:
        with _urlreq.urlopen('http://localhost:11434/api/tags', timeout=5) as r:
            data = json.loads(r.read())
            names = [m['name'] for m in data.get('models', [])]
            base = model.split(':')[0]
            found = any(base in n for n in names)
        msg = (
            f"✓ Setup complete! Ollama is running and model '{model}' is ready."
            if found else
            f"✓ Setup complete! Model '{model}' should be available — restart the backend if needed."
        )
        yield _msg(msg, step=4, msg_type="complete")
    except Exception:
        yield _msg(
            f"✓ Setup steps finished. If the model is not responding, run 'ollama serve' and 'ollama pull {model}' manually.",
            step=4, msg_type="complete"
        )


@app.get("/ollama_setup")
async def ollama_setup(model: str = Query(default='llama3.2')):
    """
    Stream Ollama setup progress via SSE.
    Steps: install Ollama → start server → pull model → verify.
    """
    return EventSourceResponse(_ollama_setup_generator(model))


class ApiKeyTestRequest(BaseModel):
    api_key: str = ""


@app.post("/test_api_key/{provider}")
async def test_api_key(provider: str, body: ApiKeyTestRequest):
    """
    Test whether an API key / connection works for a given provider.
    Accepts: openai | gemini | claude | ollama
    Returns: {"ok": bool, "message": str}
    """
    key = body.api_key.strip()

    if provider == "openai":
        if not key:
            return {"ok": False, "message": "No API key entered."}
        try:
            from openai import OpenAI as _OpenAI, AuthenticationError as _OAIAuthError
            tc = _OpenAI(api_key=key, timeout=10)
            tc.models.list()
            return {"ok": True, "message": "OpenAI key is valid — connection successful ✓"}
        except _OAIAuthError:
            return {"ok": False, "message": "Invalid API key — authentication failed."}
        except Exception as e:
            msg = str(e)
            if "401" in msg or "invalid" in msg.lower():
                return {"ok": False, "message": "Invalid API key — authentication failed."}
            return {"ok": False, "message": f"Connection error: {msg[:150]}"}

    elif provider == "gemini":
        if not key:
            return {"ok": False, "message": "No API key entered."}
        try:
            from google import genai as _genai
            tc = _genai.Client(api_key=key)
            list(tc.models.list())
            return {"ok": True, "message": "Gemini key is valid — connection successful ✓"}
        except Exception as e:
            msg = str(e)
            if any(x in msg for x in ["401", "403", "API_KEY_INVALID", "invalid"]):
                return {"ok": False, "message": "Invalid API key — authentication failed."}
            return {"ok": False, "message": f"Connection error: {msg[:150]}"}

    elif provider == "claude":
        if not key:
            return {"ok": False, "message": "No API key entered."}
        try:
            from anthropic import Anthropic as _Anthropic, AuthenticationError as _AnthAuthError
            tc = _Anthropic(api_key=key, timeout=10)
            tc.models.list()
            return {"ok": True, "message": "Claude key is valid — connection successful ✓"}
        except _AnthAuthError:
            return {"ok": False, "message": "Invalid API key — authentication failed."}
        except Exception as e:
            msg = str(e)
            if any(x in msg.lower() for x in ["401", "403", "invalid", "authentication"]):
                return {"ok": False, "message": "Invalid API key — authentication failed."}
            return {"ok": False, "message": f"Connection error: {msg[:150]}"}

    elif provider == "ollama":
        try:
            import urllib.request as _urlreq
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
            with _urlreq.urlopen(f"{base_url}/api/tags", timeout=5) as r:
                data = json.loads(r.read())
                models = [m["name"] for m in data.get("models", [])]
            if models:
                preview = ", ".join(models[:4]) + ("…" if len(models) > 4 else "")
                return {"ok": True, "message": f"Ollama is running ✓ — {len(models)} model(s): {preview}"}
            return {"ok": True, "message": "Ollama is running ✓ — no models pulled yet (run setup to pull one)"}
        except Exception:
            return {
                "ok": False,
                "message": "Ollama server not reachable on port 11434 — click 'Update Environment Configuration' to install & start it."
            }

    return {"ok": False, "message": f"Unknown provider '{provider}'."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
   
   