# ADR-090 : Empreinte de contrat dans les fichiers engendrés

## Statut

Acceptée.
Décision de format des fichiers livrés à l'utilisateur ; relève du mainteneur.
Ne touche pas la règle d'or du principe 9 : Forge ne réécrit toujours rien.

## Date

2026-08-11

## Contexte

Forge engendre du code puis ne le retouche plus.
C'est le principe 9, et il est juste : le code de l'utilisateur lui appartient.

Il a une conséquence que rien ne rattrape aujourd'hui.
**Corriger un générateur ne corrige aucune application déjà engendrée**, et son auteur ne l'apprend pas.

Le cycle en cours le démontre au lieu de le supposer.
`AUTH-CASE-ASYMMETRY-001` a corrigé un défaut qui fermait la connexion sur SQLite, et `AUTH-IDENTITY-CONTACT-001` a renommé la colonne d'identité.
Les deux vivent dans `cli/security/make_auth.py`.
La seule application Forge existante porte une copie du contrôleur d'avant, et **rien ne lui signalera** qu'elle doit la reprendre.

Ce que les générateurs produisent n'est pas anodin : authentification, réinitialisation de mot de passe, formulaires publics.
Un correctif de sécurité livré dans un générateur n'atteint donc jamais les applications livrées.

Le silence est le défaut.
Personne ne décide de ne pas corriger, on ignore simplement qu'il y a quelque chose à corriger.

Le motif existe pourtant déjà chez Forge.
`forge agents:init --check` signale qu'un fichier a divergé de sa référence, mais il ne s'applique qu'à `CLAUDE.md`, qui est de la documentation, et il compare le **contenu**.

## Décision

**Chaque fichier engendré porte l'empreinte du contrat de son générateur, et `forge doctor` la compare à celui de la version installée.**

### 1. L'empreinte porte un numéro de contrat, jamais un contenu

C'est le point qui décide de tout le reste.

Un fichier engendré est **fait pour être édité** : c'est l'intérêt du `write-if-new`.
Une empreinte du contenu serait donc fausse dès la première ligne ajoutée par l'auteur, l'avertissement deviendrait permanent, et un avertissement permanent est invisible.

C'est aussi pourquoi le motif de `agents:init --check`, qui compare le contenu, ne se généralise pas tel quel : il convient à un fichier de référence qu'on ne modifie pas, pas à du code applicatif.

### 2. Le numéro appartient au générateur, pas au framework

Un contrat monte quand la **sortie du générateur change de façon signifiante**, et à ce moment seulement.

Comparer à la version du framework ferait crier à chaque montée de version, y compris celles qui n'ont rien changé au générateur concerné.
On apprendrait à ignorer l'avertissement, ce qui est le seul résultat pire que de ne pas l'émettre.

Chaque générateur déclare donc trois choses :
son nom de commande, son numéro de contrat courant, et un registre disant ce qui a changé à chaque montée.

Le registre est le vrai travail de cet ADR.
Sans lui, l'avertissement dit « en retard » sans dire de quoi, et un avertissement qu'on ne sait pas traduire en geste se désapprend en trois semaines.

### 3. Ce que le contrôle dit, et ce qu'il ne dit pas

Contrat identique : **silence**.

Contrat inférieur : le fichier est nommé, chaque montée manquée est décrite, et celles qui touchent la sécurité sont signalées comme telles.

Empreinte absente : le contrôle **dit qu'il ne sait pas**, ce qui est vrai, et donne le geste.
Il n'accuse pas.
Toutes les applications antérieures à cet ADR sont dans ce cas, et un fichier dont l'auteur a effacé l'en-tête aussi.

### 4. Rien n'est jamais réécrit

Le contrôle produit un avertissement, l'auteur décide.
`forge doctor` reste un diagnostic, il ne répare pas, conformément à ce qu'il fait déjà pour ses quinze autres contrôles.

### 5. Application progressive, dette listée

Douze modules écrivent du code utilisateur.
`make:auth` porte l'empreinte dès cet ADR, parce que c'est le générateur dont la sortie change dans la version en cours et celui dont les défauts ont la plus lourde conséquence.

Les autres sont inscrits en **dette listée**, avec un cliquet qui échoue dès qu'un module en sort.
Une exclusion muette rendrait le relevé rassurant et faux.

## Conséquences

Le format des fichiers engendrés change : une ligne de commentaire s'ajoute en tête.
Les applications existantes ne l'ont pas, et le contrôle le leur dira une fois.

`forge doctor` gagne un seizième contrôle.

Aucune API publique n'est touchée : le compteur des deux mois vers la 1.0.0 n'est pas affecté.

## Alternatives écartées

**Comparer le contenu, comme `agents:init --check`.**
Écartée pour la raison donnée au point 1 : un fichier fait pour être édité rendrait l'avertissement permanent.

**Comparer à la version du framework.**
Écartée au point 2 : crie à chaque montée, donc s'apprend à être ignorée.

**Réécrire les fichiers en retard, même sur demande explicite.**
Écartée. C'est le principe 9, et cet ADR ne l'entame pas.
Une commande de réécriture demanderait de fusionner les modifications de l'auteur avec la nouvelle sortie, ce qu'aucun générateur ne sait faire sans réviser le principe.

**Ne rien faire et documenter les ruptures dans le changelog.**
C'est l'état actuel, et il repose sur l'hypothèse que l'auteur d'une application lit chaque entrée de changelog de chaque version.
Le cycle en cours montre que non : le défaut de casse a traversé cinq préversions sans que personne le voie.

## Référence

- Principe 9 de la charte : pas d'écriture invisible dans le code utilisateur.
- `AUTH-CASE-ASYMMETRY-001` et `AUTH-IDENTITY-CONTACT-001` : les deux corrections qui n'atteindront pas les applications existantes.
- `forge agents:init --check` : le motif dont cet ADR s'écarte, et pourquoi.
