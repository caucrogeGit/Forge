#!/usr/bin/env python3
"""Import contrôlé de la documentation Forge vers docs/forge/.

Source par défaut : /home/roger/Projets/Forge/docs/
Destination par défaut : docs/forge/ (relatif au dépôt Forge-official-site)

Règles :
  - liste blanche stricte ;
  - extensions autorisées seulement ;
  - refus catégorique de tout fichier dont le nom matche un motif sensible
    (cert.pem, key.pem, *.env, *.key, *.pem, *.crt) ;
  - aucune écriture en dehors de la destination ;
  - aucune lecture en écriture sur la source.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# ADR-045 : official-site/ vit DANS le dépôt Forge. La source de l'import est
# donc la doc canonique locale (../../docs depuis ce script), et non plus un
# dépôt séparé. L'import devient une copie locale, exécutée au build.
DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "docs"
DEFAULT_DEST = Path(__file__).resolve().parent.parent / "docs" / "forge"
FORGEWEB_ROOT = Path(__file__).resolve().parent.parent

# Liste blanche : sous-dossiers de Forge/docs/ autorisés à l'import.
# entities/ et security/ contiennent de la documentation publique référencée
# par les fichiers racine ; les exclure casserait les liens internes.
WHITELISTED_SUBDIRS: tuple[str, ...] = (
    "adr",
    "install",
    "reference",
    "starters",
    "contributing",
    "project",
    "roadmap",
    "history",
    "testing",
    "entities",
    "security",
    "static",
    # Forge IoT (opt-in `forge-mvc-iot`) et structure des opt-ins —
    # publiés à partir de 1.0.0-beta.12.
    "iot",
    "architecture",
    # Réorganisation de la documentation en 1.0.0-beta.13
    # (docs/guide/, features/, philosophy/, release/, deployment/) plus
    # l'opt-in `forge-mvc-video` (docs/video/).
    "deployment",
    "features",
    "guide",
    "philosophy",
    "release",
    "video",
    # Starter pédagogique temporaire « welcome-reseau » (2TNE CIEL), publié à
    # partir de 1.0.0-beta.16 et lié depuis la landing (entrée « 2TNE »).
    # Anciennement docs/vacances/welcome-vacance ; déplacé sous
    # docs/starters-pedagogique/welcome-reseau au 1.0.0-beta.17 (dossier durable
    # du 1er starter pédagogique). Sans lien avec Forge ; à retirer (whitelist +
    # nav + entrée landing) le 2026-06-28 en parité avec le bloc TEMP du canonique.
    "starters-pedagogique",
)

# Extensions de fichiers autorisées.
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".webp",
    ".gif",
    ".ico",
    # Sketch Arduino d'exemple référencé par docs/iot/esp32-example.md
    # (asset de documentation téléchargeable, non sensible).
    ".ino",
    # Supports téléchargeables du starter welcome-reseau (QCM, activités,
    # corrigés) référencés en lien relatif depuis
    # docs/starters-pedagogique/welcome-reseau/palier-*/.
    ".pdf",
})

# Motifs de noms de fichiers explicitement refusés (ceinture de sécurité).
FORBIDDEN_NAME_SUFFIXES: tuple[str, ...] = (
    ".env",
    ".key",
    ".pem",
    ".crt",
    ".pyc",
)
FORBIDDEN_NAME_PREFIXES: tuple[str, ...] = (
    ".env",
)
FORBIDDEN_EXACT_NAMES: frozenset[str] = frozenset({
    "cert.pem",
    "key.pem",
    ".envrc",
})

# Dossiers à ignorer même s'ils apparaissent par erreur dans la source.
FORBIDDEN_DIR_NAMES: frozenset[str] = frozenset({
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".cache",
    "site",
    "core",
    "mvc",
    "packages",
    "tests",
    "env",
    "secrets",
})


def is_forbidden_file(name: str) -> bool:
    if name in FORBIDDEN_EXACT_NAMES:
        return True
    if any(name.endswith(s) for s in FORBIDDEN_NAME_SUFFIXES):
        return True
    if any(name.startswith(p) and name != "index.md" for p in FORBIDDEN_NAME_PREFIXES):
        return True
    return False


def assert_dest_within_forgeweb(dest: Path) -> None:
    try:
        dest.resolve().relative_to(FORGEWEB_ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(
            f"refus: la destination {dest} n'est pas dans {FORGEWEB_ROOT}"
        ) from exc


def clear_destination(dest: Path) -> int:
    """Vide entièrement le contenu de dest, en préservant dest elle-même."""
    if not dest.exists():
        dest.mkdir(parents=True, exist_ok=True)
        return 0
    removed = 0
    for entry in dest.iterdir():
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()
        removed += 1
    return removed


def copy_root_markdown(source: Path, dest: Path) -> list[Path]:
    """Copie les *.md à la racine de la source vers dest."""
    copied: list[Path] = []
    for entry in sorted(source.iterdir()):
        if not entry.is_file():
            continue
        if entry.suffix != ".md":
            continue
        if is_forbidden_file(entry.name):
            continue
        target = dest / entry.name
        shutil.copy2(entry, target)
        copied.append(target.relative_to(dest))
    return copied


def copy_whitelisted_tree(
    source_subdir: Path, dest_subdir: Path
) -> tuple[list[Path], list[Path]]:
    """Copie récursive d'un sous-arbre avec filtrage extensions + interdits."""
    copied: list[Path] = []
    skipped: list[Path] = []
    if not source_subdir.exists():
        return copied, skipped
    for src in source_subdir.rglob("*"):
        rel = src.relative_to(source_subdir)
        # Filtrage par segments de chemin.
        if any(part in FORBIDDEN_DIR_NAMES for part in rel.parts):
            skipped.append(rel)
            continue
        if src.is_dir():
            continue
        if is_forbidden_file(src.name):
            skipped.append(rel)
            continue
        if src.suffix.lower() not in ALLOWED_EXTENSIONS:
            skipped.append(rel)
            continue
        target = dest_subdir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied.append(rel)
    return copied, skipped


