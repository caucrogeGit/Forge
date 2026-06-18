# Convention de création d’un palier pour un Welcome pédagogique

## 1. Principe général

Un palier est une étape de progression autonome destinée à une classe d’élèves.

Il doit permettre à chaque élève d’avancer à son rythme, à partir d’une documentation claire, sans dépendre d’un cours magistral.

Chaque palier doit correspondre à un objectif précis, concret et vérifiable.

Un palier ne doit pas mélanger trop de notions.  
Si le contenu devient trop lourd, il faut le découper en plusieurs paliers.

Un palier doit garder une logique simple :

1. comprendre avec le dossier technique ;
2. vérifier la compréhension avec le QCM ;
3. réaliser l’activité ;
4. faire son auto-vérification ;
5. faire valider par le professeur.

## 2. Objectif d’un palier

Un palier doit répondre à une question simple :

> Qu’est-ce que l’élève doit être capable de faire à la fin de cette étape ?

L’objectif doit être formulé avec un verbe d’action.

Exemples :

| Palier | Objectif concret |
|---|---|
| Palier 1 | Fabriquer et tester un câble Ethernet droit T568B |
| Palier 2 | Installer deux machines virtuelles avec VirtualBox |
| Palier 3 | Relever les informations réseau et tester des modes simples |
| Palier 4 | Configurer un réseau interne et diagnostiquer une communication |

## 3. Règle de découpage d’un palier

Un palier doit contenir un seul objectif pratique principal.

Si un dossier technique contient plusieurs objectifs pratiques importants, il faut découper.

Signes qu’un palier est trop gros :

- plus de deux objectifs pratiques importants ;
- trop de procédures différentes ;
- trop de notions nouvelles ;
- plus de 15 chapitres repliables ;
- QCM qui couvre trop de domaines différents ;
- activité qui demande plusieurs types de productions ;
- élève obligé de changer plusieurs fois de contexte technique.

Exemple :

| Palier trop gros | Découpage conseillé |
|---|---|
| Installer des machines virtuelles et tester tous les modes réseau | Palier 2 : installer les VM, palier 3 : tester NAT et pont, palier 4 : réseau interne et diagnostic |
| Tester tous les modes réseau, configurer des IP fixes, diagnostiquer, calculer le réseau en binaire | Palier 3 : relever IP et tester NAT / pont, palier 4 : réseau interne, IP fixes et diagnostic |
| Fabriquer un câble, comprendre l’adresse IP et tester VirtualBox | Palier 1 : câble, palier 2 : VM, palier 3 : réseau |

## 4. Composition obligatoire d’un palier

Chaque palier doit contenir les éléments suivants.

| Élément | Fonction | Public |
|---|---|---|
| Dossier technique | Donner les connaissances nécessaires | Élève |
| QCM | Vérifier la compréhension avant l’activité | Élève |
| Activité formative | Guider la réalisation pratique | Élève |
| Checklist de validation | Auto-vérification élève et validation professeur | Élève / professeur |
| Images d’illustration | Aider à comprendre les notions importantes | Élève |
| Corrigé du QCM | Permettre la correction | Professeur |

Un palier complet doit donc séparer clairement :

- les ressources consultées par l’élève ;
- les ressources partagées entre élève et professeur ;
- les ressources réservées au professeur.

## 5. Statut des documents

Chaque document doit avoir un statut clair.

| Document | Statut | Accès |
|---|---|---|
| `dossier-technique.md` | Ressource de travail | Élève |
| `qcm-palier-X.md` | Vérification préalable | Élève |
| `activite-palier-X.md` | Travail à réaliser | Élève |
| `checklist-palier-X-validation.md` | Suivi partagé | Élève / professeur |
| `qcm-palier-X-corrige.md` | Correction | Professeur |

Le dossier technique, le QCM, l’activité et la checklist de validation sont accessibles à l’élève.

Le corrigé du QCM est réservé au professeur.

## 6. Parcours obligatoire de l’élève

Le parcours élève doit être imposé.

Ordre obligatoire :

1. lire le dossier technique ;
2. répondre au QCM dans le fichier demandé ;
3. faire valider le QCM à 100 % ;
4. commencer l’activité ;
5. utiliser la checklist pour faire son auto-vérification ;
6. demander de l’aide avec une formulation correcte si nécessaire ;
7. faire valider le travail par le professeur ;
8. passer au palier suivant uniquement après validation.

Formulation à utiliser :

