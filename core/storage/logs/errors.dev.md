# Erreurs runtime Forge — dev

Source canonique : `storage/logs/errors.dev.jsonl`  
Généré depuis le JSONL. Ne pas modifier ce fichier à la main.

Généré le : 2026-06-06T16:40:34

---

## Résumé

- Erreurs listées : 45
- Dernière erreur : 2026-06-06T14:40:34.096230+00:00

---

## err_20260606_161357_33fe — RuntimeError

**Date :** 2026-06-06T14:13:57.527964+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /boom
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/test_application.py
- Ligne : 19
- Fonction : _handler_boom

### Message

boom intentionnel

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/test_application.py:19 — _handler_boom


---

## err_20260606_162317_bd57 — RuntimeError

**Date :** 2026-06-06T14:23:17.936144+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 158
- Fonction : _handler_crash

### Message

erreur intentionnelle

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:158 — _handler_crash


---

## err_20260606_162317_4575 — ValueError

**Date :** 2026-06-06T14:23:17.938963+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 168
- Fonction : _handler_crash

### Message

détail interne sensible

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:168 — _handler_crash


---

## err_20260606_162317_eb06 — RuntimeError

**Date :** 2026-06-06T14:23:17.948516+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 181
- Fonction : _handler_crash

### Message

SECRET_DB_PASSWORD=supersecret

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:181 — _handler_crash


---

## err_20260606_162317_6ca2 — RuntimeError

**Date :** 2026-06-06T14:23:17.951284+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 192
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:192 — _handler_crash


---

## err_20260606_162317_67f4 — TemplateNotFoundError

**Date :** 2026-06-06T14:23:17.955766+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : template_inexistant.html (vues : /tmp/claude-1000/pytest-of-roger/pytest-620/test_missing_template_returns_0).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_162317_66b9 — TemplateNotFoundError

**Date :** 2026-06-06T14:23:17.957993+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : template_inexistant.html (vues : /tmp/claude-1000/pytest-of-roger/pytest-620/test_missing_template_500_body0).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_162317_c1af — TemplateSyntaxError

**Date :** 2026-06-06T14:23:17.961866+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /tmp/claude-1000/pytest-of-roger/pytest-620/test_template_syntax_error_ret0/broken.html
- Ligne : 1
- Fonction : template

### Message

Expected an expression, got 'end of statement block'

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:249 — _handler_broken_template
- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:34 — render
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:1016 — get_template
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:975 — _load_template
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/loaders.py:138 — load
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:771 — compile
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:942 — handle_exception
- /tmp/claude-1000/pytest-of-roger/pytest-620/test_template_syntax_error_ret0/broken.html:1 — template


---

## err_20260606_162317_7921 — UndefinedError

**Date :** 2026-06-06T14:23:17.966127+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py
- Ligne : 490
- Fonction : getattr

### Message

'objet_inexistant' is undefined

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:263 — _handler_undefined
- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:40 — render
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:1295 — render
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:942 — handle_exception
- /tmp/claude-1000/pytest-of-roger/pytest-620/test_undefined_variable_in_tem0/test.html:1 — top-level template code
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:490 — getattr


---

## err_20260606_162317_c440 — RuntimeError

**Date :** 2026-06-06T14:23:17.969382+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 281
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:281 — _handler_crash


---

## err_20260606_162317_fe93 — TypeError

**Date :** 2026-06-06T14:23:17.974786+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 316
- Fonction : _handler_type_error

### Message

mauvais type

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:316 — _handler_type_error


---

## err_20260606_162317_bad9 — AttributeError

**Date :** 2026-06-06T14:23:17.977920+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 327
- Fonction : _handler_attr_error

### Message

'NoneType' object has no attribute 'methode_inexistante'

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:327 — _handler_attr_error


---

## err_20260606_162317_2e3c — KeyError

**Date :** 2026-06-06T14:23:17.980756+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 338
- Fonction : _handler_key_error

### Message

'cle_inexistante'

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:338 — _handler_key_error


---

## err_20260606_162317_2200 — RuntimeError

**Date :** 2026-06-06T14:23:17.983586+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 349
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:349 — _handler_crash


---

## err_20260606_162317_2d5d — RuntimeError

**Date :** 2026-06-06T14:23:17.984848+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 349
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:349 — _handler_crash


---

## err_20260606_162317_7144 — RuntimeError

**Date :** 2026-06-06T14:23:17.985756+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 349
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:349 — _handler_crash


---

## err_20260606_162324_bb4b — RuntimeError

**Date :** 2026-06-06T14:23:24.757571+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /boom
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/test_application.py
- Ligne : 19
- Fonction : _handler_boom

### Message

boom intentionnel

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/test_application.py:19 — _handler_boom


---

## err_20260606_163948_b69e — RuntimeError

**Date :** 2026-06-06T14:39:48.411204+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 158
- Fonction : _handler_crash

### Message

erreur intentionnelle

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:158 — _handler_crash


---

## err_20260606_163948_1cd0 — ValueError

**Date :** 2026-06-06T14:39:48.414575+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 168
- Fonction : _handler_crash

### Message

détail interne sensible

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:168 — _handler_crash


---

## err_20260606_163948_bc9b — RuntimeError

**Date :** 2026-06-06T14:39:48.423867+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 181
- Fonction : _handler_crash

### Message

SECRET_DB_PASSWORD=supersecret

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:181 — _handler_crash


---

## err_20260606_163948_ce02 — RuntimeError

