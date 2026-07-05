# ADR-062 : forge new épingle le projet généré sur la source d'installation de Forge

## Statut

Acceptée, Forge 1.0.0-rc.x (ticket `FORGE-NEW-INSTALL-SOURCE-001`).
Décision actée ; l'implémentation accompagne cet ADR.

---

## Date

2026-07-05

---

## Contexte

Un projet créé par `forge new` déclare sa dépendance au framework dans
`requirements.txt`, sous la forme `forge-mvc==<version>` (la version courante,
publiée sur PyPI). Ce pin convient à l'utilisateur du framework qui installe
Forge depuis PyPI.

Il existe pourtant trois publics distincts, pas deux :

1. **Utilisateur (stable)** : installe `forge-mvc` depuis PyPI, crée une
   application avec la version publiée. C'est le parcours `poste-linux.md`.
2. **Contributeur du cœur** : clone le dépôt et l'installe en mode éditable
   pour modifier Forge lui-même. C'est le parcours `core-dev.md`, doté du
   mécanisme `FORGE_DEV_SRC` (un projet généré exécute le working tree local).
3. **Utilisateur avant-garde** : veut créer une application avec la **dernière
   version poussée sur GitHub** (`main`), en avance sur PyPI, **sans** cloner
   le dépôt pour contribuer.

Le troisième public est réel et cassé aujourd'hui.
Le squelette est embarqué dans le paquet `forge` (CLI), donc
`pipx install "git+https://github.com/caucrogeGit/Forge.git@main"` fournit
déjà le CLI et le squelette les plus récents.
Mais `forge new` épingle ensuite `forge-mvc==<version de main>`, souvent une
version **non publiée sur PyPI** (par exemple un `rc` en préparation) : le
`pip install -r requirements.txt` du projet généré échoue, car cette version
n'existe pas sur l'index.

Le seul contournement existant, `FORGE_DEV_SRC`, impose un clone local et
relève du parcours contributeur, que l'utilisateur avant-garde veut justement
éviter.

---

## Décision

`forge new` détermine la **source dont le paquet `forge-mvc` est lui-même
issu** et épingle le projet généré en cohérence. Trois cas, dans cet ordre de
priorité :

1. **`FORGE_DEV_SRC` pointe vers un dossier local** (contributeur, retour
   terrain) : `forge-mvc` est installé en éditable depuis ce dossier.
   Inchangé, priorité maximale car explicite.
2. **`forge-mvc` a été installé depuis un dépôt Git** (détecté via le
   `direct_url.json` de PEP 610, champ `vcs_info`) : le projet généré dépend
   de `forge-mvc @ git+<url>@<commit>`, en réécrivant la ligne `forge-mvc` de
   son `requirements.txt` à la génération. Le commit exact est épinglé, donc le
   projet est reproductible.
3. **Sinon** (installation PyPI classique) : pin `forge-mvc==<version>`.
   Inchangé, comportement par défaut.

Aucune nouvelle commande ni option n'est ajoutée : le comportement découle de
la façon dont l'utilisateur a installé Forge. Installer le CLI depuis GitHub
suffit pour que les projets générés suivent GitHub.

La réécriture de la ligne `forge-mvc` se fait pendant la **génération** du
projet (fichier neuf, write-if-new), pas sur un fichier applicatif existant :
elle ne contredit pas le principe 9. `forge new` **annonce** explicitement la
source retenue en fin de sortie.

---

## Conséquences

- L'utilisateur avant-garde fait `pipx install "git+…@main"` puis `forge new`,
  et son projet suit `main`, épinglé au commit installé. Aucun clone, aucun
  contournement manuel.
- Le `requirements.txt` généré reflète honnêtement la source réelle du
  framework (git ou PyPI), au lieu d'un pin PyPI trompeur.
- Le mécanisme est symétrique des trois parcours d'installation et documenté
  par une page dédiée (`docs/install/`).
- La détection est purement locale (lecture des métadonnées installées), sans
  accès réseau ni magie cachée (principe 3).

### Alternatives écartées

- **Option `forge new --from-git`** : ajoute une surface CLI et un état à
  retenir, alors que la source d'installation suffit à décider (principe 11,
  une seule façon officielle).
- **Workaround documenté seulement** (éditer à la main la ligne `forge-mvc` du
  `requirements.txt` généré) : fragile, non reproductible, à la charge de
  l'utilisateur.

---

## Charte appliquée

- **Principe 3 (refuser la magie cachée)** : détection explicite et annoncée,
  fondée sur les métadonnées standard PEP 610.
- **Principe 9 (pas d'écriture invisible dans le code utilisateur)** : la ligne
  `forge-mvc` est fixée à la génération d'un projet neuf, pas réécrite dans un
  projet existant.
- **Principe 11 (une seule façon officielle)** : le projet généré dépend de la
  même source que le CLI qui l'a produit, sans mode ni option supplémentaire.

Lié à `FORGE_DEV_SRC` (ADR non dédié, documenté dans `core-dev.md`) et à
ADR-060 (squelette nu, sans backend).
