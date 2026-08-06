from jose import jwt
from datetime import datetime, timedelta
import json
import urllib.request
import urllib.error

secret = None
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('JWT_SECRET_KEY='):
            secret = line.strip().split('=')[1].strip('\"\'')
            break

payload = {
    'sub': 'test2_oauth_register@example.com',
    'name': 'Test User 2',
    'oauth_id': '54321',
    'purpose': 'oauth_registration',
    'exp': datetime.utcnow() + timedelta(minutes=10)
}
valid_token = jwt.encode(payload, secret, algorithm='HS256')
fake_token = jwt.encode(payload, 'wrong_secret_123', algorithm='HS256')

def make_request(token, name):
    print(f'\n--- Testing {name} ---')
    data = json.dumps({'reg_token': token, 'org_name': 'My Org'}).encode('utf-8')
    req = urllib.request.Request('http://localhost:8000/api/v1/auth/register/oauth', data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            print(f'Status: {response.status}')
            print(f'Response: {response.read().decode()}')
    except urllib.error.HTTPError as e:
        print(f'Status: {e.code}')
        print(f'Response: {e.read().decode()}')

make_request(valid_token, 'Valid Flow')
make_request(fake_token, 'Fabricated Flow (Invalid Signature)')
