"""Renderer HTML pour `Response.debug(obj)` — DX-DEBUG-DUMP-HTML-001.

Ticket : DX-DEBUG-DUMP-HTML-001.

Objectif : produire une page HTML lisible et sûre quand un contrôleur
appelle ``Response.debug(obj)`` en ``APP_ENV=dev``. Le rendu est
volontairement simple, pédagogique, indépendant d'assets statiques.

Priorités de normalisation :

1. Si l'objet possède une propriété ``.data`` exploitable
   (``dict``/``list``/``tuple``/``set``) → utiliser ``obj.data``.
2. Sinon si l'objet est un conteneur natif → rendu récursif.
3. Sinon → afficher ``type(obj).__name__`` suivi de ``repr(obj)``.

Sécurité :

- les valeurs ``str`` (clés et valeurs) sont échappées via ``html.escape`` ;
- les noms sensibles (Authorization, Cookie, password, csrf, token, …)
  sont remplacés par ``[masked]`` — mêmes règles que ``request.data`` ;
- la profondeur est bornée par ``MAX_DEPTH`` ;
- les références circulaires sont détectées (``<cycle detected>``).

Le renderer ne dépend pas du registre ``core.forge`` : la décision
``dev`` vs ``prod`` reste portée par ``Response.debug``.
"""

from __future__ import annotations

import html as _html
from typing import Any

from core.http.request import (
    MASKED_VALUE,
    SENSITIVE_FIELD_FRAGMENTS,
    SENSITIVE_HEADER_NAMES,
)


MAX_DEPTH = 5

MAX_DEPTH_MARKER = "<max depth reached>"
CYCLE_MARKER = "<cycle detected>"


def _is_sensitive_key(key: object) -> bool:
    """True si ``key`` ressemble à un nom sensible (header, champ).

    Couvre les mêmes règles que ``Request.data`` :
    - égalité exacte (insensible à la casse) avec ``SENSITIVE_HEADER_NAMES``
      (``authorization``, ``cookie``, ``set-cookie``, …) ;
    - sous-chaîne (insensible à la casse) avec ``SENSITIVE_FIELD_FRAGMENTS``
      (``password``, ``passwd``, ``secret``, ``token``, ``csrf``,
      ``api_key``, ``apikey``).
    """
    name = str(key).lower()
    if name in SENSITIVE_HEADER_NAMES:
        return True
    return any(fragment in name for fragment in SENSITIVE_FIELD_FRAGMENTS)


def _escape(text: str) -> str:
    return _html.escape(text, quote=True)


def _container_view(obj: Any) -> Any:
    """Retourne ``obj.data`` si exploitable, sinon ``obj`` tel quel.

    Une propriété ``.data`` n'est utilisée que si elle pointe sur un
    conteneur (``dict``/``list``/``tuple``/``set``) — un attribut
    homonyme arbitraire (``str`` ``bytes`` …) ne déclenche pas le
    déballage.
    """
    data_attr = getattr(obj, "data", None)
    if isinstance(data_attr, (dict, list, tuple, set)):
        return data_attr
    return obj


def _render_value(value: Any, depth: int, seen: frozenset[int]) -> str:
    if depth > MAX_DEPTH:
        return f'<span class="forge-debug-meta">{_escape(MAX_DEPTH_MARKER)}</span>'

    if value is None:
        return '<span class="forge-debug-none">None</span>'
    if isinstance(value, bool):
        label = "True" if value else "False"
        return f'<span class="forge-debug-bool">{label}</span>'
    if isinstance(value, (int, float)):
        return f'<span class="forge-debug-num">{_escape(str(value))}</span>'
    if isinstance(value, str):
        return f'<span class="forge-debug-str">{_escape(value)}</span>'

    if isinstance(value, (dict, list, tuple, set)):
        obj_id = id(value)
        if obj_id in seen:
            return f'<span class="forge-debug-meta">{_escape(CYCLE_MARKER)}</span>'
        seen = seen | {obj_id}

    if isinstance(value, dict):
        return _render_dict(value, depth, seen)
    if isinstance(value, (list, tuple, set)):
        return _render_sequence(value, depth, seen)

    data_attr = getattr(value, "data", None)
    if isinstance(data_attr, (dict, list, tuple, set)):
        return _render_value(data_attr, depth + 1, seen)

    type_name = _escape(type(value).__name__)
    repr_text = _escape(repr(value))
    return (
        f'<span class="forge-debug-obj">'
        f'<span class="forge-debug-typename">{type_name}</span>: {repr_text}'
        f'</span>'
    )


