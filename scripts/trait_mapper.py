import re
import os
import sys
import time
from lxml import etree
from xml_validator import validate_xml
from slug_generator import generate_slug

# ==========================================
# UTILITAIRES
# ==========================================

def clean_text(text):
    """Nettoie les sauts de ligne et espaces superflus de pdfplumber."""
    return re.sub(r'\s+', ' ', text).strip()



# ==========================================
# PARSING SPÉCIFIQUE TRAITS
# ==========================================

def parse_traits_md(content):
    """
    Extrait la liste des traits depuis le Markdown.
    Ignore le texte avant "TRAITS DES CRÉATURES",
    saute les textes d'introduction, et s'arrête avant "RITUELS".
    """
    traits_data = []
    print("[PARSING] Début de l'analyse des traits...")

    # 0. Normalisation : tiret non-sécable (U+2011) → tiret ordinaire
    # Certains PDFs (LdM complet) utilisent ‑ dans les noms de traits (âme‑en‑peine, etc.)
    content = content.replace('\u2011', '-')

    # 1. Isolation de la zone utile (DÉBUT)
    start_match = re.search(r'TRAITS\s+DES\s+CRÉATURES', content)
    if start_match:
        content = content[start_match.end():]

    # 2. Isolation de la zone utile (FIN)
    if "RITUELS" in content:
        content = content.split("RITUELS")[0]

    # 3. Regex de capture des traits
    pattern = r'^[ \t]*\*\*([A-ZÀ-Ÿa-zà-ÿ\s\-]+?)\.\s*\*\*\s*(.*?)(?=(?:^[ \t]*\*\*|\Z))'
    
    matches = re.finditer(pattern, content, flags=re.MULTILINE | re.DOTALL)
    
    count = 0
    for m in matches:
        name = clean_text(m.group(1))
        desc = clean_text(m.group(2))
        
        # Sécurité : on ignore les captures accidentelles trop longues pour être un nom de trait
        if len(name) > 40:
            continue
            
        # Génération de l'ID dynamique
        trait_id = generate_slug("trait", name)
            
        traits_data.append({
            'id': trait_id,
            'name': name,
            'description': desc
        })
        count += 1
        
    print(f"[PARSING] ✓ {count} traits détectés et extraits.")
    return traits_data

# ==========================================
# GÉNÉRATION XML
# ==========================================

def generate_trait_xml(traits_data, output_path):
    """
    Construit l'arbre XML à partir de la liste des traits
    et l'écrit dans le fichier de sortie.
    """
    start_time = time.time()
    print("[XML] Début de la génération du fichier XML...")
    
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    root = etree.Element("traits", nsmap={'xsi': XSI_NS})
    
    root.set(f"{{{XSI_NS}}}noNamespaceSchemaLocation", "../../schema/trait.xsd")

    for t in traits_data:
        # Ajout de l'attribut id directement dans la balise <trait>
        trait_elem = etree.SubElement(root, "trait", id=t['id'])
        
        etree.SubElement(trait_elem, "name").text = t['name']
        etree.SubElement(trait_elem, "description").text = t['description']

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree = etree.ElementTree(root)
    
    tree.write(output_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    
    print(f"[XML] ✓ Fichier sauvegardé à {output_path} - {time.time() - start_time:.3f}s")

# ==========================================
# EXÉCUTION PRINCIPALE
# ==========================================

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "./output/subset_3/traits_LdM.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./output/subset_3/traits.xml"

    print("="*60)
    print("DÉBUT DU TRAITEMENT (TRAIT MAPPER)")
    print("="*60 + "\n")

    start_total = time.time()

    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        traits_data = parse_traits_md(md_content)
        generate_trait_xml(traits_data, output_file)

        xsd_file = "./schema/trait.xsd"
        if os.path.exists(output_file) and os.path.exists(xsd_file):
            validate_xml(output_file, xsd_file)
        else:
            print(f"[WARNING] Fichier XSD introuvable ({xsd_file}), validation ignorée.")
    else:
        print(f"[ERREUR] Le fichier d'entrée '{input_file}' est introuvable.")

    total_elapsed = time.time() - start_total
    print(f"\n[MAIN] Temps total de traitement: {total_elapsed:.3f}s")
    print("="*60)