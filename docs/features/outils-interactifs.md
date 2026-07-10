# Outils interactifs

Cette page décrit la façon officielle de construire des **outils interactifs** dans une application Forge.
On appelle « outil » une petite fonction autonome offerte à l'utilisateur : un calculateur, un convertisseur, un simulateur, un visualiseur.
Ce genre d'outil se prête bien à un **bac à sable** pédagogique, mobilisable depuis un parcours d'apprentissage ou une section dédiée du projet.

Forge n'ajoute aucune machinerie pour cela : les briques nécessaires existent déjà (SSR, service statique, CSP).
Cette page pose le motif, pas un nouveau générateur.

## Deux familles d'outils

Un outil tombe dans l'une de deux familles, selon qu'il a besoin ou non de JavaScript côté navigateur.

| Famille | Exemples | Rendu Forge |
|---|---|---|
| **Calcul pur, sans état** | calcul de sous-réseau, loi d'Ohm, code couleur des résistances, encodage base64, générateur de mot de passe, description d'une expression cron | **SSR pur** : formulaire, POST, calcul Python, rendu Jinja. Zéro JavaScript. |
| **Temps réel, animé** | oscilloscope, simulateur de liaison série, curseurs en direct, jeu de réflexes, LED clignotante | **SSR + JavaScript local** servi depuis `'self'`, un module par outil. |

Environ la moitié des outils courants sont de purs calculateurs : ils tombent naturellement dans le modèle Forge sans la moindre dérogation.
Commencez toujours par vous demander si l'outil peut se contenter du SSR pur.

## Famille 1 : outil SSR pur

C'est le motif idiomatique de Forge, et le plus sûr.
L'outil est un **service Python testable** appelé par un contrôleur, dont le résultat est rendu par une vue Jinja.

Le flux est toujours le même :

1. une route `GET` affiche le formulaire de saisie ;
2. l'utilisateur soumet en `POST` (protégé par le jeton CSRF) ;
3. le contrôleur lit les champs avec `request.form(...)`, appelle un **service** pur ;
4. la vue rend le résultat.

Le cœur de l'outil est le service, une fonction Python sans dépendance HTTP, donc **testable en isolation** :

```python
# mvc/services/subnet.py
import ipaddress


def describe_subnet(cidr: str) -> dict[str, str]:
    """Décrit un sous-réseau IPv4 à partir d'une notation CIDR (ex. 192.168.1.10/24)."""
    network = ipaddress.ip_network(cidr, strict=False)
    hosts = list(network.hosts())
    return {
        "reseau": str(network.network_address),
        "masque": str(network.netmask),
        "diffusion": str(network.broadcast_address),
        "premier_hote": str(hosts[0]) if hosts else "-",
        "dernier_hote": str(hosts[-1]) if hosts else "-",
        "nb_hotes": str(network.num_addresses - 2 if network.num_addresses > 2 else 0),
    }
```

Le contrôleur ne fait que relier HTTP et service, la validation reste côté serveur.
Aucun rendu HTML n'est construit à la main : la vue Jinja échappe automatiquement les valeurs, ce qui écarte tout risque d'injection.

Un tel outil se génère souvent à partir des commandes existantes : voir `forge make:public-form` et `forge make:public-page` dans [Front et CSS](front.md).
Le parcours [welcome-outils](../starters/welcome-outils/index.md) construit un calculateur de sous-réseau complet, pas à pas.

## Famille 2 : outil temps réel avec JavaScript local

Certains outils (animation, curseurs en direct, canvas) demandent du JavaScript côté navigateur.
Forge l'autorise, à une condition stricte : le JavaScript est **local**, servi depuis l'application, jamais depuis un CDN.

La CSP de Forge est `script-src 'self'` par défaut (voir [Le nonce CSP](../core-security/csp.md)).
Un fichier `.js` **externe** servi depuis `static/js/` est donc autorisé **sans nonce** : `'self'` couvre déjà les scripts de même origine.
Le nonce ne sert qu'aux scripts **inline**, que ce motif évite précisément.

Le motif recommandé :

