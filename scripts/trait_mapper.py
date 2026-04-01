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

def parse_traits_md(content, format="ldm"):
    """
    Extrait la liste des traits depuis le Markdown.

    format="ldm" (défaut) :
        Livre des Monstres — section "TRAITS DES CRÉATURES", toutes les entrées **Nom.**
    format="ldj" :
        Livre des Joueurs — section GLOSSAIRE, uniquement les entrées **Nom (trait).**
        Le suffixe " (trait)" est supprimé du nom ; les numéros de page en fin de
        description sont tronqués.
    """
    traits_data = []
    print(f"[PARSING] Début de l'analyse des traits (format={format})...")

    # 0. Normalisation : tiret non-sécable (U+2011) → tiret ordinaire
    content = content.replace('\u2011', '-')

    if format == "ldj":
        return _parse_traits_ldj(content, traits_data)
    else:
        return _parse_traits_ldm(content, traits_data)


def _parse_traits_ldm(content, traits_data):
    """Parser format LdM : section TRAITS DES CRÉATURES … RITUELS."""
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

        if len(name) > 40:
            continue

        trait_id = generate_slug("trait", name)
        traits_data.append({'id': trait_id, 'name': name, 'description': desc})
        count += 1

    print(f"[PARSING] ✓ {count} traits détectés et extraits.")
    return traits_data


def _parse_traits_ldj(content, traits_data):
    """
    Parser format LdJ : glossaire mixte, seules les entrées suffixées (trait) sont retenues.

    Format réel dans le MD :
      **Nom **(trait). Description... numéros de page
      **Nom** (trait). Description... numéros de page

    Le `(trait)` apparaît APRÈS le `**` fermant, pas à l'intérieur.
    La regex ci-dessous encode ce format directement : le filtre est structurel,
    pas textuel — pas besoin de vérifier '(trait)' dans le nom capturé.
    """
    # Regex adaptée au format LdJ : **Nom **(trait). ou **Nom** (trait).
    pattern = (
        r'[ \t]*\*\*([A-ZÀ-Ÿa-zà-ÿ\s\-]+?)\s*\*\*\s*\(trait\)\.\s*'
        r'(.*?)(?=(?:[ \t]*\*\*[A-ZÀ-Ÿa-zà-ÿ]|\Z))'
    )
    matches = re.finditer(pattern, content, flags=re.MULTILINE | re.DOTALL)

    count = 0
    for m in matches:
        name = clean_text(m.group(1))

        if len(name) > 40:
            continue

        desc_raw = clean_text(m.group(2))

        # 1. Normaliser les marqueurs gras dans les plages de pages (**‑**, **,**)
        desc_raw = re.sub(r'\*\*[\-–,]\*\*', '-', desc_raw)

        # 2. Corriger les césures PDF : "réac- tions" → "réactions"
        desc_raw = re.sub(r'(\w)- (\w)', r'\1\2', desc_raw)

        # 3. Supprimer les numéros de page en fin de description
        #    Motifs : "215", "LMJ 276", "10, 402-403", "p. 76–77"
        #    Passe 1 : refs en fin après du contenu textuel
        desc = re.sub(
            r'(?:\s+(?:(?:p\.\s*)?(?:LMJ\s+)?[\d][\d\-–,\s]*)+)+$',
            '',
            desc_raw
        ).strip()
        #    Passe 2 : description entièrement composée de refs de page (ex: "LMJ 276" → "")
        desc = re.sub(
            r'^(?:(?:p\.\s*)?(?:LMJ\s+)?[\d][\d\-–,\s]*|LMJ)+$',
            '',
            desc
        ).strip()

        trait_id = generate_slug("trait", name)
        traits_data.append({'id': trait_id, 'name': name, 'description': desc})
        count += 1

    print(f"[PARSING] ✓ {count} traits (trait) retenus depuis le glossaire LdJ.")
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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", default="./output/subset_3/traits_LdM.md")
    ap.add_argument("output", nargs="?", default="./output/subset_3/traits.xml")
    ap.add_argument("--format", choices=["ldm", "ldj"], default="ldm",
                    help="Format source : ldm (Livre des Monstres, défaut) ou ldj (Livre des Joueurs)")
    args = ap.parse_args()

    input_file = args.input
    output_file = args.output

    print("="*60)
    print("DÉBUT DU TRAITEMENT (TRAIT MAPPER)")
    print("="*60 + "\n")

    start_total = time.time()

    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        traits_data = parse_traits_md(md_content, format=args.format)
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