```markdown
Vous ne passez au palier suivant que lorsque le palier en cours est terminé et vérifié.
```

## 7. Rôle du dossier technique

Le dossier technique est la ressource principale de l’élève.

Il doit contenir les connaissances nécessaires pour réussir l’activité.

Il ne doit pas être une simple fiche de consignes.  
Il doit permettre à l’élève de chercher les informations utiles.

Le dossier technique doit contenir :

- les notions importantes ;
- les définitions ;
- les tableaux de repérage ;
- les exemples utiles ;
- les commandes ou procédures nécessaires ;
- les erreurs fréquentes ;
- les éléments à retenir ;
- les liens vers le QCM et l’activité.

Le dossier technique ne doit pas contenir :

- une fiche à remplir ;
- une correction ;
- des consignes réservées au professeur ;
- des informations inutiles au palier.

## 8. Structure recommandée du dossier technique

Structure à utiliser :

````markdown
# Palier X : titre du palier

## Dossier technique

## Objectif du dossier technique

Ce dossier donne les connaissances nécessaires pour...

À la fin de cette lecture, vous devez être capable de comprendre :

* ...
* ...
* ...

??? note "1. Premier chapitre"
    Contenu du chapitre.

??? note "2. Deuxième chapitre"
    Contenu du chapitre.

??? note "3. Troisième chapitre"
    Contenu du chapitre.

??? note "Dernier chapitre : ce qu’il faut retenir"
    Synthèse courte.

??? info "Activité à réaliser"
    Vous avez maintenant les informations nécessaires pour passer à la partie pratique.

    Important : vous commencez par le QCM. Vous ne démarrez l’activité que lorsque votre QCM est validé à 100 %.

    Marche à suivre :

    1. Ouvrir le QCM du palier.
    2. Répondre au QCM dans le fichier demandé.
    3. Faire valider le QCM.
    4. Une fois le QCM validé à 100 %, ouvrir ou télécharger l’activité.

    Pendant l’activité, vous devrez revenir dans ce dossier technique chaque fois que vous aurez besoin d’une information.
````

## 9. Utilisation des bandeaux repliables

Les chapitres du dossier technique doivent être placés dans des bandeaux repliables.

Syntaxe à utiliser :

````markdown
??? note "1. Titre du chapitre"
    Contenu du chapitre.
````

Pour un encadré d’information :

````markdown
??? info "Activité à réaliser"
    Contenu de l’encadré.
````

Pour un avertissement :

````markdown
!!! warning "Attention"
    Message d’avertissement.
````

Les bandeaux repliables permettent de rendre le dossier moins lourd visuellement.

## 10. Rôle des images d’illustration

Les images doivent servir à comprendre, pas à décorer.

Elles doivent être placées uniquement lorsque cela aide l’élève à visualiser une notion.

Exemples :

| Sujet | Image utile |
|---|---|
| Câble RJ45 | Ordre des fils T568B |
| VirtualBox | Hôte, logiciel VirtualBox, machines invitées |
| Réseau | Modes NAT, pont, réseau interne |
| Diagnostic | Méthode de vérification étape par étape |

Format d’insertion recommandé :

```html
<p align="center">
  <img src="images/nom-de-l-image.png" alt="Titre de l’image" width="60%">
</p>
```

Règles de création :

- image légère ;
- image utile à la compréhension ;
- pas d’image décorative ;
- pas d’image trop lourde ;
- texte alternatif obligatoire ;
- largeur recommandée : 60 % ;
- nom stable et explicite.

Règles de nommage :

- minuscules ;
- sans accents ;
- sans espaces ;
- mots séparés par des tirets simples.

Exemples :

```text
principe-virtualisation.png
reseau-interne-virtualbox.png
test-ping-vm.png
norme-t568b.png
```

## 11. Rôle du QCM

Le QCM sert à vérifier que l’élève a lu et compris le dossier technique avant de commencer l’activité.

Le QCM est une condition d’accès à l’activité.

L’élève ne passe pas à l’activité tant que le QCM n’est pas correct à 100 %.

Il ne faut donc pas mettre de barème de niveau.

La règle est simple :

```text
20 bonnes réponses sur 20
```

## 12. Convention de rédaction du QCM

Chaque QCM doit contenir 20 questions.

Chaque question doit proposer trois réponses :

- A ;
- B ;
- C.

Une seule réponse doit être correcte.

La répartition des réponses correctes doit être équilibrée.

