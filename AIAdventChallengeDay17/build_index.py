#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple
import urllib.error
import urllib.request


# ----------------------------
# Константы / дефолты
# ----------------------------
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "nomic-embed-text"

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_OVERLAP = 200

ALLOWED_EXT = {
    ".txt", ".md",
    ".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h",
    ".html", ".css", ".json", ".yaml", ".yml",
    ".sql", ".sh", ".zsh",
}


# ----------------------------
# Ошибки
# ----------------------------
class BuildIndexError(Exception):
    """Базовая ошибка пайплайна с понятным сообщением."""


class OllamaConnectionError(BuildIndexError):
    pass


class OllamaModelError(BuildIndexError):
    pass


class InputDataError(BuildIndexError):
    pass


# ----------------------------
# Утилиты вывода
# ----------------------------
def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def fatal(msg: str, hint: Optional[str] = None, exit_code: int = 1) -> None:
    eprint("\n❌ Ошибка: " + msg)
    if hint:
        eprint("💡 Подсказка: " + hint)
    sys.exit(exit_code)


# ----------------------------
# Чтение файлов / чанкинг
# ----------------------------
def iter_files(root: Path) -> Iterator[Path]:
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXT:
            yield p


def read_text_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # иногда код/данные могут быть не-utf8 — читаем с заменой символов
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
    except Exception:
        return None


