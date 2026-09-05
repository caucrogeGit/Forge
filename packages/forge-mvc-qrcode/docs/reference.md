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

    Les bornes sont **basses** : `scale` vaut au moins 1, `border` au moins 0.

    !!! danger "Ne faites pas venir `scale` d'un paramètre de requête"
        Il n'y a pas de borne haute, et il n'y en aura pas : une affiche imprimée en grand format en demande légitimement une valeur élevée, si bien qu'un plafond choisi au hasard refuserait un usage réel.

        La conséquence est que `scale` reçu d'une requête laisse un visiteur commander la taille de l'image que votre serveur calcule.
        Posez-le dans le contrôleur, comme la cible du code.

    !!! warning "Entrées invalides"
        Un texte vide ou un `fmt` inconnu lève `QrCodeError` (sous-classe de `ValueError`).

        L'application doit décider quoi afficher dans ce cas (page d'erreur, valeur par défaut).

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-qrcode`.

        L'opt-in s'appuie sur `segno` (pur Python) et sur la classe `Response` du cœur, sans rien lui imposer.

??? note "12. Choisir le niveau de correction d'erreur"

    Le niveau existait sur `QrCode.from_text`, mais `QrCodeResponse.from_text` **ne le transmettait pas** (`QRCODE-ERROR-LEVEL-001`).

    Un contrôleur, c'est à dire le chemin documenté pour servir un QR Code, ne pouvait donc pas le choisir.

    ```python
    from forge_mvc_qrcode import QrCodeResponse

    return QrCodeResponse.from_text(url, error="h")
    ```

    | Niveau | Perte tolérée | Pour quoi |
    |---|---|---|
    | `l` | 7 % | écran, code lu de près |
    | `m` | 15 % | défaut |
    | `q` | 25 % | impression courante |
    | `h` | 30 % | étiquette, affiche, extérieur |

    !!! warning "Ce n'est pas un réglage de confort"
        Un code imprimé sur une étiquette ou une affiche, susceptible d'être rayé ou partiellement couvert, demande `h`.

        En `m`, il devient illisible dès qu'un coin manque, et la panne se découvre sur le terrain, une fois les étiquettes collées.

    Un niveau plus élevé produit un code plus dense, donc plus grand à surface égale : c'est le prix de la robustesse, et il se voit à la taille du fichier.

    `ERROR_LEVELS` est exporté : une application peut découvrir les valeurs valides sans lire la source du paquet.

??? note "13. Produire un fichier en ligne de commande"

    Le paquet savait produire un QR Code depuis du code Python et le servir en HTTP. Produire un fichier, pour une affiche, une étiquette ou une documentation, demandait d'écrire un script à usage unique (`QRCODE-CLI-001`).

    ```bash
    forge qrcode:make "https://forgemvc.com"
    forge qrcode:make "https://forgemvc.com" --out docs/qr.png --error h
    forge qrcode:make "https://forgemvc.com" --out docs/qr.svg --scale 8
    ```

    Sans `--out`, la commande affiche seulement la taille et les réglages retenus (charte §7).

    !!! danger "Un fichier existant n'est jamais écrasé"
        Deux QR Codes se ressemblent à l'œil : ce sont deux carrés noirs et blancs.

        Régénéré avec un autre contenu sous le même nom, l'ancien serait perdu sans que rien ne le signale, et personne ne s'en apercevrait avant qu'un scan mène au mauvais endroit.

    !!! warning "L'extension et le format doivent s'accorder"
        `--format svg --out code.png` est **refusé**.

        Un fichier SVG nommé `.png` est servi avec le mauvais type par un serveur web, et refusé par un imprimeur. Sans `--format`, le format se déduit de l'extension.

    !!! info "Le niveau par défaut est rappelé"
        Un fichier écrit sans `--error` explicite affiche un rappel : `m` tolère 15 % de perte, `h` en tolère 30 %.

        C'est le moment où l'information sert, pas trois semaines plus tard.

## Voir aussi

- [La génération (generator.py)](references/generator.md) : détail de `QrCode`.
- [La réponse HTTP (response.py)](references/response.md) : détail de `QrCodeResponse`.
- [Les erreurs (errors.py)](references/errors.md) : détail de `QrCodeError`.
- [Welcome-QR Code](welcome/debutant/qrcode-welcome.md) : parcours d'apprentissage.

## Deux cas concrets : le lien d'une séance, le badge d'un élève

Les exemples précédents encodent une URL reçue en paramètre.
C'est commode pour essayer, et ce n'est pas ce qu'on met en production.

!!! danger "Une route qui encode l'URL reçue encode celle d'un attaquant"
    `QrCodeResponse.from_text(request.query("url"))` produit, depuis **votre** domaine, un QR Code vers n'importe quelle destination.

    Un visiteur scanne un code servi par un site qu'il connaît et arrive ailleurs, sans jamais lire l'adresse : le QR Code est précisément le format où l'on ne vérifie pas où l'on va.

    Construisez la cible dans le contrôleur, depuis un identifiant interne.

### Le lien d'une séance

La cible est fabriquée côté serveur, l'identifiant seul vient de la route.

```python
from core.http.request import Request
from core.http.response import Response
from forge_mvc_qrcode import QrCodeResponse

BASE_PUBLIQUE = "https://lycee.exemple.fr"


class SeanceController:
    @staticmethod
    def qrcode(request: Request) -> Response:
        identifiant = request.route("id", default="")
        if not identifiant.isdigit():
            return Response(404, b"Seance inconnue", "text/plain; charset=utf-8")
        cible = f"{BASE_PUBLIQUE}/seance/rejoindre?id={identifiant}"
        return QrCodeResponse.from_text(
            cible,
            fmt="png",
            scale=6,
            error="h",
            headers={"Cache-Control": "public, max-age=3600"},
        )
```

Trois choix se lisent dans ce code.

| Choix | Pourquoi |
|---|---|
| L'identifiant est vérifié avant usage | Il entre dans une URL ; un contenu quelconque y ferait entrer autre chose |
| `error="h"` | Un code projeté ou imprimé est vu de travers et parfois masqué ; `h` tolère 30 % de perte, le défaut `m` en tolère 15 |
| `Cache-Control` | Le code d'une séance donnée ne change pas ; le régénérer à chaque affichage est du calcul pur |

### Le badge d'un élève

Un badge s'imprime, se glisse dans une pochette et se raye.

```python
class BadgeController:
    @staticmethod
    def qrcode(request: Request) -> Response:
        eleve = request.route("id", default="")
        if not eleve.isdigit():
            return Response(404, b"Eleve inconnu", "text/plain; charset=utf-8")
        return QrCodeResponse.from_text(
            f"{BASE_PUBLIQUE}/presence/pointer?eleve={eleve}",
            fmt="svg",
            scale=8,
            error="h",
        )
```

Le SVG est le bon format ici : il s'agrandit sans se pixeliser, ce que demande une impression.

!!! warning "Un QR Code n'est pas un secret"
    Il se lit par quiconque le photographie, et il ne s'agit là que d'un encodage.

    Ne mettez donc pas dans un badge ce qu'un élève ne doit pas pouvoir présenter à la place d'un autre : la route pointée fait l'authentification et l'autorisation, par exemple avec `forge-mvc-rbac`.

!!! note "La route reste écrite par vous"
    Forge affiche ce code, il ne l'installe pas (principe 9).

    Le câblage de la route suit la convention ordinaire, un fichier par contrôleur dans `mvc/routes/`.
