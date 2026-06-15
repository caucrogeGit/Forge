# Préambule : construire vos façades helper

Ce parcours vous apprend à construire, **à la main**, un petit jeu de façades de
confort dans `mvc/helpers/` : `Session`, `Cookies`, `Flash`. Ce sont des
**regroupements ergonomiques** par-dessus les briques explicites du noyau.

!!! info "Pourquoi côté application, et pas dans le noyau"
    Le noyau Forge reste **minimal et explicite** (pas de magie cachée). Le
    confort, regrouper plusieurs fonctions sous un point d'entrée, est la
    responsabilité de **votre application**. Ces façades sont **votre code** :
    libre à vous de les étendre. Ce tutoriel vous montre comment les écrire ;
    Forge ne les impose pas.

## Prérequis

- Un projet Forge déjà créé (voir [Parcours Welcome Forge](../welcome-forge/index.md)).
- Le dossier `mvc/helpers/` existe déjà (créé par `forge new`, avec un
  `__init__.py` vide).

## Ce que vous allez obtenir

Un dossier `mvc/helpers/` structuré, où chaque façade couvre **un** concern du
noyau, toutes bâties sur une même base non instanciable :

    mvc/helpers/
    ├── __init__.py     # ré-exporte les façades
    ├── _facade.py      # base commune : namespace non instanciable
    ├── session.py      # class Session  — le store de session
    ├── cookies.py      # class Cookies  — cookies applicatifs
    └── flash.py        # class Flash    — messages flash

[Continuer avec La base Facade](facade-base.md)
