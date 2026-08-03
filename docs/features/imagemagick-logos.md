# ImageMagick : guide complet pour développeurs

ImageMagick est un outil externe, indépendant du cœur de Forge.
Ce guide explique comment l'installer et l'utiliser en ligne de commande pour préparer des images : détourage, redimensionnement, transparence, composition, favicons et traitement par lots.

!!! warning "Hors runtime Forge"
    ImageMagick n'est **pas** une dépendance de Forge.
    Le traitement d'image applicatif (uploads, miniatures, variantes servies pendant une requête) passe par l'opt-in `forge-mvc-images`, qui s'appuie sur **Pillow** (une bibliothèque Python pure, en-processus).
    ImageMagick est ici un outil de développeur **hors-ligne**, pour fabriquer des assets une fois pour toutes (logos, favicons, planches de contrôle).
    Ne l'exposez jamais directement à des fichiers non fiables : voir le chapitre « Sécurité ».

---

## 1. À qui s'adresse ce guide

Ce guide vise le développeur qui a un besoin ponctuel : recadrer un export graphique, générer plusieurs tailles d'un logo, produire un favicon, assembler une planche, convertir un lot d'images.

Vous n'avez pas besoin de connaître ImageMagick au préalable.
Chaque chapitre part d'un cas concret et donne la commande complète, puis l'explique.

Deux repères pour situer l'outil dans Forge :

- Pour tout ce qui est **applicatif** (traiter un upload utilisateur), utilisez `forge-mvc-images` (Pillow), pas ImageMagick.
- Pour tout ce qui est **préparation d'assets du projet** (les logos de `docs/logos/`, un favicon, une illustration), ImageMagick est l'outil adapté.

---

## 2. Installation

### 2.1. Installer ImageMagick

Sous Debian, Ubuntu ou Linux Mint :

```bash
sudo apt update
sudo apt install imagemagick
```

Sous macOS, avec Homebrew :

```bash
brew install imagemagick
```

### 2.2. Vérifier l'installation et choisir la commande

ImageMagick existe en deux générations, avec deux commandes différentes.

Tester d'abord la commande de la version 7 :

```bash
magick -version
```

Exemple de résultat :

```text
Version: ImageMagick 7.1.1-43 Q16 x86_64
```

Si `magick` n'existe pas, vous avez probablement la version 6, dont la commande principale est `convert` :

```bash
convert -version
```

```text
Version: ImageMagick 6.9.12-98 Q16 x86_64
```

**Convention de ce guide** : toutes les commandes utilisent `magick` (version 7, recommandée).
Si vous êtes en version 6, remplacez `magick` par `convert` dans chaque exemple.

Deux exceptions : la version 6 n'a pas de sous-commandes, mais des outils séparés.
`magick montage` s'y écrit `montage`, et `magick identify` s'y écrit `identify`.

Le `Q16` indique la profondeur de calcul (16 bits par canal), ce qui garantit une bonne qualité sur les dégradés et la transparence.

---

## 3. Concepts clés

Comprendre cinq notions évite 90 pour cent des erreurs.

### 3.1. Le modèle de commande

Une commande ImageMagick se lit ainsi :

```text
magick  [image source]  [opérations, dans l'ordre]  [image de sortie]
```

L'**ordre des opérations compte** : elles s'appliquent de gauche à droite, comme une chaîne de traitement.

### 3.2. Réglages contre opérateurs

- Un **réglage** (`-background`, `-gravity`, `-fill`, `-quality`) prépare le terrain et influence les opérateurs qui le suivent.
- Un **opérateur** (`-resize`, `-trim`, `-crop`, `-rotate`) agit réellement sur les pixels.

Un réglage doit donc être placé **avant** l'opérateur qu'il concerne.

### 3.3. La géométrie

Beaucoup d'options prennent une « geometry ». Les formes utiles :

