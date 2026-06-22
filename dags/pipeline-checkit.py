import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import time

# --- CONFIGURATION DU CHEMIN ---
SRC_DIR = '/opt/airflow/src'
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# --- NOUVEAUX IMPORTS ÉPURÉS ---
# On n'importe QUE les fonctions d'action, plus aucune fonction "save_to_json"
from checkit.extractor import extract_and_format_api
from checkit.scraper import extract_and_format_rss
from checkit.transformer import run_transformation_pipeline
from checkit.loader import load_to_db, save_metrics

# --- WRAPPERS AIRFLOW (Système XCom) ---

def task_extract_api(**kwargs):
    """Tâche 1 : Extrait l'API et renvoie la liste. Airflow la garde en mémoire (XCom)."""
    print("Démarrage de l'extraction API...")
    return extract_and_format_api() 

def task_extract_rss(**kwargs):
    """Tâche 2 : Extrait le RSS et renvoie la liste. Airflow la garde en mémoire (XCom)."""
    print("Démarrage du scraping RSS...")
    return extract_and_format_rss()

def task_transform_data(ti, **kwargs):
    """Tâche 3 : Récupère les données en mémoire, les fusionne, les nettoie, et les renvoie."""
    print("Démarrage de la transformation...")
    
    # 'ti' (TaskInstance) est l'outil Airflow pour tirer les données de la mémoire
    api_data = ti.xcom_pull(task_ids='extract_and_format_api') or []
    rss_data = ti.xcom_pull(task_ids='extract_and_format_rss') or []
    
    # On fusionne les deux sources de données
    raw_data = api_data + rss_data
    
    if not raw_data:
        print("Aucune donnée brute extraite. Fin de la transformation.")
        return []

    # On passe les données au transformateur métier
    clean_data = run_transformation_pipeline(raw_data)
    print(f"Transformation de {len(clean_data)} articles terminée.")
    
    return {
        "clean_data": clean_data,
        "api_count": len(api_data),
        "rss_count": len(rss_data)
    }

def task_load_data(ti, **kwargs):
    # On récupère le dictionnaire complet depuis la tâche de transformation
    data_dict = ti.xcom_pull(task_ids='transform_and_clean_data')
    
    if not data_dict or not data_dict.get("clean_data"):
        print("Aucune donnée nettoyée à charger.")
        return

    clean_data = data_dict["clean_data"]
    
    # 1. Chargement dans la base
    load_to_db(clean_data)
    
    # 2. Calcul du temps d'exécution total (grâce au "start_date" d'Airflow)
    execution_date = kwargs['execution_date']
    current_time = datetime.now(execution_date.tzinfo)
    total_seconds = (current_time - execution_date).total_seconds()
    
    # 3. Sauvegarde des métriques
    save_metrics(
        api_count=data_dict["api_count"],
        rss_count=data_dict["rss_count"],
        valid_count=len(clean_data),
        execution_time=round(total_seconds, 2)
    )


# --- CONFIGURATION DU DAG ---

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'checkit_daily_pipeline',
    default_args=default_args,
    description='Pipeline ETL 100% Base de Données pour la détection de Fake News + data KPI',
    schedule=timedelta(hours=12),
    start_date=datetime(2026, 6, 16),
    catchup=False,
    tags=['checkit', 'etl'],
) as dag:

    # Déclaration des 4 nœuds
    extract_api_node = PythonOperator(
        task_id='extract_and_format_api',
        python_callable=task_extract_api,
    )

    extract_rss_node = PythonOperator(
        task_id='extract_and_format_rss',
        python_callable=task_extract_rss,
    )

    transform_node = PythonOperator(
        task_id='transform_and_clean_data',
        python_callable=task_transform_data,
    )

    load_node = PythonOperator(
        task_id='load_to_postgres',
        python_callable=task_load_data,
    )

    # La chaîne de montage
    [extract_api_node, extract_rss_node] >> transform_node >> load_node