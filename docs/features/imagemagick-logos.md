# ImageMagick : installation, utilisation et scripts pour logos PNG transparents

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

ImageMagick est un outil externe, indépendant du cœur de Forge.
Il sert ici à produire les déclinaisons de taille des logos de la documentation à partir d'un export Canva en PNG transparent.

Pour détourer un fond uni (vert ou magenta) et obtenir un PNG transparent, voir l'outil interne `tools/chroma_key.py`.
ImageMagick intervient ensuite, une fois la transparence obtenue, pour générer les différentes tailles.

---

## 1. Objectif

Ce document explique comment installer et utiliser **ImageMagick** sous Linux Mint, Ubuntu ou Debian.

Dans le cas traité ici, l'objectif est de partir de logos exportés depuis Canva en **PNG avec fond transparent**, puis de générer automatiquement plusieurs tailles :

```text
1024 x 1024 px
512 x 512 px
256 x 256 px
128 x 128 px
64 x 64 px
32 x 32 px
16 x 16 px
```

Cela évite de refaire tous les exports à la main dans Canva.

---

## 2. Installation

### 2.1. Installer ImageMagick

Sous Linux Mint, Ubuntu ou Debian :

```bash
sudo apt update
sudo apt install imagemagick
```

### 2.2. Vérifier l'installation

Selon la version installée, la commande principale peut être différente.

Tester d'abord :

```bash
magick -version
```

Si la commande n'existe pas, tester :

```bash
convert -version
```

Sur Linux Mint, il est fréquent d'avoir ImageMagick 6 avec la commande :

```bash
convert
```

Exemple de résultat obtenu :

```text
Version: ImageMagick 6.9.12-98 Q16 x86_64
```

Dans ce cas, tous les scripts de ce document utilisent `convert`.

---

## 3. Vérifier les images avant traitement

Se placer dans le dossier qui contient les logos PNG :

```bash
cd ~/Téléchargements
```

Ou, si les fichiers sont dans un sous-dossier :

```bash
cd ~/Téléchargements/"Design sans titre"
```

Lister les fichiers :

```bash
ls -lh *.png
```

Vérifier les dimensions des images :

```bash
identify -format "%f : %wx%h - %m\n" *.png
```

Exemple de sortie :

```text
forge-1.png : 1024x1024 - PNG
forge-2.png : 1024x1024 - PNG
serveur-forge.png : 1024x1024 - PNG
```

Ici, les fichiers sont bien en PNG et ont tous une taille de `1024 x 1024 px`.

---

## 4. Recadrer une image exportée trop grande (Canva)

Au téléchargement, Canva exporte la **page entière**, pas seulement l'élément sélectionné.

Le cadre violet dans l'éditeur indique uniquement l'élément sélectionné.
Il ne définit pas la zone exportée.

Donc si la page fait `1024 x 1024 px`, Canva exporte un PNG `1024 x 1024 px`, même si l'illustration n'occupe qu'une bande au milieu.
Le reste de l'image est transparent si l'option **Arrière-plan transparent** est cochée.

La solution la plus propre : exporter depuis Canva en PNG transparent, puis supprimer automatiquement tout le vide autour avec ImageMagick.

Se placer dans le dossier de l'image téléchargée, puis tester sur un seul fichier :

```bash
convert "ton-image.png" -trim +repage "ton-image-recadree.png"
```

Exemple :

```bash
convert "illustration.png" -trim +repage "illustration-recadree.png"
```

Vérifier ensuite la nouvelle taille :

```bash
identify "illustration-recadree.png"
```

Explication :

| Élément | Rôle |
|---|---|
| `-trim` | Supprime les bords vides transparents autour de l'image. |
| `+repage` | Réinitialise la zone de page pour que la nouvelle taille soit propre. |

