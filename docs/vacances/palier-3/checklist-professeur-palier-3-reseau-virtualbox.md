# Checklist professeur : validation du palier 3

# Tester les modes réseau VirtualBox

## Identification de l’élève

| Élément | Information |
|---|---|
| Nom | |
| Prénom | |
| Classe | |
| Poste utilisé | |
| Date de validation | |

## Objectif de la checklist

Cette checklist sert au professeur pour vérifier que l’élève a correctement terminé le palier 3.

Le palier est validé uniquement lorsque l’élève a testé les modes réseau demandés, relevé les adresses IP, réalisé les calculs de réseau, interprété les résultats et rédigé une conclusion cohérente.

## 1. Validation du QCM

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| Le fichier `qcm-palier3.txt` existe | ☐ | ☐ | |
| Le fichier contient 25 réponses | ☐ | ☐ | |
| Le format est respecté, par exemple `1a`, `2b`, `3c` | ☐ | ☐ | |
| Le QCM est correct à 100 % | ☐ | ☐ | |
| Les erreurs éventuelles ont été corrigées avant l’activité | ☐ | ☐ | |

Validation de cette partie :

| État | Décision |
|---|---|
| ☐ | QCM validé |
| ☐ | QCM à reprendre |

## 2. Vérification du fichier de compte rendu

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| Le fichier `activite-palier3.txt` existe | ☐ | ☐ | |
| Le fichier est lisible | ☐ | ☐ | |
| Le fichier contient toutes les parties demandées | ☐ | ☐ | |
| Les résultats sont écrits clairement | ☐ | ☐ | |
| Les conclusions sont rédigées par l’élève | ☐ | ☐ | |

Parties attendues dans le fichier :

| Partie attendue | Présente | Observation |
|---|---|---|
| 1. Identification des machines | ☐ | |
| 2. Relevé des adresses IP | ☐ | |
| 3. Calcul des réseaux | ☐ | |
| 4. Test du mode NAT | ☐ | |
| 5. Test du mode réseau interne | ☐ | |
| 6. Test du mode accès par pont | ☐ | |
| 7. Test du mode réseau privé hôte | ☐ | |
| 8. Diagnostic en cas d’échec | ☐ | |
| 9. Conclusion finale | ☐ | |

## 3. Vérification de l’environnement de départ

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| VirtualBox démarre correctement sur le poste Debian 13 | ☐ | ☐ | |
| La VM `VM-Windows-11-Pro` existe | ☐ | ☐ | |
| La VM `VM-Zorin` existe | ☐ | ☐ | |
| Les deux machines virtuelles démarrent correctement | ☐ | ☐ | |
| Les sessions s’ouvrent avec le compte `tne` | ☐ | ☐ | |
| Les deux machines virtuelles s’arrêtent proprement | ☐ | ☐ | |

## 4. Identification des machines

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| Le nom de la machine hôte Debian 13 est relevé | ☐ | ☐ | |
| Le nom de la VM Windows 11 Pro est relevé | ☐ | ☐ | |
| Le nom de la VM Zorin OS est relevé | ☐ | ☐ | |
| L’élève utilise les commandes adaptées pour identifier les machines | ☐ | ☐ | |

Commandes attendues :

| Système | Commande attendue | Vérifié |
|---|---|---|
| Debian 13 | `hostname` | ☐ |
| Zorin OS | `hostname` | ☐ |
| Windows 11 Pro | `hostname` | ☐ |

## 5. Relevé des adresses IP

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| L’adresse IP de la machine hôte Debian 13 est relevée | ☐ | ☐ | |
| L’adresse IP de la VM Windows 11 Pro est relevée | ☐ | ☐ | |
| L’adresse IP de la VM Zorin OS est relevée | ☐ | ☐ | |
| L’élève indique la commande utilisée pour chaque relevé | ☐ | ☐ | |
| L’élève sait identifier l’adresse IP utile pour le test | ☐ | ☐ | |

Commandes attendues :

| Système | Commandes possibles | Vérifié |
|---|---|---|
| Debian 13 | `hostname -I`, `ip a` | ☐ |
| Zorin OS | `hostname -I`, `ip a` | ☐ |
| Windows 11 Pro | `ipconfig` | ☐ |

## 6. Calcul des réseaux

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| L’élève utilise le tableau des puissances de 2 | ☐ | ☐ | |
| L’élève sait convertir un octet en binaire | ☐ | ☐ | |
| L’élève sait lire le masque `255.255.255.0` | ☐ | ☐ | |
| L’élève sait déterminer le réseau d’une adresse IP | ☐ | ☐ | |
| L’élève compare correctement deux adresses IP | ☐ | ☐ | |
| L’élève sait dire si deux machines sont dans le même réseau logique | ☐ | ☐ | |

