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

Présentation (DX-DEBUG-DUMP-RENDER-002) :

- les dictionnaires sont rendus en **grille à deux colonnes** (clés
  alignées verticalement, valeurs à droite) ;
- les conteneurs imbriqués non vides (dict, liste d'objets) sont des
  **sections repliables** (``<details>`` natif, aucun JavaScript) avec un
  badge de comptage (``{n}`` pour un dict, ``[n]`` pour une séquence) ;
- les séquences de scalaires sont rendues en ligne (``[ a, b ]``).

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

_SCALAR_TYPES = (str, int, float, bool)


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


# ── Briques de rendu élémentaires ────────────────────────────────────────────


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, _SCALAR_TYPES)


def _scalar_only(items: Any) -> bool:
    return all(_is_scalar(item) for item in items)


def _render_scalar(value: Any) -> str:
    if value is None:
        return '<span class="forge-debug-none">None</span>'
    if isinstance(value, bool):
        return f'<span class="forge-debug-bool">{"True" if value else "False"}</span>'
    if isinstance(value, (int, float)):
        return f'<span class="forge-debug-num">{_escape(str(value))}</span>'
    return f'<span class="forge-debug-str">{_escape(value)}</span>'


def _render_obj(value: Any) -> str:
    type_name = _escape(type(value).__name__)
    repr_text = _escape(repr(value))
    return (
        '<span class="forge-debug-obj">'
        f'<span class="forge-debug-typename">{type_name}</span>: {repr_text}'
        '</span>'
    )


def _meta(text: str) -> str:
    return f'<span class="forge-debug-meta">{_escape(text)}</span>'


def _badge(value: Any) -> str:
    n = len(value)
    inner = f'{{{n}}}' if isinstance(value, dict) else f'[{n}]'
    return f'<span class="forge-debug-badge">{inner}</span>'


def _seq_inline(items: Any) -> str:
    inner = ", ".join(_render_scalar(item) for item in items)
    return f'<span class="forge-debug-seqinline">[ {inner} ]</span>'


def _row(label_html: str, value_html: str) -> str:
    """Une entrée scalaire : deux cellules de grille (clé puis valeur)."""
    return (
        f'<div class="forge-debug-key">{label_html}</div>'
        f'<div class="forge-debug-value">{value_html}</div>'
    )


# ── Rendu récursif ───────────────────────────────────────────────────────────


def _render_leaf(value: Any, depth: int, seen: frozenset[int]) -> str:
    """Rendu d'une valeur non-conteneur (scalaire, ou objet via ``.data``/repr)."""
    if _is_scalar(value):
        return _render_scalar(value)
    data_attr = getattr(value, "data", None)
    if isinstance(data_attr, (dict, list, tuple, set)):
        return _render_node(data_attr, depth + 1, seen)
    return _render_obj(value)


def _details(label_html: str, value: Any, depth: int, seen: frozenset[int]) -> str:
    """Section repliable pour un conteneur imbriqué non vide."""
    body = _render_node(value, depth + 1, seen)
    return (
        '<details class="forge-debug-block" open>'
        '<summary class="forge-debug-summary">'
        f'<span class="forge-debug-key">{label_html}</span> {_badge(value)}'
        '</summary>'
        f'<div class="forge-debug-blockbody">{body}</div>'
        '</details>'
    )


def _render_entry(
    label_html: str, value: Any, depth: int, seen: frozenset[int], *, sensitive: bool = False
) -> str:
    """Rendu d'une entrée (clé de dict ou index de séquence).

    Décide entre une ligne alignée (scalaire, conteneur vide, séquence de
    scalaires) et une section repliable (dict ou séquence d'objets).
    """
    if sensitive:
        return _row(label_html, f'<span class="forge-debug-str">{_escape(MASKED_VALUE)}</span>')

    if isinstance(value, (dict, list, tuple, set)):
        if id(value) in seen:
            return _row(label_html, _meta(CYCLE_MARKER))
        if depth + 1 > MAX_DEPTH:
            return _row(label_html, _meta(MAX_DEPTH_MARKER))
        if len(value) == 0:
            return _row(label_html, _meta("{}" if isinstance(value, dict) else "[]"))
        if isinstance(value, dict) or not _scalar_only(value):
            return _details(label_html, value, depth, seen)
        return _row(label_html, _seq_inline(value))

    return _row(label_html, _render_leaf(value, depth, seen))


def _render_dict(d: dict, depth: int, seen: frozenset[int]) -> str:
    if not d:
        return _meta("{}")
    rows = ['<div class="forge-debug-dict">']
    for key, value in d.items():
        rows.append(
            _render_entry(
                _escape(str(key)), value, depth, seen, sensitive=_is_sensitive_key(key)
            )
        )
    rows.append("</div>")
    return "".join(rows)


