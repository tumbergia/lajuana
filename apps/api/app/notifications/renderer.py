from __future__ import annotations

import re


def render_template(template_body: str, variables: dict[str, str]) -> str:
    def _replace(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", _replace, template_body)


def render_subject(template_subject: str | None, variables: dict[str, str]) -> str | None:
    if template_subject is None:
        return None
    return render_template(template_subject, variables)
