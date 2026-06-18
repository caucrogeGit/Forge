# Checklist de validation du palier 3

# Relever les informations réseau et tester les modes NAT et accès par pont

## Identification de l’élève

| Élément | Information |
|---|---|
| Nom | |
| Prénom | |
| Classe | |
| Poste utilisé | |
| Date | |

## Principe

Cette checklist sert à vérifier que le palier 3 est terminé.

L’élève commence par faire son auto-vérification.

Le professeur valide ensuite les points attendus.

La checklist ne remplace pas le fichier de résultats `palier3-resultats.txt`.

## 1. Validation du QCM

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le fichier de réponse du QCM existe | ☐ | ☐ | |
| Le format demandé est respecté | ☐ | ☐ | |
| Le QCM du palier 3 est validé à 100 % | ☐ | ☐ | |
| L’activité a commencé uniquement après validation du QCM | ☐ | ☐ | |

## 2. Vérification du matériel et de l’environnement

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le poste hôte Debian 13 est disponible | ☐ | ☐ | |
| VirtualBox démarre correctement | ☐ | ☐ | |
| La VM Windows 11 Pro est présente | ☐ | ☐ | |
| La VM Zorin OS est présente | ☐ | ☐ | |
| Le dossier technique du palier 3 est accessible | ☐ | ☐ | |
| L’activité du palier 3 est accessible | ☐ | ☐ | |

## 3. Fichier de résultats

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le fichier `palier3-resultats.txt` existe | ☐ | ☐ | |
| Le fichier contient les informations de Debian 13 | ☐ | ☐ | |
| Le fichier contient les informations de Windows 11 Pro en mode NAT | ☐ | ☐ | |
| Le fichier contient les informations de Zorin OS en mode NAT | ☐ | ☐ | |
| Le fichier contient les résultats des tests réseau | ☐ | ☐ | |
| Le fichier contient une comparaison NAT / accès par pont | ☐ | ☐ | |
| Le fichier contient une conclusion courte | ☐ | ☐ | |

## 4. Relevés réseau de la machine hôte Debian 13

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le nom de la machine hôte est relevé avec `hostname` | ☐ | ☐ | |
| L’adresse IP principale est relevée | ☐ | ☐ | |
| La passerelle est relevée avec `ip route` | ☐ | ☐ | |
| L’interface réseau utilisée est identifiée | ☐ | ☐ | |
| Les informations sont recopiées dans `palier3-resultats.txt` | ☐ | ☐ | |

## 5. Configuration et relevés de Windows 11 Pro en mode NAT

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| La VM Windows 11 Pro est arrêtée proprement avant modification | ☐ | ☐ | |
| L’adaptateur 1 est activé | ☐ | ☐ | |
| Le mode réseau est réglé sur NAT | ☐ | ☐ | |
| La VM Windows 11 Pro démarre correctement | ☐ | ☐ | |
| Le nom de la machine est relevé avec `hostname` | ☐ | ☐ | |
| L’adresse IPv4 est relevée avec `ipconfig` | ☐ | ☐ | |
| Le masque est relevé avec `ipconfig` | ☐ | ☐ | |
| La passerelle par défaut est relevée avec `ipconfig` | ☐ | ☐ | |
| L’élève indique si l’adresse IP semble être dans le même réseau que Debian 13 | ☐ | ☐ | |

## 6. Test réseau de Windows 11 Pro en mode NAT

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| La commande `ping -n 4 8.8.8.8` est lancée | ☐ | ☐ | |
| Le nombre de paquets envoyés est relevé | ☐ | ☐ | |
| Le nombre de paquets reçus est relevé | ☐ | ☐ | |
| La perte de paquets est relevée | ☐ | ☐ | |
| Le résultat est noté dans `palier3-resultats.txt` | ☐ | ☐ | |
| L’élève sait dire si Windows reçoit une IP en mode NAT | ☐ | ☐ | |
| L’élève sait dire si Windows accède à une adresse extérieure | ☐ | ☐ | |
| L’élève sait dire que la VM n’est pas directement visible sur le réseau réel en NAT | ☐ | ☐ | |
| L’élève sait que l’adresse IP est généralement donnée par le DHCP VirtualBox en mode NAT | ☐ | ☐ | |

## 7. Configuration et relevés de Zorin OS en mode NAT

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| La VM Zorin OS est arrêtée proprement avant modification | ☐ | ☐ | |
| L’adaptateur 1 est activé | ☐ | ☐ | |
| Le mode réseau est réglé sur NAT | ☐ | ☐ | |
| La VM Zorin OS démarre correctement | ☐ | ☐ | |
| Le nom de la machine est relevé avec `hostname` | ☐ | ☐ | |
| L’adresse IP est relevée avec `hostname -I` ou `ip a` | ☐ | ☐ | |
| La passerelle est relevée avec `ip route` | ☐ | ☐ | |
| L’interface réseau utilisée est identifiée | ☐ | ☐ | |
| L’élève indique si l’adresse IP semble être dans le même réseau que Debian 13 | ☐ | ☐ | |

## 8. Test réseau de Zorin OS en mode NAT

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| La commande `ping -c 4 8.8.8.8` est lancée | ☐ | ☐ | |
| Le nombre de paquets envoyés est relevé | ☐ | ☐ | |
| Le nombre de paquets reçus est relevé | ☐ | ☐ | |
| La perte de paquets est relevée | ☐ | ☐ | |
| Le résultat est noté dans `palier3-resultats.txt` | ☐ | ☐ | |
| L’élève sait dire si Zorin OS reçoit une IP en mode NAT | ☐ | ☐ | |
| L’élève sait dire si Zorin OS accède à une adresse extérieure | ☐ | ☐ | |
| L’élève sait expliquer l’intérêt principal du mode NAT | ☐ | ☐ | |

