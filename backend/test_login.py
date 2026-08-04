import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/auth/login',
    data=b'{"email":"userA_55ba732a-2c88-4090-8603-9158580360b8@a.com","password":"password123"}',
    headers={'Content-Type':'application/json'}
)
try:
    resp = urllib.request.urlopen(req)
    print(resp.read().decode())
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code)
    print(e.read().decode())
except Exception as e:
    print("Error:", e)
