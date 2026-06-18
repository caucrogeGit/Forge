<!--
PAGE TEMPORAIRE - support de cours, sans aucune relation avec le framework Forge.
A SUPPRIMER le 2026-06-28 (voir docs/starters-pedagogique/welcome-reseau/index.md).
-->

[Semaine réseau et virtualisation](../index.md) <a href="javascript:void(0)" onclick="window.history.back()"> / Retour</a>

# Palier 2 : installer deux machines virtuelles avec VirtualBox

## Dossier technique

## Objectif du dossier technique

Ce dossier donne les connaissances nécessaires pour préparer et installer deux machines virtuelles avec VirtualBox.

À la fin de cette lecture, vous devez être capable de comprendre :

* ce qu’est une machine virtuelle ;
* ce qu’est une machine hôte ;
* ce qu’est une machine invitée ;
* le rôle de VirtualBox ;
* le rôle d’une image ISO ;
* le rôle d’un disque virtuel ;
* pourquoi il faut attribuer de la mémoire et du processeur à une machine virtuelle ;
* pourquoi les machines virtuelles doivent utiliser des identifiants communs en classe ;
* comment créer une machine virtuelle Windows 11 Pro ;
* comment créer une machine virtuelle Zorin OS.

??? note "1. Le principe de la virtualisation"
    La virtualisation permet de faire fonctionner un ordinateur simulé à l’intérieur d’un ordinateur réel.

    L’ordinateur réel continue d’exister normalement.  
    La machine virtuelle fonctionne dans une fenêtre, comme si c’était un autre ordinateur.

    Dans cette situation :

    * la machine réelle est le poste Debian 13 ;
    * VirtualBox est le logiciel utilisé pour créer les machines virtuelles ;
    * les machines virtuelles à installer sont Windows 11 Pro et Zorin OS.

    Une machine virtuelle peut être démarrée, arrêtée, configurée, supprimée ou restaurée sans modifier directement le système principal, si le travail est fait correctement.

    <p align="center">
      <img src="../images/principe-virtualisation.png" alt="Le principe de la virtualisation" width="60%">
    </p>

??? note "2. Machine hôte et machine invitée"
    En virtualisation, il faut distinguer deux éléments.

    | Élément | Définition |
    |---|---|
    | Machine hôte | Ordinateur réel qui exécute VirtualBox |
    | Système hôte | Système installé sur l’ordinateur réel |
    | Machine invitée | Ordinateur simulé dans VirtualBox |
    | Système invité | Système installé dans la machine virtuelle |

    Dans notre cas :

    | Rôle | Élément |
    |---|---|
    | Machine hôte | Poste de la salle |
    | Système hôte | Debian 13 |
    | Logiciel de virtualisation | VirtualBox |
    | Machine invitée 1 | Machine virtuelle Windows 11 Pro |
    | Machine invitée 2 | Machine virtuelle Zorin OS |

    La machine hôte fournit les ressources.  
    La machine invitée utilise une partie de ces ressources.

    <p align="center">
      <img src="../images/machine-hote-machine-invitee.png" alt="Machine hôte et machine invitée" width="60%">
    </p>

??? note "3. Le rôle de VirtualBox"
    VirtualBox est un logiciel de virtualisation.

    Il permet de créer des machines virtuelles.

    Chaque machine virtuelle possède ses propres éléments simulés :

    * mémoire vive ;
    * processeur ;
    * disque dur ;
    * carte réseau ;
    * lecteur optique ;
    * écran ;
    * clavier ;
    * souris.

    VirtualBox ne remplace pas le système Debian 13.  
    Il fonctionne au-dessus de Debian 13.

    Debian 13 reste le système principal du poste.

