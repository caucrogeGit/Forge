# Bilan — niveau avancé

Récapitulatif des compétences acquises au **niveau avancé** du starter
*Bonjour Forge*. Ce niveau sort du CRUD pur pour aborder les préoccupations
d'une vraie application : données reliées, fichiers, emails, API et écritures
atomiques.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 — [Relations entre tables](relations.md) | Relier deux tables par une clé étrangère et les lire avec un `JOIN` SQL visible. |
| 2 — [Téléverser un fichier](file-upload.md) | Recevoir un fichier (`multipart`), le récupérer avec `request.file` et le stocker via `save_upload` (validé). |
| 3 — [Envoyer un email](send-email.md) | Composer un `MailMessage` et l'envoyer via `Mailer` sur un transport (`ConsoleTransport` en dev). |
| 4 — [API JSON protégée](json-api.md) | Renvoyer du JSON (`Response.json`) derrière un jeton `Authorization: Bearer …` lu avec `request.header`. |

Vous savez maintenant relier vos données sans ORM, recevoir des fichiers,
envoyer des emails et exposer une API JSON protégée, le SQL restant explicite.

## Et ensuite

Le **récapitulatif** rassemble toutes les API de la progression sur une seule
page et vous oriente vers les starters autonomes (à commencer par le CRUD
complet).

[Récapitulatif de la progression](../recapitulatif.md)
