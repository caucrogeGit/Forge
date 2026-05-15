# ADR-006 — Version Python minimale : 3.12+

## Statut

Acceptée

---

## Contexte

Forge cible actuellement Python 3.11+ comme version minimale. Python 3.11
sera en fin de vie en octobre 2027, mais Python 3.12 est disponible depuis
octobre 2023 et apporte des améliorations substantielles.

La décision de la version minimale doit être prise avant la phase 14.3 car
elle impacte :

- la syntaxe autorisée dans le code de Forge (type hints, f-strings, etc.) ;
- les outils de packaging (`pyproject.toml`, `python_requires`) ;
- la matrice de tests CI ;
- la documentation d'installation.

---

## Décision

**Forge 3.0 cible Python 3.12+ comme version minimale.**

Concrètement :

1. `python_requires = ">=3.12"` dans tous les `pyproject.toml` des distributions
   Forge 3.0.

2. Les nouvelles syntaxes Python 3.12 sont autorisées dans le code de Forge :
   - Syntaxe des paramètres de type génériques (`type X = ...`)
   - Améliorations des f-strings
   - `pathlib` étendu
   - Sous-interpréteurs (si pertinent)

3. La matrice de tests CI est réduite à Python 3.12 et 3.13 (dernière stable).

4. La documentation d'installation et les starters référencent Python 3.12+.

5. Python 3.11 reste fonctionnel avec Forge 2.x — cette décision ne s'applique
   qu'à Forge 3.0.

---

## Conséquences

- Les développeurs sur Python 3.11 devront rester sur Forge 2.x ou migrer.
- Le guide de migration `MIGRATION-GUIDE-3.0-001` documentera la contrainte
  de version Python.
- La matrice CI est simplifiée (2 versions au lieu de 3+).
- Forge peut exploiter les améliorations de performance de Python 3.12 (meilleur
  GIL, interpréteur plus rapide).

---

## Alternatives considérées

**Python 3.11+.** Conserverait la compatibilité maximale mais bloque
l'utilisation des nouvelles syntaxes et laisse Forge supporter une version
Python proche de sa fin de vie.

**Python 3.13+.** Trop restrictif au moment de la release de Forge 3.0 ;
3.13 est récent et beaucoup d'environnements de production sont encore sur
3.12.
