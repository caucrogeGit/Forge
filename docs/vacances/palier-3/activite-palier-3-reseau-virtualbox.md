# Activité du palier 3 : tester les modes réseau VirtualBox

## Principe de l’activité

Cette activité se réalise à partir du dossier technique du palier 3.

Le dossier technique contient les informations nécessaires pour réussir le travail demandé.

L’activité ne redonne pas les explications techniques.  
Vous devez donc consulter le dossier technique lorsque vous avez besoin d’une information.

## Condition de départ

Vous ne commencez cette activité que lorsque le QCM du palier 3 est validé à 100 %.

Le fichier `qcm-palier3.txt` doit être correct avant de passer aux manipulations.

## Travail demandé

Vous devez tester les communications réseau entre :

- la machine hôte Debian 13 ;
- la machine virtuelle Windows 11 Pro ;
- la machine virtuelle Zorin OS.

Vous devez tester plusieurs modes réseau VirtualBox :

- NAT ;
- accès par pont, uniquement si le professeur l’autorise ;
- réseau interne ;
- réseau privé hôte, si disponible.

Vous devez aussi relever les adresses IP, tester les communications avec `ping`, interpréter les résultats et expliquer ce que vous observez.

## Fichier de compte rendu

Vous devez créer un fichier texte nommé :

```text
activite-palier3.txt
```

Ce fichier doit contenir vos résultats.

Le fichier doit être organisé avec les titres suivants :

```text
Palier 3 : tests réseau VirtualBox

1. Identification des machines
2. Relevé des adresses IP
3. Calcul des réseaux
4. Test du mode NAT
5. Test du mode réseau interne
6. Test du mode accès par pont
7. Test du mode réseau privé hôte
8. Diagnostic en cas d’échec
9. Conclusion finale
```

Vous devez compléter ce fichier pendant l’activité.

## Demander de l’aide

Vous pouvez demander de l’aide, mais la demande doit être formulée correctement.

Avant d’appeler le professeur, vous devez pouvoir expliquer clairement :

- l’étape sur laquelle vous travaillez ;
- la machine concernée ;
- le mode réseau testé ;
- ce que vous avez déjà essayé ;
- ce que vous avez observé ;
- ce qui ne fonctionne pas ;
- la partie du dossier technique que vous avez consultée.

Une demande d’aide ne doit pas être formulée comme ceci :

> Je ne comprends rien.  
> Ça ne marche pas.  
> Je ne sais pas quoi faire.

Une demande d’aide doit être formulée comme ceci :

> Je suis à l’étape du test du réseau interne.  
> J’ai placé les deux machines virtuelles sur le même réseau interne.  
> J’ai configuré les adresses IP demandées.  
> J’ai vérifié les adresses avec les commandes indiquées dans le dossier technique.  
> Le ping de Zorin OS vers Windows 11 Pro ne répond pas.  
> J’ai consulté le chapitre sur le réseau interne et le chapitre sur le pare-feu Windows.  
> J’ai besoin d’aide pour savoir si le problème vient de l’adresse IP, du mode réseau ou du pare-feu.

Un technicien ne dit pas seulement que ça ne fonctionne pas.  
Il explique ce qu’il a fait, ce qu’il a observé et ce qu’il veut vérifier.

## Étape 1 : préparer l’environnement

Ouvrez VirtualBox.

Vérifiez que les deux machines virtuelles du palier 2 sont présentes :

- `VM-Windows-11-Pro` ;
- `VM-Zorin`.

Vérifiez que les deux machines virtuelles démarrent correctement.

Vérifiez que vous pouvez ouvrir la session avec le compte demandé.

Si une machine virtuelle ne démarre pas, ne commencez pas les tests réseau.

## Étape 2 : identifier les machines

Dans le fichier `activite-palier3.txt`, indiquez le nom de chaque machine.

À compléter :

```text
Machine hôte :
Nom de la machine :
Système :

Machine virtuelle Windows :
Nom de la machine :
Système :

Machine virtuelle Zorin OS :
Nom de la machine :
Système :
```

Utilisez les commandes du dossier technique pour relever les noms des machines.

## Étape 3 : relever les adresses IP de départ

Relevez les adresses IP des trois machines.

