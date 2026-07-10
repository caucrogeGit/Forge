# ADR-073 : namespace `app/` des vues applicatives

## Statut

Acceptée (2026-07-11).

## Contexte

Le dossier `mvc/views/` mélange à plat, au même niveau, deux natures de vues :

- les dossiers du **cadre** livrés par le squelette : `components`, `errors`,
  `home`, `layouts`, `pages`, `partials` (6 dossiers stables) ;
- les dossiers de **l'application**, un par entité, créés au fil du projet.

Le banc d'essai RéférenCiel (retour terrain 018, F41) le remonte à l'échelle : une
application d'une quarantaine d'entités affiche **43 dossiers à la racine** de
`mvc/views/`, sans séparation visible entre cadre et application. La racine devient
illisible à mesure que l'application grandit.

La cause est dans les générateurs : `forge make:crud` écrit **en dur** dans
`mvc/views/<snake>/`, et le contrôleur généré appelle `render("<snake>/…")`. Le
porteur ne peut pas regrouper ses vues d'application sans **diverger des
générateurs** (chaque `make:crud` suivant recréerait un dossier à la racine, et il
faudrait réécrire tous les `render(...)`), ce que la charte proscrit (« une seule
façon officielle », principe 11).

Trois faits cadrent la solution :

1. **`render()` résout un chemin explicite relatif à `mvc/views/`** (loader rooté
   sur `VIEWS_DIR`). Regrouper les vues **ne demande aucun changement de `render()`
   ni du loader** : il suffit que le chemin écrit et le chemin passé à `render()`
   partagent le même préfixe.
2. **Forge namespace déjà ses vues publiques** : `make:public-*` écrit sous
   `mvc/views/public/<plural>/`. Un namespace de vues n'est donc pas un motif neuf.
3. Le préfixe `<snake>` est dérivé d'une seule variable et réutilisé aux mêmes
   endroits : écriture des fichiers, `render("<snake>/…")` du contrôleur généré,
   `{% include "<snake>/…" %}` entre partials. Le changement est **localisé aux
   générateurs**.

## Décision

Les vues **de l'application** vivent sous un namespace dédié `mvc/views/app/`, par
convention, aux côtés des vues publiques (`mvc/views/public/`). Les 6 dossiers du
cadre restent à la racine de `mvc/views/`.

```
mvc/views/
├── components/  ┐
├── errors/      │
├── home/        │  cadre (squelette), racine
├── layouts/     │
├── pages/       │
├── partials/    ┘
├── public/      ← vues publiques (make:public-*, inchangé)
└── app/         ← vues de l'application (à la main OU make:crud)
    ├── eleve/
    └── professeur/
```

Le namespace `app/` désigne **les vues de l'application, écrites à la main ou
générées** : ce n'est pas un artefact de génération. Un débutant qui écrit ses vues
à la main les range sous `app/<snake>/` et son contrôleur appelle
`render("app/<snake>/index.html")` ; `make:crud` produit exactement la même chose.

### Réglage projet

Le namespace est un attribut de `config.py`, où vivent les réglages du projet :

```python
# config.py (squelette)
APP_VIEWS_NAMESPACE = os.getenv("APP_VIEWS_NAMESPACE", "app")
```

- **Défaut `"app"`** : un nouveau projet est rangé d'office (F41 résolu sans action).
- **`""` (vide)** : rétabli le **plat** historique (`mvc/views/<snake>/`), échappatoire
  de rétro-compatibilité pour un projet existant qui ne veut pas migrer.

`make:crud` lit ce namespace **au moment de la génération** via
`load_project_config()` (comme les commandes d'entités adossées à la base lisent
déjà la config, ADR-060), le fige dans les fichiers écrits et dans les `render(...)`
/ `{% include %}` générés. La lecture est **tolérante** : si `config.py` est absent
ou illisible, le générateur retombe sur le défaut `"app"`. `render()` ne lit jamais
ce réglage : les chemins générés (et écrits à la main) sont littéraux.

### Portée

