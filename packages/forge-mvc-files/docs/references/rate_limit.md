# Le rate-limit d'upload dans Forge

Ce document explique comment `forge_mvc_files` limite la fréquence des uploads par adresse IP.

Le fichier de code correspondant est `forge_mvc_files/rate_limit.py`.

## 1. À quoi sert ce module ?

Sans limite, un client pourrait inonder le serveur d'uploads.
Le rate-limit compte les tentatives d'upload par IP sur une **fenêtre glissante** et bloque au-delà d'un seuil.

Il fonctionne en **mémoire**, sur le même modèle que le rate-limit de connexion du cœur ; les compteurs d'upload sont **isolés** de ceux de la connexion.

## 2. L'API

| Fonction | Rôle |
|---|---|
| `is_upload_rate_limited(ip)` | `True` si l'IP a atteint la limite sur la fenêtre courante |
| `record_upload_attempt(ip)` | enregistre une tentative d'upload pour cette IP |

## 3. Usage dans un contrôleur

```python
from forge_mvc_files import is_upload_rate_limited, record_upload_attempt

def upload_avatar(request):
    if is_upload_rate_limited(request.ip):
        return Response.json({"error": "too_many_uploads"}, status=429)
    record_upload_attempt(request.ip)
    saved = save_upload(request.file("avatar"))
    ...
```

L'ordre est important : on **vérifie** avant de traiter, puis on **enregistre** la tentative.

## 4. Limites connues

Le compteur est **en mémoire processus** : il est perdu au redémarrage et n'est pas partagé entre plusieurs workers.
C'est cohérent avec le modèle mono-processus de Forge (voir la politique de sécurité) ; un déploiement multi-worker exigerait un backend partagé.

## 5. Contextes d'utilisation

- **Route d'upload** : garde en tête de contrôleur, avant `save_upload`.
- **Tests** : les compteurs sont vidés entre tests par l'infrastructure de test partagée.

## 6. Voir aussi

- [L'upload générique](manager.md) : ce que l'on protège.
- [Les primitives de stockage](storage.md).