À compléter dans `activite-palier3.txt` :

```text
Adresses IP de départ

Machine hôte Debian 13 :
Commande utilisée :
Adresse IP relevée :

VM Windows 11 Pro :
Commande utilisée :
Adresse IP relevée :

VM Zorin OS :
Commande utilisée :
Adresse IP relevée :
```

Si une machine possède plusieurs adresses IP, notez celle qui correspond au test en cours.

## Étape 4 : calculer le réseau des adresses IP

Pour au moins deux adresses IP relevées, calculez le réseau correspondant.

Vous devez utiliser la méthode du tableau des puissances de 2 sur un octet présentée dans le dossier technique.

À compléter dans `activite-palier3.txt` :

```text
Calcul du réseau

Adresse IP 1 :
Masque :
Réseau obtenu :

Adresse IP 2 :
Masque :
Réseau obtenu :

Les deux machines sont-elles dans le même réseau logique ?
Réponse :
Justification :
```

Vous devez expliquer si les machines peuvent communiquer directement ou non.

## Étape 5 : tester le mode NAT

Placez les deux machines virtuelles en mode NAT.

Démarrez les deux machines virtuelles.

Relevez les adresses IP obtenues.

Testez les communications demandées.

À compléter dans `activite-palier3.txt` :

```text
Mode NAT

VM Windows 11 Pro :
Adresse IP :
Commande utilisée :

VM Zorin OS :
Adresse IP :
Commande utilisée :

Test Zorin OS vers Internet :
Commande utilisée :
Résultat :

Test Windows 11 Pro vers Internet :
Commande utilisée :
Résultat :

Test Zorin OS vers Windows 11 Pro :
Commande utilisée :
Résultat :

Test Windows 11 Pro vers Zorin OS :
Commande utilisée :
Résultat :

Conclusion sur le mode NAT :
```

Votre conclusion doit expliquer ce qui fonctionne et ce qui ne fonctionne pas.

## Étape 6 : tester le mode réseau interne

Placez les deux machines virtuelles sur le même réseau interne VirtualBox.

Utilisez le nom de réseau interne demandé dans le dossier technique.

Configurez les adresses IP demandées dans le dossier technique.

Vérifiez les adresses IP après configuration.

À compléter dans `activite-palier3.txt` :

```text
Mode réseau interne

Nom du réseau interne utilisé :

VM Zorin OS :
Adresse IP configurée :
Masque :
Commande de vérification :
Adresse IP observée :

VM Windows 11 Pro :
Adresse IP configurée :
Masque :
Commande de vérification :
Adresse IP observée :

Calcul du réseau Zorin OS :
Calcul du réseau Windows 11 Pro :

Les deux machines sont-elles dans le même réseau logique ?
Réponse :

Test Zorin OS vers Windows 11 Pro :
Commande utilisée :
Résultat :

Test Windows 11 Pro vers Zorin OS :
Commande utilisée :
Résultat :

Conclusion sur le mode réseau interne :
```

Si le ping vers Windows 11 Pro échoue, consultez le chapitre sur le pare-feu Windows avant de conclure.

Ne désactivez pas le pare-feu Windows sans autorisation du professeur.

## Étape 7 : tester le mode accès par pont

Cette étape se fait uniquement avec l’autorisation du professeur.

Le mode accès par pont connecte la machine virtuelle au réseau réel de la salle.

Placez une machine virtuelle en mode accès par pont.

Relevez son adresse IP.

Comparez l’adresse IP de la machine virtuelle avec celle de la machine hôte.

À compléter dans `activite-palier3.txt` :

```text
Mode accès par pont

Machine virtuelle testée :
Adresse IP de la machine hôte :
Adresse IP de la machine virtuelle :
Masque :

La machine virtuelle est-elle dans le même réseau que l’hôte ?
Réponse :
Justification :

Test vers la passerelle :
Commande utilisée :
Résultat :

Test vers Internet :
Commande utilisée :
Résultat :

La machine virtuelle semble-t-elle visible comme une machine du réseau réel ?
Réponse :

Conclusion sur le mode accès par pont :
```

Ne modifiez pas les paramètres du réseau réel de la salle.

## Étape 8 : tester le mode réseau privé hôte

