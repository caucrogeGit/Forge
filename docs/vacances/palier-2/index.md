<!--
PAGE TEMPORAIRE - support de cours, sans aucune relation avec le framework Forge.
A SUPPRIMER le 2026-06-28 (voir docs/vacances/welcome-vacance.md).
-->

# Palier 2 - Installer deux machines virtuelles avec VirtualBox

[Welcome Vacance](../welcome-vacance.md) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

!!! warning "Page temporaire, sans lien avec Forge"
    Support provisoire pour la classe de seconde TNE CIEL, retiré le 28 juin 2026.

## Partie 1 - Dossier technique

Objectif : comprendre ce qu'est une machine virtuelle, différencier machine hôte et machine invitée, et installer deux systèmes dans VirtualBox : Windows 11 et une distribution Linux.

| Section | Contenu |
|---|---|
| 1. Machine physique | Ordinateur réel sous Debian 13 |
| 2. Système hôte | Debian 13, le système qui exécute VirtualBox |
| 3. Machine virtuelle | Ordinateur simulé dans VirtualBox |
| 4. Système invité | Windows 11 ou Linux installé dans la VM |
| 5. Ressources d'une VM | RAM, CPU, disque virtuel, carte réseau virtuelle |
| 6. Image ISO | Fichier d'installation du système |
| 7. Disque virtuel | Fichier qui contient le système de la VM |
| 8. Snapshot | Point de retour en cas d'erreur |
| 9. Installation Windows 11 | Création de la VM, ISO, disque, démarrage, installation |
| 10. Installation Linux | Même logique avec une distribution Linux |
| 11. Bonnes pratiques | Nommer les VM proprement, ne pas donner trop de RAM, éteindre proprement |

Noms recommandés des VM :

| VM | Nom |
|---|---|
| Windows 11 | 2TNE-WIN11-NOM |
| Linux | 2TNE-LINUX-NOM |

Réglages proposés :

| Élément | Windows 11 | Linux |
|---|---|---|
| RAM | 4 Go si possible | 2 Go |
| CPU | 2 cœurs | 1 ou 2 cœurs |
| Disque | 64 Go | 20 à 30 Go |
| Réseau au départ | NAT | NAT |

À retenir : la VM utilise des ressources de la machine physique.
Si on donne trop de RAM ou trop de CPU à la VM, Debian 13 peut ralentir.

## Partie 2 - Activité : créer deux machines virtuelles, Windows 11 et Linux

Étapes :

1. Ouvrir VirtualBox.
2. Créer la VM Windows 11.
3. Choisir le nom correct.
4. Associer l'image ISO Windows 11.
5. Régler RAM, CPU et disque.
6. Lancer l'installation.
7. Arrêter proprement la VM.
8. Créer un snapshot nommé « Installation propre ».
9. Créer la VM Linux.
10. Associer l'image ISO Linux.
11. Régler RAM, CPU et disque.
12. Lancer l'installation.
13. Arrêter proprement la VM.
14. Créer un snapshot nommé « Installation propre ».
15. Compléter une fiche d'inventaire des VM.

Livrables :

* VM Windows 11 créée ;
* VM Linux créée ;
* un snapshot présent sur chaque VM ;
* tableau de configuration rempli.

Tableau à remplir :

| Élément | VM Windows 11 | VM Linux |
|---|---|---|
| Nom de la VM | | |
| RAM attribuée | | |
| Nombre de CPU | | |
| Taille du disque | | |
| ISO utilisée | | |
| Snapshot créé | oui / non | oui / non |
