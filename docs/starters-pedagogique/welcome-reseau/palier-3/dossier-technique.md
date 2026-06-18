# Palier 3 : relever les informations réseau et tester les modes simples VirtualBox

## Dossier technique

## Objectif du dossier technique

Ce dossier donne les connaissances nécessaires pour relever les informations réseau et tester les premiers modes réseau de VirtualBox.

Dans ce palier, vous allez travailler avec :

* la machine hôte sous Debian 13 ;
* la machine virtuelle Windows 11 Pro ;
* la machine virtuelle Zorin OS.

À la fin de cette lecture, vous devez être capable de comprendre :

* le rôle de la machine hôte ;
* le rôle des machines virtuelles ;
* le rôle d’une carte réseau réelle ;
* le rôle d’une carte réseau virtuelle ;
* le rôle d’une adresse IP ;
* le rôle d’un masque réseau ;
* le rôle d’une passerelle ;
* comment relever le nom et l’adresse IP d’une machine ;
* comment utiliser les commandes réseau de base ;
* comment tester une communication avec `ping` ;
* comment changer le mode réseau d’une machine virtuelle dans VirtualBox ;
* la différence entre le mode NAT et le mode accès par pont ;
* les résultats attendus avec ces deux modes.

Dans ce palier, vous ne configurez pas encore d’adresse IP fixe.

Le réseau interne entre deux machines virtuelles sera étudié dans le palier suivant.

??? note "1. Les machines utilisées dans ce palier"
    <p align="center">
      <img src="../images/01-hote-et-machines-virtuelles.png" alt="Les machines utilisées dans ce palier" width="60%">
    </p>

    Dans ce palier, trois machines sont utilisées.

    | Machine | Type | Rôle |
    |---|---|---|
    | Debian 13 | Machine réelle | Machine hôte |
    | Windows 11 Pro | Machine virtuelle | Machine invitée |
    | Zorin OS | Machine virtuelle | Machine invitée |

    La machine hôte est l’ordinateur réel de la salle.

    Les machines virtuelles sont les machines installées dans VirtualBox pendant le palier 2.

    La machine hôte possède une carte réseau réelle.

    Les machines virtuelles possèdent des cartes réseau virtuelles créées par VirtualBox.

    À retenir :

    * Debian 13 est la machine réelle ;
    * Windows 11 Pro et Zorin OS sont des machines virtuelles ;
    * VirtualBox permet de connecter les cartes réseau virtuelles selon différents modes ;
    * le mode réseau choisi détermine avec qui la machine virtuelle peut communiquer.

??? note "2. Carte réseau réelle et carte réseau virtuelle"
    <p align="center">
      <img src="../images/02-cartes-reseau-reelle-et-virtuelles.png" alt="Carte réseau réelle et cartes réseau virtuelles" width="60%">
    </p>

    Une carte réseau permet à une machine de communiquer avec un réseau.

    La machine hôte Debian 13 possède une carte réseau réelle.

    Cette carte peut être :

    * une carte Ethernet ;
    * une carte Wi-Fi ;
    * une autre interface réseau présente sur le poste.

    Une machine virtuelle ne possède pas directement une carte réseau physique.

    VirtualBox lui fournit une carte réseau virtuelle.

    Cette carte réseau virtuelle est simulée par le logiciel VirtualBox.

    La machine virtuelle voit cette carte comme une vraie carte réseau.

    À retenir :

    | Élément | Exemple | Type |
    |---|---|---|
    | Carte réseau Debian 13 | Ethernet ou Wi-Fi | Réelle |
    | Carte réseau Windows 11 Pro | Adaptateur VirtualBox | Virtuelle |
    | Carte réseau Zorin OS | Adaptateur VirtualBox | Virtuelle |

    La carte réseau virtuelle permet à la VM de communiquer, mais seulement selon le mode réseau choisi dans VirtualBox.

