"""
rag.py
------

Moteur RAG LegalAI avec Groq API

FAISS :
Recherche des articles similaires

Groq :
Génération réponse juridique

AMÉLIORATIONS (v2) :
- Normalisation du texte (accents, casse, ponctuation)
- Correction automatique des fautes d'orthographe (via un vocabulaire
  extrait des chunks + difflib, sans dépendance externe)
- Dictionnaire de synonymes juridiques pour enrichir la question avant
  la recherche vectorielle (ex: "renvoi" -> "licenciement")
- Détection élargie de "article" (article, art., art, articles, n°, etc.)
  même mal orthographié ("artcle", "artikle"...)
- Recherche hybride : exacte + FAISS + garde-fou sur le score de similarité
"""


import os
import re
import pickle
import string
import unicodedata
from difflib import get_close_matches

import faiss

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from groq import Groq



# ==============================
# CONFIGURATION
# ==============================


load_dotenv()


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


client = Groq(
    api_key=GROQ_API_KEY
)



MODEL_EMBEDDING = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)


INDEX_PATH = (
    "models/index.faiss"
)


CHUNKS_PATH = (
    "models/chunks.pkl"
)


# Seuil en dessous duquel on considère que FAISS n'a rien trouvé de
# pertinent (distance L2 : plus petit = plus proche). À ajuster selon
# vos tests réels.
FAISS_MAX_DISTANCE = 1.2


# Nombre minimum de lettres pour tenter une correction orthographique
# sur un mot (on évite de "corriger" des mots trop courts).
MIN_WORD_LEN_FOR_CORRECTION = 4


# Seuil de similarité (0-1) pour accepter une correction orthographique.
SPELLING_CUTOFF = 0.78



# ==============================
# DICTIONNAIRE DE SYNONYMES JURIDIQUES
# ==============================

# Clé = terme canonique utilisé dans le Code du travail
# Valeur = liste de synonymes / variantes / formulations familières
# que les utilisateurs pourraient employer.
#
# -> À compléter au fur et à mesure des questions réelles des clients.

SYNONYMS = {
    "licenciement": [
        "renvoi", "renvoyer", "virer", "viré", "mise à pied",
        "rupture du contrat", "fin de contrat", "congédiement",
        "révocation",
    ],
    "démission": [
        "quitter le travail", "démissionner", "abandon de poste",
        "quitter mon emploi",
    ],
    "salaire": [
        "paie", "paye", "rémunération", "solde", "traitement",
        "salaire minimum", "smig",
    ],
    "congé": [
        "vacances", "repos", "permission", "absence autorisée",
    ],
    "congé de maladie": [
        "arrêt maladie", "congé maladie", "malade", "certificat médical",
    ],
    "congé de maternité": [
        "maternité", "grossesse", "accouchement",
    ],
    "heures supplémentaires": [
        "heure sup", "heures sup", "travail supplémentaire",
        "heures en plus",
    ],
    "contrat de travail": [
        "contrat", "cdd", "cdi", "engagement",
    ],
    "période d'essai": [
        "essai", "essai professionnel",
    ],
    "préavis": [
        "délai de préavis", "délai congé",
    ],
    "indemnité": [
        "indemnisation", "compensation", "dédommagement",
    ],
    "faute grave": [
        "faute lourde", "faute professionnelle grave",
    ],
    "employeur": [
        "patron", "chef d'entreprise", "société", "entreprise",
    ],
    "employé": [
        "salarié", "travailleur", "ouvrier", "personnel",
    ],
    "syndicat": [
        "délégué du personnel", "représentant syndical",
    ],
    "harcèlement": [
        "harcèlement moral", "harcèlement au travail", "intimidation",
    ],
    "accident de travail": [
        "accident du travail", "accident professionnel",
    ],
    "convention collective": [
        "accord collectif", "convention",
    ],
}

# Index inversé synonyme -> terme canonique, pour accélérer la recherche
_SYNONYM_LOOKUP = {}
for canonical, variants in SYNONYMS.items():
    for variant in variants:
        _SYNONYM_LOOKUP[variant.lower()] = canonical
    _SYNONYM_LOOKUP[canonical.lower()] = canonical



