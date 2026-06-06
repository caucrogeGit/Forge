"""
core/errors/runtime_error_markdown.py — Rendu Markdown des erreurs runtime Forge.

Lit storage/logs/errors.dev.jsonl et génère storage/logs/errors.dev.md.

Règle :
    errors.dev.jsonl = source canonique
    errors.dev.md    = rendu lisible généré à partir du JSONL

Ne pas modifier errors.dev.md à la main.
Forge Design lira errors.dev.jsonl directement.
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime

_MD_FILENAME  = "errors.dev.md"
_HEADER_LINES = (
    "# Erreurs runtime Forge — dev",
    "",
    "Source canonique : `storage/logs/errors.dev.jsonl`  ",
    "Généré depuis le JSONL. Ne pas modifier ce fichier à la main.",
)


# ── Lecture du JSONL ───────────────────────────────────────────────────────────

def load_error_events_from_jsonl(path: pathlib.Path) -> list[dict]:
    """
    Charge les événements depuis un fichier JSONL.

    - Les lignes vides sont ignorées.
    - Les lignes JSON invalides sont retournées comme dicts spéciaux
      {"_invalid_line": <numéro>, "_raw": <texte>}.
    - Retourne une liste vide si le fichier est absent.
    """
    if not path.exists():
        return []
    events: list[dict] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            events.append(json.loads(stripped))
        except json.JSONDecodeError:
            events.append({"_invalid_line": i, "_raw": stripped})
    return events


# ── Rendu d'un événement ───────────────────────────────────────────────────────

def render_error_event_markdown(event: dict) -> str:
    """Rend un événement d'erreur en Markdown. Gère les lignes invalides."""
    if "_invalid_line" in event:
        num = event["_invalid_line"]
        raw = event.get("_raw", "")
        return f"## ⚠ Ligne JSONL invalide (ligne {num})\n\n```\n{raw}\n```\n"

    event_id = event.get("id", "inconnu")
    exc_type = event.get("exception_type", "Erreur inconnue")

    parts: list[str] = [f"## {event_id} — {exc_type}", ""]

    timestamp   = event.get("timestamp", "")
    environment = event.get("environment", "")
    level       = event.get("level", "")
    category    = event.get("category", "")
    safe        = event.get("safe_for_display", False)

    if timestamp:
        parts.append(f"**Date :** {timestamp}  ")
    if environment:
        parts.append(f"**Environnement :** {environment}  ")
    if level:
        parts.append(f"**Niveau :** {level}  ")
    if category:
        parts.append(f"**Catégorie :** {category}  ")
    parts.append(f"**Safe for display :** {'true' if safe else 'false'}  ")
    parts.append("")

    # Requête
    req = event.get("request")
    if req:
        parts.append("### Requête")
        parts.append("")
        if req.get("method"):
            parts.append(f"- Méthode : {req['method']}")
        if req.get("path"):
            parts.append(f"- Chemin : {req['path']}")
        parts.append(f"- Query : {req.get('query', '')}")
        post_keys = req.get("post_keys", [])
        if post_keys:
            parts.append(f"- Champs POST : {', '.join(str(k) for k in post_keys)}")
        parts.append("")

    # Localisation
    location = event.get("location")
    if location:
        parts.append("### Localisation")
        parts.append("")
        parts.append(f"- Fichier : {location.get('file', '')}")
        parts.append(f"- Ligne : {location.get('line', '')}")
        parts.append(f"- Fonction : {location.get('function', '')}")
        parts.append("")

    # Message
    message = event.get("message", "")
    if message:
        parts.append("### Message")
        parts.append("")
        parts.append(message)
        parts.append("")

    # Traceback
    frames = event.get("traceback", [])
    if frames:
        parts.append("### Traceback simplifié")
        parts.append("")
        for frame in frames:
            f_file = frame.get("file", "")
            f_line = frame.get("line", "")
            f_func = frame.get("function", "")
            parts.append(f"- {f_file}:{f_line} — {f_func}")
        parts.append("")

    # Hint
    hint = event.get("hint", "")
    if hint:
        parts.append("### Piste")
        parts.append("")
        parts.append(hint)
        parts.append("")

    return "\n".join(parts)


# ── Rendu de la liste complète ────────────────────────────────────────────────

def render_errors_markdown(events: list[dict]) -> str:
    """Génère le contenu Markdown complet depuis une liste d'événements."""
    now = datetime.now().isoformat(timespec="seconds")
    valid = [e for e in events if "_invalid_line" not in e]
    last_ts = max((e.get("timestamp", "") for e in valid), default="")

    header = list(_HEADER_LINES) + [
        "",
        f"Généré le : {now}",
        "",
        "---",
        "",
        "## Résumé",
        "",
        f"- Erreurs listées : {len(valid)}",
    ]
    if last_ts:
        header.append(f"- Dernière erreur : {last_ts}")
    header += ["", "---", ""]

    sections = ["\n".join(header)]
    for event in events:
        sections.append(render_error_event_markdown(event))
        sections.append("\n---\n")

    return "\n".join(sections)


# ── Écriture du Markdown ──────────────────────────────────────────────────────

def write_errors_markdown(jsonl_path: pathlib.Path, markdown_path: pathlib.Path) -> None:
    """
    Lit le JSONL et écrit le fichier Markdown.

    Silencieux si le JSONL est absent ou vide (aucun fichier créé).
    Ne modifie jamais le fichier JSONL.
    """
    events = load_error_events_from_jsonl(jsonl_path)
    if not events:
        return
    content = render_errors_markdown(events)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(content, encoding="utf-8")
