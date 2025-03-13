from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

class Conversation(BaseModel):
    user_input: str

@app.post("/chat")
async def chat(conversation: Conversation):
    try:
        # Log the incoming request
        logging.info(f"Received chat request with input: {conversation.user_input[:50]}...")
        
        # Get Ollama host from environment variable with fallback
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        logging.info(f"Using Ollama host: {ollama_host}")
        
        # Test basic connectivity to Ollama
        try:
            version_check = requests.get(
                f"{ollama_host}/api/version",
                timeout=5
            )
            if version_check.status_code == 200:
                logging.info(f"Ollama API is reachable. Version: {version_check.json()}")
            else:
                logging.error(f"Ollama API returned non-200 status on version check: {version_check.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Ollama service is not responding properly. Status: {version_check.status_code}"
                )
        except requests.exceptions.RequestException as conn_error:
            logging.error(f"Failed to connect to Ollama API: {conn_error}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Cannot connect to Ollama service: {str(conn_error)}"
            )
        
        # Check if model exists, if not try to pull it
        model_name = "qwen2.5:7b"
        fallback_model = "llama2"
        model_exists = False
        
        try:
            # Check if model exists
            logging.info(f"Checking if model {model_name} exists")
            model_check = requests.get(
                f"{ollama_host}/api/tags",
                timeout=10
            )
            
            if model_check.status_code == 200:
                models_data = model_check.json()
                logging.info(f"Available models: {json.dumps(models_data)}")
                
                models = models_data.get("models", [])
                model_exists = any(model.get("name") == model_name for model in models)
                logging.info(f"Model {model_name} exists: {model_exists}")
                
                # Also check if fallback model exists
                fallback_exists = any(model.get("name") == fallback_model for model in models)
                logging.info(f"Fallback model {fallback_model} exists: {fallback_exists}")
                
                # If model doesn't exist, try to pull it
                if not model_exists:
                    logging.info(f"Model {model_name} not found, attempting to pull...")
                    pull_response = requests.post(
                        f"{ollama_host}/api/pull",
                        json={"name": model_name},
                        timeout=300  # Longer timeout for model pulling
                    )
                    if pull_response.status_code == 200:
                        logging.info(f"Successfully initiated pull for model {model_name}")
                        # Wait for model to be ready
                        for _ in range(5):  # Try up to 5 times
                            time.sleep(5)  # Wait 5 seconds between checks
                            check_response = requests.get(f"{ollama_host}/api/tags", timeout=10)
                            if check_response.status_code == 200:
                                models = check_response.json().get("models", [])
                                if any(model.get("name") == model_name for model in models):
                                    model_exists = True
                                    logging.info(f"Model {model_name} is now available")
                                    break
                        if not model_exists:
                            logging.warning(f"Model {model_name} still not available after pull attempt")
                    else:
                        logging.error(f"Failed to pull model: {pull_response.text}")
            else:
                logging.error(f"Failed to get model list: {model_check.status_code}")
        except Exception as model_error:
            logging.error(f"Error checking/pulling model: {model_error}")
            # Continue anyway, maybe the model exists but we couldn't check
        
        # Try with primary model first, then fallback if needed
        response = None
        try:
            # Log the request we're about to make
            logging.info(f"Sending request to model {model_name}")
            start_time = time.time()
            
            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": model_name,
                    "prompt": conversation.user_input,
                    "stream": False
                },
                timeout=120  # Increased timeout for model generation
            )
            
            elapsed_time = time.time() - start_time
            logging.info(f"Response received from {model_name} in {elapsed_time:.2f} seconds with status {response.status_code}")
            
            # Log response headers and partial content for debugging
            logging.info(f"Response headers: {dict(response.headers)}")
            if response.content:
                content_preview = response.content[:200] if len(response.content) > 200 else response.content
                logging.info(f"Response content preview: {content_preview}")
            
        except requests.exceptions.Timeout as timeout_error:
            logging.error(f"Timeout error with {model_name}: {timeout_error}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Request to model {model_name} timed out after 120 seconds"
            )
        except Exception as api_error:
            logging.error(f"API request error with {model_name}: {api_error}")
            
            # Try with a fallback model
            logging.info(f"Attempting to use fallback model {fallback_model}")
            try:
                start_time = time.time()
                response = requests.post(
                    f"{ollama_host}/api/generate",
                    json={
                        "model": fallback_model,
                        "prompt": conversation.user_input,
                        "stream": False
                    },
                    timeout=60
                )
                elapsed_time = time.time() - start_time
                logging.info(f"Response received from fallback model {fallback_model} in {elapsed_time:.2f} seconds with status {response.status_code}")
            except Exception as fallback_error:
                logging.error(f"Fallback model error: {fallback_error}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Both primary and fallback models failed. Last error: {fallback_error}"
                )
        
        if not response or response.status_code != 200:
            error_detail = "No response received" if not response else f"Model API error: {response.status_code}"
            if response and response.content:
                try:
                    error_content = response.json()
                    error_detail = f"{error_detail}. Details: {json.dumps(error_content)}"
                except:
                    error_detail = f"{error_detail}. Raw response: {response.text[:200]}"
            
            logging.error(f"Failed request: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )
        
        # Parse the response
        try:
            response_json = response.json()
            logging.info(f"Successfully parsed JSON response: {json.dumps(response_json)[:200]}...")
            model_response = response_json.get("response", "No response received")
            if not model_response or model_response == "No response received":
                logging.warning(f"Empty or missing response field in API response: {json.dumps(response_json)[:200]}...")
        except Exception as json_error:
            logging.error(f"Failed to parse JSON response: {json_error}. Response content: {response.text[:200]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse model response: {str(json_error)}"
            )
        
        # Store conversation in database
        try:
            logging.info("Storing conversation in database")
            conn = psycopg2.connect(
                host="postgres",
                database="vit",
                user="vit",
                password="vit"
            )
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversation_history (user_input, model_response) VALUES (%s, %s)",
                (conversation.user_input, model_response)
            )
            conn.commit()
            cursor.close()
            conn.close()
            logging.info("Successfully stored conversation in database")
        except Exception as db_error:
            logging.error(f"Database error: {db_error}")
            # Continue even if database operation fails
        
        logging.info(f"Returning successful response with length {len(model_response)}")
        return {"response": model_response}
    
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        logging.exception(f"Unhandled exception in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )