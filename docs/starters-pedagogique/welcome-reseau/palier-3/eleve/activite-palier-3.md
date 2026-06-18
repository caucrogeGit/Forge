# Activité du palier 3 : relever les informations réseau et tester les modes NAT et accès par pont

## Principe de l’activité

Cette activité se réalise à partir du dossier technique du palier 3.

Le dossier technique contient les informations nécessaires pour réussir le travail demandé.

L’activité ne redonne pas les explications techniques. Vous devez donc consulter le dossier technique lorsque vous avez besoin d’une information.

Dans ce palier, vous allez relever les informations réseau de la machine hôte Debian 13 et de deux machines virtuelles, puis comparer le comportement réseau en mode NAT et en mode accès par pont.

Vous ne configurez pas d’adresse IP fixe dans cette activité.

Le réseau interne entre deux machines virtuelles sera étudié dans le palier suivant.

## Travail demandé

Vous devez vérifier le fonctionnement réseau de deux machines virtuelles VirtualBox :

* une machine virtuelle Windows 11 Pro ;
* une machine virtuelle Zorin OS.

Pour chaque machine virtuelle, vous devez tester :

* le mode NAT ;
* le mode accès par pont, uniquement si le professeur l’autorise.

Vous devez relever les informations réseau, faire les tests demandés, compléter vos tableaux de résultats, puis demander la validation du professeur.

## Matériel et fichiers nécessaires

Avant de commencer, vérifiez que vous disposez des éléments suivants :

| Élément nécessaire | Présent |
|---|---|
| Poste hôte sous Debian 13 | ☐ |
| VirtualBox fonctionnel | ☐ |
| Machine virtuelle Windows 11 Pro installée | ☐ |
| Machine virtuelle Zorin OS installée | ☐ |
| Dossier technique du palier 3 accessible | ☐ |
| QCM du palier 3 validé à 100 % | ☐ |
| Checklist de validation du palier 3 accessible | ☐ |

## Fichier de résultats à créer

Vous devez créer un fichier texte pour conserver vos résultats.

Nom du fichier attendu :

```text
palier3-resultats.txt
```

Ce fichier doit contenir :

* les informations relevées sur la machine hôte Debian 13 ;
* les informations relevées sur la VM Windows 11 Pro en mode NAT ;
* les informations relevées sur la VM Zorin OS en mode NAT ;
* les informations relevées en mode accès par pont si ce mode est autorisé ;
* les résultats des tests ;
* une conclusion courte.

## Traces attendues

À la fin de l’activité, vous devez pouvoir présenter :

| Trace attendue | Présente |
|---|---|
| Fichier `palier3-resultats.txt` | ☐ |
| Informations réseau de Debian 13 relevées | ☐ |
| Informations réseau de Windows 11 Pro relevées en mode NAT | ☐ |
| Informations réseau de Zorin OS relevées en mode NAT | ☐ |
| Test Internet ou ping extérieur réalisé en mode NAT | ☐ |
| Comparaison NAT / accès par pont réalisée si le mode pont est autorisé | ☐ |
| Conclusion claire sur les deux modes réseau | ☐ |
| Checklist de validation complétée | ☐ |

## Demander de l’aide

Vous pouvez demander de l’aide, mais la demande doit être formulée correctement.

Avant d’appeler le professeur, vous devez pouvoir expliquer clairement :

* l’étape sur laquelle vous travaillez ;
* la machine concernée ;
* le mode réseau utilisé ;
* ce que vous avez déjà essayé ;
* ce que vous avez observé ;
* ce qui ne fonctionne pas ;
* la partie du dossier technique que vous avez consultée.

Une demande d’aide ne doit pas être formulée comme ceci :

> Je ne comprends rien.  
> Ça ne marche pas.  
> Je ne sais pas quoi faire.

Une demande d’aide doit être formulée comme ceci :

> Je suis à l’étape de test du mode NAT sur la VM Zorin OS.  
> J’ai réglé l’adaptateur réseau sur NAT dans VirtualBox.  
> J’ai relevé l’adresse IP avec `hostname -I`.  
> J’ai lancé `ping -c 4 8.8.8.8`, mais je n’obtiens pas de réponse.  
> J’ai consulté le chapitre 10 du dossier technique.  
> J’ai besoin d’aide pour vérifier si le problème vient du réseau ou de la configuration de la VM.

