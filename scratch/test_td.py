import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get('TWELVE_DATA_API_KEY')
print("Key length:", len(api_key))

url = f"https://api.twelvedata.com/quote?symbol=RELIANCE&exchange=NSE&apikey={api_key}"
resp = requests.get(url)
print(resp.status_code)
print(resp.json())
