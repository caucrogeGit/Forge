# Palier 1 : dossier technique

# Fabriquer et tester un câble Ethernet droit en norme T568B

## Objectif du dossier technique

Ce dossier donne les connaissances nécessaires pour fabriquer un câble Ethernet droit et le tester correctement.

À la fin de cette lecture, vous devez être capable de comprendre :

* à quoi sert un câble Ethernet RJ45 ;
* comment est constitué un câble réseau ;
* pourquoi les fils doivent être placés dans un ordre précis ;
* ce qu’est la norme T568B ;
* ce qu’est un câble droit ;
* comment utiliser un testeur RJ45 ;
* comment reconnaître un câble conforme ou non conforme.

## 1. Le réseau local

Un réseau informatique permet à plusieurs équipements d’échanger des informations.

Exemples d’équipements reliés à un réseau :

* ordinateur ;
* imprimante ;
* serveur ;
* switch ;
* routeur ;
* borne Wi-Fi.

Un réseau local est un réseau limité à un espace proche.

Exemples :

* une salle informatique ;
* un atelier ;
* un lycée ;
* une maison ;
* une entreprise.

Dans une salle informatique, les postes fixes sont souvent reliés avec un câble Ethernet RJ45. Cette liaison est généralement plus stable qu’une liaison Wi-Fi.

<p>
  <img src="../images/reseau-local.png" alt="Le réseau local" width="60%">
</p>

## 2. Le rôle du câble Ethernet RJ45

Le câble Ethernet RJ45 sert à relier physiquement un équipement au réseau.

Il peut relier :

* un ordinateur à une prise murale ;
* un ordinateur à un switch ;
* une imprimante réseau à un switch ;
* un serveur à un switch ;
* un switch à un routeur.

Le câble RJ45 transporte les données sous forme de signaux électriques.

Il ne donne pas une adresse IP.
Il ne configure pas le réseau.
Il permet seulement au signal de passer entre deux équipements.



## 3. Connexion physique et configuration logique

Pour qu’une machine communique sur un réseau, deux conditions sont nécessaires.

!<p>
  <img src="../images/reseau-physique-logique.png" alt="Connexion physique et configuration logique" width="60%">
</p>

## 3.1 La connexion physique

La connexion physique concerne le matériel.

Elle dépend de plusieurs éléments :

* le câble RJ45 ;
* le connecteur RJ45 ;
* la prise réseau ;
* la carte réseau ;
* le switch ;
* les voyants de liaison.

Si le câble est mal fabriqué, coupé, mal serti ou mal branché, la communication peut échouer.

Même avec une bonne adresse IP, un câble défectueux empêche la communication.

## 3.2 La configuration logique

La configuration logique concerne les paramètres réseau.

Elle comprend par exemple :

* l’adresse IP ;
* le masque de réseau ;
* la passerelle ;
* le DNS.

Même avec un bon câble, une mauvaise adresse IP peut empêcher la communication.

## 3.3 Règle de diagnostic

Quand un réseau ne fonctionne pas, on vérifie d’abord la partie physique.

Ordre de vérification :

1. vérifier que le câble est branché ;
2. vérifier les voyants réseau ;
3. vérifier que le câble est testé conforme ;
4. vérifier l’adresse IP ;
5. tester la communication.

Dans ce palier, le travail porte uniquement sur la partie physique : le câble Ethernet RJ45.

## 4. Constitution d’un câble Ethernet

Un câble Ethernet cuivre est composé de plusieurs éléments.

| Élément              | Rôle                                         |
| -------------------- | -------------------------------------------- |
| Gaine extérieure     | Protège les fils                             |
| Fils conducteurs     | Transportent les signaux électriques         |
| Paires torsadées     | Réduisent les perturbations électriques      |
| Connecteur RJ45      | Permet de brancher le câble à un équipement  |
| Contacts métalliques | Assurent la liaison électrique avec la prise |

Un câble Ethernet contient généralement 8 fils.

Ces 8 fils sont regroupés en 4 paires torsadées.

Les couleurs des fils sont :

* blanc-orange ;
* orange ;
* blanc-vert ;
* vert ;
* blanc-bleu ;
* bleu ;
* blanc-marron ;
* marron.

Chaque fil doit être placé au bon endroit dans le connecteur RJ45.

<p>
  <img src="../images/constitution-cable-ethernet.png" alt="Constitution d’un câble Ethernet" width="60%">
</p>

## 5. Pourquoi les fils sont torsadés

