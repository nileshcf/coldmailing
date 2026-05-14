from __future__ import annotations

from collections import defaultdict


class SafeFormatDict(defaultdict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render_template(template: str, values: dict[str, str]) -> str:
    safe_values = SafeFormatDict(str)
    safe_values.update({key: value or "" for key, value in values.items()})
    rendered = template.format_map(safe_values)
    compacted_lines = []
    previous_blank = False

    for line in rendered.splitlines():
        stripped = line.rstrip()
        is_blank = not stripped
        if is_blank and previous_blank:
            continue
        compacted_lines.append(stripped)
        previous_blank = is_blank

    return "\n".join(compacted_lines).strip() + "\n"
