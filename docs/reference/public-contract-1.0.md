# Contrat public 1.0 (gel)

> **Gel de la surface publique** avant `1.0.0`. Tickets :
> `CLI-PUBLIC-CONTRACT-FREEZE-001`, `STARTERS-FINAL-CONTRACT-001`,
> `DOCS-LINKS-FINAL-AUDIT-001` (Phase 1 de la
> [roadmap beta.13](../roadmap/beta13-roadmap.md)).

Ce document **fige** ce qui constitue l'API publique de Forge pour la série
1.x. Après `1.0.0`, toute rupture de cette surface (renommage, suppression)
passe par une **release majeure** (charte, règle C). Avant 1.0, le gel sert à
**arrêter la valse de renommages** et à donner un contrat stable aux premiers
utilisateurs.

Un garde-fou — `tests/meta/test_public_contract_1_0_001.py` — verrouille
mécaniquement les listes ci-dessous : toute dérive casse la suite.

---

## 1. Famille de commandes `opt-in:*` (gelée)

La famille canonique de gestion des opt-ins officiels, **exactement 5 verbes** :

| Commande | Axe | Effet |
|---|---|---|
| `forge opt-in:install <name>` | présence (+) | affiche la commande `pip`/`pipx` (n'exécute rien) |
| `forge opt-in:remove <name>` | présence (−) | affiche la désinstallation |
| `forge opt-in:enable <name>` | activation (+) | câblage réel (kind `route`) / conseil (library, crosscutting) |
| `forge opt-in:disable <name>` | activation (−) | inverse de `enable` |
| `forge opt-in:list` | lecture | état des 7 opt-ins officiels |

**Décisions finales 1.0** :

- `enable`/`disable` font un **câblage réel uniquement pour le kind `route`**
  (iot) ; pour `library` (workflow, stats, media) et `crosscutting` (mfa,
  rbac), ils sont **informatifs** (ADR-016 D8 + A1). C'est le contrat 1.0, pas
  une étape intermédiaire.
- Les anciennes commandes `optin:enable` / `optin:list` (sans tiret) sont
  **définitivement retirées**.

## 2. Famille `module:*` (gelée, distincte)

Le système de **module local** (workflow d'auteur), **exactement 4 commandes** :

`forge module:list`, `forge module:install`, `forge module:files`,
`forge module:routes`.

**Décision finale 1.0** : `module:*` reste **distinct** de `opt-in:*`
(ADR-016 A2) — il sert à *fabriquer* un module local, pas à *consommer* un
opt-in officiel. Il n'est pas fusionné. Un nom inconnu passé à `opt-in:*`
oriente vers `forge module:install`.

## 3. Reste de la surface CLI

L'ensemble des commandes dispatchées est figé par
`tests/meta/test_cli_help_flags_closing_audit_001.py`
(`ALL_DISPATCHED_COMMANDS`). Chaque commande publique a une aide riche
(`forge <cmd> --help`) et une entrée dans
[`cli-commands.md`](cli-commands.md). Les codes de sortie suivent la
convention : `0` succès, `2` usage/argument, `1` erreur d'exécution.

## 4. Starters 1.0 (gelés — 17)

La liste pédagogique est **figée** : 17 starters, numérotés de 1 à 17,
nommés selon [la convention](../philosophy/starter-author-guide.md)
(`welcome-optin-<module>`, `users-core-auth`, `first-*`…). Le 17ᵉ,
`welcome-optin-video`, accompagne le passage de `forge-mvc-video` en Beta.

```
csrf, dynamic-route, first-crud, first-crud-generated, first-html-view,
first-sql, first-sql-write, form-post, json-response, query-params,
request-debug, server-validation, users-core-auth, welcome,
welcome-optin-iot, welcome-optin-mfa
```

Les anciennes applications métier lourdes ont été **archivées hors du système
starter**. Aucun ajout, retrait ni renommage de starter avant 1.0 sans mise à
jour de ce contrat.

## 5. Liens documentaires

L'intégrité des liens internes de la documentation est **garantie en
continu** par `mkdocs build --strict`, exécuté dans la suite de tests
(`tests/meta/test_install_docs_structure_001.py` et autres). Un lien cassé
fait échouer la suite. Aucun audit manuel séparé n'est requis : c'est déjà
enforced.
