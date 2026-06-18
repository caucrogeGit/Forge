<!--
PAGE TEMPORAIRE - support de cours, sans aucune relation avec le framework Forge.
A SUPPRIMER le 2026-06-28 (voir docs/vacances/welcome-vacance.md).
-->

[Semaine réseau et virtualisation](../welcome-vacance.md) <a href="javascript:void(0)" onclick="window.history.back()"> / Retour</a>

# Palier 3 : Réseau IP et communication entre l’hôte et les machines virtuelles

## Dossier technique

## Objectif du dossier technique

Ce dossier donne les connaissances nécessaires pour tester les communications réseau entre :

* la machine hôte sous Debian 13 ;
* la machine virtuelle Windows 11 Pro ;
* la machine virtuelle Zorin OS.

À la fin de cette lecture, vous devez être capable de comprendre :

* le rôle d’une carte réseau réelle ;
* le rôle d’une carte réseau virtuelle ;
* le rôle d’une adresse IP ;
* le rôle d’un masque réseau ;
* comment convertir un octet en binaire avec un tableau de puissances de 2 ;
* comment vérifier si deux machines appartiennent au même réseau ;
* comment utiliser les commandes `hostname`, `hostname -I`, `ip a`, `ip route`, `ipconfig` et `ping` ;
* la différence entre les modes NAT, accès par pont, réseau interne et réseau privé hôte ;
* comment diagnostiquer une communication réseau qui ne fonctionne pas.

??? note "1. Pourquoi tester les modes réseau VirtualBox"
    Une machine virtuelle peut communiquer de plusieurs manières.

    Dans VirtualBox, le mode réseau choisi détermine avec qui la machine virtuelle peut communiquer.

    Une machine virtuelle peut par exemple :

    * accéder à Internet ;
    * communiquer avec la machine hôte ;
    * communiquer avec une autre machine virtuelle ;
    * apparaître comme une machine réelle du réseau local ;
    * rester isolée du réseau réel.

    Le but de ce palier est de comparer ces comportements.

    Il ne faut pas modifier un mode réseau au hasard.

    Avant de changer un mode réseau, il faut comprendre ce que l’on veut tester.

??? note "2. Machine hôte, machines virtuelles et cartes réseau"
    Dans ce palier, trois machines sont utilisées.

    | Machine | Rôle |
    |---|---|
    | Debian 13 | Machine hôte réelle |
    | Windows 11 Pro | Machine virtuelle |
    | Zorin OS | Machine virtuelle |

    La machine hôte possède une carte réseau réelle.

    Les machines virtuelles possèdent des cartes réseau virtuelles créées par VirtualBox.

    Une carte réseau virtuelle permet à une machine virtuelle de communiquer, mais cette communication dépend du mode réseau choisi dans VirtualBox.

    À retenir :

    * la carte réseau de Debian 13 est réelle ;
    * les cartes réseau des VM sont simulées ;
    * VirtualBox relie les cartes virtuelles au réseau selon le mode choisi.

??? note "3. Adresse IP et masque réseau"
    Une adresse IP permet d’identifier une machine sur un réseau.

    Exemple :

    ```text
    192.168.10.20
    ```

    Une adresse IPv4 est composée de 4 nombres séparés par des points.

    Chaque nombre est appelé un octet.

    Exemple :

    | Adresse IP | Octet 1 | Octet 2 | Octet 3 | Octet 4 |
    |---|---:|---:|---:|---:|
    | 192.168.10.20 | 192 | 168 | 10 | 20 |

    Un octet peut aller de 0 à 255.

    Le masque réseau sert à savoir quelle partie de l’adresse correspond au réseau.

    Exemple de masque courant :

    ```text
    255.255.255.0
    ```

    Avec ce masque, les trois premiers octets indiquent le réseau.

    Exemple :

    | Machine | Adresse IP | Masque | Réseau |
    |---|---|---|---|
    | Zorin OS | 192.168.10.10 | 255.255.255.0 | 192.168.10.0 |
    | Windows 11 Pro | 192.168.10.20 | 255.255.255.0 | 192.168.10.0 |

    Les deux machines sont dans le même réseau logique.

    Elles peuvent donc communiquer si le mode réseau VirtualBox le permet.

