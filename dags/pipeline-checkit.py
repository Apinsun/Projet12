import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# --- NOUVELLE CONFIGURATION DU CHEMIN (Spécial Docker) ---
# Dans le conteneur Docker officiel, tout ton projet est monté dans /opt/airflow
SRC_DIR = '/opt/airflow/src'

# On ajoute ce dossier au radar de Python
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Maintenant, l'import fonctionnera !
from checkit.extractor import load_existing_data, fetch_raw_api_data, filter_multimodal_data, save_to_json
from checkit.scraper import fetch_urls_from_rss, scrape_multimodal_article
from checkit.transformer import load_raw_data, run_transformation_pipeline, save_processed_data
from checkit.loader import load_to_db

# --- DÉFINITION DES TÂCHES (WRAPPERS) ---

def task_extract_api():
    """Tâche 1 : Extraction depuis NewsData.io"""
    print("Démarrage de l'extraction API...")
    existing_articles, known_urls = load_existing_data()
    raw_data = fetch_raw_api_data()
    if raw_data:
        clean_data = filter_multimodal_data(raw_data)
        new_articles = [art for art in clean_data if art.get('article_url') not in known_urls]
        if new_articles:
            existing_articles.extend(new_articles)
            save_to_json(existing_articles)
            print(f"{len(new_articles)} nouveaux articles API sauvegardés.")
        else:
            print("Aucun nouvel article API inédit.")

def task_extract_rss():
    """Tâche 2 : Extraction depuis le flux RSS France 24"""
    print("Démarrage du scraping RSS...")
    RSS_TARGET = "https://www.france24.com/fr/rss"
    recent_urls = fetch_urls_from_rss(RSS_TARGET, limit=5)
    existing_articles, known_urls = load_existing_data()
    
    new_urls = [url for url in recent_urls if url not in known_urls]
    for url in new_urls:
        article_data = scrape_multimodal_article(url)
        if article_data:
            existing_articles.append(article_data)
    
    if new_urls:
        save_to_json(existing_articles)
        print(f"{len(new_urls)} nouveaux articles RSS scrapés.")
    else:
        print("Aucun nouvel article RSS inédit.")

def task_transform_data():
    """Tâche 3 : Nettoyage et standardisation"""
    print("Démarrage de la transformation...")
    raw_data = load_raw_data()
    if raw_data:
        clean_data = run_transformation_pipeline(raw_data)
        save_processed_data(clean_data)
        print("Transformation terminée avec succès.")

# --- CONFIGURATION DU DAG ---

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# On définit le DAG (son nom, sa fréquence, etc.)
with DAG(
    'checkit_daily_pipeline', # Le nom qui s'affichera dans l'interface
    default_args=default_args,
    description='Pipeline ETL pour la détection de Fake News',
    schedule=timedelta(hours=12), # Tourne toutes les 12 heures
    start_date=datetime(2026, 6, 16),
    catchup=False, # Ne rattrape pas les jours passés
    tags=['checkit', 'etl'],
) as dag:

    # On transforme nos fonctions Python en Tâches Airflow
    extract_api_node = PythonOperator(
        task_id='extract_news_api',
        python_callable=task_extract_api,
    )

    extract_rss_node = PythonOperator(
        task_id='extract_rss_scraper',
        python_callable=task_extract_rss,
    )

    transform_node = PythonOperator(
        task_id='transform_and_clean_data',
        python_callable=task_transform_data,
    )

    load_node = PythonOperator(
            task_id='load_to_postgres',
            python_callable=lambda: load_to_db(load_processed_data()) # Remplace par la fonction qui lit tes données nettoyées
        )

    # La nouvelle chaîne de montage : Extraction -> Transformation -> Chargement
    [extract_api_node, extract_rss_node] >> transform_node >> load_node
