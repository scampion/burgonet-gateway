import json
import requests
import os

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer your_token_here',
}

def test_deepseek():
    print("Testing Deepseek")
    json_data = {
        'model': 'deepseek-chat',
        'messages': [
            {
                'role': 'system',
                'content': 'You are a helpful assistant.',
            },
            {
                'role': 'user',
                'content': 'Hello!',
            },
        ],
        'stream': False,
    }
    response = requests.post(
        'http://127.0.0.1:6191/api.deepseek.com/chat/completions',
        headers=headers,
        json=json_data,
        verify=False
      )

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
        'http://127.0.0.1:6191/api.openai.com/v1/chat/completions',
        headers=headers,
        json=data
    )

    assert response.status_code == 200, response.text
    assert "gpt-4o-mini" in response.json()["model"], response.json()

def test_gemini():
    print("Testing Gemini")
    json_data = {
        "model": "gemini-1.5-flash",
        "prompt": {
            "content": "Hi"
        }
    }
    response = requests.post(
        'http://127.0.0.1:6191/gemini',
        headers=headers,
        json=json_data,
    )

    assert response.status_code == 200, response.text
    assert "gemini-1.5-flash" in response.json()["model"], response.json()

