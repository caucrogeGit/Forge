# ADR-020 — Périmètre de `forge-mvc-files` : primitives de stockage média génériques

## Statut

Proposé — Forge 1.0.0-beta.x.

> Décision de **direction** (option B ci-dessous). L'ADR fixe le périmètre cible
> de `forge-mvc-files` ; l'exécution est progressive et **non urgente** (les
> opt-ins déjà livrés ne sont pas refondus avant la 1.0).

---

## Date

2026-06-05

---

## Contexte

Depuis ADR-019, `forge-mvc-files` détient le pipeline d'**upload générique**
extrait du core : écriture disque anti-traversal, `save_upload`/`SavedUpload`,
service de fichiers `serve_media_file` (HTTP Range), suppression, rate-limit.
La validation pure (extension/MIME/taille, `UploadError`) **reste dans le core**
(`core.forms.upload_validation`), réexportée par files — le core ne peut pas
dépendre d'un opt-in (ADR-004).

`forge-mvc-files` est **présenté** comme l'upload générique de Forge. Mais l'audit
des dépendances révèle qu'il n'est **pas** la fondation commune annoncée :

| Module | S'appuie sur `forge-mvc-files` ? | Modèle de stockage |
|---|---|---|
| `forge-mvc-images` | **Oui** (dépendance déclarée + imports réels) | nom assaini + variantes (même forme que le « document » de files) |
| `forge-mvc-video` | **Non** (0 dépendance, 0 import) | **propre** storage UUID, multi-rendition (`originals/mp4/posters`), transcodage |
| `forge-mvc-audio` | **Non** (0 dépendance, 0 import) | **propre** storage UUID, transcodage |

Il existe donc **deux approches de stockage parallèles** dans Forge :

- le pipeline générique core→files (utilisé par images) ;
- des stockages dédiés UUID (video, audio), indépendants.

Pourquoi cette divergence ? Elle est **principielle**, pas accidentelle :

- video/audio adoptent un chemin **100% UUID** (le nom utilisateur n'apparaît
  jamais — anti-traversal *par construction*), **plus strict** que le modèle
  « nom assaini conservé » de `save_upload` ;
- ils produisent **plusieurs fichiers dérivés** par upload (source + MP4/MP3 +
  poster), dans un sous-arbre dédié ;
- ils ont un **cycle de vie** (transcodage ffmpeg, états `uploaded→processing→ready`)
  hors périmètre de files.

À noter : le service **HTTP Range** est déjà mutualisé **dans le core**
(`Response.file`) — files et le `http.py` de video y délèguent tous deux. La
duplication réelle n'est donc **pas** dans le service, mais dans l'écriture sûre
et les helpers anti-traversal, ré-implémentés côté video/audio.

Le résultat : la promesse « files = socle média générique » n'est tenue qu'à
moitié, et chaque nouvel opt-in média risque de re-diverger (tension avec le
principe 11, « une seule façon officielle »).

---

## Décision

**Option B — `forge-mvc-files` devient une boîte à primitives de stockage média
génériques** sur laquelle **tout opt-in média** (image, video, audio, futurs)
compose **sa propre** disposition.

1. **files reste un opt-in, hors du core** (confirmation d'ADR-019/ADR-004 :
   le core n'a pas à traiter de fichiers).
2. **files expose des primitives composables**, pas un pipeline imposé :
   - écriture disque sûre, y compris un **mode UUID** (nom utilisateur absent du
     chemin) en plus du mode « nom assaini » actuel ;
   - helpers anti-traversal / chemin (`secure_filename`, `is_safe_media_path`,
     `normalize_media_path`, `save_bytes`) ;
   - un appui pour les **dispositions multi-rendition** (un média = plusieurs
     fichiers dérivés sous une racine) ;
   - service Range (mince enveloppe sur la primitive core), rate-limit, suppression.
3. **`save_upload` reste la convenance « document »** bâtie sur ces primitives —
   c'est elle qu'images réutilise pour le chemin document. Elle n'est **plus**
   présentée comme « la » façon de stocker un média, mais comme **une** façade.
4. **Règle pérenne** : tout **nouvel** opt-in média s'appuie sur les primitives
   de files (et on vérifie que files expose ce dont il a besoin).
5. **L'API des primitives est conçue contre les 3 clients réels** (image, video,
   audio) déjà existants — on extrait la forme commune observée, on n'invente pas
   une abstraction spéculative.

