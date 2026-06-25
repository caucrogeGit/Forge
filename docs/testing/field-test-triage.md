# Tests terrain, Triage et stabilisation

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

## 1. But

Ce document sert au référent Forge après réception des retours de testeurs.

Il permet de :

- normaliser les retours ;
- classer les problèmes ;
- distinguer bug, documentation, ergonomie et hors périmètre ;
- décider des tickets correctifs ;
- décider si Forge peut avancer vers une release candidate ou une version stable.

## 2. Triage initial

Pour chaque retour, remplir :

| Champ | Valeur |
|---|---|
| Ticket FT concerné |  |
| Testeur |  |
| Statut du testeur |  |
| Gravité proposée |  |
| Aide utilisée | A0/A1/A2/A3/A4/A5 |
| Reproductible | oui/non/à vérifier |
| Type principal | bug / documentation officielle erronée / documentation incomplète / ergonomie / environnement / hors périmètre |
| Impact | installation / config / DB / route / template / CLI / CRUD / sécurité / déploiement / autre |
| Décision | corriger / documenter / backlog / refuser / demander compléments |

## 3. Règles de décision

### S0, Bloquant critique

Créer un ticket correctif immédiat.

Exemples :

- installation impossible sur environnement censé être supporté ;
- perte de données ;
- faille évidente ;
- framework inutilisable ;
- erreur empêchant tout projet de démarrer.

### S1, Bloquant fonctionnel

Créer un ticket correctif prioritaire avant release candidate.

Exemples :

- commande documentée qui échoue ;
- CRUD inutilisable ;
- migration impossible ;
- auth annoncée mais non fonctionnelle ;
- documentation qui mène à une impasse.

### S2, Friction forte

Créer soit :

- un ticket de correction ;
- un ticket documentation ;
- un ticket ergonomie CLI ;
- une limite documentée.

Exemples :

- message d’erreur incompréhensible ;
- procédure correcte mais trop implicite ;
- documentation incomplète ;
- comportement surprenant mais contournable.

### S3, Friction mineure

Classer backlog ou traiter si simple.

Exemples :

- wording perfectible ;
- commande manquant d’exemple ;
- petit inconfort non bloquant.

### S4, Suggestion

Backlog post-stable.

Exemples :

- amélioration UX ;
- commande de confort ;
- nouvelle option ;
- idée pour Forge Design.

### S5, Hors périmètre

Classer hors campagne.

Exemples :

- demande métier spécifique ;
- demande de paiement ;
- demande SaaS ;
- demande Forge Design hors campagne core ;
- préférence personnelle non liée à la validation terrain.


## 4. Cas spécifique, Documentation officielle erronée

Si un retour signale une documentation officielle fausse, incomplète ou contradictoire, le référent doit vérifier :

- page concernée ;
- passage concerné ;
- étape du ticket touchée ;
- comportement annoncé par la documentation ;
- comportement réel observé ;
- preuve fournie ;
- contournement éventuel ;
- impact sur le ticket.

### Décision selon l’impact

| Impact | Statut | Gravité | Action |
|---|---|---|---|
| Le ticket ne peut pas être terminé | BLOQUÉ PAR DOCUMENTATION | S1 | créer un ticket `DOC-FT-*` prioritaire |
| Le ticket est terminé avec contournement lourd | VALIDÉ AVEC FRICTION | S2 | corriger la documentation avant conversion tutoriel |
| Le ticket est terminé avec ambiguïté mineure | VALIDÉ AVEC FRICTION | S3 | backlog documentation ou correction simple |
| Suggestion d’exemple ou précision | VALIDÉ | S4 | amélioration documentation |
| Hors sujet documentaire | HORS PÉRIMÈTRE | S5 | classer hors périmètre |

### Nommage du ticket documentaire

```text
DOC-FT-XX-NOM-DU-TICKET-001
```

Exemple :

```text
DOC-FT-04-FORGE-DB-CONFIG-001
```

### Validation minimale d’un ticket documentaire

```bash
mkdocs build --strict
git diff --check
```

