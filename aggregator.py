#!/usr/bin/env python3
import json
import pprint
import sys
import redis
from frontend.app.models import DeepSeek, OpenAI, Anthropic, Azure, Ollama

parsers = {
    'deepseek': DeepSeek.parse_response,
    'openai': OpenAI.parse_response,
    'anthropic': Anthropic.parse_response,
    'azure': Azure.parse_response,
    'ollama': Ollama.parse_response,
}

def main():
    if len(sys.argv) != 3:
        print("Usage: aggregator.py <redis_host> <redis_port>")
        sys.exit(1)

    redis_host = sys.argv[1]
    redis_port = sys.argv[2]

    rd = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

    tokens = rd.keys("responses:*")
    for token in tokens:
        print(f"\nProcessing token: {token}")
        for k, v in rd.hgetall(token).items():
            try:
                print(f"{k}")
                response = json.loads(v)
                provider_name = response['provider']
                parsed_response = parsers[provider_name](response)
                parsed_response['provider'] = provider_name
                pprint.pprint(parsed_response)
                print("-" * 80)
            except Exception as e:
                print(f"Error: {e} {v}")
                continue


if __name__ == "__main__":
    main()