??? note "4. Les ressources d’une machine virtuelle"
    Une machine virtuelle utilise une partie des ressources de la machine réelle.

    Ces ressources ne sont pas illimitées.

    Si une machine virtuelle reçoit trop de mémoire ou trop de processeur, le poste Debian 13 peut devenir lent.

    Il faut donc choisir des valeurs adaptées.

    | Ressource | Rôle |
    |---|---|
    | Mémoire vive | Permet au système invité de fonctionner |
    | Processeur | Permet d’exécuter les instructions |
    | Disque virtuel | Stocke le système invité et ses fichiers |
    | Carte réseau virtuelle | Permet à la machine virtuelle de communiquer |
    | Lecteur ISO | Permet de démarrer l’installation du système invité |

    Une machine virtuelle doit avoir assez de ressources pour fonctionner, mais pas au point de bloquer la machine hôte.

    <p align="center">
      <img src="../images/ressources-machine-virtuelle.png" alt="Les ressources d'une machine virtuelle" width="60%">
    </p>

    ### 4.1 La mémoire vive

    La mémoire vive est souvent appelée RAM.

    Quand on donne de la mémoire vive à une machine virtuelle, cette mémoire est prise sur celle de la machine hôte.

    Exemple :

    * le poste Debian 13 possède une certaine quantité de mémoire ;
    * une partie est utilisée par Debian 13 ;
    * une autre partie peut être attribuée à la machine virtuelle.

    Si trop de mémoire est donnée à une machine virtuelle, Debian 13 peut ralentir fortement.

    Il faut respecter les valeurs données dans ce dossier ou par le professeur.

    ### 4.2 Le processeur

    VirtualBox permet d’attribuer un ou plusieurs cœurs de processeur à une machine virtuelle.

    Plus une machine virtuelle reçoit de cœurs, plus elle peut être réactive.

    Mais la machine hôte doit toujours garder assez de ressources pour fonctionner correctement.

    Il ne faut donc pas attribuer tous les cœurs disponibles à une machine virtuelle.

    ### 4.3 Le disque virtuel

    Une machine virtuelle utilise un disque virtuel.

    Ce disque n’est pas un disque physique séparé.  
    C’est un fichier stocké sur la machine hôte.

    Pour la machine virtuelle, ce fichier se comporte comme un vrai disque dur.

    Le disque virtuel contient :

    * le système installé ;
    * les programmes ;
    * les fichiers ;
    * les paramètres de la machine virtuelle.

    Il faut choisir une taille suffisante, mais raisonnable.

    ### 4.4 L’image ISO

    Une image ISO est un fichier qui contient le programme d’installation d’un système d’exploitation.

    Elle joue le même rôle qu’un DVD ou qu’une clé USB d’installation.

    Dans VirtualBox, on peut utiliser une image ISO pour installer un système dans une machine virtuelle.

    Pour ce palier, les images ISO nécessaires seront fournies ou indiquées par le professeur.

    Il ne faut pas télécharger une image ISO au hasard.  
    Il faut utiliser l’image demandée pour l’activité.

    <p align="center">
      <img src="../images/image-iso-installation.png" alt="L'image ISO" width="60%">
    </p>

