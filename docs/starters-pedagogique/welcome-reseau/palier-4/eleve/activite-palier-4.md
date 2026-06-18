# Activité du palier 4 : configurer un réseau interne et diagnostiquer une communication

## Principe de l’activité

Cette activité se réalise à partir du dossier technique du palier 4.

Le dossier technique contient les informations nécessaires pour configurer un réseau interne entre deux machines virtuelles, attribuer des adresses IP fixes, tester la communication et diagnostiquer un problème simple.

L’activité ne redonne pas les explications techniques.
Vous devez donc consulter le dossier technique lorsque vous avez besoin d’une information.

## Travail demandé

Vous devez faire communiquer directement deux machines virtuelles entre elles dans un réseau interne VirtualBox.

Les deux machines virtuelles utilisées sont :

* Windows 11 Pro ;
* Zorin OS.

La machine hôte Debian 13 sert à lancer VirtualBox et à modifier les paramètres des machines virtuelles.
Elle n’est pas la machine principale à tester dans ce palier.

## Condition obligatoire avant de commencer

Vous ne commencez cette activité que lorsque le QCM du palier 4 est validé à 100 %.

Le fichier de réponse du QCM doit être nommé :

```text
qcm-palier4.txt
```

Le QCM doit être validé par le professeur avant le début de l’activité.

## Matériel et fichiers nécessaires

Avant de commencer, vérifiez que vous disposez des éléments suivants :

* VirtualBox installé sur la machine hôte Debian 13 ;
* une machine virtuelle Windows 11 Pro fonctionnelle ;
* une machine virtuelle Zorin OS fonctionnelle ;
* le dossier technique du palier 4 ;
* la checklist de validation du palier 4 ;
* un fichier texte pour noter vos résultats.

## Traces attendues

À la fin de l’activité, vous devez pouvoir présenter :

* les deux VM configurées en réseau interne ;
* le nom du réseau interne utilisé ;
* l’adresse IP fixe de Zorin OS ;
* l’adresse IP fixe de Windows 11 Pro ;
* le résultat du test de Zorin OS vers Windows 11 Pro ;
* le résultat du test de Windows 11 Pro vers Zorin OS ;
* une conclusion courte ;
* la checklist de validation complétée.

Vous devez noter vos résultats dans un fichier nommé :

```text
palier4-resultats.txt
```

## Demander de l’aide

Vous pouvez demander de l’aide, mais la demande doit être formulée correctement.

Avant d’appeler le professeur, vous devez pouvoir expliquer clairement :

* l’étape sur laquelle vous travaillez ;
* la machine concernée ;
* ce que vous avez déjà essayé ;
* ce que vous avez observé ;
* ce qui ne fonctionne pas ;
* la partie du dossier technique que vous avez consultée.

Une demande d’aide ne doit pas être formulée comme ceci :

> Ça ne marche pas.

Une demande d’aide doit être formulée comme ceci :

> Je travaille sur le test de Zorin OS vers Windows 11 Pro.
> Les deux VM sont en réseau interne avec le nom `reseau-2tne`.
> Zorin OS a l’adresse `192.168.10.10`.
> Windows a l’adresse `192.168.10.20`.
> J’ai lancé `ping -c 4 192.168.10.20` depuis Zorin OS.
> Je n’ai pas de réponse.
> J’ai consulté le chapitre sur le pare-feu Windows.
> J’ai besoin d’aide pour vérifier si Windows bloque le ping.

Un technicien explique ce qu’il a fait, ce qu’il a observé et ce qu’il veut vérifier.

## Étape 1 : préparer les deux machines virtuelles

Ouvrez VirtualBox depuis la machine hôte Debian 13.

Vérifiez que les deux machines virtuelles existent :

* Windows 11 Pro ;
* Zorin OS.

Les deux machines doivent être arrêtées proprement avant de modifier leur configuration réseau.

Dans votre fichier `palier4-resultats.txt`, notez :

```text
Étape 1 : préparation des VM
Windows 11 Pro présente : oui / non
Zorin OS présente : oui / non
Les deux VM sont arrêtées proprement : oui / non
```

## Étape 2 : configurer le réseau interne dans VirtualBox

Configurez les deux machines virtuelles en mode réseau interne.

Le nom du réseau interne à utiliser est :

```text
reseau-2tne
```

Les deux machines virtuelles doivent utiliser exactement le même nom.

Dans votre fichier `palier4-resultats.txt`, notez :

```text
Étape 2 : configuration VirtualBox
Windows 11 Pro : mode réseau =
Windows 11 Pro : nom du réseau interne =
Zorin OS : mode réseau =
Zorin OS : nom du réseau interne =
Les deux noms sont strictement identiques : oui / non
```

## Étape 3 : configurer l’adresse IP fixe de Zorin OS

Démarrez la machine virtuelle Zorin OS.

Configurez l’adresse IP fixe demandée dans le dossier technique.

Vérifiez ensuite la configuration réseau depuis Zorin OS.

