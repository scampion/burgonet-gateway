#!/usr/bin/env python3
import json
import pprint
import sys
import redis

redis_host = sys.argv[1]
redis_port = sys.argv[2]

rd = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)


tokens = rd.keys("responses:*")
for token in tokens:
    print(token)
    for k, v in rd.hgetall(token).items():
        print(k, v)
        response = json.loads(v)
        pprint.pprint(response)
        provider = response['provider']
        # parse the response 


    print("-" * 80)
