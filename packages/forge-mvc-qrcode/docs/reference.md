# Le QR Code dans Forge (forge-mvc-qrcode)

Ce document explique ce que fait l'opt-in `forge-mvc-qrcode`, ce qu'il expose, et comment on s'en sert dans un contrôleur.

`forge-mvc-qrcode` génère un QR Code PNG ou SVG depuis du texte ou une URL, et le sert via une réponse HTTP.

Le cœur de Forge ignore tout des QR Codes : ce paquet fournit l'API, l'application décide de ce qu'elle encode.

??? note "1. Rôle du module"

    Un QR Code encode une chaîne (un lien, un identifiant, un jeton) en une image lisible par un appareil photo.

    L'opt-in fait deux choses, et seulement deux :

    - **générer** l'image du QR Code (PNG binaire ou SVG texte) à partir d'une chaîne ;
    - **servir** cette image dans une réponse HTTP utilisable depuis un contrôleur.

    Il ne décide jamais de ce qui est encodé ni de la route : c'est le rôle de l'application.

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
    pip install --pre forge-mvc-qrcode
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-qrcode"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-qrcode`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-qrcode==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable qrcode --apply
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
    forge opt-in:disable qrcode
    pip uninstall forge-mvc-qrcode
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove qrcode` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    Cet opt-in n'expose aucune commande CLI : il s'utilise **par import** dans le code applicatif (voir l'API publique ci-dessous).

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-qrcode` |
    | Module | `forge_mvc_qrcode` |
    | Catégorie | Contenu (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc`, `segno` (pur Python, sans Pillow) |
    | API publique | `QrCode`, `QrCodeResponse`, `QrCodeError`, `PNG_MIME`, `SVG_MIME` |
    | Objet lié important | `Response` (réponse HTTP du cœur) |
    | Exception liée | `QrCodeError` si le texte est vide ou le format inconnu |
    | Décision d'architecture | ADR-050 |
    | Installation | `pip install --pre forge-mvc-qrcode` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les objets exposés et leurs liens.

    Le diagramme de séquence montre le déroulement d'une requête servant un QR Code.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que `QrCodeResponse` s'appuie sur `QrCode` pour produire une `Response` du cœur, et que les deux peuvent lever `QrCodeError`.

    ```mermaid
    classDiagram
        direction LR

        class QrCode {
            +str text
            +from_text(text, error) QrCode
            +to_png(scale, border) bytes
            +to_svg(scale, border) str
        }

        class QrCodeResponse {
            +from_text(text, fmt, scale, border, headers) Response
        }

        class QrCodeError {
            <<exception>>
        }

        class Response {
            +int status
            +body
            +str content_type
        }

        class Controller {
            +action(request) Response
        }

        QrCodeResponse --> QrCode : utilise
        QrCodeResponse --> Response : retourne
        QrCode ..> QrCodeError : peut lever
        QrCodeResponse ..> QrCodeError : peut lever
        Controller --> QrCodeResponse : appelle
        Controller --> Response : retourne

    ```

    À retenir :

    - `QrCode` est la fabrique d'images (PNG ou SVG) ;
    - `QrCodeResponse` enveloppe `QrCode` dans une `Response` HTTP ;
    - `QrCodeError` signale une entrée invalide ;
    - le contrôleur appelle `QrCodeResponse` et retourne la `Response`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre le parcours d'une requête qui affiche un QR Code.

    ```mermaid
    sequenceDiagram
        actor Navigateur
        participant Forge as Application Forge
        participant Controleur as Contrôleur
        participant QrResp as QrCodeResponse
        participant QrCode as QrCode
        participant Response as Response

        Navigateur->>Forge: GET /qrcode (requête HTTP)
        Forge->>Controleur: Appelle action(request)
        Controleur->>QrResp: from_text(texte, fmt)
        QrResp->>QrCode: from_text(texte) puis to_png/to_svg
        QrCode-->>QrResp: octets PNG ou texte SVG
        QrResp-->>Controleur: Response (image)
        Controleur-->>Forge: Retourne la Response
        Forge-->>Navigateur: Renvoie l'image du QR Code

    ```

    À retenir :

    - le contrôleur ne génère pas l'image lui-même : il délègue à `QrCodeResponse` ;
    - `QrCodeResponse` construit le `QrCode` puis l'encode dans le format demandé ;
    - la `Response` renvoyée porte le bon `Content-Type` (`image/png` ou `image/svg+xml`).

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `QrCode.from_text` | `from_text(text, *, error="m") -> QrCode` | construit un QR Code depuis une chaîne |
    | `QrCode.to_png` | `to_png(*, scale=4, border=4) -> bytes` | rend l'image PNG (octets) |
    | `QrCode.to_svg` | `to_svg(*, scale=4, border=4) -> str` | rend l'image SVG (texte) |
    | `QrCodeResponse.from_text` | `from_text(text, *, fmt="png", scale=4, border=4, headers=None) -> Response` | réponse HTTP servant le QR Code |
    | `QrCodeError` | exception (`ValueError`) | texte vide ou format inconnu |
    | `PNG_MIME` | `"image/png"` | type MIME du PNG |
    | `SVG_MIME` | `"image/svg+xml"` | type MIME du SVG |

    Le paramètre `error` règle le niveau de correction d'erreur (`"l"`, `"m"`, `"q"`, `"h"`).

    Le paramètre `fmt` vaut `"png"` (défaut) ou `"svg"`.

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Obtenir les octets PNG d'un QR Code | `QrCode.from_text(...).to_png()` |
    | Obtenir le SVG (texte) d'un QR Code | `QrCode.from_text(...).to_svg()` |
    | Servir un QR Code depuis un contrôleur | `QrCodeResponse.from_text(...)` |
    | Choisir PNG ou SVG | paramètre `fmt` de `QrCodeResponse.from_text` |
    | Ajuster la taille | paramètres `scale` et `border` |
    | Gérer une entrée invalide | intercepter `QrCodeError` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Générer un PNG

    ```python
    from forge_mvc_qrcode import QrCode

    qr = QrCode.from_text("https://forgemvc.com")
    png_bytes = qr.to_png(scale=6, border=2)
    ```

    ### 8.2 Servir un QR Code depuis un contrôleur

    ```python
    from core.http.request import Request
    from core.http.response import Response
    from forge_mvc_qrcode import QrCodeResponse


    def show(request: Request) -> Response:
        url = request.query("url", default="https://forgemvc.com")
        return QrCodeResponse.from_text(url, fmt="png")

    ```

    La réponse porte `Content-Type: image/png` et le navigateur affiche l'image.

    ### 8.3 Servir un SVG

    ```python
    def show_svg(request: Request) -> Response:
        return QrCodeResponse.from_text("https://forgemvc.com", fmt="svg")

    ```

    !!! tip "Aide-mémoire"
        Deux classes, deux usages :

        - `QrCode` quand vous voulez les octets ou le texte de l'image ;
        - `QrCodeResponse` quand vous voulez une réponse HTTP prête à retourner.

??? note "11. Options et erreurs"

    Les paramètres `scale` (taille d'un module) et `border` (marge) contrôlent le rendu.

    Des valeurs hors bornes lèvent `QrCodeError` plutôt que de produire une image illisible.

    !!! warning "Entrées invalides"
        Un texte vide ou un `fmt` inconnu lève `QrCodeError` (sous-classe de `ValueError`).

        L'application doit décider quoi afficher dans ce cas (page d'erreur, valeur par défaut).

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-qrcode`.

        L'opt-in s'appuie sur `segno` (pur Python) et sur la classe `Response` du cœur, sans rien lui imposer.

## Voir aussi

- [La génération (generator.py)](references/generator.md) : détail de `QrCode`.
- [La réponse HTTP (response.py)](references/response.md) : détail de `QrCodeResponse`.
- [Les erreurs (errors.py)](references/errors.md) : détail de `QrCodeError`.
- [Welcome-QR Code](welcome/debutant/qrcode-welcome.md) : parcours d'apprentissage.
