# Corrigé du QCM du palier 3 : réseau NAT et accès par pont

## Principe de correction

Ce corrigé est destiné au professeur.

Le QCM est validé uniquement avec :

```text
20 bonnes réponses sur 20
```

En cas d’erreur, l’élève doit relire le chapitre concerné du dossier technique, corriger son fichier `qcm-palier3.txt`, puis demander une nouvelle validation.

## Correction détaillée

| Question | Réponse | Explication courte |
|---:|:---:|---|
| 1 | A | La machine hôte est l’ordinateur réel de la salle. Dans ce palier, il s’agit de Debian 13. |
| 2 | B | Les deux machines virtuelles utilisées sont Windows 11 Pro et Zorin OS. |
| 3 | C | Une carte réseau virtuelle est simulée par VirtualBox pour permettre à une VM de communiquer. |
| 4 | A | Une adresse IP sert à identifier une machine sur un réseau. |
| 5 | B | Une adresse IPv4 est composée de 4 nombres séparés par des points. |
| 6 | C | Dans `192.168.1.25`, le dernier octet est `25`. |
| 7 | A | Le masque réseau permet de savoir quelle partie de l’adresse IP correspond au réseau. |
| 8 | B | La passerelle permet de sortir du réseau local. |
| 9 | A | Le DHCP permet d’attribuer automatiquement une adresse IP à une machine. |
| 10 | C | Dans ce palier, les élèves observent les adresses IP, sans les modifier manuellement. |
| 11 | B | La commande `hostname` affiche le nom de la machine. |
| 12 | A | La commande `hostname -I` affiche rapidement les adresses IP de la machine sous Linux. |
| 13 | C | Sous Windows, la commande `ipconfig` affiche l’adresse IP, le masque et la passerelle. |
| 14 | A | La commande `ping` permet de tester si une machine répond sur le réseau. |
| 15 | B | Sous Linux, `ping -c 4 adresse_ip` envoie 4 tests ping. |
| 16 | A | Sous Windows, `ping -n 4 adresse_ip` envoie 4 tests ping. |
| 17 | C | En mode NAT, la VM passe par VirtualBox et la machine hôte pour accéder au réseau. |
| 18 | A | En mode NAT, l’adresse IP de la VM est généralement donnée par le serveur DHCP de VirtualBox. |
| 19 | B | En mode accès par pont, la VM est connectée au réseau réel comme une machine du réseau. |
| 20 | C | Si le mode accès par pont ne fonctionne pas, l’élève doit demander de l’aide avec une explication précise. |

## Réponses seules

```text
1a
2b
3c
4a
5b
6c
7a
8b
9a
10c
11b
12a
13c
14a
15b
16a
17c
18a
19b
20c
```

## Répartition des réponses

| Réponse | Nombre |
|---|---:|
| A | 7 |
| B | 6 |
| C | 7 |

La répartition est équilibrée.

## Validation

| Score | Décision |
|---:|---|
| 20 / 20 | QCM validé, l’élève peut commencer l’activité du palier 3 |
| Moins de 20 / 20 | QCM à reprendre, l’élève ne commence pas l’activité |

## Consigne en cas d’erreur

L’élève doit :

1. identifier les questions fausses ;
2. relire les chapitres correspondants dans le dossier technique ;
3. corriger le fichier `qcm-palier3.txt` ;
4. demander une nouvelle validation.
