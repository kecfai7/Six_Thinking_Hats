import requests

resp = requests.post(
    "http://127.0.0.1:5000/api/solve",
    json={
        "problem": "직장에서의 인간관계가 어렵습니다.",
        "email": "test@example.com"
    }
)
print(resp.json())