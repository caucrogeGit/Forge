# Starter Communes & Séjours

## Objectif du starter

!!! success "Démonstrateur avancé principal"
    Communes & Séjours est le démonstrateur avancé principal de Forge. Il montre comment combiner les briques modernes du framework — pages publiques, formulaire, mails, i18n, seed — sans intégrer de logique métier dans le cœur.

Communes & Séjours est le démonstrateur avancé principal de Forge.

Il montre Forge en situation réelle, sans être une application métier dans le cœur :

- pages publiques (accueil, liste, fiche) ;
- formulaire de demande avec validation serveur ;
- notifications mail (visiteur + propriétaire) ;
- textes i18n via le système de traduction Forge ;
- données fictives de démonstration ;
- structure métier réaliste : communes, propriétaires, hébergements, demandes de séjour.

**Le starter démontre Forge. Il ne transforme pas Forge en application métier spécialisée.**

## État actuel

Le starter est complet. Toutes les briques prévues pour la Phase 8 sont livrées.

Le démonstrateur est visible immédiatement après `forge starter:build 5`, sans base de données requise.

## Installation

### Prérequis

Un projet Forge existant créé avec `forge new`.

### Commandes

```bash
# Lister les starters disponibles
forge starter:list

# Aperçu sans écriture
forge starter:build 5 --dry-run

# Générer le starter dans un projet Forge
forge new CommunesSejours
cd CommunesSejours
forge starter:build 5
python app.py
```

Ouvrir : `http://localhost:8000/communes-sejours`

```bash
# Forcer la réinstallation
forge starter:build 5 --force
```

### Aliases

Le starter est accessible via les aliases suivants :

```bash
forge starter:build 5
forge starter:build communes-sejours
forge starter:build communes
```

### Base de données optionnelle

Le starter fonctionne sans base de données pour les pages publiques (données placeholder).

Pour générer le schéma SQL et travailler avec les entités :

```bash
forge check:model
forge build:model
forge db:init
forge db:apply
```

## Routes publiques

| Méthode | Route | Rôle |
|---|---|---|
| `GET` | `/communes-sejours` | Accueil du démonstrateur |
| `GET` | `/communes-sejours/hebergements` | Liste des hébergements |
| `GET` | `/communes-sejours/hebergements/{slug}` | Fiche d'un hébergement |
| `POST` | `/communes-sejours/hebergements/{slug}/demande` | Soumission du formulaire de demande |

Toutes les routes sont publiques (aucune authentification requise).

## Structure générée

Après `forge starter:build 5`, le projet contient :

```
mvc/
  controllers/
    communes_sejours_controller.py
  entities/
    commune/commune.json
    proprietaire/proprietaire.json
    hebergement/hebergement.json
    demande_sejour/demande_sejour.json
    relations.json
  forms/
    demande_sejour_form.py
  mail/templates/communes_sejours/
    demande_visiteur_subject.txt
    demande_visiteur_text.txt
    demande_proprietaire_subject.txt
    demande_proprietaire_text.txt
  views/public/communes_sejours/
    home.html
    hebergements_index.html
    hebergements_show.html
seed/
  communes.json
  proprietaires.json
  hebergements.json
  demandes_sejour.json
translations/
  fr.json
routes.py               (snippet injecté)
```

## Entités livrées

| Entité | Table | Rôle |
|---|---|---|
| `Commune` | `commune` | Commune ou collectivité présentée dans le démonstrateur |
| `Proprietaire` | `proprietaire` | Propriétaire ou gestionnaire d'un hébergement |
| `Hebergement` | `hebergement` | Hébergement publié, lié à une commune et un propriétaire |
| `DemandeSejour` | `demande_sejour` | Demande de séjour envoyée par un visiteur |

## Relations livrées

```text
Hebergement → Commune         (many_to_one, FK fk_hebergement_commune)
Hebergement → Proprietaire    (many_to_one, FK fk_hebergement_proprietaire)
DemandeSejour → Hebergement   (many_to_one, FK fk_demande_hebergement)
```

Les clés étrangères utilisent `ON DELETE SET NULL ON UPDATE CASCADE`.

## Médias

L'entité `Hebergement` déclare deux emplacements médias conformes aux conventions Forge :

| Nom | Rôle | Type | Variantes | Multiple |
|---|---|---|---|---|
| `cover` | `cover` | image | oui (`thumbnail`, `medium`) | non |
| `photos` | `gallery` | image | non | oui |

La déclaration suit le format standard `"media": [...]` de Forge.

Aucune image réelle n'est fournie dans ce starter. Les pages affichent un emplacement réservé.

## Pages publiques

Trois templates publics sont livrés dans `mvc/views/public/communes_sejours/` :

| Template | Route | Contenu |
|---|---|---|
| `home.html` | `GET /communes-sejours` | Accueil, lien vers la liste |
| `hebergements_index.html` | `GET /communes-sejours/hebergements` | Grille des hébergements |
| `hebergements_show.html` | `GET /communes-sejours/hebergements/{slug}` | Fiche + formulaire de demande |

Les pages utilisent :

- le layout `layouts/public.html` de Forge ;
- Tailwind CSS pour le style ;
- aucun JavaScript ni HTMX obligatoire ;
- la fonction `trans()` de Forge pour les textes visibles.

Les données sont des placeholders définis dans le contrôleur (`_HEBERGEMENTS`). Ils sont cohérents avec les données de démonstration fournies dans `seed/`.

## Formulaire de demande