Avec 20 questions, utiliser une des répartitions suivantes :

| Réponse correcte | Nombre attendu |
|---|---:|
| A | 7 |
| B | 7 |
| C | 6 |

ou :

| Réponse correcte | Nombre attendu |
|---|---:|
| A | 7 |
| B | 6 |
| C | 7 |

Le QCM doit couvrir tout le dossier technique, pas seulement les premiers chapitres.

## 13. Format de réponse du QCM

L’élève doit répondre dans un fichier texte.

Nom du fichier :

```text
qcm-palierX.txt
```

Exemple pour le palier 2 :

```text
qcm-palier2.txt
```

Format attendu :

```text
1a
2b
3c
4a
5b
```

Le fichier doit contenir une réponse par ligne.

Il ne doit pas contenir :

- de phrases ;
- de justification ;
- d’espace entre le numéro et la lettre ;
- de ligne inutile.

Exemple de fichier complet :

```text
1a
2b
3c
4a
5b
6c
7a
8b
9c
10a
11b
12c
13a
14b
15c
16a
17b
18c
19a
20b
```

## 14. Rôle du corrigé du QCM

Le corrigé est destiné au professeur.

Il doit contenir :

- le numéro de la question ;
- la réponse correcte ;
- une explication courte.

Il ne doit pas contenir de barème si le QCM est une condition d’accès à l’activité.

Structure recommandée :

````markdown
# Corrigé du QCM du palier X

## Correction détaillée

| Question | Réponse | Explication courte |
|---:|---|---|
| 1 | A | Explication courte. |
| 2 | B | Explication courte. |

## Validation

Le QCM est validé uniquement avec 20 bonnes réponses sur 20.

En cas d’erreur, l’élève doit relire le chapitre concerné du dossier technique, corriger son fichier, puis demander une nouvelle validation.
````

## 15. Rôle de l’activité formative

L’activité est le document qui indique ce que l’élève doit faire.

Elle ne doit pas redonner le cours.

L’élève doit chercher les informations dans le dossier technique.

L’activité doit donc :

- dire quoi faire ;
- donner l’ordre de travail ;
- demander de consulter le dossier technique ;
- ne pas redonner toutes les réponses ;
- ne pas refaire le cours ;
- prévoir une demande d’aide formalisée ;
- indiquer les traces attendues ;
- indiquer le résultat attendu ;
- indiquer les conditions de validation.

## 16. Structure recommandée de l’activité

Structure à utiliser :

````markdown
# Activité du palier X : titre de l’activité

## Principe de l’activité

Cette activité se réalise à partir du dossier technique du palier X.

Le dossier technique contient les informations nécessaires pour réussir le travail demandé.

L’activité ne redonne pas les explications techniques.  
Vous devez donc consulter le dossier technique lorsque vous avez besoin d’une information.

## Travail demandé

Vous devez...

## Matériel et fichiers nécessaires

Avant de commencer, vérifiez que vous disposez des éléments nécessaires :

* ...
* ...
* ...

## Traces attendues

À la fin de l’activité, vous devez pouvoir présenter :

* ...
* ...
* ...

## Demander de l’aide

Vous pouvez demander de l’aide, mais la demande doit être formulée correctement.

## Étape 1 : ...

## Étape 2 : ...

## Résultat attendu

À la fin de l’activité :

* ...
* ...
* ...

## Validation du palier

Le palier est validé lorsque...
````

## 17. Traces attendues dans une activité

Chaque activité doit préciser les traces attendues.

Une trace attendue est un élément que l’élève doit pouvoir montrer, déposer ou expliquer.

Exemples :

| Type d’activité | Trace attendue |
|---|---|
| Câble RJ45 | Câble testé conforme, testeur affichant 1 vers 1 jusqu’à 8 vers 8 |
| VirtualBox | Deux VM fonctionnelles, comptes accessibles, instantanés créés |
| Réseau | Tableau de tests, adresses IP relevées, captures ou résultats de commandes |
| Arduino | Montage fonctionnel, code, capture TinkerCad ou démonstration réelle |
| Programmation | Fichier de code, résultat affiché, explication de la logique |

Les traces doivent être adaptées au palier.

Elles ne doivent pas être trop nombreuses.  
Un excès de traces rend l’activité lourde et peu lisible.

## 18. Nommage des fichiers rendus par l’élève

Les fichiers rendus par l’élève doivent avoir un nom clair.