| Écriture | Effet |
|---|---|
| `512x512` | Rentre l'image dans 512x512 en gardant les proportions. |
| `512x512>` | Comme ci-dessus, mais **ne fait que réduire** (jamais agrandir). |
| `512x512^` | Remplit 512x512 en débordant (à recadrer ensuite). |
| `512x512!` | Force exactement 512x512, **au prix d'une déformation**. |
| `50%` | Met à l'échelle en pourcentage. |
| `512x512+30+20` | Taille 512x512 à la position (30, 20) pour un recadrage. |

Le `>` est le plus sûr pour un jeu de tailles : il évite tout agrandissement destructeur.

### 3.4. La gravité

`-gravity` définit le point d'ancrage (`center`, `north`, `southeast`, etc.) utilisé par `-extent`, `-annotate` ou `-composite`.
`-gravity center` est le réglage le plus courant pour centrer.

### 3.5. Transparence et canevas virtuel

- `-background none` demande un fond transparent pour les zones ajoutées.
- `PNG32:` en préfixe de la sortie force un PNG avec canal alpha propre (8 bits par canal, transparence incluse).
- `+repage` réinitialise le « canevas virtuel » après un `-trim` ou un `-crop`, pour que la nouvelle taille soit nette. Oublier `+repage` est la cause la plus fréquente de comportements surprenants.

---

## 4. Inspecter une image

Avant de traiter, regardez ce que vous avez.

Lister avec les tailles de fichier :

```bash
ls -lh *.png
```

Afficher le format et les dimensions :

```bash
identify -format "%f : %wx%h - %m\n" *.png
```

Exemple de sortie :

```text
forge-1.png : 1024x1024 - PNG
serveur-forge.png : 1024x1024 - PNG
```

Vérifier qu'une image contient bien de la transparence :

```bash
identify -verbose forge-1.png | grep -i alpha
```

Voir tous les détails (profil, canaux, compression) :

```bash
magick identify -verbose forge-1.png | less
```

---

## 5. Opérations de base

### 5.1. Redimensionner

```bash
magick "forge-1.png" -resize "512x512" -background none "PNG32:forge-1-512.png"
```

| Élément | Rôle |
|---|---|
| `-resize "512x512"` | Rentre l'image dans 512x512 en gardant les proportions. |
| `-background none` | Conserve un fond transparent. |
| `PNG32:` | Force une sortie PNG avec transparence propre. |

Pour ne jamais agrandir, utilisez le suffixe `>` :

```bash
magick "forge-1.png" -resize "512x512>" -background none "PNG32:forge-1-512.png"
```

### 5.2. Recadrer une zone

```bash
magick "photo.png" -crop "300x200+50+40" +repage "photo-recadree.png"
```

`300x200+50+40` = une zone de 300x200 pixels à partir du point (50, 40).
Le `+repage` réajuste le canevas après la découpe.

### 5.3. Pivoter et retourner

```bash
magick "photo.png" -rotate 90 "photo-90.png"
magick "photo.png" -flip  "photo-vertical.png"    # miroir haut-bas
magick "photo.png" -flop  "photo-horizontal.png"  # miroir gauche-droite
```

### 5.4. Convertir de format

La conversion se fait simplement par l'extension de sortie :

```bash
magick "logo.png" "logo.webp"
magick "photo.png" -background white -flatten "photo.jpg"
```

Le JPG ne gère pas la transparence : on aplatit d'abord sur un fond (`-flatten`) pour éviter un fond noir.

### 5.5. Compresser et nettoyer

```bash
magick "photo.jpg" -strip -quality 82 "photo-web.jpg"
```

| Élément | Rôle |
|---|---|
| `-strip` | Retire les métadonnées (EXIF, profils), allège le fichier. |
| `-quality 82` | Compression JPEG (82 est un bon compromis web). |

---

## 6. Transparence et fond

### 6.1. Détourer le vide autour d'une image

Un export graphique contient souvent une grande marge transparente autour du sujet.
`-trim` supprime cette bordure uniforme :

```bash
magick "illustration.png" -trim +repage "illustration-recadree.png"
```

