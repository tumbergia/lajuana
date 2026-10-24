from __future__ import annotations

import re
import unicodedata

from beanie import Document


def slugify(name: str, *, fallback: str = "item") -> str:
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or fallback


async def unique_slug(document_class: type[Document], base_slug: str) -> str:
    slug = base_slug
    suffix = 2
    while await document_class.find_one({"slug": slug}):
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug
