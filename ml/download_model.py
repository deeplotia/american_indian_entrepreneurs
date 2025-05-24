from transformers import AutoTokenizer, AutoModelForCausalLM

#modelid = "meta-llama/Meta-Llama-3-8B" # requires approval as it's under gated repo https://huggingface.co/meta-llama/Meta-Llama-3-8B

modelid = "deepseek-ai/deepseek-llm-7b-base"
tokenizer = AutoTokenizer.from_pretrained(modelid)
model = AutoModelForCausalLM.from_pretrained(modelid)

# Or if you want to download using huggingface-cli

# huggingface-cli download meta-llama/Meta-Llama-3-8B --local-dir ./llama3-8b