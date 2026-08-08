from fastapi.testclient import TestClient
from app.main import app

try:
    client = TestClient(app)
    response = client.get("/")
    print("SUCCESS:", response.status_code, response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
