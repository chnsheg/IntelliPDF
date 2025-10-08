import os
import sys
import json
from pathlib import Path
import requests

BASE = "http://localhost:8000/api/v1"
DOC_ID = sys.argv[1] if len(
    sys.argv) > 1 else "8523c731-ccea-4137-8472-600dcb5f4b64"

payload = {
    "question": "什么是本文件的主要主题？",
    "top_k": 3
}

resp = requests.post(f"{BASE}/documents/{DOC_ID}/chat", json=payload)
print('status', resp.status_code)
try:
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print('non-json response', resp.text)
