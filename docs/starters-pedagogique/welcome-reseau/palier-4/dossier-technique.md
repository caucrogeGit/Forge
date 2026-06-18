# Palier 4 : configurer un réseau interne et diagnostiquer une communication

## Dossier technique

## Objectif du dossier technique

Ce dossier donne les connaissances nécessaires pour configurer un réseau interne entre deux machines virtuelles, relever les informations réseau, tester la communication et diagnostiquer un problème simple.

Dans ce palier, vous allez travailler avec :

* la machine virtuelle Windows 11 Pro ;
* la machine virtuelle Zorin OS ;
* VirtualBox installé sur la machine hôte Debian 13.

À la fin de cette lecture, vous devez être capable de comprendre :

* le rôle du mode réseau interne dans VirtualBox ;
* la différence entre une adresse IP automatique et une adresse IP fixe ;
* pourquoi une adresse IP fixe est nécessaire dans un réseau interne simple ;
* comment configurer les deux VM sur le même réseau interne ;
* comment attribuer une adresse IP fixe à Zorin OS ;
* comment attribuer une adresse IP fixe à Windows 11 Pro ;
* comment vérifier que deux machines sont dans le même réseau logique ;
* comment tester une communication avec `ping` ;
* pourquoi le pare-feu Windows peut bloquer certains tests ;
* comment diagnostiquer une communication qui ne fonctionne pas ;
* comment utiliser le binaire pour mieux comprendre le masque réseau.

Dans ce palier, vous ne travaillez plus sur le mode NAT ni sur le mode accès par pont.

Ces modes ont été étudiés dans le palier 3.

??? note "1. Les machines utilisées dans ce palier"
    <p align="center">
      <img src="../images/01-machines-utilisees.png" alt="Les machines utilisées dans ce palier" width="60%">
    </p>

    Dans ce palier, deux machines virtuelles sont utilisées.

    | Machine | Type | Rôle |
    |---|---|---|
    | Windows 11 Pro | Machine virtuelle | Machine invitée |
    | Zorin OS | Machine virtuelle | Machine invitée |

    La machine hôte Debian 13 sert à lancer VirtualBox et à modifier les paramètres des VM.

    Elle n’est pas la machine principale à tester dans ce palier.

    Le but est de faire communiquer directement les deux machines virtuelles entre elles.

    À retenir :

    * Windows 11 Pro et Zorin OS doivent être dans le même mode réseau VirtualBox ;
    * elles doivent utiliser le même nom de réseau interne ;
    * elles doivent avoir des adresses IP différentes ;
    * elles doivent appartenir au même réseau logique.

??? note "2. Ce que l’on va tester dans ce palier"
    Dans ce palier, vous allez vérifier si deux machines virtuelles peuvent communiquer dans un réseau isolé.

    Vous allez tester le mode :

    ```text
    Réseau interne
    ```

    Le but est d’observer une situation simple :

    * les deux VM peuvent communiquer entre elles ;
    * les deux VM ne communiquent pas avec le réseau réel ;
    * les deux VM ne vont normalement pas sur Internet ;
    * la machine hôte Debian 13 ne fait pas partie de ce réseau interne.

    Vous allez vérifier :

    * le nom du réseau interne VirtualBox ;
    * l’adresse IP de chaque VM ;
    * le masque réseau ;
    * la communication de Zorin OS vers Windows 11 Pro ;
    * la communication de Windows 11 Pro vers Zorin OS ;
    * les causes possibles si la communication ne fonctionne pas.

??? note "3. Rappel : rôle du mode réseau interne"
    <p align="center">
      <img src="../images/03-role-reseau-interne.png" alt="Le rôle du mode réseau interne" width="60%">
    </p>

    Le mode réseau interne permet de créer un réseau isolé entre plusieurs machines virtuelles.

    Ce réseau est créé par VirtualBox.

    En mode réseau interne :

    * les machines virtuelles peuvent communiquer entre elles ;
    * les machines virtuelles ne sont pas visibles sur le réseau réel ;
    * les machines virtuelles ne communiquent pas avec la machine hôte ;
    * les machines virtuelles n’ont pas accès à Internet ;
    * le réseau réel de la salle n’est pas modifié.

    Le mode réseau interne est utile pour apprendre le réseau sans risquer de perturber le réseau de l’établissement.

    Point important :

    Les deux machines virtuelles doivent utiliser exactement le même nom de réseau interne.

    Pour ce palier, le nom utilisé est :

    ```text
    reseau-2tne
    ```

    Si une VM utilise `reseau-2tne` et l’autre utilise un autre nom, elles ne pourront pas communiquer.