??? note "5. Images ISO à utiliser"
    Les images ISO doivent être téléchargées depuis une source fiable indiquée par le professeur.

    Pour cette activité, l’ISO Windows se télécharge depuis le guide Le Crabe Info, et l’ISO Zorin OS depuis le site officiel zorin.com.

    Il ne faut pas utiliser une image ISO trouvée au hasard sur Internet.

    ### 5.1 ISO Windows 11

    Lien direct vers le guide de téléchargement :

    [Télécharger l’ISO Windows 11 avec le guide Le Crabe Info](https://lecrabeinfo.net/guides/telecharger-iso-windows-11/)

    Sur cette page, suivre la procédure permettant de télécharger l’image disque ISO de Windows 11 pour les appareils x64.

    Choisir l’image : **Windows 11 25H2 x64**.

    Cette ISO est une ISO multi-édition.

    Pour cette activité, il faudra choisir l’édition **Windows 11 Pro** pendant l’installation, lorsque l’installateur le demande.

    Ne pas télécharger une autre image ISO sans consigne du professeur.

    ### 5.2 ISO Zorin OS

    Lien de téléchargement officiel :

    [Télécharger Zorin OS sur zorin.com](https://zorin.com/os/download/)

    Sur le site, télécharger la dernière version de Zorin OS en 64 bits.

    Choisir de préférence l’édition Lite, plus légère et adaptée à une machine virtuelle, si elle est proposée.  
    Sinon, prendre l’édition Core.

    Il ne faut pas prendre la version 32 bits.

    ### 5.3 Règle à respecter

    Les images ISO utilisées en classe doivent être celles indiquées par le professeur.

    Si l’image ISO est déjà présente sur le poste, il ne faut pas en télécharger une autre sans consigne.

    Si l’image ISO est absente, il faut demander au professeur quel fichier utiliser.

??? note "6. Identifiants à utiliser pour les machines virtuelles"
    Pour cette activité, les machines virtuelles doivent utiliser des identifiants communs.

    Cela permet au professeur d’ouvrir rapidement une machine virtuelle si une vérification ou une correction est nécessaire.

    Ces identifiants sont utilisés uniquement pour les machines virtuelles de classe.

    Ils ne doivent jamais être utilisés pour un compte personnel, un compte de l’établissement ou un service accessible sur Internet.

    | Élément | Valeur à utiliser |
    |---|---|
    | Nom d’utilisateur | tne |
    | Mot de passe | Tne2026! |
    | Indice de mot de passe Windows | classe |

    Pour Zorin OS, si l’installation demande un nom complet et un nom d’ordinateur, utiliser :

    | Élément | Valeur à utiliser |
    |---|---|
    | Nom complet | Utilisateur TNE |
    | Nom de l’ordinateur | zorin-tne |
    | Nom d’utilisateur | tne |
    | Mot de passe | Tne2026! |

    Si l’installation de Windows demande obligatoirement un compte Microsoft, ne pas utiliser de compte personnel.

    Dans ce cas, il faut appeler le professeur.

??? note "7. Vue d’ensemble de l’installation des deux machines virtuelles"
    Les deux chapitres suivants détaillent l’installation de la machine virtuelle Windows 11 Pro, puis de la machine virtuelle Zorin OS.

    Les paramètres à renseigner et les étapes d’installation suivent les mêmes principes pour les deux machines.

    Les deux schémas ci-dessous servent de repère pour ces deux chapitres.

    <p align="center">
      <img src="../images/parametres-vm-windows-zorin.png" alt="Paramètres complets des machines virtuelles" width="60%">
    </p>

    <p align="center">
      <img src="../images/procedure-installation-vm.png" alt="Procédure générale d'installation d'une machine virtuelle" width="60%">
    </p>

??? note "8. La machine virtuelle Windows 11 Pro"
    La première machine virtuelle à installer sera une machine virtuelle Windows 11 Pro.

    Elle servira à observer le fonctionnement d’un système Windows dans VirtualBox.

    Cette machine virtuelle devra être créée avec les paramètres indiqués dans ce dossier.

    Les points importants à vérifier sont :

    * le nom de la machine virtuelle ;
    * le type de système ;
    * l’image ISO utilisée ;
    * la mémoire attribuée ;
    * le nombre de cœurs processeur ;
    * la taille du disque virtuel ;
    * le démarrage correct de l’installation ;
    * la création du compte utilisateur ;
    * l’arrêt propre de la machine virtuelle après installation ;
    * la création d’un instantané.

    Windows 11 peut demander une configuration plus stricte qu’une distribution Linux.

    Il faut donc suivre les consignes et ne pas modifier les paramètres au hasard.

    ### 8.1 Paramètres complets

    Utiliser les paramètres suivants, sauf consigne différente du professeur.

    | Paramètre | Valeur à utiliser |
    |---|---|
    | Nom de la machine virtuelle | VM-Windows-11-Pro |
    | Type | Microsoft Windows |
    | Version | Windows 11 64 bits |
    | Image ISO | ISO Windows 11 fournie ou indiquée |
    | Édition à installer | Windows 11 Pro |
    | Mémoire vive | 4 Go |
    | Processeur | 2 cœurs |
    | Disque virtuel | 64 Go |
    | Type de disque | VDI |
    | Stockage | Allocation dynamique |
    | Carte réseau | NAT pendant l’installation |
    | EFI | Activé |
    | TPM | Activé si disponible |
    | Secure Boot | Activé si disponible |
    | Mémoire vidéo | 128 Mo si disponible |

    Windows 11 demande plus de ressources qu’une distribution Linux légère.

    Si le poste devient lent, il faut fermer les applications inutiles et prévenir le professeur.

    ### 8.2 Créer la machine virtuelle

    Dans VirtualBox :

    1. créer une nouvelle machine virtuelle ;
    2. nommer la machine : VM-Windows-11-Pro ;
    3. choisir le type : Microsoft Windows ;
    4. choisir la version : Windows 11 64 bits ;
    5. sélectionner l’image ISO Windows 11 ;
    6. attribuer la mémoire vive demandée ;
    7. attribuer le nombre de processeurs demandé ;
    8. créer le disque virtuel ;
    9. vérifier les paramètres ;
    10. démarrer la machine virtuelle.

    Le nom d’une machine virtuelle doit être clair : il permet de savoir immédiatement à quoi correspond la machine.

    Ici, la machine s’appelle VM-Windows-11-Pro.

    Évitez les noms vagues comme test, machine, truc ou nouvelle VM.

    ### 8.3 Lancer l’installation

    Au démarrage de la machine virtuelle :

    1. attendre le lancement de l’installateur Windows ;
    2. choisir la langue demandée ;
    3. choisir le clavier adapté ;
    4. lancer l’installation ;
    5. choisir l’édition Windows 11 Pro lorsque l’installateur le demande ;
    6. accepter les conditions si elles sont demandées ;
    7. choisir une installation personnalisée si l’installateur le demande ;
    8. sélectionner le disque virtuel vide ;
    9. lancer l’installation ;
    10. attendre les redémarrages automatiques.

    Pendant l’installation, il ne faut pas éteindre brutalement la machine virtuelle.

    ### 8.4 Créer le compte utilisateur

    Lorsque l’installateur demande comment configurer l’appareil, choisir : Configurer pour une utilisation personnelle.

    Windows 11 Pro essaie ensuite d’imposer un compte Microsoft.

    Pour cette activité, il faut un compte local.

    Pour l’obtenir, sur l’écran « Ajoutez votre compte Microsoft » :

    1. appuyer sur Maj + F10 pour ouvrir l’invite de commandes ;
    2. taper la commande suivante, puis valider avec Entrée :

    ```cmd
    start ms-cxh:localonly
    ```

    3. dans la fenêtre « Créer un compte local » qui s’ouvre, créer le compte avec les informations imposées.

    | Élément | Valeur |
    |---|---|
    | Nom d’utilisateur | tne |
    | Mot de passe | Tne2026! |
    | Indice de mot de passe | classe |

    Si la commande ne fonctionne pas : couper la connexion réseau de la machine virtuelle dans le menu Périphériques, puis Réseau, décocher « Connecter la carte réseau », créer le compte local, puis reconnecter la carte réseau.

    En cas de doute, appeler le professeur.

    ### 8.5 Terminer l’installation

    Après la création du compte :

    1. attendre l’arrivée sur le bureau Windows ;
    2. vérifier que la session s’ouvre avec le compte demandé ;
    3. mettre Windows à jour : Démarrer, Paramètres, Windows Update, Rechercher des mises à jour, puis installer les mises à jour proposées ;
    4. redémarrer si Windows le demande, et relancer une recherche jusqu’à ce qu’il n’y ait plus de mise à jour ;
    5. arrêter proprement Windows ;
    6. revenir dans VirtualBox.

    Une fois la machine installée, à jour et arrêtée proprement, il faut créer un instantané de cet état propre.

    Cette étape est décrite dans le chapitre « L’instantané ».

    La machine virtuelle Windows 11 Pro est prête lorsque :

    * elle démarre correctement ;
    * le compte demandé fonctionne ;
    * le système est à jour ;
    * l’arrêt se fait correctement ;
    * l’instantané Installation propre existe.

??? note "9. La machine virtuelle Linux"
    La deuxième machine virtuelle à installer sera une machine virtuelle avec Zorin OS.

    Zorin OS est une distribution Linux conviviale, basée sur Ubuntu.

    Elle servira à comparer le fonctionnement d’un système Linux avec celui de Windows 11 dans VirtualBox.

    Cette machine virtuelle devra aussi être créée avec les paramètres indiqués dans ce dossier.

    Les points importants à vérifier sont :

    * le nom de la machine virtuelle ;
    * le type de système ;
    * l’image ISO utilisée ;
    * la mémoire attribuée ;
    * le nombre de cœurs processeur ;
    * la taille du disque virtuel ;
    * le démarrage correct de l’installation ;
    * la création du compte utilisateur ;
    * l’arrêt propre de la machine virtuelle après installation ;
    * la création d’un instantané.

    On utilise l’édition Zorin OS Lite, avec bureau XFCE, afin de pouvoir travailler confortablement dans une machine virtuelle.

    ### 9.1 Paramètres complets

    Utiliser les paramètres suivants, sauf consigne différente du professeur.

    | Paramètre | Valeur à utiliser |
    |---|---|
    | Nom de la machine virtuelle | VM-Zorin |
    | Type | Linux |
    | Version | Ubuntu 64 bits |
    | Image ISO | ISO Zorin OS Lite 64 bits téléchargée |
    | Mémoire vive | 4 Go |
    | Processeur | 2 cœurs |
    | Disque virtuel | 30 Go |
    | Type de disque | VDI |
    | Stockage | Allocation dynamique |
    | Carte réseau | NAT pendant l’installation |
    | Mémoire vidéo | 128 Mo |
    | Édition conseillée | Zorin OS Lite |

    Comme Zorin OS est basé sur Ubuntu, on choisit le type Ubuntu 64 bits dans VirtualBox.

    ### 9.2 Créer la machine virtuelle

    Dans VirtualBox :

    1. créer une nouvelle machine virtuelle ;
    2. nommer la machine : VM-Zorin ;
    3. choisir le type : Linux ;
    4. choisir la version : Ubuntu 64 bits ;
    5. sélectionner l’image ISO Zorin OS ;
    6. attribuer la mémoire vive demandée ;
    7. attribuer le nombre de processeurs demandé ;
    8. créer le disque virtuel ;
    9. vérifier les paramètres ;
    10. démarrer la machine virtuelle.

    Comme pour la machine Windows, donnez un nom clair : ici VM-Zorin.

    Évitez les noms vagues comme test, machine ou truc.

    ### 9.3 Lancer l’installation

    Au démarrage de la machine virtuelle :

    1. laisser Zorin OS démarrer ;
    2. choisir « Try or Install Zorin OS » si un menu apparaît ;
    3. attendre le chargement du bureau Zorin en session live ;
    4. lancer « Installer Zorin OS » depuis l’icône présente sur le bureau ;
    5. choisir la langue : Français ;
    6. choisir la disposition du clavier : Français ;
    7. au choix des logiciels, prendre « Installation minimale » pour une machine légère ;
    8. cocher « Télécharger les mises à jour pendant l’installation » si le réseau le permet.

    ### 9.4 Choisir le type d’installation

    Pour cette activité, choisir : Effacer le disque et installer Zorin OS.

    Attention : cela concerne uniquement le disque virtuel de la machine virtuelle.

    Cela ne doit pas effacer le disque réel de la machine hôte.

    Lancer ensuite l’installation, puis choisir le fuseau horaire si l’installateur le demande.

    ### 9.5 Créer le compte utilisateur

    Lorsque l’installateur demande les identifiants, utiliser les valeurs imposées.

    | Élément | Valeur |
    |---|---|
    | Nom complet | Utilisateur TNE |
    | Nom de l’ordinateur | zorin-tne |
    | Nom d’utilisateur | tne |
    | Mot de passe | Tne2026! |

    Zorin OS, comme Ubuntu, utilise un seul compte qui dispose des droits d’administration.

    Il n’y a pas de mot de passe administrateur séparé.

    Choisir « Demander mon mot de passe pour ouvrir une session ».

    Il faut écrire le mot de passe avec attention.

    Une erreur dans le mot de passe empêchera l’ouverture de session.

    ### 9.6 Terminer l’installation

    À la fin de l’installation :

    1. attendre la fin de la copie des fichiers ;
    2. cliquer sur « Redémarrer maintenant » ;
    3. retirer le support d’installation si l’installateur le demande, puis appuyer sur Entrée ;
    4. ouvrir la session avec le compte tne ;
    5. vérifier que le bureau s’affiche correctement ;
    6. mettre le système à jour ;
    7. arrêter proprement Zorin OS ;
    8. revenir dans VirtualBox.

    Pour mettre Zorin OS à jour, ouvrir un terminal et lancer les commandes suivantes, en saisissant le mot de passe du compte tne :

    ```bash
    sudo apt update
    sudo apt upgrade
    ```

    On peut aussi passer par l’outil graphique « Mise à jour de logiciels » si Zorin OS le propose.

    Comme pour la machine Windows, il faut ensuite créer un instantané de cet état propre.

    Cette étape est décrite dans le chapitre « L’instantané ».

    La machine virtuelle Zorin OS est prête lorsque :

    * elle démarre correctement ;
    * le compte demandé fonctionne ;
    * le système est à jour ;
    * l’arrêt se fait correctement ;
    * l’instantané Installation propre existe.

??? note "10. Les additions invitées"
    Les additions invitées sont des pilotes et des outils à installer à l’intérieur de chaque machine virtuelle.

    Elles améliorent nettement le confort d’utilisation :

    * ajustement automatique de la résolution et passage en plein écran ;
    * pointeur de souris fluide, sans capture du clavier ;
    * presse-papiers partagé entre la machine hôte et la machine virtuelle ;
    * dossiers partagés entre l’hôte et l’invité.

    Sans les additions invitées, l’affichage reste souvent en petite résolution et la souris est moins fluide.

    Les additions invitées s’installent une fois le système installé, séparément dans chaque machine virtuelle.

    ### 10.1 Additions invitées sur Windows 11

    1. démarrer la machine virtuelle Windows et ouvrir la session tne ;
    2. dans le menu de la fenêtre VirtualBox : Périphériques, puis Insérer l’image CD des Additions invitées ;
    3. dans Windows, ouvrir l’Explorateur de fichiers, puis le lecteur CD « VirtualBox Guest Additions » ;
    4. lancer VBoxWindowsAdditions.exe et suivre l’assistant ;
    5. redémarrer Windows à la fin de l’installation.

    Après le redémarrage, la fenêtre de la machine virtuelle peut se redimensionner et passer en plein écran.

    ### 10.2 Additions invitées sur Zorin OS

    Zorin OS a besoin des outils de compilation pour construire les additions invitées.

    Ouvrir un terminal et installer les paquets nécessaires :

    ```bash
    sudo apt update
    sudo apt install build-essential dkms linux-headers-$(uname -r)
    ```

    Dans le menu de la fenêtre VirtualBox : Périphériques, puis Insérer l’image CD des Additions invitées.

    Monter le CD et lancer l’installateur :

    ```bash
    sudo mkdir -p /mnt/cdrom
    sudo mount /dev/cdrom /mnt/cdrom
    cd /mnt/cdrom
    sudo sh ./VBoxLinuxAdditions.run
    sudo reboot
    ```

    Après le redémarrage, l’affichage s’ajuste automatiquement à la taille de la fenêtre.

??? note "11. Démarrer et arrêter une machine virtuelle"
    Une machine virtuelle doit être arrêtée correctement.

    Il ne faut pas fermer brutalement la fenêtre de la machine virtuelle sans comprendre ce que l’on fait.

    Pour arrêter correctement une machine virtuelle, il faut utiliser l’arrêt du système invité.

    Exemples :

    * dans Windows 11 : menu démarrer, puis arrêt ;
    * dans Zorin OS : menu d’arrêt ou commande adaptée.

    Si la machine virtuelle est arrêtée brutalement, le système invité peut être endommagé.

??? note "12. L’instantané"
    Un instantané est une sauvegarde de l’état d’une machine virtuelle à un moment précis.

    Le mot anglais souvent utilisé dans VirtualBox est “snapshot”.

    Dans ce dossier, on utilise le mot français : instantané.

    Un instantané permet de revenir à un état précédent.

    Exemple :

    1. la machine virtuelle vient d’être installée proprement ;
    2. un instantané est créé ;
    3. une erreur est faite plus tard ;
    4. l’instantané permet de revenir à un état propre.

    L’instantané est très utile en apprentissage.

    Il permet de faire des essais sans tout recommencer depuis le début.

    <p align="center">
      <img src="../images/instantane-machine-virtuelle.png" alt="L'instantané d'une machine virtuelle" width="60%">
    </p>

    Il faut créer un instantané lorsque la machine virtuelle est dans un état propre et stable.

    Dans cette activité, l’instantané doit être créé après l’installation correcte du système invité.

    L’instantané doit avoir un nom clair.

    | Machine virtuelle | Nom de l’instantané |
    |---|---|
    | Windows 11 Pro | Installation propre |
    | Zorin OS | Installation propre |

    Un nom clair permet de savoir à quel moment on peut revenir.

??? note "13. Les erreurs fréquentes"
    <p align="center">
      <img src="../images/erreurs-virtualbox.png" alt="Les erreurs fréquentes dans VirtualBox" width="60%">
    </p>

    ### 13.1 Donner trop de mémoire à une machine virtuelle

    Si la machine virtuelle reçoit trop de mémoire, la machine hôte peut devenir lente.

    Il faut respecter la valeur demandée dans ce dossier ou par le professeur.

    ### 13.2 Choisir le mauvais type de système

    VirtualBox demande le type de système à installer.

    Si le mauvais type est choisi, l’installation peut être plus difficile ou mal configurée.

    Il faut choisir le type correspondant au système invité.

    ### 13.3 Utiliser la mauvaise image ISO

    Une mauvaise image ISO peut empêcher l’installation.

    Il faut utiliser l’image indiquée par le professeur.

    ### 13.4 Créer un disque virtuel trop petit

    Si le disque virtuel est trop petit, l’installation peut échouer ou manquer d’espace rapidement.

    Il faut respecter la taille demandée dans ce dossier ou par le professeur.

    ### 13.5 Éteindre brutalement la machine virtuelle

    Une fermeture brutale peut provoquer des erreurs dans le système invité.

    Il faut arrêter proprement la machine virtuelle.

    ### 13.6 Oublier de créer l’instantané

    Si aucun instantané n’est créé après une installation propre, il sera plus difficile de revenir en arrière en cas d’erreur.

    L’instantané fait partie du travail demandé.

    ### 13.7 Utiliser un identifiant personnel

    Il ne faut pas utiliser d’identifiant personnel dans les machines virtuelles de cette activité.

    Les machines virtuelles doivent utiliser les identifiants communs de classe.

??? note "14. Vérification finale avant le palier 3"
    Avant de passer au palier 3, les deux machines virtuelles doivent être prêtes.

    | Vérification | Windows 11 Pro | Zorin OS |
    |---|---|---|
    | La machine virtuelle existe | Oui | Oui |
    | Elle démarre correctement | Oui | Oui |
    | Le compte tne fonctionne | Oui | Oui |
    | Le mot de passe commun fonctionne | Oui | Oui |
    | Le système est à jour | Oui | Oui |
    | La machine s’arrête proprement | Oui | Oui |
    | L’instantané Installation propre existe | Oui | Oui |

    Le palier 2 est terminé lorsque les deux machines virtuelles sont installées, accessibles avec les identifiants demandés et sauvegardées par un instantané.

??? note "15. Ce qu’il faut retenir"
    VirtualBox permet de créer des machines virtuelles.

    La machine hôte est le poste réel sous Debian 13.

    La machine invitée est la machine virtuelle créée dans VirtualBox.

    Une machine virtuelle utilise des ressources de la machine hôte :

    * mémoire vive ;
    * processeur ;
    * disque ;
    * carte réseau virtuelle.

    Une image ISO sert à installer un système d’exploitation.

    Un disque virtuel contient le système invité et ses fichiers.

    Les machines virtuelles de classe utilisent des identifiants communs afin que le professeur puisse les vérifier.

    Un instantané permet de revenir à un état propre.

    Les machines virtuelles doivent être nommées clairement, configurées proprement et arrêtées correctement.

??? info "Activité à réaliser"
    Vous avez maintenant les informations nécessaires pour passer à la partie pratique.

    Important : vous commencez par le QCM. Vous ne démarrez l’activité que lorsque votre QCM est validé à 100 %.

    Marche à suivre :

    1. [Télécharger le QCM du palier 2](eleve/qcm-palier-2.pdf), puis répondez à toutes les questions.
    2. Faites valider votre QCM. Tant qu’il n’est pas correct à 100 %, vous ne passez pas à l’activité.
    3. Une fois le QCM validé à 100 %, [télécharger l’activité : installer deux machines virtuelles avec VirtualBox](eleve/activite-palier-2.pdf) et réalisez les étapes demandées.

    Pendant l’activité, vous devrez revenir dans ce dossier technique chaque fois que vous aurez besoin d’une information.