# Checklist de validation du palier 4

## Palier 4 : configurer un réseau interne et diagnostiquer une communication

## Identification de l’élève

| Élément | Information |
|---|---|
| Nom | |
| Prénom | |
| Classe | |
| Poste utilisé | |
| Date | |

## Principe

Cette checklist sert à vérifier que le palier 4 est terminé.

L’élève commence par faire son auto-vérification.
Le professeur valide ensuite les points attendus.

La checklist est un document partagé entre l’élève et le professeur.

## 1. Validation du QCM

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le fichier `qcm-palier4.txt` existe | ☐ | ☐ | |
| Le format demandé est respecté | ☐ | ☐ | |
| Le QCM contient 20 réponses | ☐ | ☐ | |
| Le QCM est validé à 100 % | ☐ | ☐ | |
| L’élève a corrigé les erreurs éventuelles avant de commencer l’activité | ☐ | ☐ | |

## 2. Préparation des machines virtuelles

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| La VM Windows 11 Pro est présente | ☐ | ☐ | |
| La VM Zorin OS est présente | ☐ | ☐ | |
| Les deux VM ont été arrêtées proprement avant modification réseau | ☐ | ☐ | |
| L’élève sait expliquer le rôle de la machine hôte Debian 13 | ☐ | ☐ | |

## 3. Configuration VirtualBox

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Windows 11 Pro est configurée en réseau interne | ☐ | ☐ | |
| Zorin OS est configurée en réseau interne | ☐ | ☐ | |
| Le nom du réseau interne Windows est `reseau-2tne` | ☐ | ☐ | |
| Le nom du réseau interne Zorin OS est `reseau-2tne` | ☐ | ☐ | |
| Les deux VM utilisent exactement le même nom de réseau interne | ☐ | ☐ | |
| Les cartes réseau virtuelles sont activées | ☐ | ☐ | |

## 4. Configuration IP de Zorin OS

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Zorin OS utilise l’adresse IP `192.168.10.10` | ☐ | ☐ | |
| Zorin OS utilise le masque `255.255.255.0` ou `/24` | ☐ | ☐ | |
| La passerelle est vide ou non utilisée | ☐ | ☐ | |
| Le DNS est vide ou non utilisé | ☐ | ☐ | |
| L’élève sait retrouver l’adresse avec une commande Linux | ☐ | ☐ | |

## 5. Configuration IP de Windows 11 Pro

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Windows 11 Pro utilise l’adresse IP `192.168.10.20` | ☐ | ☐ | |
| Windows 11 Pro utilise le masque `255.255.255.0` | ☐ | ☐ | |
| La passerelle est vide ou non utilisée | ☐ | ☐ | |
| Le DNS est vide ou non utilisé | ☐ | ☐ | |
| L’élève sait retrouver l’adresse avec `ipconfig` | ☐ | ☐ | |

## 6. Vérification du même réseau logique

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Zorin OS appartient au réseau `192.168.10.0` | ☐ | ☐ | |
| Windows 11 Pro appartient au réseau `192.168.10.0` | ☐ | ☐ | |
| Les deux VM ont des adresses IP différentes | ☐ | ☐ | |
| L’élève sait expliquer pourquoi les deux VM sont dans le même réseau logique | ☐ | ☐ | |

## 7. Tests de communication

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le test de Zorin OS vers Windows 11 Pro a été réalisé | ☐ | ☐ | |
| La commande Linux utilisée est correcte | ☐ | ☐ | |
| Le test de Windows 11 Pro vers Zorin OS a été réalisé | ☐ | ☐ | |
| La commande Windows utilisée est correcte | ☐ | ☐ | |
| Les résultats des tests sont notés | ☐ | ☐ | |
| L’élève sait expliquer le résultat obtenu | ☐ | ☐ | |

## 8. Diagnostic et pare-feu Windows

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| L’élève ne modifie pas les paramètres au hasard | ☐ | ☐ | |
| L’élève suit l’ordre de diagnostic du dossier technique | ☐ | ☐ | |
| L’élève tient compte du pare-feu Windows si le ping vers Windows échoue | ☐ | ☐ | |
| L’élève ne désactive pas le pare-feu Windows sans consigne | ☐ | ☐ | |
| L’élève formule une demande d’aide précise si nécessaire | ☐ | ☐ | |

## 9. Traces attendues

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le fichier `palier4-resultats.txt` existe | ☐ | ☐ | |
| Les relevés IP sont présents | ☐ | ☐ | |
| Les résultats des tests sont présents | ☐ | ☐ | |
| La conclusion est présente | ☐ | ☐ | |
| Les informations sont lisibles et exploitables | ☐ | ☐ | |

## 10. Autonomie et méthode

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| L’élève utilise le dossier technique | ☐ | ☐ | |
| L’élève sait retrouver l’information utile | ☐ | ☐ | |
| L’élève sait expliquer ce qu’il a fait | ☐ | ☐ | |
| L’élève sait corriger une erreur simple | ☐ | ☐ | |
| L’élève sait présenter son résultat | ☐ | ☐ | |

## 11. Validation finale

| Élément final à valider | Élève | Professeur | Observation |
|---|---|---|---|
| Le palier 4 est terminé | ☐ | ☐ | |
| Le travail peut être présenté | ☐ | ☐ | |
| Le palier suivant peut être commencé | ☐ | ☐ | |

Décision finale :

| État | Décision |
|---|---|
| ☐ | Palier validé |
| ☐ | Palier à reprendre |
| ☐ | Correction demandée |

Commentaire professeur :

....................................................................................................

....................................................................................................

....................................................................................................