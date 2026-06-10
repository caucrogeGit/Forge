# Les listes

**Objectif** : énumérer les principes de Forge et les prérequis d'installation.

**Ce que vous allez apprendre :** les listes à puces, les listes numérotées (extension `sane_lists`) et les listes de tâches (extension `tasklist`).

Votre page présente Forge.

Nous ajoutons deux sections : ses principes, puis les prérequis à cocher.

## Listes à puces

Une puce commence par `-` suivi d'une espace ; l'indentation crée des sous-listes.

~~~md
- Explicite
- Minimal
    - Noyau réduit
    - Modules opt-in
- Testable
~~~

Rendu :

- Explicite
- Minimal
    - Noyau réduit
    - Modules opt-in
- Testable

## Listes numérotées

Les numéros réels importent peu : Markdown renumérote.
L'extension `sane_lists` évite qu'une liste démarre par accident.

~~~md
1. Installer Python 3.12
2. Installer Forge
3. Créer un projet
~~~

Rendu :

1. Installer Python 3.12
2. Installer Forge
3. Créer un projet

## Listes de tâches

L'extension `tasklist` ajoute des cases à cocher.

~~~md
- [x] Python 3.12 installé
- [ ] Forge installé
- [ ] Base MariaDB prête
~~~

Rendu :

- [x] Python 3.12 installé
- [ ] Forge installé
- [ ] Base MariaDB prête

## Ajoutez à votre page

Ajoutez ces deux sections à `prise-en-main.md` :

~~~md
## Principes

- **Explicite** : le SQL reste visible.
- **Minimal** : un noyau réduit, des modules opt-in.
- **Testable** : on teste avant d'élargir.

## Prérequis

- [ ] Python 3.12 ou plus
- [ ] Une base MariaDB
- [ ] Le gestionnaire de paquets `pip`
~~~

## À retenir

- Puces avec `-`, sous-listes par indentation.
- Listes numérotées avec `1.`, `2.`… ; Markdown renumérote.
- Cases à cocher avec `- [ ]` et `- [x]` grâce à `tasklist`.

[Continuer avec Citations et séparateurs](citations-et-separations.md)
