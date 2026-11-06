# 07_test_model.py
# Quick test: can Python talk to the AI model running in Ollama?

import ollama

# The model we downloaded with "ollama pull"
MODEL = "qwen2.5-coder:7b"

# Send one message to the model, just like typing in a chat
response = ollama.chat(
    model=MODEL,
    messages=[
        {"role": "user", "content": "Write a SQL query that counts the rows in a table called orders. Reply with only the SQL."}
    ]
)

# The model's reply is inside response["message"]["content"]
print(response["message"]["content"])