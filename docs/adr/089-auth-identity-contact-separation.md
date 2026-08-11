# ADR-089 : Séparer l'identité du contact dans l'authentification

## Statut

Acceptée.
Décision de contrat public du cœur ; relève du mainteneur.
Touche le périmètre du cœur défini par l'ADR-004, l'authentification y vivant, et rompt l'API publique de `core.auth`.

## Date

2026-08-11

## Contexte

La table `users` du cœur n'a qu'une colonne d'identité, `email`.
La connexion la lit, la récupération de mot de passe cherche le compte par elle.
Une colonne, deux usages, et donc un effet de bord inévitable : poser son adresse, c'est changer son identifiant de connexion.

**Rien dans le cœur ne vérifie que cette colonne contient une adresse.**
`core/auth/user.py` n'exige qu'une chaîne non vide.
Une application y met donc légitimement autre chose, et c'est déjà le cas : la première application Forge y inscrit `2TNE1-01` pour ses élèves et `admin` pour son compte d'installation.

Le mécanisme est neutre. C'est le **vocabulaire** qui ne l'est pas, et il a fini par produire du comportement.

### Ce que le vocabulaire a produit

Deux divergences entre la CLI et le cœur, toutes deux nées du nom de la colonne.

**La casse**, corrigée par `AUTH-CASE-ASYMMETRY-001`.
Une fonction nommée `_normalize_email` abaissait la casse, parce qu'on normalise une adresse.
Le contrôleur engendré par `make:auth` ne le faisait pas.
Sur SQLite, où `TEXT` compare en binaire, un compte créé par la CLI ne pouvait pas se connecter dès que l'utilisateur tapait une majuscule.

**La forme**, que cet ADR tranche.
La CLI refuse tout argument sans `@` : `forge auth:user:show 2TNE1-01` ne cherche pas le compte, il **rejette la saisie**.
`auth:user:create` ne peut donc pas créer un compte dont l'identité n'est pas une adresse, alors que le cœur l'accepte sans réserve.
Les comptes de la première application n'ont pas pu être créés par la CLI : ils l'ont été par le code applicatif, ce qui a fait vivre les deux chemins séparément et laissé la divergence prospérer.

### Ce qu'une identité et un contact ne partagent pas

Une identité est stable, unique, choisie une fois, sans contrainte de forme, et sa casse lui appartient.
Un contact change au fil d'une carrière, peut être partagé entre deux comptes, et peut ne pas exister du tout — c'est le cas d'un élève mineur.

Une seule colonne ne peut pas porter les deux jeux de propriétés sans en trahir un.

## Décision

**Séparer les deux en deux colonnes, nommées pour ce qu'elles sont.**

### 1. `login` porte l'identité

Unique, obligatoire, sans contrainte de forme, **casse conservée**.
C'est ce que l'utilisateur saisit pour se connecter, et cela ne change jamais du fait d'une autre opération.

Le nom est tranché ici et non laissé au premier fichier écrit.
`username` promet un nom, ce que `2TNE1-01` n'est pas.
`identifier` se confond à la lecture avec la clé primaire `id`.
`login` dit exactement ce que la colonne sert à faire, et c'est le mot que porte déjà le formulaire engendré.

### 2. `email` porte le contact, et devient enfin ce que son nom annonce

**Facultative** : un compte sans adresse est un compte valide.
**Non unique** : deux comptes peuvent légitimement partager une adresse de dépannage.
**Normalisée en minuscules**, parce qu'une adresse l'est.

`email_verified_at` suit le contact et cesse de qualifier l'identité.

### 3. La récupération par courriel cherche le contact

Le cœur ne fait aucune recherche : `create_password_reset_request` reçoit un utilisateur déjà chargé.
La recherche appartient donc à l'application, et cet ADR ne la lui retire pas.

