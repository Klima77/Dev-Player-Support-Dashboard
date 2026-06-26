"""
Moduł tłumaczenia – obsługuje automatyczne tłumaczenie tekstów na język polski.
"""
from deep_translator import GoogleTranslator

MAX_CHARS = 4000  # Limit darmowego API Google Translate


def translate_to_pl(text: str) -> str:
    """Tłumaczy tekst na język polski. Obcina do 4000 znaków."""
    if not text or text.strip() == "":
        return ""
    try:
        return GoogleTranslator(source='auto', target='pl').translate(text[:MAX_CHARS])
    except Exception:
        return f"[Błąd tłumaczenia] {text[:200]}..."
