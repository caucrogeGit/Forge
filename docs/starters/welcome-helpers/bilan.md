# Bilan : vos façades helper

Vous avez construit un jeu de façades de confort dans `mvc/helpers/`, toutes
bâties sur une base non instanciable, chacune centrée sur un concern.

## État final de mvc/helpers/

    mvc/helpers/
    ├── __init__.py     # ré-exporte Session, Cookies, Flash
    ├── _facade.py      # base : namespace non instanciable
    ├── session.py      # Session — le store + son cookie sécurisé
    ├── cookies.py      # Cookies — cookies applicatifs génériques
    └── flash.py        # Flash   — messages one-shot

## Quand utiliser quoi

| Besoin | À utiliser |
|---|---|
| Créer / lire / écrire une session | `Session.new` / `Session.get` / `Session.set` |
| Lire l'id de session depuis le cookie | `Session.current_id(request)` |
| Poser le cookie de session (sécurisé) | `Session.set_cookie(response, id)` |
| Lire / poser un cookie applicatif | `Cookies.get` / `Cookies.set` |
| Message flash, sans redirection | `Flash.set` / `Flash.get` |
| Message flash sur POST→redirect | `BaseController.redirect(..., flash="…")` (Forge) |

## Les frontières à garder en tête

- **Le noyau reste minimal et explicite.** Vos façades ne font que **regrouper**
  des briques du core ; elles ne contiennent **aucune logique** propre. La
  sécurité (durcissement `__Host-`, validation, CSRF) vit dans le core, jamais
  dans la façade.
- **Une façade = un concern.** Session (store), Cookies (cookies génériques),
  Flash (messages). Pas de classe fourre-tout.
- **C'est votre code.** Ces fichiers vous appartiennent : étendez-les selon vos
  besoins (nouvelle méthode, nouvelle façade). Forge ne les impose ni ne les
  réécrit.
- **Limite connue** : un seul `Set-Cookie` par réponse (cf. palier Cookies).

## À retenir

- L'ergonomie est la **responsabilité de l'application** : ces façades sont du
  sucre côté projet, le noyau Forge n'en porte aucune.
- Une base `Facade` commune évite de répéter le garde « non instanciable ».
- Déléguez toujours au core ; ne dupliquez pas sa logique.

Vous savez maintenant construire des façades de confort propres, sans alourdir le
noyau. Réappliquez le même patron pour tout autre regroupement utile à votre
projet.