??? note "3. Ce que l’on va tester dans ce palier"
    <p align="center">
      <img src="../images/03-tests-mode-nat-et-pont.png" alt="Les tests des modes NAT et accès par pont" width="60%">
    </p>

    Dans ce palier, vous allez tester deux modes réseau simples :

    * le mode NAT ;
    * le mode accès par pont.

    Le but est d’observer les différences entre ces deux modes.

    Vous allez vérifier :

    * si la machine virtuelle reçoit une adresse IP ;
    * si la machine virtuelle peut accéder à Internet ;
    * si la machine virtuelle semble appartenir au même réseau que la machine hôte ;
    * si le résultat observé correspond au mode réseau choisi.

    Vous devez apprendre à ne pas conclure trop vite.

    Un test réseau doit toujours suivre une méthode :

    1. identifier la machine utilisée ;
    2. relever son nom ;
    3. relever son adresse IP ;
    4. vérifier le mode réseau VirtualBox ;
    5. faire le test demandé ;
    6. noter le résultat ;
    7. comparer avec le résultat attendu.

??? note "4. Adresse IP, masque et passerelle"
    <p align="center">
      <img src="../images/04-adresse-ip-masque-passerelle.png" alt="Adresse IP, masque réseau et passerelle" width="60%">
    </p>

    Une adresse IP permet d’identifier une machine sur un réseau.

    Exemple :

    ```text
    192.168.1.25
    ```

    Une adresse IPv4 est composée de 4 nombres séparés par des points.

    Chaque nombre est appelé un octet.

    Exemple :

    | Adresse IP | Octet 1 | Octet 2 | Octet 3 | Octet 4 |
    |---|---:|---:|---:|---:|
    | 192.168.1.25 | 192 | 168 | 1 | 25 |

    Un octet peut aller de 0 à 255.

    Le masque réseau sert à savoir quelle partie de l’adresse correspond au réseau.

    Exemple de masque courant :

    ```text
    255.255.255.0
    ```

    Avec ce masque, les trois premiers octets indiquent généralement le réseau.

    Exemple :

    | Machine | Adresse IP | Masque | Réseau |
    |---|---|---|---|
    | Debian 13 | 192.168.1.12 | 255.255.255.0 | 192.168.1.0 |
    | VM en accès par pont | 192.168.1.25 | 255.255.255.0 | 192.168.1.0 |

    Dans cet exemple, les deux machines sont dans le même réseau logique.

    La passerelle est l’adresse de l’équipement qui permet de sortir du réseau local.

    Dans une maison ou un établissement, la passerelle est souvent la box, le routeur ou un équipement réseau de l’établissement.

    Exemple :

    ```text
    Passerelle : 192.168.1.1
    ```

    À retenir :

    | Élément | Rôle |
    |---|---|
    | Adresse IP | Identifie une machine |
    | Masque | Indique la partie réseau de l’adresse |
    | Passerelle | Permet de sortir du réseau local |
    | DNS | Permet de traduire un nom de site en adresse IP |

??? note "5. DHCP et adresse IP automatique"
    <p align="center">
      <img src="../images/05-dhcp-adresse-ip-automatique.png" alt="DHCP et adresse IP automatique" width="60%">
    </p>

    Une machine peut recevoir son adresse IP automatiquement.

    Ce mécanisme s’appelle DHCP.

    Le DHCP évite de régler l’adresse IP à la main.

    Dans ce palier, vous utilisez uniquement des adresses automatiques.

    Vous ne configurez pas encore d’adresse IP fixe.

    Le DHCP peut venir :

    * de VirtualBox en mode NAT ;
    * du réseau réel en mode accès par pont.

    Exemple en mode NAT :

    | Élément | Rôle |
    |---|---|
    | VirtualBox | Donne une adresse IP à la VM |
    | VM | Utilise cette adresse pour communiquer |
    | Hôte | Sert d’intermédiaire vers le réseau extérieur |

    Exemple en mode accès par pont :

    | Élément | Rôle |
    |---|---|
    | Réseau réel | Donne une adresse IP à la VM |
    | VM | Apparaît presque comme une machine réelle |
    | Hôte | N’est plus le seul intermédiaire |

    À retenir :

    * en mode NAT, VirtualBox donne généralement l’adresse IP à la VM ;
    * en mode accès par pont, le réseau réel donne généralement l’adresse IP à la VM ;
    * dans ce palier, vous observez les adresses IP, vous ne les modifiez pas manuellement.

