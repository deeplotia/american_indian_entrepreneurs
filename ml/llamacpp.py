from llama_cpp import Llama
import concurrent.futures

# Update with your actual GGUF model path
MODEL_PATH = "/Users/deeplotia/Documents/deep/personal/ml/models/deepseek-llm-7b-base-q5_k_m.gguf"

# Initialize model (adjust n_ctx and threads if needed)
llm = Llama(model_path=MODEL_PATH, n_ctx=512, n_threads=4)

def is_indian_name(name: str) -> str:
    prompt = f'Is the name "{name}" of Indian origin? Answer with Yes or No only.'
    output = llm(prompt, max_tokens=10, stop=["\n"], echo=False)
    response = output["choices"][0]["text"].strip().lower()
    return "yes" if "yes" in response else "no"

# Sample list of CEO names
ceo_names = ["Satya Nadella", "Sundar Pichai", "Elon Musk", "Arvind Krishna", "Tim Cook"]

# Multithreaded batch processing
def process_names(names):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(is_indian_name, name): name for name in names}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                results.append((name, result))
            except Exception as e:
                results.append((name, f"error: {e}"))
    return results

# Run
results = process_names(ceo_names)

# Output
for name, origin in results:
    print(f"{name}: {origin}")