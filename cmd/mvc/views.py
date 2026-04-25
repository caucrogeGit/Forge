#!/usr/bin/env python3
"""
Génère les templates HTML vides pour un contrôleur MVC.

Usage :
    python cmd/make.py views <NomEntite> [--force]

Options :
    --force, -f   Écrase les fichiers existants

Exemple :
    python cmd/make.py views Produit
    → mvc/views/produits/index.html
    → mvc/views/produits/create.html
    → mvc/views/produits/edit.html
    → mvc/views/produits/partials/fields.html
    → mvc/views/produits/partials/row.html
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _common import to_snake, parse_all_args, validate_name, pluralize, read_project_var

VIEWS_DIR = ROOT / read_project_var("VIEWS_DIR", "mvc/views", ROOT)

T_INDEX = """\
{{flash}}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold text-gray-800">Liste des {nom_pluriel}</h1>
    <a href="/{slug}/add" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        Ajouter
    </a>
</div>

<div class="bg-white rounded shadow overflow-hidden">
    <table class="w-full text-sm text-left">
        <thead class="bg-gray-200 text-gray-700 uppercase text-xs">
            <tr>
                <th class="px-4 py-3">ID</th>
                <!-- TODO: ajouter les colonnes -->
                <th class="px-4 py-3">Actions</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
            {{lignes}}
        </tbody>
    </table>
</div>

<div class="flex justify-between items-center mt-4">
    <a href="/{slug}?page={{prev_page}}" class="{{has_prev}} bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300">
        &larr; Précédent
    </a>
    <span class="text-gray-600 text-sm">Page {{page}} sur {{nb_pages}}</span>
    <a href="/{slug}?page={{next_page}}" class="{{has_next}} bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300">
        Suivant &rarr;
    </a>
</div>
"""

T_CREATE = """\
<div class="max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Ajouter un(e) {Nom}</h1>

    {{erreurs}}
    <form method="POST" action="/{slug}/add" class="bg-white rounded shadow p-6 space-y-4">
        <input type="hidden" name="csrf_token" value="{{csrf_token}}">

        <div>
            <label class="block text-sm font-medium text-gray-700">ID</label>
            <!-- TODO: adapter name/value au vrai nom de la clé primaire -->
            <input type="text" name="{Nom}Id" value="{{{Nom}Id}}" required
                class="mt-1 w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
        </div>

        {{champs}}

        <div class="flex gap-3 pt-2">
            <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
                Ajouter
            </button>
            <a href="/{slug}" class="bg-gray-200 text-gray-700 px-6 py-2 rounded hover:bg-gray-300">
                Annuler
            </a>
        </div>
    </form>
</div>
"""

T_EDIT = """\
<div class="max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Modifier un(e) {Nom}</h1>

    {{erreurs}}
    <form method="POST" action="/{slug}/edit" class="bg-white rounded shadow p-6 space-y-4">
        <input type="hidden" name="csrf_token" value="{{csrf_token}}">
        <!-- TODO: adapter au vrai nom de la clé primaire -->
        <input type="hidden" name="{Nom}Id" value="{{{Nom}Id}}">

        <div>
            <label class="block text-sm font-medium text-gray-700">ID</label>
            <input type="text" value="{{{Nom}Id}}" disabled
                class="mt-1 w-full border border-gray-200 rounded px-3 py-2 bg-gray-50 text-gray-500">
        </div>

        {{champs}}

        <div class="flex gap-3 pt-2">
            <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
                Enregistrer
            </button>
            <a href="/{slug}" class="bg-gray-200 text-gray-700 px-6 py-2 rounded hover:bg-gray-300">
                Annuler
            </a>
        </div>
    </form>
</div>
"""

T_FIELDS = """\
<!-- TODO: ajouter les champs du formulaire -->
<!-- Exemple :
<div>
    <label class="block text-sm font-medium text-gray-700">Nom</label>
    <input type="text" name="Nom" value="{{Nom}}" maxlength="40"
        class="mt-1 w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
</div>
-->
"""

T_ROW = """\
<tr class="hover:bg-gray-50">
    <!-- TODO: adapter au vrai nom de la clé primaire -->
    <td class="px-4 py-3">{{{Nom}Id}}</td>
    <!-- TODO: ajouter les colonnes -->
    <td class="px-4 py-3 flex gap-2">
        <a href="/{slug}/edit?id={{{Nom}Id}}"
           class="text-blue-600 hover:underline">Modifier</a>
        <form method="POST" action="/{slug}/delete">
            <input type="hidden" name="csrf_token" value="{{csrf_token}}">
            <input type="hidden" name="{Nom}Id" value="{{{Nom}Id}}">
            <button type="submit" class="text-red-600 hover:underline">Supprimer</button>
        </form>
    </td>
</tr>
"""

T_SHOW = """\
<div class="max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Détail — {Nom}</h1>

    <div class="bg-white rounded shadow p-6 space-y-3">
        <!-- TODO: afficher les champs, ex: <p><span class="font-medium">Nom :</span> {{{Nom}}}</p> -->
    </div>

    <div class="flex gap-3 mt-6">
        <a href="/{slug}/edit?id={{{snake}_id}"
           class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Modifier
        </a>
        <a href="/{slug}" class="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300">
            Retour
        </a>
    </div>
</div>
"""

FICHIERS = {
    "index.html"           : T_INDEX,
    "show.html"            : T_SHOW,
    "create.html"          : T_CREATE,
    "edit.html"            : T_EDIT,
    "partials/fields.html" : T_FIELDS,
    "partials/row.html"    : T_ROW,
}


def main():
    args, force, plural = parse_all_args()
    if len(args) != 1:
        print(__doc__)
        sys.exit(1)

    nom         = validate_name(args[0].strip())
    snake       = to_snake(nom)
    nom_pluriel = pluralize(snake)
    slug        = plural if plural else f"{snake}s"
    base_dir    = VIEWS_DIR / slug

    creees  = []
    ignores = []

    for chemin, contenu in FICHIERS.items():
        dest = base_dir / chemin
        if dest.exists() and not force:
            ignores.append(dest.relative_to(ROOT))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            contenu.format(Nom=nom, snake=snake, nom_pluriel=nom_pluriel, slug=slug),
            encoding="utf-8",
        )
        creees.append(dest.relative_to(ROOT))

    for f in creees:
        print(f"[OK]     {f}")
    for f in ignores:
        print(f"[IGNORÉ] {f}  (utilisez --force pour écraser)")

    if ignores:
        if creees:
            print("\n[ATTENTION] Certains fichiers existants n'ont pas été mis à jour.")
            print("[CONSEIL]   Utilisez --force pour regénérer TOUS les fichiers.")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