Pour un QCM :

```text
qcm-palierX.txt
```

Pour un résultat d’activité :

```text
palierX-resultats.txt
```

Pour une capture :

```text
palierX-capture-etapeY.png
```

Pour un fichier nominatif déposé dans un espace protégé :

```text
palierX-nom-prenom.txt
palierX-nom-prenom.png
```

Attention : les fichiers contenant le nom et le prénom d’un élève ne doivent jamais être publiés dans un espace public.

## 19. Demande d’aide formalisée

Chaque activité doit contenir une partie « Demander de l’aide ».

L’objectif est d’éviter les demandes vagues.

Formulation à intégrer :

````markdown
## Demander de l’aide

Vous pouvez demander de l’aide, mais la demande doit être formulée correctement.

Avant d’appeler le professeur, vous devez pouvoir expliquer clairement :

* l’étape sur laquelle vous travaillez ;
* ce que vous avez déjà essayé ;
* ce que vous avez observé ;
* ce qui ne fonctionne pas ;
* la partie du dossier technique que vous avez consultée.

Une demande d’aide ne doit pas être formulée comme ceci :

> Je ne comprends rien.  
> Ça ne marche pas.  
> Je ne sais pas quoi faire.

Une demande d’aide doit être formulée comme ceci :

> Je suis à l’étape de configuration du mode réseau de la machine virtuelle Windows 11 Pro.  
> J’ai sélectionné le mode réseau interne, mais je ne suis pas sûr du nom de réseau à utiliser.  
> J’ai consulté le chapitre sur le changement du mode réseau dans VirtualBox.  
> J’ai besoin d’aide pour vérifier ma configuration avant de démarrer la machine virtuelle.

Le professeur aide plus efficacement lorsque le problème est expliqué avec précision.

Un technicien ne dit pas seulement que ça ne fonctionne pas.  
Il explique ce qu’il a fait, ce qu’il a observé et ce qu’il veut vérifier.
````

## 20. Rôle de la checklist de validation

La checklist de validation est un document partagé entre l’élève et le professeur.

Elle n’est pas seulement un document professeur.

Elle sert à deux choses :

- l’élève l’utilise pour vérifier qu’il pense avoir terminé le palier ;
- le professeur l’utilise pour valider, refuser ou demander une correction.

La checklist doit donc être accessible à l’élève.

Elle doit contenir des colonnes séparées pour :

- l’auto-vérification élève ;
- la validation professeur ;
- les observations.

La checklist ne contient pas les réponses du QCM.  
Elle ne remplace pas le corrigé.

## 21. Structure recommandée de la checklist de validation

Structure à utiliser :

````markdown
# Checklist de validation du palier X

## Identification de l’élève

| Élément | Information |
|---|---|
| Nom | |
| Prénom | |
| Classe | |
| Poste utilisé | |
| Date | |

## Principe

Cette checklist sert à vérifier que le palier est terminé.

L’élève commence par faire son auto-vérification.  
Le professeur valide ensuite les points attendus.

## 1. Validation du QCM

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le fichier QCM existe | ☐ | ☐ | |
| Le format demandé est respecté | ☐ | ☐ | |
| Le QCM est validé à 100 % | ☐ | ☐ | |

## 2. Vérification technique

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| Le travail demandé est réalisé | ☐ | ☐ | |
| Le résultat attendu est obtenu | ☐ | ☐ | |
| Les consignes du dossier technique sont respectées | ☐ | ☐ | |

## 3. Vérification de l’autonomie

| Point à vérifier | Élève | Professeur | Observation |
|---|---|---|---|
| L’élève utilise le dossier technique | ☐ | ☐ | |
| L’élève sait expliquer ce qu’il a fait | ☐ | ☐ | |
| L’élève sait retrouver l’information utile | ☐ | ☐ | |
| L’élève formule correctement ses demandes d’aide | ☐ | ☐ | |

## 4. Validation finale

| Élément final à valider | Élève | Professeur | Observation |
|---|---|---|---|
| Le palier est terminé | ☐ | ☐ | |
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
````

## 22. Règle de correction et reprise

Une erreur n’est pas une fin d’activité.

Une erreur déclenche une reprise ciblée.

En cas d’échec au QCM :

1. l’élève relit le chapitre concerné ;
2. il corrige son fichier de réponse ;
3. il redemande une validation ;
4. il ne commence pas l’activité tant que le QCM n’est pas correct à 100 %.

