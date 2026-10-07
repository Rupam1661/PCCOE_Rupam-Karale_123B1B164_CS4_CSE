import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(ROOT, "Input_Data", "sample_code")
RULES_FILE = os.path.join(ROOT, "Input_Data", "guidelines", "coding_rules.txt")
RESULTS_DIR = os.path.join(ROOT, "Evaluation_Results")
DB_PATH = os.path.join(RESULTS_DIR, "findings.db")
OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "llama3.2:3b"
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_LINES = 12
CHUNK_STRIDE = 8
TOP_K = 3
