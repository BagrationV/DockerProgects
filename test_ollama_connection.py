#!/usr/bin/env python3
import requests
import os
import json
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_ollama_connection():
    # Get Ollama host from environment variable with fallback
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    logging.info(f"Using Ollama host: {ollama_host}")
    
    # Test basic connectivity
    try:
        logging.info("Testing basic connectivity to Ollama API...")
        version_check = requests.get(
            f"{ollama_host}/api/version",
            timeout=5
        )
        if version_check.status_code == 200:
            logging.info(f"Ollama API is reachable. Version: {version_check.json()}")
        else:
            logging.error(f"Ollama API returned non-200 status on version check: {version_check.status_code}")
            return False
    except requests.exceptions.RequestException as conn_error:
        logging.error(f"Failed to connect to Ollama API: {conn_error}")
        return False
    
    # Check available models
    try:
        logging.info("Checking available models...")
        model_check = requests.get(
            f"{ollama_host}/api/tags",
            timeout=10
        )
        
        if model_check.status_code == 200:
            models_data = model_check.json()
            logging.info(f"Available models: {json.dumps(models_data)}")
            
            # Check for specific models
            models = models_data.get("models", [])
            primary_model = "qwen2.5:7b"
            fallback_model = "llama2"
            
            primary_exists = any(model.get("name") == primary_model for model in models)
            fallback_exists = any(model.get("name") == fallback_model for model in models)
            
            logging.info(f"Primary model '{primary_model}' exists: {primary_exists}")
            logging.info(f"Fallback model '{fallback_model}' exists: {fallback_exists}")
            
            # Try to pull primary model if it doesn't exist
            if not primary_exists:
                logging.info(f"Attempting to pull model {primary_model}...")
                pull_response = requests.post(
                    f"{ollama_host}/api/pull",
                    json={"name": primary_model},
                    timeout=300
                )
                if pull_response.status_code == 200:
                    logging.info(f"Successfully initiated pull for model {primary_model}")
                    # Wait for model to be ready
                    for _ in range(5):
                        time.sleep(5)
                        check_response = requests.get(f"{ollama_host}/api/tags", timeout=10)
                        if check_response.status_code == 200:
                            models = check_response.json().get("models", [])
                            if any(model.get("name") == primary_model for model in models):
                                logging.info(f"Model {primary_model} is now available")
                                primary_exists = True
                                break
                    if not primary_exists:
                        logging.warning(f"Model {primary_model} still not available after pull attempt")
                else:
                    logging.error(f"Failed to pull model: {pull_response.text}")
            
            # Try to pull fallback model if it doesn't exist
            if not fallback_exists and not primary_exists:
                logging.info(f"Attempting to pull fallback model {fallback_model}...")
                pull_response = requests.post(
                    f"{ollama_host}/api/pull",
                    json={"name": fallback_model},
                    timeout=300
                )
                if pull_response.status_code == 200:
                    logging.info(f"Successfully initiated pull for model {fallback_model}")
                else:
                    logging.error(f"Failed to pull fallback model: {pull_response.text}")
        else:
            logging.error(f"Failed to get model list: {model_check.status_code}")
            return False
    except Exception as model_error:
        logging.error(f"Error checking models: {model_error}")
        return False
    
    # Test model generation
    model_to_test = primary_model if primary_exists else fallback_model if fallback_exists else None
    if model_to_test:
        try:
            logging.info(f"Testing model generation with {model_to_test}...")
            test_prompt = "Hello, how are you today?"
            
            start_time = time.time()
            response = requests.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": model_to_test,
                    "prompt": test_prompt,
                    "stream": False
                },
                timeout=120
            )
            elapsed_time = time.time() - start_time
            
            logging.info(f"Response received in {elapsed_time:.2f} seconds with status {response.status_code}")
            
            if response.status_code == 200:
                response_json = response.json()
                model_response = response_json.get("response", "")
                logging.info(f"Model response: {model_response[:100]}...")
                logging.info("Model generation test successful!")
                return True
            else:
                logging.error(f"Model generation failed with status {response.status_code}")
                if response.content:
                    try:
                        error_content = response.json()
                        logging.error(f"Error details: {json.dumps(error_content)}")
                    except:
                        logging.error(f"Raw error response: {response.text[:200]}")
                return False
        except Exception as gen_error:
            logging.error(f"Error during model generation test: {gen_error}")
            return False
    else:
        logging.error("No models available for testing")
        return False

if __name__ == "__main__":
    success = test_ollama_connection()
    if success:
        logging.info("All tests passed successfully!")
    else:
        logging.error("Some tests failed. Check the logs for details.")