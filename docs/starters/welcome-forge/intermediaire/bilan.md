# Bilan — niveau intermédiaire

Récapitulatif des compétences acquises au **niveau intermédiaire** du starter
*Bonjour Forge*. Ce niveau fait passer des opérations unitaires (niveau
débutant) à une petite application pilotée par les données.

## Ce que vous avez validé

| Palier | Compétence acquise |
|--------|--------------------|
| 1 — [Lister des enregistrements](list-records.md) | Lire **plusieurs** lignes avec `fetch_all` et les itérer dans une vue (`{% for %}`). |
| 2 — [Rechercher / filtrer](filter-list.md) | Filtrer une liste avec `request.param` + `WHERE … LIKE ?` paramétré. |
| 3 — [Paginer une liste](pagination.md) | `LIMIT ? OFFSET ?` + `COUNT(*)`, liens précédent/suivant. |
| 4 — [Héritage de gabarit](layout-template.md) | Factoriser l'enveloppe HTML avec `{% extends %}` + `{% block %}`. |
| 5 — [Modifier un enregistrement](update-record.md) | Formulaire pré-rempli + `UPDATE … WHERE id = ?` (POST + CSRF). |

*(Le niveau intermédiaire s'enrichira des paliers suivants : suppression,
sessions, messages flash.)*

## Et ensuite

Le **niveau avancé** arrivera prochainement. En attendant, le récapitulatif
rassemble toutes les API de la progression sur une seule page et vous oriente
vers les starters autonomes (à commencer par le CRUD complet).

[Récapitulatif de la progression](../recapitulatif.md)