??? note "4. Pourquoi utiliser une adresse IP fixe"
    Dans le palier 3, les VM recevaient généralement une adresse IP automatiquement.

    Cette adresse pouvait venir :

    * de VirtualBox en mode NAT ;
    * du réseau réel en mode accès par pont.

    Dans un réseau interne simple, il n’y a généralement pas de serveur DHCP.

    Cela signifie que personne ne donne automatiquement d’adresse IP aux machines.

    Il faut donc configurer les adresses IP à la main.

    On parle alors d’adresse IP fixe.

    Pour ce palier, les adresses utilisées sont :

    | Machine virtuelle | Adresse IP | Masque |
    |---|---|---|
    | Zorin OS | `192.168.10.10` | `255.255.255.0` |
    | Windows 11 Pro | `192.168.10.20` | `255.255.255.0` |

    Les deux adresses sont différentes.

    Elles appartiennent au même réseau logique :

    ```text
    192.168.10.0
    ```

    La passerelle et le DNS peuvent rester vides.

    Ils ne sont pas nécessaires pour faire communiquer deux machines dans le même réseau interne.

??? note "5. Adresse IP, masque et même réseau logique"
    <p align="center">
      <img src="../images/05-adresse-ip-meme-reseau-logique.png" alt="Adresse IP, masque et même réseau logique" width="60%">
    </p>

    Une adresse IP permet d’identifier une machine sur un réseau.

    Exemple :

    ```text
    192.168.10.20
    ```

    Le masque réseau permet de savoir quelle partie de l’adresse correspond au réseau.

    Exemple de masque utilisé dans ce palier :

    ```text
    255.255.255.0
    ```

    Avec ce masque, les trois premiers octets indiquent le réseau.

    Exemple :

    | Machine | Adresse IP | Masque | Réseau obtenu |
    |---|---|---|---|
    | Zorin OS | `192.168.10.10` | `255.255.255.0` | `192.168.10.0` |
    | Windows 11 Pro | `192.168.10.20` | `255.255.255.0` | `192.168.10.0` |

    Les deux machines ont le même réseau logique.

    Elles peuvent donc communiquer si le mode réseau VirtualBox le permet et si le pare-feu ne bloque pas le test.

    Exemple incorrect :

    | Machine | Adresse IP | Masque | Réseau obtenu |
    |---|---|---|---|
    | Zorin OS | `192.168.10.10` | `255.255.255.0` | `192.168.10.0` |
    | Windows 11 Pro | `192.168.20.20` | `255.255.255.0` | `192.168.20.0` |

    Les deux machines n’ont pas le même réseau logique.

    Elles ne peuvent pas communiquer directement dans ce réseau simple.

??? note "6. Configurer le mode réseau interne dans VirtualBox"
    La configuration du mode réseau se fait depuis la machine hôte Debian 13, dans VirtualBox.

    Avant de changer le mode réseau, la machine virtuelle doit être arrêtée proprement.

    Il ne faut pas modifier le mode réseau pendant que la machine virtuelle est en cours d’exécution.

    Pour configurer Windows 11 Pro :

    1. sélectionner la machine virtuelle Windows 11 Pro ;
    2. cliquer sur **Configuration** ;
    3. ouvrir **Réseau** ;
    4. choisir **Adaptateur 1** ;
    5. vérifier que **Activer la carte réseau** est coché ;
    6. choisir **Réseau interne** dans **Mode d’accès réseau** ;
    7. saisir le nom du réseau interne :

    ```text
    reseau-2tne
    ```

    8. valider avec **OK**.

    Pour configurer Zorin OS :

    1. sélectionner la machine virtuelle Zorin OS ;
    2. ouvrir **Configuration** ;
    3. ouvrir **Réseau** ;
    4. choisir **Adaptateur 1** ;
    5. vérifier que **Activer la carte réseau** est coché ;
    6. choisir **Réseau interne** ;
    7. saisir exactement le même nom :

    ```text
    reseau-2tne
    ```

    8. valider avec **OK**.

    À vérifier :

    | Point à vérifier | Résultat attendu |
    |---|---|
    | Les deux VM sont en réseau interne | Oui |
    | Le nom du réseau interne est identique | `reseau-2tne` |
    | Les cartes réseau sont activées | Oui |
    | Les VM sont redémarrées après modification | Oui |