??? note "6. Commandes utiles sous Debian 13 et Zorin OS"
    <p align="center">
      <img src="../images/06-commandes-reseau-linux.png" alt="Commandes réseau utiles sous Linux" width="60%">
    </p>

    Sous Debian 13 et Zorin OS, les commandes réseau se lancent dans le terminal.

    Elles permettent d’identifier la machine, de relever son adresse IP et de tester une communication.

    | Commande | Rôle |
    |---|---|
    | `hostname` | Afficher le nom de la machine |
    | `hostname -I` | Afficher rapidement les adresses IP de la machine |
    | `ip a` | Afficher les interfaces réseau et les adresses IP |
    | `ip route` | Afficher les routes réseau et la passerelle |
    | `ping adresse_ip` | Tester si une machine répond |
    | `ping -c 4 adresse_ip` | Envoyer seulement 4 tests ping |

    Exemple pour afficher le nom de la machine :

    ```bash
    hostname
    ```

    Exemple pour afficher rapidement l’adresse IP :

    ```bash
    hostname -I
    ```

    Exemple pour afficher les interfaces réseau :

    ```bash
    ip a
    ```

    Exemple pour afficher la passerelle :

    ```bash
    ip route
    ```

    Exemple pour tester une communication :

    ```bash
    ping 192.168.1.1
    ```

    Exemple pour envoyer seulement 4 tests :

    ```bash
    ping -c 4 192.168.1.1
    ```

    Pour arrêter un ping qui continue :

    ```text
    Ctrl + C
    ```

??? note "7. Commandes utiles sous Windows 11 Pro"
    <p align="center">
      <img src="../images/07-commandes-reseau-windows.png" alt="Commandes réseau utiles sous Windows" width="60%">
    </p>

    Sous Windows 11 Pro, les commandes réseau se lancent dans le terminal Windows ou l’invite de commandes.

    | Commande | Rôle |
    |---|---|
    | `hostname` | Afficher le nom de la machine |
    | `ipconfig` | Afficher l’adresse IP, le masque et la passerelle |
    | `ping adresse_ip` | Tester si une machine répond |
    | `ping -n 4 adresse_ip` | Envoyer seulement 4 tests ping |

    Exemple pour afficher le nom de la machine :

    ```text
    hostname
    ```

    Exemple pour afficher l’adresse IP :

    ```text
    ipconfig
    ```

    Exemple pour tester une communication :

    ```text
    ping 192.168.1.1
    ```

    Exemple pour envoyer seulement 4 tests :

    ```text
    ping -n 4 192.168.1.1
    ```

    Pour arrêter un ping qui continue :

    ```text
    Ctrl + C
    ```

    Dans `ipconfig`, il faut repérer principalement :

    * l’adresse IPv4 ;
    * le masque de sous-réseau ;
    * la passerelle par défaut.

??? note "8. Méthode de relevé des informations réseau"
    Avant de faire un test, il faut relever les informations de chaque machine.

    Pour chaque machine, vous devez pouvoir indiquer :

    * son nom ;
    * son adresse IP ;
    * son masque ;
    * sa passerelle si elle existe ;
    * le mode réseau VirtualBox utilisé pour la VM.

    Tableau de relevé à utiliser :

    | Information | Debian 13 | Windows 11 Pro | Zorin OS |
    |---|---|---|---|
    | Nom de la machine | `hostname` | `hostname` | `hostname` |
    | Adresse IP | `hostname -I` ou `ip a` | `ipconfig` | `hostname -I` ou `ip a` |
    | Masque | `ip a` | `ipconfig` | `ip a` |
    | Passerelle | `ip route` | `ipconfig` | `ip route` |
    | Test réseau | `ping` | `ping` | `ping` |

    Il ne faut pas recopier une adresse IP au hasard.

    Une adresse IP doit toujours être relevée sur la machine concernée.

