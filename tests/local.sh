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
}' | jq

echo "----------------------------------------------------"
echo " LLAMACPP  LLAMACPP  LLAMACPP  LLAMACPP  LLAMACPP  LLAMACPP "


curl http://127.0.0.1:8080/llamacpp/phi4/  \
-H "Authorization: Bearer your-token-here" \
-d '{
      "prompt": "Answer Yes or No",
      "n_predict": 128
    }
' | jq

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


curl http://127.0.0.1:8080/ollama/gemma2/2b/  \
-H "Authorization: Bearer your-token-here" \
-d '{
  "model": "gemma2:2b-instruct-q6_K",                                                                                                                        "messages": [
    {
      "role": "user",
      "content": "Can I share information with my you ? My name is Jean-Claude Dusse"
    }
  ] ,
  "stream": false
}'

echo "----------------------------------------------------"


curl http://127.0.0.1:8080/llamacpp/phi4//  \
-H "Authorization: Bearer your-token-here" \
-d '{
  "model": "gemma2:2b-instruct-q6_K",                                                                                                                        "messages": [
    {
      "role": "user",
      "content": "Can I share information with my you ?"
    }
  ] ,
  "stream": false
}'

echo "----------------------------------------------------"



