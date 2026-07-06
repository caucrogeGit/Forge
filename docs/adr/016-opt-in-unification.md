# ADR-016 : Unification du modèle opt-in : concept unique, cycle install/enable à 4 verbes

## Statut

Acceptée

> Décision-cadre.
> Les tickets d'exécution la référencent (« charte appliquée : ADR-016 »).

---

## Contexte

Forge distribue six briques optionnelles (`forge-mvc-mfa`, `forge-mvc-rbac`, `forge-mvc-workflow`, `forge-mvc-stats`, `forge-mvc-media`, `forge-mvc-iot`) en plus du noyau minimal.
L'expérience de ces briques souffre aujourd'hui de trois incohérences accumulées au fil des versions :

### 1. Trois mots pour un même référent

Une même chose, une brique optionnelle, est nommée de trois façons selon l'endroit :

- **module** : « modules officiels » (CLAUDE.md §1, ADR-005) ;
- **package** : la distribution PyPI (`forge-mvc-iot`) ;
- **opt-in** : « opt-ins officiels » (docs d'installation).

Pire, deux de ces mots sont **doublement chargés** : « module » désigne aussi le système local `modules/` (`module:install` / `module:remove`, `module.json`) et « opt-in » désigne aussi la couche de câblage `optins/` (`register_optins`).

### 2. Trois mécanismes de branchement hétérogènes

Les briques n'ont pas la même surface de contact avec une application :

- **possède des routes** (`iot`) → expose `register_iot_routes(router)`, se branche via la couche `optins/` ;
- **bibliothèque pure** (`workflow`, `stats`, `media`) → on importe et on appelle ses fonctions ; rien à brancher ;
- **transversale** (`mfa`, `rbac`) → se greffe dans un flux existant (`mfa_available()` dans le squelette, décorateurs pour RBAC).

Conséquence visible : `optin:enable` ne supporte que `iot`, et `forge_mvc_rbac` **s'auto-enregistre à l'import** (un provider de contexte Jinja), ce qui contredit le principe §3 « refuser la magie cachée ».

### 3. Install / désinstall asymétriques

- le système `modules/` local a `module:install` **et** `module:remove` (symétriques, retrait de bloc par marqueurs) ;
- le système `optins/` a `optin:enable` mais **pas** `optin:disable` ;
- `starter:build` injecte des routes mais n'a pas de retrait.

Le retrait propre existe donc côté « module » mais pas côté « opt-in ».

### 4. Squelette non neutre

`mvc/routes.py` livre par défaut des routes pré-câblées (auth, MFA conditionnel, starter `welcome`).
Un développeur qui clone le dépôt ou installe via pipx n'obtient pas un squelette vierge : des capacités sont déjà branchées sans geste explicite de sa part.

### Fenêtre temporelle

Forge est en bêta publique pré-1.0.
La convention (CLAUDE.md §2) autorise les ruptures internes **sans alias dépréciés** avant le tag 1.0 stable.
C'est la fenêtre idéale pour unifier sans dette de compatibilité.

---

## Décision

### D1 : « opt-in » est le concept unique

« opt-in » devient le **seul** terme désignant une brique optionnelle.
Le mot « module officiel » est retiré de la documentation, des ADR et des messages CLI.
« package » est conservé **uniquement** comme véhicule de distribution (« un opt-in officiel est *livré comme* un package PyPI »).

Le mot « module » reste disponible pour le seul système **local** (code que le développeur écrit lui-même), désormais traité comme un opt-in de **source locale**, sans recouvrement avec les briques officielles.

### D2 : Deux axes orthogonaux, quatre verbes

Le cycle de vie d'un opt-in se décompose en deux axes indépendants :

- **présence** (le code est-il sur la machine ?) → `install` / `remove` ;
- **activation** (est-il branché dans l'app ?) → `enable` / `disable`.

```
                 install              enable
   absent  ───────────────▶  installé  ───────────────▶  activé
           ◀───────────────           ◀───────────────
                 remove               disable
```

| Commande | Axe | Source officielle | Source locale |
|---|---|---|---|
| `forge opt-in:install <x>` | présence + | `pip install` / `pipx inject` | scaffold `optins/<x>/` |
| `forge opt-in:enable <x>` | activation + | câblage + `register_optins` | injection de marqueurs dans `mvc/routes.py` |
| `forge opt-in:disable <x>` | activation − | retrait des marqueurs (laisse installé) | idem |
| `forge opt-in:remove <x>` | présence − | `pip uninstall` / `pipx uninject` | suppression de `optins/<x>/` (gardée, voir D6) |
| `forge opt-in:list` | lecture | source + état (`absent` / `installé` / `activé`) | idem |

### D3 : Garanties par construction

- `install` **n'active jamais** automatiquement (§3 « refuser la magie cachée » garanti par le découpage) ;
- `disable` **ne désinstalle jamais** (débranchement réversible sans perte de code).

### D4 : Emplacement unique des opt-ins activés

Tout opt-in activé vit sous `optins/<name>/`, quelle que soit sa source.
Le dossier contient deux natures de fichiers selon la source :

- officiel → câblage mince **généré** (régénérable, write-if-new) ;
- local → **code utilisateur** (protégé §9, hook `forge-write-if-new.sh`).

### D5 : Fusion des moteurs et rupture CLI

Les deux moteurs `module:*` et `optin:*` fusionnent en une seule famille `opt-in:*`.
Les anciennes commandes (`module:install`, `module:remove`, `module:files`, `module:routes`, `optin:enable`, `optin:list`) sont **supprimées franchement**, sans alias déprécié (fenêtre pré-1.0).
Le moteur de retrait par marqueurs existant (`module:remove`, `route_ops`) est réutilisé pour `opt-in:disable`.

### D6 : `remove` sur source locale est une opération gardée

`opt-in:remove` sur une source **officielle** se borne à désinstaller le package : aucun fichier utilisateur touché.
Sur une source **locale**, il supprimerait du code écrit par le développeur ; il est donc :

- **non destructif par défaut** : affiche ce qui serait supprimé (`--dry-run` implicite, convention Forge) ;
- **destructif seulement avec `--force`** + confirmation explicite ;
- aligné sur le hook `forge-write-if-new.sh` (le CLI ne le contourne pas).

### D7 : Squelette neutre

`mvc/routes.py` livré par défaut ne contient qu'une route :

```python
from core.http.router import Router
from mvc.controllers.home_controller import HomeController

router = Router()

with router.group("", public=True) as public:
    public.add("GET", "/", HomeController.index, name="home")
```

Auth, MFA et le starter `welcome` ne sont plus pré-câblés : ils s'ajoutent par `opt-in:*` (auth/MFA) ou `starter:build` (welcome).

### D8 : Adaptateur trois-formes

Derrière l'interface uniforme `opt-in:*`, un adaptateur résout la forme de chaque opt-in (monter des routes / greffer des contrôleurs / pure bibliothèque / copie de fichiers locaux).
**L'uniformité vit au niveau du contrat, pas de l'implémentation** ; l'utilisateur ne voit jamais la différence.

### D9 : Les starters restent hors périmètre

Un starter est une **démo pédagogique**, pas une capacité optionnelle.
Les commandes `starter:*` restent distinctes de `opt-in:*`.

---

## Conséquences

- **Rupture CLI assumée** : les commandes `module:*` et `optin:*` disparaissent au profit de `opt-in:*`.
  Acceptable en pré-1.0 (CLAUDE.md §2).
- **Renommage transverse** : « module officiel » → « opt-in » dans CLAUDE.md, ADR-005, docs d'installation, textes d'aide.
- **Migration des tests** : les meta-tests qui épinglent l'ancien vocabulaire, les anciennes commandes ou les blocs du squelette (`test_app_default_no_mfa_001`, `test_module_remove_001`, etc.) doivent être ajustés ou redéployés.
- **Correctif §3** : l'auto-enregistrement Jinja de `forge_mvc_rbac` à l'import doit redevenir explicite (sinon une brique se branche dans le dos de l'utilisateur, en contradiction avec D3).
- **Réversibilité acquise** : tout opt-in devient désactivable proprement, ce qui n'était vrai que pour les modules locaux.
- **Découpage en tickets** : vocabulaire → squelette neutre → CLI unifié → adaptateur + source locale → migration des tests (un ticket = une responsabilité, §5).

---

## Alternatives considérées

**Garder « module » comme mot canonique.**
Plus familier, mais « module » est déjà pris par le système local et par « module officiel » ; le mot ne porte pas la philosophie du choix explicite.
Écarté au profit d'« opt-in », terme déjà présent dans la doc et porteur du principe §8.

**Conserver les deux moteurs séparés (`module:*` et `optin:*`).**
Maintient la duplication et l'asymétrie de retrait.
Écarté : la valeur recherchée est précisément une surface unique pour l'utilisateur.

**Un seul verbe `remove --purge` plutôt que quatre verbes.**
Mélange les axes présence et activation dans une seule commande paramétrée.
Écarté : séparer `install`/`remove` (présence) de `enable`/`disable` (activation) rend les états explicites et garantit « install n'active pas » / « disable ne désinstalle pas » par construction.

**Uniformiser aussi l'implémentation du branchement.**
Forcerait une cérémonie `register_optins` vide sur les bibliothèques pures (`stats`, `workflow`, `media`).
Écarté : l'uniformité doit vivre au niveau du contrat (D8), pas des mécanismes internes.

**Inclure les starters dans le modèle opt-in.**
Les starters injectent aussi des routes, mais ce sont des démos pédagogiques, pas des capacités.
Les fusionner brouillerait les deux intentions.
Écarté (D9).

---

## Amendements

### A1 : Câblage opt-in : pattern registre, pas marqueurs (palier 3b)

D2/D4 décrivaient `opt-in:enable` comme « injection marqueurs + register_optins ».
L'implémentation (palier 3b) a révélé que la couche `optins/` existante utilise **uniquement le pattern registre** : un seul point d'injection dans `mvc/routes.py` (`register_optins(router)`) qui délègue à `optins/registry.py`, puis à chaque opt-in.
C'est un design **plus propre** que des marqueurs par opt-in (un seul appel dans `routes.py`, aucun bloc par brique) et `optin:enable --apply` l'auto-injecte déjà.

**Décision retenue** : conserver le pattern registre pour le câblage des opt-ins.
Les marqueurs `# forge-starter:<id>` restent réservés aux **starters** et aux **modules locaux** (qui injectent un bloc de routes).
`opt-in:enable` n'utilise pas de marqueurs ; `opt-in:disable` est l'inverse exact d'`enable` (retire la couche `optins/<name>/` et l'appel `register_optins` si plus aucun opt-in actif).

`opt-in:enable`/`disable` restent limités à `iot` jusqu'à l'adaptateur 3-formes (ticket 4), qui généralise le câblage aux six opt-ins.

### A2 : Le système `module:*` local reste distinct (ticket 4b)

D5 prévoyait de fusionner les moteurs `module:*` et `optin:*`.
L'implémentation (palier 4b) a révélé que le système de **module local** a un cycle de vie d'**auteur** fondamentalement différent du modèle opt-in à 4 verbes :

- `module:install`, **déclare** le module dans `forge_modules.json` ;
- `module:files`, **copie** les fichiers dans l'application ;
- `module:routes`, **génère** un fichier `mvc/routes_<module>.py` séparé à copier (« Forge affiche », ne touche jamais `mvc/routes.py`) ;
- `module:remove`, retire ce que Forge peut prouver avoir installé.

Ce *déclarer → copier → générer-des-routes* (on **fabrique** sa brique) ne mappe pas 1:1 sur *install affiche / enable câble / disable débranche* (on **consomme** une brique officielle).
Forcer la fusion reviendrait à redéfinir un sous-système testé et à migrer ~40 tests pour un seul nom de commande unifié.

**Décision retenue** : **ne pas fusionner**.
Le système `module:*` reste l'outil du workflow d'auteur de **module local** ; la famille `opt-in:*` couvre les **opt-ins officiels** (catalogue `cli/optins/catalog.py`).
Conceptuellement, un module local **est** un « opt-in de source locale » (vocabulaire unifié, [glossaire](../reference/vocabulaire-opt-in.md)), mais il garde ses commandes propres car son cycle de vie diffère.
Quand un nom inconnu est passé à `opt-in:*`, la commande **oriente** vers `forge module:install`.

Cet amendement **clôt** la trajectoire ADR-016 : la surface opt-in officielle est unifiée (`install`/`remove`/`enable`/`disable`/`list`), kind-aware, sans commandes legacy.

---

## Liens

- Charte : principes §3 (magie cachée), §8 (noyau minimal, briques opt-in), §9 (pas d'écriture invisible), §11 (une seule façon officielle).
- [ADR-004](004-core-perimeter.md), périmètre du core minimal.
- [ADR-005](005-packaging.md), packaging monorepo + distributions PyPI.
- [ADR-012](012-legacy-format-deprecation-policy.md), politique de dépréciation (cadre pour la rupture pré-1.0 sans alias).