En cas d’échec dans l’activité :

1. l’élève identifie l’étape bloquante ;
2. il consulte le dossier technique ;
3. il corrige le point demandé ;
4. il complète ou met à jour sa checklist ;
5. il redemande une validation.

L’objectif n’est pas de sanctionner l’erreur.

L’objectif est de faire reprendre précisément ce qui n’est pas acquis.

## 23. Validation d’un palier

Un palier est validé lorsque :

- le QCM est correct à 100 % ;
- l’activité est réalisée ;
- les traces attendues sont présentes ;
- la checklist a été complétée par l’élève ;
- les points techniques attendus sont vérifiés par le professeur ;
- l’élève sait expliquer ce qu’il a fait ;
- l’élève sait retrouver une information dans le dossier technique.

La validation ne repose pas seulement sur le résultat final.

Elle repose aussi sur la méthode de travail.

## 24. Ancrage au référentiel

Un palier peut contenir un ancrage au référentiel.

Cet ancrage est optionnel pour un Welcome de fin d’année non noté, mais il reste utile pour préparer les futurs supports.

Structure recommandée :

````markdown
## Ancrage au référentiel

Ce palier mobilise principalement :

| Élément | Référence |
|---|---|
| Bloc concerné | ... |
| Compétence travaillée | ... |
| Savoirs associés | ... |
| Résultat observable | ... |
````

L’ancrage au référentiel doit rester simple.

Il ne doit pas transformer le palier en document administratif lourd.

## 25. Nommage des fichiers du palier

Chaque palier doit utiliser des noms de fichiers clairs.

Exemple pour le palier 2 :

| Document | Nom conseillé |
|---|---|
| Dossier technique | `dossier-technique.md` |
| QCM élève | `qcm-palier-2-machines-virtuelles.md` |
| Activité élève | `activite-palier-2-machines-virtuelles.md` |
| Checklist de validation | `checklist-palier-2-validation.md` |
| Corrigé QCM professeur | `qcm-palier-2-corrige.md` |

Pour les PDF élèves :

| Document | Nom conseillé |
|---|---|
| QCM PDF élève | `qcm-palier-2-machines-virtuelles.pdf` |
| Activité PDF élève | `activite-palier-2-machines-virtuelles.pdf` |
| Checklist PDF élève / professeur | `checklist-palier-2-validation.pdf` |

Pour les PDF professeur :

| Document | Nom conseillé |
|---|---|
| Corrigé QCM PDF | `qcm-palier-2-corrige.pdf` |

## 26. Organisation des dossiers

L’organisation d’un palier doit séparer clairement les ressources élèves, les ressources partagées et les ressources réservées au professeur.

Cette séparation permet :

- de rendre le parcours élève plus clair ;
- d’éviter de mélanger activité, corrigé et documents internes ;
- de préparer une future gestion des autorisations ;
- de pouvoir limiter l’accès aux documents professeur.

Organisation recommandée :

```text
palier-X/
├── index.md
├── dossier-technique.md
├── images/
│   ├── illustration-1.png
│   ├── illustration-2.png
│   └── illustration-3.png
├── eleve/
│   ├── qcm-palier-X.md
│   ├── activite-palier-X.md
│   ├── checklist-palier-X-validation.md
│   ├── qcm-palier-X.pdf
│   ├── activite-palier-X.pdf
│   └── checklist-palier-X-validation.pdf
└── professeur/
    ├── qcm-palier-X-corrige.md
    └── qcm-palier-X-corrige.pdf
```

Les fichiers placés à la racine du palier sont les pages principales du palier.

Le dossier `images/` contient uniquement les illustrations utilisées par le dossier technique ou l’activité.

Le dossier `eleve/` contient les documents élèves et les documents partagés :

- QCM ;
- activité formative ;
- checklist de validation ;
- versions PDF élèves si nécessaire.

Le dossier `professeur/` contient les documents réservés au professeur :

- corrigés ;
- documents non accessibles aux élèves ;
- versions PDF professeur si nécessaire.

Dans une logique de droits d’accès, la structure à retenir est :

| Dossier | Public visé | Contenu |
|---|---|---|
| Racine du palier | Élève | Pages principales et dossier technique |
| `images/` | Élève | Illustrations du palier |
| `eleve/` | Élève / professeur | QCM, activité, checklist de validation |
| `professeur/` | Professeur | Corrigés, documents réservés |