Un technicien ne dit pas seulement que ça ne fonctionne pas. Il explique ce qu’il a fait, ce qu’il a observé et ce qu’il veut vérifier.

## Étape 1 : vérifier que le QCM est validé

Avant de commencer l’activité, le QCM du palier 3 doit être validé à 100 %.

| Point à vérifier | Oui | Non |
|---|---|---|
| Le fichier de réponse du QCM existe | ☐ | ☐ |
| Le format demandé est respecté | ☐ | ☐ |
| Le QCM est validé à 100 % | ☐ | ☐ |

Si le QCM n’est pas validé à 100 %, vous ne commencez pas cette activité.

## Étape 2 : relever les informations réseau de la machine hôte Debian 13

Sur la machine hôte Debian 13, ouvrez un terminal.

Relevez les informations demandées dans votre fichier `palier3-resultats.txt`.

| Information à relever | Commande à utiliser | Résultat obtenu |
|---|---|---|
| Nom de la machine | `hostname` | |
| Adresse IP | `hostname -I` ou `ip a` | |
| Passerelle | `ip route` | |
| Interface réseau utilisée | `ip a` | |

Questions à traiter dans votre fichier de résultats :

1. Quel est le nom de la machine hôte ?
2. Quelle est l’adresse IP principale de Debian 13 ?
3. Quelle est l’adresse de la passerelle ?
4. Quelle interface réseau semble utilisée ?

## Étape 3 : placer la VM Windows 11 Pro en mode NAT

La machine virtuelle doit être arrêtée proprement avant de modifier son mode réseau.

Dans VirtualBox :

1. sélectionnez la VM Windows 11 Pro ;
2. ouvrez **Configuration** ;
3. ouvrez **Réseau** ;
4. choisissez **Adaptateur 1** ;
5. vérifiez que **Activer la carte réseau** est coché ;
6. sélectionnez **NAT** dans **Mode d’accès réseau** ;
7. validez avec **OK** ;
8. démarrez la machine virtuelle.

Dans Windows 11 Pro, ouvrez l’invite de commandes ou le terminal Windows.

Relevez les informations suivantes :

| Information à relever | Commande à utiliser | Résultat obtenu |
|---|---|---|
| Nom de la machine | `hostname` | |
| Adresse IPv4 | `ipconfig` | |
| Masque | `ipconfig` | |
| Passerelle par défaut | `ipconfig` | |

Dans votre fichier de résultats, indiquez si l’adresse IP de la VM Windows semble être dans le même réseau que l’adresse IP de Debian 13.

## Étape 4 : tester la connexion réseau de Windows 11 Pro en mode NAT

Dans Windows 11 Pro, lancez le test suivant :

```text
ping -n 4 8.8.8.8
```

Complétez le tableau :

| Test | Résultat attendu | Résultat obtenu |
|---|---|---|
| Ping vers `8.8.8.8` | Réponse si l’hôte a Internet | |
| Nombre de paquets envoyés | 4 | |
| Nombre de paquets reçus | 4 si le test fonctionne | |
| Perte de paquets | 0 % si le test fonctionne | |

Dans votre fichier de résultats, répondez aux questions suivantes :

1. La VM Windows 11 Pro reçoit-elle une adresse IP en mode NAT ?
2. Le ping vers `8.8.8.8` fonctionne-t-il ?
3. La VM Windows 11 Pro semble-t-elle directement visible sur le réseau réel ?
4. Quel élément donne généralement l’adresse IP à la VM en mode NAT ?

## Étape 5 : placer la VM Zorin OS en mode NAT

La machine virtuelle doit être arrêtée proprement avant de modifier son mode réseau.

Dans VirtualBox :

1. sélectionnez la VM Zorin OS ;
2. ouvrez **Configuration** ;
3. ouvrez **Réseau** ;
4. choisissez **Adaptateur 1** ;
5. vérifiez que **Activer la carte réseau** est coché ;
6. sélectionnez **NAT** dans **Mode d’accès réseau** ;
7. validez avec **OK** ;
8. démarrez la machine virtuelle.

