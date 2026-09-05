# L'internationalisation dans Forge (forge-mvc-i18n)

Ce document explique ce que fait l'opt-in `forge-mvc-i18n`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-i18n` traduit des chaînes via des catalogues JSON (`translations/<locale>.json`), avec une locale par défaut, une locale de repli, et un helper `trans()` utilisable dans le code et les templates.

Extrait du cœur (ADR-027), il s'active dès qu'il est installé : le renderer Jinja du cœur expose alors `trans()` aux templates.

??? note "1. Rôle du module"

    Une application multilingue a besoin de sortir le texte du code et de le ranger par langue.

    L'opt-in stocke les traductions dans des **catalogues JSON** (un fichier par locale) et fournit `trans("clé")` pour récupérer la bonne chaîne selon la locale courante.

    Quand une clé manque dans la locale demandée, il bascule sur la **locale de repli** ; si elle manque toujours, il renvoie la clé elle-même (jamais une erreur d'affichage).

??? note "2. Installation"

    !!! warning "Prérequis : activez le venv du projet"

        Quelle que soit la source, installez **dans le venv du projet** :

        ```bash
        source .venv/bin/activate
        ```

        Lancé hors d'un venv, `pip` vise le Python **système** (Debian 12+, Ubuntu 23.04+),
        protégé par PEP 668. Il refuse alors d'installer, pour ne pas écraser les paquets
        gérés par `apt`, et affiche `externally-managed-environment`.
        Le venv de projet créé par `forge new` n'a pas ce verrou.

    #### Installer le paquet

    <div class="canal">

    #### A. Depuis PyPI (stable)

    La dernière version publiée :

    ```bash
    pip install --pre forge-mvc-i18n
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-i18n"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-i18n`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-i18n==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable i18n --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Rien à faire : cet opt-in n'apporte aucune table.

    #### 4. Le brancher là où il agit

    Il s'importe dans le code qui s'en sert. Il n'y a ni route à monter ni middleware
    à poser.

    #### 5. Le prouver

    ```bash
    make check
    forge doctor
    ```

    Puis un premier usage réel.
    Un opt-in installé, inscrit et provisionné qu'aucun code n'appelle n'est pas
    opérationnel : il est seulement présent.


??? note "4. Désinstallation"

    ```bash
    forge opt-in:disable i18n
    pip uninstall forge-mvc-i18n
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove i18n` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-i18n` ajoute ces commandes (le noyau garde un repli no-op, ADR-027) :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `i18n:init` | Initialise les fichiers de traduction. | `forge i18n:init` |
    | `i18n:check` | Vérifie la complétude des traductions entre locales. | `forge i18n:check` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-i18n` |
    | Module | `forge_mvc_i18n` |
    | Catégorie | Internationalisation (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` |
    | API publique | `trans`, `load_catalog`, `get_default_locale`, `set_default_locale`, `get_fallback_locale`, `set_fallback_locale`, `clear_translation_cache`, `detect_locale`, `available_locales`, `parse_accept_language`, `negotiate_locale` |
    | Catalogues | `translations/<locale>.json` |
    | Configuration | `i18n_default_locale`, `i18n_fallback_locale` (cœur) |
    | Helper Jinja | `trans()` exposé aux templates (ADR-046) |
    | Commandes | `i18n:init`, `i18n:check` |
    | Exceptions | `I18nError`, `TranslationCatalogError` |
    | Décision d'architecture | ADR-027 (extraction, repli no-op du cœur) |
    | Installation | `pip install --pre forge-mvc-i18n` |

??? note "7. Schémas UML"

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

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `trans` | `trans(key, locale=None, translations_dir="translations") -> str` | traduit une clé |
    | `load_catalog` | `load_catalog(locale, translations_dir="translations") -> dict[str, str]` | charge un catalogue (caché) |
    | `get_default_locale` | `get_default_locale() -> str` | locale par défaut |
    | `set_default_locale` | `set_default_locale(locale) -> None` | fixe la locale par défaut |
    | `get_fallback_locale` | `get_fallback_locale() -> str \| None` | locale de repli |
    | `set_fallback_locale` | `set_fallback_locale(locale) -> None` | fixe la locale de repli |
    | `clear_translation_cache` | `clear_translation_cache() -> None` | vide le cache des catalogues |
    | `detect_locale` | `detect_locale(*, session_locale=None, accept_language=None, available=None, default=None) -> str \| None` | locale active, session puis en-tête puis défaut |
    | `available_locales` | `available_locales(translations_dir="translations") -> list[str]` | locales ayant un catalogue, liste blanche de la négociation |
    | `parse_accept_language` | `parse_accept_language(header) -> list[str]` | locales de l'en-tête, triées par facteur de qualité |
    | `negotiate_locale` | `negotiate_locale(voulues, disponibles) -> str \| None` | première voulue qu'on sait servir |
    | `SESSION_KEY_LOCALE` | constante | clé de session portant le choix de l'utilisateur |
    | `I18nError`, `TranslationCatalogError` | exceptions | erreurs (locale invalide, catalogue illisible) |

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Traduire une clé (code) | `trans("clé")` |
    | Traduire dans un template | `{{ trans("clé") }}` |
    | Forcer une locale | `trans("clé", locale="en")` |
    | Choisir la langue par défaut | `set_default_locale("fr")` |
    | Définir le repli | `set_fallback_locale("en")` |
    | Vérifier les manques | `forge i18n:check` |
    | Recharger après édition | `clear_translation_cache()` |
    | Savoir quelle langue servir | `detect_locale(...)` |
    | Connaître les langues servables | `available_locales()` |

??? note "9 bis. D'où vient la locale active"

    Le paquet annonçait « locale et fallback » sans savoir d'où venait la locale.
    `trans()` retombait sur une valeur **globale**, la même pour tous les visiteurs, et une application multilingue devait écrire sa propre détection (`I18N-LOCALE-DETECTION-001`).

    L'ordre va du plus intentionnel au plus supposé.

    | Rang | Source | Pourquoi ce rang |
    |---|---|---|
    | 1 | Choix en session | un geste de l'utilisateur, explicite |
    | 2 | En-tête `Accept-Language` | une préférence du navigateur |
    | 3 | Locale par défaut | la configuration de l'application |

    ```python
    from forge_mvc_i18n import SESSION_KEY_LOCALE, available_locales, detect_locale, trans

    locale = detect_locale(
        session_locale=session.get(SESSION_KEY_LOCALE),
        accept_language=request.header("Accept-Language"),
        available=available_locales(),
        default="fr",
    )
    titre = trans("page.title", locale)
    ```

    Pour enregistrer un choix, l'application écrit la clé en session.

    ```python
    session[SESSION_KEY_LOCALE] = "en"
    ```

    !!! warning "La liste blanche n'est pas facultative"
        `available` borne les deux premières sources, qui viennent du client.

        Sans elle, elles sont refusées et le défaut est rendu.
        Un `Accept-Language` forgé ferait sinon chercher un catalogue arbitraire, et cet en-tête n'est pas de confiance.

    !!! info "Une région retombe sur sa base, jamais l'inverse"
        `fr-FR` est servi par `fr` quand seul `fr` a un catalogue : un navigateur annonce presque toujours une région, et exiger l'exactitude ne servirait jamais personne.

        `fr` ne choisit pas `fr-CA` pour autant.
        Servir une variante régionale que personne n'a demandée serait une supposition, pas une négociation.

    !!! info "Rien ne se détecte tout seul"
        `trans()` ne change pas de comportement, et l'application appelle `detect_locale` puis passe le résultat.

        Un helper qui lirait la requête à l'insu de l'appelant serait de la magie cachée, que le principe 3 refuse.
        Les fonctions prennent des valeurs simples, jamais une requête HTTP, et se testent sans monter de serveur.

??? note "10. Exemples d'utilisation"

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

??? note "11. Repli, cache et intégration"

    Le repli est en cascade : locale demandée, puis locale de fallback, puis la clé elle-même.

    Les catalogues sont mis en cache ; après avoir édité un fichier de traduction, appelez `clear_translation_cache()` (ou redémarrez) pour le recharger.

    !!! note "Repli no-op du cœur"
        Le cœur fournit un `trans()` no-op (qui renvoie la clé) quand l'opt-in n'est pas installé (ADR-027).

        Un template qui utilise `trans()` fonctionne donc avec ou sans l'opt-in ; sans lui, il affiche les clés.

    !!! note "Configuration par le cœur"
        Les locales par défaut et de repli sont des réglages du cœur (`i18n_default_locale`, `i18n_fallback_locale`), pilotés par `set_default_locale` / `set_fallback_locale`.

    !!! note "Indépendance du cœur"
        Le cœur ne dépend pas de `forge-mvc-i18n` ; il l'expose seulement s'il est présent (mécanisme de loader, ADR-046).

??? note "12. Voir les clés manquantes avant l'utilisateur"

    `trans()` rend la clé elle même quand la traduction manque, et c'est le bon comportement : une page ne doit pas casser pour une traduction absente (`I18N-MISSING-KEYS-DEV-001`).

    Mais **rien ne le signalait**. On ajoute `{{ trans("panier_vide") }}` dans une page, on oublie de l'ajouter au catalogue, et la page affiche « panier_vide » à l'utilisateur.

    ```python
    from forge_mvc_i18n import clear_missing_keys, missing_keys

    missing_keys()        # (("fr", "panier_vide"), ...)
    ```

    !!! info "Hors production seulement"
        Journaliser chaque clé manquante à chaque requête noierait le journal, et une traduction absente n'est pas un incident d'exploitation.

        C'est un défaut à corriger au développement, et c'est là qu'il doit se voir. En production, la clé est rendue en silence, comme avant.

    !!! info "Une clé n'est signalée qu'une fois"
        La même clé manquante sur mille requêtes est un seul défaut.

        L'accumuler mille fois ferait grossir la mémoire d'un processus de développement sans rien apprendre de plus.

    !!! warning "Le signalement ne lève jamais"
        Une page qui casse parce qu'il manque une traduction serait un remède pire que le mal, y compris en développement, où elle empêcherait de voir le reste de la page.

    `missing_keys()` sert aussi à un test qui refuse de livrer avec des traductions manquantes.

??? note "13. Lister les clés employées dans les gabarits"

    `i18n:check` compare deux catalogues entre eux : il dit quelle clé du français manque à l'anglais (`I18N-EXTRACT-CLI-001`).

    Il ne peut rien dire d'une clé employée dans un gabarit et absente **des deux**, puisqu'il ne lit que les catalogues. C'est pourtant le cas le plus fréquent.

    ```bash
    forge i18n:extract
    forge i18n:extract --locale en
    ```

    La commande balaye `mvc/views/`, relève les appels à `trans()` et les compare au catalogue. Une clé employée et absente fait échouer la commande ; une clé du catalogue non trouvée dans les gabarits est signalée sans être une erreur, puisqu'elle peut servir à un appel calculé.

    !!! warning "Seules les clés littérales sont extraites"
        `trans(variable)` et `trans("prefixe_" ~ suffixe)` ne peuvent pas être lus : la clé n'existe qu'à l'exécution.

        Ces appels sont **comptés et rapportés** à part, et la sortie annonce alors que la liste est un minorant. Le prétendre exhaustive donnerait une fausse assurance.

    L'extraction elle même vit dans l'opt-in (`extract.py`, `extract_from_directory`, `extract_from_text`, `ExtractionResult`), qui seul connaît la forme des appels. La commande l'importe paresseusement : le cœur ne dépend pas d'un opt-in (ADR-004).

??? note "14. Singulier et pluriel"

    `trans()` rend une chaîne unique par clé (`I18N-PLURALS-001`). Afficher « 1 articles », ou écrire deux clés avec un `if` dans chaque gabarit, sont les deux contournements qu'on rencontre, et aucun ne tient quand une troisième langue arrive.

    ```json
    {"articles": {"one": "{n} article", "other": "{n} articles"}}
    ```

    ```python
    from forge_mvc_i18n import trans

    trans("articles", "fr", count=compte).format(n=compte)
    ```

    Une clé dont la valeur est une chaîne reste une clé ordinaire : le format existant continue de fonctionner sans changement, et `count` y est sans effet.
    Vous pouvez donc écrire l'appel pluralisé sans savoir si la clé l'est encore.

    !!! danger "Ce catalogue était refusé au chargement"
        Cette page montrait déjà ce JSON, et un appel `select_plural(catalogue["articles"], ...)`.

        Le chargeur refusait pourtant toute valeur qui n'était pas une chaîne, et `trans` n'avait pas de `count` : la valeur que `select_plural` attendait ne pouvait pas venir d'un catalogue, et le pluriel n'était joignable qu'en construisant le dictionnaire à la main (`I18N-PLURAL-CATALOG-REACHABLE-001`).

    !!! info "Le texte n'est pas formaté pour vous"
        `trans` choisit la forme, il ne substitue rien : le `.format(n=compte)` de l'exemple est à vous.

        Ce module n'a jamais formaté, et le faire ici casserait toute traduction contenant une accolade littérale.

    !!! danger "Forge implémente deux formes, CLDR en définit six"
        `one` et `other`, avec une règle par famille de langues. C'est exact pour le français, l'anglais et la plupart des langues d'Europe occidentale.

        C'est **faux** pour le russe, l'arabe, le polonais et le gallois, et `plural_form` **lève** pour ces langues plutôt que de rendre une forme qu'elle sait fausse.

        Ce n'est pas un choix par facilité : une implémentation partielle de CLDR donnerait l'impression de couvrir une langue qu'elle massacre. Une application qui doit traduire vers l'une d'elles emploie une bibliothèque d'internationalisation complète.

    !!! info "Le français met zéro au singulier"
        « 0 article » en français, « 0 articles » en anglais.

        La règle dépend de la langue et jamais de la région : le français de Belgique et celui de France comptent pareil.

    !!! warning "Une forme absente est refusée au chargement"
        Retomber sur l'autre forme afficherait « 3 article » sans que rien ne le signale.

        Le refus tombe au chargement du catalogue, et non à la requête qui porte le nombre manquant : sans cela, la page marche pour un article et casse pour deux.

        `forge i18n:check` applique le même contrôle avant l'exécution.

## Voir aussi

- [Traduction (translator.py)](references/translator.md) : détail de `trans` et des locales.
- [Erreurs (exceptions.py)](references/exceptions.md) : `I18nError`, `TranslationCatalogError`.
- [Welcome-i18n](welcome/debutant/i18n-welcome.md) : parcours d'apprentissage.