Il ne faut jamais placer un corrigé dans un dossier accessible aux élèves.

## 27. Modèle d’index de palier

Chaque palier doit contenir une page `index.md`.

Cette page sert de point d’entrée.

Elle doit contenir :

- le titre du palier ;
- l’objectif du palier ;
- l’ordre obligatoire ;
- les liens vers le dossier technique, le QCM, l’activité et la checklist ;
- le rappel du QCM à 100 % ;
- le rappel de la validation professeur.

Structure recommandée :

````markdown
# Palier X : titre du palier

## Objectif

Dans ce palier, vous allez...

À la fin du palier, vous devez être capable de...

## Parcours obligatoire

1. Lire le dossier technique.
2. Répondre au QCM.
3. Faire valider le QCM à 100 %.
4. Réaliser l’activité.
5. Compléter la checklist de validation.
6. Faire valider le palier par le professeur.

## Documents

| Document | Lien |
|---|---|
| Dossier technique | [Ouvrir](dossier-technique.md) |
| QCM | [Ouvrir](eleve/qcm-palier-X.md) |
| Activité | [Ouvrir](eleve/activite-palier-X.md) |
| Checklist de validation | [Ouvrir](eleve/checklist-palier-X-validation.md) |

## Rappel

Vous ne commencez pas l’activité tant que le QCM n’est pas validé à 100 %.

Vous ne passez pas au palier suivant tant que ce palier n’est pas validé.
````

## 28. Règle RGPD et données élèves

Les modèles de documents peuvent être versionnés dans un dépôt ou publiés dans un espace pédagogique.

En revanche, les documents complétés avec les données des élèves ne doivent pas être publiés dans un espace public.

Sont considérées comme données élèves :

- nom ;
- prénom ;
- classe ;
- poste utilisé ;
- date de validation ;
- observations individuelles ;
- résultats individualisés ;
- captures contenant une session personnelle.

Règle à appliquer :

```text
Modèle vide : publiable.
Document complété avec données élèves : espace protégé uniquement.
```

Les fichiers remplis par les élèves ou annotés par le professeur doivent rester dans un environnement sécurisé de l’établissement.

## 29. Règles de rédaction

Le style doit être clair, direct et adapté à une classe d’élèves.

Règles à respecter :

- phrases courtes ;
- vocabulaire technique expliqué ;
- pas de ton infantilisant ;
- pas de cours magistral déguisé ;
- pas de formulations vagues ;
- pas de texte inutile ;
- pas de tiret cadratin ;
- ponctuation française sobre ;
- pas de signes décoratifs inutiles ;
- pas de formulations artificielles.

À éviter :

```text
Vous allez découvrir le monde fascinant de...
Cette activité immersive vous permettra...
Dans ce merveilleux parcours...
```

À préférer :

```text
Dans cette activité, vous allez...
À la fin du palier, vous devez être capable de...
Le palier est validé lorsque...
```

## 30. Modèle minimal d’un palier

Un palier complet doit contenir au minimum :

```text
1. Une page index
2. Une page dossier technique
3. Un QCM de 20 questions
4. Un corrigé de QCM
5. Une activité formative
6. Une checklist de validation partagée élève / professeur
7. Des illustrations utiles
8. Un encadré final de passage vers l’activité
```

## 31. Convention de création et règles élèves

Il faut distinguer deux documents.

| Document | Public | Rôle |
|---|---|---|
| Convention de création d’un palier | Professeur | Définir comment produire les paliers |
| Règles du parcours élève | Élève | Expliquer comment travailler dans le Welcome |

La convention de création est détaillée.

Les règles élèves doivent être beaucoup plus courtes.

Elles doivent simplement rappeler :

- je lis le dossier technique ;
- je réponds au QCM ;
- je dois obtenir 100 % ;
- je réalise l’activité ;
- je complète la checklist ;
- je demande de l’aide correctement ;
- je fais valider avant de continuer.

## 32. Principe pédagogique général

Le palier doit rendre l’élève actif.

L’élève ne doit pas attendre que le professeur explique chaque étape.

Il doit apprendre à :

- lire une documentation technique ;
- extraire une information utile ;
- appliquer une procédure ;
- vérifier son résultat ;
- corriger une erreur ;
- formuler une demande d’aide précise ;
- faire son auto-vérification ;
- faire valider son travail.

Le professeur n’est pas là pour refaire le dossier technique à l’oral.

Le professeur accompagne, vérifie, débloque et valide.
