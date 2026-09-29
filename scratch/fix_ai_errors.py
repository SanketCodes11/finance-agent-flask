import re

file_path = 'app/services/ai_service.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the inner try-except block inside the fetch_agent_insight function
target = '''        for attempt in range(max_retries):
            try:
                response = chat.send_message(query)
                return response.text
            except Exception as e:
                err_msg = str(e)
                # Check for 503 or 429 in the error string
                if ("503" in err_msg or "429" in err_msg) and attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                else:
                    if "503" in err_msg:
                        return "I'm currently experiencing very high demand and couldn't process your request. Please try again in a moment!"
                    if "429" in err_msg or "quota" in err_msg.lower() or "resource_exhausted" in err_msg.lower():
                        return "dY"^ **AI Analysis Unavailable (Quota Exceeded)**\\n\\nOur free-tier AI daily limit has been reached. Please check back tomorrow. The rest of the platform (charts, screeners, portfolios) is fully operational and unaffected!"
                    raise Exception(f"AI Provider Error: {err_msg}")
                    
    except Exception as e:
        # If it's already a friendly message, return it directly
        if "high demand" in str(e):
            return str(e)
        raise Exception(f"AI Provider Error: {str(e)}")'''

replacement = '''        for attempt in range(max_retries):
            try:
                response = chat.send_message(query)
                return response.text
            except Exception as e:
                err_msg = str(e)
                
                # Identify if it's a quota error which should NOT be retried (429 Resource Exhausted)
                is_quota = "429" in err_msg or "quota" in err_msg.lower() or "resource_exhausted" in err_msg.lower()
                is_timeout = "503" in err_msg or "504" in err_msg or "timeout" in err_msg.lower()
                is_auth = "401" in err_msg or "403" in err_msg or "api_key" in err_msg.lower()
                
                # Only retry timeouts, not hard quota or auth errors
                if is_timeout and attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                    
                if is_quota:
                    raise Exception("AI Analysis Unavailable (Quota Exceeded): The AI service rate limit or daily quota has been reached. Please check back later. The rest of the platform remains fully operational.")
                if is_timeout:
                    raise Exception("AI Analysis Unavailable: The service is currently experiencing high demand or a temporary timeout. Please try again in a few moments.")
                if is_auth:
                    raise Exception("AI Analysis Unavailable: Invalid API Key. Please contact the administrator to verify the configuration.")
                
                # For any other errors, do not expose the raw payload to the frontend
                raise Exception("AI Provider Error: An unexpected provider error occurred.")
                
    except Exception as e:
        raise Exception(str(e))'''

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed ai_service.py")
else:
    print("Could not find target in ai_service.py")
