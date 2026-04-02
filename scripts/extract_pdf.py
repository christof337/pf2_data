import sys
import pdfplumber
import os
import re
from datetime import datetime
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
            # On ferme le gras sur le caractère PRÉCÉDENT, avant l'espace trailing
            t = modified_chars[i-1]['text']
            modified_chars[i-1]['text'] = t.rstrip(' ') + "**" + (" " if t.endswith(' ') else "")

        # --- Gestion de l'ITALIQUE (Underscore) ---
        if curr_it and not prev_it:
            curr['text'] = "_" + curr['text']
        if not curr_it and prev_it:
            # On ferme l'italique sur le caractère PRÉCÉDENT, avant l'espace trailing
            t = modified_chars[i-1]['text']
            modified_chars[i-1]['text'] = t.rstrip(' ') + "_" + (" " if t.endswith(' ') else "")

    # 3. Extraction avec le moteur de pdfplumber
    text = extract_text(       
        modified_chars, 
        layout=True, 
        use_text_flow=useTextFlow,
        x_tolerance=3, 
        y_tolerance=3)
    
    # Nettoyage des marqueurs vides type **** ou ** **
    text = text.replace("****", "").replace("** **", " ").replace("**\n**", "\n")
    text = text.replace("_ _", " ").replace("_\n_", "\n")
    return text

def extract_text_with_italics(page_area, useTextFlow=False):
    """Reconstruit le texte d'une zone en préservant l'italique"""
    chars = page_area.extract_text(layout=True, useTextFlow=useTextFlow)
    if not chars:
        return ""

    styled_text = ""
    is_italic = False
    
    for char in chars:
        char_is_italic = "Italic" in char['fontname'] or "-It" in char['fontname']
        
        if char_is_italic and not is_italic:
            styled_text += "*"
            is_italic = True
        elif not char_is_italic and is_italic:
            if styled_text.endswith(" "):
                styled_text = styled_text[:-1] + "* "
            else:
                styled_text += "*"
            is_italic = False
            
        styled_text += char['text']
        
    if is_italic:
        styled_text += "*"
        
    return styled_text

def extract_with_sidebar_detection(pdf_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Détermination du nom du fichier de sortie basé sur le PDF d'entrée
    base_name = os.path.basename(pdf_path).replace('.pdf', '.md')
    output_file = os.path.join(output_dir, base_name)

    print(f"Analyse géométrique et extraction de : {os.path.basename(pdf_path)}...")
    
    # Accumulateur global sous forme de liste (plus optimisé que la concaténation de strings)
    full_text = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            print(f"  -> Traitement de la page {page_num}/{total_pages}")
            
            # Injection du marqueur sémantique strict
            page_content = [f"[[PAGE {page_num}]]\n\n"]
            
            # 1. Identifier les encarts via les rectangles
            sidebars = [r for r in page.rects if r['width'] > 100 and r['height'] > 50]
            sidebar_bboxes = [(r['x0'], r['top'], r['x1'], r['bottom']) for r in sidebars]
            
            # 2. Extraire le texte des encarts
            # Clip bboxes to page boundaries to avoid ValueError
            page_bbox = (0, 0, page.width, page.height)
            valid_bboxes = []
            for bbox in sidebar_bboxes:
                x0, top, x1, bottom = bbox
                cx0 = max(x0, page_bbox[0])
                ctop = max(top, page_bbox[1])
                cx1 = min(x1, page_bbox[2])
                cbottom = min(bottom, page_bbox[3])
                if cx1 > cx0 and cbottom > ctop:
                    valid_bboxes.append((cx0, ctop, cx1, cbottom))
            sidebar_bboxes = valid_bboxes
            sidebar_contents = []
            for bbox in sidebar_bboxes:
                try:
                    sidebar_area = page.within_bbox(bbox)
                    text = extract_styled_layout(sidebar_area)
                    if text:
                        sidebar_contents.append(text)
                except Exception as e:
                    print(f"    [WARN] Encart ignoré (page {page_num}): {e}")

            # 3. Exclure les caractères des encarts de la page principale
            def is_outside_sidebars(obj):
                obj_mid_x = (obj['x0'] + obj['x1']) / 2
                obj_mid_y = (obj['top'] + obj['bottom']) / 2
                for (x0, top, x1, bottom) in sidebar_bboxes:
                    if x0 <= obj_mid_x <= x1 and top <= obj_mid_y <= bottom:
                        return False
                return True

            main_page_filtered = page.filter(is_outside_sidebars)

            # 4. Extraction finale du flux principal
            main_text = extract_styled_layout(main_page_filtered, useTextFlow=True)

            # 5. Fusion des coupures de mots hyphenées (avant tout traitement)
            # Remplace "mot-\n  " par "mot" SEULEMENT si suivi d'une minuscule (accentuée ou non)
            main_text = re.sub(r'-\n\s+([a-zàâäæçéèêëîïôöœùûüÿ])', r'\1', main_text)

            # 6. Construction du bloc de la page
            page_content.append("# FLUX PRINCIPAL (STATS/BASE)\n")
            page_content.append(f"{main_text}\n" if main_text else "\n")
            
            if sidebar_contents:
                page_content.append("\n# ENCARTS DETECTÉS (LORE/ANNEXES)\n")
                page_content.append("\n\n---\n\n".join(sidebar_contents))
                page_content.append("\n")
                
            page_content.append("\n") # Espace avant la page suivante
            
            # Ajout au buffer global
            full_text.append("".join(page_content))
            
            # 6. Optimisation mémoire vitale (purge les caches de chars, rects, etc.)
            page.flush_cache()

    # Écriture de l'intégralité du document consolidé
    metadata = (
        f"[[METADATA]]\n"
        f"source: {os.path.abspath(pdf_path)}\n"
        f"generated: {datetime.now().isoformat(timespec='seconds')}\n"
        f"[[/METADATA]]\n"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(metadata + "".join(full_text))

    print(f"Extraction terminée. Fichier consolidé disponible ici : {output_file}")

if __name__ == "__main__":
    input_pdf = sys.argv[1] if len(sys.argv) > 1 else "./pdf_sources/monstre_unique.pdf"
    output_directory = sys.argv[2] if len(sys.argv) > 2 else "./output/subset_1"

    extract_with_sidebar_detection(input_pdf, output_directory)