??? note "4. Calcul binaire d’un octet avec les puissances de 2"
    Un octet contient 8 bits.

    Chaque bit correspond à une puissance de 2.

    Tableau des puissances de 2 sur un octet :

    | Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
    |---|---:|---:|---:|---:|---:|---:|---:|---:|
    | Valeur | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |

    Pour convertir un nombre décimal en binaire, on cherche quelles valeurs il faut additionner.

    Exemple avec 192 :

    | Valeur | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
    |---|---:|---:|---:|---:|---:|---:|---:|---:|
    | Utilisé | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |

    Calcul :

    ```text
    128 + 64 = 192
    ```

    Donc :

    ```text
    192 = 11000000
    ```

    Exemple avec 10 :

    | Valeur | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
    |---|---:|---:|---:|---:|---:|---:|---:|---:|
    | Utilisé | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |

    Calcul :

    ```text
    8 + 2 = 10
    ```

    Donc :

    ```text
    10 = 00001010
    ```

    Exemple avec 20 :

    | Valeur | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |
    |---|---:|---:|---:|---:|---:|---:|---:|---:|
    | Utilisé | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 |

    Calcul :

    ```text
    16 + 4 = 20
    ```

    Donc :

    ```text
    20 = 00010100
    ```

    Cette méthode permet de comprendre comment une adresse IP est lue par une machine.

??? note "5. Calculer le réseau d’une adresse IP"
    Pour savoir si deux machines appartiennent au même réseau, on utilise l’adresse IP et le masque.

    Exemple :

    ```text
    Adresse IP : 192.168.10.20
    Masque     : 255.255.255.0
    ```

    Conversion en binaire :

    | Élément | Octet 1 | Octet 2 | Octet 3 | Octet 4 |
    |---|---|---|---|---|
    | Adresse IP | 11000000 | 10101000 | 00001010 | 00010100 |
    | Masque | 11111111 | 11111111 | 11111111 | 00000000 |

    Avec le masque `255.255.255.0`, les trois premiers octets sont conservés.

    Le dernier octet est mis à 0 pour obtenir l’adresse du réseau.

    Résultat :

    ```text
    Réseau : 192.168.10.0
    ```

    Autre exemple :

    | Machine | Adresse IP | Masque | Réseau obtenu |
    |---|---|---|---|
    | Zorin OS | 192.168.10.10 | 255.255.255.0 | 192.168.10.0 |
    | Windows 11 Pro | 192.168.10.20 | 255.255.255.0 | 192.168.10.0 |

    Les deux machines ont le même réseau : `192.168.10.0`.

    Elles sont donc dans le même réseau logique.

    Exemple différent :

    | Machine | Adresse IP | Masque | Réseau obtenu |
    |---|---|---|---|
    | Zorin OS | 192.168.10.10 | 255.255.255.0 | 192.168.10.0 |
    | Windows 11 Pro | 192.168.20.20 | 255.255.255.0 | 192.168.20.0 |

    Les deux machines n’ont pas le même réseau.

    Elles ne sont donc pas dans le même réseau logique.

??? note "6. DHCP et adresse IP fixe"
    Une machine peut recevoir son adresse IP de deux manières.

    | Méthode | Explication |
    |---|---|
    | DHCP | L’adresse IP est donnée automatiquement |
    | IP fixe | L’adresse IP est réglée manuellement |

    En mode NAT et en mode accès par pont, l’adresse IP est souvent donnée automatiquement par DHCP.

    En mode réseau interne, il n’y a généralement pas de serveur DHCP.

    Il faut donc configurer manuellement les adresses IP.

    Pour le réseau interne de ce palier, les adresses utilisées sont :

    | Machine | Adresse IP | Masque |
    |---|---|---|
    | VM Zorin OS | 192.168.10.10 | 255.255.255.0 |
    | VM Windows 11 Pro | 192.168.10.20 | 255.255.255.0 |

    Pour ce réseau interne :

    * les deux machines ont des adresses différentes ;
    * les deux machines sont dans le même réseau logique ;
    * la passerelle peut rester vide ;
    * le DNS peut rester vide.

    La passerelle n’est pas nécessaire pour faire communiquer deux machines dans le même réseau interne.