??? note "9. Comprendre le mode NAT"
    <p align="center">
      <img src="../images/09-comprendre-mode-nat.png" alt="Le mode NAT dans VirtualBox" width="60%">
    </p>

    Le mode NAT permet à une machine virtuelle d’accéder au réseau en passant par la machine hôte.

    C’est le mode le plus simple pour donner Internet à une VM.

    En mode NAT :

    * la VM peut généralement accéder à Internet si l’hôte a Internet ;
    * VirtualBox donne généralement une adresse IP à la VM ;
    * la VM n’apparaît pas comme une machine réelle du réseau local ;
    * les autres machines du réseau réel ne voient pas directement la VM ;
    * la VM passe par l’hôte pour sortir vers le réseau.

    Exemple de situation :

    | Élément | Rôle |
    |---|---|
    | Debian 13 | Machine hôte connectée au réseau |
    | VirtualBox | Intermédiaire réseau |
    | VM Windows ou Zorin | Utilise NAT pour accéder au réseau |

    Usage principal du mode NAT :

    * faire les mises à jour ;
    * accéder à Internet ;
    * télécharger des paquets ou des logiciels ;
    * travailler simplement sans exposer la VM au réseau réel.

    Le mode NAT est généralement le mode le plus sûr pour commencer.

??? note "10. Tester le mode NAT"
    <p align="center">
      <img src="../images/10-tester-mode-nat-virtualbox.png" alt="Tester le mode NAT dans VirtualBox" width="60%">
    </p>

    Pour tester le mode NAT, la machine virtuelle doit être configurée en NAT dans VirtualBox.

    La machine virtuelle doit être arrêtée proprement avant de modifier son mode réseau.

    Procédure dans VirtualBox :

    1. sélectionner la machine virtuelle ;
    2. cliquer sur **Configuration** ;
    3. ouvrir **Réseau** ;
    4. choisir **Adaptateur 1** ;
    5. vérifier que **Activer la carte réseau** est coché ;
    6. choisir **NAT** dans **Mode d’accès réseau** ;
    7. valider avec **OK** ;
    8. démarrer la machine virtuelle ;
    9. relever son adresse IP ;
    10. faire les tests demandés.

    Tests possibles en mode NAT :

    | Test | Résultat attendu |
    |---|---|
    | Relever une adresse IP | La VM possède une adresse IP |
    | Tester Internet | Fonctionne si l’hôte a Internet |
    | Comparer l’adresse IP avec celle de l’hôte | La VM n’est généralement pas dans le même réseau que l’hôte |
    | Voir la VM depuis le réseau réel | Non, pas directement |

    Exemples de tests :

    Sous Zorin OS :

    ```bash
    hostname
    hostname -I
    ip route
    ping -c 4 8.8.8.8
    ```

    Sous Windows 11 Pro :

    ```text
    hostname
    ipconfig
    ping -n 4 8.8.8.8
    ```

    Si le ping vers `8.8.8.8` fonctionne, la machine communique avec une adresse IP extérieure.

    Si un site Internet ne s’ouvre pas alors que le ping vers `8.8.8.8` fonctionne, le problème peut venir du DNS.

??? note "11. Comprendre le mode accès par pont"
    <p align="center">
      <img src="../images/11-comprendre-mod-pont.png" alt="Le mode accès par pont dans VirtualBox" width="60%">
    </p>

    Le mode accès par pont connecte la machine virtuelle au réseau réel.

    Dans ce mode, la VM se comporte presque comme une machine physique du réseau.

    En mode accès par pont :

    * la VM peut recevoir une adresse IP du réseau réel ;
    * la VM peut accéder à Internet si le réseau l’autorise ;
    * la VM peut être dans le même réseau logique que la machine hôte ;
    * la VM peut être visible sur le réseau réel ;
    * la VM dépend davantage des règles du réseau de la salle.

    Exemple :

    | Machine | Adresse IP possible | Réseau |
    |---|---|---|
    | Debian 13 | 192.168.1.12 | 192.168.1.0 |
    | VM Zorin en accès par pont | 192.168.1.25 | 192.168.1.0 |

    Dans cet exemple, la machine hôte et la VM sont dans le même réseau logique.

    !!! warning "Mode accès par pont"
        Le mode accès par pont connecte la machine virtuelle au réseau réel de la salle.

        Il ne doit être utilisé que si le professeur l’autorise.

    Le mode accès par pont est utile pour comprendre qu’une VM peut se comporter comme une machine du réseau réel.

    Il faut l’utiliser avec prudence dans un établissement.