## 9. Autorisation du mode accès par pont

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| L’élève a demandé l’autorisation avant d’utiliser l’accès par pont | ☐ | ☐ | |
| Le professeur a indiqué si le mode pont était autorisé | ☐ | ☐ | |
| La ou les VM à tester en mode pont sont clairement indiquées | ☐ | ☐ | |
| La carte réseau réelle à utiliser est clairement indiquée | ☐ | ☐ | |
| Si le mode pont n’est pas autorisé, l’élève l’a noté dans son fichier de résultats | ☐ | ☐ | |

## 10. Test de Windows 11 Pro en mode accès par pont, si autorisé

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| La VM Windows 11 Pro est arrêtée proprement avant modification | ☐ | ☐ | |
| Le mode réseau est réglé sur accès par pont | ☐ | ☐ | |
| La bonne carte réseau réelle est sélectionnée | ☐ | ☐ | |
| L’adresse IPv4 est relevée avec `ipconfig` | ☐ | ☐ | |
| Le masque est relevé | ☐ | ☐ | |
| La passerelle par défaut est relevée | ☐ | ☐ | |
| Le ping vers la passerelle est réalisé | ☐ | ☐ | |
| L’élève indique si Windows est dans le même réseau que Debian 13 | ☐ | ☐ | |
| L’élève indique si Windows semble intégré au réseau réel | ☐ | ☐ | |

## 11. Test de Zorin OS en mode accès par pont, si autorisé

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| La VM Zorin OS est arrêtée proprement avant modification | ☐ | ☐ | |
| Le mode réseau est réglé sur accès par pont | ☐ | ☐ | |
| La bonne carte réseau réelle est sélectionnée | ☐ | ☐ | |
| L’adresse IP est relevée avec `hostname -I` ou `ip a` | ☐ | ☐ | |
| La passerelle est relevée avec `ip route` | ☐ | ☐ | |
| Le ping vers la passerelle est réalisé | ☐ | ☐ | |
| L’élève indique si Zorin OS est dans le même réseau que Debian 13 | ☐ | ☐ | |
| L’élève indique si Zorin OS semble intégré au réseau réel | ☐ | ☐ | |

## 12. Comparaison NAT et accès par pont

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| L’élève indique qui donne l’adresse IP en mode NAT | ☐ | ☐ | |
| L’élève indique qui donne l’adresse IP en mode accès par pont | ☐ | ☐ | |
| L’élève compare l’accès Internet dans les deux modes | ☐ | ☐ | |
| L’élève compare l’appartenance au réseau de Debian 13 | ☐ | ☐ | |
| L’élève compare la visibilité de la VM sur le réseau réel | ☐ | ☐ | |
| L’élève indique que le mode pont demande l’autorisation du professeur | ☐ | ☐ | |
| La conclusion distingue clairement NAT et accès par pont | ☐ | ☐ | |

## 13. Remise en état des machines virtuelles

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le mode réseau final demandé par le professeur est noté | ☐ | ☐ | |
| Windows 11 Pro est remis dans le mode réseau demandé | ☐ | ☐ | |
| Zorin OS est remis dans le mode réseau demandé | ☐ | ☐ | |
| Les machines virtuelles sont arrêtées proprement | ☐ | ☐ | |
| Les fenêtres des VM ne sont pas fermées brutalement | ☐ | ☐ | |

## 14. Autonomie et méthode de travail

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| L’élève utilise le dossier technique pour chercher les informations | ☐ | ☐ | |
| L’élève ne demande pas directement la solution sans recherche préalable | ☐ | ☐ | |
| L’élève sait indiquer le chapitre consulté dans le dossier technique | ☐ | ☐ | |
| L’élève sait expliquer ce qu’il a fait | ☐ | ☐ | |
| L’élève sait expliquer ce qu’il a observé | ☐ | ☐ | |
| L’élève sait expliquer ce qui bloque en cas de problème | ☐ | ☐ | |

## 15. Formulation d’une demande d’aide

| Point attendu | Élève | Professeur | Observation |
|---|---|---|---|
| L’élève indique l’étape concernée | ☐ | ☐ | |
| L’élève indique la machine concernée | ☐ | ☐ | |
| L’élève indique le mode réseau utilisé | ☐ | ☐ | |
| L’élève indique la commande lancée | ☐ | ☐ | |
| L’élève indique le résultat observé | ☐ | ☐ | |
| L’élève indique la partie du dossier technique consultée | ☐ | ☐ | |
| L’élève formule une demande précise | ☐ | ☐ | |

## 16. Validation finale du palier 3

| Élément final à valider | Élève | Professeur | Observation |
|---|---|---|---|
| QCM validé à 100 % | ☐ | ☐ | |
| Fichier `palier3-resultats.txt` présent | ☐ | ☐ | |
| Relevés réseau de Debian 13 complets | ☐ | ☐ | |
| Tests Windows 11 Pro en mode NAT réalisés | ☐ | ☐ | |
| Tests Zorin OS en mode NAT réalisés | ☐ | ☐ | |
| Mode accès par pont testé ou mentionné comme non autorisé | ☐ | ☐ | |
| Comparaison NAT / accès par pont correcte | ☐ | ☐ | |
| Conclusion rédigée | ☐ | ☐ | |
| Machines virtuelles remises dans l’état demandé | ☐ | ☐ | |
| L’élève sait expliquer la différence entre NAT et accès par pont | ☐ | ☐ | |

Décision finale :

| État | Décision |
|---|---|
| ☐ | Palier 3 validé |
| ☐ | Palier 3 à reprendre |
| ☐ | Correction ciblée demandée |

Commentaire professeur :

....................................................................................................

....................................................................................................

....................................................................................................
