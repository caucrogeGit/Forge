# ADR-046 : Registre de loaders de templates Jinja pour les opt-ins

## Statut

Accepté, bêta publique 1.0 (`1.0.0-beta.x`).
Implémenté par `CORE-JINJA-OPTIN-LOADERS-001`.
Cadrage de l'intégration HTTP de Forge Admin (chantier `ADMIN-*`).

---

## Date

2026-06-24

---

## Contexte

Le moteur de rendu du cœur instancie un `Environment` Jinja avec un loader unique.

```python
# integrations/jinja2/renderer.py
self._env = Environment(loader=FileSystemLoader(views_dir), ...)
```

`views_dir` pointe sur `mvc/views/` du projet.
Un opt-in ne peut donc pas faire rendre un template qu'il embarque dans son paquet : un appel à `BaseController.render("admin/dashboard.html")` échoue si le fichier n'est pas sous `mvc/views/`.

Le cœur expose déjà un registre symétrique pour le **contexte** Jinja.

```python
# core/mvc/controller/registry.py
register_jinja_context_provider(fn)   # rbac, i18n s'enregistrent ainsi
iter_jinja_context_providers()
```

C'est le pattern « push » de la charte (principe 8) : l'opt-in se déclare lui-même, le cœur ne nomme aucun module opt-in.

Forge Admin (opt-in `forge-mvc-admin`) sera le premier opt-in à servir des pages HTML rendues côté serveur.
Il a besoin d'embarquer ses templates par défaut, tout en permettant au projet de les surcharger (ticket `ADMIN-TEMPLATE-OVERRIDE-001`).

Les autres pistes (templates copiés dans le projet par une commande, ou un `Environment` Jinja propre au paquet) ont été écartées : voir Alternatives.

---

## Décision

Ajouter au cœur un **registre de loaders de templates Jinja**, symétrique au registre de fournisseurs de contexte, et composer ces loaders avec un `ChoiceLoader`.

1. Dans `core/mvc/controller/registry.py` : `register_jinja_template_loader(loader)` et `iter_jinja_template_loaders()`.
2. Dans `integrations/jinja2/renderer.py` : le loader compose, dans cet ordre, `FileSystemLoader(views_dir)` du projet puis les loaders d'opt-in.

La composition est résolue **dynamiquement** : un petit loader maison relit `iter_jinja_template_loaders()` à chaque résolution de template, plutôt qu'un `ChoiceLoader` figé à la construction.
C'est nécessaire car le renderer du squelette est construit **avant** l'import des routes et des opt-ins ; un `ChoiceLoader` statique manquerait les loaders enregistrés ensuite.
La sémantique reste celle d'un `ChoiceLoader` (premier loader qui résout gagne), mais l'ordre d'import des paquets devient sans effet.

3. Un opt-in s'enregistre lui-même, en dégradation gracieuse si le cœur n'est pas présent.

```python
# forge_mvc_admin/__init__.py
try:
    from core.mvc.controller.registry import register_jinja_template_loader
    from jinja2 import PackageLoader
    register_jinja_template_loader(PackageLoader("forge_mvc_admin", "templates"))
except ImportError:
    pass
```

**Ordre des loaders** : `mvc/views/` du projet en premier, loaders des paquets ensuite.
Un template du projet (`mvc/views/admin/dashboard.html`) **masque** donc le template par défaut du paquet de même chemin logique.
C'est le mécanisme natif de surcharge de templates, sans configuration : il satisfait directement `ADMIN-TEMPLATE-OVERRIDE-001`.

Ce registre est une **infrastructure générale du cœur**, pas une fonctionnalité de Forge Admin.
Tout opt-in (présent ou futur) qui sert des pages peut s'en servir.

---

## Conséquences

Positives :

- un opt-in sert ses templates embarqués sans dupliquer le moteur de rendu ;
- les globals du cœur (`url_for`, `csrf_token`, `can`, `current_user`, `trans`) restent disponibles, une seule source de vérité ;
- la surcharge de template par le projet est native (ordre du `ChoiceLoader`), sans option ni magie ;
- le cœur ne nomme aucun opt-in : il itère un registre, comme pour le contexte.

Coûts et limites :

- petite modification du cœur (le renderer et le registre) : à couvrir par des tests de garde-fou ;
- un conflit de noms de templates entre deux paquets se résout par l'ordre d'enregistrement ; les opt-ins préfixent donc leurs templates par leur domaine (ex. `admin/…`) pour éviter les collisions ;
- le registre est un état de processus : il se peuple à l'import des paquets installés, jamais par découverte sur disque.

---

## Alternatives écartées

**Templates générés dans le projet (copie par `admin:init`).**
Aucun changement du cœur, mais pas de template par défaut de repli : un fichier manquant casse le rendu, les templates sont dupliqués par projet, et les améliorations du châssis ne profitent pas aux projets existants.
La surcharge perd son sens (tout est déjà un fichier du projet).

**Environnement Jinja propre au paquet.**
Aucun changement du cœur, mais le paquet recrée la plomberie : il faut réinjecter à la main `url_for`, `csrf_token`, `can`, `trans`.
Deux moteurs Jinja en parallèle, deux sources de vérité, risque de divergence avec le cœur et duplication de la sécurité.

---

## Liens

- Registre de contexte Jinja existant : `core/mvc/controller/registry.py` (pattern « push », principe 8).
- Découplage cœur / opt-ins : [ADR-042](042-doc-core-optins-decoupling.md).
- Cadrage et tickets : `docs/roadmap/forge-admin-roadmap.md`.
