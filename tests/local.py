import requests
import json

data = {
    "model": "gemma2:2b-instruct-q6_K",
    "messages": [
        {
            "role": "user",
            "content": "Hi"
        }
    ],
    "stream": False
}
def test_invalid_token():
    headers = {
        'Authorization': 'Bearer your-token-here',
    }
    response = requests.post('http://127.0.0.1:6191/ollama/gemma2/2b/', headers=headers, data=json.dumps(data))
    assert response.status_code == 401, response.text


def test_valid_token():
    headers = {
        'Authorization': 'Bearer your_token_here',
    }
    response = requests.post('http://127.0.0.1:6191/ollama/gemma2/2b/', headers=headers, data=json.dumps(data))
    assert response.status_code == 200, response.text
    print(response.json())
