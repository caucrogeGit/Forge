# L'authentification multi-facteurs dans Forge (forge-mvc-mfa)

Ce document explique ce que fait l'opt-in `forge-mvc-mfa`, ce qu'il expose, et comment on s'en sert.

!!! note "Module extrait"
    Le code MFA a été extrait du cœur vers le paquet `forge-mvc-mfa` ; le cœur Forge n'en dépend pas.

!!! info "Statut : Beta"
    `forge-mvc-mfa` est en **Beta** (`Development Status :: 4 - Beta`), publié sur PyPI depuis `1.0.0-beta.9` (`MFA-PYPI-READY-001`).
    Le secret TOTP est chiffré au repos via Fernet (`SEC-MFA-SECRET-ENCRYPTION-001`).

`forge-mvc-mfa` ajoute un second facteur d'authentification : TOTP (application d'authentification), codes de récupération, challenge à la connexion, revalidation et protections (anti-rejeu, rate-limit).

Le secret TOTP est **chiffré au repos** (Fernet) ; l'application décide où persister les facteurs et quand exiger le second facteur.

!!! warning "Clé de chiffrement obligatoire"
    Le secret TOTP est chiffré avec `FORGE_MFA_SECRET_KEY` (Fernet).

    Démarrer sans cette variable lève `MfaSecretKeyMissing` : le chiffrement n'est pas optionnel.