Dans Zorin OS, ouvrez un terminal.

Relevez les informations suivantes :

| Information à relever | Commande à utiliser | Résultat obtenu |
|---|---|---|
| Nom de la machine | `hostname` | |
| Adresse IP | `hostname -I` ou `ip a` | |
| Passerelle | `ip route` | |
| Interface réseau utilisée | `ip a` | |

Dans votre fichier de résultats, indiquez si l’adresse IP de la VM Zorin OS semble être dans le même réseau que l’adresse IP de Debian 13.

## Étape 6 : tester la connexion réseau de Zorin OS en mode NAT

Dans Zorin OS, lancez le test suivant :

```bash
ping -c 4 8.8.8.8
```

Complétez le tableau :

| Test | Résultat attendu | Résultat obtenu |
|---|---|---|
| Ping vers `8.8.8.8` | Réponse si l’hôte a Internet | |
| Nombre de paquets envoyés | 4 | |
| Nombre de paquets reçus | 4 si le test fonctionne | |
| Perte de paquets | 0 % si le test fonctionne | |

Dans votre fichier de résultats, répondez aux questions suivantes :

1. La VM Zorin OS reçoit-elle une adresse IP en mode NAT ?
2. Le ping vers `8.8.8.8` fonctionne-t-il ?
3. La VM Zorin OS semble-t-elle directement visible sur le réseau réel ?
4. Quel est l’intérêt principal du mode NAT ?

## Étape 7 : demander l’autorisation pour tester le mode accès par pont

Le mode accès par pont connecte la machine virtuelle au réseau réel de la salle.

Vous ne devez pas utiliser ce mode sans autorisation.

Demandez au professeur si le test du mode accès par pont est autorisé.

| Question | Réponse |
|---|---|
| Le professeur autorise-t-il le mode accès par pont ? | Oui / Non |
| Machine virtuelle à tester en accès par pont | Windows 11 Pro / Zorin OS / Les deux |
| Carte réseau réelle à utiliser | Ethernet / Wi-Fi / Autre |

Si le professeur n’autorise pas le mode accès par pont, passez directement à l’étape 11.

## Étape 8 : tester Windows 11 Pro en mode accès par pont

Cette étape est réalisée uniquement si le professeur l’autorise.

La machine virtuelle doit être arrêtée proprement avant de modifier son mode réseau.

Dans VirtualBox :

1. sélectionnez la VM Windows 11 Pro ;
2. ouvrez **Configuration** ;
3. ouvrez **Réseau** ;
4. choisissez **Adaptateur 1** ;
5. vérifiez que **Activer la carte réseau** est coché ;
6. sélectionnez **Accès par pont** ;
7. choisissez la carte réseau réelle utilisée par la machine hôte ;
8. validez avec **OK** ;
9. démarrez la VM.

Dans Windows 11 Pro, relevez les informations suivantes :

| Information à relever | Commande à utiliser | Résultat obtenu |
|---|---|---|
| Nom de la machine | `hostname` | |
| Adresse IPv4 | `ipconfig` | |
| Masque | `ipconfig` | |
| Passerelle par défaut | `ipconfig` | |

Testez la passerelle relevée avec :

```text
ping -n 4 adresse_de_la_passerelle
```

Complétez :

| Test | Résultat obtenu |
|---|---|
| Ping vers la passerelle | |
| Adresse IP de Windows dans le même réseau que Debian 13 | Oui / Non |
| Windows semble intégré au réseau réel | Oui / Non |

## Étape 9 : tester Zorin OS en mode accès par pont

Cette étape est réalisée uniquement si le professeur l’autorise.

La machine virtuelle doit être arrêtée proprement avant de modifier son mode réseau.

Dans VirtualBox :

1. sélectionnez la VM Zorin OS ;
2. ouvrez **Configuration** ;
3. ouvrez **Réseau** ;
4. choisissez **Adaptateur 1** ;
5. vérifiez que **Activer la carte réseau** est coché ;
6. sélectionnez **Accès par pont** ;
7. choisissez la carte réseau réelle utilisée par la machine hôte ;
8. validez avec **OK** ;
9. démarrez la VM.

