# Nasdaq Data Scraper

## How to run script

- [x] install python.
- [x] open terminal in project dir.
- [x] run `pip install virtualenv` command to install virtualenv.
- [x] create and activate virtual environment.
    - [x] run `virtualenv <my_env_name>` command.
    - [x] (windows) run `<my_env_name>\scripts\activate` command to activate virtualenv.
    - [x] (mac/linux) run `source <my_env_name>/bin/activate` command to activate virtualenv.
- [x] run `pip install -r requirements.txt` command to install dependencies.
- [x] run `python run.py` command to start script.
- [x] `nasdaq_ceo.xlsx` file will be generated after script completes.


# ML Model to identify the CEO Names

- There are two ways to use it 

1. Run ollama serve and run the intended model and call Ollama api locally to get the CEO name heuristics
    - Pros: Very Fast, Scalable, Parralel, Product-style batching
2. Download the model
    1. From huggingface using transformers
        - refer download_model.py
        - the file size would be quite high (13-15GB)
        - Pros: High flexibility, native Python use.
	    - Cons: Slow for many queries (~3–5 sec per prompt), high RAM/GPU usage. would take hours to complete 10k requests

    2. llama.cpp (CPU/GPU optimized .gguf format):
        - The file size is small approximately 4GB.
        - Steps
            1. Download .gguf model file:
              - From: https://huggingface.co/TheBloke
            2. Clone llama.cpp and build it:

                ```
                git clone https://github.com/ggerganov/llama.cpp
                cd llama.cpp
                make
                ```

                ```./main -m ./path-to/llama3.gguf -p "Hello, world"```

        - Steps to build .gguf model file:
            ```
            git clone https://github.com/ggerganov/llama.cpp
            cd llama.cpp
            mkdir build && cd build
            cmake ..
            cmake --build . --config Release
            ```

        - Execute
            ```
            ./llama-cli -m ~/Documents/deep/personal/ml/models/deepseek-llm-7b-base-q5_k_m.gguf -p "Is Deep Lotia an Indian Name? Yes or No"
            ```


# Findings
1. Good VPN. not sure if it works (VPN for Google apps (some devs were not succesfull)
2. Change the approach and use APIs
3. Try to fix the consent issue
4. SEC EDGAR local data (exploring)
   - huge files. Taking time to open. Didn't found CEO data in compaines 
5. names_match.py (very bad approach. deprecating it)