def _render_dict(d: dict, depth: int, seen: frozenset[int]) -> str:
    if not d:
        return '<span class="forge-debug-meta">{}</span>'
    rows: list[str] = ['<div class="forge-debug-dict">']
    for key, value in d.items():
        key_str = _escape(str(key))
        if _is_sensitive_key(key):
            rendered = f'<span class="forge-debug-str">{_escape(MASKED_VALUE)}</span>'
        else:
            rendered = _render_value(value, depth + 1, seen)
        rows.append(
            '<div class="forge-debug-entry">'
            f'<span class="forge-debug-key">{key_str}</span>'
            '<span class="forge-debug-sep">:</span> '
            f'<span class="forge-debug-value">{rendered}</span>'
            '</div>'
        )
    rows.append('</div>')
    return "".join(rows)


def _render_sequence(seq: Any, depth: int, seen: frozenset[int]) -> str:
    items = list(seq)
    container_name = type(seq).__name__
    if not items:
        return (
            f'<span class="forge-debug-meta">empty {_escape(container_name)}</span>'
        )
    rows: list[str] = [f'<div class="forge-debug-seq" data-kind="{_escape(container_name)}">']
    for item in items:
        rendered = _render_value(item, depth + 1, seen)
        rows.append(
            '<div class="forge-debug-entry">'
            '<span class="forge-debug-bullet">-</span> '
            f'<span class="forge-debug-value">{rendered}</span>'
            '</div>'
        )
    rows.append('</div>')
    return "".join(rows)


_CSS = (
    "body{background:#f8fafc;color:#1f2937;margin:0;padding:2rem;"
    "font-family:-apple-system,system-ui,Segoe UI,Roboto,sans-serif;}"
    ".forge-debug-card{max-width:960px;margin:0 auto;background:#ffffff;"
    "border:1px solid #e5e7eb;border-radius:8px;padding:1.5rem;}"
    ".forge-debug-title{font-size:1.25rem;font-weight:600;margin:0 0 0.25rem 0;}"
    ".forge-debug-type{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
    "font-size:0.875rem;color:#6b7280;margin-bottom:1rem;}"
    ".forge-debug-body{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
    "font-size:0.875rem;line-height:1.5;white-space:normal;}"
    ".forge-debug-dict,.forge-debug-seq{padding-left:1.25rem;"
    "border-left:2px solid #e5e7eb;margin-top:0.25rem;}"
    ".forge-debug-entry{padding:0.125rem 0;}"
    ".forge-debug-key{color:#b45309;font-weight:600;}"
    ".forge-debug-bullet{color:#6b7280;}"
    ".forge-debug-sep{color:#9ca3af;}"
    ".forge-debug-str{color:#047857;}"
    ".forge-debug-num{color:#2563eb;}"
    ".forge-debug-bool{color:#b91c1c;font-weight:600;}"
    ".forge-debug-none{color:#6b7280;font-style:italic;}"
    ".forge-debug-obj{color:#6d28d9;}"
    ".forge-debug-typename{font-weight:600;}"
    ".forge-debug-meta{color:#9ca3af;font-style:italic;}"
)


def render_debug_html(obj: Any) -> str:
    """Rendu HTML lisible et sûr de ``obj`` pour le mode développement.

    - Échappe systématiquement les chaînes (``html.escape``).
    - Masque les clés sensibles (Authorization, password, csrf, token, …).
    - Borne la récursion à ``MAX_DEPTH``.
    - Détecte les références circulaires (``<cycle detected>``).
    """
    type_name = _escape(type(obj).__name__)
    normalized = _container_view(obj)
    body = _render_value(normalized, depth=0, seen=frozenset())
    return (
        "<!doctype html>\n"
        '<html lang="fr"><head><meta charset="utf-8">'
        "<title>Debug Forge</title>"
        f"<style>{_CSS}</style>"
        "</head><body>"
        '<div class="forge-debug-card">'
        '<h1 class="forge-debug-title">Debug Forge</h1>'
        f'<div class="forge-debug-type">{type_name}</div>'
        f'<div class="forge-debug-body">{body}</div>'
        "</div></body></html>"
    )
