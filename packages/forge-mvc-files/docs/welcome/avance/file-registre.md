# Avancé 5 : Le registre et les orphelins

Objectif : savoir ce qui est sur le disque, et effacer ce qui ne sert plus.

## Une table qui double le disque

Chaque fichier écrit par Forge s'inscrit dans une table : chemin, nom d'origine, taille, type, propriétaire.

```python
from forge_mvc_files import get_file_record, list_paths_for_owner, owner_file_count

combien = owner_file_count("user", utilisateur.id)
```

Sans elle, trois questions restent sans réponse : combien cet utilisateur occupe-t-il, à qui appartient ce fichier, et lesquels ne servent plus à personne.

## La purge d'orphelins

```bash
forge files:orphans
forge files:orphans --delete
```

Un **orphelin** est un fichier présent sur le disque et absent du registre.
La commande les liste ; `--delete` les efface.

!!! danger "Tout ce qui écrit doit inscrire"
    Un opt-in qui écrit sous `UPLOAD_ROOT` sans inscrire produit des fichiers que cette purge prendra pour des orphelins.

    C'est arrivé : les images et leurs variantes étaient écrites sans inscription, et `--delete` les supprimait. La règle n'est pas un confort de comptage, c'est ce qui empêche une purge de détruire des fichiers vivants.

!!! warning "Un fichier trop récent n'est jamais un orphelin"
    Une écriture en cours n'a pas encore été inscrite : la prendre pour un orphelin la détruirait pendant qu'elle se fait.

    La purge ignore donc ce qui est plus jeune qu'un âge minimum.

!!! info "La purge refuse d'agir sur un registre vide"
    Un registre vide et un disque plein signifie presque toujours que la table n'a pas été provisionnée, pas que tout est orphelin.

    Effacer alors viderait le disque : la commande refuse et le dit.

## À retenir

- Le registre répond à « à qui », « combien », « lequel ne sert plus ».
- Écrire sans inscrire, c'est fabriquer des orphelins que la purge détruira.
- Deux garde-fous : l'âge minimum, et le refus sur registre vide.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
