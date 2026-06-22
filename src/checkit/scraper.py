import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

# On importe l'accès à la BDD !
from checkit.loader import get_known_urls

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_urls_from_rss(rss_url, limit=5):
    """Extrait les URLs récentes du flux RSS."""
    logging.info(f"Lecture du flux RSS : {rss_url}")
    feed = feedparser.parse(rss_url)
    urls = [entry.link for entry in feed.entries[:limit] if hasattr(entry, 'link')]
    return urls

def scrape_multimodal_article(url):
    """Télécharge la page et extrait texte et image."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Titre introuvable"
        
        image_meta = soup.find('meta', property='og:image')
        image_url = image_meta['content'] if image_meta else None
        
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text(strip=True) for p in paragraphs])
        
        if image_url and len(content) > 100:
            return {
                "article_url": url,
                "title": title,
                "content": content,
                "image_url": image_url,
                "source_type": "rss_scraping",
                "extracted_at": datetime.now().isoformat()
            }
        else:
            logging.warning(f"Article ignoré (manque image ou texte trop court) : {url}")
            return None
    except Exception as e:
        logging.error(f"Erreur lors du scraping de {url} : {e}")
        return None

def extract_and_format_rss():
    """Le Wrapper principal appelé par Airflow"""
    RSS_TARGET = "https://www.france24.com/fr/rss" 
    
    recent_urls = fetch_urls_from_rss(RSS_TARGET, limit=5)
    known_urls = get_known_urls() # L'interrogation de Postgres !
    
    new_urls = [url for url in recent_urls if url not in known_urls]
    logging.info(f"Déduplication : {len(new_urls)} nouveaux articles sur {len(recent_urls)} à scraper.")
    
    valid_articles = []
    for url in new_urls:
        article_data = scrape_multimodal_article(url)
        if article_data:
            valid_articles.append(article_data)
            
    return valid_articles

# --- BLOC DE TEST LOCAL ---
if __name__ == "__main__":
    print("\n--- TEST MANUEL DU SCRAPER RSS ---")
    resultats = extract_and_format_rss()
    
    if resultats:
        print(f"\nSuccès ! {len(resultats)} nouveaux articles scrapés.")
    else:
        print("\nAucune nouveauté ou erreur réseau.")