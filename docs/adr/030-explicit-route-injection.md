# ADR-030 : Injection de routes par commande explicite et règle 4.3

## Statut

Acceptée, Forge 1.0.0-beta.17 (ticket `GOV-ADR-STATUS-RESOLVE-001`).
Proposé en 1.0.0-beta.15 (ticket `ADR-EXPLICIT-ROUTE-INJECTION-001`), révisé en 1.0.0-beta.17 (ticket `ADR-030-REVISION-001`) pour retirer la référence à `starter:build`, commande supprimée par l'ADR-035.

La décision est appliquée dans le code : les `make:public-*` injectent les routes selon les quatre conditions, avec détection robuste du marqueur `router` (`FIX-PUBLIC-ROUTES-MARKER-001`).
La précision du texte de la règle 4.3 de `CHARTE_DOC.md` reste un geste mainteneur distinct, non appliqué par cet ADR.

Précise la portée de la règle de génération 4.3 de la charte v2 (« le fichier principal de routes applicatives `mvc/routes.py` reste sous le contrôle explicite du développeur ; pas de marqueurs commentaires auto-injectés, pas de réécriture automatique »).
Aucune modification de `CHARTE_DOC.md` n'est appliquée tant que le mainteneur n'a pas validé cet ADR.

---

## Date

2026-06-08 (révisé le 2026-06-19).

---

## Contexte

La règle 4.3 de la charte v2 interdit la réécriture automatique de `mvc/routes.py`.
Or les commandes `make:public-*` l'écrivent aujourd'hui :

- `forge make:public-page`, `make:public-list`, `make:public-form`, `make:public-show` et `make:public-contact` insèrent un import et un bloc de route dans le `mvc/routes.py` existant (`cli/public/public_page.py`, `public_list.py`, `public_form.py`, etc.).

Note historique : un second injecteur, `forge starter:build`, encadrait son bloc par des marqueurs `# forge-starter:<nom>:start` / `:end` et ajustait la route racine.
Cette commande a été **supprimée** par l'ADR-035 (bêta.16, retrait de la génération de starters).
Le présent ADR ne couvre donc plus que les `make:public-*`.

Cette injection est un choix délibéré, jamais réconcilié avec la lettre de la règle 4.3.
Un auditeur strict peut donc considérer le comportement livré comme non conforme à une règle marquée « non négociable ».

Dans le même temps, le générateur `make:crud` **n'injecte pas** : il **affiche** le bloc de routes sur la sortie standard, à coller manuellement.
Il existe donc deux comportements selon le générateur.

Le point à trancher : la règle 4.3 interdit-elle **toute** écriture dans `mvc/routes.py`, ou seulement l'écriture **silencieuse et automatique** que le développeur n'a pas demandée ?

---

## Décision

La règle 4.3 vise l'écriture **silencieuse et automatique** : Forge ne doit jamais réécrire `mvc/routes.py` de sa propre initiative, en arrière-plan, sans geste de l'utilisateur.
Elle **n'interdit pas** une commande de scaffolding que le développeur invoque explicitement.

Une commande Forge est autorisée à injecter des routes dans `mvc/routes.py` si, et seulement si, **les quatre conditions** suivantes sont réunies :

1. **Explicite** : l'écriture résulte d'une commande que l'utilisateur tape lui-même (`make:public-*`).
   Aucune écriture déclenchée par un autre flux (démarrage, autre générateur, hook) n'est permise.
2. **Idempotente** : ré-exécuter la commande ne duplique pas le bloc ; la présence du bloc (ou de la route) est détectée avant insertion.
3. **Délimitée et visible** : le bloc injecté est clairement identifiable, de sorte que le développeur voie et puisse retirer ce qui a été ajouté.
4. **Annoncée** : la commande signale sur la sortie standard ce qu'elle a écrit (fichier touché, route ajoutée).

Toute détection de point d'injection se fait de manière **robuste** (analyse AST ou ancrage fiable), jamais par simple sous-chaîne susceptible d'être trompée par un commentaire ou une chaîne (cf. correctif `FIX-PUBLIC-ROUTES-MARKER-001`).

Le mode **affichage** de `make:crud` reste une variante conservatrice acceptable et n'a pas à être aligné sur l'injection : pour un générateur d'entité unique, laisser le développeur coller lui-même la route est un choix légitime.
Les deux modes coexistent, chacun adapté à son contexte (scaffolding d'une page publique vs route d'une entité).

---

## Conséquences

- La charte (règle 4.3) sera précisée, après validation du mainteneur, pour distinguer « réécriture silencieuse/automatique » (interdite) de « injection par commande explicite répondant aux quatre conditions » (autorisée).
- Les `make:public-*` sont conformes dès lors qu'ils respectent les quatre conditions ; le correctif de détection robuste du marqueur `router` (`FIX-PUBLIC-ROUTES-MARKER-001`) renforce la condition 2.
- Les contrôleurs applicatifs (`mvc/controllers/*.py`) ne sont **pas** couverts par cette autorisation : la réécriture in-place d'un contrôleur utilisateur reste une question distincte, à trancher séparément (principe 4, préservation du code utilisateur).
- Aucune écriture dans `mvc/routes.py` hors commande explicite ne devient permise ; le périmètre reste étroit.

---

## Alternatives écartées

- **Tout basculer en mode affichage (comme `make:crud`)** : respecterait 4.3 à la lettre mais dégraderait l'UX des `make:public-*`, dont la valeur est de câbler la page d'un geste.
  Corriger ce symptôme plutôt que la portée trop large de 4.3 contredit la règle d'évolution A (retirer la cause, pas le symptôme).
- **Laisser la contradiction implicite** : expose à un reproche d'audit récurrent sur une règle « non négociable ».

---

## Référence

- ADR-023 `starter:build` canonique (commande retirée depuis par l'ADR-035) : [ADR-023](023-starter-build-canonical.md).
- ADR-035 starters réalisés à la main (retrait de la génération) : [ADR-035](035-starters-manual-not-generated.md).
- Correctif de détection robuste du `router` : `FIX-PUBLIC-ROUTES-MARKER-001`.
- Charte : `CHARTE_DOC.md` (règle 4.3 ; règle d'évolution A).
