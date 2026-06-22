import json
import logging
import re
from pathlib import Path

# Configuration du logging requise par le projet
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_raw_data(filename="articles_bruts.json"):
    """Charge les données brutes depuis le dossier data/raw."""
    current_dir = Path(__file__).resolve().parent
    file_path = current_dir.parent.parent / "data" / "raw" / filename
    
    if not file_path.exists():
        logging.error(f"Fichier introuvable : {file_path}")
        return []
        
    with open(file_path, 'r', encoding='utf-8') as f:
        logging.info(f"Chargement de {file_path} réussi.")
        return json.load(f)

def clean_text(text, article_ref="Inconnu"):
    """Nettoie le texte et logge les modifications précises en mode DEBUG."""
    if not text:
        return ""
        
    # 1. Traitement du HTML
    text_no_html = re.sub(r'<[^>]+>', '', text)
    html_removed = len(text) != len(text_no_html) # Si la longueur change, c'est qu'on a retiré des balises
    
    # 2. Traitement des espaces
    text_clean = re.sub(r'\s+', ' ', text_no_html).strip()
    spaces_fixed = len(text_no_html) != len(text_clean)
    
    # 3. Journalisation ciblée
    if html_removed or spaces_fixed:
        modifs = []
        if html_removed: 
            modifs.append("Balises HTML purgées")
        if spaces_fixed: 
            modifs.append("Espaces/Sauts de ligne lissés")
            
        # On logge en DEBUG avec un bout de l'URL pour identifier l'article
        logging.debug(f"Modif [{article_ref[:40]}...] -> {' | '.join(modifs)}")
        
    return text_clean

def run_transformation_pipeline(raw_data):
    """Applique les règles métier sur l'ensemble du dataset."""
    processed_data = []
    
    for art in raw_data:
        url = art.get('article_url', 'Sans URL')
        # On passe maintenant l'URL à notre fonction de nettoyage pour les logs
        cleaned_content = clean_text(art.get('content', ''), article_ref=url)
        cleaned_title = clean_text(art.get('title', 'Titre introuvable'), article_ref=url)
        
        # Ultime vérification de qualité post-nettoyage
        if len(cleaned_content) > 50 and art.get('image_url'):
            transformed_art = {
                "article_url": url,
                "title": cleaned_title,
                "content": cleaned_content,
                "image_url": art.get('image_url'),
                "source_type": art.get('source_type'),
                "extracted_at": art.get('extracted_at'),
                "content_length": len(cleaned_content) 
            }
            processed_data.append(transformed_art)
            
    logging.info(f"Transformation terminée : {len(processed_data)} articles validés sur {len(raw_data)} bruts.")
    return processed_data

def save_processed_data(data, filename="articles_clean.json"):
    """Sauvegarde les données transformées dans le dossier data/processed."""
    if not data:
        logging.warning("Aucune donnée à sauvegarder après transformation.")
        return
        
    current_dir = Path(__file__).resolve().parent
    # On crée le nouveau dossier cible "processed"
    file_path = current_dir.parent.parent / "data" / "processed" / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    logging.info(f"Sauvegarde du dataset propre dans : {file_path}")

if __name__ == "__main__":
    # 1. Lecture (Extract)
    raw_data = load_raw_data()
    
    if raw_data:
        # 2. Traitement (Transform)
        clean_data = run_transformation_pipeline(raw_data)
        
        # 3. Exportation (Load)
        save_processed_data(clean_data)