??? note "7. Configurer une adresse IP fixe sous Zorin OS"
    Sous Zorin OS, l’adresse IP fixe peut être configurée depuis les paramètres réseau ou en ligne de commande selon la configuration du poste.

    Pour ce palier, l’objectif est de renseigner les valeurs suivantes :

    | Élément | Valeur |
    |---|---|
    | Adresse IP | `192.168.10.10` |
    | Masque | `255.255.255.0` |
    | Passerelle | vide |
    | DNS | vide |

    Méthode par l’interface graphique :

    1. ouvrir les paramètres de Zorin OS ;
    2. ouvrir la partie **Réseau** ;
    3. sélectionner la connexion filaire ;
    4. ouvrir les paramètres de la connexion ;
    5. passer l’adresse IPv4 en mode manuel ;
    6. saisir l’adresse IP `192.168.10.10` ;
    7. saisir le masque `255.255.255.0` ou le préfixe `/24` selon l’interface ;
    8. laisser la passerelle vide ;
    9. laisser le DNS vide ;
    10. enregistrer ;
    11. désactiver puis réactiver la connexion, ou redémarrer la VM.

    Vérification dans le terminal :

    ```bash
    hostname
    hostname -I
    ip a
    ip route
    ```

    Résultat attendu :

    L’adresse `192.168.10.10` doit apparaître sur l’interface réseau de Zorin OS.

??? note "8. Configurer une adresse IP fixe sous Windows 11 Pro"
    Sous Windows 11 Pro, l’adresse IP fixe se configure dans les paramètres de la carte réseau.

    Pour ce palier, l’objectif est de renseigner les valeurs suivantes :

    | Élément | Valeur |
    |---|---|
    | Adresse IP | `192.168.10.20` |
    | Masque | `255.255.255.0` |
    | Passerelle | vide |
    | DNS | vide |

    Méthode par l’interface graphique :

    1. ouvrir les paramètres réseau de Windows ;
    2. ouvrir les paramètres avancés de la carte réseau ;
    3. sélectionner la carte Ethernet de la VM ;
    4. ouvrir les propriétés IPv4 ;
    5. choisir une configuration manuelle ;
    6. saisir l’adresse IP `192.168.10.20` ;
    7. saisir le masque `255.255.255.0` ;
    8. laisser la passerelle vide ;
    9. laisser le DNS vide ;
    10. valider ;
    11. redémarrer la VM si nécessaire.

    Vérification dans le terminal Windows ou l’invite de commandes :

    ```text
    hostname
    ipconfig
    ```

    Résultat attendu :

    L’adresse `192.168.10.20` doit apparaître dans les informations IPv4 de Windows 11 Pro.

??? note "9. Résultats attendus dans ce palier"
    Les résultats attendus sont les suivants.

    Configuration VirtualBox :

    | Point à vérifier | Résultat attendu |
    |---|---|
    | Windows 11 Pro | Mode réseau interne |
    | Zorin OS | Mode réseau interne |
    | Nom du réseau interne | `reseau-2tne` |
    | Accès Internet | Non attendu |
    | Accès au réseau réel | Non attendu |

    Configuration IP :

    | Machine | Adresse IP | Masque |
    |---|---|---|
    | Zorin OS | `192.168.10.10` | `255.255.255.0` |
    | Windows 11 Pro | `192.168.10.20` | `255.255.255.0` |

    Tests de communication :

    | Test | Commande | Résultat attendu |
    |---|---|---|
    | Zorin OS vers Windows | `ping -c 4 192.168.10.20` | Réponse attendue si Windows accepte le ping |
    | Windows vers Zorin OS | `ping -n 4 192.168.10.10` | Réponse attendue |

    Attention : Windows peut bloquer les réponses au ping avec son pare-feu.

    Il faut donc analyser les résultats avec méthode.