Exemples de points attendus :

| Élément | Attendu | Conforme |
|---|---|---|
| `192` converti en binaire | `11000000` | ☐ |
| `10` converti en binaire | `00001010` | ☐ |
| `20` converti en binaire | `00010100` | ☐ |
| `192.168.10.20` avec `255.255.255.0` | réseau `192.168.10.0` | ☐ |
| `192.168.10.10` et `192.168.10.20` avec `255.255.255.0` | même réseau logique | ☐ |

## 7. Test du mode NAT

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| Les deux VM sont placées en mode NAT | ☐ | ☐ | |
| Les adresses IP des deux VM sont relevées | ☐ | ☐ | |
| L’accès Internet de Windows 11 Pro est testé | ☐ | ☐ | |
| L’accès Internet de Zorin OS est testé | ☐ | ☐ | |
| Un test entre les deux VM est réalisé | ☐ | ☐ | |
| L’élève note les résultats observés | ☐ | ☐ | |
| L’élève rédige une conclusion sur le mode NAT | ☐ | ☐ | |

Validation du mode NAT :

| État | Décision |
|---|---|
| ☐ | Mode NAT validé |
| ☐ | Mode NAT à reprendre |

## 8. Test du mode réseau interne

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| Les deux VM sont placées sur le même réseau interne VirtualBox | ☐ | ☐ | |
| Le nom du réseau interne est correctement renseigné | ☐ | ☐ | |
| L’adresse IP fixe de Zorin OS est configurée | ☐ | ☐ | |
| L’adresse IP fixe de Windows 11 Pro est configurée | ☐ | ☐ | |
| Le masque réseau est correctement configuré | ☐ | ☐ | |
| Les deux adresses IP sont différentes | ☐ | ☐ | |
| Les deux machines sont dans le même réseau logique | ☐ | ☐ | |
| Le ping de Zorin OS vers Windows 11 Pro est testé | ☐ | ☐ | |
| Le ping de Windows 11 Pro vers Zorin OS est testé | ☐ | ☐ | |
| L’élève tient compte du pare-feu Windows si le ping échoue | ☐ | ☐ | |
| L’élève rédige une conclusion sur le mode réseau interne | ☐ | ☐ | |

Adresses attendues pour le réseau interne :

| Machine | Adresse IP attendue | Masque attendu | Conforme |
|---|---|---|---|
| VM Zorin OS | `192.168.10.10` | `255.255.255.0` | ☐ |
| VM Windows 11 Pro | `192.168.10.20` | `255.255.255.0` | ☐ |

Validation du réseau interne :

| État | Décision |
|---|---|
| ☐ | Réseau interne validé |
| ☐ | Réseau interne à reprendre |

## 9. Test du mode accès par pont

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| Le mode accès par pont a été utilisé avec autorisation du professeur | ☐ | ☐ | |
| Une VM est placée en mode accès par pont | ☐ | ☐ | |
| L’adresse IP de la VM est relevée | ☐ | ☐ | |
| L’adresse IP de la machine hôte est relevée | ☐ | ☐ | |
| L’élève compare les réseaux de l’hôte et de la VM | ☐ | ☐ | |
| Le test vers la passerelle est réalisé | ☐ | ☐ | |
| Le test vers Internet est réalisé | ☐ | ☐ | |
| L’élève comprend que la VM devient visible sur le réseau réel | ☐ | ☐ | |
| L’élève rédige une conclusion sur le mode accès par pont | ☐ | ☐ | |

Validation du mode accès par pont :

| État | Décision |
|---|---|
| ☐ | Mode accès par pont validé |
| ☐ | Mode accès par pont à reprendre |
| ☐ | Mode non testé, non autorisé par le professeur |

## 10. Test du mode réseau privé hôte

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| L’élève vérifie si le mode réseau privé hôte est disponible | ☐ | ☐ | |
| Si le mode est indisponible, l’élève le note dans son compte rendu | ☐ | ☐ | |
| Si le mode est disponible, une VM est placée en réseau privé hôte | ☐ | ☐ | |
| L’adresse IP de l’hôte sur le réseau privé hôte est relevée | ☐ | ☐ | |
| L’adresse IP de la VM est relevée | ☐ | ☐ | |
| Le test hôte vers VM est réalisé | ☐ | ☐ | |
| Le test VM vers hôte est réalisé | ☐ | ☐ | |
| Le test VM vers Internet est réalisé | ☐ | ☐ | |
| L’élève rédige une conclusion sur le mode réseau privé hôte | ☐ | ☐ | |

