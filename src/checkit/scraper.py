import logging
import requests
import feedparser
from bs4 import BeautifulSoup
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_urls_from_rss(rss_url, limit=5):
    """
    Lit un flux RSS et retourne une liste d'URLs d'articles récents.
    """
    logging.info(f"Lecture du flux RSS : {rss_url}")
    feed = feedparser.parse(rss_url)
    
    urls = []
    # On prend les 'limit' premiers articles
    for entry in feed.entries[:limit]:
        if hasattr(entry, 'link'):
            urls.append(entry.link)
            
    logging.info(f"{len(urls)} URLs récupérées depuis le flux.")
    return urls

def scrape_multimodal_article(url):
    """
    Télécharge la page web et extrait le texte principal et l'image de couverture.
    """
    try:
        # On se fait passer pour un vrai navigateur pour éviter d'être bloqué
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extraction du Titre
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Titre introuvable"
        
        # 2. Extraction de l'Image (Via la balise standard OpenGraph)
        image_meta = soup.find('meta', property='og:image')
        image_url = image_meta['content'] if image_meta else None
        
        # 3. Extraction du Texte (On rassemble tous les paragraphes <p>)
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text(strip=True) for p in paragraphs])
        
        # Le filtre : on ne renvoie la donnée QUE si elle est multimodale
        if image_url and len(content) > 100:
            return {
                "source_url": url,
                "title": title,
                "content": content,
                "image_url": image_url
            }
        else:
            logging.warning(f"Article ignoré (manque image ou texte trop court) : {url}")
            return None
            
    except Exception as e:
        logging.error(f"Erreur lors du scraping de {url} : {e}")
        return None

def load_existing_data(filename="articles_bruts.json"):
    """Charge les données existantes et retourne la liste des articles et un set d'URLs connues."""
    current_dir = Path(__file__).resolve().parent
    file_path = current_dir.parent.parent / "data" / "raw" / filename
    
    if not file_path.exists():
        return [], set()
        
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # On crée un Set d'URLs pour une recherche ultra-rapide
            known_urls = {art.get('source_url', art.get('link')) for art in data}
            return data, known_urls
        except json.JSONDecodeError:
            return [], set()

def save_to_json(data, filename="articles_bruts.json"):
    """Sauvegarde les données à la racine du projet."""
    current_dir = Path(__file__).resolve().parent
    file_path = current_dir.parent.parent / "data" / "raw" / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"Fichier mis à jour. Total : {len(data)} articles.")

if __name__ == "__main__":
    RSS_TARGET = "https://www.france24.com/fr/rss" 
    
    # 1. Récupération des URLs fraîches
    recent_urls = fetch_urls_from_rss(RSS_TARGET, limit=5)
    
    # 2. Chargement de l'historique pour la déduplication
    existing_articles, known_urls = load_existing_data()
    
    # 3. Filtrage : on ne garde que les URLs qu'on ne connaît pas encore
    new_urls = [url for url in recent_urls if url not in known_urls]
    logging.info(f"{len(new_urls)} nouveaux articles à scraper sur {len(recent_urls)} détectés.")
    
    # 4. Scraping des nouveautés
    for url in new_urls:
        logging.info(f"Scraping en cours : {url}")
        article_data = scrape_multimodal_article(url)
        
        if article_data:
            existing_articles.append(article_data)
            
    # 5. Sauvegarde du fichier global mis à jour
    save_to_json(existing_articles)
