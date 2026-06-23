import urllib.request
try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/quality/c23709e2-41e3-4db3-bcc2-3036e9bad288')
    urllib.request.urlopen(req)
except Exception as e:
    print(e.read().decode())