# ==============================
# CHARGEMENT MODELES
# ==============================


print("Chargement FAISS...")


index = faiss.read_index(
    INDEX_PATH
)



with open(
    CHUNKS_PATH,
    "rb"
) as f:

    chunks = pickle.load(f)



embedding_model = SentenceTransformer(
    MODEL_EMBEDDING
)


print("Construction du vocabulaire pour la correction orthographique...")


def _build_vocabulary(chunks):
    """
    Construit un ensemble de mots (vocabulaire) à partir de tous les
    chunks du Code du travail. Ce vocabulaire sert de référence pour
    corriger les fautes de frappe dans les questions des utilisateurs.
    """

    vocab = set()

    for chunk in chunks:

        text = chunk.get("page_content", "")

        text = _normalize_text(text)

        for word in text.split():

            if len(word) >= MIN_WORD_LEN_FOR_CORRECTION:

                vocab.add(word)

    return vocab


def _normalize_text(text):
    """
    Normalise un texte :
    - minuscules
    - suppression des accents
    - suppression de la ponctuation
    """

    text = text.lower()

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text if not unicodedata.combining(c)
    )

    text = text.translate(
        str.maketrans("", "", string.punctuation)
    )

    text = re.sub(r"\s+", " ", text).strip()

    return text


VOCABULARY = None  # sera rempli après chargement des chunks


print("RAG prêt")



# ==============================
# CORRECTION ORTHOGRAPHIQUE
# ==============================


def correct_spelling(question):
    """
    Corrige les fautes d'orthographe probables dans la question, en
    comparant chaque mot au vocabulaire extrait du Code du travail.
    Les mots déjà corrects, les nombres, et les mots courts sont
    laissés tels quels.
    """

    global VOCABULARY

    if VOCABULARY is None:
        VOCABULARY = _build_vocabulary(chunks)

    normalized = _normalize_text(question)

    corrected_words = []

    for word in normalized.split():

        if word.isdigit():
            corrected_words.append(word)
            continue

        if len(word) < MIN_WORD_LEN_FOR_CORRECTION:
            corrected_words.append(word)
            continue

        if word in VOCABULARY or word in _SYNONYM_LOOKUP:
            corrected_words.append(word)
            continue

        matches = get_close_matches(
            word,
            VOCABULARY | set(_SYNONYM_LOOKUP.keys()),
            n=1,
            cutoff=SPELLING_CUTOFF,
        )

        if matches:
            corrected_words.append(matches[0])
        else:
            corrected_words.append(word)

    return " ".join(corrected_words)



# ==============================
# EXPANSION PAR SYNONYMES
# ==============================


def expand_with_synonyms(question):
    """
    Enrichit la question avec les termes juridiques canoniques
    correspondant aux synonymes détectés, pour améliorer le rappel
    de la recherche vectorielle FAISS.

    Exemple :
        "je me suis fait virer" -> "je me suis fait virer licenciement"
    """

    normalized = _normalize_text(question)

    extra_terms = set()

    # Recherche des synonymes multi-mots (ex: "mise à pied")
    for variant, canonical in _SYNONYM_LOOKUP.items():

        variant_normalized = _normalize_text(variant)

        if variant_normalized and variant_normalized in normalized:

            extra_terms.add(canonical)

    if not extra_terms:
        return question

    return question + " " + " ".join(sorted(extra_terms))



# ==============================
# RECHERCHE DOCUMENTS
# ==============================


# Regex tolérante : "article", "art.", "art", "articles", avec ou sans
# "n°"/"numero"/"num", même partiellement mal orthographié
ARTICLE_PATTERN = re.compile(
    r"\bart[a-z]{0,7}\.?\s*(?:n[°o]?\.?\s*|num[eé]ro\s*)?(\d+)",
    re.IGNORECASE,
)