??? note "12. Tester le mode accès par pont"
    Pour tester le mode accès par pont, la machine virtuelle doit être configurée en accès par pont dans VirtualBox.

    La machine virtuelle doit être arrêtée proprement avant de modifier son mode réseau.

    Procédure dans VirtualBox :

    1. sélectionner la machine virtuelle ;
    2. cliquer sur **Configuration** ;
    3. ouvrir **Réseau** ;
    4. choisir **Adaptateur 1** ;
    5. vérifier que **Activer la carte réseau** est coché ;
    6. choisir **Accès par pont** dans **Mode d’accès réseau** ;
    7. choisir la carte réseau réelle utilisée par la machine hôte ;
    8. valider avec **OK** ;
    9. démarrer la machine virtuelle ;
    10. relever son adresse IP ;
    11. faire les tests demandés.

    La carte réseau réelle peut être :

    * une carte Ethernet ;
    * une carte Wi-Fi.

    Il faut choisir la carte réellement utilisée par Debian 13 pour accéder au réseau.

    Tests possibles en mode accès par pont :

    | Test | Résultat attendu |
    |---|---|
    | Relever une adresse IP | La VM possède une adresse IP donnée par le réseau réel |
    | Comparer l’adresse IP avec celle de l’hôte | Les adresses peuvent appartenir au même réseau |
    | Tester Internet | Fonctionne si le réseau l’autorise |
    | Tester la passerelle | La VM peut joindre la passerelle si le réseau l’autorise |
    | Voir la VM sur le réseau réel | Possible |

    Exemples de tests :

    Sous Zorin OS :

    ```bash
    hostname
    hostname -I
    ip route
    ping -c 4 adresse_de_la_passerelle
    ```

    Sous Windows 11 Pro :

    ```text
    hostname
    ipconfig
    ping -n 4 adresse_de_la_passerelle
    ```

    L’adresse de la passerelle doit être relevée sur la machine avec `ip route` ou `ipconfig`.

??? note "13. Comparer NAT et accès par pont"
    <p align="center">
      <img src="../images/13-comparaison-nat-pont.png" alt="Comparaison entre NAT et accès par pont" width="60%">
    </p>

    Le mode NAT et le mode accès par pont ne donnent pas le même comportement.

    Tableau de comparaison :

    | Point comparé | NAT | Accès par pont |
    |---|---|---|
    | Adresse IP donnée par | VirtualBox | Réseau réel |
    | Accès Internet | Oui, si l’hôte a Internet | Oui, si le réseau l’autorise |
    | VM visible sur le réseau réel | Non directement | Oui, généralement |
    | Simplicité | Plus simple | Plus proche d’une vraie machine réseau |
    | Prudence nécessaire | Faible | Plus importante |
    | Usage principal | Mise à jour et Internet simple | Test d’intégration au réseau réel |

    Aucun mode n’est meilleur dans tous les cas.

    Le bon mode dépend du test à réaliser.

    Pour installer ou mettre à jour une VM, le mode NAT est souvent suffisant.

    Pour observer une VM comme une machine du réseau réel, le mode accès par pont est plus adapté, mais il doit être autorisé par le professeur.

