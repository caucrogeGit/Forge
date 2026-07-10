# L'internationalisation dans Forge (forge-mvc-i18n)

Ce document explique ce que fait l'opt-in `forge-mvc-i18n`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-i18n` traduit des chaînes via des catalogues JSON (`translations/<locale>.json`), avec une locale par défaut, une locale de repli, et un helper `trans()` utilisable dans le code et les templates.

Extrait du cœur (ADR-027), il s'active dès qu'il est installé : le renderer Jinja du cœur expose alors `trans()` aux templates.

??? note "1. Rôle du module"

    Une application multilingue a besoin de sortir le texte du code et de le ranger par langue.

    L'opt-in stocke les traductions dans des **catalogues JSON** (un fichier par locale) et fournit `trans("clé")` pour récupérer la bonne chaîne selon la locale courante.

    Quand une clé manque dans la locale demandée, il bascule sur la **locale de repli** ; si elle manque toujours, il renvoie la clé elle-même (jamais une erreur d'affichage).

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-i18n
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-i18n"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable i18n
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
    `forge opt-in:install i18n` affiche la commande `pip` sans l'exécuter.

    ### Désinstallation

    ```bash
    forge opt-in:disable i18n
    pip uninstall forge-mvc-i18n
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove i18n` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Commandes"

    `forge-mvc-i18n` ajoute ces commandes (le noyau garde un repli no-op, ADR-027) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `i18n:init` | Initialise les fichiers de traduction. | `forge i18n:init` |
    | `i18n:check` | Vérifie la complétude des traductions entre locales. | `forge i18n:check` |

??? note "4. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-i18n` |
    | Module | `forge_mvc_i18n` |
    | Catégorie | Internationalisation (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` |
    | API publique | `trans`, `load_catalog`, `get_default_locale`, `set_default_locale`, `get_fallback_locale`, `set_fallback_locale`, `clear_translation_cache` |
    | Catalogues | `translations/<locale>.json` |
    | Configuration | `i18n_default_locale`, `i18n_fallback_locale` (cœur) |
    | Helper Jinja | `trans()` exposé aux templates (ADR-046) |
    | Commandes | `i18n:init`, `i18n:check` |
    | Exceptions | `I18nError`, `TranslationCatalogError` |
    | Décision d'architecture | ADR-027 (extraction, repli no-op du cœur) |
    | Installation | `pip install --pre forge-mvc-i18n` |

??? note "5. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre le helper, les catalogues et l'exposition Jinja.

    Le diagramme de séquence montre la résolution d'une clé avec repli.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que `trans` lit des catalogues JSON (mis en cache) et que le renderer Jinja du cœur l'expose aux templates quand l'opt-in est présent.

    ```mermaid
    classDiagram
        direction LR

        class translator {
            <<module>>
            +trans(key, locale, translations_dir) str
            +load_catalog(locale, translations_dir) dict
            +get_default_locale() str
            +set_default_locale(locale)
            +get_fallback_locale() str
            +set_fallback_locale(locale)
            +clear_translation_cache()
        }

        class catalogues {
            <<fichiers JSON>>
            +fr.json
            +en.json
        }

        class JinjaRenderer {
            <<cœur>>
            +expose trans() aux templates
        }

        class I18nError {
            <<exception>>
        }

        translator --> catalogues : charge (avec cache)
        JinjaRenderer --> translator : expose trans()
        translator ..> I18nError : peut lever
    ```

    À retenir :

    - les traductions vivent dans `translations/<locale>.json` ;
    - `trans` résout une clé selon la locale, avec repli ;
    - les catalogues sont mis en cache (`clear_translation_cache` pour vider) ;
    - le helper `trans()` est exposé aux templates par le cœur quand l'opt-in est installé.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre la résolution d'une clé, avec repli sur la locale de fallback.

    ```mermaid
    sequenceDiagram
        participant App as Code / template
        participant Trans as trans()
        participant Cat as Catalogue JSON
        participant Conf as Locale (cœur)

        App->>Trans: trans("welcome.title")
        Trans->>Conf: locale courante (ou défaut)
        Trans->>Cat: load_catalog(locale) [cache]
        alt clé présente
            Cat-->>Trans: traduction
        else clé absente
            Trans->>Cat: load_catalog(locale de repli)
            Cat-->>Trans: traduction (ou la clé elle-même)
        end
        Trans-->>App: chaîne traduite
    ```

    À retenir :

    - la locale par défaut sert quand aucune n'est précisée ;
    - une clé absente déclenche le repli sur la locale de fallback ;
    - en dernier recours, `trans` renvoie la clé (pas d'erreur d'affichage) ;
    - le chargement passe par un cache pour éviter de relire le fichier.

??? note "6. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `trans` | `trans(key, locale=None, translations_dir="translations") -> str` | traduit une clé |
    | `load_catalog` | `load_catalog(locale, translations_dir="translations") -> dict[str, str]` | charge un catalogue (caché) |
    | `get_default_locale` | `get_default_locale() -> str` | locale par défaut |
    | `set_default_locale` | `set_default_locale(locale) -> None` | fixe la locale par défaut |
    | `get_fallback_locale` | `get_fallback_locale() -> str \| None` | locale de repli |
    | `set_fallback_locale` | `set_fallback_locale(locale) -> None` | fixe la locale de repli |
    | `clear_translation_cache` | `clear_translation_cache() -> None` | vide le cache des catalogues |
    | `I18nError`, `TranslationCatalogError` | exceptions | erreurs (locale invalide, catalogue illisible) |

??? note "7. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Traduire une clé (code) | `trans("clé")` |
    | Traduire dans un template | `{{ trans("clé") }}` |
    | Forcer une locale | `trans("clé", locale="en")` |
    | Choisir la langue par défaut | `set_default_locale("fr")` |
    | Définir le repli | `set_fallback_locale("en")` |
    | Vérifier les manques | `forge i18n:check` |
    | Recharger après édition | `clear_translation_cache()` |

??? note "8. Exemples d'utilisation"

    ### 8.1 Catalogue et traduction

    `translations/fr.json` :

    ```json
    {
      "welcome.title": "Bienvenue",
      "welcome.cta": "Commencer"
    }
    ```

    ```python
    from forge_mvc_i18n import trans, set_default_locale

    set_default_locale("fr")
    titre = trans("welcome.title")        # "Bienvenue"
    en = trans("welcome.title", locale="en")
    ```

    ### 8.2 Dans un template Jinja

    ```html
    <h1>{{ trans("welcome.title") }}</h1>
    <a href="/start">{{ trans("welcome.cta") }}</a>
    ```

    `trans()` est disponible dans les templates dès que l'opt-in est installé (le cœur l'expose via son renderer).

    !!! tip "Aide-mémoire"
        Une clé, un catalogue par langue :

        - `trans("clé")` dans le code ;
        - `{{ trans("clé") }}` dans les templates ;
        - `i18n:check` pour repérer les clés manquantes.

??? note "9. Repli, cache et intégration"

    Le repli est en cascade : locale demandée, puis locale de fallback, puis la clé elle-même.

    Les catalogues sont mis en cache ; après avoir édité un fichier de traduction, appelez `clear_translation_cache()` (ou redémarrez) pour le recharger.

    !!! note "Repli no-op du cœur"
        Le cœur fournit un `trans()` no-op (qui renvoie la clé) quand l'opt-in n'est pas installé (ADR-027).

        Un template qui utilise `trans()` fonctionne donc avec ou sans l'opt-in ; sans lui, il affiche les clés.

    !!! note "Configuration par le cœur"
        Les locales par défaut et de repli sont des réglages du cœur (`i18n_default_locale`, `i18n_fallback_locale`), pilotés par `set_default_locale` / `set_fallback_locale`.

    !!! note "Indépendance du cœur"
        Le cœur ne dépend pas de `forge-mvc-i18n` ; il l'expose seulement s'il est présent (mécanisme de loader, ADR-046).

## Voir aussi

- [Traduction (translator.py)](references/translator.md) : détail de `trans` et des locales.
- [Erreurs (exceptions.py)](references/exceptions.md) : `I18nError`, `TranslationCatalogError`.
- [Welcome-i18n](welcome/debutant/i18n-welcome.md) : apprendre l'opt-in pas à pas.