Dans un câble réseau, les fils sont regroupés par paires.

Chaque paire est torsadée.

Le torsadage permet de limiter les perturbations électriques.

Ces perturbations peuvent venir :

* d’un autre câble ;
* d’une alimentation électrique ;
* d’un moteur ;
* d’un appareil électronique ;
* d’un environnement technique perturbé.

Il ne faut donc pas dévriller les fils sur une trop grande longueur.

Plus les fils sont dévrillés, plus le câble devient sensible aux perturbations.

Lors de la fabrication, il faut dévriller seulement ce qui est nécessaire pour insérer les fils dans le connecteur.

## 6. Le connecteur RJ45

Le connecteur RJ45 possède 8 emplacements pour les 8 fils du câble.

Chaque emplacement correspond à une broche.

Les broches sont numérotées de 1 à 8.

Pour que le câble fonctionne, il faut respecter deux conditions :

* les fils doivent être dans le bon ordre ;
* les fils doivent être insérés jusqu’au fond du connecteur.

Un câble peut sembler correct à l’œil, mais ne pas fonctionner si un fil n’est pas assez enfoncé.

C’est pour cela que le testeur RJ45 est indispensable.

<p>
  <img src="../images/connecteur-rj45-vue-face.png" alt="Le connecteur RJ45" width="60%">
</p>

## 7. La norme T568B

Pour fabriquer un câble RJ45, on ne place pas les fils au hasard.

On respecte une norme de câblage.

Dans cette activité, la norme utilisée est la norme T568B.

Ordre des fils en norme T568B :

| Broche | Couleur du fil |
| -----: | -------------- |
|      1 | Blanc-orange   |
|      2 | Orange         |
|      3 | Blanc-vert     |
|      4 | Bleu           |
|      5 | Blanc-bleu     |
|      6 | Vert           |
|      7 | Blanc-marron   |
|      8 | Marron         |

Attention : l’ordre dépend du sens dans lequel on regarde le connecteur.

Pendant l’activité, gardez toujours le connecteur dans le même sens que celui indiqué par le professeur.

Si vous inversez le sens du connecteur, vous risquez d’inverser l’ordre des fils.

<p>
  <img src="../images/norme-t568b.png" alt="La norme T568B" width="60%">
</p>

## 8. Le câble droit

Un câble droit est un câble dont les deux extrémités sont câblées de la même manière.

Dans ce palier, vous devez fabriquer un câble droit en norme T568B.

Cela signifie :

* première extrémité : norme T568B ;
* deuxième extrémité : norme T568B.

Dans un câble droit, chaque broche arrive au même numéro de l’autre côté.

<p>
  <img src="../images/cable-droit-t568b.png" alt="Le câble droit" width="60%">
</p>

Un câble droit est utilisé pour relier des équipements différents.

Exemples :

* ordinateur et switch ;
* ordinateur et prise réseau murale ;
* imprimante réseau et switch ;
* serveur et switch ;
* switch et routeur.


## 9. Le matériel nécessaire

Pour fabriquer un câble droit, il faut :

| Matériel              | Rôle                                            |
| --------------------- | ----------------------------------------------- |
| Câble Ethernet        | Support physique contenant les 8 fils           |
| Deux connecteurs RJ45 | Connecteurs placés aux deux extrémités du câble |
| Pince à dénuder       | Retirer la gaine extérieure                     |
| Pince à sertir RJ45   | Fixer le connecteur sur le câble                |
| Testeur RJ45          | Vérifier que le câble est correctement fabriqué |

Le testeur est obligatoire.

Un câble non testé ne doit pas être considéré comme conforme.

## 10. Méthode générale de fabrication

La fabrication d’un câble RJ45 doit être faite calmement.

Il faut éviter de vouloir aller vite.

Les étapes importantes sont :

1. couper le câble proprement ;
2. retirer la gaine extérieure sans abîmer les fils ;
3. séparer les paires ;
4. ranger les fils dans l’ordre T568B ;
5. couper les fils à la même longueur ;
6. insérer les fils jusqu’au fond du connecteur ;
7. vérifier l’ordre des fils ;
8. sertir le connecteur ;
9. refaire la même chose à l’autre extrémité ;
10. tester le câble.

## 11. Points de contrôle avant sertissage

Avant de sertir, il faut vérifier plusieurs points.

