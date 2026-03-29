from lxml import etree

# ==========================================
# VALIDATION XSD
# ==========================================

def validate_xml(xml_path, xsd_path):
    """Vérifie si le fichier XML est valide par rapport au schéma XSD."""
    print(f"[VALIDATION] Vérification de {xml_path} avec {xsd_path}...")
    try:
        with open(xsd_path, 'rb') as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)
        
        with open(xml_path, 'rb') as f:
            xml_doc = etree.parse(f)
            
        if schema.validate(xml_doc):
            print("[VALIDATION] ✓ Le fichier XML est VALIDE.")
            return True
        else:
            print("[VALIDATION] ✗ Le fichier XML est INVALIDE !")
            for error in schema.error_log:
                print(f"    - Ligne {error.line}, colonne {error.column}: {error.message}")
            return False
    except Exception as e:
        print(f"[VALIDATION] Erreur lors de la validation : {e}")
        return False