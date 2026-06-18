<!--
PAGE TEMPORAIRE - support de cours, sans aucune relation avec le framework Forge.
A SUPPRIMER le 2026-06-28 : retirer tout le dossier docs/starters-pedagogique/ ET
le bloc de nav "Welcome Réseau (2TNE CIEL)" dans mkdocs.yml, ainsi que l'entrée
"2TNE" de la landing.
-->

# Semaine réseau et virtualisation pour les 2TNE CIEL

[Accueil](../../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## Dernière semaine avant les vacances

Cette semaine, le travail se fera autrement.

Il n’y aura pas de cours magistral.
Vous allez avancer à votre rythme, à partir de documents techniques et d’activités pratiques.

Le but n’est pas d’aller le plus vite possible.
Le but est de comprendre, de manipuler, de tester, puis de corriger votre travail lorsque c’est nécessaire.

Chaque palier se déroule en trois étapes :

1. **Un dossier technique**
   Il présente les connaissances nécessaires pour réussir le QCM et l’activité.

2. **Un QCM**
   Vous le remplissez à partir du dossier technique. Vous ne passez à l’activité que lorsque votre QCM est validé à 100 %.

3. **Une activité pratique**
   Une fois le QCM validé, elle permet d’utiliser directement les informations du dossier technique.

---

## Objectif de la semaine

À la fin de cette semaine, vous aurez travaillé sur quatre situations techniques :

* fabriquer et tester un câble réseau droit ;
* installer deux machines virtuelles avec VirtualBox ;
* tester plusieurs modes de communication réseau entre la machine hôte et les machines virtuelles ;
* configurer un réseau interne et diagnostiquer une communication.

Vous allez donc travailler comme dans un atelier technique.

La démarche attendue est la suivante :

1. lire la documentation ;
2. préparer le matériel ou l’environnement de travail ;
3. réaliser la manipulation ;
4. tester le résultat ;
5. observer ce qui fonctionne ou ce qui ne fonctionne pas ;
6. corriger si nécessaire ;
7. conclure.

---

## Organisation du travail

### Activité glissante

Tout le monde ne sera pas forcément au même palier au même moment.
Chaque élève avance à son rythme, en fonction de son niveau d’autonomie et de l’avancement de son travail.

Pour chaque palier, vous devez :

* lire le dossier technique ;
* réaliser l’activité demandée ;
* compléter les tableaux de suivi ;
* faire vérifier votre travail si nécessaire ;
* passer au palier suivant lorsque le travail est terminé.

### Avant de demander de l’aide

Avant d’appeler le professeur, vous devez pouvoir expliquer :

* ce que vous avez essayé ;
* ce que vous avez observé ;
* ce qui ne fonctionne pas ;
* quelle partie du dossier technique vous avez consultée.

---

## Vue d’ensemble des paliers

| Palier | Thème                | Travail à réaliser                                                        | Production attendue                                        |
| -----: | -------------------- | ------------------------------------------------------------------------- | ---------------------------------------------------------- |
|      1 | Câble Ethernet droit | Fabriquer un câble RJ45 en norme T568B et le tester                       | Un câble droit conforme                                    |
|      2 | Machines virtuelles  | Installer une machine virtuelle Windows 11 et une machine virtuelle Linux | Deux machines virtuelles fonctionnelles avec un instantané |
|      3 | Modes réseau simples | Relever les informations réseau et tester les modes NAT et accès par pont  | Un tableau de tests des deux modes                         |
|      4 | Réseau interne       | Configurer un réseau interne et diagnostiquer une communication           | Un réseau interne fonctionnel et un diagnostic             |

---

## Les paliers à réaliser

### Palier 1 : Câble Ethernet droit T568B

Dans ce palier, vous allez fabriquer un câble réseau droit en respectant la norme **T568B**.

Vous devrez ensuite vérifier votre câble avec un testeur RJ45.

[Ouvrir le palier 1 : Fabriquer et tester un câble Ethernet droit T568B](palier-1/index.md)

---

### Palier 2 : Installer deux machines virtuelles

Dans ce palier, vous allez préparer deux machines virtuelles avec VirtualBox :

* une machine virtuelle avec **Windows 11** ;
* une machine virtuelle avec une **distribution Linux**.

Vous devrez aussi créer un **instantané** afin de pouvoir revenir à un état propre en cas d’erreur.

[Ouvrir le palier 2 : Installer deux machines virtuelles avec VirtualBox](palier-2/index.md)

---

### Palier 3 : Relever les informations réseau et tester les modes simples VirtualBox

Dans ce palier, vous allez relever les informations réseau des trois machines (hôte Debian 13, machine virtuelle Windows 11, machine virtuelle Linux), puis tester deux modes réseau simples de VirtualBox :

* le mode NAT ;
* l’accès par pont.

Vous apprendrez aussi à lire la configuration réseau d’une machine (adresse IP, masque) avec les commandes utiles.

[Ouvrir le palier 3 : Relever les informations réseau et tester les modes simples VirtualBox](palier-3/index.md)

---

### Palier 4 : Configurer un réseau interne et diagnostiquer une communication

Dans ce palier, vous allez configurer un réseau interne entre deux machines virtuelles, puis diagnostiquer une communication qui ne fonctionne pas.

Vous allez :

* attribuer des adresses IP fixes ;
* vérifier que les deux machines sont dans le même réseau logique ;
* tester la communication avec `ping` ;
* diagnostiquer une panne réseau dans l’ordre.

[Ouvrir le palier 4 : Configurer un réseau interne et diagnostiquer une communication](palier-4/index.md)

---

## Ce qu’il faut retenir

Cette semaine, vous ne venez pas recopier un cours.

Vous venez pour :

* manipuler du matériel réseau ;
* installer des systèmes ;
* observer des résultats ;
* comprendre les erreurs ;
* corriger votre travail ;
* expliquer simplement ce que vous avez fait.

Un technicien ne travaille pas au hasard.
Il vérifie, il teste, il observe, puis il conclut.

---

## Parcours obligatoire

Les paliers doivent être réalisés dans l’ordre.

1. Palier 1 : fabriquer et tester un câble réseau.
2. Palier 2 : installer deux machines virtuelles.
3. Palier 3 : tester les communications réseau.
4. Palier 4 : configurer un réseau interne et diagnostiquer une communication.

Vous ne passez au palier suivant que lorsque le palier en cours est terminé et vérifié.

Travaillez proprement, avancez étape par étape, et gardez une trace de vos résultats.
