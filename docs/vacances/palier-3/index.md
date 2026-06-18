<!--
PAGE TEMPORAIRE - support de cours, sans aucune relation avec le framework Forge.
A SUPPRIMER le 2026-06-28 (voir docs/vacances/welcome-vacance.md).
-->

# Palier 3 - Tester les modes réseau VirtualBox

[Welcome Vacance](../welcome-vacance.md) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

!!! warning "Page temporaire, sans lien avec Forge"
    Support provisoire pour la classe de seconde TNE CIEL, retiré le 28 juin 2026.

## Partie 1 - Dossier technique

Objectif : comprendre que VirtualBox propose plusieurs modes réseau, puis tester la communication entre la machine hôte Debian 13, la VM Windows 11 et la VM Linux.

| Section | Contenu |
|---|---|
| 1. Carte réseau réelle | Carte réseau de la machine Debian 13 |
| 2. Carte réseau virtuelle | Carte réseau simulée dans la VM |
| 3. Adresse IP | Identifiant logique d'une machine |
| 4. Commande ip a | Voir l'adresse IP sous Linux et Debian |
| 5. Commande ipconfig | Voir l'adresse IP sous Windows |
| 6. Commande ping | Tester si une machine répond |
| 7. Mode NAT | La VM accède au réseau via l'hôte, simple pour Internet |
| 8. Mode pont (bridge) | La VM apparaît comme une machine du réseau local |
| 9. Réseau interne | Les VM communiquent entre elles, isolées du réseau réel |
| 10. Host-only | Communication entre l'hôte et la VM |
| 11. Méthode de diagnostic | Vérifier le mode réseau, l'IP, le ping, le pare-feu éventuel |

Comparaison des modes réseau :

| Mode réseau | VM vers Internet | VM vers hôte | VM vers autre VM | Visible sur le LAN |
|---|---|---|---|---|
| NAT | Oui | Limité | Non directement | Non |
| Accès par pont | Oui si LAN OK | Oui | Oui si même réseau | Oui |
| Réseau interne | Non | Non | Oui | Non |
| Host-only | Non sauf configuration spéciale | Oui | Oui | Non |

Commandes utiles sous Linux et Debian :

```bash
ip a
ip route
ping adresse_ip
```

Commandes utiles sous Windows :

```text
ipconfig
ping adresse_ip
```

Arrêter un ping : `Ctrl + C`.

## Partie 2 - Activité : tester les communications entre hôte Debian 13, VM Windows 11 et VM Linux

### Étape 1 - Relever les adresses IP

| Machine | Commande | Adresse IP |
|---|---|---|
| Hôte Debian 13 | ip a | |
| VM Linux | ip a | |
| VM Windows 11 | ipconfig | |

### Étape 2 - Tester le mode NAT

Mettre les deux VM en NAT.

| Test | Résultat attendu | Résultat observé |
|---|---|---|
| VM Linux vers Internet | fonctionne si réseau OK | |
| VM Windows vers Internet | fonctionne si réseau OK | |
| VM Linux vers VM Windows | ne fonctionne pas directement | |
| VM vers hôte | variable selon la configuration | |

### Étape 3 - Tester le mode réseau interne

Mettre les deux VM sur le même réseau interne, par exemple `reseau-2tne`.

Attribuer des adresses IP simples :

| Machine | Adresse IP | Masque |
|---|---|---|
| VM Linux | 192.168.10.10 | 255.255.255.0 |
| VM Windows 11 | 192.168.10.20 | 255.255.255.0 |

| Test | Commande | Résultat |
|---|---|---|
| Linux vers Windows | ping 192.168.10.20 | |
| Windows vers Linux | ping 192.168.10.10 | |

Conclusion attendue : en réseau interne, les deux VM peuvent communiquer entre elles mais ne sont pas connectées au réseau réel.

### Étape 4 - Tester le mode accès par pont

Mettre une VM en accès par pont.
Relever son adresse IP.
Comparer avec l'adresse IP de l'hôte Debian 13.

Questions :

1. La VM reçoit-elle une adresse du même réseau que l'hôte ?
2. La VM peut-elle faire un ping vers la passerelle ?
3. La VM peut-elle accéder à Internet ?
4. La VM est-elle visible comme une machine du réseau local ?

Conclusion attendue : en mode pont, la VM se comporte comme une machine réelle connectée au réseau local.

### Étape 5 - Tester le mode host-only si disponible

Mettre la VM en host-only.

| Test | Résultat |
|---|---|
| Hôte Debian vers VM | |
| VM vers hôte Debian | |
| VM vers Internet | |

Conclusion attendue : en host-only, la VM communique avec l'hôte, mais pas forcément avec Internet.

Livrables :

* tableau des adresses IP rempli ;
* tableau des tests ping rempli ;
* captures d'écran des modes réseau VirtualBox ;
* conclusion simple pour chaque mode.

---

!!! info "Ressources du palier 3"

    * [Dossier technique complet](palier-3-dossier-technique-reseau-virtualbox.md) : toutes les explications détaillées sur les modes réseau.
    * [QCM du palier 3](qcm-palier-3-reseau-virtualbox.md) : à valider à 100 % avant de réaliser l'activité.
    * [Activité du palier 3](activite-palier-3-reseau-virtualbox.md) : les manipulations à réaliser une fois le QCM validé.