??? note "10. Pare-feu Windows et ping"
    <p align="center">
      <img src="../images/10-pare-feu-windows-et-ping.png" alt="Le pare-feu Windows et le ping" width="60%">
    </p>

    Sous Windows 11 Pro, le pare-feu peut bloquer les réponses au ping.

    Cela signifie qu’un ping vers Windows peut échouer même si :

    * l’adresse IP de Windows est correcte ;
    * le masque est correct ;
    * le mode réseau interne est correct ;
    * le nom du réseau interne est correct.

    Si Zorin OS ne reçoit pas de réponse de Windows, il faut vérifier dans cet ordre :

    1. le mode réseau VirtualBox de Windows ;
    2. le mode réseau VirtualBox de Zorin OS ;
    3. le nom du réseau interne sur les deux VM ;
    4. l’adresse IP de Windows ;
    5. l’adresse IP de Zorin OS ;
    6. le masque réseau ;
    7. le pare-feu Windows avec le professeur.

    Il ne faut pas désactiver le pare-feu Windows sans consigne.

    Le pare-feu protège la machine.

    Si une modification du pare-feu est nécessaire, elle doit être faite avec le professeur.

??? note "11. Méthode de diagnostic réseau"
    Quand une communication ne fonctionne pas, il faut suivre une méthode.

    Ne modifiez pas les paramètres au hasard.

    Ordre de diagnostic :

    1. vérifier que les deux VM sont démarrées ;
    2. vérifier que les cartes réseau virtuelles sont activées ;
    3. vérifier que les deux VM sont en mode réseau interne ;
    4. vérifier que les deux VM utilisent exactement le même nom de réseau interne ;
    5. relever l’adresse IP de Zorin OS ;
    6. relever l’adresse IP de Windows 11 Pro ;
    7. vérifier que les adresses IP sont différentes ;
    8. vérifier que les deux adresses sont dans le même réseau logique ;
    9. tester le ping de Windows vers Zorin OS ;
    10. tester le ping de Zorin OS vers Windows ;
    11. tenir compte du pare-feu Windows si le ping vers Windows échoue ;
    12. demander de l’aide si le problème reste présent.

    Exemple de diagnostic :

    | Problème observé | Vérification à faire |
    |---|---|
    | Les VM n’ont pas d’adresse IP correcte | Vérifier la configuration IP fixe |
    | Les VM ne communiquent pas | Vérifier le nom du réseau interne |
    | Zorin OS répond mais Windows ne répond pas | Vérifier le pare-feu Windows avec le professeur |
    | Une VM a la même IP que l’autre | Corriger une des deux adresses IP |
    | Une VM est en NAT | Remettre le mode réseau interne |

??? note "12. Demander de l’aide correctement"
    Si vous avez besoin d’aide, la demande doit être précise.

    Une demande d’aide ne doit pas être :

    > Ça ne marche pas.

    Une demande d’aide doit indiquer :

    * l’étape concernée ;
    * la machine concernée ;
    * le mode réseau choisi ;
    * l’adresse IP relevée ;
    * la commande lancée ;
    * le résultat obtenu ;
    * le chapitre du dossier technique consulté.

    Exemple de demande correcte :

    > Je travaille sur le test de Zorin OS vers Windows 11 Pro.  
    > Les deux VM sont en réseau interne avec le nom `reseau-2tne`.  
    > Zorin OS a l’adresse `192.168.10.10`.  
    > Windows a l’adresse `192.168.10.20`.  
    > J’ai lancé `ping -c 4 192.168.10.20` depuis Zorin OS.  
    > Je n’ai pas de réponse.  
    > J’ai consulté le chapitre sur le pare-feu Windows.  
    > J’ai besoin d’aide pour vérifier si Windows bloque le ping.

    Un technicien explique ce qu’il a fait, ce qu’il a observé et ce qu’il veut vérifier.

