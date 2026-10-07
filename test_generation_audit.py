"""
Standalone audit script for Stage 3: LLM Generation Quality.
Runs the exact test query 3 times against Ollama with calibrated parameters
and compares output length, sentence structure, and citation consistency.
"""

import json
import requests
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"

SYSTEM_PROMPT = (
    "Answer ONLY using the provided context, in 2-4 clear sentences. "
    "Cite sources inline as [1], [2]. Do not repeat the question. "
    "Do not add conversational filler or disclaimers unless the context is insufficient."
)

SAMPLE_CHUNK = (
    "Project Apollo uses PostgreSQL 16.2 hosted on AWS RDS Aurora in a multi-AZ deployment. "
    "Connection pooling is handled by PgBouncer configured in transaction pooling mode with "
    "max_client_conn=1000 and default_pool_size=25. Backup retention is set to 30 days with "
    "automated point-in-time recovery enabled."
)

USER_PROMPT = (
    f"CONTEXT:\n[1] {SAMPLE_CHUNK}\n\n"
    "QUESTION: How is connection pooling and the database configured in Project Apollo?"
)

PAYLOAD = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT}
    ],
    "options": {
        "temperature": 0.2,
        "top_p": 0.9,
        "num_predict": 512
    },
    "stop": ["<|im_end|>", "<|endoftext|>", "<|im_start|>"],
    "stream": False
}

def main():
    print("=== Stage 3 LLM Generation Consistency Test ===")
    print(f"Model: {MODEL} | Temperature: 0.2 | top_p: 0.9 | num_predict: 512\n")

    runs = []
    for i in range(1, 4):
        print(f"--- Running Query Iteration #{i} ---")
        try:
            resp = requests.post(OLLAMA_URL, json=PAYLOAD, timeout=45)
            if resp.status_code != 200:
                print(f"Error: {resp.status_code} - {resp.text}")
                continue
            data = resp.json()
            content = data.get("message", {}).get("content", "").strip()
            
            # Count sentences
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if s.strip()]
            citations = re.findall(r'\[\d+\]', content)

            print(f"Response #{i}:")
            print(content)
            print(f"Sentence count: {len(sentences)} (Target: 2-4)")
            print(f"Citations found: {citations}")
            print(f"Character length: {len(content)}")
            print("-" * 50)

            runs.append({
                "iteration": i,
                "content": content,
                "sentence_count": len(sentences),
                "citations": citations,
                "length": len(content)
            })
        except Exception as e:
            print(f"Failed iteration #{i}: {e}")

    print("\n=== Summary Across Runs ===")
    for r in runs:
        print(f"Run {r['iteration']}: {r['sentence_count']} sentences, {len(r['citations'])} citation(s), {r['length']} chars")
    print("=== Stage 3 Audit Complete ===")

if __name__ == "__main__":
    main()
