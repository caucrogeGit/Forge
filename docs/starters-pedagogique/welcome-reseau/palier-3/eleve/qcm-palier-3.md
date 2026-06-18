# QCM du palier 3 : réseau NAT et accès par pont

## Objectif du QCM

Ce QCM vérifie que vous avez compris le dossier technique du palier 3 avant de commencer l’activité.

Vous ne commencez pas l’activité tant que le QCM n’est pas validé à 100 %.

## Travail demandé

Répondez aux 20 questions dans un fichier texte nommé :

```text
qcm-palier3.txt
```

Le fichier doit contenir une réponse par ligne, au format suivant :

```text
1a
2b
3c
4a
```

Règles à respecter :

* une seule réponse par ligne ;
* pas d’espace entre le numéro et la lettre ;
* pas de phrase ;
* pas de justification ;
* uniquement les lettres `a`, `b` ou `c` en minuscule.

Exemple :

```text
1a
2b
3c
```

## Validation

Le QCM est validé uniquement avec :

```text
20 bonnes réponses sur 20
```

En cas d’erreur, vous devez relire le chapitre concerné du dossier technique, corriger votre fichier, puis demander une nouvelle validation.

## Questions

### Question 1

Dans ce palier, la machine hôte est :

A. Debian 13  
B. Windows 11 Pro  
C. Zorin OS  

### Question 2

Les machines virtuelles utilisées dans ce palier sont :

A. Debian 13 et VirtualBox  
B. Windows 11 Pro et Zorin OS  
C. Windows 11 Pro et Debian 13  

### Question 3

Une carte réseau virtuelle est :

A. une carte physique ajoutée dans l’ordinateur  
B. une carte Wi-Fi réelle  
C. une carte simulée par VirtualBox pour une machine virtuelle  

### Question 4

Une adresse IP sert principalement à :

A. identifier une machine sur un réseau  
B. afficher le nom de l’utilisateur  
C. choisir le système d’exploitation  

### Question 5

Une adresse IPv4 est composée de :

A. 2 nombres séparés par des points  
B. 4 nombres séparés par des points  
C. 8 nombres séparés par des tirets  

### Question 6

Dans l’adresse `192.168.1.25`, le dernier octet est :

A. 192  
B. 168  
C. 25  

### Question 7

Le masque réseau sert à :

A. savoir quelle partie de l’adresse IP correspond au réseau  
B. cacher l’adresse IP de la machine  
C. donner un nom à la machine virtuelle  

### Question 8

La passerelle permet principalement de :

A. supprimer une adresse IP  
B. sortir du réseau local  
C. créer une machine virtuelle  

### Question 9

Le DHCP permet à une machine de :

A. recevoir automatiquement une adresse IP  
B. désactiver sa carte réseau  
C. changer de système d’exploitation  

### Question 10

Dans ce palier, les élèves doivent :

A. configurer manuellement les adresses IP fixes  
B. supprimer les cartes réseau virtuelles  
C. observer les adresses IP sans les modifier manuellement  

### Question 11

Sous Debian 13 ou Zorin OS, la commande `hostname` permet de :

A. tester l’accès à Internet  
B. afficher le nom de la machine  
C. afficher uniquement la passerelle  

### Question 12

Sous Debian 13 ou Zorin OS, la commande `hostname -I` permet de :

A. afficher rapidement les adresses IP de la machine  
B. ouvrir VirtualBox  
C. changer le mode réseau  

### Question 13

Sous Windows 11 Pro, la commande qui affiche l’adresse IP, le masque et la passerelle est :

A. `hostname`  
B. `ping`  
C. `ipconfig`  

### Question 14

La commande `ping` sert à :

A. tester si une machine répond sur le réseau  
B. installer une machine virtuelle  
C. modifier le masque réseau  

### Question 15

Sous Linux, pour envoyer seulement 4 tests ping, on utilise :

A. `ping -n 4 adresse_ip`  
B. `ping -c 4 adresse_ip`  
C. `ipconfig /4 adresse_ip`  

### Question 16

Sous Windows 11 Pro, pour envoyer seulement 4 tests ping, on utilise :

A. `ping -n 4 adresse_ip`  
B. `ping -c 4 adresse_ip`  
C. `hostname -I adresse_ip`  

### Question 17

En mode NAT, la machine virtuelle :

A. est toujours visible directement sur le réseau réel  
B. n’a jamais d’adresse IP  
C. passe par VirtualBox et la machine hôte pour accéder au réseau  

### Question 18

En mode NAT, l’adresse IP de la machine virtuelle est généralement donnée par :

A. le serveur DHCP de VirtualBox  
B. le testeur RJ45  
C. l’élève obligatoirement à la main  

### Question 19

En mode accès par pont, la machine virtuelle :

A. est isolée de tout réseau  
B. est connectée au réseau réel comme une machine du réseau  
C. ne peut jamais recevoir d’adresse IP  

### Question 20

Si le mode accès par pont ne fonctionne pas dans la salle, la bonne attitude est de :

A. modifier plusieurs paramètres au hasard  
B. désactiver la carte réseau de la machine hôte  
C. demander au professeur en expliquant le test réalisé et le résultat observé  