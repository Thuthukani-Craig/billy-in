import json
import urllib.request

request = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/login/',
    method='OPTIONS',
    headers={'Origin': 'http://127.0.0.1:3000', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'},
)
with urllib.request.urlopen(request) as response:
    print(response.status)
    print(dict(response.headers))
