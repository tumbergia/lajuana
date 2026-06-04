from langdetect import DetectorFactory, LangDetectException, detect

DetectorFactory.seed = 0

SUPPORTED_LANGUAGES: set[str] = {"es", "en", "fr", "pt", "de", "it", "nl"}


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "es"
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else "en"
    except LangDetectException:
        return "es"