Il en fixe la **conséquence** : le contact n'étant pas unique, toute recherche par contact peut rendre plusieurs comptes.
Une application qui sert le premier trouvé se trompera un jour de compte.
`PasswordResetRequest.email` porte désormais le contact, et vaut `None` quand le compte n'en a pas — auquel cas la récupération par courriel n'est pas possible, et c'est voulu.

### 4. `last_login_at` reste sur la ligne d'utilisateur

Décidé, non subi.
Le journal d'audit a sa table et répond à une autre question, celle de la trace.
Cette colonne répond à un besoin d'affichage immédiat, et la déplacer imposerait une jointure à chaque page de compte pour un gain nul.

### 5. La CLI distingue les deux

`--login` désigne l'identité, `--email` le contact.
Le contrôle de forme `@` quitte l'identité et s'applique au contact, où il a un sens.

### 6. Aucune migration

La convention pré-1.0 de Forge autorise les ruptures sans alias déprécié ni guide de migration : il n'y a pas de code applicatif externe à protéger.
La seule application Forge existante est en bêta et sa base peut être reconstruite.

Cette décision est donc **prise avant le tag 1.0.0 précisément pour éviter la migration en trois temps** qu'elle imposerait après : colonne ajoutée, recopie conditionnelle, double vie, alias de compatibilité, renommage à la majeure suivante.
Chacune de ces étapes est une occasion de dérive, et l'alias en particulier est le genre de contournement qu'on ne reprend jamais.

## Conséquences

**Rupture d'API publique.**
`AuthUser.email` devient `AuthUser.login`, et un champ `email` facultatif apparaît.
Le compteur des deux mois sans changement d'API publique, condition de la bascule en 1.0.0, repart de la livraison.

Ce coût n'est pas imputable à cette décision : il l'est au défaut qu'elle corrige.
Un socle dont le champ d'identité est mal nommé, se comporte différemment selon le backend et refuse par la CLI ce que le cœur accepte, n'est pas taggable en 1.0.0.
La rendre visible ne la crée pas.

**Ce qui ne change pas.**
L'authentification à deux facteurs et le journal d'audit lisent l'identité, ils n'en changent pas la nature.
L'envoi du courriel appartient à l'opt-in de messagerie, et cet ADR ne poste rien.

## Alternatives écartées

**Accepter l'identifiant ou l'adresse à la connexion.**
L'unicité devrait alors valoir en croisé, sans quoi un compte pourrait prendre pour identifiant l'adresse d'un autre, et une saisie désignerait deux comptes.
L'ambiguïté remonterait ensuite partout, messages d'erreur, limitation de débit, journal d'authentification.
C'est un motif fréquent chez les services à millions de comptes, dont le besoin de récupération de masse n'est pas celui d'un établissement.

**Garder une colonne et n'en changer que la validation.**
C'était la solution la moins chère, et elle laissait le nom mentir.
Le défaut de casse est né exactement de là : une fonction a cru pouvoir normaliser une adresse parce que la colonne s'appelait `email`.
Le nom est la cause, pas le symptôme, et la règle A de la charte demande de retirer la cause.

**Rendre le contact unique.**
Séduisant, parce qu'il permettrait de chercher un compte par son adresse sans ambiguïté.
Écarté parce que deux professeurs d'un même établissement partagent légitimement une adresse de dépannage, et qu'une contrainte d'unicité le leur interdirait.

**Attendre la 1.0.0 stable.**
Coûterait la migration en trois temps, l'alias de compatibilité et une version majeure pour retirer ce qui n'a jamais eu lieu d'exister.
Le moment où ce schéma peut être remodelé librement est celui-ci, et il ne reviendra pas.

## Référence

- `AUTH-CASE-ASYMMETRY-001` : correctif de la casse, livré séparément, sans rupture d'API.
- ADR-003 : convention de langue, l'API publique en anglais.
- ADR-004 : périmètre du cœur, où vit l'authentification.
- ADR-084 : niveaux de support des backends, qui rendent SQLite exigible au même titre que MariaDB.
- `CHARTE_DOC.md`, règle A : retirer la cause, pas le symptôme.
