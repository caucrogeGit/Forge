# Oscilloscope (JavaScript local)

**Objectif**{ .intro-label } : construire un outil temps réel avec du JavaScript **local**, sans CDN, sous CSP stricte.

**Ce que vous allez apprendre :**{ .intro-label } servir un module JavaScript depuis `static/js/`, le charger via `{% block scripts %}`, et lui passer des données par des attributs `data-*` plutôt que par un script inline.

L'oscilloscope dessine une sinusoïde animée sur un canvas, pilotée par deux curseurs (fréquence, amplitude).
C'est un cas typique de la famille temps réel : le SSR seul ne suffit pas, un peu de JavaScript est légitime.
La règle reste stricte : le JavaScript est local, servi depuis `'self'`, jamais depuis un CDN.

??? note "Documentations"
    Pour bien comprendre ce palier :

    | Document | Ce qu'il apporte |
    |---|---|
    | [Outils interactifs](../../features/outils-interactifs.md) | le motif JavaScript-live et ses contraintes |
    | [Front et CSS](../../features/front.md) | le dossier `static/js/` et le bloc `{% block scripts %}` |
    | [Le nonce CSP](../../core-security/csp.md) | pourquoi un fichier `.js` externe passe sous `script-src 'self'` sans nonce |

??? note "Pourquoi aucun nonce n'est nécessaire"
    La CSP de Forge est `script-src 'self'` par défaut.
    Un fichier `.js` **externe** servi depuis `static/js/` est de même origine : `'self'` l'autorise déjà.

    Le nonce (`APP_CSP_NONCE_ENABLED`) ne sert qu'aux scripts **inline** (`<script>…</script>` dans la page).
    Ce motif n'en écrit aucun : toute la logique est dans le fichier externe, les données passent par des attributs `data-*`.
    Vous n'activez donc pas le nonce pour cet outil.

??? note "Contrôleur"
    Le contrôleur ne fait que rendre la page, avec les valeurs initiales des curseurs.
    Aucun POST, aucune session, aucun état serveur : le temps réel se joue entièrement côté navigateur.

    Ajoutez la méthode à `mvc/controllers/sandbox_controller.py` :

    ```python
        @staticmethod
        def oscilloscope(request: Request) -> Response:
            return BaseController.render(
                "sandbox/oscilloscope.html",
                request=request,
                context={"frequence": 2, "amplitude": 60},
            )
    ```

    Les valeurs `frequence` et `amplitude` sont de simples entiers passés à la vue, qui les posera dans le DOM.

??? note "Route"
    Ajoutez la route dans le groupe public de `mvc/routes/__init__.py` :

    ```python
    # mvc/routes/__init__.py
    from mvc.controllers.sandbox_controller import SandboxController

    with router.group("", public=True) as public:
        # ... routes existantes ...
        public.add("GET", "/sandbox/oscilloscope", SandboxController.oscilloscope, name="sandbox-oscilloscope")
    ```

    Une seule route `GET` : l'outil n'envoie rien au serveur.

??? note "Vue"
    Créez `mvc/views/sandbox/oscilloscope.html`.
    Les données du serveur sont posées dans des attributs `data-*`, jamais dans un script inline :

    ```html
    {% extends "layouts/public.html" %}

    {% block title %}Oscilloscope{% endblock %}

    {% block content %}
    <h1>Oscilloscope</h1>

    <div id="oscilloscope"
         data-frequence="{{ frequence }}"
         data-amplitude="{{ amplitude }}">
        <label>Fréquence : <input type="range" name="frequence" min="1" max="10" value="{{ frequence }}"></label>
        <label>Amplitude : <input type="range" name="amplitude" min="10" max="90" value="{{ amplitude }}"></label>
        <canvas width="600" height="200"></canvas>
    </div>
    {% endblock %}

    {% block scripts %}
        <script src="/static/js/oscilloscope.js" defer></script>
    {% endblock %}
    ```

    Le bloc `scripts` charge le module local.
    Le fichier est servi depuis `static/`, donc autorisé par `script-src 'self'`.

??? note "Module JavaScript local"
    Créez `static/js/oscilloscope.js`.
    Le module lit ses paramètres dans le DOM (`dataset`, valeurs des curseurs) et dessine sur le canvas.
    Aucune donnée n'est injectée en HTML brut, aucun appel réseau externe :

    ```javascript
    // static/js/oscilloscope.js
    const racine = document.getElementById("oscilloscope");
    const canvas = racine.querySelector("canvas");
    const ctx = canvas.getContext("2d");
    const curseurFrequence = racine.querySelector('input[name="frequence"]');
    const curseurAmplitude = racine.querySelector('input[name="amplitude"]');

    // Valeurs initiales lues depuis les attributs data-* posés par le serveur.
    curseurFrequence.value = racine.dataset.frequence;
    curseurAmplitude.value = racine.dataset.amplitude;

    let phase = 0;

    function dessiner() {
        const frequence = Number(curseurFrequence.value);
        const amplitude = Number(curseurAmplitude.value);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.beginPath();
        for (let x = 0; x < canvas.width; x++) {
            const y = canvas.height / 2 + amplitude * Math.sin((x / 40) * frequence + phase);
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
        phase += 0.05;
        requestAnimationFrame(dessiner);
    }

    requestAnimationFrame(dessiner);
    ```

    Toute la logique tient dans ce fichier local : le HTML reste statique, le serveur ne fournit que les valeurs initiales.

??? note "Tests"
    | Action | Résultat |
    |---|---|
    | `GET https://localhost:8000/sandbox/oscilloscope` | une sinusoïde animée sur le canvas |
    | Déplacer le curseur Fréquence | l'onde se resserre ou s'étale en direct |
    | Déplacer le curseur Amplitude | l'onde grandit ou s'aplatit en direct |
    | Ouvrir la console du navigateur | aucune violation CSP, aucun script bloqué |

    Si la console signale une violation `script-src`, c'est que le script est resté inline ou vient d'un CDN : ramenez-le dans `static/js/`.

??? note "À retenir"
    - Le JavaScript temps réel est **local**, servi depuis `static/js/`, jamais depuis un CDN.
    - Un fichier `.js` externe passe sous `script-src 'self'` **sans nonce**.
    - Les données du serveur passent par des attributs `data-*`, pas par un script inline.
    - Le serveur ne porte que les valeurs initiales : le temps réel vit côté navigateur.

[Voir le bilan du parcours](bilan.md)
