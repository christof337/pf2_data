import pdfplumber
import os
from pdfplumber.utils import extract_text

def extract_styled_layout(page_or_crop, useTextFlow=False):
    """Extrait le texte avec layout, italique (*) et gras (**) en modifiant le flux de chars"""
    chars = page_or_crop.chars
    if not chars:
        return ""

    # 1. Détecteurs de styles
    def is_italic(fontname):
        return fontname and any(x in fontname for x in ["Italic", "-It", "Oblique"])

    def is_bold(fontname):
        # L'éditeur utilise souvent 'Bold', 'Black' ou 'Heavy'
        return fontname and any(x in fontname for x in ["Bold", "Black", "Heavy"])

    # 2. On travaille sur une copie
    modified_chars = [c.copy() for c in chars]

    for i in range(len(modified_chars)):
        curr = modified_chars[i]
        font = curr.get('fontname', '')
        
        curr_it = is_italic(font)
        curr_bd = is_bold(font)
        
        prev = modified_chars[i-1] if i > 0 else {}
        prev_font = prev.get('fontname', '')
        prev_it = is_italic(prev_font)
        prev_bd = is_bold(prev_font)

        # --- Gestion du GRAS (Double étoile) ---
        if curr_bd and not prev_bd:
            curr['text'] = "**" + curr['text']
        if not curr_bd and prev_bd:
            # On ferme le gras sur le caractère PRÉCÉDENT
            modified_chars[i-1]['text'] = modified_chars[i-1]['text'] + "**"

        # --- Gestion de l'ITALIQUE (Simple étoile) ---
        if curr_it and not prev_it:
            curr['text'] = "*" + curr['text']
        if not curr_it and prev_it:
            # On ferme l'italique sur le caractère PRÉCÉDENT
            modified_chars[i-1]['text'] = modified_chars[i-1]['text'] + "*"

    # 3. Extraction avec le moteur de pdfplumber
    # On passe les caractères modifiés au moteur d'extraction de texte
    text = extract_text(       
        modified_chars, 
        layout=True, 
        use_text_flow=useTextFlow,
        x_tolerance=3, 
        y_tolerance=3)
    
    # Nettoyage des marqueurs vides type **** ou ** **
    text = text.replace("** **", " ").replace("**\n**", "\n")
    return text

def extract_text_with_italics(page_area, useTextFlow=False):
    """Reconstruit le texte d'une zone en préservant l'italique"""
    chars = page_area.extract_text(layout=True, useTextFlow=useTextFlow)
    if not chars:
        return ""

    styled_text = ""
    is_italic = False
    
    for char in chars:
        # Détection du style (ajustez le mot-clé selon votre PDF)
        char_is_italic = "Italic" in char['fontname'] or "-It" in char['fontname']
        
        # Transition : Entrée en italique
        if char_is_italic and not is_italic:
            styled_text += "*"
            is_italic = True
        # Transition : Sortie d'italique
        elif not char_is_italic and is_italic:
            # On gère l'espace avant l'étoile de fin si nécessaire
            if styled_text.endswith(" "):
                styled_text = styled_text[:-1] + "* "
            else:
                styled_text += "*"
            is_italic = False
            
        styled_text += char['text']
        
    # Fermeture si la ligne finit en italique
    if is_italic:
        styled_text += "*"
        
    return styled_text

def extract_with_sidebar_detection(pdf_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Analyse géométrique de : {os.path.basename(pdf_path)}...")
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # 1. Identifier les encarts via les rectangles (rects)
            # On filtre pour ne garder que les rectangles "significatifs" 
            # (ex: largeur > 100 et hauteur > 50 pour éviter les petites cases de stats)
            sidebars = [r for r in page.rects if r['width'] > 100 and r['height'] > 50]
            
            sidebar_bboxes = [(r['x0'], r['top'], r['x1'], r['bottom']) for r in sidebars]
            
            # 2. Extraire le texte des encarts
            sidebar_contents = []
            for bbox in sidebar_bboxes:
                #.within_bbox() crée une "sous-page" limitée au rectangle
                sidebar_area = page.within_bbox(bbox)
                text = extract_styled_layout(sidebar_area)
                if text:
                    sidebar_contents.append(text)

            # 3. Exclure les caractères des encarts de la page principale
            # On utilise.filter() : on ne garde que les objets (chars) 
            # qui ne sont PAS dans les bboxes des sidebars
            def is_outside_sidebars(obj):
                # On vérifie si le centre du caractère est dans un encart
                obj_mid_x = (obj['x0'] + obj['x1']) / 2
                obj_mid_y = (obj['top'] + obj['bottom']) / 2
                for (x0, top, x1, bottom) in sidebar_bboxes:
                    if x0 <= obj_mid_x <= x1 and top <= obj_mid_y <= bottom:
                        return False
                return True

            main_page_filtered = page.filter(is_outside_sidebars)

            # 4. Extraction finale du flux principal
            # On garde use_text_flow=True pour suivre l'ordre de l'Editeur Officiel
            # On récupère les extra_attrs pour votre future brique XML
            main_text = extract_styled_layout(main_page_filtered, useTextFlow=True)

            # Sauvegarde séparée pour faciliter le mapping XML
            # output_file = os.path.join(output_dir, f"page_{i+1}_structured.md")
            output_file = os.path.join(output_dir, f"young_empyreal_dragon.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# FLUX PRINCIPAL (STATS/BASE)\n\n{main_text}\n\n")
                if sidebar_contents:
                    f.write("# ENCARTS DETECTÉS (LORE/ANNEXES)\n\n")
                    f.write("\n\n---\n\n".join(sidebar_contents))

    print(f"Extraction terminée. Les fichiers sont dans {output_dir}")

if __name__ == "__main__":
    # extract_with_sidebar_detection("./pdf_sources/bandersnatch.pdf", "./output/subset_2")
    extract_with_sidebar_detection("./pdf_sources/monstre_unique.pdf", "./output/subset_5")