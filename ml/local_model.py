from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 🔧 Path to your local LLM (adjust this to your setup)
MODEL_PATH = "/path/to/your/local/llama3_or_deepseek_model"

print("📦 Loading local model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, torch_dtype=torch.float16).to("cuda")

def ask_if_indian_origin(name):
    """Use local LLM to classify name origin"""
    if not name:
        return False
    prompt = f"""
You are an expert in identifying name origins.

Determine whether the following person's name likely originates from India:
Name: {name}

Answer with only "Yes" or "No".
"""
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=10)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return "yes" in response.lower()