- **`make:crud`** (vues d'entités) : namespacé sous `APP_VIEWS_NAMESPACE`.
- **`make:public-*`** : inchangé (déjà sous `public/`).
- **`make:auth`** (dossier `auth/`) : hors périmètre de cet ADR (un seul dossier,
  générateur distinct du cœur) ; pourra rejoindre `app/auth/` dans un suivi si le
  besoin se confirme.
- Le cadre (`components`, `errors`, `home`, `layouts`, `pages`, `partials`) reste à
  la racine.

## Conséquences

- La racine de `mvc/views/` ne porte plus, hors cadre, que `public/` et `app/` :
  lisible quelle que soit la taille de l'application.
- `render()` et le loader Jinja sont inchangés ; le changement est confiné aux
  générateurs (`make:crud`) et à un réglage de `config.py`.
- **Nouveau projet** : rangé sous `app/` par défaut.
- **Projet existant** (RéférenCiel et co.) : pour rester à plat, ajoute
  `APP_VIEWS_NAMESPACE = ""` à son `config.py` (une ligne, ajoutée à la main :
  `config.py` est un fichier utilisateur, jamais réécrit par Forge, principe 9).
  Sans cette ligne, le prochain `make:crud` écrit sous `app/` (les vues existantes
  restent où elles sont) ; le porteur choisit alors de migrer ou de poser `""`.
- Le défaut `"app"` est dupliqué en deux endroits (config.py du squelette et repli
  du générateur) : un garde-fou vérifie qu'ils coïncident.
- Rupture de défaut assumée en phase bêta (pré-1.0, pas d'alias) : les nouveaux
  projets changent de disposition, les projets existants disposent d'une échappatoire
  explicite.

## Alternatives écartées

- **Documenter le plat comme convention assumée.** Rejeté : à l'échelle réelle
  (positionnement « production auditable », ADR-049) la racine plate est
  effectivement illisible, et laisser le porteur diverger des générateurs est pire
  pour la charte qu'un namespace propre.
- **Namespace fixe non configurable** (comme `public/`). Rejeté : casserait tout
  projet existant sans échappatoire, or Forge **ne peut pas** réécrire
  automatiquement les `render(...)` des contrôleurs utilisateur (principe 9) ; la
  migration serait entièrement manuelle et sans issue de secours.
- **Flag par commande** (`make:crud <E> --views-dir <ns>`). Rejeté : répétitif,
  oubliable, et source d'incohérence dans un même projet (deux dispositions selon
  l'invocation) ; le réglage projet garantit une disposition unique.
- **Namespace `crud/`.** Rejeté : enferme dans la génération alors que les mêmes
  vues sont souvent écrites à la main (parcours pédagogique) ; `app/` décrit la
  **nature** (vues applicatives), pas leur origine.

## Charte appliquée

- Principe 11 (une seule façon officielle) : le défaut `app/` est la façon
  officielle ; `""` est une échappatoire de rétro-compat documentée, pas une seconde
  méthode encouragée.
- Principe 3 (refuser la magie cachée) : chemins littéraux, `render()` inchangé,
  namespace lu explicitement depuis `config.py`.
- Principe 9 (pas d'écriture invisible) : `config.py` n'est jamais réécrit ; le
  porteur pose lui-même `APP_VIEWS_NAMESPACE`.
- Relations : cohérent avec le namespace `public/` (make:public-*), lit `config.py`
  comme ADR-060, `render()` reste rooté sur `VIEWS_DIR`.

## Plan de tickets de suite

1. **VIEWS-NAMESPACE-CONFIG-001** : `config.py` du squelette gagne
   `APP_VIEWS_NAMESPACE` (défaut `"app"`) ; helper tolérant de lecture côté
   générateur d'entités.
2. **VIEWS-NAMESPACE-MAKECRUD-001** : `make:crud` honore le namespace (chemins
   d'écriture, `render(...)` et `{% include %}` générés), un seul préfixe dérivé.
3. **VIEWS-NAMESPACE-DOC-001** : page « où vivent les vues » (cadre / `public/` /
   `app/`), note de migration pour projets existants, alignement des parcours
   welcome qui écrivent des vues à la main.
4. **VIEWS-NAMESPACE-GUARDS-001** : garde-fous (vues générées sous `app/`,
   `render(...)` cohérents, plat préservé quand `""`, défaut config ↔ générateur).
