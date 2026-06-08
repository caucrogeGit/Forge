# ADR-030 — Injection de routes par commande explicite et règle 4.3

## Statut

Proposé — Forge 1.0.0-beta.15 (ticket `ADR-EXPLICIT-ROUTE-INJECTION-001`).

Précise la portée de la règle de génération 4.3 de la charte v2 (« le fichier
principal de routes applicatives `mvc/routes.py` reste sous le contrôle explicite
du développeur ; pas de marqueurs commentaires auto-injectés, pas de réécriture
automatique »). Aucune modification de `CHARTE_DOC.md` n'est appliquée tant que
le mainteneur n'a pas validé cet ADR.

---

## Date

2026-06-08

---

## Contexte

La règle 4.3 de la charte v2 interdit la réécriture automatique de
`mvc/routes.py`. Or deux familles de commandes l'écrivent aujourd'hui :

- `forge starter:build <starter>` injecte un bloc de routes encadré par des
  marqueurs `# forge-starter:<nom>:start` / `:end`, et ajuste au besoin la route
  racine (`forge_cli/starters/route_ops.py`).
- `forge make:public-page` / `make:public-list` / `make:public-form` insèrent un
  import et un bloc de route dans le `mvc/routes.py` existant
  (`forge_cli/public_page.py`, `public_list.py`, `public_form.py`).

Cette injection est un choix délibéré, déjà acté par l'ADR-023 pour
`starter:build`, mais jamais réconcilié avec la lettre de la règle 4.3. Un
auditeur strict peut donc considérer le comportement livré comme non conforme à
une règle marquée « non négociable ».

Dans le même temps, le générateur `make:crud` **n'injecte pas** : il **affiche**
le bloc de routes sur la sortie standard, à coller manuellement. Il existe donc
deux comportements selon le générateur.

Le point à trancher : la règle 4.3 interdit-elle **toute** écriture dans
`mvc/routes.py`, ou seulement l'écriture **silencieuse et automatique** que le
développeur n'a pas demandée ?

---

## Décision

La règle 4.3 vise l'écriture **silencieuse et automatique** : Forge ne doit
jamais réécrire `mvc/routes.py` de sa propre initiative, en arrière-plan, sans
geste de l'utilisateur. Elle **n'interdit pas** une commande de scaffolding que
le développeur invoque explicitement.

Une commande Forge est autorisée à injecter des routes dans `mvc/routes.py` si,
et seulement si, **les quatre conditions** suivantes sont réunies :

1. **Explicite** : l'écriture résulte d'une commande que l'utilisateur tape
   lui-même (`starter:build`, `make:public-*`). Aucune écriture déclenchée par un
   autre flux (démarrage, autre générateur, hook) n'est permise.
2. **Idempotente** : ré-exécuter la commande ne duplique pas le bloc ; la
   présence du bloc (ou de la route) est détectée avant insertion.
3. **Délimitée et visible** : le bloc injecté est encadré par des marqueurs
   lisibles (`# forge-starter:<nom>:start` / `:end`) ou clairement identifiable,
   de sorte que le développeur voie et puisse retirer ce qui a été ajouté.
4. **Annoncée** : la commande signale sur la sortie standard ce qu'elle a écrit
   (fichier touché, route ajoutée).

Toute détection de point d'injection se fait de manière **robuste** (analyse AST
ou ancrage fiable), jamais par simple sous-chaîne susceptible d'être trompée par
un commentaire ou une chaîne (cf. correctif `FIX-PUBLIC-ROUTES-MARKER-001`).

Le mode **affichage** de `make:crud` reste une variante conservatrice acceptable
et n'a pas à être aligné sur l'injection : pour un générateur d'entité unique,
laisser le développeur coller lui-même la route est un choix légitime. Les deux
modes coexistent, chacun adapté à son contexte (scaffolding complet d'un opt-in
vs route d'une entité).

---

## Conséquences

- La charte (règle 4.3) sera précisée, après validation du mainteneur, pour
  distinguer « réécriture silencieuse/automatique » (interdite) de « injection
  par commande explicite répondant aux quatre conditions » (autorisée).
- `starter:build` et `make:public-*` sont conformes dès lors qu'ils respectent
  les quatre conditions ; le correctif de détection robuste du marqueur `router`
  (`FIX-PUBLIC-ROUTES-MARKER-001`) renforce la condition 2.
- Les contrôleurs applicatifs (`mvc/controllers/*.py`) ne sont **pas** couverts
  par cette autorisation : la réécriture in-place d'un contrôleur utilisateur
  reste une question distincte, à trancher séparément (principe 4, préservation
  du code utilisateur).
- Aucune écriture dans `mvc/routes.py` hors commande explicite ne devient
  permise ; le périmètre reste étroit.

---

## Alternatives écartées

- **Tout basculer en mode affichage (comme `make:crud`)** : respecterait 4.3 à la
  lettre mais dégraderait l'UX de `starter:build`, dont la valeur est précisément
  de câbler l'opt-in d'un geste. Corriger ce symptôme plutôt que la portée trop
  large de 4.3 contredit la règle d'évolution A (retirer la cause, pas le
  symptôme).
- **Laisser la contradiction implicite** : expose à un reproche d'audit récurrent
  sur une règle « non négociable ».
