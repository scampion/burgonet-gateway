#!/bin/bash

# Test Ollama Gemma2 2B model with a simple greeting
echo "Testing Ollama Gemma2 2B model with greeting..."
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
echo "Testing LlamaCPP Phi4 model with yes/no question..."

curl http://127.0.0.1:8080/llamacpp/phi4/  \
-H "Authorization: Bearer your-token-here" \
-d '{
      "prompt": "Answer Yes or No",
      "n_predict": 128
    }
' | jq

echo "----------------------------------------------------"

# Test Ollama Gemma2 2B model with confidential information question
echo "Testing Ollama Gemma2 2B model with confidential information question..."
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

# Test Ollama Gemma2 2B model with personal information question
echo "Testing Ollama Gemma2 2B model with personal information question..."
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

# Test LlamaCPP Phi4 model with information sharing question
# Note: This appears to be using the wrong endpoint/model combination
echo "Testing LlamaCPP Phi4 model with information sharing question (potential misconfiguration)..."
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