# Substitutions statiques des macros normalement injectées par le hook
# ``tools/mkdocs_version_hook.py`` de Forge core. Le hook n'est pas porté
# dans Forge-official-site ; on remplace donc ces placeholders à l'import.
# Source de vérité : pyproject.toml de Forge core (1.0.0b17 au 2026-06-18).
FORGE_MACROS: dict[str, str] = {
    "{{forge_version}}": "1.0.0b17",
    "{{ forge_version }}": "1.0.0b17",
    "{{forge_tag}}": "v1.0.0-beta.17",
    "{{ forge_tag }}": "v1.0.0-beta.17",
    "{{python_min}}": "3.12",
    "{{ python_min }}": "3.12",
}


def sanitize_imported_markdown(dest: Path) -> int:
    """Rewrite imported .md to fix links that Forge core resolved against
    its own ``index.html`` landing and to substitute Forge core macros
    that were normally injected at build time by a hook we don't ship.

    Returns the number of files modified.
    """
    import re

    import posixpath

    # Rewrites only the URL part of Markdown links and HTML hrefs that
    # *end with* ``index.html`` (preserving any relative prefix).
    md_link_re = re.compile(r"(\]\()([^)\s]*?)(index\.html)([)#?])")
    html_href_re = re.compile(r"((?:href|src)=[\"'])([^\"']*?)(index\.html)([\"'#?])")

    # MkDocs ne réécrit pas certains liens Markdown relatifs vers d'autres
    # pages/assets — notamment dans les grandes cellules de tableau du roadmap
    # et de l'historique (liens dont le texte est du code inline, ou liens
    # internes que le treeprocessor de chemins relatifs laisse « tels quels »).
    # La cible `.md`/asset reste alors brute dans le HTML et, à cause des URLs
    # en répertoire, pointe un niveau trop bas → lien cassé signalé par
    # check_local_links. On pré-résout donc, à l'import, *tout* lien relatif
    # interne en URL absolue `/docs/forge/…` — uniquement si la cible existe
    # réellement (garde-fou : on ne touche jamais un lien qui ne résout pas, et
    # MkDocs laisse intacte une URL absolue qui ne finit pas par `.md`).
    md_rel_link_re = re.compile(
        r"(!?\]\()"                 # 1: ]( ou ![…](
        r"([^)\s#]+)"              # 2: cible (chemin)
        r"(#[^)\s]*)?"             # 3: ancre éventuelle
        r"(\))"                     # 4: )
    )
    rewritable_suffixes = tuple(ALLOWED_EXTENSIONS)

    def absolute_doc_url(source_rel_dir: str, target: str) -> str | None:
        """Convertit une cible relative interne en URL absolue `/docs/forge/…`.

        Retourne ``None`` (lien laissé intact) si la cible est externe/absolue,
        n'a pas une extension connue, s'échappe de ``forge/``, ou n'existe pas
        sur le disque sous la destination importée.
        """
        if target.startswith(("/", "http://", "https://", "mailto:", "tel:")):
            return None
        if not target.lower().endswith(rewritable_suffixes):
            return None
        resolved = posixpath.normpath(posixpath.join(source_rel_dir, target))
        if not resolved.startswith("forge/") and resolved != "forge":
            return None
        # Vérifie l'existence réelle (dest == docs/forge).
        fs_target = dest / resolved[len("forge/") :]
        if not fs_target.exists():
            return None
        if resolved.endswith("/index.md"):
            return "/docs/" + resolved[: -len("index.md")]
        if resolved == "forge/index.md":
            return "/docs/forge/"
        if resolved.endswith(".md"):
            return "/docs/" + resolved[: -len(".md")] + "/"
        # Asset (image, .ino, …) : URL directe vers le fichier, extension gardée.
        return "/docs/" + resolved

    changed = 0
    for md in dest.rglob("*.md"):
        original = md.read_text(encoding="utf-8")
        rewritten = md_link_re.sub(
            lambda m: f"{m.group(1)}{m.group(2)}index.md{m.group(4)}", original
        )
        rewritten = html_href_re.sub(
            lambda m: f"{m.group(1)}{m.group(2)}index.md{m.group(4)}", rewritten
        )

        rel = md.relative_to(dest)
        rel_dir = rel.parent.as_posix()
        source_rel_dir = "forge" if rel_dir == "." else f"forge/{rel_dir}"

        def _rewrite_link(m: "re.Match[str]") -> str:
            url = absolute_doc_url(source_rel_dir, m.group(2))
            if url is None:
                return m.group(0)
            anchor = m.group(3) or ""
            return f"{m.group(1)}{url}{anchor}{m.group(4)}"

        rewritten = md_rel_link_re.sub(_rewrite_link, rewritten)

        # Substitution des macros Forge core (version, tag, python_min).
        for placeholder, value in FORGE_MACROS.items():
            rewritten = rewritten.replace(placeholder, value)
        if rewritten != original:
            md.write_text(rewritten, encoding="utf-8")
            changed += 1
    return changed


