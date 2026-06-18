# QCM du palier 3 : tester les modes réseau VirtualBox

## Consigne

Ce QCM vérifie que le dossier technique du palier 3 a été compris.

Pour chaque question, choisir une seule réponse : A, B ou C.

Vous devez enregistrer vos réponses dans un fichier texte nommé :

```text
qcm-palier3.txt
```

Le fichier doit contenir une réponse par ligne, sans espace entre le numéro de la question et la lettre choisie.

Exemple de format attendu :

```text
1a
2b
3c
4a
5b
```

Le fichier doit contenir les réponses aux 25 questions.

Le QCM doit être validé à 100 % avant de commencer l’activité.

## Questions

### Question 1

Dans VirtualBox, le mode réseau choisi permet de définir :

A. avec qui la machine virtuelle peut communiquer  
B. la couleur du bureau de la machine virtuelle  
C. le mot de passe de la machine virtuelle  

### Question 2

Dans ce palier, la machine hôte est :

A. Windows 11 Pro  
B. Debian 13  
C. Zorin OS  

### Question 3

La carte réseau d’une machine virtuelle est :

A. une carte réseau physique branchée directement dans la VM  
B. un câble Ethernet réel relié directement à la VM  
C. une carte réseau simulée par VirtualBox  

### Question 4

Sous Debian 13 ou Zorin OS, la commande qui permet d’afficher le nom de la machine est :

A. `hostname`  
B. `ipconfig`  
C. `apt upgrade`  

### Question 5

Sous Windows 11 Pro, la commande qui permet d’afficher l’adresse IP est :

A. `ip a`  
B. `ipconfig`  
C. `hostname -I`  

## Questions sur le calcul des adresses IP

### Question 6

Une adresse IPv4 est composée de :

A. 2 octets  
B. 8 octets  
C. 4 octets  

### Question 7

Un octet peut prendre une valeur comprise entre :

A. 0 et 255  
B. 0 et 8  
C. 0 et 1024  

### Question 8

Dans le tableau des puissances de 2 sur un octet, les valeurs utilisées sont :

A. 1, 2, 3, 4, 5, 6, 7, 8  
B. 128, 64, 32, 16, 8, 4, 2, 1  
C. 255, 254, 253, 252, 251, 250, 249, 248  

### Question 9

La valeur décimale 192 correspond au binaire :

A. 00001010  
B. 00010100  
C. 11000000  

### Question 10

La valeur décimale 10 correspond au binaire :

A. 00001010  
B. 00000101  
C. 00010000  

### Question 11

La valeur décimale 20 correspond au binaire :

A. 00100000  
B. 00010100  
C. 00001100  

### Question 12

Avec l’adresse IP `192.168.10.20` et le masque `255.255.255.0`, l’adresse du réseau est :

A. `192.168.10.0`  
B. `192.168.20.0`  
C. `192.168.10.20`  

### Question 13

Avec le masque `255.255.255.0`, quelle partie indique généralement le réseau ?

A. uniquement le dernier octet  
B. les trois premiers octets  
C. uniquement le premier octet  

### Question 14

Les adresses `192.168.10.10` et `192.168.10.20` avec le masque `255.255.255.0` sont :

A. dans deux réseaux différents  
B. automatiquement sur Internet  
C. dans le même réseau logique  

### Question 15

Les adresses `192.168.10.10` et `192.168.20.20` avec le masque `255.255.255.0` sont :

A. forcément dans le même réseau  
B. dans deux réseaux logiques différents  
C. identiques  

## Questions sur les modes réseau, les commandes et le diagnostic

### Question 16

Le DHCP sert à :

A. désactiver une carte réseau  
B. tester un câble RJ45  
C. donner automatiquement une adresse IP à une machine  

### Question 17

En mode NAT, une machine virtuelle peut généralement :

A. accéder à Internet en passant par la machine hôte  
B. devenir visible sur tout le réseau réel  
C. communiquer directement avec toutes les autres VM sans configuration  

### Question 18

Le mode accès par pont permet à la machine virtuelle :

A. de rester totalement isolée de tout réseau  
B. d’apparaître comme une machine du réseau réel  
C. de supprimer son disque virtuel  

### Question 19

En mode réseau interne, deux machines virtuelles peuvent communiquer si :

A. elles ont le même mot de passe  
B. elles sont toutes les deux sous Windows  
C. elles utilisent le même nom de réseau interne VirtualBox  

### Question 20

Le mode réseau privé hôte permet principalement :

A. de faire communiquer la machine hôte et une machine virtuelle  
B. d’accéder à Internet sans passer par l’hôte  
C. de remplacer le mode NAT  

### Question 21

La commande `ping adresse_ip` sert à :

A. changer l’adresse IP d’une machine  
B. tester si une machine répond sur le réseau  
C. afficher la version de VirtualBox  

### Question 22

Sous Debian 13 ou Zorin OS, la commande qui permet d’envoyer seulement 4 tests ping est :

A. `ping -n 4 adresse_ip`  
B. `ping adresse_ip 4`  
C. `ping -c 4 adresse_ip`  

### Question 23

Sous Windows 11 Pro, la commande qui permet d’envoyer seulement 4 tests ping est :

A. `ping -n 4 adresse_ip`  
B. `ping -c 4 adresse_ip`  
C. `ip route adresse_ip`  

### Question 24

Si Windows 11 Pro ne répond pas au ping, cela peut venir :

A. du pare-feu Windows  
B. uniquement d’un mauvais câble RJ45  
C. obligatoirement d’une mauvaise image ISO  

### Question 25

Le palier 3 est terminé lorsque :

A. les machines virtuelles sont seulement démarrées  
B. le QCM est commencé mais pas validé  
C. les tests réseau sont réalisés, observés et expliqués  

## Validation

Le QCM est validé uniquement avec **25 bonnes réponses sur 25**.

Si une réponse est fausse :

1. relire le chapitre correspondant dans le dossier technique ;
2. corriger le fichier `qcm-palier3.txt` ;
3. demander une nouvelle validation.

Vous ne démarrez pas l’activité tant que le fichier `qcm-palier3.txt` n’est pas correct à 100 %.
