import re
import unicodedata

def generate_slug(prefix, text):
    """
    Génère un identifiant unique (slug) normalisé.
    Ex: "Très grande" -> "trait-très-grande"
    """
    # 1. Retirer les accents
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    # 2. Mettre en minuscules
    text = text.lower()
    # 3. Remplacer tout ce qui n'est pas alphanumérique par des tirets
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # 4. Nettoyer les tirets en début et fin de chaîne
    text = text.strip('-')
    
    return f"{prefix}-{text}"