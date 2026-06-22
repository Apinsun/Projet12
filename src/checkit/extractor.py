import os
import json
import logging
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = os.getenv("NEWSDATA_API_KEY")
BASE_URL = "https://newsdata.io/api/1/news"

def fetch_raw_api_data(query="fake news OR misinformation OR fact check", language="en", limit=10):
    """1. Récupère les données brutes de l'API"""
    if not API_KEY:
        logging.error("Clé API introuvable.")
        return []

    params = {'apikey': API_KEY, 'q': query, 'language': language, 'image': 1}
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur API : {e}")
        return []

def filter_multimodal_data(raw_articles):
    """2. Filtre et standardise les articles (La fonction testée par pytest !)"""
    if not raw_articles:
        return []

    valid_articles = []
    for art in raw_articles:
        raw_content = art.get('content', '')
        description = art.get('description', '')
        
        text = description if raw_content == "ONLY AVAILABLE IN PAID PLANS" else (raw_content or description)
        
        if text and art.get('image_url') and art.get('link'):
            valid_articles.append({
                "article_url": art.get('link'),
                "title": art.get('title', 'Titre introuvable'),
                "content": text,
                "image_url": art.get('image_url'),
                "source_type": "api_newsdata",
                "extracted_at": datetime.now().isoformat()
            })
            
    logging.info(f"Nettoyage : {len(valid_articles)} articles multimodaux conservés.")
    return valid_articles

def extract_and_format_api():
    """3. Le Wrapper principal appelé par Airflow"""
    raw_data = fetch_raw_api_data()
    return filter_multimodal_data(raw_data)

# --- BLOC DE TEST LOCAL ---
if __name__ == "__main__":
    print("\n--- TEST MANUEL DE L'EXTRACTEUR API ---")
    resultats = extract_and_format_api()
    
    if resultats:
        print(f"\nSuccès ! {len(resultats)} articles valides récupérés.")
        print(json.dumps(resultats[0], indent=4, ensure_ascii=False))
    else:
        print("\nAucun résultat.")