Dans Zorin OS, relevez les informations suivantes :

| Information à relever | Commande à utiliser | Résultat obtenu |
|---|---|---|
| Nom de la machine | `hostname` | |
| Adresse IP | `hostname -I` ou `ip a` | |
| Passerelle | `ip route` | |
| Interface réseau utilisée | `ip a` | |

Testez la passerelle relevée avec :

```bash
ping -c 4 adresse_de_la_passerelle
```

Complétez :

| Test | Résultat obtenu |
|---|---|
| Ping vers la passerelle | |
| Adresse IP de Zorin OS dans le même réseau que Debian 13 | Oui / Non |
| Zorin OS semble intégré au réseau réel | Oui / Non |

## Étape 10 : comparer les résultats NAT et accès par pont

Complétez le tableau dans votre fichier `palier3-resultats.txt`.

| Point comparé | Mode NAT | Mode accès par pont |
|---|---|---|
| Qui donne l’adresse IP à la VM ? | | |
| La VM reçoit-elle une adresse IP ? | | |
| La VM peut-elle accéder à Internet ? | | |
| La VM est-elle dans le même réseau que Debian 13 ? | | |
| La VM semble-t-elle visible sur le réseau réel ? | | |
| Ce mode est-il simple à utiliser ? | | |
| Ce mode demande-t-il une autorisation du professeur ? | | |

Conclusion à rédiger :

```text
En mode NAT, j’observe que...

En mode accès par pont, j’observe que...

La différence principale entre les deux modes est...
```

## Étape 11 : remettre les machines virtuelles dans l’état demandé

À la fin de l’activité, demandez au professeur quel mode réseau doit être conservé.

Sauf consigne contraire, remettez les machines virtuelles en mode NAT.

| Machine virtuelle | Mode réseau final demandé | Mode réseau réellement configuré |
|---|---|---|
| Windows 11 Pro | NAT | |
| Zorin OS | NAT | |

Arrêtez proprement les machines virtuelles.

Ne fermez pas brutalement les fenêtres des VM.

## Étape 12 : compléter la checklist de validation

Avant d’appeler le professeur, complétez la checklist de validation du palier 3.

Vous devez cocher uniquement ce que vous avez réellement vérifié.

| Point à auto-vérifier | Élève |
|---|---|
| J’ai relevé les informations réseau de Debian 13 | ☐ |
| J’ai testé Windows 11 Pro en mode NAT | ☐ |
| J’ai testé Zorin OS en mode NAT | ☐ |
| J’ai comparé les adresses IP obtenues | ☐ |
| J’ai demandé l’autorisation avant d’utiliser le mode accès par pont | ☐ |
| J’ai testé le mode accès par pont si le professeur l’a autorisé | ☐ |
| J’ai rédigé une conclusion | ☐ |
| J’ai remis les VM dans l’état demandé | ☐ |
| Mon fichier `palier3-resultats.txt` est complet | ☐ |

## Résultat attendu

À la fin de l’activité :

* le QCM du palier 3 est validé à 100 % ;
* les informations réseau de Debian 13 sont relevées ;
* les informations réseau de Windows 11 Pro sont relevées en mode NAT ;
* les informations réseau de Zorin OS sont relevées en mode NAT ;
* les tests de communication demandés sont réalisés ;
* le mode accès par pont est testé uniquement si le professeur l’autorise ;
* les différences entre NAT et accès par pont sont expliquées simplement ;
* la checklist de validation est complétée ;
* le professeur peut valider ou demander une correction ciblée.

## Validation du palier

Le palier 3 est validé lorsque :

| Élément à valider | Validation |
|---|---|
| QCM validé à 100 % | ☐ |
| Fichier `palier3-resultats.txt` présent | ☐ |
| Relevés réseau complets | ☐ |
| Tests NAT réalisés | ☐ |
| Test accès par pont réalisé ou mentionné comme non autorisé | ☐ |
| Comparaison NAT / accès par pont correcte | ☐ |
| Conclusion rédigée | ☐ |
| Checklist complétée | ☐ |
| Validation professeur obtenue | ☐ |

Vous ne passez pas au palier suivant tant que ce palier n’est pas terminé et vérifié.