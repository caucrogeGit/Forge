# ADR-051 : Insertion d'une méthode dans le contrôleur des pages publiques

## Statut

Proposé, Forge 1.0.0-beta.17 (ticket `ARCH-USER-CONTROLLER-REWRITE-ADR-001`).

ADR distinct annoncé par l'[ADR-030](030-explicit-route-injection.md), qui a
explicitement laissé hors de son périmètre la réécriture in-place d'un
contrôleur utilisateur (« question distincte, à trancher séparément, principe
4 »). Tant que cet ADR n'est pas accepté par le mainteneur, le comportement
décrit reste celui livré, sans modification de la charte.

---

## Date

2026-06-26

---

## Contexte

`forge make:public-page <Nom>` génère une page publique : un template, une route
(via le mécanisme d'injection cadré par l'ADR-030) et une **méthode de
contrôleur**. Cette dernière est posée par `_ensure_controller_method`
(`cli/public/public_page.py`), qui écrit dans
`mvc/controllers/public_pages_controller.py`, un fichier sous contrôle de
l'utilisateur.

Trois cas se présentent :

1. **Fichier absent** : Forge crée `public_pages_controller.py` avec la classe
   `PublicPagesController` et la méthode. C'est une écriture write-if-new,
   conforme au principe 9 (création d'un fichier nouveau).
2. **Méthode déjà présente** : un test (`def <méthode>(`) détecte la méthode ;
   Forge ne touche à rien. Comportement idempotent.
3. **Fichier présent sans la méthode** : Forge **insère** la méthode dans la
   classe `PublicPagesController` existante. L'insertion repère la fin de la
   classe par analyse **AST** (`ast.parse`, `ClassDef.end_lineno`), insère le
   bloc de méthode, puis réécrit le fichier.

Le cas 3 est une **modification in-place d'un fichier sous contrôle
utilisateur**, ce que le principe 4 (préserver le code utilisateur) et le
principe 9 (pas d'écriture invisible) encadrent strictement. C'est le point que
l'ADR-030 a renvoyé à un ADR dédié.

Garde-fous déjà présents dans le code livré :

- **Explicite** : l'écriture résulte d'une commande tapée par l'utilisateur
  (`make:public-page`), jamais d'un autre flux.
- **Idempotent** : la présence de la méthode est détectée avant insertion (cas
  2), ré-exécuter ne duplique pas.
- **Fail-safe** : si le fichier ne parse pas (`SyntaxError`) ou si la classe
  `PublicPagesController` est absente, Forge **n'écrit pas** et renvoie un
  avertissement invitant à compléter le contrôleur manuellement.
- **Ciblé** : l'insertion ne vise qu'un fichier et une classe de nom
  conventionnel Forge (`public_pages_controller.py` / `PublicPagesController`),
  jamais un contrôleur métier arbitraire.
- **Annoncé** : `make_public_page` renvoie un résultat (`controller_changed`,
  avertissement éventuel) affiché à l'utilisateur.

Limite assumée : si l'utilisateur a écrit lui-même une classe
`PublicPagesController` dans ce fichier conventionnel, Forge y insérera quand
même la méthode. Le nom est conventionnel et le fail-safe couvre les cas
ambigus, mais l'écriture reste in-place.

---

## Décision (proposée)

Acter le comportement du cas 3 comme **conforme**, en étendant au seul
contrôleur des pages publiques les quatre conditions de l'ADR-030 (explicite,
idempotent, délimité/visible, annoncé), renforcées par deux garanties propres au
code utilisateur :

5. **Fail-safe** : aucune écriture si le fichier ne parse pas ou si la classe
   cible est absente ; un avertissement oriente vers une complétion manuelle.
6. **Ciblé sur un nom conventionnel Forge** : seul
   `mvc/controllers/public_pages_controller.py` / `PublicPagesController` est
   modifié, jamais un contrôleur métier arbitraire.

La charte (principe 4) sera précisée, **après validation du mainteneur**, pour
distinguer la réécriture in-place silencieuse et arbitraire (interdite) de
l'insertion explicite, idempotente, fail-safe et ciblée sur un fichier
conventionnel généré par Forge (autorisée pour `make:public-page`).

---

## Conséquences

- `make:public-page` conserve sa valeur (câbler une page publique d'un geste)
  sans dégrader l'UX vers un mode « affichage » pur.
- Le périmètre reste étroit : aucune autre commande n'est autorisée à modifier
  in-place un contrôleur ; les contrôleurs métier restent intouchables.
- Un test de garde-fou pourra verrouiller les invariants (fail-safe sur fichier
  non parsable, idempotence, ciblage sur `PublicPagesController`).

---

## Alternatives écartées

- **Re-scoper `make:public-page` en mode affichage** (comme `make:crud`) :
  respecterait le principe 4 à la lettre mais imposerait à l'utilisateur de
  coller la méthode lui-même, dégradant une commande dont la valeur est le
  câblage d'un geste. Corriger ce symptôme plutôt que préciser la portée du
  principe 4 contredit la règle d'évolution A (retirer la cause, pas le
  symptôme).
- **Laisser la contradiction implicite** : expose à un reproche d'audit
  récurrent sur un principe non négociable, comme c'était le cas avant
  l'ADR-030.

---

## Référence

- [ADR-030](030-explicit-route-injection.md) : injection de routes par commande
  explicite, qui a renvoyé ce point à un ADR distinct.
- `cli/public/public_page.py` (`_ensure_controller_method`).
- Charte : `CHARTE_DOC.md` (principe 4, préserver le code utilisateur ; principe
  9, pas d'écriture invisible ; règle d'évolution A).