??? note "14. Tests attendus dans ce palier"
    Dans ce palier, vous devez principalement observer et comparer.

    Vous ne devez pas modifier les adresses IP à la main.

    Tests attendus en mode NAT :

    | Machine | Test | Résultat attendu |
    |---|---|---|
    | Windows 11 Pro | Relever l’adresse IP | Une adresse IP est présente |
    | Windows 11 Pro | Tester `ping -n 4 8.8.8.8` | Fonctionne si l’hôte a Internet |
    | Zorin OS | Relever l’adresse IP | Une adresse IP est présente |
    | Zorin OS | Tester `ping -c 4 8.8.8.8` | Fonctionne si l’hôte a Internet |

    Tests attendus en mode accès par pont :

    | Machine | Test | Résultat attendu |
    |---|---|---|
    | Windows 11 Pro | Relever l’adresse IP | Adresse donnée par le réseau réel |
    | Windows 11 Pro | Comparer avec l’adresse IP de Debian 13 | Réseau souvent identique |
    | Zorin OS | Relever l’adresse IP | Adresse donnée par le réseau réel |
    | Zorin OS | Comparer avec l’adresse IP de Debian 13 | Réseau souvent identique |

    Si le mode accès par pont ne fonctionne pas, cela peut venir des règles du réseau de la salle.

    Il ne faut pas modifier les paramètres au hasard.

    Il faut demander au professeur en expliquant le test réalisé.

??? note "15. Méthode simple si un test ne fonctionne pas"
    Si un test ne fonctionne pas, il faut suivre une méthode simple.

    Ne modifiez pas plusieurs paramètres en même temps.

    Ordre de vérification :

    1. vérifier que la VM est démarrée ;
    2. vérifier que la carte réseau virtuelle est activée ;
    3. vérifier le mode réseau choisi dans VirtualBox ;
    4. vérifier que l’adresse IP est bien relevée ;
    5. vérifier que l’adresse testée est correcte ;
    6. refaire le test avec la bonne commande ;
    7. redémarrer la VM si le changement de mode réseau n’a pas été pris en compte ;
    8. demander de l’aide si le problème reste présent.

    Une demande d’aide doit préciser :

    * la machine utilisée ;
    * le mode réseau utilisé ;
    * la commande lancée ;
    * le résultat obtenu ;
    * le chapitre du dossier technique consulté.

    Exemple de demande correcte :

    > Je travaille sur la VM Zorin OS en mode NAT.  
    > J’ai relevé l’adresse IP avec `hostname -I`.  
    > J’ai lancé `ping -c 4 8.8.8.8`, mais les paquets ne répondent pas.  
    > J’ai vérifié le chapitre sur le mode NAT.  
    > J’ai besoin d’aide pour savoir si le problème vient de la VM ou du réseau.

??? note "16. Ce qu’il faut retenir"
    Une machine virtuelle utilise une carte réseau virtuelle.

    Le mode réseau VirtualBox détermine avec qui la machine virtuelle peut communiquer.

    En mode NAT, la VM passe par VirtualBox et par la machine hôte pour accéder au réseau.

    En mode accès par pont, la VM est connectée au réseau réel de la salle.

    Une adresse IP identifie une machine sur un réseau.

    Le masque permet de savoir à quel réseau appartient une adresse IP.

    La passerelle permet de sortir du réseau local.

    Les commandes utiles sont :

    | Système | Commandes principales |
    |---|---|
    | Debian 13 | `hostname`, `hostname -I`, `ip a`, `ip route`, `ping` |
    | Zorin OS | `hostname`, `hostname -I`, `ip a`, `ip route`, `ping` |
    | Windows 11 Pro | `hostname`, `ipconfig`, `ping` |

    Dans ce palier, vous relevez, vous testez et vous comparez.

    Vous ne configurez pas encore d’adresse IP fixe.

    Le réseau interne entre deux VM sera étudié dans le palier suivant.

??? info "Activité à réaliser"
    Vous avez maintenant les informations nécessaires pour passer à la partie pratique.

    Important : vous commencez par le QCM. Vous ne démarrez l’activité que lorsque votre QCM est validé à 100 %.

    Marche à suivre :

    1. [Ouvrir le QCM du palier 3](eleve/qcm-palier-3.pdf), puis répondez à toutes les questions.
    2. Enregistrez vos réponses dans le fichier demandé.
    3. Faites valider votre QCM. Tant qu’il n’est pas correct à 100 %, vous ne passez pas à l’activité.
    4. Une fois le QCM validé à 100 %, [ouvrir l’activité du palier 3](eleve/activite-palier-3.pdf).
    5. Complétez la checklist de validation avant de demander la validation du professeur.

    Pendant l’activité, vous devrez revenir dans ce dossier technique chaque fois que vous aurez besoin d’une information.