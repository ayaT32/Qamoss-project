"""
Arabic text normalization for matching purposes only.

IMPORTANT: Never overwrite or display the normalized text to the user.
Normalization is used ONLY to compare/search text — the original,
unmodified text is always what gets shown and cited.
"""
import re

# Arabic diacritics (tashkeel) + tatweel (kashida)
_TASHKEEL_RE = re.compile(r'[ؗ-ًؚ-ْٰـ]')
_ALEF_RE = re.compile(r'[إأآا]')
_YAA_RE = re.compile(r'[ىئ]')
_TAA_MARBUTA_RE = re.compile(r'ة')
_WHITESPACE_RE = re.compile(r'\s+')
_PUNCT_RE = re.compile(r'[\.\,\!\?\;\:\(\)\[\]\{\}"\'«»ـ]')


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for fuzzy matching / search.

    Removes diacritics, unifies letter variants, strips punctuation.
    Never use the output for display — only for comparison.
    """
    if not text:
        return ""
    s = text
    s = _TASHKEEL_RE.sub('', s)
    s = _ALEF_RE.sub('ا', s)
    s = _YAA_RE.sub('ي', s)
    s = _TAA_MARBUTA_RE.sub('ه', s)
    s = _PUNCT_RE.sub(' ', s)
    s = _WHITESPACE_RE.sub(' ', s).strip()
    return s


if __name__ == "__main__":
    tests = [
        "إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ",
        "انما الاعمال بالنيات",
        "إنَّما الأعمالُ بالنيّاتِ.",
    ]
    for t in tests:
        print(f"{t!r:55} -> {normalize_arabic(t)!r}")
