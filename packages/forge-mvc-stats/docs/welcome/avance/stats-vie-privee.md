# Avancé 5 : Compter sans ficher

Objectif : mesurer la fréquentation sans transformer une table de statistiques en fichier de données personnelles.

## Le geste naturel, et son coût

Pour compter des visiteurs uniques, le réflexe est d'écrire l'adresse IP dans les métadonnées.

```python
track_event("accueil", metadata={"ip": request.remote_addr})   # refusé
```

Forge refuse. Une adresse brute rangée sous une clé qui la nomme transforme la table en fichier de données personnelles, soumis à conservation limitée et à droit d'accès, sans que personne ne l'ait décidé.

## Deux réponses, selon le besoin

```python
from forge_mvc_stats import visitor_hash, anonymize_ip

empreinte = visitor_hash(request.remote_addr, secret=CLE, day=aujourdhui)
approx = anonymize_ip(request.remote_addr)
```

| Fonction | Ce qu'elle garde | Quand l'employer |
|---|---|---|
| `visitor_hash` | rien, un identifiant salé valable une journée | compter des visiteurs uniques |
| `anonymize_ip` | une adresse amputée de sa partie identifiante | granularité géographique approximative |

!!! danger "La troncature ne rend pas une donnée anonyme"
    Le résultat reste rattachable à un petit ensemble d'abonnés, et sur un réseau peu peuplé il désigne parfois une seule personne.

    Le module le dit plutôt que de laisser croire l'inverse : préférez l'empreinte, qui ne garde rien.

!!! info "L'empreinte tourne chaque jour"
    Deux visites du même visiteur le même jour donnent la même empreinte ; deux jours de suite, non.

    C'est ce qui permet de compter sans suivre.

!!! warning "Le refus porte sur le nom de la clé"
    `{"ip": ...}` est refusé ; `{"note": "vu depuis 203.0.113.42"}` ne l'est pas.

    Élargir à toute valeur ressemblant à une adresse refuserait un numéro de version comme `1.2.3.4` : une garde qui accuse à tort finit désactivée.

## À retenir

- Une adresse brute sous une clé qui la nomme est refusée à l'écriture.
- L'empreinte tournante compte sans rien garder ; la troncature garde peu.
- Le refus est fondé sur le nom de la clé, et le module le dit.

## Étape suivante

[Bilan du niveau avancé](bilan.md)