Un formulaire public est intégré à la fiche hébergement (`hebergements_show.html`).

### Champs

| Champ | Type | Obligatoire |
|---|---|---|
| `nom` | Texte | oui |
| `email` | Email (validé) | oui |
| `telephone` | Texte | non |
| `date_arrivee` | Date (YYYY-MM-DD) | oui |
| `date_depart` | Date (YYYY-MM-DD) | oui |
| `nombre_personnes` | Entier ≥ 1 | oui |
| `message` | Texte long | non |

### Traitement

- Soumission invalide → réaffichage de la fiche avec les erreurs inline.
- Soumission valide → envoi des notifications mail → redirection avec message flash de confirmation.
- Protection CSRF intégrée.

**Une demande n'est pas une réservation confirmée.** Le visiteur sera contacté directement par le propriétaire ou gestionnaire.

## Notifications mail

Lors d'une soumission valide, deux mails sont envoyés via le système Forge Mail.

| Mail | Destinataire | Contenu |
|---|---|---|
| Confirmation visiteur | adresse email saisie | récapitulatif de la demande, note "non réservation" |
| Notification gestionnaire | `_GESTIONNAIRE_EMAIL` (constante) | coordonnées visiteur, dates, message, `Reply-To` visiteur |

### Templates

```
mvc/mail/templates/communes_sejours/
  demande_visiteur_subject.txt
  demande_visiteur_text.txt
  demande_proprietaire_subject.txt
  demande_proprietaire_text.txt
```

Les templates utilisent Jinja2. Variables disponibles : `nom`, `email`, `telephone`, `date_arrivee`, `date_depart`, `nombre_personnes`, `message`, `hebergement_titre`, `hebergement_commune`, `trans`.

### Logique d'envoi

La fonction `send_demande_sejour_notifications(hebergement, form_data, *, mailer=None, renderer=None)` est injectable pour les tests. En production, elle utilise `Mailer.from_config()` et `MailTemplateRenderer()`.

## Internationalisation

Les textes visibles du starter sont compatibles avec le système i18n Forge via `trans()`.

### Préfixe des clés

Le préfixe retenu est `starter.cs` (et non `starter.communes_sejours`, qui contient des termes interdits par la validation `i18n:check`).

### Clés fournies

Le catalogue `translations/fr.json` installé avec le starter contient 22 clés `starter.cs.*` :

| Préfixe | Portée |
|---|---|
| `starter.cs.title`, `starter.cs.subtitle` | Titre et sous-titre |
| `starter.cs.nav.*` | Liens de navigation |
| `starter.cs.listings.*` | Titre et état vide de la liste |
| `starter.cs.listing.*` | Labels de la fiche (adresse, capacité, contact, retour) |
| `starter.cs.form.*` | Labels et bouton du formulaire |
| `starter.cs.request.sent` | Message de confirmation après soumission |
| `starter.cs.mail.visitor.subject` | Sujet du mail visiteur |
| `starter.cs.mail.owner.subject` | Sujet du mail gestionnaire |

### Utilisation

```jinja2
{{ trans('starter.cs.title') }}
{{ trans('starter.cs.form.submit') }}
```

```python
from core.i18n import trans
trans("starter.cs.request.sent")  # message flash
```

### Limites

- Routes traduites non livrées.
- Traduction automatique non livrée.
- Traductions en base de données non livrées.
- Corps des mails non traduit via clés i18n (les sujets le sont).

## Données de démonstration

Des données fictives sont fournies dans `seed/` pour illustrer le modèle de données.

```
seed/
  communes.json          3 communes
  proprietaires.json     3 propriétaires
  hebergements.json      3 hébergements
  demandes_sejour.json   3 demandes (statuts : nouveau, en_cours, traite)
```

Ces données sont copiées dans le projet lors de `forge starter:build 5`. Elles sont **inspectables en JSON** mais **ne sont pas insérées automatiquement en base de données**.

| Fichier | Contenu |
|---|---|
| `communes.json` | Saint-Rémy-de-Provence, Apt, Saintes-Maries-de-la-Mer |
| `proprietaires.json` | Marie Dupont, Jean Martin, Sophie Blanc |
| `hebergements.json` | Mas des Cigales, Gîte du Luberon, Chambre d'hôtes Camargue |
| `demandes_sejour.json` | 3 demandes fictives liées aux hébergements |

Les slugs des hébergements sont alignés avec les données placeholder du contrôleur. Les emails utilisent le domaine `@example.test`.

## Ce qui n'est pas livré

Ce starter est un démonstrateur. Les fonctionnalités suivantes ne font pas partie de son périmètre :

- réservation confirmée ;
- paiement en ligne ;
- calendrier de disponibilités ;
- tarification ;
- comptes propriétaires et espace privé ;
- authentification spécifique au starter ;
- back-office métier (gestion des demandes, tableau de bord) ;
- workflow métier avancé (statuts automatisés, relances) ;
- dashboard statistiques ;
- images réelles ou galerie avancée ;
- insertion SQL automatique du seed ;
- déploiement spécifique ;
- Forge Design.

## Prochaines évolutions possibles

Ces évolutions sont hors périmètre de la Phase 8 mais envisageables dans des phases ultérieures :

- back-office minimal de gestion des demandes ;
- comptes propriétaires avec espace privé ;
- galerie photo publique alimentée par le système média Forge ;
- seed insérable via `forge db:seed` si une commande officielle est créée ;
- nouvelles langues (en.json, etc.) ;
- starter comme base de départ pour un vrai projet commercial.
