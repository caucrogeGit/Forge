# Le rendu de gabarits mail dans Forge

Ce document décrit `MailTemplateRenderer`, qui produit un message à partir de gabarits Jinja2.

Le fichier de code correspondant est `forge_mvc_mail/templates.py`.

## 1. À quoi sert ce module ?

Écrire le corps d'un email à la main dans le code est pénible.
Le `MailTemplateRenderer` rend un jeu de gabarits Jinja2 (sujet, corps texte, corps HTML) en un `MailMessage` prêt à envoyer.

## 2. Rendre un message

```python
from forge_mvc_mail import MailTemplateRenderer

renderer = MailTemplateRenderer(template_dir="mvc/templates/mail")
msg = renderer.render("welcome", context={"name": "Alice"}, to="alice@example.org")
```

`MailTemplateRenderer(template_dir=None)` utilise le dossier de gabarits mail du projet à défaut.
Le rendu produit un `MailMessage` (sujet + corps), qu'on passe ensuite au [`Mailer`](mailer.md).

## 3. Les erreurs

Un gabarit absent, illisible ou produisant une erreur de rendu lève `MailTemplateError`.

## 4. Contextes d'utilisation

- **Emails transactionnels** : un dossier de gabarits par type de message (bienvenue, réinitialisation…).
- **Séparation** : le rendu (ici) et l'envoi ([mailer](mailer.md)) restent distincts.

## 5. Voir aussi

- [Le message mail](message.md) : le résultat du rendu.
- [Le mailer](mailer.md) : envoie le message rendu.
- [Vue d'ensemble Mail](../reference.md).