??? note "7. Commandes utiles sous Debian 13, Zorin OS et Windows 11 Pro"
    Pour tester le réseau, il faut utiliser quelques commandes simples.

    Ces commandes permettent d’identifier la machine, de relever son adresse IP, de vérifier sa route réseau et de tester la communication avec une autre machine.

    ### 7.1 Commandes utiles sous Debian 13 et Zorin OS

    | Commande | Rôle |
    |---|---|
    | `hostname` | Afficher le nom de la machine |
    | `hostname -I` | Afficher rapidement les adresses IP de la machine |
    | `ip a` | Afficher les interfaces réseau et les adresses IP |
    | `ip route` | Afficher la route par défaut et la passerelle |
    | `ping adresse_ip` | Tester si une machine répond sur le réseau |
    | `ping -c 4 adresse_ip` | Envoyer seulement 4 tests ping |

    Exemple pour afficher le nom de la machine :

    ```bash
    hostname
    ```

    Exemple pour afficher rapidement l’adresse IP :

    ```bash
    hostname -I
    ```

    Exemple pour afficher toutes les interfaces réseau :

    ```bash
    ip a
    ```

    Exemple pour afficher la passerelle :

    ```bash
    ip route
    ```

    Exemple pour tester une communication :

    ```bash
    ping 192.168.10.20
    ```

    Exemple pour envoyer seulement 4 tests :

    ```bash
    ping -c 4 192.168.10.20
    ```

    Pour arrêter un ping qui continue :

    ```text
    Ctrl + C
    ```

    ### 7.2 Commandes utiles sous Windows 11 Pro

    | Commande | Rôle |
    |---|---|
    | `hostname` | Afficher le nom de la machine |
    | `ipconfig` | Afficher l’adresse IP de Windows |
    | `ping adresse_ip` | Tester si une machine répond sur le réseau |
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
    ping 192.168.10.10
    ```

    Exemple pour envoyer seulement 4 tests :

    ```text
    ping -n 4 192.168.10.10
    ```

    Pour arrêter un ping qui continue :

    ```text
    Ctrl + C
    ```

    ### 7.3 Méthode de relevé à appliquer

    Pour chaque machine, il faut relever :

    | Élément à relever | Debian 13 | Zorin OS | Windows 11 Pro |
    |---|---|---|---|
    | Nom de la machine | `hostname` | `hostname` | `hostname` |
    | Adresse IP | `hostname -I` ou `ip a` | `hostname -I` ou `ip a` | `ipconfig` |
    | Route réseau | `ip route` | `ip route` | non demandé dans cette activité |
    | Test de communication | `ping adresse_ip` | `ping adresse_ip` | `ping adresse_ip` |

    L’adresse IP relevée doit ensuite être comparée avec le mode réseau VirtualBox utilisé.

??? note "8. Le mode NAT"
    Le mode NAT permet à la machine virtuelle d’accéder au réseau en passant par la machine hôte.

    C’est souvent le mode le plus simple pour donner Internet à une VM.

    En mode NAT :

    * la VM peut généralement accéder à Internet si l’hôte a Internet ;
    * la VM n’est pas directement visible sur le réseau réel ;
    * les autres machines ne communiquent pas directement avec elle ;
    * deux VM en NAT ne communiquent pas forcément directement entre elles.

    Usage principal :

    * installer des mises à jour ;
    * télécharger des paquets ;
    * accéder à Internet simplement depuis une VM.

??? note "9. Le mode accès par pont"
    Le mode accès par pont connecte la machine virtuelle au réseau réel.

    Dans ce mode, la VM se comporte presque comme une machine physique du réseau.

    En mode accès par pont :

    * la VM peut recevoir une adresse IP du réseau réel ;
    * la VM peut accéder à Internet si le réseau l’autorise ;
    * la VM peut communiquer avec les machines du réseau local si les règles du réseau le permettent ;
    * la VM devient visible sur le réseau réel.

    !!! warning "Mode accès par pont"
        Le mode accès par pont connecte la machine virtuelle au réseau réel de la salle.

        Il ne doit être utilisé que si le professeur l’autorise.

    Le mode pont est utile pour comprendre qu’une VM peut se comporter comme une machine réelle.

    Il faut cependant l’utiliser avec prudence dans un établissement.

??? note "10. Le mode réseau interne"
    Le mode réseau interne permet de faire communiquer plusieurs machines virtuelles entre elles.

    Les machines virtuelles restent isolées du réseau réel.

    En mode réseau interne :

    * les VM peuvent communiquer entre elles ;
    * les VM ne communiquent pas avec l’hôte ;
    * les VM ne vont pas sur Internet ;
    * le réseau réel de la salle n’est pas modifié.

    Point important :

    Les deux VM doivent être placées sur le même réseau interne VirtualBox.

    Exemple de nom de réseau interne :

    ```text
    reseau-2tne
    ```

    Si une VM est sur `reseau-2tne` et l’autre sur un autre nom de réseau interne, elles ne communiqueront pas.

    Pour ce palier, le réseau interne est le mode le plus important à comprendre.

??? note "11. Le mode réseau privé hôte"
    Le mode réseau privé hôte est aussi appelé host-only.

    Il permet la communication entre :

    * la machine hôte ;
    * une ou plusieurs machines virtuelles.

    En mode réseau privé hôte :

    * la VM peut communiquer avec l’hôte ;
    * plusieurs VM peuvent communiquer entre elles si elles sont sur le même réseau privé hôte ;
    * la VM ne va pas sur Internet, sauf configuration spéciale ;
    * la VM n’est pas visible sur le réseau réel.

    Ce mode peut ne pas être disponible sur tous les postes.

    Il dépend de la configuration de VirtualBox.

    Si le mode réseau privé hôte n’est pas disponible, il ne faut pas essayer de le créer sans consigne du professeur.

??? note "12. Comparaison des modes réseau"
    Tableau de comparaison :

    | Mode réseau | Accès Internet | Communication avec l’hôte | Communication entre VM | Visible sur le réseau réel |
    |---|---|---|---|---|
    | NAT | Oui, si l’hôte a Internet | Possible mais limitée | Non directement | Non |
    | Accès par pont | Oui, si le réseau l’autorise | Oui, si même réseau | Oui, si même réseau | Oui |
    | Réseau interne | Non | Non | Oui, si même nom de réseau interne | Non |
    | Réseau privé hôte | Non, sauf configuration spéciale | Oui | Oui, si même réseau privé hôte | Non |

    Aucun mode réseau n’est meilleur dans tous les cas.

    Le bon mode dépend du test à réaliser.

    Exemples :

    | Besoin | Mode adapté |
    |---|---|
    | Donner Internet à une VM facilement | NAT |
    | Faire apparaître la VM comme une machine du réseau réel | Accès par pont |
    | Faire communiquer deux VM sans toucher au réseau réel | Réseau interne |
    | Faire communiquer l’hôte et une VM sans réseau réel | Réseau privé hôte |

??? note "13. Méthode de diagnostic réseau"
    Quand une communication ne fonctionne pas, il faut suivre une méthode.

    Ne modifiez pas les paramètres au hasard.

    Ordre de vérification :

    1. vérifier le mode réseau choisi dans VirtualBox ;
    2. vérifier que la carte réseau virtuelle est activée ;
    3. vérifier que les deux VM sont sur le même réseau VirtualBox si nécessaire ;
    4. relever les adresses IP ;
    5. vérifier que les machines ont des adresses différentes ;
    6. vérifier que les machines sont dans le même réseau logique ;
    7. tester avec `ping` ;
    8. analyser le résultat ;
    9. tenir compte du pare-feu Windows.

    Exemple de diagnostic :

    | Problème | Vérification |
    |---|---|
    | Le ping ne répond pas | Vérifier l’adresse IP de la machine cible |
    | Les deux VM ne communiquent pas | Vérifier le mode réseau VirtualBox |
    | Une VM n’a pas d’adresse IP | Vérifier DHCP ou configurer une IP fixe |
    | Windows ne répond pas au ping | Vérifier le pare-feu Windows avec le professeur |
    | La VM n’a pas Internet | Vérifier le mode NAT ou le mode pont |

??? note "14. Pare-feu Windows et ping"
    Sous Windows 11 Pro, le pare-feu peut bloquer les réponses au ping.

    Cela signifie qu’un ping vers Windows peut échouer même si la configuration réseau est correcte.

    Si Windows 11 Pro ne répond pas au ping, il faut vérifier dans cet ordre :

    1. le mode réseau dans VirtualBox ;
    2. l’adresse IP de Windows ;
    3. le masque réseau ;
    4. l’adresse IP de l’autre machine ;
    5. le pare-feu Windows avec le professeur.

    Il ne faut pas désactiver le pare-feu Windows sans consigne.

    Le pare-feu protège la machine.

??? note "15. Erreurs fréquentes"
    ### 15.1 Deux machines ont la même adresse IP

    Deux machines du même réseau ne doivent pas avoir la même adresse IP.

    Si deux machines ont la même adresse, il y a un conflit.

    ### 15.2 Les machines ne sont pas dans le même réseau logique

    Exemple incorrect avec le masque `255.255.255.0` :

    | Machine | Adresse IP |
    |---|---|
    | Zorin OS | 192.168.10.10 |
    | Windows 11 Pro | 192.168.20.20 |

    Les deux machines ne sont pas dans le même réseau.

    ### 15.3 Les VM ne sont pas sur le même réseau interne

    En mode réseau interne, les deux VM doivent utiliser le même nom de réseau interne.

    Exemple :

    ```text
    reseau-2tne
    ```

    ### 15.4 La carte réseau virtuelle est désactivée

    Si la carte réseau virtuelle est désactivée, la VM ne communique pas.

    ### 15.5 Le pare-feu Windows bloque le ping

    Windows peut bloquer les réponses au ping.

    Il faut demander au professeur avant de modifier le pare-feu.

    ### 15.6 Le mode pont est utilisé sans autorisation

    Le mode pont connecte la VM au réseau réel.

    Il doit être utilisé uniquement avec l’autorisation du professeur.

??? note "16. Ce qu’il faut retenir"
    Une machine virtuelle utilise une carte réseau virtuelle.

    Le mode réseau VirtualBox détermine avec qui la VM peut communiquer.

    Une adresse IP identifie une machine sur un réseau.

    Le masque permet de savoir à quel réseau appartient une adresse IP.

    Avec le masque `255.255.255.0`, les trois premiers octets indiquent le réseau.

    Le tableau des puissances de 2 permet de convertir un octet en binaire.

    Pour que deux machines communiquent directement :

    * elles doivent être dans le même réseau logique ;
    * elles doivent avoir des adresses IP différentes ;
    * le mode réseau VirtualBox doit permettre la communication ;
    * le pare-feu ne doit pas bloquer le test.

    La commande `ping` permet de tester si une machine répond.

    Un ping qui échoue ne signifie pas toujours que le réseau est mal configuré.

    Il faut diagnostiquer dans l’ordre.

??? info "Activité à réaliser"
    Vous avez maintenant les informations nécessaires pour passer à la partie pratique.

    Important : vous commencez par le QCM. Vous ne démarrez l’activité que lorsque votre QCM est validé à 100 %.

    Marche à suivre :

    1. [Ouvrir le QCM du palier 3](qcm-palier-3-reseau-virtualbox.md), puis répondez à toutes les questions.
    2. Faites valider votre QCM. Tant qu’il n’est pas correct à 100 %, vous ne passez pas à l’activité.
    3. Une fois le QCM validé à 100 %, [ouvrir l’activité : tester les modes réseau VirtualBox](activite-palier-3-reseau-virtualbox.md) et réalisez les étapes demandées.

    Pendant l’activité, vous devrez revenir dans ce dossier technique chaque fois que vous aurez besoin d’une information.
