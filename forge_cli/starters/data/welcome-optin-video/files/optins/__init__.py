"""Couche de branchement local des opt-ins de ce projet Forge.

Les paquets opt-in restent **distribués** (`forge-mvc-*`, installés via
pip) ; ce dossier ne contient **pas** leur code complet. Il sert
uniquement à les **brancher localement** : routes, migrations utilisées,
README et docs locales minimales.

Le branchement est **explicite** (voir ``optins/registry.py``) — Forge ne
fait aucune découverte automatique d'opt-ins. Contrat :
docs/architecture/optins-project-structure.md.
"""
