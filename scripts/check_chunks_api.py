import sys
import requests

doc_id = sys.argv[1] if len(
    sys.argv) > 1 else '8523c731-ccea-4137-8472-600dcb5f4b64'
base = 'http://localhost:8000/api/v1'
print('GET', f'{base}/documents/{doc_id}/chunks')
r = requests.get(f'{base}/documents/{doc_id}/chunks')
print('status', r.status_code)
try:
    print(r.json())
except Exception as e:
    print('non-json', r.text)
