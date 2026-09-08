from .base import TranslatorAdapter


class MockTranslator(TranslatorAdapter):
    def translate(self, text: str) -> str:
        return f"[MOCK]{text}"
