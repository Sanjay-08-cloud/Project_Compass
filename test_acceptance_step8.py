import requests
import json
import time

queries = [
    "what is tech stack used in AgriGrow project?",
    "what is the model accuracy?",
    "who are the team members?",
    "what is the capital of France?"
]

for q in queries:
    print("=" * 80)
    print(f"QUERY: {q}")
    t0 = time.time()
    try:
        res = requests.post(
            "http://127.0.0.1:8000/api/chat/query/",
            json={"query": q, "debug": True, "requested_project_ids": [4]},
            stream=True,
            timeout=120
        )
        elapsed = time.time() - t0
        print(f"STATUS CODE: {res.status_code}")
        answer_tokens = []
        citations = []
        debug_info = {}
        refused = False
        refusal_reason = None
        final_answer = ""

        for line in res.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data: "):
                data_str = line[6:].strip()
                try:
                    event = json.loads(data_str)
                    etype = event.get("type")
                    if etype == "token":
                        answer_tokens.append(event.get("text", ""))
                    elif etype == "citation":
                        citations.append(event)
                    elif etype == "debug":
                        debug_info = event.get("debug_info", {})
                    elif etype in ("refused", "refusal"):
                        refused = True
                        refusal_reason = event.get("reason")
                        final_answer = event.get("text") or event.get("answer", "")
                        if event.get("debug"):
                            debug_info = event.get("debug")
                    elif etype == "done":
                        if not final_answer:
                            final_answer = "".join(answer_tokens)
                        if event.get("debug"):
                            debug_info = event.get("debug")
                except Exception as je:
                    pass

        if not final_answer and answer_tokens:
            final_answer = "".join(answer_tokens)

        print(f"ELAPSED: {elapsed:.2f}s")
        print(f"REFUSED: {refused}")
        if refusal_reason:
            print(f"REFUSAL REASON: {refusal_reason}")
        print(f"ANSWER:\n{final_answer.strip()}\n")
        print("CITATIONS:")
        for c in citations:
            print(f"  - Chunk: {c.get('chunk_id')} | Page: {c.get('page')} | Score: {c.get('score')} | Doc: {c.get('document')}")
        if debug_info:
            print(f"DEBUG: path_a_thresh={debug_info.get('path_a_threshold')}, path_b_thresh={debug_info.get('path_b_threshold')}, max_score={debug_info.get('rerank_max_score')}, gate_passed={debug_info.get('gate_passed')}")
            print(f"TOP RERANK SCORES: {debug_info.get('cross_encoder_top5')}")
    except Exception as e:
        print(f"EXCEPTION: {e}")
print("=" * 80)
