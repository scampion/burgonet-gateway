import json
import requests

headers = {
    'Authorization': 'Bearer your_token_here',
    'Content-Type': 'application/json'
}


def test_deepseek():
    print("Testing Deepseek")
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        "stream": False
    }
    response = requests.post('http://localhost:6191/deepseek/chat/completions', headers=headers, data=json.dumps(data))

    assert response.status_code == 200, response.text
    assert response.json()["model"] == "deepseek-chat", response.json()

def test_openai():
    print("Testing OpenAI")
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Hi"}
        ]
    }
    response = requests.post(
        'http://localhost:6191/api.openai.com/v1/chat/completions',
        headers=headers,
        json=data
    )

    assert response.status_code == 200, response.text
    assert response.json()["model"] == "gpt-4o-mini", response.json()

