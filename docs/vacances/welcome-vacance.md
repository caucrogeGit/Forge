<!--
PAGE TEMPORAIRE - support de cours, sans aucune relation avec le framework Forge.
A SUPPRIMER le 2026-06-28 : retirer ce fichier ET son entree de nav dans mkdocs.yml.
Ne pas referencer cette page depuis d'autres pages de la documentation Forge.
-->

# Welcome Vacance - 2TNE CIEL

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

!!! warning "Page temporaire, sans lien avec Forge"
    Cette page est un support de cours provisoire pour la classe de seconde TNE CIEL.
    Elle n'a aucun rapport avec le framework Forge et sera retirée le 28 juin 2026.

Ce support contient trois paliers.
Chaque palier se compose de deux parties : un dossier technique à lire, puis une activité à réaliser qui s'appuie sur ce dossier.

## Vue d'ensemble

| Palier | Titre | Production attendue |
|---|---|---|
| 1 | Câble droit T568B | Un câble droit testé conforme |
| 2 | Installation de deux VM | Une VM Windows 11 et une VM Linux avec snapshot |
| 3 | Tests réseau VirtualBox | Un tableau comparatif des communications |

---

## Palier 1 - Fabriquer et tester un câble Ethernet droit T568B

### Partie 1 - Dossier technique

Objectif : comprendre à quoi sert un câble RJ45, comment il est constitué, pourquoi il faut respecter la norme T568B, et comment vérifier qu'un câble droit fonctionne.

| Section | Contenu |
|---|---|
| 1. Réseau local LAN | Plusieurs équipements qui échangent des informations |
| 2. Rôle du câble RJ45 | Liaison physique entre PC, switch, prise murale, routeur, imprimante |
| 3. Connexion physique et logique | Physique : câble, connecteur, carte réseau, switch. Logique : IP, masque, passerelle, DNS |
| 4. Structure du câble | 8 fils, 4 paires torsadées, gaine, connecteur RJ45 |
| 5. Fils torsadés | Réduction des perturbations électriques |
| 6. Norme T568B | Ordre des fils à connaître |
| 7. Câble droit | Même norme aux deux extrémités : T568B vers T568B |
| 8. Câble croisé | À connaître seulement par comparaison |
| 9. Matériel nécessaire | Câble, connecteurs RJ45, pince à dénuder, pince à sertir, testeur |
| 10. Testeur RJ45 | Résultat attendu : 1 vers 1, 2 vers 2, 3 vers 3, et ainsi de suite |
| 11. Erreurs fréquentes | Fils inversés, fils pas assez enfoncés, gaine hors connecteur, mauvais sertissage |

Ordre des fils en norme T568B :

| Broche | Couleur |
|---|---|
| 1 | Blanc / orange |
| 2 | Orange |
| 3 | Blanc / vert |
| 4 | Bleu |
| 5 | Blanc / bleu |
| 6 | Vert |
| 7 | Blanc / marron |
| 8 | Marron |

### Partie 2 - Activité : réaliser et tester un câble Ethernet droit en norme T568B

Étapes :

1. Identifier le matériel.
2. Couper le câble à la longueur demandée.
3. Dénuder proprement.
4. Ranger les fils en norme T568B.
5. Insérer les fils dans le connecteur RJ45.
6. Vérifier visuellement l'ordre.
7. Sertir le premier connecteur.
8. Refaire exactement la même norme à l'autre extrémité.
9. Tester le câble au testeur RJ45.
10. Compléter une fiche de résultat.

Livrables :

* câble droit terminé ;
* testeur RJ45 montrant 1 vers 1, 2 vers 2, 3 vers 3, 4 vers 4, 5 vers 5, 6 vers 6, 7 vers 7, 8 vers 8 ;
* tableau de contrôle rempli ;
* conclusion courte : câble conforme ou non conforme.

---

## Palier 2 - Installer deux machines virtuelles avec VirtualBox

### Partie 1 - Dossier technique

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

### Partie 2 - Activité : créer deux machines virtuelles, Windows 11 et Linux

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

---

## Palier 3 - Tester les modes réseau VirtualBox

### Partie 1 - Dossier technique

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

### Partie 2 - Activité : tester les communications entre hôte Debian 13, VM Windows 11 et VM Linux

#### Étape 1 - Relever les adresses IP

| Machine | Commande | Adresse IP |
|---|---|---|
| Hôte Debian 13 | ip a | |
| VM Linux | ip a | |
| VM Windows 11 | ipconfig | |

#### Étape 2 - Tester le mode NAT

Mettre les deux VM en NAT.

| Test | Résultat attendu | Résultat observé |
|---|---|---|
| VM Linux vers Internet | fonctionne si réseau OK | |
| VM Windows vers Internet | fonctionne si réseau OK | |
| VM Linux vers VM Windows | ne fonctionne pas directement | |
| VM vers hôte | variable selon la configuration | |

#### Étape 3 - Tester le mode réseau interne

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

#### Étape 4 - Tester le mode accès par pont

Mettre une VM en accès par pont.
Relever son adresse IP.
Comparer avec l'adresse IP de l'hôte Debian 13.

Questions :

1. La VM reçoit-elle une adresse du même réseau que l'hôte ?
2. La VM peut-elle faire un ping vers la passerelle ?
3. La VM peut-elle accéder à Internet ?
4. La VM est-elle visible comme une machine du réseau local ?

Conclusion attendue : en mode pont, la VM se comporte comme une machine réelle connectée au réseau local.

#### Étape 5 - Tester le mode host-only si disponible

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
