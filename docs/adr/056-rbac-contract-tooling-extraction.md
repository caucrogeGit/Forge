# ADR-056 : Extraction du contrat et de l'outillage RBAC vers forge-mvc-rbac

## Statut

Proposé, Forge 1.0.0-rc (ticket `ADR-RBAC-SCHEMA-EXTRACT-001`).
Décision de périmètre cœur/opt-in ; relève du mainteneur.

---

## Date

2026-06-29

---

## Contexte

RBAC est un opt-in (`forge-mvc-rbac`).
Pourtant, son contrat et son outillage vivent encore dans le cœur :

- `cli/schemas/rbac.schema.json` (et sa copie source `schemas/rbac.schema.json`)
  portent le JSON Schema du fichier `mvc/security/rbac.json` ;
- `cli/security/rbac_validate.py` et `cli/security/rbac_audit.py` fournissent les
  commandes `rbac:validate` et `rbac:audit` ;
- `forge.schema.index.json` liste `rbac` parmi les schémas du cœur.

Le couplage est même inversé : le paquet opt-in `forge-mvc-rbac`
(`forge_mvc_rbac/contract.py`) **lit le schéma depuis le cœur**
(`Path(cli.__file__).parent / "schemas"`).
L'opt-in dépend donc du cœur pour valider son propre contrat.

Cela contredit le principe 8 (noyau minimal, briques opt-in) et le principe 10
(une API publique est un contrat de complétude : l'opt-in doit fournir son
contrat complet, schéma et validation compris).
Un projet sans RBAC embarque aujourd'hui le schéma et les commandes RBAC sans
les utiliser.

L'analyse du graphe des schémas confirme que `rbac.schema.json` est **autonome** :
aucun autre schéma ne le référence, et il ne référence aucun autre schéma.
Contrairement à `pivot.schema.json` (référencé par `relations.schema.json` du
cœur), il est donc détachable sans redesign de contrat.

L'ADR-014 a fixé l'**emplacement du contrat** dans un projet
(`mvc/security/rbac.json`, séparé du schéma d'entité).
Le présent ADR fixe l'**emplacement du schéma et de l'outillage** de validation.

---

## Décision

### Le contrat RBAC et son outillage rejoignent l'opt-in

1. **Schéma** : `rbac.schema.json` est déplacé dans `forge-mvc-rbac` (donnée de
   paquet, embarquée et packagée avec l'opt-in). Il est retiré de
   `cli/schemas/`, de `schemas/` (racine) et de `forge.schema.index.json`.
   Son `$id` (`https://forge-mvc.dev/schemas/rbac.schema.json`) reste inchangé :
   c'est une identité, pas un chemin.

2. **Validation** : `forge_mvc_rbac.contract` charge le schéma depuis **son
   propre paquet**, plus depuis le cœur.

3. **Commandes** : `rbac:validate` et `rbac:audit` deviennent des commandes de
   l'opt-in `forge-mvc-rbac` (précédent établi : `mail:*`, `iot:*`, `deploy:*`,
   `admin:*` sont fournis par leurs opt-ins). Elles sont retirées du cœur.

4. **Cœur** : le cœur ne contient plus aucun artefact RBAC (ni schéma, ni
   commande, ni entrée d'index).

### Conséquence d'usage

Utiliser `rbac:validate` / `rbac:audit` suppose `forge-mvc-rbac` installé, ce qui
est cohérent : ce sont des commandes de l'opt-in RBAC.
Sans l'opt-in, le cœur ne propose ni ne mentionne ces commandes.

---

## Conséquences

Le cœur perd le schéma RBAC, les deux commandes et l'entrée d'index : périmètre
réduit, conforme aux principes 8 et 10.
`forge-mvc-rbac` devient autoporteur : il embarque son schéma, le charge
lui-même et expose sa validation.
La doc embarquée de l'opt-in (ADR-038) accueille la référence du schéma et des
commandes.

Blast radius de l'implémentation (ticket distinct) : déplacer le fichier schéma ;
déplacer `rbac_validate.py` / `rbac_audit.py` ; recâbler `contract.py` sur le
schéma local ; retirer `rbac` de `forge.schema.index.json` et des deux dossiers
`schemas/` ; mettre à jour le dispatch et l'aide du cœur ; déplacer/adapter les
tests (`test_rbac_schema_contract`, `test_rbac_validate_command`, garde
`test_schemas_identiques`) ; mettre à jour la guidance et la documentation.

---

## Alternatives écartées

**Laisser le schéma et l'outillage RBAC dans le cœur.**
Maintient un opt-in dont le contrat vit dans le cœur, contre les principes 8 et
10, et impose à tout projet le poids du RBAC inutilisé.

**Déplacer le schéma mais garder les commandes dans le cœur.**
Le cœur devrait alors lire un schéma absent (il a quitté le cœur) ou en garder
une copie : incohérent. Schéma et validation forment un tout, ils migrent
ensemble.

---

## Charte appliquée

- Principe 4 (périmètre du cœur) : le RBAC quitte entièrement le cœur.
- Principe 8 (noyau minimal, briques opt-in) : l'opt-in porte son contrat.
- Principe 10 (contrat de complétude) : `forge-mvc-rbac` fournit schéma +
  validation + commandes, pas une moitié.
- Règle A (retirer la cause) : on supprime le couplage inversé opt-in vers cœur.

---

## Référence

- [ADR-014](014-rbac-contract-location.md) : emplacement du contrat RBAC dans un projet.
- [ADR-038](038-optin-docs-embedded-per-package.md) : doc des opt-ins embarquée par paquet.
- [ADR-052](052-optin-strategy.md) : stratégie et critères des opt-ins.
- `cli/security/rbac_validate.py`, `cli/security/rbac_audit.py` : outillage à déplacer.
- `forge-mvc-rbac/forge_mvc_rbac/contract.py` : validation à recâbler sur le schéma local.
