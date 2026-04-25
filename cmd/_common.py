import re
import sys
from pathlib import Path


def to_snake(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


def parse_args():
    """Retourne (positional_args, force)."""
    args, force, _ = parse_all_args()
    return args, force


def parse_all_args():
    """Retourne (positional_args, force, plural|None)."""
    argv   = sys.argv[1:]
    force  = False
    plural = None
    result = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--force", "-f"):
            force = True
        elif argv[i] == "--plural" and i + 1 < len(argv):
            plural = argv[i + 1]
            i += 1
        else:
            result.append(argv[i])
        i += 1
    return result, force, plural


def validate_name(nom: str) -> str:
    """Valide et normalise le nom en PascalCase. Exit(1) si invalide."""
    if not re.match(r'^[A-Za-z][A-Za-z0-9]*$', nom):
        print("[ERREUR] Le nom doit être un identifiant CamelCase valide.")
        print("         - Commence par une lettre (A-Z ou a-z)")
        print("         - Suivi de lettres ou chiffres uniquement")
        print("         - Pas d'espaces, tirets, underscores ni caractères spéciaux")
        print("         Exemples valides : Produit, CommandeLigne, TVA")
        sys.exit(1)
    return nom[0].upper() + nom[1:]


def pluralize(snake: str) -> str:
    """commande_ligne → Commande lignes  |  produit → Produits"""
    words = snake.split("_")
    words[-1] += "s"
    return " ".join(words).capitalize()


def read_project_var(key: str, default: str, root: Path) -> str:
    """
    Lit une variable depuis env/example puis env/dev sans importer config.
    Évite la collision cmd/inspect/ vs stdlib inspect via le chaîne d'import config→logging.
    """
    for env_file in [root / "env" / "example", root / "env" / "dev"]:
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip()
    return default