def _render_sequence(seq: Any, depth: int, seen: frozenset[int]) -> str:
    items = list(seq)
    if not items:
        return _meta("[]")
    if _scalar_only(items):
        return _seq_inline(items)
    rows = ['<div class="forge-debug-seq">']
    for index, item in enumerate(items):
        rows.append(_render_entry(f"#{index}", item, depth, seen))
    rows.append("</div>")
    return "".join(rows)


def _render_node(value: Any, depth: int, seen: frozenset[int]) -> str:
    """Rendu autonome d'une valeur : grille pour un dict, liste pour une
    séquence, span pour un scalaire ou un objet."""
    if depth > MAX_DEPTH:
        return _meta(MAX_DEPTH_MARKER)
    if _is_scalar(value):
        return _render_scalar(value)
    if isinstance(value, (dict, list, tuple, set)):
        obj_id = id(value)
        if obj_id in seen:
            return _meta(CYCLE_MARKER)
        seen = seen | {obj_id}
        if isinstance(value, dict):
            return _render_dict(value, depth, seen)
        return _render_sequence(value, depth, seen)
    data_attr = getattr(value, "data", None)
    if isinstance(data_attr, (dict, list, tuple, set)):
        return _render_node(data_attr, depth + 1, seen)
    return _render_obj(value)


_CSS = (
    "*{box-sizing:border-box;}"
    "body{background:#f1f5f9;color:#0f172a;margin:0;padding:2rem;"
    "font-family:-apple-system,system-ui,Segoe UI,Roboto,sans-serif;}"
    ".forge-debug-card{max-width:980px;margin:0 auto;background:#ffffff;"
    "border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;"
    "box-shadow:0 1px 3px rgba(15,23,42,0.08);}"
    ".forge-debug-head{display:flex;align-items:baseline;gap:0.75rem;"
    "padding:0.85rem 1.5rem;background:#1e293b;}"
    ".forge-debug-title{font-size:1.05rem;font-weight:650;margin:0;color:#ffffff;}"
    ".forge-debug-type{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
    "font-size:0.8rem;color:#94a3b8;}"
    ".forge-debug-body{padding:1rem 1.5rem;"
    "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
    "font-size:0.85rem;line-height:1.6;}"
    ".forge-debug-dict,.forge-debug-seq{display:grid;"
    "grid-template-columns:max-content minmax(0,1fr);gap:0.1rem 0.9rem;align-items:start;}"
    ".forge-debug-dict>.forge-debug-block,.forge-debug-seq>.forge-debug-block"
    "{grid-column:1 / -1;}"
    ".forge-debug-key{color:#b45309;font-weight:600;white-space:nowrap;}"
    ".forge-debug-value{overflow-wrap:anywhere;min-width:0;}"
    ".forge-debug-block{margin:0.1rem 0;}"
    ".forge-debug-summary{cursor:pointer;list-style:none;display:flex;"
    "align-items:center;gap:0.45rem;padding:0.1rem 0;}"
    ".forge-debug-summary::-webkit-details-marker{display:none;}"
    ".forge-debug-summary::before{content:'▸';color:#94a3b8;font-size:0.7rem;}"
    "details[open]>.forge-debug-summary::before{content:'▾';}"
    ".forge-debug-blockbody{margin:0.15rem 0 0.35rem 0.35rem;padding-left:1rem;"
    "border-left:2px solid #e2e8f0;}"
    ".forge-debug-badge{color:#64748b;font-size:0.78rem;}"
    ".forge-debug-str{color:#047857;}"
    ".forge-debug-num{color:#2563eb;}"
    ".forge-debug-bool{color:#7c3aed;font-weight:600;}"
    ".forge-debug-none{color:#94a3b8;font-style:italic;}"
    ".forge-debug-obj{color:#6d28d9;}"
    ".forge-debug-typename{font-weight:600;}"
    ".forge-debug-meta{color:#94a3b8;font-style:italic;}"
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
    body = _render_node(normalized, depth=0, seen=frozenset())
    return (
        "<!doctype html>\n"
        '<html lang="fr"><head><meta charset="utf-8">'
        "<title>Debug Forge</title>"
        f"<style>{_CSS}</style>"
        "</head><body>"
        '<div class="forge-debug-card">'
        '<div class="forge-debug-head">'
        '<h1 class="forge-debug-title">Debug Forge</h1>'
        f'<span class="forge-debug-type">{type_name}</span>'
        "</div>"
        f'<div class="forge-debug-body">{body}</div>'
        "</div></body></html>"
    )