Dans votre fichier `palier4-resultats.txt`, notez :

```text
Étape 3 : configuration IP de Zorin OS
Nom de la machine =
Adresse IP attendue =
Adresse IP relevée =
Masque attendu =
Masque relevé =
Passerelle =
DNS =
Configuration conforme : oui / non
```

## Étape 4 : configurer l’adresse IP fixe de Windows 11 Pro

Démarrez la machine virtuelle Windows 11 Pro.

Configurez l’adresse IP fixe demandée dans le dossier technique.

Vérifiez ensuite la configuration réseau depuis Windows 11 Pro.

Dans votre fichier `palier4-resultats.txt`, notez :

```text
Étape 4 : configuration IP de Windows 11 Pro
Nom de la machine =
Adresse IP attendue =
Adresse IP relevée =
Masque attendu =
Masque relevé =
Passerelle =
DNS =
Configuration conforme : oui / non
```

## Étape 5 : vérifier le même réseau logique

Comparez les adresses IP et les masques des deux machines virtuelles.

Vous devez vérifier que les deux machines appartiennent au même réseau logique.

Dans votre fichier `palier4-resultats.txt`, complétez :

```text
Étape 5 : vérification du réseau logique
Réseau obtenu pour Zorin OS =
Réseau obtenu pour Windows 11 Pro =
Les deux VM sont dans le même réseau logique : oui / non
Les deux VM ont des adresses IP différentes : oui / non
```

## Étape 6 : tester la communication de Zorin OS vers Windows 11 Pro

Depuis Zorin OS, testez la communication vers Windows 11 Pro.

Utilisez la commande adaptée à Linux.

Dans votre fichier `palier4-resultats.txt`, notez :

```text
Étape 6 : test Zorin OS vers Windows 11 Pro
Machine source =
Machine cible =
Adresse IP testée =
Commande utilisée =
Résultat obtenu = réussite / échec
Observation =
```

Si le test échoue, ne modifiez pas les paramètres au hasard.
Consultez la méthode de diagnostic du dossier technique.

## Étape 7 : tester la communication de Windows 11 Pro vers Zorin OS

Depuis Windows 11 Pro, testez la communication vers Zorin OS.

Utilisez la commande adaptée à Windows.

Dans votre fichier `palier4-resultats.txt`, notez :

```text
Étape 7 : test Windows 11 Pro vers Zorin OS
Machine source =
Machine cible =
Adresse IP testée =
Commande utilisée =
Résultat obtenu = réussite / échec
Observation =
```

Si le test échoue, ne modifiez pas les paramètres au hasard.
Consultez la méthode de diagnostic du dossier technique.

## Étape 8 : analyser les résultats

Comparez les deux tests.

Dans votre fichier `palier4-resultats.txt`, complétez :

```text
Étape 8 : analyse
Zorin OS vers Windows 11 Pro = réussite / échec
Windows 11 Pro vers Zorin OS = réussite / échec
Les deux VM communiquent correctement = oui / non
Une vérification du pare-feu Windows est nécessaire = oui / non
```

Si une vérification du pare-feu Windows est nécessaire, demandez au professeur.

Il ne faut pas désactiver le pare-feu Windows sans consigne.

## Étape 9 : établir la conclusion

Rédigez une conclusion courte dans votre fichier `palier4-resultats.txt`.

La conclusion doit indiquer :

* si les deux VM sont correctement configurées ;
* si elles sont dans le même réseau logique ;
* si la communication fonctionne ;
* si un problème a été identifié ;
* si une aide du professeur a été nécessaire.

Modèle possible :

```text
Conclusion :
Les deux machines virtuelles sont configurées en réseau interne avec le nom ...
Zorin OS utilise l’adresse ...
Windows 11 Pro utilise l’adresse ...
Les deux machines appartiennent au réseau ...
Le test de communication est ...
Le palier peut / ne peut pas être validé car ...
```

## Étape 10 : compléter la checklist de validation

Complétez la colonne élève de la checklist de validation du palier 4.

Vous devez ensuite demander la validation au professeur.

Le professeur vérifie :

* le QCM ;
* la configuration VirtualBox ;
* les adresses IP ;
* les tests de communication ;
* le fichier `palier4-resultats.txt` ;
* votre capacité à expliquer ce que vous avez fait.

## Résultat attendu

À la fin de l’activité :

* les deux VM sont en réseau interne ;
* le réseau interne utilisé est `reseau-2tne` ;
* Zorin OS utilise l’adresse IP attendue ;
* Windows 11 Pro utilise l’adresse IP attendue ;
* les deux VM sont dans le même réseau logique ;
* au moins un test de communication est analysé correctement ;
* la conclusion est rédigée ;
* la checklist est complétée.

## Validation du palier

Le palier 4 est validé lorsque :

* le QCM est correct à 100 % ;
* l’activité est réalisée ;
* les traces attendues sont présentes ;
* la checklist est complétée par l’élève ;
* le professeur valide les points techniques ;
* l’élève sait expliquer sa configuration et ses tests.