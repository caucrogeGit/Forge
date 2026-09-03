# ADR-095 : Héritage entre rôles RBAC

## Statut

Acceptée.
Amende l'[ADR-014](014-rbac-contract-location.md), dont le contrat associait un rôle à une liste plate de permissions.
Ne révise ni l'[ADR-056](056-rbac-contract-tooling-extraction.md) ni le principe 8 : le RBAC reste un opt-in, et le cœur ignore toujours cette hiérarchie.

## Date

2026-09-03

## Contexte

Le contrat `mvc/security/rbac.json` associe chaque rôle à une liste de codes de permission.

Un projet ordinaire décline trois rôles au moins, `lecteur`, `editeur` et `admin`, chacun reprenant les droits du précédent et en ajoutant.
La liste du lecteur est donc recopiée dans l'éditeur, et les deux dans l'admin.

Trois copies de la même règle.

Elles divergent au premier ajout : on ajoute une permission à l'éditeur, on oublie l'admin, et l'administrateur se retrouve avec **moins** de droits qu'un éditeur.

Le défaut est silencieux.
Personne n'écrit un test vérifiant qu'un administrateur peut faire tout ce qu'un éditeur peut faire, et l'écran qui manque ne se découvre que le jour où un administrateur en a besoin.

Ce ticket figurait au lot 5 du cycle rc8, celui des demandes en tension avec la charte.
La tension nommée était que l'ADR-014 assume cette limite, et que la rouvrir élargit le contrat public.

## Décision

**Le contrat RBAC accepte une déclaration d'héritage entre rôles, `role_inherits`.**

### 1. La forme

```json
{
  "schema_version": "1.0",
  "roles": {
    "lecteur": ["article.list"],
    "editeur": ["article.create"],
    "admin":   ["article.destroy"]
  },
  "role_inherits": {
    "admin":   ["editeur"],
    "editeur": ["lecteur"]
  }
}
```

Un administrateur porte alors les trois permissions.

La clé est **facultative**.
Un contrat qui ne la déclare pas se comporte exactement comme avant, et aucun projet existant n'a de geste à faire.

### 2. L'héritage est déclaré, jamais deviné

Forge ne déduit aucune hiérarchie d'un nom de rôle.

« admin » ne domine pas « editeur » parce qu'il s'appelle ainsi, et supposer le contraire accorderait des droits que personne n'a écrits.
C'est le principe 3, et il vaut ici plus qu'ailleurs : une déduction fausse sur un contrôle d'accès ne se répare pas après coup.

### 3. Un cycle est refusé

`admin` héritant d'`editeur` héritant d'`admin` ne décrit aucun ordre.

La résolution ne pourrait que boucler ou s'arrêter arbitrairement, et un arrêt arbitraire donnerait des permissions différentes selon l'ordre de lecture du fichier JSON.

Le cycle est **nommé** dans le message, « admin puis editeur puis admin » : un cycle qu'on peut lire se corrige, « hiérarchie invalide » ne se corrige pas.

### 4. Un rôle hérité inconnu est refusé

`"admin": ["editur"]`, faute de frappe, n'accorderait rien du tout.

L'administrateur perdrait ses droits en silence, et la cause serait introuvable dans un fichier de cinquante lignes.

### 5. Une hiérarchie fautive n'accorde rien

`get_contract_permissions` rend un ensemble **vide** quand la hiérarchie est fautive, plutôt que les permissions directes en ignorant l'héritage.

Accorder les droits directs donnerait un contrôle d'accès dégradé sans que rien ne le signale, et un contrôle qui se dégrade en silence est pire qu'un contrôle qui refuse.
`forge rbac:validate` nomme la faute.

### 6. La profondeur est bornée

Dix niveaux.

Au delà, l'héritage n'est plus un modèle de droits mais un enchevêtrement que personne ne relit, et une revue de sécurité qui ne peut pas suivre la chaîne ne vérifie rien.

## Conséquences

### Positives

La règle est écrite une fois.
Ajouter une permission à l'éditeur la donne à l'administrateur, sans geste et sans oubli possible.

`forge rbac:export` rend la hiérarchie visible, ce qui est précisément ce qu'une revue de sécurité vient chercher.

Le contrat gagne une notion que l'ADR-014 citait déjà comme relevant d'un contrat RBAC : « rôles, politiques multi-entités, héritages de permissions ».
La limite levée ici était une limite d'implémentation, non une frontière de conception.

### Coûts et ruptures

Le contrat public s'élargit d'une clé.
`rbac.schema.json` la déclare, et le refuser demanderait désormais une release majeure.

La résolution d'un rôle coûte un parcours de graphe au lieu d'une lecture de table.
Le coût est négligeable à l'échelle d'une dizaine de rôles, et le graphe est borné à dix niveaux.

Aucune rupture : un contrat sans `role_inherits` se résout comme avant, à l'identique.

## Alternatives écartées

**Laisser l'application aplatir sa hiérarchie avant d'écrire le contrat.**
C'est la position de l'ADR-014, et elle est tenable.
Elle laisse chaque projet écrire son aplatisseur, et le contrat cesse alors de dire la règle : il dit son résultat, que plus personne ne peut relire.

**Déduire la hiérarchie d'un ordre déclaré, une liste de rôles du moins au plus puissant.**
Plus compact, et faux dès qu'un projet a deux branches, un `comptable` et un `editeur` qui ne se dominent pas.
Un ordre total impose une hiérarchie que le métier n'a pas.

**Une profondeur illimitée.**
Rien ne casserait techniquement, le cycle étant déjà refusé.
Mais une chaîne de quinze rôles n'est plus vérifiable par un humain, et un modèle de droits qu'on ne peut pas relire ne protège personne.

## Références

- [ADR-014](014-rbac-contract-location.md), emplacement du contrat RBAC, amendé ici.
- [ADR-056](056-rbac-contract-tooling-extraction.md), extraction du contrat et de l'outillage vers l'opt-in.
- [Roadmap des opt-ins rc8](../roadmap/forge-rc8-optins-roadmap.md), lot 5.
