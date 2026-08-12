# ADR-091 : Le cœur émet les événements d'authentification

## Statut

Acceptée.
Décision de comportement du cœur ; relève du mainteneur.
**Complète l'ADR-008 sans le réviser** : celui-ci décide du destinataire, celui-ci décide de l'émetteur.

## Date

2026-08-12

## Contexte

Un retour terrain relève que la table `auth_audit_log` d'une application Forge en usage quotidien depuis des semaines contient **zéro ligne**, et propose que le cœur l'alimente.

La proposition ne peut pas être retenue telle quelle, et il faut le dire avant tout le reste.

### Ce que l'ADR-008 a déjà tranché

L'ADR-008 fournit trois briques sans les assembler : le contrat d'événement, l'émission vers le logger Python `forge.auth.audit`, et une table SQL qu'il qualifie lui-même de **latente**.

Il écrit explicitement que Forge ne décide pas du destinataire, « fichier, base, Sentry, Kafka », et que la persistance est applicative.
Il anticipe même la confusion constatée : « un développeur découvrant la table SQL `auth_audit_log` sans documentation pouvait croire que Forge la remplissait automatiquement ».

**Une table d'audit vide est donc le comportement décidé**, et le corriger demanderait de réviser l'ADR-008, ce que rien ici ne justifie : la rétention, la purge, l'indexation et la conformité restent des choix d'exploitation.

### Le défaut réel, qui est ailleurs

Le relevé contient pourtant un fait que l'ADR-008 ne couvre pas, et qui est un vrai manquement.

Le générateur qui produit le contrôleur d'authentification de toute application Forge n'appelle **jamais** `safe_log_auth_event`.
Aucun événement n'est donc émis, **pas même vers le logger**.

Forge annonce trois constantes, `login.success`, `login.failed` et `logout`, et n'en émet aucune.
Ce n'est pas la persistance qui manque, c'est la **brique 2 de l'ADR-008**, celle que le framework s'était engagé à fournir.

Une application qui configurerait consciencieusement un handler sur `forge.auth.audit`, comme l'ADR-008 le lui demande, ne recevrait rien.

## Décision

**Le cœur émet les trois événements d'authentification, au moment où il les connaît.**

### 1. L'émission appartient au cœur, pas au code engendré

Deux raisons, et la seconde est décisive.

Une émission écrite dans le code engendré peut être supprimée par mégarde, et rien ne le signalerait : c'est exactement ce que le relevé constate, une trace qu'on peut oublier d'écrire étant une trace qu'on oubliera.

Surtout, **`authenticate_user` est le seul endroit qui sait pourquoi une connexion échoue**.
Le contrôleur ne reçoit qu'un `None` : il ne peut distinguer un identifiant inconnu, un mot de passe faux, un compte désactivé, ni un loader applicatif qui a levé.
Émettre depuis le contrôleur produirait donc des lignes moins utiles, et c'est le cas d'échec qui intéresse une enquête.

### 2. Ce qui est émis, et ce qui ne l'est jamais

`login.success` porte l'identifiant du compte.
`login.failed` porte la raison, distinguant compte introuvable, compte désactivé et vérification en échec.
`logout` porte l'identifiant du compte quitté.

**Le mot de passe ne va jamais dans un événement**, ni en clair, ni haché, ni tronqué, et pas davantage la valeur saisie quand elle a échoué : une faute de frappe sur un mot de passe y ressemble trop.
La métadonnée étant libre, la règle est écrite ici et tenue par un test.

### 3. L'émission ne peut jamais faire échouer une connexion

Elle passe par `safe_log_auth_event`, qui avale l'exception, la journalise et incrémente un compteur.
Cette garantie existe déjà ; cet ADR l'étend aux appels neufs plutôt que de la refaire.

Une table saturée, un disque plein ou un verrou ne doivent jamais empêcher quelqu'un d'entrer.

### 4. Émettre une seule fois

Si le cœur émet et que le code engendré émet aussi, chaque connexion écrit deux lignes et tout comptage devient faux sans que rien ne le dise.
Le générateur n'émet donc pas, et un test **compte** les émissions au lieu de vérifier leur présence.

### 5. `last_login_at` est retirée

La colonne est créée par le cœur et **écrite par personne** depuis toujours.
Le relevé propose de l'écrire ou de la retirer ; c'est le retrait qui est choisi, pour trois raisons.

Le cœur n'écrit nulle part ailleurs dans `users`, et l'y faire entrer pour une seule colonne ferait du framework un écrivain de la table applicative.

C'est un horodatage géré, donc l'ADR-081 s'applique et son autorité serait Python, ce qui suppose un écrivain que le cœur n'a pas.

Enfin le journal d'audit répond déjà à « qui s'est connecté et quand », avec la raison en prime.
`last_login_at` en est une copie dénormalisée que personne n'a réclamée, et une colonne que le framework crée sans jamais l'alimenter est un mensonge de schéma.

## Conséquences

Une application qui configure un handler sur `forge.auth.audit`, comme l'ADR-008 le lui demande, reçoit enfin quelque chose.

La table `auth_audit_log` **reste latente**, et le retour terrain qui la voulait pleine trouvera dans l'ADR-008 le mode d'emploi pour la remplir en dix lignes.
Cet ADR ne change pas cet état, il en supprime la cause de confusion : jusqu'ici, aucune brique ne fonctionnait, si bien qu'on ne pouvait pas distinguer « Forge ne persiste pas » de « Forge n'émet rien ».

Le retrait de `last_login_at` est une rupture de schéma, sans rupture d'API publique.

## Alternatives écartées

**Le cœur écrit dans `auth_audit_log`.**
C'est la proposition du relevé. Écartée : elle révise l'ADR-008, qui a examiné la question et rangé la persistance du côté applicatif, avec ses corollaires de rétention et de conformité.

**Le code engendré émet.**
Écartée au point 1 : le contrôleur ne connaît pas la raison de l'échec, et l'émission y est supprimable en silence.

**Écrire `last_login_at` à la connexion réussie.**
Écartée au point 5. Elle ferait du cœur un écrivain de `users`, ce qu'il n'est nulle part, pour une information que le journal porte déjà mieux.

**Ne rien faire, la persistance étant applicative.**
C'est confondre les deux briques. La persistance est applicative, l'émission ne l'est pas : l'ADR-008 la donne comme fournie par Forge, et elle ne l'était pas.

## Référence

- ADR-008 : les trois briques, et la persistance applicative.
- ADR-081 : Python seule autorité sur les horodatages gérés, qui condamne `last_login_at` sans écrivain.
- `safe_log_auth_event` : la garantie que l'audit ne bloque jamais une vérification de sécurité.
