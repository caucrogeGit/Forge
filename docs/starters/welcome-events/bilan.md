# Bilan : ce que vous avez gagné, ce que vous avez perdu

Vous avez construit un registre d'événements complet, en une centaine de lignes, et vous l'avez cassé assez de fois pour savoir ce qu'il coûte.

## État final de mvc/events/

    mvc/events/ ├── __init__.py # API publique : emit, subscribe, listeners_for ├── _registry.py # le mécanisme : un dict, une boucle for ├── wiring.py # LA liste des abonnements, à la main └── listeners/ └── user.py # les réactions à l'inscription

## Le bilan honnête

| Vous avez gagné | Vous avez perdu |
|---|---|
| Le contrôleur d'inscription ne connaît plus les réactions | Lire le contrôleur ne suffit plus pour savoir ce qui se passe |
| Ajouter une réaction ne touche plus le contrôleur | Il faut ouvrir `wiring.py` en plus, à chaque fois |
| Chaque écouteur est testable seul | La charge utile est un dictionnaire libre, vérifié par rien |
| Les réactions sont regroupées par domaine | L'ordre d'exécution est devenu implicite |
| Un point d'extension unique et nommé | Une faute de frappe dans un nom est silencieuse |

Aucune colonne n'est vide, et c'est le résultat le plus important de ce parcours.

## Quand ce patron vaut son prix

Le rapport penche en sa faveur quand **plusieurs réactions indépendantes** suivent un même fait métier, que ces réactions **changent souvent**, et qu'elles appartiennent à des **domaines différents** (courriel, statistiques, notification).
Trois réactions qui bougent tous les mois : oui.

Il ne le vaut pas quand une seule réaction suit le fait, quand les réactions ne changent jamais, ou quand elles doivent s'exécuter dans un ordre précis.
Dans ce dernier cas, une fonction nommée `after_registration()` qui appelle les trois services à la suite est **meilleure** : elle est explicite, ordonnée, typée, et elle se lit d'un coup.

Le piège classique consiste à installer le mécanisme pour un seul événement, « parce qu'on en aura d'autres ».
La verbosité arrive tout de suite, le bénéfice peut-être jamais.

## Pourquoi Forge ne le fournit pas

Vous êtes maintenant en position de comprendre la décision, et de la contester si vous le souhaitez.

L'[ADR-052](../../adr/052-optin-strategy.md) classe `events` hors trajectoire 1.x sous sa forme habituelle, le bus à découverte automatique par décorateur, au motif qu'il viole le principe 3 (refuser la magie cachée) et le principe 11 (une seule façon officielle).
Le même ADR juge recevable la forme que vous venez d'écrire : « registre câblé dans un fichier visible, `emit` manuel ».

La raison de fond est celle du palier sur le câblage.
Un framework qui fournit le bus fournit aussi, inévitablement, la découverte automatique qui le rend agréable, et c'est elle qui casse la propriété centrale de Forge : pouvoir lire le code et savoir ce qu'il fait.

L'autre raison est plus prosaïque.
Publier ce mécanisme reviendrait à s'engager pour de bon sur les questions du palier précédent : que fait-on d'un écouteur qui lève, l'ordre est-il garanti, peut-on se désabonner, que fait-on des cycles.
Ces réponses ne se trouvent pas au tableau : elles se trouvent dans l'usage.
Vous venez d'en faire l'expérience ; vous êtes donc mieux placé qu'un mainteneur pour trancher, **pour votre application**.

## À retenir

- Un système d'événements tient en un dictionnaire et une boucle ; sa difficulté est entièrement dans les politiques qui l'entourent.
- Le fichier de câblage explicite est ce qui sépare un mécanisme auditable d'un mécanisme magique.
- Le patron se paie en lisibilité locale : ne l'installez que là où plusieurs réactions changeantes le justifient.
- Les événements découplent le code, `forge-mvc-jobs` découple le temps.

Ce code est le vôtre.
Étendez-le, réduisez-le, ou supprimez-le si vos trois appels alignés se portaient très bien.
C'est aussi une conclusion valable.

## Voir aussi

- [Événements](../../features/evenements.md) : le guide de référence, qui résume la position de Forge sans passer par ce parcours.
- [ADR-052](../../adr/052-optin-strategy.md) : les critères d'admission des opt-ins et le classement de `events`.
- [forge-mvc-jobs](../../jobs/reference.md) : la file de tâches, pour le découplage temporel.
