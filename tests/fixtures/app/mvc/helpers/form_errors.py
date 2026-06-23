import html


def render_errors_html(errors: list[str]) -> str:
    if not errors:
        return ""
    items = "".join(f"<li>{html.escape(e)}</li>" for e in errors)
    return (
        '<ul class="list-disc list-inside bg-red-100 border border-red-400 '
        f'text-red-800 px-4 py-3 rounded mb-4">{items}</ul>'
    )
