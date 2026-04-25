"""
Génère un hash PBKDF2 pour un mot de passe.

Usage :
    python cmd/make.py security:hash

Copier la valeur affichée dans .env :
    PasswordHash=<valeur>
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from core.security.hashing import hacher_mot_de_passe

mot_de_passe = input("Nouveau mot de passe : ")
print(hacher_mot_de_passe(mot_de_passe))
