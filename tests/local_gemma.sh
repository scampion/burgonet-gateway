curl http://127.0.0.1:8080/ollama/gemma2/2b/ -d '{
  "model": "gemma2:2b-instruct-q6_K",                                                                                                                        "messages": [
    {
      "role": "user",
      "content": "Hi"
    }
  ] ,
  "stream": false
}'


