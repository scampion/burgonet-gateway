import json
import requests

headers = {
    'Authorization': 'Bearer your_token_here',
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

