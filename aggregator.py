#!/usr/bin/env python3
import json
import pprint
import sys
import redis
from frontend.models import DeepSeek, OpenAI, Anthropic, Azure

def get_provider_class(provider_name):
    """Get the appropriate Provider subclass based on provider name"""
    provider_classes = {
        'deepseek': DeepSeek,
        'openai': OpenAI,
        'anthropic': Anthropic,
        'azure': Azure
    }
    return provider_classes.get(provider_name.lower())

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
            print(f"Key: {k}")
            response = json.loads(v)
            provider_name = response.get('provider')
            
            if not provider_name:
                print("No provider specified in response")
                continue
                
            ProviderClass = get_provider_class(provider_name)
            if not ProviderClass:
                print(f"Unknown provider: {provider_name}")
                continue
                
            provider = ProviderClass()
            try:
                parsed_response = provider.parse_response(response)
                print("Parsed response:")
                pprint.pprint(parsed_response)
            except Exception as e:
                print(f"Error parsing response: {str(e)}")
                
        print("-" * 80)

if __name__ == "__main__":
    main()
