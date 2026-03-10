import pdfplumber
import os

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
                text = sidebar_area.extract_text(layout=True)
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
            main_text = main_page_filtered.extract_text(
                layout=True, 
                use_text_flow=True
            )

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
    extract_with_sidebar_detection("./pdf_sources/monstre_unique.pdf", "./output/subset_3")