| Point à vérifier                             | Résultat attendu |
| -------------------------------------------- | ---------------- |
| Les fils sont dans l’ordre T568B             | Oui              |
| Les fils sont bien alignés                   | Oui              |
| Les fils arrivent au fond du connecteur      | Oui              |
| La gaine entre légèrement dans le connecteur | Oui              |
| Aucun fil n’est plié ou croisé               | Oui              |
| Le connecteur est dans le bon sens           | Oui              |

Si un point n’est pas correct, il ne faut pas sertir.

Il faut retirer les fils, les remettre correctement, puis vérifier à nouveau.

Une fois le connecteur serti, il ne peut pas être démonté proprement.

## 12. Le testeur RJ45

Le testeur RJ45 permet de vérifier la continuité et l’ordre des fils.

Il possède généralement deux parties :

* une partie principale ;
* une partie distante.

On branche une extrémité du câble sur chaque partie du testeur.

Le testeur allume ensuite les numéros des broches.

Pour un câble droit conforme, le résultat attendu est le suivant.

<p>
  <img src="../images/testeur-rj45.png" alt="Le testeur RJ45" width="60%">
</p>

Si les numéros ne correspondent pas, le câble n’est pas conforme.

## 13. Interpréter les résultats du testeur

| Résultat observé                         | Cause possible                                         |
| ---------------------------------------- | ------------------------------------------------------ |
| Tous les numéros correspondent           | Le câble est conforme                                  |
| Un numéro ne s’allume pas                | Fil coupé, mal inséré ou mal serti                     |
| Deux numéros sont inversés               | Deux fils ont été inversés                             |
| Aucun numéro ne s’allume                 | Mauvais sertissage, mauvais branchement ou câble coupé |
| Les numéros ne suivent pas le même ordre | Câble mal câblé ou câble croisé                        |

Le testeur ne vérifie pas si le câble est beau.

Il vérifie si les fils sont correctement reliés.

## 14. Erreurs fréquentes

<p>
  <img src="../images/erreurs-cablage-rj45.png" alt="Erreurs fréquentes" width="60%">
</p>

## 15.1 Fils inversés

Deux fils sont placés dans le mauvais ordre.

Conséquences possibles :

* le testeur indique une inversion ;
* le câble ne fonctionne pas correctement.

## 15.2 Fils pas assez enfoncés

Les fils ne vont pas jusqu’au fond du connecteur.

Conséquences possibles :

* un ou plusieurs fils ne font pas contact ;
* le testeur n’allume pas toutes les broches.

## 15.3 Gaine extérieure hors du connecteur

La gaine extérieure n’entre pas dans le connecteur.

Conséquences possibles :

* les petits fils supportent seuls les efforts mécaniques ;
* le câble devient fragile ;
* les fils peuvent se débrancher.

## 15.4 Fils trop dévrillés

Les fils sont dévrillés sur une longueur trop importante.

Conséquences possibles :

* le signal peut être plus sensible aux perturbations ;
* le câble est moins propre techniquement.

## 15.5 Mauvais sens du connecteur

Le connecteur a été regardé dans le mauvais sens.

Conséquences possibles :

* l’ordre des fils est inversé ;
* le câble n’est pas conforme.

## 15.6 Sertissage trop rapide

Le connecteur est serti sans vérification sérieuse.

Conséquences possibles :

* connecteur perdu ;
* câble à recommencer ;
* perte de temps.

## 16. Ce qu’il faut retenir

Un câble Ethernet RJ45 sert à établir une liaison physique entre une machine et un réseau.

Il contient 8 fils organisés en 4 paires torsadées.

Un câble droit T568B utilise la norme T568B aux deux extrémités.

Le câble est conforme seulement si le testeur indique une correspondance correcte de la broche 1 à la broche 8.

---

!!! info "Activité à réaliser"

    Vous avez maintenant les informations nécessaires pour passer à la partie pratique.

    Important : vous commencez par le QCM. Vous ne démarrez l’activité que lorsque votre QCM est validé à 100 %.

    Marche à suivre :

    1. [Télécharger le QCM du palier 1](eleve/qcm-palier-1.pdf), puis répondez à toutes les questions.
    2. Faites valider votre QCM. Tant qu’il n’est pas correct à 100 %, vous ne passez pas à l’activité.
    3. Une fois le QCM validé à 100 %, [télécharger l’activité : fabriquer et tester un câble Ethernet droit T568B](eleve/activite-palier-1.pdf) et réalisez les étapes demandées.

    Pendant l’activité, vous devrez revenir dans ce dossier technique chaque fois que vous aurez besoin d’une information.
