# ADR-061 : Registre d'opt-ins visible et unifié dans le projet

## Statut

Proposée, Forge 1.0.0-rc.x (ticket `OPTIN-PROJECT-REGISTRY-001`).
Direction retenue ; deux questions de design restent ouvertes et sont tranchées dans la Décision ci-dessous.
S'appuie sur l'existant (`optins/registry.py`, `forge opt-in:enable`) et se lie à ADR-060 (le backend BDD devient un opt-in choisi par l'utilisateur).

---

## Date

2026-07-04

---

## Contexte

Les opt-ins Forge sont des paquets PyPI installés dans le `.venv` du projet (`site-packages`), jamais copiés dans l'arborescence utilisateur (principe 9).
Leur code est donc invisible dans le projet, ce qui est le bon choix : c'est exactement ce que fait Composer avec `vendor/` chez Symfony, et cela préserve la gestion des versions par pip.

Le problème est la **découvrabilité** : un développeur ne voit pas d'un coup d'œil quels opt-ins son projet utilise.

L'état actuel est partiel et hétérogène selon le type d'opt-in (`kind` du catalogue `cli/optins/catalog.py`) :

- les opt-ins `route` (iot, video, audio) laissent une trace visible : un dossier `optins/<name>/` et une inscription dans `optins/registry.py`, posés par `forge opt-in:enable` ;
- les opt-ins `library`, `crosscutting` et `cli` (rbac, i18n, qrcode, mfa, mail, deploy, etc.) ne laissent **aucune trace** dans le projet : ils vivent seulement dans le `.venv` ;
- le backend BDD (ADR-054, ADR-060) est encore plus invisible, puisqu'il devient une brique installée par l'utilisateur sans marqueur projet.

Les sources de vérité existantes sont insuffisantes prises isolément :

- `requirements.txt` liste ce qui est *installé* par pip, mêlé aux dépendances non opt-in ; il ne dit pas le rôle ni l'état ;
- `forge opt-in:list` lit un catalogue statique et n'affiche l'état projet que pour les opt-ins `route` ; il refuse volontairement de scanner les paquets installés (« pas de discovery magique ») ;
- `pip list` montre l'installé brut, sans lien avec la sémantique Forge.

Le modèle de référence est Symfony Flex, souvent mal résumé.
Symfony ne copie pas le code des bundles dans le projet : il reste dans `vendor/`.
La lisibilité vient de deux fichiers déclaratifs que Flex écrit dans le projet : `composer.json` (le manifeste installé) et surtout `config/bundles.php`, un **registre** listant une ligne par bundle activé.
Forge a déjà l'équivalent du premier (`requirements.txt`) et un embryon du second (`optins/registry.py`), mais ce dernier ne couvre que les opt-ins `route`.

---

## Décision

**Le projet porte un registre d'opt-ins unique et visible, `optins/registry.py`, qui liste tout opt-in utilisé par le projet, quel que soit son `kind`, plus le backend BDD choisi.**

C'est l'équivalent Forge de `config/bundles.php` : un fichier déclaratif, lisible, qui répond d'un coup d'œil à « quels opt-ins ce projet utilise-t-il ? », sans scanner le `.venv`.
Le code des opt-ins reste dans le `.venv` (aucune copie dans le projet, principe 9 préservé).

### Registre = opt-ins *utilisés*, déclaré explicitement

Le registre liste les opt-ins que le projet **utilise et active**, pas le résultat d'un scan des paquets installés.
Il est écrit uniquement par des commandes explicites (`forge opt-in:enable` / `disable`), jamais par découverte automatique (principe 3 : refuser la magie cachée).

Répartition des rôles, calquée sur Symfony (première question de design tranchée) :

- `requirements.txt` répond à « qu'est-ce qui est *installé* par pip ? » (équivalent `composer.json`) ;
- `optins/registry.py` répond à « quels opt-ins le projet *utilise* ? » (équivalent `config/bundles.php`).

Le recouvrement partiel pour les opt-ins `library` (installés et déclarés) est assumé : c'est exactement le modèle Symfony (un bundle figure dans `composer.json` et dans `bundles.php`).
La redondance est acceptable parce que les deux fichiers répondent à deux questions différentes et que le registre apporte le nom court, le `kind`, la catégorie et, pour les types qui en ont besoin, le câblage.

### Une ligne par opt-in, sémantique selon le `kind`

Chaque opt-in activé apparaît sous une forme déclarative unique, mais la portée de la ligne dépend de son `kind` (deuxième question de design tranchée) :

- `route` : la ligne porte le câblage réel (agrégation des `register_*_routes`, comme aujourd'hui) ;
- `crosscutting` : la ligne déclare le point de greffe si l'opt-in en a un ;
- `library` et `cli` : la ligne est **documentaire** (visibilité seule) ; ces opt-ins n'ont rien à câbler, mais leur présence au registre est ce qui rend le projet lisible d'un coup d'œil.

Un opt-in `cli` comme deploy, qui ne câble rien à l'exécution, obtient donc une ligne documentaire : c'est précisément le but recherché (le voir sans fouiller le `.venv`).

### Le backend BDD figure au registre

Le backend BDD choisi (ADR-060) s'inscrit lui aussi au registre, sur une ligne dédiée à sa famille exclusive (ADR-054 : un seul backend par projet).
C'est le point le plus invisible aujourd'hui ; l'y faire figurer répond directement au besoin qui a motivé ADR-060.

Forme illustrative (le format exact relève du ticket) :

```python
# optins/registry.py : registre des opt-ins du projet.
# Écrit et maintenu par « forge opt-in:enable / disable ». Édition manuelle possible.

BACKEND = "sqlite"          # forge-mvc-sqlite (ADR-054/060)

ENABLED_OPTINS = {
    "qrcode": "library",    # forge-mvc-qrcode
    "iot":    "route",      # forge-mvc-iot
    "deploy": "cli",        # forge-mvc-deploy
}

def register_optins(router):
    # câblage des opt-ins « route » activés (inchangé)
    ...
```

### Écriture sûre, fichier utilisateur

Le registre est un fichier du projet, donc du code utilisateur.
Les commandes qui l'écrivent conservent le contrat déjà en vigueur pour `opt-in:enable` : dry-run par défaut, `--apply` pour écrire, idempotence, jamais d'écrasement silencieux, aucun import du paquet opt-in (vérification par `importlib.util.find_spec`).
`forge opt-in:list` lit ce registre pour afficher l'état réel des opt-ins de tous les `kind`, sans scanner le `.venv`.

---

## Conséquences

Positives :

- Un fichier unique répond à « quels opt-ins ai-je ? », d'un coup d'œil, sans `pip list` ni fouille du `.venv`.
- Traitement homogène de tous les `kind` : la disparité route / library / cli disparaît.
- Le backend BDD redevient visible, ce qui referme le trou de découvrabilité ouvert par ADR-060.
- Fidèle au modèle Symfony correctement compris : code dans le `.venv`, lisibilité par registre déclaratif.
- Explicite et auditable (principe 3) : pas de découverte magique, le registre est du code lisible.

Coûts et limites :

- Un nouveau fichier de projet à générer et maintenir ; `opt-in:enable` / `disable` / `list` doivent être étendus à tous les `kind`.
- Recouvrement partiel avec `requirements.txt` pour les opt-ins `library` : tension apparente avec le principe 11, levée par la séparation des rôles (installé vs utilisé), mais à documenter clairement pour éviter la confusion.
- Le registre peut diverger du `.venv` (opt-in déclaré mais non installé, ou l'inverse) : `forge doctor` doit signaler l'incohérence.
- Les opt-ins `library` / `cli` gagnent une ligne documentaire sans effet à l'exécution : utile pour la lisibilité, mais il faut éviter de laisser croire qu'elle « active » un câblage.

---

## Trajectoire

1. **Format du registre** : figer la structure de `optins/registry.py` couvrant les quatre `kind` plus `BACKEND`.
2. **`opt-in:enable` / `disable`** : inscrire et retirer toute forme d'opt-in au registre, pas seulement les `route`.
3. **`opt-in:list`** : afficher l'état d'après le registre pour tous les `kind`.
4. **Backend au registre** : `forge db:*` (ou l'installation du backend) inscrit `BACKEND`, en cohérence avec ADR-060.
5. **`forge doctor`** : détecter les divergences registre vs `.venv` (déclaré non installé, installé non déclaré).
6. **Documentation** : onboarding et guidance agent (ADR-047) présentent `optins/registry.py` comme la vue d'ensemble des opt-ins du projet.

---

## Alternatives rejetées

**Copier le source de l'opt-in dans un dossier `packages/` du projet (vendoring visible).**
Rejetée : contredit le principe 9 (écriture de code framework dans le projet), casse la gestion des versions par pip (plus de correctifs), duplique le code et défait le packaging PyPI (ADR-005).
Ce n'est d'ailleurs pas ce que fait Symfony : son code de bundle reste dans `vendor/`.

**Ne rien ajouter ; ériger `requirements.txt` en manifeste et enrichir `opt-in:list` d'un scan des paquets installés.**
Plus léger, mais ne donne aucune vue dans l'arborescence du projet (le besoin exprimé), mélange opt-ins et dépendances techniques, et rouvre la tension du scan du `.venv` que `opt-in:list` refuse par principe.

**Découverte automatique des opt-ins installés par entry points, sans registre.**
Rejetée : c'est de la magie cachée (principe 3) ; l'activation d'un opt-in doit rester un acte explicite et visible dans le projet.

---

## Charte appliquée

Principe 3 (refuser la magie cachée), principe 8 (noyau minimal, briques opt-in), principe 9 (pas d'écriture invisible dans le code utilisateur), principe 11 (une seule façon officielle de faire chaque chose, via la séparation des rôles installé/utilisé), ADR-016 (modèle opt-in install/enable), ADR-054 (backends BDD), ADR-055 (catégories d'opt-ins), ADR-060 (squelette sans backend).