def file_sha1_12(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[Tuple[int, int, str]]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    n = len(text)
    if n == 0:
        return []

    step = chunk_size - overlap
    if chunk_size <= 0:
        raise InputDataError("chunk_size должен быть > 0.")
    if overlap < 0:
        raise InputDataError("overlap не может быть отрицательным.")
    if step <= 0:
        raise InputDataError(
            "overlap должен быть меньше chunk_size, иначе чанкинг зациклится."
        )

    chunks: List[Tuple[int, int, str]] = []
    start = 0
    while start < n:
        end = min(n, start + chunk_size)
        piece = text[start:end].strip()
        if piece:
            chunks.append((start, end, piece))
        if end == n:
            break
        start += step

    return chunks


# ----------------------------
# Ollama API
# ----------------------------
def _post_json(url: str, payload: Dict, timeout_sec: int = 60) -> Dict:
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as ex:
        # читаем тело ответа если есть
        try:
            body = ex.read().decode("utf-8")
        except Exception:
            body = ""
        raise BuildIndexError(
            f"Ollama вернула HTTP {ex.code} на {url}. Ответ: {body[:300]}"
        )
    except urllib.error.URLError as ex:
        raise OllamaConnectionError(
            f"Не удалось подключиться к Ollama по адресу {url}. Детали: {ex}"
        )
    except json.JSONDecodeError:
        raise BuildIndexError("Не удалось разобрать JSON-ответ от Ollama.")
    except Exception as ex:
        raise BuildIndexError(f"Неожиданная ошибка при запросе к Ollama: {ex}")


def check_ollama_running(ollama_url: str) -> None:
    # простой health-check: GET /
    try:
        with urllib.request.urlopen(ollama_url, timeout=5) as resp:
            _ = resp.read()
    except Exception:
        raise OllamaConnectionError(
            f"Ollama не отвечает на {ollama_url}."
        )


def check_model_available(ollama_url: str, model: str) -> None:
    """
    Нормально проверить список моделей через API проще всего: /api/tags.
    Если не получается — не валим всё, но при ошибке эмбеддинга дадим подсказку.
    """
    try:
        data = _post_json(f"{ollama_url}/api/tags", payload={}, timeout_sec=10)
        # форматы могут отличаться, но часто: {"models":[{"name":"..."}]}
        names = set()
        if isinstance(data, dict) and "models" in data and isinstance(data["models"], list):
            for m in data["models"]:
                if isinstance(m, dict) and "name" in m:
                    names.add(str(m["name"]))
        if names and not any(n == model or n.startswith(model + ":") for n in names):
            raise OllamaModelError(
                f"Модель '{model}' не найдена в Ollama."
            )
    except OllamaConnectionError:
        raise
    except OllamaModelError:
        raise
    except Exception:
        # если /api/tags вдруг не поддерживается/меняется — просто пропускаем
        return


def ollama_embed(ollama_url: str, model: str, input_text: str) -> List[float]:
    """
    Пробуем сначала /api/embed (современный), затем /api/embeddings (старый).
    """
    # /api/embed
    try:
        data = _post_json(
            f"{ollama_url}/api/embed",
            payload={"model": model, "input": input_text},
            timeout_sec=60,
        )
        if "embeddings" in data and isinstance(data["embeddings"], list) and data["embeddings"]:
            emb = data["embeddings"][0]
            if isinstance(emb, list) and emb and isinstance(emb[0], (int, float)):
                return emb
        # если формат не тот
    except BuildIndexError:
        # важно: если /api/embed есть, но дал осмысленную ошибку — пробросим её
        # однако если это 404 или подобное, можно попробовать старый endpoint.
        # (в _post_json 404 превращается в BuildIndexError — поэтому ниже аккуратно)
        pass
    except Exception:
        pass

    # /api/embeddings (старый)
    data2 = _post_json(
        f"{ollama_url}/api/embeddings",
        payload={"model": model, "prompt": input_text},
        timeout_sec=60,
    )
    if "embedding" in data2 and isinstance(data2["embedding"], list):
        emb = data2["embedding"]
        if emb and isinstance(emb[0], (int, float)):
            return emb

    raise BuildIndexError(
        "Ollama вернула неожиданный формат ответа для embeddings."
    )


# ----------------------------
# Основной процесс
# ----------------------------
@dataclass
class Config:
    data_dir: Path
    out_index: Path
    out_meta: Path
    ollama_url: str
    model: str
    chunk_size: int
    overlap: int


def build_index(cfg: Config) -> None:
    if not cfg.data_dir.exists():
        raise InputDataError(
            f"Папка с документами не найдена: {cfg.data_dir.resolve()}"
        )

    files = list(iter_files(cfg.data_dir))
    if not files:
        raise InputDataError(
            f"В папке {cfg.data_dir.resolve()} не найдено файлов с расширениями: {sorted(ALLOWED_EXT)}"
        )

    # проверим Ollama
    check_ollama_running(cfg.ollama_url)
    # попробуем проверить модель заранее (если API поддерживает)
    check_model_available(cfg.ollama_url, cfg.model)

    # подготовка вывода
    cfg.out_index.parent.mkdir(parents=True, exist_ok=True)
    cfg.out_meta.parent.mkdir(parents=True, exist_ok=True)

    # перезапишем индекс
    if cfg.out_index.exists():
        cfg.out_index.unlink()

    t0 = time.time()
    total_chunks = 0
    embedding_dim: Optional[int] = None
    skipped_files = 0

    with cfg.out_index.open("w", encoding="utf-8") as out:
        for i, path in enumerate(files, start=1):
            rel = path.relative_to(Path.cwd()) if path.is_absolute() else path
            text = read_text_file(path)
            if not text:
                skipped_files += 1
                eprint(f"⚠️  Пропуск: {rel} (не удалось прочитать как текст)")
                continue

            try:
                chunks = chunk_text(text, cfg.chunk_size, cfg.overlap)
            except BuildIndexError as ex:
                skipped_files += 1
                eprint(f"⚠️  Пропуск: {rel} (ошибка чанкинга: {ex})")
                continue

            doc_id = file_sha1_12(path)
            print(f"[{i}/{len(files)}] {rel} → {len(chunks)} chunks")

            for chunk_i, (start, end, chunk_str) in enumerate(chunks):
                try:
                    emb = ollama_embed(cfg.ollama_url, cfg.model, chunk_str)
                except OllamaConnectionError as ex:
                    raise OllamaConnectionError(
                        f"{ex}\nВо время обработки файла: {rel}"
                    )
                except BuildIndexError as ex:
                    # тут часто вылезает "model not found" и т.п.
                    raise BuildIndexError(
                        f"Не удалось получить эмбеддинг.\n"
                        f"Файл: {rel}\nЧанк: {chunk_i}\nПричина: {ex}"
                    )

                if embedding_dim is None:
                    embedding_dim = len(emb)

                item = {
                    "id": f"{doc_id}::{chunk_i}",
                    "doc_id": doc_id,
                    "source": str(rel),
                    "chunk_index": chunk_i,
                    "char_start": start,
                    "char_end": end,
                    "text": chunk_str,
                    "embedding": emb,
                    "model": cfg.model,
                }
                out.write(json.dumps(item, ensure_ascii=False) + "\n")
                total_chunks += 1

    meta = {
        "created_at_unix": int(time.time()),
        "data_dir": str(cfg.data_dir),
        "model": cfg.model,
        "ollama_url": cfg.ollama_url,
        "chunk_size": cfg.chunk_size,
        "overlap": cfg.overlap,
        "files_found": len(files),
        "files_skipped": skipped_files,
        "chunks_total": total_chunks,
        "embedding_dim": embedding_dim,
        "elapsed_sec": round(time.time() - t0, 3),
        "format": "jsonl (one chunk per line)",
    }
    cfg.out_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> Config:
    p = argparse.ArgumentParser(
        description="Build a local embeddings index (JSONL) using Ollama embeddings."
    )
    p.add_argument("--data-dir", default="data", help="Папка с документами (default: data)")
    p.add_argument("--out-index", default="index.jsonl", help="Файл индекса (default: index.jsonl)")
    p.add_argument("--out-meta", default="meta.json", help="Файл метаданных (default: meta.json)")
    p.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help=f"Ollama URL (default: {DEFAULT_OLLAMA_URL})")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Embedding model (default: {DEFAULT_MODEL})")
    p.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help=f"Размер чанка в символах (default: {DEFAULT_CHUNK_SIZE})")
    p.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help=f"Перекрытие чанков в символах (default: {DEFAULT_OVERLAP})")

    args = p.parse_args()
    return Config(
        data_dir=Path(args.data_dir),
        out_index=Path(args.out_index),
        out_meta=Path(args.out_meta),
        ollama_url=args.ollama_url.rstrip("/"),
        model=args.model,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )


def main() -> None:
    cfg = parse_args()

    try:
        build_index(cfg)
    except OllamaConnectionError as ex:
        fatal(
            str(ex),
            hint=(
                "Запусти Ollama и проверь, что она слушает порт 11434.\n"
                "Проверка: curl http://localhost:11434\n"
                "Если ставил через brew: в отдельном терминале запусти: ollama serve"
            ),
            exit_code=2,
        )
    except OllamaModelError as ex:
        fatal(
            str(ex),
            hint=f"Установи модель: ollama pull {cfg.model}\nПроверь: ollama list",
            exit_code=3,
        )
    except InputDataError as ex:
        fatal(
            str(ex),
            hint=(
                "Проверь, что папка data существует и внутри есть .md/.txt/.py и т.п.\n"
                f"Текущая папка: {Path.cwd()}"
            ),
            exit_code=4,
        )
    except BuildIndexError as ex:
        fatal(
            str(ex),
            hint=(
                "Чаще всего причина — модель не установлена или неправильный URL.\n"
                f"Проверь модель: ollama pull {cfg.model}\n"
                f"Проверь URL: {cfg.ollama_url}"
            ),
            exit_code=5,
        )
    except KeyboardInterrupt:
        fatal("Остановлено пользователем (Ctrl+C).", exit_code=130)

    print("\n✅ Готово!")
    print(f"Index: {cfg.out_index.resolve()}")
    print(f"Meta:  {cfg.out_meta.resolve()}")


if __name__ == "__main__":
    main()

