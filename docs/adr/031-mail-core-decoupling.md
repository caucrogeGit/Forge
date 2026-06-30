# ADR-031 : Découplage complet du mail hors de `core.forge`

## Statut

Acceptée et mise en œuvre (ticket `MAIL-DECOUPLE-CORE-001`).
Le cœur ne porte plus aucune configuration `mail_*` ; `forge-mvc-mail` lit la sienne depuis l'environnement.

Complète [ADR-022](022-mail-extraction.md) (extraction de l'email vers
`forge-mvc-mail`) et renforce [ADR-004](004-core-perimeter.md) (périmètre du
core minimal) ainsi que le principe 8 (noyau minimal, briques opt-in).

---

## Contexte

ADR-022 a extrait `core/mail/` vers l'opt-in `forge-mvc-mail`, mais a laissé un
**couplage résiduel** que l'ADR notait lui-même : « sa seule dépendance core est
`core.forge` pour la config ». Concrètement, le core et le squelette nu
continuent de connaître le mail :

- `core/forge.py` réserve 13 clés `mail_*` dans son registre de configuration ;
- `core.forge.configure()` accepte des kwargs `mail_*` ;
- `core/app/app_factory.py` lit un bloc `MAIL_*` optionnel depuis `config.py`
  (`_optional_mail_kwargs()`) ;
- le squelette nu pré-câble la config mail sur trois fichiers utilisateur :
  `env/example` (bloc `MAIL_*`), `config.py` (imports + attributs) et `app.py`
  (13 arguments `mail_*` passés à `forge.configure`).

`forge-mvc-mail`, quand il est installé, lit ces valeurs via l'API publique
`core.forge.get("mail_*")`.

Deux constats rendent ce couplage injustifié :

1. **Aucun code du core ne lit `core.forge.get("mail_*")`.** Seul
   `forge-mvc-mail` les consomme. Le core auth manipule des **adresses** et des
   **jetons** de vérification (`core/auth/email.py`, `reset.py`) mais
   **n'envoie aucun email**.
2. Un projet nu (`forge new`, `requirements.txt = forge-mvc` seul) transporte
   ainsi une cinquantaine de lignes de plomberie mail pour une brique qui n'est
   pas installée. C'est contraire au principe 3 (refuser la magie cachée) et au
   principe 8.

Le test de légitimité d'ADR-004 (« si je retire cette brique, une application
basique tourne-t-elle encore ? ») est satisfait : le mail doit relever de la
**seule** responsabilité de son opt-in, registre de config compris.

---

## Décision

**Toute connaissance du mail quitte le core et le squelette nu.
`forge-mvc-mail` possède sa configuration de bout en bout, lue depuis
l'environnement.**

| Élément | Avant | Après |
|---|---|---|
| Slots `mail_*` dans `core/forge.py` | présents (défauts) | supprimés |
| `core.forge.configure(mail_*=…)` | accepte les kwargs | n'accepte plus |
| `core/app/app_factory.py` `_optional_mail_kwargs()` | présent | supprimé |
| Source de config de `forge-mvc-mail` | `core.forge.get("mail_*")` | `os.getenv` (config interne au module) |
| Squelette `env/example` / `config.py` / `app.py` | pré-câblent `MAIL_*` | aucune trace mail |
| Défaut de `MAIL_ENABLED` quand la variable est absente | `True` (côté core) | `False` (zéro envoi accidentel) |

L'environnement est déjà chargé par `config.py` (`load_dotenv`), donc
`os.getenv("MAIL_*")` fonctionne dès que l'utilisateur ajoute le bloc `MAIL_*`
à son `env/dev`. Le mail ne dépend plus du registre core, et le core ne dépend
plus du mail.

---

## Conséquences

**Positives :**

- Le core respecte strictement ADR-004 pour le mail : `grep -ri mail core/` ne
  retourne plus que `EmailField` (validation de formulaire) et le module
  `email` de la bibliothèque standard.
- Un projet nu démarre sans aucune plomberie mail.
- `forge-mvc-mail` devient autonome : il lit et porte sa propre config.
- Défaut plus sûr (`MAIL_ENABLED` absent => désactivé).

**À assumer :**

- Rupture **interne** de `core.forge.configure` (retrait des kwargs `mail_*`).
  Aucun alias ni guide de migration : phase bêta pré-1.0 (convention CLAUDE.md),
  `forge-mvc-mail` est le seul appelant et il est migré dans le même lot.
  À signaler au `CHANGELOG.md`.
- Le provisioning de la config mail (le bloc `MAIL_*` à ajouter à `env/dev`)
  est documenté et fourni **par le module mail**, jamais écrit silencieusement
  dans les fichiers utilisateur (principe 9). Mode « Forge affiche ».

---

## Mise en œuvre (ticket `MAIL-DECOUPLE-CORE-001`)

1. Gardes d'abord (rouges au départ) : `mail` absent de `core/forge.py` ;
   projet nu sans `MAIL_*` ; `forge-mvc-mail` ne référence plus `core.forge`
   pour le mail.
2. Module mail : `MailConfig.from_env()` (généralise
   `cli._configure_forge_from_env`) remplace `from_forge()` ; bascule
   `mailer.from_config`, `transports`, `cli` dessus ; défaut
   `mail_enabled=False`.
3. Core : retirer les 13 clés `mail_*` de `core/forge.py` et
   `_optional_mail_kwargs()` (+ son appel) de `core/app/app_factory.py`.
4. Squelette nu : retirer la plomberie mail de `env/example` (hook §12, édition
   par script), `config.py` et `app.py`.
5. Documentation : `docs/features/mail.md` documente le bloc env côté module ;
   mise à jour du parcours welcome-mail.
6. Recette : un projet nu démarre sans trace mail ; un projet
   `pip install forge-mvc-mail` + bloc env vérifie `mail:test` / `mail:doctor`
   (transport `log`).

**Validations :**

```bash
python -m pytest -x -q
python -m compileall -q .
ruff check .
mkdocs build --strict
git diff --check
```

---

## Alternatives rejetées

**Conserver les slots `mail_*` inertes dans `core.forge`** (demi-mesure :
ne déplacer que la plomberie du squelette). Rejetée : laisse de la connaissance
mail dans le core, donc ne satisfait pas le principe 4. Le mail doit être de la
seule responsabilité de l'opt-in, registre compris.

---

## Charte appliquée

Principe 3 (refuser la magie cachée), principe 4 / ADR-004 (périmètre du core),
principe 8 (noyau minimal), principe 9 (pas d'écriture invisible dans le code
utilisateur), principe 10 (l'API publique reste un contrat clair).
