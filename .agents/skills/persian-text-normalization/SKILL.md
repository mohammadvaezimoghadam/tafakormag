---
name: persian-text-normalization
description: >-
  Standardizes Persian text normalization and content hash generation across Tafakor backend.
  Use when processing note titles, post content, search indexing, or detecting duplicate messages.
---

# Persian Text Normalization & Deduplication Standard

Tafakor relies on a deterministic Persian text normalization routine to ensure consistent search indexing and duplicate post detection via cryptographic content hashing (`content_hash`).

## 1. Canonical Normalization Routine

Always import and use the canonical `normalize_persian_text` function:

```python
from backend.apps.notes.models import normalize_persian_text
```

### What it normalizes:
- Replaces Arabic letters with Persian equivalents:
  - `ي` -> `ی` (Arabic Yeh to Persian Yeh)
  - `ك` -> `ک` (Arabic Kaf to Persian Keheh)
  - `ة` -> `ه` or `ت` depending on context
- Normalizes Persian and Arabic digits: `۰-۹` / `٠-٩` -> `0-9`
- Strips redundant zero-width non-joiners (ZWNJ / نیم‌فاصله) and multiple consecutive whitespace characters.
- Normalizes quote marks, diacritics (اعراب), and punctuation.

## 2. Generating `content_hash` for Deduplication

When saving or checking for duplicate posts:

```python
import hashlib
from backend.apps.notes.models import normalize_persian_text

def compute_content_hash(raw_text: str) -> str:
    """
    Computes deterministic SHA-256 / MD5 hash of normalized Persian text.
    """
    normalized = normalize_persian_text(raw_text or "").strip()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
```

## 3. Strict Rules
- **NEVER** write custom character-replacing regexes inside serializers or views.
- Changing the normalization algorithm will invalidate existing `content_hash` values in the database and cause duplicate detection to fail.

