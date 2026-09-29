import re

file_path = 'app/services/ai_service.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''                else:
                    if "503" in err_msg:
                        return "I'm currently experiencing very high demand and couldn't process your request. Please try again in a moment!"
                    raise Exception(f"AI Provider Error: {err_msg}")'''
                    
replace = '''                else:
                    if "503" in err_msg:
                        return "I'm currently experiencing very high demand and couldn't process your request. Please try again in a moment!"
                    if "429" in err_msg or "quota" in err_msg.lower() or "resource_exhausted" in err_msg.lower():
                        return "📈 **AI Analysis Unavailable (Quota Exceeded)**\\n\\nOur free-tier AI daily limit has been reached. Please check back tomorrow. The rest of the platform (charts, screeners, portfolios) is fully operational and unaffected!"
                    raise Exception(f"AI Provider Error: {err_msg}")'''

content = content.replace(target, replace)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated ai_service.py with friendly 429 message")
