#!/usr/bin/env python3
"""
Génère un script Python de fixtures (données de test) pour une entité.

Usage :
    python cmd/make.py table:fixtures <NomEntite> [--force]

Exemple :
    python cmd/make.py table:fixtures Produit
    → sql/fixtures/produit_fixtures.py

Le fichier généré utilise Faker + factory_boy pour produire des données
réalistes et peut être exécuté directement :

    python sql/fixtures/produit_fixtures.py --count 20
    python sql/fixtures/produit_fixtures.py --count 20 --env prod

Dépendances (à installer une seule fois) :
    pip install faker factory-boy
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import parse_args, validate_name, to_snake

ROOT         = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = ROOT / "sql" / "fixtures"

TEMPLATE = '''\
#!/usr/bin/env python3
"""
Fixtures : données de test pour la table {snake}.

Usage :
    python sql/fixtures/{snake}_fixtures.py [--count N] [--env dev|prod]

Dépendances :
    pip install faker factory-boy
"""

import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.database import obtenir_connexion


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

import factory
from faker import Faker

_fake = Faker("fr_FR")


class {Nom}Factory(factory.Factory):
    class Meta:
        model = dict

    {Nom}Id = factory.LazyFunction(lambda: _fake.bothify("???-####").upper())
    # TODO : déclarez ici les champs de la table avec des générateurs Faker
    # Exemples :
    # Nom        = factory.Faker("company",    locale="fr_FR")
    # Email      = factory.Faker("email",      locale="fr_FR")
    # Telephone  = factory.Faker("phone_number", locale="fr_FR")
    # Prix       = factory.LazyFunction(lambda: round(_fake.pyfloat(min_value=1, max_value=999, right_digits=2), 2))
    # Actif      = factory.LazyFunction(lambda: 1)


# ---------------------------------------------------------------------------
# Insertion
# ---------------------------------------------------------------------------

# TODO : listez ici les colonnes réelles de la table (dans l\'ordre)
COLONNES = [
    "{Nom}Id",
    # "Nom",
    # "Email",
]

INSERT_SQL = (
    f"INSERT INTO {snake} ({{cols}}) VALUES ({{placeholders}})"
    .format(
        cols         = ", ".join(COLONNES),
        placeholders = ", ".join(["%s"] * len(COLONNES)),
    )
)


def build_row(obj: dict) -> tuple:
    return tuple(obj[col] for col in COLONNES)


def inserer(count: int, env: str) -> None:
    conn = obtenir_connexion()
    cur  = conn.cursor()
    try:
        rows = [{Nom}Factory() for _ in range(count)]
        cur.executemany(INSERT_SQL, [build_row(r) for r in rows])
        conn.commit()
        print(f"[OK] {{count}} ligne(s) insérée(s) dans `{snake}` (env={{env}}).")
    except Exception as e:
        conn.rollback()
        print(f"[ERREUR] Insertion échouée : {{e}}")
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10,
                        help="Nombre de lignes à insérer (défaut : 10)")
    parser.add_argument("--env", choices=["dev", "prod"], default="dev")
    args = parser.parse_args()

    inserer(args.count, args.env)


if __name__ == "__main__":
    main()
'''


def main():
    args, force = parse_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom   = validate_name(args[0].strip())
    snake = to_snake(nom)
    dest  = FIXTURES_DIR / f"{snake}_fixtures.py"

    if dest.exists() and not force:
        print(f"[ERREUR] {dest.relative_to(ROOT)} existe déjà. Utilisez --force pour écraser.")
        sys.exit(1)

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    was_new = not dest.exists()
    dest.write_text(TEMPLATE.format(Nom=nom, snake=snake, date=date.today()), encoding="utf-8")
    print(f"[OK] {dest.relative_to(ROOT)} {'créé' if was_new else 'régénéré'}.")
    print(f"     Déclarez vos champs dans {nom}Factory, puis :")
    print(f"     python sql/fixtures/{snake}_fixtures.py --count 20")


if __name__ == "__main__":
    main()
