#!/bin/bash

echo "🚀 Début de l'initialisation de l'environnement Airflow..."

# 1. Téléchargement du docker-compose.yaml officiel (version 2.10.0)
if [ ! -f "docker-compose.yaml" ]; then
    echo "📥 Téléchargement de docker-compose.yaml..."
    curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.10.0/docker-compose.yaml'
else
    echo "✅ docker-compose.yaml déjà présent."
fi

# 2. Création des répertoires de travail
echo "📁 Création des dossiers locaux (dags, logs, plugins, config)..."
mkdir -p ./dags ./logs ./plugins ./config

# 3. Configuration des permissions (UID)
echo "🔐 Configuration des permissions utilisateur..."
echo -e "AIRFLOW_UID=$(id -u)" > .env

# 4. Initialisation de la base de données Airflow
echo "⚙️ Initialisation de la base de données via Docker..."
docker compose up airflow-init

echo "✅ Initialisation terminée avec succès !"
