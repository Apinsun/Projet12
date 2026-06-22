classDiagram
    direction LR
    class Dataset_Checkit_AI {
        <<Processed>>
        +String article_url : Clé unique / Identifiant source
        +String title : Texte normalisé (NLP)
        +String content : Feature textuelle principale (NLP)
        +String image_url : Lien de téléchargement des pixels (Vision)
        +String source_type : Variable catégorielle (Suivi des biais)
        +DateTime extracted_at : Métadonnée temporelle (Data lineage)
        +Int content_length : Feature stylométrique (Classification)
    }

    note for Dataset_Checkit_AI "Alignement Cas d'Usage IA :
• content : Analyse sémantique et vectorisation (Embeddings)
• image_url : Entrée pour le modèle de Computer Vision (ResNet/ViT)
• content_length : Analyse de la distribution statistique (Stylométrie)
• source_type : Équilibrement des classes et détection de biais de source"
