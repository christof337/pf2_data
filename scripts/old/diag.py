import pdfplumber

with pdfplumber.open("./pdf_sources/monstre_unique.pdf") as pdf:
    page = pdf.pages[0]
    # Liste unique des polices présentes sur la page
    fonts = set(c['fontname'] for c in page.chars)
    print("Polices détectées :", fonts)