### Hors périmètre

- **Pas de big-bang** : video et audio (déjà livrés, video publié) ne sont **pas**
  refondus en urgence. Leur repointage sur les primitives de files est
  **opportuniste** et **post-1.0**.
- **files ne devient pas un framework configurable** à options (anti principe 8) :
  des primitives, pas une usine.
- files **n'absorbe pas** la validation de domaine (codecs/ffprobe), le
  transcodage, ni aucun **état/BDD** — cela reste propriété des opt-ins métier.
- On ne **force pas** video/audio sur le modèle « nom assaini » : ce serait un
  recul de sécurité par rapport à leur chemin UUID.

---

## Conséquences

### Positives

- **Sécurité à un seul endroit** : l'écriture sûre / anti-traversal écrite,
  auditée et corrigée **une fois**, partagée par tous les médias.
- **Clarté conceptuelle** : « files = la fondation média » devient vrai, pas un
  slogan à moitié tenu.
- **Extensibilité** : un nouvel opt-in média **assemble** au lieu de réinventer.
- **Cohérence** (principe 11) : une seule façon officielle de stocker/servir un
  fichier en bas niveau.

### Coûts / ruptures

- L'API de files **grandit** (mode UUID, appui multi-rendition) — à garder
  minimale et justifiée par les 3 clients réels.
- video et audio gagneront (à terme) une **dépendance** sur files qu'ils n'ont
  pas aujourd'hui.
- **Effort de repointage** sur du code livré/publié (video b13) → assumé
  progressif, post-1.0.
- **Gain de dé-duplication modéré** : le service Range est déjà core ; l'essentiel
  partagé est l'écriture sûre + helpers. La valeur est *cohérence + sécurité +
  extensibilité*, pas un dégraissage massif.
- **Risque** : sur-généraliser files en framework. Garde-fou : revue stricte au
  regard du principe 8 à chaque ajout de primitive.

---

## Plan d'exécution (tickets)

1. **Cet ADR** — fixe la direction (option B).
2. **`FILES-PRIMITIVES-*`** — exposer proprement le mode UUID + l'appui
   multi-rendition, **validés contre la forme de image/video/audio**, sans
   modifier encore aucun consommateur.
3. **Repointage opportuniste** de video puis audio sur les primitives de files
   (post-1.0, tickets dédiés, suite verte à chaque étape).
4. **Règle de contribution** : documenter que tout nouvel opt-in média s'appuie
   sur files (à refléter dans `docs/philosophy/module-author-guide.md` et la
   page médias).

---

## Alternatives écartées

- **(A) Statu quo — files = pipeline document unique.** Laisse video/audio
  divergents et la promesse « socle générique » à moitié fausse ; la dérive se
  répète au prochain opt-in média. Écarté.
- **Forcer video/audio à utiliser `save_upload`.** Les mettrait sur le modèle
  « nom assaini conservé », un **recul de sécurité** vs leur chemin UUID *par
  construction*. Écarté.
- **Réintégrer un stockage commun dans le core.** Contredit ADR-004 et le
  principe 8 (le core n'a pas à traiter de fichiers). Écarté.
- **Tout laisser tel quel et l'assumer.** Deux stockages parallèles non
  documentés = dette implicite ; au minimum la frontière doit être actée — ce que
  fait cet ADR. Écarté au profit de la convergence dirigée par B.

---

## Références

- ADR-004 — Périmètre du core minimal strict (le core ne dépend pas d'un opt-in).
- ADR-018 — Extraction du traitement d'image (`forge-mvc-images`).
- ADR-019 — Extraction de l'upload générique (`forge-mvc-files`).
- Charte v2 — principe 8 (noyau minimal, briques opt-in) et principe 11 (une
  seule façon officielle de faire chaque chose).
