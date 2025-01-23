import json
import requests

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your_token_here',
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
#
# curl https://api.anthropic.com/v1/messages \
#      --header "x-api-key: $ANTHROPIC_API_KEY" \
#      --header "anthropic-version: 2023-06-01" \
#      --header "content-type: application/json" \
#      --data \
# '{
#     "model": "claude-3-5-sonnet-20241022",
#     "max_tokens": 1024,
#     "messages": [
#         {"role": "user", "content": "Hello, world"}
#     ]
# }'
#
# {
#   "content": [
#     {
#       "text": "Hi! My name is Claude.",
#       "type": "text"
#     }
#   ],
#   "id": "msg_013Zva2CMHLNnXjNJJKqJ2EF",
#   "model": "claude-3-5-sonnet-20241022",
#   "role": "assistant",
#   "stop_reason": "end_turn",
#   "stop_sequence": null,
#   "type": "message",
#   "usage": {
#     "input_tokens": 2095,
#     "output_tokens": 503
#   }
# }