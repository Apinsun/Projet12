from checkit.extractor import filter_multimodal_data

def test_filter_multimodal_data():
    """
    Vérifie que la fonction de nettoyage ne conserve que les articles
    possédant du texte, une image et un lien, et qu'elle les standardise.
    """
    # faux jeu de données
    raw_data_mock = [
        {
            "title": "Article Parfait", 
            "description": "Ceci est un texte valide.", 
            "image_url": "http://site.com/image.jpg",
            "link": "http://site.com/article-parfait"
        },
        {
            "title": "Article Sans Image", 
            "description": "Texte très intéressant mais pas d'image.", 
            "image_url": None,
            "link": "http://site.com/article-sans-image"
        },
        {
            "title": "Article Sans Texte", 
            "content": None, 
            "description": None, 
            "image_url": "http://site.com/image.jpg",
            "link": "http://site.com/article-sans-texte"
        }
    ]

    # On fait passer nos fausses données dans le filtre
    clean_data = filter_multimodal_data(raw_data_mock)

    # 3 On vérifie les affirmations
    # Sur les 3 articles, un seul doit survivre
    assert len(clean_data) == 1
    
    # On vérifie que le mapping vers notre standard a bien fonctionné
    article_valide = clean_data[0]
    assert article_valide["title"] == "Article Parfait"
    assert article_valide["image_url"] == "http://site.com/image.jpg"
    assert article_valide["content"] == "Ceci est un texte valide."
    assert article_valide["article_url"] == "http://site.com/article-parfait"
    assert article_valide["source_type"] == "api_newsdata"