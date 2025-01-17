#!/bin/bash
curl http://127.0.0.1:8080/ollama/gemma2/2b/  \
-H "Authorization: Bearer your-token-here" \
-d '{
  "model": "gemma2:2b-instruct-q6_K",                                                                                                                        "messages": [
    {
      "role": "user",
      "content": "Hi"
    }
  ] ,
  "stream": false
}'

echo "----------------------------------------------------"

curl http://127.0.0.1:8080/ollama/gemma2/2b/  \
-H "Authorization: Bearer your-token-here" \
-d '{
  "model": "gemma2:2b-instruct-q6_K",                                                                                                                        "messages": [
    {
      "role": "user",
      "content": "Can I share confidential information with my you ?"
    }
  ] ,
  "stream": false
}'

echo "----------------------------------------------------"