def _find_article_number(question):
    """
    Essaie de détecter un numéro d'article dans la question, en
    tolérant les variantes ("article", "art.", "artcle", "art n°"...).
    """

    match = ARTICLE_PATTERN.search(question.lower())

    if match:
        return int(match.group(1))

    return None


def search_documents(
        question,
        k=5
):

    """
    Recherche hybride :

    1. Correction orthographique + expansion par synonymes
    2. Recherche exacte article XX (tolérante aux fautes)
    3. Recherche vectorielle FAISS (avec garde-fou sur le score)
    """

    corrected_question = correct_spelling(question)
    enriched_question = expand_with_synonyms(corrected_question)

    if corrected_question != _normalize_text(question):
        print(f"[Correction orthographique] '{question}' -> '{corrected_question}'")

    if enriched_question != corrected_question:
        print(f"[Expansion synonymes] -> '{enriched_question}'")


    # ==========================
    # Recherche article exacte
    # ==========================


    article_num = _find_article_number(question)


    if article_num is not None:


        exact_results = [
            chunk
            for chunk in chunks
            if chunk["metadata"]["article_num"]
            == article_num
        ]



        if exact_results:


            print(
                f"[Recherche exacte] Article {article_num}"
            )


            return exact_results



    # ==========================
    # Recherche FAISS
    # ==========================


    print(
        "[Recherche FAISS]"
    )


    vector = embedding_model.encode(
        [enriched_question],
        normalize_embeddings=True
    )


    vector = vector.astype(
        "float32"
    )



    scores, ids = index.search(
        vector,
        k
    )



    results = []



    for score, idx in zip(scores[0], ids[0]):

        if idx == -1:
            continue

        # Garde-fou : on ignore les résultats trop éloignés
        if score > FAISS_MAX_DISTANCE:
            continue

        results.append(
            chunks[idx]
        )


    if not results:
        print("[Recherche FAISS] Aucun résultat suffisamment pertinent")


    return results




# ==============================
# GENERATION GROQ
# ==============================


def ask_legal_ai(question):


    documents = search_documents(
        question
    )


    if not documents:

        return (
            "Je ne trouve pas cette information dans le Code du "
            "travail malgache. Pouvez-vous reformuler votre question "
            "ou préciser l'article concerné ?"
        )



    context = "\n\n".join(
        [
            doc["page_content"]
            for doc in documents
        ]
    )



    sources = "\n".join(
        [
            f"- Article {doc['metadata']['article_num']}"
            for doc in documents
        ]
    )



    prompt = f"""

Tu es LegalAI, un assistant spécialisé
dans le Code du travail malgache.

Règles :

- Réponds uniquement avec les informations
  présentes dans le contexte.
- Cite les articles utilisés.
- Si la question contient des fautes d'orthographe
  ou des synonymes, comprends l'intention de l'utilisateur
  et réponds normalement.
- Si l'information n'est pas présente,
  dis clairement que tu ne trouves pas
  cette information dans le Code du travail.

CONTEXTE JURIDIQUE :

{context}


SOURCES :

{sources}


QUESTION (originale de l'utilisateur) :

{question}


Réponse :
"""



    response = client.chat.completions.create(


        model="llama-3.3-70b-versatile",


        messages=[

            {
                "role":"system",
                "content":
                "Tu es un assistant juridique précis."
            },


            {
                "role":"user",
                "content":prompt
            }

        ],


        temperature=0.2

    )



    return response.choices[0].message.content





# ==============================
# MODE CHAT TERMINAL
# ==============================


if __name__ == "__main__":


    print("\n==============================")
    print(" LegalAI - Chatbot Droit du travail")
    print("==============================")

    print(
        "Tapez 'exit' pour quitter\n"
    )



    while True:


        question = input(
            "Vous : "
        )



        if question.lower() in [
            "exit",
            "quit",
            "q"
        ]:


            print(
                "Au revoir !"
            )

            break



        if question.strip() == "":

            continue



        answer = ask_legal_ai(
            question
        )



        print(
            "\nLegalAI :"
        )


        print(
            answer
        )



        print(
            "\n" + "-"*50
        )