??? note "13. Erreurs fréquentes"
    ### 14.1 Les deux VM ne sont pas sur le même réseau interne

    Les deux VM doivent utiliser exactement :

    ```text
    reseau-2tne
    ```

    Une différence de lettre, d’espace ou de tiret peut empêcher la communication.

    ### 14.2 Une VM est restée en NAT

    Le palier 4 utilise le mode réseau interne.

    Si une VM est encore en NAT, elle ne sera pas dans le réseau interne attendu.

    ### 14.3 Les deux VM ont la même adresse IP

    Deux machines du même réseau ne doivent pas avoir la même adresse IP.

    Pour ce palier :

    * Zorin OS : `192.168.10.10` ;
    * Windows 11 Pro : `192.168.10.20`.

    ### 14.4 Les VM ne sont pas dans le même réseau logique

    Exemple incorrect :

    | Machine | Adresse IP |
    |---|---|
    | Zorin OS | `192.168.10.10` |
    | Windows 11 Pro | `192.168.20.20` |

    Avec le masque `255.255.255.0`, ces deux machines ne sont pas dans le même réseau logique.

    ### 14.5 Le pare-feu Windows bloque le ping

    Windows peut bloquer les réponses au ping.

    Il faut demander au professeur avant de modifier le pare-feu.

    ### 14.6 L’élève teste la mauvaise adresse IP

    Il faut toujours tester l’adresse IP de la machine cible.

    Exemple :

    * depuis Zorin OS, on teste l’adresse de Windows ;
    * depuis Windows, on teste l’adresse de Zorin OS.

??? note "14. Pour comprendre : convertir un octet en binaire"
    <p align="center">
      <img src="../images/14-convertir-octet-binaire.png" alt="Convertir un octet en binaire" width="60%">
    </p>

    Cette partie sert à mieux comprendre comment une adresse IP et un masque sont lus par une machine.

    Elle aide à comprendre la notion de réseau logique.

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

??? note "15. Pour comprendre : calculer le réseau d’une adresse IP"
    <p align="center">
      <img src="../images/15-calculer-reseau-adresse-ip.png" alt="Calculer le réseau d’une adresse IP" width="60%">
    </p>

    Pour savoir précisément si deux machines appartiennent au même réseau, on utilise l’adresse IP et le masque.

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

    Application au palier :

    | Machine | Adresse IP | Masque | Réseau obtenu |
    |---|---|---|---|
    | Zorin OS | `192.168.10.10` | `255.255.255.0` | `192.168.10.0` |
    | Windows 11 Pro | `192.168.10.20` | `255.255.255.0` | `192.168.10.0` |

    Les deux machines ont le même réseau :

    ```text
    192.168.10.0
    ```

    Elles sont donc dans le même réseau logique.

??? note "16. Ce qu’il faut retenir"
    Le mode réseau interne permet de faire communiquer deux VM entre elles sans utiliser le réseau réel.

    Les deux VM doivent utiliser exactement le même nom de réseau interne :

    ```text
    reseau-2tne
    ```

    Dans ce palier, les adresses IP sont fixes.

    Les valeurs attendues sont :

    | Machine | Adresse IP | Masque |
    |---|---|---|
    | Zorin OS | `192.168.10.10` | `255.255.255.0` |
    | Windows 11 Pro | `192.168.10.20` | `255.255.255.0` |

    Pour que les deux VM communiquent :

    * elles doivent être en réseau interne ;
    * elles doivent utiliser le même nom de réseau interne ;
    * elles doivent avoir des adresses IP différentes ;
    * elles doivent être dans le même réseau logique ;
    * le pare-feu ne doit pas bloquer le test.

    Les commandes principales sont :

    | Système | Commandes principales |
    |---|---|
    | Zorin OS | `hostname`, `hostname -I`, `ip a`, `ping -c 4` |
    | Windows 11 Pro | `hostname`, `ipconfig`, `ping -n 4` |

    Un test qui échoue doit être diagnostiqué dans l’ordre.

    Il ne faut pas modifier les paramètres au hasard.

??? info "Activité à réaliser"
    Vous avez maintenant les informations nécessaires pour passer à la partie pratique.

    Important : vous commencez par le QCM. Vous ne démarrez l’activité que lorsque votre QCM est validé à 100 %.

    Marche à suivre :

    1. [Ouvrir le QCM du palier 4](eleve/qcm-palier-4.pdf), puis répondez à toutes les questions.
    2. Enregistrez vos réponses dans le fichier demandé.
    3. Faites valider votre QCM. Tant qu’il n’est pas correct à 100 %, vous ne passez pas à l’activité.
    4. Une fois le QCM validé à 100 %, [ouvrir l’activité du palier 4](eleve/activite-palier-4.pdf).
    5. Complétez la checklist de validation avant de demander la validation du professeur.

    Pendant l’activité, vous devrez revenir dans ce dossier technique chaque fois que vous aurez besoin d’une information.
