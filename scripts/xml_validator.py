import xmlschema

# ==========================================
# VALIDATION XSD 1.1
# ==========================================

def validate_xml(xml_path, xsd_path, silent=False):
    """Vérifie si le fichier XML est valide par rapport au schéma XSD 1.1.

    Utilise xmlschema (XSD 1.1 natif) — les xs:assert du schéma sont appliqués directement.
    Si silent=True, supprime toute sortie console (utile pour le traitement en lot).
    """
    if not silent:
        print(f"[VALIDATION] Vérification de {xml_path} avec {xsd_path}...")
    try:
        schema = xmlschema.XMLSchema11(xsd_path)
        errors = list(schema.iter_errors(xml_path))

        if errors:
            if not silent:
                print("[VALIDATION] ✗ Le fichier XML est INVALIDE !")
                for error in errors:
                    print(f"    - {error.reason}")
            return False

        if not silent:
            print("[VALIDATION] ✓ Le fichier XML est VALIDE.")
        return True
    except Exception as e:
        if not silent:
            print(f"[VALIDATION] Erreur lors de la validation : {e}")
        return False
