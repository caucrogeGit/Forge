# QCM du palier 4 : réseau interne et diagnostic

## Consigne

Répondez aux 20 questions dans un fichier texte nommé :

```text
qcm-palier4.txt
```

Format obligatoire : une réponse par ligne, sans espace entre le numéro et la lettre.

Exemple :

```text
1a
2b
3c
```

Vous ne commencez pas l’activité tant que le QCM n’est pas validé à 100 %.

## Questions

### Question 1

Dans le palier 4, les machines principales à tester sont :

A. Windows 11 Pro et Zorin OS
B. Debian 13 et la box Internet
C. Debian 13 et le réseau réel de la salle

### Question 2

Dans ce palier, Debian 13 sert principalement à :

A. remplacer la machine virtuelle Windows
B. lancer VirtualBox et modifier les paramètres des VM
C. fournir automatiquement les adresses IP du réseau interne

### Question 3

Le mode réseau étudié dans le palier 4 est :

A. NAT
B. Accès par pont
C. Réseau interne

### Question 4

Le mode réseau interne permet principalement de :

A. faire communiquer plusieurs VM dans un réseau isolé
B. connecter directement une VM au réseau réel de la salle
C. donner Internet automatiquement à toutes les VM

### Question 5

En mode réseau interne, les machines virtuelles :

A. sont toujours visibles sur le réseau réel
B. peuvent communiquer entre elles si elles sont correctement configurées
C. utilisent obligatoirement le Wi-Fi de la salle

### Question 6

Dans ce palier, le nom du réseau interne à utiliser est :

A. reseau-internet
B. reseau-windows
C. reseau-2tne

### Question 7

Si les deux VM n’utilisent pas exactement le même nom de réseau interne :

A. elles ne pourront pas communiquer entre elles
B. elles auront automatiquement accès à Internet
C. Windows corrigera automatiquement le problème

### Question 8

Pourquoi utilise-t-on des adresses IP fixes dans ce palier ?

A. Parce que le mode réseau interne simple ne fournit généralement pas d’adresse automatiquement
B. Parce que le mode NAT est encore utilisé
C. Parce que le pare-feu Windows impose toujours une IP fixe

### Question 9

L’adresse IP attendue pour Zorin OS est :

A. 192.168.10.20
B. 192.168.10.10
C. 192.168.20.10

### Question 10

L’adresse IP attendue pour Windows 11 Pro est :

A. 192.168.10.20
B. 192.168.10.10
C. 10.0.2.15

### Question 11

Le masque réseau utilisé dans ce palier est :

A. 255.255.0.0
B. 255.0.0.0
C. 255.255.255.0

### Question 12

Avec le masque `255.255.255.0`, les adresses `192.168.10.10` et `192.168.10.20` appartiennent :

A. au même réseau logique
B. à deux réseaux logiques différents
C. à Internet directement

### Question 13

Avec le masque `255.255.255.0`, les adresses `192.168.10.10` et `192.168.20.20` appartiennent :

A. au même réseau logique
B. à deux réseaux logiques différents
C. au même poste informatique

### Question 14

Depuis Zorin OS, la commande adaptée pour tester Windows 11 Pro avec 4 paquets est :

A. `ping -c 4 192.168.10.20`
B. `ping -n 4 192.168.10.20`
C. `ipconfig 192.168.10.20`

### Question 15

Depuis Windows 11 Pro, la commande adaptée pour tester Zorin OS avec 4 paquets est :

A. `hostname -I 192.168.10.10`
B. `ping -c 4 192.168.10.10`
C. `ping -n 4 192.168.10.10`

### Question 16

Si le ping de Zorin OS vers Windows 11 Pro échoue, alors que les IP et le réseau interne sont corrects, une cause possible est :

A. le pare-feu Windows bloque les réponses au ping
B. Zorin OS est forcément mal installé
C. le câble RJ45 de la salle est forcément débranché

### Question 17

Que faut-il faire avant de désactiver ou modifier le pare-feu Windows ?

A. Redémarrer Debian 13 sans prévenir
B. Demander au professeur
C. Supprimer la VM Windows

### Question 18

Dans la méthode de diagnostic, il faut d’abord vérifier :

A. que les deux VM sont démarrées et que les cartes réseau virtuelles sont activées
B. le prix de la licence Windows
C. la couleur du thème graphique de Zorin OS

### Question 19

Une bonne demande d’aide doit préciser :

A. seulement que ça ne marche pas
B. uniquement le prénom de l’élève
C. l’étape, la machine, l’adresse IP, la commande lancée et le résultat obtenu

### Question 20

Pour convertir 192 en binaire, on utilise :

A. 128 + 32 + 16
B. 128 + 64
C. 64 + 32 + 8