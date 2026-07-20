"""
pdf_loader.py

Responsabilité :
- Lire le PDF
- Extraire le texte page par page
- Sauvegarder le résultat dans pages.json

Auteur : LegalAI Mada
"""

from pathlib import Path
import json
import fitz  # PyMuPDF


class PDFLoader:

    def __init__(self, pdf_path: str):

        self.pdf_path = Path(pdf_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(
                f"❌ PDF introuvable : {self.pdf_path}"
            )

    def extract_pages(self):
        """
        Extrait le texte de chaque page.

        Retour :
        [
            {
                "page": 1,
                "text": "..."
            },
            ...
        ]
        """

        document = fitz.open(self.pdf_path)

        pages = []

        for page_number, page in enumerate(document, start=1):

            text = page.get_text("text")

            pages.append(
                {
                    "page": page_number,
                    "text": text.strip()
                }
            )

        document.close()

        return pages

    def save(self, output_path: str):

        pages = self.extract_pages()

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                pages,
                f,
                ensure_ascii=False,
                indent=4,
            )

        print("=" * 50)
        print("Extraction terminée")
        print(f"Pages extraites : {len(pages)}")
        print(f"Fichier créé : {output_path}")
        print("=" * 50)


if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent.parent

    pdf_path = BASE_DIR / "data" / "raw" / "Code_travail_2024.pdf"

    output_path = BASE_DIR / "data" / "processed" / "pages.json"

    loader = PDFLoader(pdf_path)

    loader.save(output_path)