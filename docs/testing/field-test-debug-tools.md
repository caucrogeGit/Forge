# Tests terrain : Outils de diagnostic

[Accueil](../index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

---

## Principe général

Le testeur ne corrige pas Forge pendant un ticket FT. Son rôle est d'observer, de lancer les outils de diagnostic prévus, de collecter les preuves et de remplir un retour exploitable.

Un bon retour terrain ne dit pas seulement "ça ne marche pas".
Il indique la commande lancée, le résultat obtenu, le diagnostic exécuté, les logs utiles, le statut et la gravité.

---

## Quel outil utiliser ?

| Situation | Outil conseillé | Preuve à fournir |
|---|---|---|
| Le projet semble mal configuré | `forge doctor` | sortie complète |
| Validation stricte du projet | `forge project:check` | sortie complète |
| Rapport d'audit détaillé | `forge project:audit` | sortie complète |
| Une route ne répond pas | `forge routes:list` | route attendue + sortie |
| Une page docs ne se construit pas | `mkdocs build --strict` | sortie complète |
| Un ticket modifie des fichiers | `git status` | état avant/après |
| Problème de whitespace ou fin de ligne | `git diff --check` | sortie complète |
| Erreur Python ou import cassé | `python -m compileall -q .` | sortie complète |
| Régression supposée (si demandé) | `pytest` ciblé | commande + résultat |
| Erreur applicative en développement | logs Forge | fichier/log concerné |
| Erreur dans la documentation | modèle "documentation officielle erronée" | page + passage + preuve |

---

## Commandes de diagnostic disponibles

### `forge doctor`

**Objectif :** diagnostic large et tolérant de l'environnement Forge. Lecture seule, non destructif.

**Quand l'utiliser :** à chaque fois que quelque chose semble anormal dans le projet ou l'environnement. En particulier avant de signaler un problème.

**Ce que le testeur doit copier :** la sortie complète de la commande.

**À ne pas faire :** modifier Forge pour "corriger" ce que doctor signale.

```bash
forge doctor
```

---

### `forge project:check`

**Objectif :** contrôle strict des conventions du projet (CI-ready). Signale les écarts structurels.

**Quand l'utiliser :** quand la structure du projet semble incorrecte ou quand un ticket demande de vérifier la conformité.

**Ce que le testeur doit copier :** la sortie complète, y compris les lignes `[OK]` et `[WARN]` ou `[ERREUR]`.

**À ne pas faire :** corriger les erreurs signalées sans les documenter d'abord.

```bash
forge project:check
```

---

### `forge project:audit`

**Objectif :** rapport d'audit détaillé non destructif. Donne plus de détails que `project:check`.

**Quand l'utiliser :** pour approfondir un diagnostic après `project:check`, ou quand `project:check` signale une anomalie.

**Ce que le testeur doit copier :** les lignes `[OK]`, `[WARN]` et `[ERREUR]` pertinentes.

**À ne pas faire :** confondre avec `project:check`, les deux sont complémentaires.

```bash
forge project:audit
```

---

### `forge routes:list`

**Objectif :** affiche les routes déclarées dans `mvc/routes.py`.

**Quand l'utiliser :** quand une page ne répond pas, quand une URL semble absente, ou quand une route est supposée exister.

**Ce que le testeur doit copier :** la sortie complète + la route attendue.

**À ne pas faire :** modifier `mvc/routes.py` sans le documenter dans le retour.

```bash
forge routes:list
```

---

### `mkdocs build --strict`

**Objectif :** vérifie que la documentation Forge se construit sans erreur ni lien cassé.

**Quand l'utiliser :** quand un ticket touche à la documentation ou quand une page docs semble absente.

**Ce que le testeur doit copier :** la sortie complète, en particulier les lignes `ERROR` ou `WARNING`.

**À ne pas faire :** ignorer les avertissements, en mode `--strict`, un warning est une erreur.

```bash
mkdocs build --strict
```

---

### `git status`

**Objectif :** affiche l'état du dépôt, fichiers modifiés, non suivis, en attente de commit.

**Quand l'utiliser :** avant et après une étape de ticket qui crée ou modifie des fichiers.

**Ce que le testeur doit copier :** la sortie avant et après l'action.

```bash
git status
```

---

### `git diff --check`

**Objectif :** détecte les espaces de fin de ligne, les tabulations parasites et les problèmes de whitespace.

**Quand l'utiliser :** si un commit échoue pour cause de whitespace, ou lors de la validation finale.

**Ce que le testeur doit copier :** la sortie complète (vide = OK).

```bash
git diff --check
```

---

### `python -m compileall -q .`

**Objectif :** vérifie que tous les fichiers Python du projet se compilent sans erreur de syntaxe.

**Quand l'utiliser :** si une erreur d'import ou de syntaxe est suspectée, ou si un ticket a modifié des fichiers Python.

**Ce que le testeur doit copier :** la sortie complète (vide = OK).

```bash
python -m compileall -q .
```

---

### `pytest` (si demandé explicitement)

**Objectif :** exécute la suite de tests automatisés de Forge.

**Quand l'utiliser :** uniquement si le ticket le demande explicitement. Ne pas lancer `pytest` de façon préventive pendant un ticket documentaire ou d'installation.

**Ce que le testeur doit copier :** la ligne de résumé finale (`X passed, Y failed`) et les messages d'erreur éventuels.

**À ne pas faire :** corriger une erreur de test sans la documenter.

```bash
python -m pytest -x -q
```

---

## Logs et erreurs Forge

Forge enregistre les erreurs runtime en mode développement dans :

```text
storage/logs/errors.dev.jsonl   — journal JSON Lines (source canonique)
storage/logs/errors.dev.md      — vue lisible générée depuis le JSONL
```

**Où regarder :** ouvrir `storage/logs/errors.dev.md` pour une lecture rapide, ou `storage/logs/errors.dev.jsonl` pour le détail technique.

**Quoi copier :** les lignes correspondant à l'erreur observée, champ `message`, `exception_type`, `path`, `traceback`.

**Quoi ne pas publier :** les champs qui pourraient contenir des secrets (mots de passe, tokens, clés API). Vérifier le champ `message` avant de le copier dans un retour public.

**Comment signaler sans exposer de secret :**

```text
Erreur observée : [exception_type] dans [file]:[line]
Message : [remplacer la valeur sensible par ****]
```

Ne pas partager le fichier `env/dev` ou `env/prod` avec le retour.

---

## Documentation officielle erronée

Si la documentation Forge est fausse, incomplète ou contradictoire pendant un ticket :

1. ne pas corriger la documentation directement ;
2. noter la page concernée ;
3. noter le passage erroné ou ambigu ;
4. noter l'étape du ticket concernée ;
5. expliquer ce que la documentation dit ;
6. expliquer ce que Forge fait réellement ;
7. fournir les preuves ;
8. indiquer le contournement éventuel ;
9. choisir le statut `BLOQUÉ PAR DOCUMENTATION` ou `VALIDÉ AVEC FRICTION` ;
10. proposer la gravité S1, S2, S3 ou S4.

Voir : [Modèle de retour testeur](field-test-feedback-template.md) · [Triage et stabilisation](field-test-triage.md)

---

## Ce qu'il ne faut pas faire

- Ne pas modifier `core/` pendant un ticket FT.
- Ne pas corriger Forge pendant le ticket.
- Ne pas masquer une erreur par un contournement non signalé.
- Ne pas supprimer les logs avant le retour.
- Ne pas publier de secrets (mots de passe, tokens, clés).
- Ne pas classer "Validé" un ticket réussi uniquement grâce à l'aide du référent sans le noter.

---

## Résumé minimal à fournir dans un retour

```text
Commande lancée :
Résultat obtenu :
Outil de diagnostic utilisé :
Sortie du diagnostic :
Fichier/log consulté :
Statut proposé :
Gravité proposée :
```
