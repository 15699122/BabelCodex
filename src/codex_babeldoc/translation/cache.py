"""SQLite-backed translation segment cache.

Keyed by a normalized hash of the source text, languages, translator, model,
effort and glossary/context versions so that the same segment translated under
different settings never collides. Uses WAL mode and a busy timeout so the
cache survives the concurrent reads a batching gateway produces.
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS translations (
    cache_key TEXT PRIMARY KEY,
    source_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    lang_in TEXT NOT NULL,
    lang_out TEXT NOT NULL,
    translator TEXT NOT NULL,
    model TEXT NOT NULL,
    effort TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    glossary_version TEXT,
    context_version TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_translations_created
    ON translations (created_at);
"""


class TranslationCache:
    """Process-safe SQLite cache for translated segments."""

    def __init__(
        self,
        db_path: Path | None,
        *,
        store_plaintext: bool = True,
        ttl_seconds: int | None = None,
    ) -> None:
        self.store_plaintext = store_plaintext
        self.ttl_seconds = ttl_seconds
        self._lock = threading.RLock()

        if db_path is None:
            self._db = None
            return

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(
            str(db_path),
            timeout=30,
            check_same_thread=False,
        )
        self._db.executescript(_SCHEMA)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=NORMAL")
        self._db.commit()

    @staticmethod
    def make_key(
        source_text: str,
        lang_in: str,
        lang_out: str,
        translator: str,
        model: str,
        effort: str,
        prompt_version: str,
        glossary_version: str | None,
        context_version: str | None,
    ) -> str:
        """Deterministic cache key covering every input that affects output."""
        parts = (
            source_text,
            lang_in,
            lang_out,
            translator,
            model,
            effort,
            prompt_version,
            glossary_version or "",
            context_version or "",
        )
        raw = "\x00".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> str | None:
        with self._lock:
            if self._db is None:
                return None
            row = self._db.execute(
                "SELECT translated_text, created_at FROM translations WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if row is None:
            return None
        translated, created = row
        if self.ttl_seconds is not None and time.time() - created > self.ttl_seconds:
            return None
        return translated

    def put(
        self,
        cache_key: str,
        source_text: str,
        translated_text: str,
        *,
        lang_in: str,
        lang_out: str,
        translator: str,
        model: str,
        effort: str,
        prompt_version: str,
        glossary_version: str | None,
        context_version: str | None,
    ) -> None:
        with self._lock:
            if self._db is None:
                return
            self._db.execute(
                """
                INSERT OR REPLACE INTO translations
                    (cache_key, source_text, translated_text, lang_in, lang_out,
                     translator, model, effort, prompt_version, glossary_version,
                     context_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cache_key,
                    source_text if self.store_plaintext else "",
                    translated_text,
                    lang_in,
                    lang_out,
                    translator,
                    model,
                    effort,
                    prompt_version,
                    glossary_version,
                    context_version,
                    time.time(),
                ),
            )
            self._db.commit()

    def stats(self) -> dict[str, Any]:
        with self._lock:
            if self._db is None:
                return {"enabled": False, "entries": 0}
            row = self._db.execute("SELECT COUNT(*) FROM translations").fetchone()
            return {
                "enabled": True,
                "entries": int(row[0]) if row else 0,
                "store_plaintext": self.store_plaintext,
                "ttl_seconds": self.ttl_seconds,
            }

    def clear(self) -> int:
        with self._lock:
            if self._db is None:
                return 0
            row = self._db.execute("SELECT COUNT(*) FROM translations").fetchone()
            count = int(row[0]) if row else 0
            self._db.execute("DELETE FROM translations")
            self._db.commit()
            return count

    def close(self) -> None:
        with self._lock:
            if self._db is not None:
                self._db.close()
                self._db = None
