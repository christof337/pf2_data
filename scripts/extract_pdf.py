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

def is_real_data_table(rows):
    """Distingue un vrai tableau de données des lignes de traits ou de navigation."""
    if not rows or len(rows) < 2:
        return False
    first_row_cells = [c for c in rows[0] if c and c.strip()]
    # Au moins 2 colonnes dans le header pour exclure les encadrés de navigation (ex: "Sorts / A-C")
    if len(first_row_cells) < 2:
        return False
    # Traits lines : toutes les cellules non-vides sont en majuscules
    if all(c.strip() == c.strip().upper() for c in first_row_cells):
        return False
    return True

def table_to_markers(rows):
    """Convertit les lignes d'un tableau pdfplumber en block de markers [[TABLE_*]]."""
    lines = ['[[TABLE_START]]']
    if rows:
        header_cells = [str(c or '').replace('\n', ' ').replace('|', '\\|').strip() for c in rows[0]]
        lines.append('[[TABLE_HEADER]]' + '|'.join(header_cells))
        for row in rows[1:]:
            cells = [str(c or '').replace('\n', ' ').replace('|', '\\|').strip() for c in row]
            lines.append('[[TABLE_ROW]]' + '|'.join(cells))
    lines.append('[[TABLE_END]]')
    return '\n'.join(lines)

def inject_table_markers(text, table_rows):
    """Localise le bloc textuel du tableau dans `text` et le remplace par des markers."""
    if not table_rows:
        return text
    header_cells = [c for c in table_rows[0] if c and c.strip()]
    if not header_cells:
        return text

    # Chercher la ligne contenant la première cellule du header (peut être entourée de **)
    first_header = re.escape(header_cells[0].split('\n')[0].strip())
    header_match = re.search(rf'\n[^\n]*{first_header}[^\n]*\n', text)
    if not header_match:
        return text  # pas trouvé, on laisse tel quel

    start = header_match.start()

    # Trouver la fin : ancre sur les premiers mots de la dernière cellule non-vide
    last_row = table_rows[-1]
    last_cell = next((c.split('\n')[0][:30].strip() for c in reversed(last_row) if c and c.strip()), '')
    if last_cell:
        end_match = re.search(re.escape(last_cell), text[start:])
        end_pos = start + (end_match.end() if end_match else len(text) - start)
    else:
        end_pos = header_match.end()

    newline_pos = text.find('\n', end_pos)
    end = newline_pos + 1 if newline_pos != -1 else len(text)

    # Consommer les lignes de continuation de la dernière cellule
    # (lignes très indentées qui ne démarrent pas un nouveau bloc **/[[)
    while end < len(text):
        line_end = text.find('\n', end)
        if line_end == -1:
            line_end = len(text)
        line = text[end:line_end]
        if re.match(r'^ {10,}[^*\[\n\s]', line):
            end = line_end + 1
        else:
            break

    return text[:start] + '\n' + table_to_markers(table_rows) + '\n' + text[end:]

def extract_with_sidebar_detection(pdf_path, output_dir, pages=None):
    """Extrait le PDF vers un fichier Markdown structuré.

    pages : tuple (start, end) de numéros de pages 1-indexés inclus, ou None pour tout extraire.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Détermination du nom du fichier de sortie basé sur le PDF d'entrée
    base_name = os.path.basename(pdf_path).replace('.pdf', '.md')
    output_file = os.path.join(output_dir, base_name)

    pages_label = f" (pages {pages[0]}-{pages[1]})" if pages else ""
    print(f"Analyse géométrique et extraction de : {os.path.basename(pdf_path)}{pages_label}...")

    # Accumulateur global sous forme de liste (plus optimisé que la concaténation de strings)
    full_text = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        page_indices = range(len(pdf.pages))
        if pages:
            start_idx = max(0, pages[0] - 1)
            end_idx = min(len(pdf.pages), pages[1])
            page_indices = range(start_idx, end_idx)
        for i in page_indices:
            page = pdf.pages[i]
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

            # 4.5. Injection des markers de tableaux (avant la fusion des tirets)
            for tbl in page.find_tables():
                rows = tbl.extract()
                if is_real_data_table(rows):
                    main_text = inject_table_markers(main_text, rows)

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

    # Option --pages START-END (ex: --pages 322-325)
    page_range = None
    for arg in sys.argv[3:]:
        m = re.match(r'--pages\s*(\d+)-(\d+)', arg)
        if m:
            page_range = (int(m.group(1)), int(m.group(2)))
            break

    extract_with_sidebar_detection(input_pdf, output_directory, pages=page_range)