#!/usr/bin/env python3
import hashlib
import json
import pprint
import time
import sys
from json import JSONDecodeError

import redis

nginx_log_filepath = sys.argv[1]
redis_host = sys.argv[2]
redis_port = sys.argv[3]

rd = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)

def dispatch(line):
    rd.publish('nginx_log', line)
    data = json.loads(line)
    if data['status'] != "200":
        raise Exception(f"Status code is not 200: {data['status']}")
    token = data['authorization'][7:]
    keys_to_keep = ['time_local', 'request_body', 'response_body', 'provider', 'model_name', 'model_version']
    data = {k: v for k, v in data.items() if k in keys_to_keep}
    request_body = json.loads(data['request_body'])
    response_body = json.loads(data['response_body'])
    data['request_body'] = request_body
    data['response_body'] = response_body
    data['token'] = token
    pprint.pprint(data)
    data_hash = hashlib.sha1(json.dumps(data).encode()).hexdigest()
    with rd.pipeline() as pipe:
        pipe.hset(f'responses:{token}', mapping={data_hash: json.dumps(data)})
        pipe.hexpire(f'responses:{token}', 172800, data_hash)
        pipe.execute()
        print(f"Data saved with hash: {data_hash}")


#open the file and read the line by line and wait for the new line to be added
with open(nginx_log_filepath) as f:
    while True:
        line = f.readline()
        if not line:
            time.sleep(0.1)
            continue
        try:
            dispatch(line)
            print("-" * 80)
        except Exception as e:
            # log the error with the class name and the error message
            print(f"🚨️ Error:{e.__class__.__name__}   {str(e)} {line}")
            continue