Cette étape se fait uniquement si le mode réseau privé hôte est disponible sur le poste.

Si le mode n’est pas disponible, écrivez dans votre compte rendu :

```text
Le mode réseau privé hôte n’est pas disponible sur ce poste.
```

Si le mode est disponible, placez une machine virtuelle en réseau privé hôte.

Relevez les adresses IP.

Testez la communication entre l’hôte Debian 13 et la machine virtuelle.

À compléter dans `activite-palier3.txt` :

```text
Mode réseau privé hôte

Mode disponible :
Oui / Non

Machine virtuelle testée :
Adresse IP de l’hôte sur le réseau privé hôte :
Adresse IP de la machine virtuelle :
Masque :

Test hôte Debian 13 vers machine virtuelle :
Commande utilisée :
Résultat :

Test machine virtuelle vers hôte Debian 13 :
Commande utilisée :
Résultat :

Test machine virtuelle vers Internet :
Commande utilisée :
Résultat :

Conclusion sur le mode réseau privé hôte :
```

## Étape 9 : diagnostiquer un échec de communication

Choisissez un test qui n’a pas fonctionné ou qui n’a pas donné le résultat attendu.

Analysez le problème avec la méthode de diagnostic du dossier technique.

À compléter dans `activite-palier3.txt` :

```text
Diagnostic d’un problème réseau

Test concerné :
Résultat observé :

Mode réseau utilisé :
Carte réseau virtuelle activée :
Adresse IP de la machine source :
Adresse IP de la machine cible :
Masque utilisé :
Même réseau logique :
Commande utilisée :
Réponse obtenue :

Hypothèse 1 :
Hypothèse 2 :
Correction ou vérification réalisée :
Résultat après correction :

Conclusion du diagnostic :
```

Si tous les tests ont fonctionné, choisissez un cas où la communication était impossible normalement, puis expliquez pourquoi.

## Étape 10 : comparer les modes réseau

Complétez une synthèse dans votre fichier `activite-palier3.txt`.

```text
Comparaison des modes réseau

Mode NAT :
Ce qui fonctionne :
Ce qui ne fonctionne pas :
Utilité principale :

Mode réseau interne :
Ce qui fonctionne :
Ce qui ne fonctionne pas :
Utilité principale :

Mode accès par pont :
Ce qui fonctionne :
Ce qui ne fonctionne pas :
Utilité principale :

Mode réseau privé hôte :
Ce qui fonctionne :
Ce qui ne fonctionne pas :
Utilité principale :
```

## Étape 11 : conclusion finale

Rédigez une conclusion simple.

Votre conclusion doit répondre aux questions suivantes :

- Quel mode permet le plus simplement d’accéder à Internet ?
- Quel mode permet d’isoler deux machines virtuelles du réseau réel ?
- Quel mode rend une machine virtuelle visible sur le réseau réel ?
- Pourquoi faut-il vérifier les adresses IP avant de conclure ?
- Pourquoi un ping qui échoue ne suffit pas toujours à prouver que le réseau est mal configuré ?

À compléter dans `activite-palier3.txt` :

```text
Conclusion finale

....................................................................
....................................................................
....................................................................
....................................................................
....................................................................
```

## Résultat attendu

À la fin de l’activité :

- le fichier `activite-palier3.txt` existe ;
- les noms des machines sont relevés ;
- les adresses IP sont relevées ;
- au moins deux calculs de réseau sont réalisés ;
- le mode NAT est testé ;
- le mode réseau interne est testé ;
- le mode accès par pont est testé si le professeur l’autorise ;
- le mode réseau privé hôte est testé si disponible ;
- les résultats des tests ping sont notés ;
- au moins un diagnostic est expliqué ;
- une conclusion finale est rédigée.

## Validation du palier

Le palier 3 est validé lorsque :

- le QCM du palier 3 est validé à 100 % ;
- le fichier `activite-palier3.txt` est complet ;
- les tests réseau ont été réalisés ;
- les calculs de réseau sont justes ;
- les conclusions sont cohérentes ;
- l’élève sait expliquer ses résultats oralement.

Si une partie est incomplète ou incohérente, le palier n’est pas terminé.

Vous devez corriger le travail, refaire les tests nécessaires, puis demander une nouvelle validation.
