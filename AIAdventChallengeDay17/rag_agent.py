#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import math
from pathlib import Path
from typing import List, Dict, Tuple
import urllib.request

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_LLM_MODEL = "qwen2.5"          # поменяй на свою модель из `ollama list`
DEFAULT_INDEX_PATH = "index.jsonl"


# -----------------------------
# Ollama helpers
# -----------------------------
def post_json(url: str, payload: Dict, timeout: int = 120) -> Dict:
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ollama_embed(ollama_url: str, model: str, text: str) -> List[float]:
    # /api/embed (новый)
    try:
        data = post_json(f"{ollama_url}/api/embed", {"model": model, "input": text}, timeout=120)
        if "embeddings" in data and data["embeddings"]:
            return data["embeddings"][0]
    except Exception:
        pass

    # /api/embeddings (старый)
    data2 = post_json(f"{ollama_url}/api/embeddings", {"model": model, "prompt": text}, timeout=120)
    if "embedding" in data2:
        return data2["embedding"]

    raise RuntimeError("Неожиданный формат ответа Ollama embeddings.")


def ollama_generate(ollama_url: str, model: str, prompt: str) -> str:
    """
    Самый простой вариант: /api/generate.
    """
    data = post_json(
        f"{ollama_url}/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
        },
        timeout=300,
    )
    # обычно: {"response": "..."}
    return data.get("response", "").strip()


# -----------------------------
# Vector math
# -----------------------------
def cosine_similarity(a: List[float], b: List[float]) -> float:
    # устойчиво и без numpy
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


# -----------------------------
# Index loading / retrieval
# -----------------------------
def load_index(index_path: Path) -> List[Dict]:
    items = []
    with index_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def retrieve_top_k(items: List[Dict], query_emb: List[float], top_k: int) -> List[Tuple[float, Dict]]:
    scored = []
    for it in items:
        sim = cosine_similarity(query_emb, it["embedding"])
        scored.append((sim, it))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


# -----------------------------
# Prompts
# -----------------------------
def build_prompt_no_rag(question: str) -> str:
    return (
        "Ты полезный ассистент. Ответь на вопрос максимально точно.\n\n"
        f"Вопрос: {question}\n"
        "Ответ:"
    )


def build_prompt_with_rag(question: str, contexts: List[Dict]) -> str:
    ctx_blocks = []
    for i, c in enumerate(contexts, start=1):
        src = c.get("source", "unknown")
        chunk_i = c.get("chunk_index", "?")
        text = c.get("text", "")
        ctx_blocks.append(f"[{i}] source={src} chunk={chunk_i}\n{text}")

    context_text = "\n\n".join(ctx_blocks)
    
    return (
        "Ты полезный ассистент. Используй ТОЛЬКО контекст ниже, чтобы ответить на вопрос.\n"
        "Если в контексте нет ответа — честно скажи, что информации недостаточно.\n\n"
        "КОНТЕКСТ:\n"
        f"{context_text}\n\n"
        f"ВОПРОС: {question}\n"
        "ОТВЕТ:"
    )


# -----------------------------
# Main
# -----------------------------
def main():
    ap = argparse.ArgumentParser(description="Day 17: RAG vs no-RAG comparison (Ollama).")
    ap.add_argument("--index", default=DEFAULT_INDEX_PATH, help="Path to index.jsonl")
    ap.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Ollama base URL")
    ap.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="Embedding model for retrieval")
    ap.add_argument("--llm-model", default=DEFAULT_LLM_MODEL, help="LLM model for generation")
    ap.add_argument("--top-k", type=int, default=4, help="How many chunks to retrieve")
    ap.add_argument("--question", required=True, help="Question to ask")
    args = ap.parse_args()

    index_path = Path(args.index)
    if not index_path.exists():
        raise SystemExit(f"Не найден файл индекса: {index_path.resolve()}")

    items = load_index(index_path)

    # 1) ответ без RAG
    prompt_plain = build_prompt_no_rag(args.question)
    answer_plain = ollama_generate(args.ollama_url, args.llm_model, prompt_plain)

    # 2) ответ с RAG
    q_emb = ollama_embed(args.ollama_url, args.embed_model, args.question)
    top = retrieve_top_k(items, q_emb, args.top_k)
    contexts = [it for _, it in top]

    prompt_rag = build_prompt_with_rag(args.question, contexts)
    answer_rag = ollama_generate(args.ollama_url, args.llm_model, prompt_rag)

    # печать сравнения
    print("\n" + "=" * 80)
    print("ВОПРОС:")
    print(args.question)

    print("\n" + "-" * 80)
    print("ОТВЕТ БЕЗ RAG:")
    print(answer_plain if answer_plain else "(пустой ответ)")

    print("\n" + "-" * 80)
    print("ОТВЕТ С RAG:")
    print(answer_rag if answer_rag else "(пустой ответ)")

    # print("\n" + "-" * 80)
    # print(f"ТОП-{args.top_k} КОНТЕКСТОВ (для RAG):")
    # for rank, (sim, it) in enumerate(top, start=1):
    #     print(f"\n#{rank} sim={sim:.4f} source={it.get('source')} chunk={it.get('chunk_index')}")
    #     preview = (it.get("text", "")[:400] + "…") if len(it.get("text", "")) > 400 else it.get("text", "")
    #     print(preview)

    # print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
