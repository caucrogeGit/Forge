# FAQ Forge

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page regroupe les questions fréquentes retirées de la landing page. La landing reste une vitrine courte ; la FAQ appartient à la documentation.

---

## Que génère `forge make:crud` ?

`forge make:crud` génère le squelette MVC nécessaire pour administrer une entité :

- un contrôleur ;
- un modèle applicatif ;
- un formulaire ;
- les vues Jinja2 `index`, `show` et `form` ;
- les indications de routes à ajouter dans `mvc/routes.py`.

Le code généré reste lisible et modifiable. Forge ne cherche pas à cacher le fonctionnement du CRUD.

---

## Pourquoi les routes ne sont-elles pas injectées automatiquement partout ?

Parce que les routes sont une décision applicative. Forge peut générer ou afficher le bloc prêt à intégrer, mais le développeur doit garder la main sur l'organisation de `mvc/routes.py`.

Cette règle évite les injections silencieuses et rend la structure du projet plus facile à auditer.

---

## Que signifie “fichier généré” et “fichier préservé” ?

Forge sépare les fichiers régénérables des fichiers humains.

Exemples de fichiers régénérables :

```text
*_base.py
*.sql
vues CRUD générées
```

Exemples de fichiers à préserver :

```text
mvc/entities/contact/contact.py
mvc/models/contact_model.py si modifié manuellement
fichiers applicatifs propres au projet
```

L'objectif est simple : accélérer la génération sans écraser brutalement le code métier.

---

## Pourquoi utiliser `--dry-run` ?

`--dry-run` permet de vérifier ce que Forge ferait avant d'écrire sur le disque.

Exemple :

```bash
forge build:model --dry-run
```

C'est utile lorsque le JSON d'entité évolue, lorsque plusieurs entités changent ou lorsqu'on veut vérifier qu'une régénération ne touchera pas un fichier sensible.

---

## Pourquoi Forge ne fournit-il pas un ORM complet ?

Forge garde volontairement le SQL visible.

Le but n'est pas de masquer la base derrière une couche opaque, mais de produire des fichiers SQL lisibles, des requêtes compréhensibles et une architecture que le développeur peut reprendre.

Un ORM complet n'est pas impossible à long terme, mais ce n'est pas une priorité du core actuel.

---

## Comment gérer des fichiers uploadés ?

Forge fournit une brique média générique.

Initialisation :

```bash
forge upload:init
```

Utilisation côté contrôleur :

```python
save_upload(file, category="documents")
save_image(file, category="images")
```

Forge applique des garde-fous : extensions autorisées, taille maximale, validation MIME lorsque disponible, noms sûrs et protection contre le path traversal.

---

## Comment préparer le déploiement ?

Forge fournit des commandes d'aide au déploiement :

```bash
forge deploy:init
forge deploy:check
```

`forge deploy:init` prépare des fichiers de configuration pour Nginx et systemd.

`forge deploy:check` vérifie les éléments importants avant la mise en production : environnement, variables, chemins, modules et configuration attendue.

Forge ne modifie pas automatiquement le serveur de production. Le développeur garde la main.

---

## Forge remplace-t-il Django, Symfony ou Laravel ?

Non.

Forge n'est pas un clone des grands frameworks. Il vise une autre approche :

- moins de magie ;
- plus de fichiers visibles ;
- SQL compréhensible ;
- génération contrôlée ;
- lisibilité et auditabilité de bout en bout ;
- séparation stricte entre framework et application métier.

---

## Les starters sont-ils le cœur de Forge ?

Non.

Les starters sont des démonstrateurs. Ils servent à prouver que Forge peut générer des applications concrètes, mais ils ne doivent pas dicter le cœur du framework.

Le core reste générique. Les applications métier restent dans les projets, starters ou modules.

---

## Forge fournit-il déjà une authentification complète ?

Forge fournit déjà des briques de sécurité, de session et de RBAC. Les starters peuvent démontrer une authentification applicative.

En revanche, la brique Auth/User avancée générique — table `users` optionnelle, login/logout standardisé, reset password, vérification email, MFA, OIDC — appartient à la phase suivante de la roadmap.

Il ne faut donc pas présenter cette brique comme déjà livrée dans le core stable actuel.