| Élément | Rôle |
|---|---|
| `-trim` | Supprime les bords uniformes (transparents ou d'une couleur constante). |
| `+repage` | Réinitialise le canevas pour une taille propre. |

### 6.2. Ajouter une marge uniforme après détourage

Pour détourer au plus près puis remettre une petite marge transparente régulière :

```bash
magick "logo.png" -trim +repage -bordercolor none -border 24 "logo-marge.png"
```

`-border 24` ajoute 24 pixels transparents sur chaque côté.
C'est la méthode utilisée pour normaliser les logos de `docs/logos/`.

### 6.3. Aplatir sur un fond

```bash
magick "logo.png" -background "#E8651A" -flatten "logo-sur-orange.png"
```

`-flatten` fusionne la transparence sur le fond choisi (ici l'orange Forge).

### 6.4. Rendre une couleur transparente (chroma key)

Pour un détourage fin d'un fond uni (vert ou magenta), l'outil interne `tools/chroma_key.py` est plus robuste.
Pour un cas simple, ImageMagick suffit :

```bash
magick "sujet-fond-vert.png" -fuzz 12% -transparent "#00ff00" "PNG32:sujet-detoure.png"
```

`-fuzz 12%` tolère les nuances proches du vert ciblé.

---

## 7. Composition

### 7.1. Assembler plusieurs images

```bash
magick a.png b.png c.png +append "bande-horizontale.png"   # côte à côte
magick a.png b.png c.png -append "colonne-verticale.png"   # empilées
```

### 7.2. Fabriquer une planche de contrôle

Une planche (contact sheet) est pratique pour comparer des variantes d'un coup, surtout sur damier pour visualiser la transparence :

```bash
magick montage logo-*.png \
  -tile 2x5 -geometry 300x300+8+8 \
  -background none -texture pattern:checkerboard \
  "PNG32:planche.png"
```

| Élément | Rôle |
|---|---|
| `-tile 2x5` | Grille de 2 colonnes sur 5 lignes. |
| `-geometry 300x300+8+8` | Chaque vignette dans 300x300, avec 8 pixels de marge. |
| `-texture pattern:checkerboard` | Fond en damier, pour voir les zones transparentes. |

### 7.3. Superposer un filigrane

```bash
magick "fond.png" "filigrane.png" -gravity southeast -geometry +20+20 -composite "resultat.png"
```

Le filigrane est posé en bas à droite, à 20 pixels du bord.

---

## 8. Texte et annotation

Ajouter un texte sur une image :

```bash
magick "fond.png" \
  -gravity south \
  -pointsize 48 -fill white \
  -annotate +0+30 "Forge" \
  "fond-annote.png"
```

Générer une image de texte seule, sur fond transparent :

```bash
magick -background none -fill "#E8651A" -pointsize 72 label:"Forge" "PNG32:titre.png"
```

`caption:` fait la même chose mais avec retour à la ligne automatique dans une largeur donnée :

```bash
magick -background none -fill black -size 400x caption:"Un texte plus long qui se répartit sur plusieurs lignes." "PNG32:paragraphe.png"
```

---

## 9. Effets courants

```bash
magick "photo.png" -blur 0x8            "flou.png"          # flou gaussien
magick "photo.png" -sharpen 0x1.2       "net.png"           # accentuation
magick "photo.png" -colorspace Gray     "gris.png"          # niveaux de gris
magick "photo.png" -negate              "negatif.png"       # inversion
magick "photo.png" -normalize           "contraste.png"     # étalement du contraste
magick "photo.png" -modulate 100,140,100 "sature.png"       # luminosité, saturation, teinte
```

`-modulate` prend trois pourcentages : luminosité, saturation, teinte.
`140` en deuxième position augmente la saturation de 40 pour cent.

---

## 10. Traitement par lots

### 10.1. mogrify, à manier avec prudence

`mogrify` modifie les fichiers **sur place** (il écrase les originaux).
À n'utiliser que sur une copie de travail :

```bash
mkdir -p copie && cp *.png copie/ && cd copie
mogrify -resize "800x800>" *.png
```

### 10.2. Boucle bash (recommandée)

Une boucle explicite garde les originaux intacts et range la sortie à part :

```bash
mkdir -p sortie
for f in *.png; do
  magick "$f" -resize "800x800>" -background none "PNG32:sortie/$f"
done
```

### 10.3. Script réutilisable, dossier source et dossier de sortie

Enregistrez ce script dans `resize-dir.sh` :

```bash
#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${1:-.}"
OUTPUT_DIR="${2:-images-redimensionnees}"
SIZES=(1024 512 256 128 64 32 16)

if [ ! -d "$SOURCE_DIR" ]; then
  echo "Erreur : dossier source introuvable : $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

for size in "${SIZES[@]}"; do
  mkdir -p "$OUTPUT_DIR/${size}x${size}"
  find "$SOURCE_DIR" -maxdepth 1 -type f -iname "*.png" -print0 |
  while IFS= read -r -d '' file; do
    filename="$(basename "$file")"
    base="${filename%.*}"
    output="$OUTPUT_DIR/${size}x${size}/${base}-${size}.png"
    magick "$file" -resize "${size}x${size}>" -background none "PNG32:$output"
    echo "Créé : $output"
  done
done

echo "Terminé."
```

Rendre exécutable, puis lancer :

```bash
chmod +x resize-dir.sh
./resize-dir.sh ~/Téléchargements/logos images-redimensionnees
```

Sur ImageMagick 6, remplacez `magick` par `convert` dans le script.

---

## 11. Créer un favicon .ico multi-tailles

Un favicon `.ico` peut contenir plusieurs tailles dans un seul fichier.
ImageMagick les génère en une commande :

```bash
magick "logo.png" -background none -define icon:auto-resize=64,48,32,16 "favicon.ico"
```

Le fichier `favicon.ico` embarquera les tailles 16, 32, 48 et 64.

Pour un favicon net, partez d'un logo **carré**.
Si le logo ne l'est pas, centrez-le d'abord sur une toile carrée transparente :

```bash
magick "logo.png" -background none -gravity center -extent 256x256 "PNG32:logo-carre.png"
magick "logo-carre.png" -define icon:auto-resize=64,48,32,16 "favicon.ico"
```

!!! note "Favicon d'onglet et navigateurs"
    Pour l'onglet d'un site, servez un `.png` ou un `.ico`.
    Évitez un `.svg` qui embarque une image matricielle : plusieurs navigateurs ne le rendent pas et retombent sur l'icône générique.

---

## 12. Générer un jeu de tailles carrées (cas logos)

C'est le cas historique de Forge : partir d'un logo source en grande taille et produire toutes les déclinaisons.

Deux stratégies selon le résultat voulu.

### 12.1. Tailles carrées strictes (logo centré sur toile carrée)

```bash
mkdir -p logos-carres
for size in 1024 512 256 128 64 32 16; do
  mkdir -p "logos-carres/${size}x${size}"
  for file in *.png; do
    magick "$file" \
      -resize "${size}x${size}" \
      -background none -gravity center -extent "${size}x${size}" \
      "PNG32:logos-carres/${size}x${size}/${file%.png}-${size}.png"
  done
done
```

### 12.2. Détourage au plus près, marge uniforme et aspect préservé

C'est l'approche retenue pour `docs/logos/` : on retire le vide, on remet une petite marge régulière, et on garde le rapport d'aspect (les visuels ne sont plus forcés au carré).

```bash
mkdir -p logos-rognes
for file in *.png; do
  cw="$(magick "$file" -trim +repage -format '%w' info:)"
  ch="$(magick "$file" -trim +repage -format '%h' info:)"
  big=$(( cw > ch ? cw : ch ))
  m=$(( big * 5 / 100 ))   # marge de 5 pour cent
  magick "$file" -trim +repage -bordercolor none -border "$m" "PNG32:logos-rognes/$file"
done
```

### 12.3. Vérifier le résultat

```bash
find logos-carres -type f | sort
identify -format "%f : %wx%h - %m\n" logos-carres/*/*.png
```

---

## 13. Sécurité

ImageMagick est puissant, donc à surveiller dès qu'il touche des données non maîtrisées.

- **Ne traitez jamais des uploads utilisateur directement avec ImageMagick.**
  L'outil a connu des vulnérabilités notables (la famille « ImageTragick ») liées au traitement de fichiers piégés.
  Pour l'applicatif, restez sur `forge-mvc-images` (Pillow), dont la surface d'attaque est bien plus étroite.

- **Durcissez la politique système.**
  Le fichier `policy.xml` (souvent `/etc/ImageMagick-7/policy.xml`) permet de désactiver des formats dangereux et de plafonner les ressources.
  Désactivez les coders inutiles et risqués (`MSL`, `HTTPS`, `URL`, `PS`, `EPS`, `PDF`, `EPHEMERAL`) si vous n'en avez pas besoin.

- **Plafonnez la mémoire et le disque** pour éviter qu'une image malveillante ne provoque un déni de service :

```xml
<policy domain="resource" name="memory" value="256MiB"/>
<policy domain="resource" name="disk" value="1GiB"/>
```

- **Validez avant de traiter.**
  Contrôlez l'extension, le type MIME et la taille avant tout passage dans l'outil.

En résumé : ImageMagick est fait pour vos assets, sur votre machine, à partir de fichiers que vous maîtrisez.

---

## 14. Aide-mémoire des options

| Option | Rôle |
|---|---|
| `-resize WxH` | Redimensionne en gardant les proportions. |
| `-resize WxH>` | Ne réduit que si l'image est plus grande (jamais d'agrandissement). |
| `-resize WxH!` | Force la taille exacte, au prix d'une déformation. |
| `-crop WxH+X+Y` | Découpe une zone. À suivre de `+repage`. |
| `-trim` | Supprime les bords uniformes. À suivre de `+repage`. |
| `+repage` | Réinitialise le canevas virtuel. |
| `-background none` | Fond transparent pour les zones ajoutées. |
| `-flatten` | Aplatit la transparence sur le fond. |
| `-gravity center` | Point d'ancrage central. |
| `-extent WxH` | Force la taille de la toile (avec `-gravity`). |
| `-bordercolor none -border N` | Ajoute N pixels de marge transparente. |
| `-rotate D` / `-flip` / `-flop` | Pivote / miroir vertical / miroir horizontal. |
| `-quality N` / `-strip` | Compression JPEG / suppression des métadonnées. |
| `-define icon:auto-resize=...` | Favicon `.ico` multi-tailles. |
| `PNG32:sortie.png` | Sortie PNG avec alpha propre. |
| `identify -format "%wx%h" f` | Affiche les dimensions. |

---

## 15. ImageMagick ou Pillow : lequel choisir

Les deux savent redimensionner et convertir, mais ne jouent pas le même rôle.

| Critère | Pillow | ImageMagick |
|---|---|---|
| Nature | Bibliothèque Python, en-processus | Outil système, appelé en ligne de commande |
| Installation | `pip install`, épinglable, reproductible | Paquet système, version variable selon la distribution |
| Cas d'usage | Traitement web à la volée (uploads, miniatures) | Préparation d'assets, traitement par lots hors-ligne |
| Formats | Les formats web courants | Très nombreux (SVG, PDF, RAW, HEIC, PSD, etc.) |
| Sécurité sur données non fiables | Surface étroite | Surface large, à durcir |

Règle simple pour un projet Forge :

- **Dans l'application** (pendant une requête, sur un upload) : `forge-mvc-images` et Pillow.
- **En atelier** (fabriquer les logos, un favicon, une planche) : ImageMagick, comme dans ce guide.

Pour la partie applicative, reportez-vous à la documentation de l'opt-in `forge-mvc-images`, disponible dans la section « Opt-ins » du site.
