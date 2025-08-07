import requests

def ask_if_indian_origin(name):
    prompt = f"""
You are an expert in identifying name origins.

Determine whether the following person's name likely originates from India:
Name: {name}

Answer with only "Yes" or "No".
"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "deepseek" or "llama3",  # use the model name you pulled via `ollama pull`
            "prompt": prompt,
            "stream": False
        }
    )
    output = response.json()["response"]
    return "yes" in output.lower()