Recadrer le vide est utile avant de générer les tailles : l'illustration occupe alors toute la toile.
En enchaînant ensuite avec le script carré strict (section 11), le logo recadré est recentré sur une toile carrée, sans marge transparente parasite.

---

## 5. Redimensionner une seule image

Exemple : créer une version `512 x 512 px` d'un logo.

```bash
convert "forge-1.png" \
  -resize "512x512" \
  -background none \
  -alpha on \
  "PNG32:forge-1-512.png"
```

Explication :

| Élément | Rôle |
|---|---|
| `convert` | Lance ImageMagick 6. |
| `"forge-1.png"` | Image source. |
| `-resize "512x512"` | Redimensionne l'image. |
| `-background none` | Conserve un fond transparent. |
| `-alpha on` | Active le canal alpha, donc la transparence. |
| `PNG32:` | Force une sortie PNG avec transparence propre. |
| `"forge-1-512.png"` | Nom du fichier généré. |

---

## 6. Script : générer toutes les tailles pour tous les PNG du dossier

Ce script traite tous les fichiers `.png` présents dans le dossier courant.

Il crée un dossier `logos-redimensionnes`, puis un sous-dossier par taille.

```bash
mkdir -p logos-redimensionnes

for size in 1024 512 256 128 64 32 16; do
  mkdir -p "logos-redimensionnes/${size}x${size}"

  for file in *.png; do
    convert "$file" \
      -resize "${size}x${size}" \
      -background none \
      -alpha on \
      "PNG32:logos-redimensionnes/${size}x${size}/${file%.png}-${size}.png"
  done
done
```

Structure générée :

```text
logos-redimensionnes/
├── 1024x1024/
├── 512x512/
├── 256x256/
├── 128x128/
├── 64x64/
├── 32x32/
└── 16x16/
```

Exemple de fichiers générés :

```text
logos-redimensionnes/512x512/forge-1-512.png
logos-redimensionnes/256x256/forge-1-256.png
logos-redimensionnes/128x128/serveur-forge-128.png
```

---

## 7. Vérifier les fichiers générés

Afficher tous les fichiers créés :

```bash
find logos-redimensionnes -type f | sort
```

Vérifier les dimensions :

```bash
identify -format "%f : %wx%h - %m\n" logos-redimensionnes/*/*.png
```

Pour vérifier qu'un fichier contient bien un canal alpha :

```bash
identify -verbose logos-redimensionnes/512x512/forge-1-512.png | grep -i alpha
```

Si l'image contient bien de la transparence, la sortie doit mentionner `alpha`.

---

## 8. Script plus propre à enregistrer dans un fichier

Créer un fichier de script :

```bash
nano resize-logos.sh
```

Coller ce contenu :

```bash
#!/usr/bin/env bash

set -euo pipefail

OUTPUT_DIR="logos-redimensionnes"
SIZES=(1024 512 256 128 64 32 16)

mkdir -p "$OUTPUT_DIR"

for size in "${SIZES[@]}"; do
  mkdir -p "$OUTPUT_DIR/${size}x${size}"

  for file in *.png; do
    [ -e "$file" ] || continue

    output="$OUTPUT_DIR/${size}x${size}/${file%.png}-${size}.png"

    convert "$file" \
      -resize "${size}x${size}" \
      -background none \
      -alpha on \
      "PNG32:$output"

    echo "Créé : $output"
  done
done

echo "Terminé."
```

Rendre le script exécutable :

```bash
chmod +x resize-logos.sh
```

Lancer le script :

```bash
./resize-logos.sh
```

---

## 9. Script avec dossier source et dossier de sortie

Ce script est plus réutilisable.
Il permet d'indiquer un dossier source et un dossier de sortie.

Créer le fichier :

```bash
nano resize-logos-dir.sh
```

Contenu :

