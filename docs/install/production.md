# Déploiement production

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page sert d'entrée vers les guides de déploiement production de Forge.
Le contenu détaillé reste dans les pages dédiées, ne pas dupliquer ici.

!!! warning "Outils de développement, pas de production"
    `python app.py` et `forge run` sont des outils de développement. En
    production publique, Forge se déploie obligatoirement derrière un
    serveur WSGI (Gunicorn) et un reverse proxy (Caddy ou Nginx).

## À lire dans l'ordre

1. [Déploiement WSGI minimal](../deployment/wsgi-deployment.md), architecture cible,
   `create_configured_wsgi_app()`, configuration Gunicorn de référence.
2. [Limites de production](../deployment/production-limits.md), ce que Forge ne fait
   pas et où poser des garde-fous applicatifs.
3. [Guide de déploiement](../deployment/deployment.md), pas-à-pas systemd, MariaDB,
   HTTPS, contrôles `forge deploy:check`.

## Voir aussi

- [Déploiement avancé](../deployment/deploy-advanced.md), scénarios étendus.
- [Sécurité en production](../deployment/production-security.md), durcissement et audit.
