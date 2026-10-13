import requests
import json

queries = [
    "what is tech stack used in AgriGrow project?",
    "what is the model accuracy?",
    "who are the team members?",
    "what is the capital of France?"
]

for q in queries:
    res = requests.post("http://127.0.0.1:8000/api/chat/", json={"query": q, "debug": True, "requested_project_ids": [4]})
    data = res.json()
    dbg = data.get("debug", {})
    print("=" * 80)
    print(f"QUERY: {q}")
    print(f"Refused: {data.get('refused')} | Refusal Reason: {data.get('refusal_reason')} | Winning Path: {data.get('refusal_path')}")
    print(f"Answer: {data.get('answer')}")
    print(f"BM25 top-3: {dbg.get('bm25_top_10', [])[:3]}")
    print(f"FAISS top-3: {dbg.get('faiss_top_10', [])[:3]}")
    print(f"RRF top-3: {dbg.get('rrf_fused_top_10', [])[:3]}")
    print(f"Cross-encoder raw & norm top-3: {dbg.get('cross_encoder_raw_top_5', [])[:3]}")
    print(f"Thresholds: {dbg.get('threshold')}")
    print(f"Compared value: {dbg.get('compared_value')}")
print("=" * 80)