Validation du mode réseau privé hôte :

| État | Décision |
|---|---|
| ☐ | Mode réseau privé hôte validé |
| ☐ | Mode réseau privé hôte à reprendre |
| ☐ | Mode non disponible sur le poste |

## 11. Diagnostic réseau

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| L’élève choisit un test à diagnostiquer | ☐ | ☐ | |
| Le mode réseau utilisé est indiqué | ☐ | ☐ | |
| La machine source est identifiée | ☐ | ☐ | |
| La machine cible est identifiée | ☐ | ☐ | |
| Les adresses IP sont indiquées | ☐ | ☐ | |
| Le masque est indiqué | ☐ | ☐ | |
| L’élève vérifie si les machines sont dans le même réseau logique | ☐ | ☐ | |
| L’élève indique la commande utilisée | ☐ | ☐ | |
| L’élève formule au moins une hypothèse | ☐ | ☐ | |
| L’élève propose une vérification ou une correction | ☐ | ☐ | |
| L’élève conclut sur le diagnostic | ☐ | ☐ | |

## 12. Maîtrise des commandes réseau

| Commande | Rôle connu par l’élève | Utilisée correctement |
|---|---|---|
| `hostname` | ☐ | ☐ |
| `hostname -I` | ☐ | ☐ |
| `ip a` | ☐ | ☐ |
| `ip route` | ☐ | ☐ |
| `ipconfig` | ☐ | ☐ |
| `ping adresse_ip` | ☐ | ☐ |
| `ping -c 4 adresse_ip` | ☐ | ☐ |
| `ping -n 4 adresse_ip` | ☐ | ☐ |

## 13. Vérification de l’autonomie de l’élève

| Point à vérifier | Oui | Non | Observation |
|---|---|---|---|
| L’élève utilise le dossier technique pour chercher les informations | ☐ | ☐ | |
| L’élève ne demande pas directement la solution sans recherche préalable | ☐ | ☐ | |
| L’élève sait indiquer le chapitre consulté dans le dossier technique | ☐ | ☐ | |
| L’élève sait expliquer ce qu’il a fait | ☐ | ☐ | |
| L’élève sait expliquer ce qu’il a observé | ☐ | ☐ | |
| L’élève sait expliquer ce qui bloque | ☐ | ☐ | |

Formulation attendue en cas de demande d’aide :

| Point attendu | Oui | Non | Observation |
|---|---|---|---|
| L’élève indique l’étape concernée | ☐ | ☐ | |
| L’élève indique la machine concernée | ☐ | ☐ | |
| L’élève indique le mode réseau testé | ☐ | ☐ | |
| L’élève indique ce qu’il a déjà essayé | ☐ | ☐ | |
| L’élève indique ce qu’il observe | ☐ | ☐ | |
| L’élève indique la partie du dossier consultée | ☐ | ☐ | |
| L’élève formule une demande précise | ☐ | ☐ | |

## 14. Validation finale du palier 3

| Élément final à valider | Oui | Non | Observation |
|---|---|---|---|
| QCM validé à 100 % | ☐ | ☐ | |
| Fichier `activite-palier3.txt` complet | ☐ | ☐ | |
| Machines identifiées correctement | ☐ | ☐ | |
| Adresses IP relevées correctement | ☐ | ☐ | |
| Calculs de réseau réalisés et justes | ☐ | ☐ | |
| Mode NAT testé et expliqué | ☐ | ☐ | |
| Mode réseau interne testé et expliqué | ☐ | ☐ | |
| Mode accès par pont testé ou justifié comme non testé | ☐ | ☐ | |
| Mode réseau privé hôte testé ou justifié comme indisponible | ☐ | ☐ | |
| Diagnostic réseau réalisé | ☐ | ☐ | |
| Commandes réseau utilisées correctement | ☐ | ☐ | |
| Conclusion finale cohérente | ☐ | ☐ | |
| L’élève sait expliquer oralement ses résultats | ☐ | ☐ | |

Décision finale :

| État | Décision |
|---|---|
| ☐ | Palier 3 validé |
| ☐ | Palier 3 à reprendre |
| ☐ | Validation partielle, correction demandée |

Commentaire professeur :

....................................................................................................

....................................................................................................

....................................................................................................
