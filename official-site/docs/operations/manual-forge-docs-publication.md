# Publication manuelle de la documentation Forge

Cette page documente la procédure officielle de publication de la
documentation Forge vers [forgemvc.com](https://forgemvc.com/).

La publication **reste manuelle**. Aucun timer systemd, aucune action
GitHub n'est déclenché automatiquement : le développeur décide quand la
documentation est publiable.

Ticket de référence : `OFFICIAL-SITE-DOCS-PUBLISH-PROCEDURE-001`.

---

## 1. Rôle des dépôts

| Chemin | Rôle |
|--------|------|
| `~/Projets/Forge` | Source canonique de la documentation Forge (`docs/`). |
| `~/Projets/Forge-official-site` | Projet qui importe, construit et déploie le site officiel. |
| `forgemvc.com` | Site public final, servi depuis `/srv/forge-web/current` par la VM `forge-web`. |

L'import et le build se font uniquement dans `Forge-official-site`. Le
dépôt `Forge` n'est jamais modifié par la procédure de publication.

---

## 2. Préconditions

Avant toute publication :

- `Forge` est sur `main` ;
- `Forge` est propre (`git status` vide) ;
- les modifications de doc dans `Forge` sont **poussées** sur `origin/main`
  (l'import lit le working tree, mais ce qui n'est pas poussé n'est pas
  reproductible côté équipe) ;
- `Forge-official-site` est sur `main` ;
- `Forge-official-site` est propre (ou contient uniquement des
  modifications produites par un précédent import dans `docs/forge/`) ;
- la VM `forge-web` est joignable en SSH non interactif
  (cf. `roger@192.168.1.98`) ;
- Caddy sert bien `/srv/forge-web/current`.

---

## 3. Dry-run recommandé

Le mode par défaut du script de déploiement est `DRY_RUN=1`. Il n'écrit
rien sur la VM.

```bash
cd ~/Projets/Forge-official-site
make docs-check
```

Cette commande appelle en interne
`bash scripts/sync-forge-docs-and-deploy.sh`. Le script reste
utilisable directement si besoin de surcharger une variable
d'environnement ponctuelle.

Le dry-run :

- importe la documentation depuis `~/Projets/Forge/docs` vers
  `docs/forge/` ;
- vérifie la complétude de l'import ;
- construit le site dans `dist/` ;
- lance les validations locales
  (`check_no_github_pages_docs.py`, `check_local_links.py`,
  `py_compile`, `bash -n`, `git diff --check`) ;
- **n'écrit pas** sur la VM ;
- **ne crée pas** de backup distant ;
- **ne modifie pas** `/srv/forge-web/current`.

À la fin, le script affiche le bilan local (commits, taille `dist/`,
pages clés trouvées) et la commande à lancer pour le déploiement réel.

---

## 4. Déploiement réel

Une fois le dry-run vert :

```bash
cd ~/Projets/Forge-official-site
make docs-publish
```

Cette commande appelle en interne
`DRY_RUN=0 bash scripts/sync-forge-docs-and-deploy.sh`. Elle publie
réellement sur `forgemvc.com` : ne la lancer qu'après un dry-run vert.

Ce mode reprend toutes les étapes du dry-run, puis :

- crée un backup distant
  `/srv/forge-web/backups/current-YYYYMMDD-HHMMSS` (sauf premier
  déploiement, où `current` n'existe pas encore) ;
- prépare et peuple le staging distant
  `/tmp/forge-web-deploy-staging` via `rsync -avz --delete dist/` ;
- vérifie les pages clés dans le staging ;
- bascule le staging vers `/srv/forge-web/current` ;
- vérifie les pages clés dans `current`.

Si une des pages clés est manquante côté staging, la bascule est
annulée. Si elle est manquante côté `current` après bascule, le script
retourne en erreur — un rollback manuel est alors requis (cf. §7).

---

## 5. Vérifications publiques après déploiement

Une fois le déploiement réussi, vérifier depuis n'importe quelle machine
que le site répond correctement :

```bash
curl -I https://forgemvc.com/
curl -I https://forgemvc.com/docs/
curl -I https://forgemvc.com/docs/forge/
curl -I https://forgemvc.com/docs/forge/starters/query-params/
curl -I https://forgemvc.com/docs/forge/starters/server-validation/
```

Chaque réponse doit commencer par :

```text
HTTP/2 200
```

Si une route renvoie `404` ou `502`, recontrôler :

- la sortie du script (la bascule a-t-elle abouti ?) ;
- l'état de Caddy sur la VM ;
- la présence du fichier `index.html` correspondant dans
  `/srv/forge-web/current`.

---

## 6. Commit après synchronisation

Si l'import a modifié des fichiers dans `Forge-official-site` (typique
quand la documentation Forge a changé), il faut les committer pour que
l'état du dépôt reflète l'état publié.

```bash
git status --short
git add docs/forge mkdocs.yml scripts/import_forge_docs.py
git commit -m "docs: sync official site with Forge docs"
git push origin main
```

Adapter la liste `git add` au périmètre réel : si seul `docs/forge/` a
bougé, ne pas inclure `mkdocs.yml`. Si seul un script a changé, faire
un commit dédié plutôt qu'un commit mixte.

Faire ce commit **après** un déploiement réussi : on commit ce qui est
en ligne, pas une intention de publication.

---

## 7. Rollback

Les backups sont stockés sur la VM dans :

```text
/srv/forge-web/backups/current-YYYYMMDD-HHMMSS
```

Un rollback consiste à resynchroniser un backup choisi vers
`/srv/forge-web/current`. La procédure exacte n'est pas automatisée :
elle reste un acte manuel et délibéré.

> **Attention** — toute manipulation de `/srv/forge-web/current`
> impacte directement le site public. Avant d'écraser `current`,
> identifier précisément quel backup correspond à l'état souhaité
> (`ls -lt /srv/forge-web/backups/`) et noter le timestamp courant pour
> pouvoir revenir en arrière si nécessaire.

Schéma logique d'un rollback (à adapter au cas par cas, **ne pas
copier-coller à l'aveugle**) :

```bash
ssh roger@192.168.1.98
ls -lt /srv/forge-web/backups/
# choisir un backup ; le copier ensuite vers current après vérification.
```

---

## 8. Erreurs fréquentes

### SSH demande un mot de passe

Le script utilise SSH plusieurs fois (backup, rsync, vérifications). Si
SSH demande un mot de passe, chaque interaction devient bloquante.

Solution : disposer d'une clé SSH publique installée sur la VM
(`~/.ssh/authorized_keys` de `roger@forge-web`) et chargée par
`ssh-agent` côté devstation.

### Forge n'est pas propre

Le script refuse de démarrer si `~/Projets/Forge` contient des
modifications non committées. Committer ou stasher dans `Forge` avant
de relancer.

### Forge-official-site n'est pas propre

Le pré-vol tolère uniquement les modifications dans `docs/forge/` et
le script `scripts/sync-forge-docs-and-deploy.sh` lui-même. Tout autre
fichier modifié bloque la procédure : committer ou stasher.

### `check_local_links.py` trouve un lien cassé

La sortie liste les liens cassés (`fichier:'url' → cible`). Corriger
soit dans la source (`~/Projets/Forge/docs`) — repousser dans `Forge`
puis relancer — soit ajuster `KNOWN_FIXUPS` dans
`scripts/import_forge_docs.py` si c'est un lien systémique cassé à
l'import.

### GitHub Pages / `github.io` réapparaît

`check_no_github_pages_docs.py` échoue dès qu'un lien actif vers
`caucrogegit.github.io/Forge` est trouvé dans la landing ou la
documentation publiée. Le site officiel ne doit pas dépendre de
GitHub Pages : remplacer le lien par `/docs/forge/...` ou
`https://forgemvc.com/docs/forge/...`.

### `/srv/forge-web/current` n'est pas accessible en écriture

Le script tente `rm -rf` puis `mv` sur `current`. Si les droits sont
insuffisants, vérifier que le compte SSH distant possède les droits
d'écriture sur `/srv/forge-web/`. Ne pas contourner avec `sudo` dans
le script : régler les permissions à la source.

### `mkdocs build --strict` échoue

Le build est strict : tout warning devient une erreur. Les causes
classiques sont un lien Markdown cassé, un fichier référencé dans la
nav `mkdocs.yml` mais absent du disque, ou une page importée avec un
front-matter invalide. La sortie de `mkdocs build --strict` indique le
fichier et le warning à corriger.
