# Vocabulaire : opt-in, package, module

Ce glossaire fixe le vocabulaire canonique de Forge pour tout ce qui touche
aux capacités optionnelles. Il applique [ADR-016](../adr/016-opt-in-unification.md)
(D1) et le principe §11 de la charte (« une seule façon officielle de faire
chaque chose »).

Trois mots, trois référents distincts, **zéro recouvrement** :

| Terme | Référent | Tu le… |
|---|---|---|
| **opt-in** | une brique optionnelle officielle | actives / désactives |
| **package** | le véhicule de distribution PyPI d'un opt-in officiel | (détail interne) |
| **module** | une unité applicative que **tu** écris localement (`modules/`) | crées / installes localement |

## opt-in

Le **concept central**. Un opt-in est une capacité optionnelle, séparée du
noyau minimal (principe §8). Forge en distribue six officiels :
`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`,
`forge-mvc-media`, `forge-mvc-iot`.

Un opt-in a une **source** :

- **officielle** — livré comme *package* PyPI ;
- **locale** — un *module* que tu écris dans ton projet.

Son cycle de vie suit deux axes orthogonaux (quatre verbes) :

```
                 install              enable
   absent  ───────────────▶  installé  ───────────────▶  activé
           ◀───────────────           ◀───────────────
                 remove               disable
```

- `install` / `remove` → **présence** (le code est-il sur la machine ?) ;
- `enable` / `disable` → **activation** (est-il branché dans l'app ?).

Deux garanties par construction : `install` n'active jamais tout seul (§3,
« refuser la magie cachée ») ; `disable` ne désinstalle jamais.

Un opt-in activé vit sous `optins/<name>/`, quelle que soit sa source.

## package

Le simple **véhicule de distribution** : un opt-in officiel est *livré comme*
un package PyPI sous le namespace `forge-mvc-*`, et expose son API depuis le
namespace Python `forge_mvc_*`. Terme purement technique — on n'« installe pas
un package », on **active un opt-in** (qui se trouve livré comme package).

## module

Réservé au **système local** (`modules/`, manifeste `module.json`) : une unité
applicative que le développeur **écrit lui-même** dans son projet, par
opposition à une brique officielle qu'il **consomme**. Dans le modèle ADR-016,
un module local est un opt-in de **source locale**.

Le mot « module » ne désigne **plus** les briques officielles (on dit
« opt-in »). Il reste aussi, hors de ce périmètre, son sens Python habituel
(un fichier `.py` importable).

## En une phrase

> Un **opt-in** est une capacité optionnelle qu'on active/désactive ; il est
> *livré comme* un **package** (s'il est officiel) ou écrit comme un
> **module** local (s'il est à toi).