??? note "1. Rôle du module"

    Le mot de passe seul ne suffit pas pour les actions sensibles.
    L'opt-in ajoute un **second facteur**.

    Il couvre quatre temps :

    - **enrôlement** : générer un secret TOTP, l'afficher en QR Code, confirmer le premier code ;
    - **challenge** : après le mot de passe, exiger un code TOTP avant d'ouvrir la session ;
    - **revalidation** : redemander le facteur avant une action critique (step-up) ;
    - **récupération** : des codes à usage unique si l'appareil TOTP est perdu.

    Forge fournit les helpers et les contrats ; la **persistance** des facteurs et des codes reste applicative (ADR-008).

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
    pip install --pre forge-mvc-mfa
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-mfa"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-mfa`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-mfa==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable mfa --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    Rien à faire dans le cas courant.
    Cet opt-in n'apporte aucune table, la persistance des facteurs appartenant à l'application.

    Une seule exception, si vous servez l'authentification par **plusieurs workers** et voulez
    un anti-rejeu TOTP commun à tous.
    Le registre partagé, décrit plus bas, s'appuie alors sur une table.

    ```bash
    forge mfa:init          # écrit la migration dans mvc/migrations/, sans l'exécuter
    forge migration:apply   # après relecture
    ```

    La déclaration de cette table vit dans `tables.py`, rendue pour le backend installé.

    #### 4. Le brancher là où il agit

    Il se branche dans `app.py`, là où l'application compose ses middlewares et ses
    fournisseurs de contexte. Ce câblage vous appartient : Forge ne l'écrit jamais à
    votre place (principe 9).

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
    forge opt-in:disable mfa
    pip uninstall forge-mvc-mfa
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre, sans toucher au paquet.
    `forge opt-in:remove mfa` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    Cet opt-in n'expose aucune commande CLI : il s'utilise **par import** dans le code applicatif (voir l'API publique ci-dessous).

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-mfa` |
    | Module | `forge_mvc_mfa` |
    | Catégorie | Sécurité et accès (ADR-055) |
    | Couche | opt-in (brique optionnelle), transversal au flux d'auth |
    | Dépend de | `forge-mvc`, `pyotp`, `cryptography` (Fernet) |
    | Facteurs | TOTP (`MFA_FACTOR_TOTP`), codes de récupération (`MFA_FACTOR_RECOVERY`) |
    | Chiffrement | secret TOTP chiffré (Fernet), clé `FORGE_MFA_SECRET_KEY` |
    | Protections | anti-rejeu TOTP, rate-limit du challenge et de la revalidation |
    | API publique | enrôlement, challenge, revalidation, codes de récupération, chiffrement |
    | Persistance | applicative (ADR-008) : `AuthMfaFactor`, codes de récupération |
    | Installation | `pip install --pre forge-mvc-mfa` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les groupes d'API et le secret chiffré.

    Le diagramme de séquence montre le challenge MFA à la connexion.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre les fonctions groupées par rôle, le facteur persisté et le chiffrement du secret.

    ```mermaid
    classDiagram
        direction LR

        class enrolment {
            <<module>>
            +generate_totp_secret() str
            +create_totp_factor(...)
            +confirm_totp_factor(...) AuthMfaFactor
            +totp_provisioning_uri(...) str
            +verify_totp_code(...)
        }

        class challenge {
            <<module>>
            +start_mfa_challenge(...)
            +verify_mfa_challenge(...)
            +require_recent_mfa(...)
            +verify_mfa_revalidation(...)
        }

        class recovery {
            <<module>>
            +create_recovery_codes(...)
            +consume_recovery_code(...)
        }

        class secret_crypto {
            <<module>>
            +encrypt_totp_secret(...)
            +decrypt_totp_secret(...)
            +validate_mfa_secret_key_config()
        }

        class AuthMfaFactor {
            <<dataclass>>
            +user_id
            +type
            +status
            +secret_chiffré
        }

        enrolment --> AuthMfaFactor : produit
        enrolment --> secret_crypto : chiffre le secret
        challenge --> AuthMfaFactor : vérifie
        recovery --> AuthMfaFactor : alternative TOTP

    ```

    À retenir :

    - l'enrôlement produit un `AuthMfaFactor` (secret chiffré) ;
    - le challenge vérifie un code TOTP ou un code de récupération ;
    - la revalidation rejoue le facteur avant une action critique ;
    - le secret n'est jamais stocké en clair (Fernet).

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre le challenge à la connexion, après le mot de passe.

    ```mermaid
    sequenceDiagram
        actor Utilisateur
        participant Login as Contrôleur login
        participant MFA as forge_mvc_mfa
        participant Session as Session

        Utilisateur->>Login: identifiants (mot de passe OK)
        Login->>MFA: is_mfa_enabled(user) ?
        alt MFA actif
            Login->>MFA: start_mfa_challenge(user)
            Login-->>Utilisateur: demande le code TOTP
            Utilisateur->>Login: code à 6 chiffres
            Login->>MFA: verify_mfa_challenge(code)
            MFA-->>Login: succès (ou code de récupération)
            Login->>Session: ouvre la session
        else MFA inactif
            Login->>Session: ouvre la session directement
        end

    ```

    À retenir :

    - le challenge intervient **après** la vérification du mot de passe ;
    - la session n'est ouverte qu'une fois le second facteur validé ;
    - un code de récupération est une alternative au code TOTP ;
    - le challenge est limité en tentatives et en durée (anti-bruteforce).

??? note "8. API publique"

    ### Secret et chiffrement

    | Élément | Rôle |
    |---|---|
    | `generate_totp_secret() -> str` | génère un secret TOTP |
    | `encrypt_totp_secret` / `decrypt_totp_secret` | chiffre/déchiffre le secret (Fernet) |
    | `validate_mfa_secret_key_config() -> None` | vérifie `FORGE_MFA_SECRET_KEY` au démarrage |

    ### Enrôlement TOTP

    | Élément | Rôle |
    |---|---|
    | `create_totp_factor(...)` | crée un facteur TOTP en attente |
    | `confirm_totp_factor(...) -> AuthMfaFactor` | confirme avec le premier code |
    | `totp_provisioning_uri(...) -> str` | URI `otpauth://` (pour QR Code) |
    | `verify_totp_code(...)` | vérifie un code TOTP |
    | `TotpSetup`, `AuthMfaFactor` | données d'enrôlement et facteur |

    ### Challenge et revalidation

    | Élément | Rôle |
    |---|---|
    | `start_mfa_challenge(...)` | démarre le challenge (état en session) |
    | `verify_mfa_challenge(...)` | vérifie le code du challenge |
    | `has_pending_mfa_challenge`, `clear_mfa_challenge` | état du challenge |
    | `require_recent_mfa(...)` | exige une revalidation récente (step-up) |
    | `mark_mfa_revalidated`, `verify_mfa_revalidation` | revalidation |

    ### Codes de récupération

    | Élément | Rôle |
    |---|---|
    | `create_recovery_codes(...)` | génère des codes à usage unique |
    | `consume_recovery_code(...)` | consomme un code (irréversible) |

    ### Constantes

    `MFA_FACTOR_TOTP`, `MFA_FACTOR_RECOVERY`, `MFA_STATUS_ACTIVE` / `PENDING` / `DISABLED`, fenêtres et tentatives du challenge et de la revalidation.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Vérifier la clé au démarrage | `validate_mfa_secret_key_config()` |
    | Enrôler un utilisateur | `create_totp_factor` + `totp_provisioning_uri` + `confirm_totp_factor` |
    | Exiger le 2e facteur au login | `start_mfa_challenge` + `verify_mfa_challenge` |
    | Protéger une action sensible | `require_recent_mfa(...)` |
    | Fournir un secours | `create_recovery_codes` / `consume_recovery_code` |

??? note "10. Exemple : challenge à la connexion"

    ```python
    from forge_mvc_mfa import (
        is_mfa_enabled, start_mfa_challenge, verify_mfa_challenge,

    )

    # Après vérification du mot de passe. `factors` vient de votre stockage :
    # c'est la liste des facteurs MFA de cet utilisateur.
    if is_mfa_enabled(factors):
        start_mfa_challenge(request, user)
        return redirect("/login/mfa")     # demander le code TOTP

    else:
        open_session(request, user)       # pas de MFA : session directe

    # Sur la page de saisie du code :
    if verify_mfa_challenge(request, request.form("code"), factors):
        open_session(request, user)

    else:
        return Response.text("Code invalide", status=401)

    ```

    `factors` est demandé partout où la décision en dépend, plutôt que rechargé en interne : Forge ne va pas chercher vos données à votre place, et le SQL de leur lecture reste chez vous (principe 5).

    !!! tip "Aide-mémoire"
        Quatre temps, une clé de chiffrement :

        - enrôler (secret + QR + confirmation) ;
        - challenger au login ;
        - revalider avant le sensible ;
        - récupérer via codes à usage unique.

??? note "11. Sécurité des secrets"

    Le secret TOTP est chiffré au repos avec Fernet (`cryptography`) et la clé `FORGE_MFA_SECRET_KEY` ; il n'est jamais stocké en clair.

    Appelez `validate_mfa_secret_key_config()` au démarrage (app.py / wsgi.py) : démarrer sans clé valide échoue tôt plutôt qu'à la première écriture.

    !!! warning "Codes de récupération à usage unique"
        Les codes de récupération sont stockés **hachés** et consommés une seule fois (`consume_recovery_code`).

        Présentez-les une fois à l'utilisateur à la génération ; ils ne sont pas réaffichables.

    !!! warning "Anti-rejeu et rate-limit"
        Un code TOTP déjà utilisé est refusé (anti-rejeu) ; le challenge et la revalidation sont limités en tentatives et en fenêtre temporelle.

        Ces protections sont actives par défaut.

    !!! danger "Par défaut, l'anti-rejeu vaut par processus, pas par application"
        Le registre des codes déjà utilisés vit en mémoire du processus.
        Derrière un serveur à plusieurs workers, gunicorn typiquement, chaque worker a le sien.
        Un même code TOTP peut donc être accepté une fois par worker, soit jusqu'à autant de fois qu'il y a de workers.

        La fenêtre est courte, un code TOTP vivant trente secondes, et l'attaquant doit déjà détenir le code.
        Le rate-limit du challenge borne par ailleurs le nombre de tentatives.
        Le risque réel est donc le rejeu d'un code intercepté, pas la découverte d'un code.

        Trois remèdes, au choix de l'exploitant.

        - Servir l'authentification par un seul worker, ce qui suffit à beaucoup d'applications.
        - Installer le registre partagé livré par Forge, voir le paragraphe suivant.
        - Porter le registre dans un magasin partagé de votre cru, en écrivant une classe conforme au protocole `TotpReplayStore`.

        Le registre n'est pas non plus persisté : un redémarrage l'oublie, avec la même fenêtre de moins de trente secondes.

    !!! tip "Partager le registre entre tous les processus"
        Forge livre `DbTotpReplayStore`, adossé au backend BDD du projet, donc commun à tous les workers.
        Il ne s'active pas tout seul, l'application le pose au démarrage en une ligne visible.

        ```python
        from forge_mvc_mfa import set_replay_store
        from forge_mvc_mfa.replay_store_db import DbTotpReplayStore

        set_replay_store(DbTotpReplayStore())
        ```

        La table se provisionne comme celle de tout opt-in adossé à la base.

        ```bash
        forge mfa:init          # écrit la migration dans mvc/migrations/, sans l'exécuter
        forge migration:apply   # après relecture
        ```

        Cette table n'est requise que si vous installez ce registre.
        Un projet qui garde le défaut n'a aucune table à créer, `forge-mvc-mfa` restant une bibliothèque sans persistance.

        Le coût est d'une écriture par validation de code.
        En contrepartie la garantie devient exacte, y compris entre processus, et elle n'exige ni Redis ni aucune dépendance nouvelle.

    !!! note "Persistance applicative"
        Forge fournit les helpers et les contrats (`AuthMfaFactor`, codes) ; l'application choisit la persistance (table, schéma), cohérent avec ADR-008.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-mfa` : la dépendance va de l'opt-in vers le cœur.

??? note "12. Politique de stockage des secrets MFA"

    ### Statut actuel

    `forge-mvc-mfa` est en Beta.
    Le secret TOTP est **chiffré au repos** via Fernet (bibliothèque `cryptography`).

    Le module est opt-in, non inclus dans `forge-mvc[all]`, et doit être configuré avec `FORGE_MFA_SECRET_KEY` avant tout déploiement.

    ### Développement et tests

    En développement et en environnement de test isolé :

    - le secret TOTP est chiffré dans `auth_mfa_factors.totp_secret` (Fernet, préfixe `enc:`) ;
    - la clé de chiffrement est lue depuis `FORGE_MFA_SECRET_KEY`, requise même en dev ;
    - les codes de récupération sont stockés sous forme hashée (`hash_recovery_code()`, SHA-256 + `secrets.compare_digest`).

    **Conditions requises même en développement :**

    - `FORGE_MFA_SECRET_KEY` positionné dans l'environnement ;
    - accès à la table `auth_mfa_factors` limité à l'utilisateur applicatif ;
    - secrets jamais loggés (`totp_secret` et `recovery_code` sont dans les champs redactés de `sanitize_auth_audit_metadata()`) ;
    - base de données non exposée publiquement.

    ### Production

    Le module est en Beta.
    Le chiffrement Fernet est en place (depuis `SEC-MFA-SECRET-ENCRYPTION-001`).
    Certaines exigences avancées (rotation de clé, sauvegarde/restauration, revue sécurité formelle) restent à la charge de l'application avant un usage critique.

    **Protection additionnelle recommandée en production :**

    - restreindre les droits d'accès à la table `auth_mfa_factors` au strict minimum applicatif ;
    - stocker `FORGE_MFA_SECRET_KEY` dans un gestionnaire de secrets (Vault, AWS Secrets Manager…) ;
    - appeler `validate_mfa_secret_key_config()` au démarrage applicatif (cf. section 7) ;
    - chiffrement du disque de la base de données ;
    - ne pas exporter `auth_mfa_factors` dans des dumps non chiffrés ;
    - documenter la procédure de rotation et de sauvegarde/restauration de la clé.

    ### Secrets TOTP

    Le secret TOTP est une clé partagée utilisée pour calculer les codes TOTP (RFC 6238).

    **Pourquoi on ne peut pas simplement hasher le secret TOTP :**

    Un hash est à sens unique.
    Pour vérifier un code TOTP, le serveur doit pouvoir recalculer `TOTP(secret, timestamp)`.
    Si le secret est hashé, cette opération est impossible.

    Le stockage production-ready d'un secret TOTP nécessite :

    - un **chiffrement applicatif réversible** (AES-256-GCM ou équivalent avec clé de chiffrement séparée), **ou**
    - un **HSM** (*Hardware Security Module*), **ou**
    - un **gestionnaire de secrets** (Vault, AWS Secrets Manager, ou équivalent).

    Depuis `SEC-MFA-SECRET-ENCRYPTION-001`, `forge-mvc-mfa` implémente le chiffrement Fernet (`cryptography.fernet.Fernet`, AES-128-CBC + HMAC-SHA256) via la clé `FORGE_MFA_SECRET_KEY`.
    Les valeurs stockées en base sont préfixées `enc:` pour distinguer les secrets chiffrés d'éventuelles valeurs legacy.

    Pour renforcer davantage, coupler `FORGE_MFA_SECRET_KEY` à un gestionnaire de secrets externe.

    ### Codes de récupération

    Les codes de récupération sont correctement protégés dans `forge-mvc-mfa` (série `1.0.0-beta.x`) :

    - générés via `secrets.choice()` sur un alphabet sans ambiguïté ;
    - hashés avant stockage via `hash_recovery_code()` (SHA-256) ;
    - vérifiés via `secrets.compare_digest()` (résistant aux timing attacks) ;
    - stockés en base uniquement sous forme de hash : le code brut n'est jamais persisté.

    **Cette conception est conforme pour la production**, à condition que la base elle-même soit protégée.
    Un hash de code de récupération exposé ne permet pas de retrouver le code brut.

    ### Exigences avant production-ready

    `forge-mvc-mfa` est en **Beta** (publié sur PyPI depuis `1.0.0-beta.9`).
    Avant un usage en production critique, l'application doit couvrir les exigences suivantes :

    1. ~~**Chiffrement applicatif des secrets TOTP**~~ ✓ livré (`SEC-MFA-SECRET-ENCRYPTION-001`) : Fernet + `FORGE_MFA_SECRET_KEY`.
    2. **Politique de rotation documentée** : rotation ou invalidation maîtrisée des secrets compromis.
    3. **Documentation de sauvegarde/restauration** : procédure en cas de perte de la clé de chiffrement.
    4. ~~**Tests dédiés au stockage chiffré**~~ ✓ livré (`SEC-MFA-SECRET-ENCRYPTION-001`) : `tests/test_mfa_secret_crypto.py`.
    5. **Revue sécurité explicite** : validation que le stockage chiffré est correct.
    6. ~~**Décision explicite de changement de statut**~~ ✓ livré (`MFA-PYPI-READY-001`).
    7. ~~**Publication PyPI**~~ ✓ livré en `1.0.0-beta.9`.
    8. ~~**Passage en Beta**~~ ✓ acté (tous les opt-ins en Beta).

    ### Tickets liés

    | Ticket | Description | État |
    |---|---|---|
    | `MFA-SECRET-STORAGE-POLICY-001` | Documenter la politique de stockage | livré |
    | `SEC-MFA-SECRET-ENCRYPTION-001` | Chiffrement applicatif du secret TOTP (Fernet) | livré |
    | `MFA-PYPI-READY-001` | Requalification Alpha (Pre-Alpha → Alpha) | livré |

## Voir aussi

- [Cœur MFA (mfa.py)](references/mfa.md) : enrôlement, challenge, revalidation.
- [Codes de récupération (recovery.py)](references/recovery.md) : génération et consommation.
- [Chiffrement des secrets (secret_crypto.py)](references/secret_crypto.md) : Fernet, `FORGE_MFA_SECRET_KEY`.
- [Protection anti-rejeu (totp_replay.py)](references/totp_replay.md).
- [Welcome-MFA](welcome/debutant/mfa-welcome.md) : parcours d'apprentissage.
