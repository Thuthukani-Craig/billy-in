import json
import urllib.request

payload = json.dumps({
    'username': 'qa-browser-user',
    'password': 'StrongPass123!'
}).encode()
request = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/login/',
    data=payload,
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(request) as response:
    body = response.read().decode()
    print(response.status)
    print(body)
