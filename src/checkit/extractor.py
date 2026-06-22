import os
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# load_dotenv(find_dotenv())
# API_KEY = os.getenv("NEWSDATA_API_KEY")

API_KEY = os.getenv("NEWSDATA_API_KEY")

BASE_URL = "https://newsdata.io/api/1/news"

# 1. FONCTION DE CONNEXION (Extract)
def fetch_raw_api_data(query="fake news OR misinformation OR fact check", language="en", limit=10):
    if not API_KEY:
        logging.error("Clé API introuvable.")
        return None

    params = {'apikey': API_KEY, 'q': query, 'language': language, 'image': 1}
    
    try:
        logging.info(f"Connexion à l'API pour la requête : '{query}'...")
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur de connexion API : {e}")
        return None

# 2. FONCTION DE PARSING / NETTOYAGE (Transform léger)
def filter_multimodal_data(raw_articles):
    if not raw_articles:
        return []

    valid_articles = []
    for art in raw_articles:
        raw_content = art.get('content', '')
        description = art.get('description', '')
        
        # Si le content est le message de blocage, on force à prendre la description
        if raw_content == "ONLY AVAILABLE IN PAID PLANS":
            text = description
        else:
            text = raw_content or description
        image = art.get('image_url')
        url = art.get('link')
        
        if text and image and url:
            # On mappe les champs de l'API vers notre format standardisé
            standardized_art = {
                "article_url": url,
                "title": art.get('title', 'Titre introuvable'),
                "content": text,
                "image_url": image,
                "source_type": "api_newsdata",
                "extracted_at": datetime.now().isoformat()
            }
            valid_articles.append(standardized_art)
            
    logging.info(f"Nettoyage : {len(valid_articles)} articles multimodaux conservés.")
    return valid_articles

# 3. FONCTION DE CHARGEMENT (Pour la déduplication)
def load_existing_data(filename="articles_bruts.json"):
    current_dir = Path(__file__).resolve().parent
    file_path = current_dir.parent.parent / "data" / "raw" / filename
    
    if not file_path.exists():
        return [], set()
        
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # L'astuce : on cherche 'link' (API) ou 'source_url' (Scraper)
            known_urls = {art.get('link', art.get('article_url')) for art in data if art.get('link') or art.get('source_url')}
            return data, known_urls
        except json.JSONDecodeError:
            return [], set()

# 4. FONCTION DE SAUVEGARDE (Load)
def save_to_json(data, filename="articles_bruts.json"):
    if not data:
        return

    current_dir = Path(__file__).resolve().parent
    file_path = current_dir.parent.parent / "data" / "raw" / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    logging.info(f"Fichier mis à jour. Total : {len(data)} articles dans la base.")

# 5. ORCHESTRATION MAIN
if __name__ == "__main__":
    # Étape A : On regarde ce qu'on a déjà en stock
    existing_articles, known_urls = load_existing_data()
    
    # Étape B : On va chercher de nouvelles données
    raw_data = fetch_raw_api_data()
    
    if raw_data:
        # Étape C : On filtre pour ne garder que le multimodal
        clean_data = filter_multimodal_data(raw_data)
        
        # Étape D : Déduplication
        # On ne garde que les articles dont le 'link' n'est pas dans notre Set
        new_articles = [art for art in clean_data if art.get('link') not in known_urls]
        logging.info(f"Déduplication : {len(new_articles)} articles totalement inédits.")
        
        # Étape E : Sauvegarde finale si on a du nouveau
        if new_articles:
            existing_articles.extend(new_articles)
            save_to_json(existing_articles)
        else:
            logging.info("Aucune nouvelle donnée multimodale à sauvegarder pour le moment.")