#!/usr/bin/env bash
# scripts/iot-local-smoke.sh — Smoke test local du parcours Forge IoT.
#
# Déroule, de façon semi-automatique et pédagogique, le flux complet :
#   Mosquitto → forge iot:doctor --mqtt → forge iot:init
#   → forge migration:apply → forge iot:doctor --db → forge iot:listen
#   → forge iot:simulate → curl /api/iot/events
#
# Ce script est OPT-IN et LOCAL : il dépend de services externes
# (Mosquitto + MariaDB) et n'est PAS lancé par la suite CI standard.
# Il ne masque aucune étape : les commandes manuelles (migration:apply,
# iot:listen) sont laissées à l'utilisateur entre deux pauses.
#
# Hors périmètre : pas de Docker, pas de systemd applicatif, pas de
# service production, pas de mock Mosquitto, pas de TLS/auth.
#
# Ticket : IOT-END-TO-END-LOCAL-SMOKE-001

set -euo pipefail

echo "== Forge IoT local smoke =="
echo

# 1. Être à la racine d'un projet Forge (app.py + mvc/).
if [[ ! -f app.py || ! -d mvc ]]; then
    echo "[ERREUR] Ce script doit être lancé à la racine d'un projet Forge"
    echo "         (fichiers app.py et dossier mvc/ attendus)."
    exit 1
fi

# 2. La CLI forge doit être disponible.
if ! command -v forge >/dev/null 2>&1; then
    echo "[ERREUR] La commande 'forge' est introuvable."
    echo "         Active ton environnement Forge (.venv) puis réessaie."
    exit 1
fi

# 3. Diagnostic statique puis broker MQTT.
echo "-- Diagnostic statique --"
forge iot:doctor
echo
echo "-- Broker MQTT (Mosquitto doit être lancé) --"
forge iot:doctor --mqtt

# 4. Préparer la migration de la table iot_events.
echo
echo "-- Préparation du stockage --"
forge iot:init

echo
echo "Applique maintenant la migration si ce n'est pas déjà fait :"
echo "  forge migration:apply"
echo
read -r -p "Appuie sur Entrée quand la migration est appliquée..."

# 5. Vérifier que la table est lisible.
forge iot:doctor --db

# 6. Lancer l'écoute dans un autre terminal.
echo
echo "Dans un AUTRE terminal, lance l'écoute (laisse tourner) :"
echo "  forge iot:listen"
echo
read -r -p "Appuie sur Entrée quand l'écoute est active..."

# 7. Publier quelques mesures factices.
echo
echo "-- Publication de 3 mesures simulées --"
forge iot:simulate --count 3 --interval 1

# 8. Lire les événements via l'API HTTP.
echo
echo "Enfin, vérifie l'API HTTP (avec l'application lancée via 'forge run') :"
echo "  curl http://localhost:8000/api/iot/events"
echo
echo "== Smoke terminé =="