**Date :** 2026-06-06T14:39:48.427073+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 192
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:192 — _handler_crash


---

## err_20260606_163948_43cb — TemplateNotFoundError

**Date :** 2026-06-06T14:39:48.431709+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : template_inexistant.html (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_missing_template_returns_0).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_163948_698b — TemplateNotFoundError

**Date :** 2026-06-06T14:39:48.434360+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : template_inexistant.html (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_missing_template_500_body0).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_163948_7a18 — TemplateSyntaxError

**Date :** 2026-06-06T14:39:48.438585+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /tmp/claude-1000/pytest-of-roger/pytest-624/test_template_syntax_error_ret0/broken.html
- Ligne : 1
- Fonction : template

### Message

Expected an expression, got 'end of statement block'

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:249 — _handler_broken_template
- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:34 — render
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:1016 — get_template
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:975 — _load_template
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/loaders.py:138 — load
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:771 — compile
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:942 — handle_exception
- /tmp/claude-1000/pytest-of-roger/pytest-624/test_template_syntax_error_ret0/broken.html:1 — template


---

## err_20260606_163948_0b08 — UndefinedError

**Date :** 2026-06-06T14:39:48.443039+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py
- Ligne : 490
- Fonction : getattr

### Message

'objet_inexistant' is undefined

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:263 — _handler_undefined
- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:40 — render
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:1295 — render
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:942 — handle_exception
- /tmp/claude-1000/pytest-of-roger/pytest-624/test_undefined_variable_in_tem0/test.html:1 — top-level template code
- /home/roger/Projets/Forge/.venv/lib/python3.12/site-packages/jinja2/environment.py:490 — getattr


---

## err_20260606_163948_0cc0 — RuntimeError

**Date :** 2026-06-06T14:39:48.446642+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 281
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:281 — _handler_crash


---

## err_20260606_163948_e651 — TypeError

**Date :** 2026-06-06T14:39:48.452184+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 316
- Fonction : _handler_type_error

### Message

mauvais type

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:316 — _handler_type_error


---

## err_20260606_163948_7135 — AttributeError

**Date :** 2026-06-06T14:39:48.455757+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 327
- Fonction : _handler_attr_error

### Message

'NoneType' object has no attribute 'methode_inexistante'

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:327 — _handler_attr_error


---

## err_20260606_163948_64c0 — KeyError

**Date :** 2026-06-06T14:39:48.459203+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 338
- Fonction : _handler_key_error

### Message

'cle_inexistante'

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:338 — _handler_key_error


---

## err_20260606_163948_6419 — RuntimeError

**Date :** 2026-06-06T14:39:48.462441+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 349
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:349 — _handler_crash


---

## err_20260606_163948_dd85 — RuntimeError

**Date :** 2026-06-06T14:39:48.464027+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 349
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:349 — _handler_crash


---

## err_20260606_163948_8cc5 — RuntimeError

**Date :** 2026-06-06T14:39:48.465368+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /test
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py
- Ligne : 349
- Fonction : _handler_crash

### Message

boom

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/meta/test_runtime_errors_audit.py:349 — _handler_crash


---

## err_20260606_164022_4cac — RuntimeError

**Date :** 2026-06-06T14:40:22.939284+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** runtime  
**Safe for display :** false  

### Requête

- Méthode : GET
- Chemin : /boom
- Query : 

### Localisation

- Fichier : /home/roger/Projets/Forge/tests/test_application.py
- Ligne : 19
- Fonction : _handler_boom

### Message

boom intentionnel

### Traceback simplifié

- /home/roger/Projets/Forge/core/app/application.py:61 — dispatch
- /home/roger/Projets/Forge/tests/test_application.py:19 — _handler_boom


---

## err_20260606_164034_e553 — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.051330+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_template_absent_retourne_0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_0215 — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.054510+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_template_absent_propose_l0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_bc74 — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.064086+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_template_absent_ne_leve_p0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_8757 — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.067031+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/core/http/helpers.py
- Ligne : 64
- Fonction : html

### Message

Template introuvable : inexistant.html (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_raw_template_absent_aussi0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:64 — html


---

## err_20260606_164034_5502 — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.070002+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_template_absent_message_m0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_49da — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.073003+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_template_absent_ne_fuit_p0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_4643 — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.076052+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_template_absent_ne_propos0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_61de — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.081453+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_render_template_absent_pa0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_a498 — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.086695+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_pas_de_traceback_dans_la_0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_fcba — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.089898+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_pas_de_traceback_dans_la_1/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_8a52 — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.093034+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_pas_de_nom_de_classe_d_ex0/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---

## err_20260606_164034_d79d — TemplateNotFoundError

**Date :** 2026-06-06T14:40:34.096230+00:00  
**Environnement :** dev  
**Niveau :** ERROR  
**Catégorie :** template  
**Safe for display :** false  

### Localisation

- Fichier : /home/roger/Projets/Forge/integrations/jinja2/renderer.py
- Ligne : 39
- Fonction : render

### Message

Template introuvable : bonjour (vues : /tmp/claude-1000/pytest-of-roger/pytest-624/test_pas_de_nom_de_classe_d_ex1/views).

### Traceback simplifié

- /home/roger/Projets/Forge/core/http/helpers.py:73 — html
- /home/roger/Projets/Forge/core/templating/manager.py:17 — render
- /home/roger/Projets/Forge/integrations/jinja2/renderer.py:39 — render


---
