#!/bin/bash

echo "🟢 Démarrage des conteneurs Airflow en arrière-plan..."

# Lancement de Docker Compose
docker compose up -d

echo "✅ Airflow est en cours de démarrage !"
echo "🌐 Interface Web : http://localhost:8080"
echo "👤 Utilisateur par défaut : airflow"
echo "🔑 Mot de passe par défaut : airflow"
echo "💡 N'oublie pas de glisser tes scripts Python dans le dossier ./dags/"