## 5. Transformation en tickets correctifs

Un ticket correctif doit rester séparé du ticket terrain.

Format conseillé :

```text
FIX-FT-XX-NOM-001
DOC-FT-XX-NOM-001
UX-FT-XX-NOM-001
SEC-FT-XX-NOM-001
```

Règle :

- un ticket correctif = une responsabilité ;
- pas de refonte globale masquée ;
- tests ajoutés si bug reproductible ;
- documentation mise à jour si comportement clarifié ;
- validation complète selon le type de correction.

## 6. Validation des corrections issues du terrain

Pour un correctif code :

```bash
pytest
python -m compileall -q .
mkdocs build --strict
git diff --check
```

Pour un correctif documentation uniquement :

```bash
mkdocs build --strict
git diff --check
```

Pour un correctif CLI/générateur :

```bash
pytest
python -m compileall -q .
mkdocs build --strict
git diff --check
```

## 7. Conversion documentaire des tickets validés

Après validation d’un ticket FT, le référent doit décider si le ticket devient un tutoriel.

| Décision | Signification |
|---|---|
| Convertir | Le ticket est validé, utile au parcours utilisateur, et suffisamment stable |
| Convertir partiellement | Seule une partie du ticket est utile en documentation |
| Ne pas convertir | Le ticket est purement interne, diagnostic, triage ou sécurité destructive |
| Reporter | Le ticket est utile mais attend une correction ou une clarification |

### Conditions minimales de conversion

- ticket validé ou validé avec friction mineure ;
- aucune erreur bloquante ouverte ;
- procédure reproductible ;
- documentation associée corrigée si nécessaire ;
- exemples décorrélés conservés ou adaptés ;
- parties internes retirées ;
- page ajoutée dans `docs/tutorials/` ;
- menu MkDocs mis à jour ;
- `mkdocs build --strict` validé.

### Nommage conseillé

```text
docs/tutorials/01-installer-forge.md
docs/tutorials/02-configurer-environnement.md
docs/tutorials/03-configurer-mariadb.md
```

## 8. Critères de release candidate terrain

Forge peut passer en release candidate terrain si :

- tous les tickets FT critiques d’installation sont validés ;
- au moins un parcours MariaDB est validé sans root applicatif ;
- premier projet validé ;
- route/contrôleur/template validés ;
- Jinja/Tailwind/HTMX/Alpine testés selon périmètre ;
- CLI de base validée ;
- entité, SQL, migration et CRUD simple validés ;
- aucun S0/S1 ouvert ;
- les S2 restants sont documentés ou acceptés.

## 9. Critères de sortie de bêta

Forge peut sortir de bêta uniquement si :

- installation reproductible sur les environnements principaux ;
- documentation de démarrage validée par testeurs non experts ;
- MariaDB et `.env` documentés et testés ;
- projet minimal, mini-projet guidé et projet autonome réalisés ;
- générateurs non destructifs vérifiés ;
- sécurité de base vérifiée ;
- déploiement serveur testé ;
- maintenance et mise à jour testées ;
- aucun S0/S1 ouvert ;
- S2 corrigés, documentés ou explicitement acceptés ;
- les bugs terrain corrigés ont été couverts par tests automatisés quand c’est possible.

## 10. Décision finale possible

### Décision A, Stable possible

Conditions :

- aucun S0/S1 ;
- S2 maîtrisés ;
- mini-projet et projet autonome réussis ;
- documentation suffisante ;
- déploiement validé.

### Décision B, Bêta prolongée

Conditions :

- usage possible ;
- frictions fortes encore nombreuses ;
- documentation à renforcer ;
- certains parcours encore trop dépendants du référent Forge.

### Décision C, Consolidation ciblée

Conditions :

- bloquants techniques ;
- incohérences architecture ;
- génération destructive ;
- auth/session fragile ;
- sécurité insuffisante ;
- déploiement non reproductible.

### Décision D, Refus de stable

Conditions :

- échec installation ;
- usage réel impossible ;
- projet autonome non réalisable ;
- retours S0/S1 nombreux ou non traités.