# Réécritures ciblées après import : (chemin relatif, motif, remplacement).
# Chaque entrée corrige un lien connu cassé dans la source Forge core mais
# fonctionnel à l'origine (dossier servi par auto-index ou nav MkDocs).
KNOWN_FIXUPS: tuple[tuple[str, str, str], ...] = (
    (
        "reference.md",
        "et les [ADR suivants](adr/)",
        "et les ADR suivants",
    ),
    (
        "install/core-dev.md",
        "| Décisions architecturales | [ADR](../adr/) |",
        "| Décisions architecturales | ADR dans la navigation Philosophie |",
    ),
    (
        "starters/01-contact-simple/index.md",
        "../index.md#progression-recommandee",
        "../#progression-recommandee",
    ),
)


def apply_known_fixups(dest: Path) -> int:
    """Applique les réécritures ciblées sur les fichiers importés."""
    changed = 0
    for rel, src, repl in KNOWN_FIXUPS:
        f = dest / rel
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8")
        if src in text:
            f.write_text(text.replace(src, repl), encoding="utf-8")
            changed += 1
    return changed


def regenerate_index(dest: Path) -> None:
    """Régénère docs/forge/index.md après l'import."""
    content = (
        "# Documentation Forge\n"
        "\n"
        "Cette section publie la documentation du framework Forge.\n"
        "\n"
        "Source canonique locale (lecture seule) :\n"
        "\n"
        "```text\n"
        "/home/roger/Projets/Forge/docs/\n"
        "```\n"
        "\n"
        "Import effectué par `scripts/import_forge_docs.py` selon une liste\n"
        "blanche stricte (FW-DOCS-IMPORT-001).\n"
    )
    (dest / "index.md").write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import contrôlé de la doc Forge vers docs/forge/."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Source par défaut : {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=DEFAULT_DEST,
        help=f"Destination par défaut : {DEFAULT_DEST}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="N'écrit rien, liste seulement.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source: Path = args.source
    dest: Path = args.dest

    if not source.is_dir():
        print(f"erreur: source introuvable: {source}", file=sys.stderr)
        return 2

    assert_dest_within_forgeweb(dest)

    print(f"Source      : {source}")
    print(f"Destination : {dest}")
    print(f"Mode        : {'dry-run' if args.dry_run else 'write'}")
    print()

    if args.dry_run:
        print("(dry-run, aucune écriture)")
        return 0

    removed = clear_destination(dest)
    print(f"Destination vidée ({removed} entrées supprimées).")

    # 1) *.md racine
    md_copied = copy_root_markdown(source, dest)
    print(f"Markdown racine importés : {len(md_copied)}")

    # 2) Sous-dossiers whitelistés
    total_subdir_copied = 0
    total_skipped = 0
    subdir_report: list[tuple[str, int, int, bool]] = []
    for name in WHITELISTED_SUBDIRS:
        src_sub = source / name
        dst_sub = dest / name
        if not src_sub.exists():
            subdir_report.append((name, 0, 0, False))
            continue
        copied, skipped = copy_whitelisted_tree(src_sub, dst_sub)
        total_subdir_copied += len(copied)
        total_skipped += len(skipped)
        subdir_report.append((name, len(copied), len(skipped), True))

    print("Sous-dossiers :")
    for name, n_copied, n_skipped, present in subdir_report:
        status = "OK" if present else "ABSENT"
        print(f"  - {name:14s} {status:6s} copiés={n_copied:4d} ignorés={n_skipped:4d}")

    # 3) Sanitisation des liens index.html (Forge core → Forge-official-site).
    sanitized = sanitize_imported_markdown(dest)
    print(f"Sanitisation index.html → index.md : {sanitized} fichiers réécrits.")

    # 4) Réécritures ciblées de liens connus cassés (cf. KNOWN_FIXUPS).
    fixed = apply_known_fixups(dest)
    print(f"Fixups ciblés appliqués : {fixed}.")

    # 5) index.md du dossier importé
    regenerate_index(dest)
    print("docs/forge/index.md régénéré.")

    # 6) Garde-fou final : aucun fichier interdit n'a fui
    leaks: list[Path] = []
    for f in dest.rglob("*"):
        if not f.is_file():
            continue
        if is_forbidden_file(f.name):
            leaks.append(f.relative_to(dest))
            continue
        if any(part in FORBIDDEN_DIR_NAMES for part in f.relative_to(dest).parts):
            leaks.append(f.relative_to(dest))
    if leaks:
        print()
        print("ERREUR: fuite détectée :", file=sys.stderr)
        for f in leaks:
            print(f"  {f}", file=sys.stderr)
        return 3

    print()
    print(
        f"Total : {len(md_copied)} .md racine + {total_subdir_copied} dans "
        f"sous-dossiers ({total_skipped} ignorés, 0 fuite)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
