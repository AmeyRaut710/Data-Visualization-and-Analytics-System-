import urllib.request
import json
import traceback

session_id_quality = '7ab1cadc-4802-4a89-993f-d132f9f3721f'
url_quality = f'http://127.0.0.1:8000/api/quality/{session_id_quality}'

try:
    req = urllib.request.Request(url_quality)
    with urllib.request.urlopen(req) as response:
        print("Quality Success")
except urllib.error.HTTPError as e:
    print(f"Quality HTTPError: {e.code}")
    print(e.read().decode())
except Exception as e:
    print("Quality Other Error:", str(e))

session_id_chat = '5c326271-fb22-4204-b808-0bbafa001fb7'
url_chat = f'http://127.0.0.1:8000/api/chat/{session_id_chat}'
try:
    req = urllib.request.Request(url_chat, data=json.dumps({"message": "hi"}).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        print("Chat Success")
except urllib.error.HTTPError as e:
    print(f"Chat HTTPError: {e.code}")
    print(e.read().decode())
except Exception as e:
    print("Chat Other Error:", str(e))