1. écrire la logique dans un module local, un fichier par outil, sous `static/js/` ;
2. le charger dans la vue via le bloc `{% block scripts %}` (voir [Front et CSS](front.md)) ;
3. passer les données du serveur au script **sans script inline**, par des attributs `data-*` sur un élément, ou un bloc `<script type="application/json">` (ce type n'est pas exécutable, la CSP ne le bloque pas).

```html
{% block content %}
<div id="oscilloscope"
     data-frequence="{{ frequence }}"
     data-amplitude="{{ amplitude }}">
    <canvas width="600" height="200"></canvas>
</div>
{% endblock %}

{% block scripts %}
    <script src="/static/js/oscilloscope.js" defer></script>
{% endblock %}
```

```javascript
// static/js/oscilloscope.js
const racine = document.getElementById("oscilloscope");
const frequence = Number(racine.dataset.frequence);
const amplitude = Number(racine.dataset.amplitude);
// ... dessin sur le canvas, aucune donnée injectée en HTML brut ...
```

Le script lit ses paramètres dans le DOM, jamais dans du HTML généré dynamiquement côté client.
Le parcours [welcome-outils](../starters/welcome-outils/index.md) construit un oscilloscope de démonstration selon ce motif.

## Contraintes de sécurité (non négociables)

Ces règles valent pour tout outil, quelle que soit sa famille.

- **CSP stricte conservée** : `script-src 'self'`, plus un `'nonce-...'` seulement si un script inline est réellement nécessaire (`APP_CSP_NONCE_ENABLED`).
  Jamais `unsafe-inline`, jamais `unsafe-eval`.
- **Aucun CDN** : ni script, ni feuille de style, ni police, ni image depuis un hôte externe.
  Tout ce dont l'outil a besoin est servi depuis `static/`.
- **CSRF sur les formulaires** : tout `POST` porte le champ caché `csrf_token`.
- **Pas de HTML non assaini** : on ne rend jamais du HTML externe ou saisi par l'utilisateur sans échappement.
  Jinja échappe par défaut ; n'utilisez `| safe` que sur du contenu que vous produisez vous-même et maîtrisez entièrement.
- **La base reste la vérité** : un outil sans état n'a pas à persister quoi que ce soit.

## Anti-patterns à ne pas reproduire

Les SPA pédagogiques générées par IA (React, Vue) offrent souvent de bons outils, mais une architecture **incompatible** avec Forge.
Ne reprenez pas leur build : inspirez-vous des outils, réécrivez-les selon le motif ci-dessus.

- **Framework front en CDN** (Tailwind, React depuis un `importmap` externe) : viole `script-src 'self'`, casse la CSP.
- **`dangerouslySetInnerHTML` ou équivalent** sur du contenu externe (flux RSS, réponse d'API tierce) : surface d'injection XSS.
- **Client-only** avec toute la logique en JavaScript : à l'opposé du service Python testable de Forge.
- **`unsafe-inline` « pour aller vite »** : ouvre la CSP globalement, à proscrire.

Le bon réflexe : un calcul en Python testable, un rendu Jinja échappé, et du JavaScript local et minimal seulement quand l'interactivité l'exige.

## Où placer un bac à sable d'outils

Un ensemble d'outils peut vivre dans une section autonome du projet, par exemple sous une route `/sandbox`, avec un contrôleur et des vues dédiés.
C'est le point de départ le plus simple : il n'impacte ni le modèle d'entités, ni la CSP.

Rattacher ensuite un outil à une activité pédagogique (une entité d'apprentissage du projet) relève d'une décision propre à l'application, pas du framework.
Forge fournit le motif de rendu et les garanties de sécurité ; l'organisation métier reste à la charge du projet.

## Voir aussi

- [Front et CSS](front.md) : dossier `static/js/`, bloc `{% block scripts %}`, layouts, composants Jinja.
- [Le nonce CSP](../core-security/csp.md) : politique CSP et nonce par requête.
- [welcome-outils](../starters/welcome-outils/index.md) : parcours qui construit un outil SSR pur et un outil JavaScript-live.
