# ADR-094 : Un registre de fichiers dans `forge-mvc-files`

## Statut

Acceptée.
Amende l'[ADR-020](020-files-media-storage-primitives.md), dont le hors périmètre excluait tout état persistant du paquet.
Ne révise ni l'[ADR-019](019-upload-extraction.md) ni l'[ADR-004](004-core-perimeter.md) : le cœur reste sans fichiers.

## Date

2026-09-01

## Contexte

`forge-mvc-files` écrit des fichiers sur disque et les sert.
Il ne garde aucune trace de ce qu'il a écrit.

L'ADR-020 l'avait posé explicitement, en hors périmètre.

> files n'absorbe pas la validation de domaine (codecs/ffprobe), le transcodage, ni aucun état/BDD, cela reste propriété des opt-ins métier.

Cette exclusion visait une dérive réelle, et elle l'a empêchée.
Le paquet ne devait pas devenir une usine métier configurable, ce que le principe 8 refuse.

Une conséquence n'avait pas été mesurée.
Sans trace de ce qui a été écrit, quatre gestes deviennent impossibles à outiller.

- Compter ce qu'un utilisateur a déposé, donc lui appliquer un quota.
- Retrouver un fichier orphelin, c'est à dire présent sur disque et référencé par personne.
- Retrouver le nom d'origine d'un fichier, que le mode UUID efface du chemin par sécurité.
- Brancher une analyse antivirus sur un fichier identifié.

L'état existait pourtant déjà, ailleurs.
`forge-mvc-images` porte une table `media` avec le chemin, le nom d'origine, le type MIME, la taille et le propriétaire.

Rien n'y est propre à l'image.
Une application qui ne stocke que des documents PDF devrait donc installer `forge-mvc-images`, et Pillow avec lui, pour disposer d'une table.
Le couplage serait faux, et le nom `media` mentirait sur son contenu.

## Décision

**`forge-mvc-files` tient un registre des fichiers qu'il écrit, et devient un opt-in adossé à la base.**

### 1. Ce que le registre est

Une table par fichier écrit, portant ce que le stockage sait de lui.

Le chemin, le nom d'origine, le type MIME, la taille en octets, un propriétaire déclaré par l'application, et la date d'écriture.

### 2. Ce que le registre n'est pas

Il ne porte aucune notion métier.

Pas de rôle, pas de position, pas de texte alternatif, pas de lien vers une entité par son nom.
Ces colonnes existent dans la table `media` de `forge-mvc-images` parce qu'une galerie en a besoin, et elles y restent.

Le propriétaire est un couple libre, une nature et un identifiant, que l'application remplit comme elle l'entend.
`forge-mvc-files` ne sait pas ce qu'est un utilisateur, et ne cherche pas à le savoir.

### 3. L'enregistrement est explicite

Écrire un fichier n'enregistre rien de soi même.

L'application appelle l'enregistrement quand elle le veut, comme elle appelle déjà l'écriture.
Un opt-in qui écrirait en base à l'insu de son appelant serait de la magie cachée, que le principe 3 refuse.

Le paquet reste donc utilisable sans base, exactement comme aujourd'hui, pour qui ne veut que des primitives de stockage.

### 4. La table appartient au paquet

Elle est décrite une fois, rendue pour le backend installé, et livrée par `files:init` selon la convention de l'[ADR-071](071-optin-db-provisioning-convention.md).

### 5. Ce que l'ADR-020 conserve

Tout le reste de son hors périmètre tient.

`forge-mvc-files` n'absorbe ni la validation de domaine, ni le transcodage, ni aucune logique métier.
Il ne devient pas une usine configurable à options.

L'amendement porte sur un point, et un seul : un registre de ce que le stockage a écrit relève du stockage.

## Conséquences

### Positives

Les quatre gestes deviennent outillables, et ils sont demandés par le cycle rc8.

Une application qui stocke des documents n'a plus à installer un paquet d'images pour disposer d'une table.

Le nom d'origine survit au mode UUID, qui l'efface du chemin pour des raisons de sécurité.

### Coûts et ruptures

`forge-mvc-files` gagne une migration, et rejoint les opt-ins adossés à la base.
Un projet qui l'utilise déjà et veut le registre doit appliquer cette migration ; un projet qui n'en veut pas n'a rien à faire.

Deux tables décrivent désormais des fichiers, `media` pour les images et le registre pour le reste.
C'est un doublon partiel, assumé le temps de la série 1.x.

La convergence appartient à un ticket post-1.0, qui devra dire si `forge-mvc-images` se repointe sur le registre.
La forcer maintenant refondrait un paquet publié et utilisé, pour un gain qui n'est pas mesuré.

## Alternatives écartées

**Généraliser la table `media` de `forge-mvc-images`.**
Aucune duplication, aucun ADR, mais un projet qui ne stocke que des PDF tirerait Pillow pour une table.
Le couplage serait faux, et le nom mentirait.

**Un opt-in séparé pour le registre.**
La frontière serait nette, au prix d'un paquet de plus pour une table, et d'une composition à trois pour un geste simple.
Le principe 8 veut un noyau minimal, pas un paquet par table.

**Laisser l'application déclarer sa table.**
C'est la position de l'ADR-020, et elle reste tenable.
Elle laisse chaque application réécrire le même registre, et rend impossible tout outillage de quota ou de purge livré par Forge.

## Références

- [ADR-019](019-upload-extraction.md), extraction de l'upload générique.
- [ADR-020](020-files-media-storage-primitives.md), périmètre des primitives, amendé ici.
- [ADR-071](071-optin-db-provisioning-convention.md), convention de provisionnement des opt-ins BDD.
- [Roadmap des opt-ins rc8](../roadmap/forge-rc8-optins-roadmap.md), section 7.10.