```bash
#!/usr/bin/env bash

set -euo pipefail

SOURCE_DIR="${1:-.}"
OUTPUT_DIR="${2:-logos-redimensionnes}"
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
    basename_no_ext="${filename%.*}"
    output="$OUTPUT_DIR/${size}x${size}/${basename_no_ext}-${size}.png"

    convert "$file" \
      -resize "${size}x${size}" \
      -background none \
      -alpha on \
      "PNG32:$output"

    echo "Créé : $output"
  done
done

echo "Terminé."
```

Rendre le script exécutable :

```bash
chmod +x resize-logos-dir.sh
```

Utilisation depuis le dossier courant :

```bash
./resize-logos-dir.sh
```

Utilisation avec un dossier source précis :

```bash
./resize-logos-dir.sh ~/Téléchargements/"Design sans titre" logos-redimensionnes
```

---

## 10. Forcer une image carrée avec fond transparent

Si une image source n'est pas parfaitement carrée, `-resize` conserve les proportions.
C'est souvent souhaitable.

Mais pour produire une image exactement carrée, par exemple `512 x 512 px`, avec le logo centré sur fond transparent :

```bash
convert "logo.png" \
  -resize "512x512" \
  -background none \
  -gravity center \
  -extent "512x512" \
  -alpha on \
  "PNG32:logo-512.png"
```

Explication :

| Élément | Rôle |
|---|---|
| `-gravity center` | Centre l'image. |
| `-extent "512x512"` | Force une toile finale exactement carrée. |
| `-background none` | Les zones ajoutées restent transparentes. |

---

## 11. Script carré strict pour tous les logos

Ce script garantit une sortie exactement carrée à chaque taille.

```bash
mkdir -p logos-carres

for size in 1024 512 256 128 64 32 16; do
  mkdir -p "logos-carres/${size}x${size}"

  for file in *.png; do
    convert "$file" \
      -resize "${size}x${size}" \
      -background none \
      -gravity center \
      -extent "${size}x${size}" \
      -alpha on \
      "PNG32:logos-carres/${size}x${size}/${file%.png}-${size}.png"
  done
done
```

C'est la version à privilégier pour des logos, favicons, icônes et illustrations techniques.

---

## 12. Créer un fichier ICO à partir d'un PNG

Pour un favicon classique, il peut être utile de générer un `.ico`.

Exemple à partir d'un logo carré transparent :

```bash
convert "forge-1.png" \
  -define icon:auto-resize=256,128,64,48,32,16 \
  "favicon.ico"
```

Le fichier `favicon.ico` contiendra plusieurs tailles intégrées.

---

## 13. Bonnes pratiques

- Toujours exporter depuis Canva en **PNG**.
- Cocher **Arrière-plan transparent** dans Canva.
- Éviter le JPG pour les logos, car le JPG ne gère pas la transparence.
- Garder une version source en grande taille, par exemple `1024 x 1024` ou `2048 x 2048`.
- Redimensionner ensuite avec ImageMagick.
- Mettre les fichiers générés dans un dossier séparé.
- Conserver des noms explicites : `logo-512.png`, `logo-256.png`, `favicon.ico`.
- Pour les logos Forge, privilégier des tailles carrées propres et une transparence réelle.

---

## 14. Commande recommandée pour le cas Forge

Dans le cas actuel, les images sont déjà en `1024 x 1024 px`.

La commande recommandée est donc :

```bash
mkdir -p logos-carres

for size in 1024 512 256 128 64 32 16; do
  mkdir -p "logos-carres/${size}x${size}"

  for file in *.png; do
    convert "$file" \
      -resize "${size}x${size}" \
      -background none \
      -gravity center \
      -extent "${size}x${size}" \
      -alpha on \
      "PNG32:logos-carres/${size}x${size}/${file%.png}-${size}.png"
  done
done
```

Puis vérifier :

```bash
find logos-carres -type f | sort
identify -format "%f : %wx%h - %m\n" logos-carres/*/*.png
```

Cette méthode est plus fiable que de refaire les exports un par un dans Canva.
