from lxml import etree

# ==========================================
# VALIDATION XSD
# ==========================================

def validate_xml(xml_path, xsd_path, silent=False):
    """Vérifie si le fichier XML est valide par rapport au schéma XSD.

    Si silent=True, supprime toute sortie console (utile pour le traitement en lot).
    """
    if not silent:
        print(f"[VALIDATION] Vérification de {xml_path} avec {xsd_path}...")
    try:
        with open(xsd_path, 'rb') as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)

        with open(xml_path, 'rb') as f:
            xml_doc = etree.parse(f)

        if schema.validate(xml_doc):
            if not silent:
                print("[VALIDATION] ✓ Le fichier XML est VALIDE.")
            return True
        else:
            if not silent:
                print("[VALIDATION] ✗ Le fichier XML est INVALIDE !")
                for error in schema.error_log:
                    print(f"    - Ligne {error.line}, colonne {error.column}: {error.message}")
            return False
    except Exception as e:
        if not silent:
            print(f"[VALIDATION] Erreur lors de la validation : {e}")
        return False