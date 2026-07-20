"""
build_embeddings.py
------------------

Création des embeddings pour LegalAI.

Entrée:
    data/processed/chunks.json

Sortie:
    models/
        index.faiss
        chunks.pkl
"""


import json
import pickle
from pathlib import Path

import numpy as np
import faiss

from sentence_transformers import SentenceTransformer



# ======================================================
# CONFIGURATION
# ======================================================


CHUNKS_FILE = Path(
    "data/processed/chunks.json"
)


MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


OUTPUT_DIR = Path(
    "models"
)

OUTPUT_DIR.mkdir(
    exist_ok=True
)



# ======================================================
# CHARGEMENT DES CHUNKS
# ======================================================


print("=" * 50)
print("Chargement des chunks...")


with open(
    CHUNKS_FILE,
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)



texts = [
    chunk["page_content"]
    for chunk in chunks
]


print(
    f"{len(texts)} chunks chargés"
)



# ======================================================
# CHARGEMENT MODELE EMBEDDING
# ======================================================


print("\nChargement du modèle embedding...")


model = SentenceTransformer(
    MODEL_NAME
)



# ======================================================
# GENERATION EMBEDDINGS
# ======================================================


print("\nCréation des vecteurs...")


embeddings = model.encode(
    texts,
    show_progress_bar=True,
    normalize_embeddings=True
)



embeddings = np.array(
    embeddings
).astype(
    "float32"
)



print(
    "Dimension embeddings :",
    embeddings.shape
)



# ======================================================
# CREATION INDEX FAISS
# ======================================================


print("\nCréation index FAISS...")


dimension = embeddings.shape[1]


index = faiss.IndexFlatIP(
    dimension
)


index.add(
    embeddings
)



# ======================================================
# SAUVEGARDE
# ======================================================


faiss.write_index(
    index,
    str(
        OUTPUT_DIR /
        "index.faiss"
    )
)



with open(
    OUTPUT_DIR /
    "chunks.pkl",
    "wb"
) as f:

    pickle.dump(
        chunks,
        f
    )



print("\n" + "=" * 50)
print(" EMBEDDINGS TERMINES ")
print("=" * 50)

print(
    "Index : models/index.faiss"
)

print(
    "Chunks : models/chunks.pkl"
)