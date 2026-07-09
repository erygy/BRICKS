#!/bin/bash
# Double-clique ce fichier pour lancer DIGGR (serveur + navigateur).
# Ferme cette fenêtre Terminal pour arrêter DIGGR.
cd "$(dirname "$0")"
echo "→ Démarrage de DIGGR…  (ne ferme pas cette fenêtre pendant la démo)"
( sleep 1.6; open "http://127.0.0.1:8970" ) &
exec python3 server.py
