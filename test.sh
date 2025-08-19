curl http://localhost:8003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mysecretkey123" \
  -d '{
    "model": "/root/.cache/huggingface/modelscope/hub/models/Qwen/Qwen2-7b",
    "messages":[
      {"role":"system","content":"You are a helpful assistant."},
      {"role":"user","content":"日本的首都是哪里？"}
    ],
    "temperature":0.7,
    "top_p":0.8,
    "max_tokens":200
  }'
