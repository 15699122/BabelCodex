from __future__ import annotations

from abc import ABC, abstractmethod


class TranslatorAdapter(ABC):
    @abstractmethod
    def translate(self, text: str) -> str:
        raise NotImplementedError

    def close(self) -> None:
        pass
