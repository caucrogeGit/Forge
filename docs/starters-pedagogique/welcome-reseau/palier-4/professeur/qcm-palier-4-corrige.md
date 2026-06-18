# Corrigé du QCM du palier 4

## Palier 4 : réseau interne et diagnostic

## Correction détaillée

| Question | Réponse | Explication courte |
|---:|---|---|
| 1 | A | Le palier 4 teste la communication entre les deux machines virtuelles Windows 11 Pro et Zorin OS. |
| 2 | B | Debian 13 est la machine hôte. Elle sert à lancer VirtualBox et à modifier les paramètres des VM. |
| 3 | C | Le palier 4 porte sur le mode réseau interne. |
| 4 | A | Le réseau interne crée un réseau isolé entre plusieurs machines virtuelles. |
| 5 | B | En réseau interne, les VM peuvent communiquer entre elles si le mode réseau, les IP et le masque sont corrects. |
| 6 | C | Le nom imposé dans ce palier est `reseau-2tne`. |
| 7 | A | Deux noms de réseau interne différents empêchent les VM de communiquer entre elles. |
| 8 | A | Dans un réseau interne simple, il n’y a généralement pas de serveur DHCP. Il faut donc configurer les IP à la main. |
| 9 | B | Zorin OS doit utiliser l’adresse `192.168.10.10`. |
| 10 | A | Windows 11 Pro doit utiliser l’adresse `192.168.10.20`. |
| 11 | C | Le masque utilisé dans ce palier est `255.255.255.0`. |
| 12 | A | Avec ce masque, les deux adresses appartiennent au réseau `192.168.10.0`. |
| 13 | B | `192.168.10.10` et `192.168.20.20` n’appartiennent pas au même réseau logique avec le masque `255.255.255.0`. |
| 14 | A | Sous Linux, l’option `-c 4` permet d’envoyer 4 paquets ping. |
| 15 | C | Sous Windows, l’option `-n 4` permet d’envoyer 4 paquets ping. |
| 16 | A | Le pare-feu Windows peut bloquer les réponses au ping même si la configuration réseau est correcte. |
| 17 | B | Le pare-feu protège la machine. Il ne doit pas être modifié sans consigne du professeur. |
| 18 | A | Le diagnostic commence par les vérifications simples : VM démarrées et cartes réseau activées. |
| 19 | C | Une demande d’aide correcte donne le contexte technique, la commande lancée et le résultat observé. |
| 20 | B | 192 se convertit avec 128 + 64, donc `11000000`. |

## Grille de réponses

```text
1a
2b
3c
4a
5b
6c
7a
8a
9b
10a
11c
12a
13b
14a
15c
16a
17b
18a
19c
20b
```

## Répartition des réponses correctes

| Réponse | Nombre |
|---|---:|
| A | 8 |
| B | 6 |
| C | 6 |

## Validation

Le QCM est validé uniquement avec :

```text
20 bonnes réponses sur 20
```

En cas d’erreur, l’élève doit :

1. relire le chapitre concerné du dossier technique ;
2. corriger son fichier `qcm-palier4.txt` ;
3. demander une nouvelle validation ;
4. attendre la validation à 100 % avant de commencer l’activité.