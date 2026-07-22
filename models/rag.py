import os
import re
import pickle
import string
import unicodedata
import logging
import time
from pathlib import Path
from difflib import get_close_matches

import faiss
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from groq import Groq, RateLimitError, APIError, APIConnectionError

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("RAG FILE =", __file__)

# ==============================
# CONFIGURATION
# ==============================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(dotenv_path=BASE_DIR.parent / ".env")
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY manquant. Vérifiez votre fichier .env "
        "(GROQ_API_KEY=votre_cle_ici)."
    )

client = Groq(api_key=GROQ_API_KEY)

MODEL_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_RERANKER = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

INDEX_PATH = str(BASE_DIR / "index.faiss")
CHUNKS_PATH = str(BASE_DIR / "chunks.pkl")

PRIMARY_MODEL = "llama-3.1-8b-instant"
FALLBACK_MODEL = "llama-3.3-70b-versatile"

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
DEFAULT_MAX_TOKENS = 800

# ==============================
# SEUILS FAISS
# ==============================

FAISS_TOP_K_CANDIDATES = 30
FAISS_TOP_K_WIDE = 40
RERANK_TOP_N = 8
RERANK_TOP_N_WIDE = 10

FAISS_MAX_DISTANCE = float(os.getenv("FAISS_MAX_DISTANCE", "1.2"))
FAISS_MIN_SIMILARITY = float(os.getenv("FAISS_MIN_SIMILARITY", "0.45"))
LOW_CONFIDENCE_THRESHOLD = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.55"))

MIN_WORD_LEN_FOR_CORRECTION = 4
SPELLING_CUTOFF = 0.85

COMMON_FRENCH_WORDS = {
    "combien", "comment", "pourquoi", "quand", "lequel", "laquelle",
    "lesquels", "lesquelles", "quelle", "quelles", "quel", "quels",
    "avant", "apres", "pendant", "depuis", "jusqu", "jusque",
    "dure", "dur", "duree", "durée",
    "parle", "parles", "parlent", "parler",
    "toujours", "jamais", "encore", "aussi", "ainsi", "alors",
    "donc", "cependant", "pourtant", "malgre", "beaucoup",
    "plusieurs", "certains", "certaines", "chaque", "quelque",
    "quelques", "vraiment", "exactement", "actuellement",
    "normalement", "legalement", "personnellement", "egalement",
    "seulement", "simplement", "rapidement", "recemment",
    "maintenant", "aujourd", "hier", "demain", "bonjour", "bonsoir",
    "merci", "svp", "possible", "impossible", "obligatoire",
    "facultatif", "gratuit", "payant",
    "quels", "quelles", "quel", "quelle", "comment", "pourquoi",
    "quand", "ou", "où", "que", "quoi", "qui", "dont",
}

# ==============================
# DICTIONNAIRE DE SYNONYMES JURIDIQUES
# ==============================

SYNONYMS = {
    "licenciement": [
        "renvoi", "renvoyer", "virer", "viré", "mise à pied",
        "rupture du contrat", "fin de contrat", "congédiement",
        "révocation", "mettre dehors", "mettre à la porte",
    ],
    "démission": [
        "quitter le travail", "démissionner", "abandon de poste",
        "quitter mon emploi", "quitter mon travail", "partir de mon travail",
    ],
    "salaire": [
        "paie", "paye", "rémunération", "solde", "traitement",
        "salaire minimum", "smig", "argent du travail",
    ],
    "congé": [
        "conges", "congé", "congés", "congé payé", "congés payés",
        "repos annuel", "jours de repos", "jours libres", "vacances",
        "permission", "absence autorisée", "absence",
    ],
    "congé de maladie": [
        "arrêt maladie", "congé maladie", "malade", "certificat médical",
    ],
    "congé de maternité": [
        "maternité", "grossesse", "accouchement",
    ],
    "heures supplémentaires": [
        "heure sup", "heures sup", "travail supplémentaire", "heures en plus",
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
        "patron", "chef d'entreprise", "société", "entreprise", "chef", "boss",
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

_SYNONYM_LOOKUP = {}
for canonical, variants in SYNONYMS.items():
    for variant in variants:
        _SYNONYM_LOOKUP[variant.lower()] = canonical
    _SYNONYM_LOOKUP[canonical.lower()] = canonical

# ==============================
# CHARGEMENT MODELES
# ==============================

print("Chargement FAISS...")
print(f"[Chemins] INDEX_PATH={INDEX_PATH}")
print(f"[Chemins] CHUNKS_PATH={CHUNKS_PATH}")

if not os.path.exists(INDEX_PATH):
    raise FileNotFoundError(f"Index FAISS introuvable : {INDEX_PATH}")
if not os.path.exists(CHUNKS_PATH):
    raise FileNotFoundError(f"Fichier chunks introuvable : {CHUNKS_PATH}")

index = faiss.read_index(INDEX_PATH)

try:
    IS_SIMILARITY_METRIC = (index.metric_type == faiss.METRIC_INNER_PRODUCT)
except AttributeError:
    IS_SIMILARITY_METRIC = False

print(f"Type de métrique FAISS détecté : {'similarité (produit scalaire)' if IS_SIMILARITY_METRIC else 'distance (L2)'}")

with open(CHUNKS_PATH, "rb") as f:
    chunks = pickle.load(f)

embedding_model = SentenceTransformer(MODEL_EMBEDDING)

print("Chargement du reranker...")
try:
    reranker_model = CrossEncoder(MODEL_RERANKER)
    RERANKER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Reranker indisponible, on continue sans ({e})")
    reranker_model = None
    RERANKER_AVAILABLE = False

print("Construction du vocabulaire pour la correction orthographique...")


def _normalize_text(text):
    """Normalise un texte pour la comparaison uniquement."""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_vocabulary(chunks):
    """Construit un ensemble de mots à partir des chunks."""
    vocab = set()
    for chunk in chunks:
        text = chunk.get("page_content", "")
        text = _normalize_text(text)
        for word in text.split():
            if len(word) >= MIN_WORD_LEN_FOR_CORRECTION:
                vocab.add(word)
    return vocab


VOCABULARY = None

print("RAG prêt")
print("VERSION RAG API ACTIVE")

# ==============================
# CORRECTION ORTHOGRAPHIQUE
# ==============================

def correct_spelling(question):
    """Corrige les fautes d'orthographe dans la question."""
    global VOCABULARY

    if VOCABULARY is None:
        VOCABULARY = _build_vocabulary(chunks)

    corrected_words = []

    for original_word in question.split():
        clean = _normalize_text(original_word)

        if not clean or clean.isdigit():
            corrected_words.append(original_word)
            continue

        if len(clean) < MIN_WORD_LEN_FOR_CORRECTION:
            corrected_words.append(original_word)
            continue

        if clean in COMMON_FRENCH_WORDS:
            corrected_words.append(original_word)
            continue

        if clean in VOCABULARY or clean in _SYNONYM_LOOKUP:
            corrected_words.append(original_word)
            continue

        matches = get_close_matches(
            clean,
            VOCABULARY | set(_SYNONYM_LOOKUP.keys()),
            n=1,
            cutoff=SPELLING_CUTOFF,
        )

        if matches and matches[0][:2] == clean[:2]:
            corrected_words.append(matches[0])
        else:
            corrected_words.append(original_word)

    return " ".join(corrected_words)

# ==============================
# EXPANSION PAR SYNONYMES
# ==============================

def expand_with_synonyms(question):
    """Enrichit la question avec les termes juridiques canoniques."""
    normalized = _normalize_text(question)
    normalized_words = set(normalized.split())
    extra_terms = set()

    for variant, canonical in _SYNONYM_LOOKUP.items():
        variant_normalized = _normalize_text(variant)
        if not variant_normalized:
            continue

        pattern = r"\b" + re.escape(variant_normalized) + r"\b"
        if re.search(pattern, normalized):
            extra_terms.add(canonical)

    extra_terms = {
        term for term in extra_terms
        if _normalize_text(term) not in normalized_words
        and not re.search(r"\b" + re.escape(_normalize_text(term)) + r"\b", normalized)
    }

    if not extra_terms:
        return question

    return question + " " + " ".join(sorted(extra_terms))

# ==============================
# RECHERCHE DOCUMENTS
# ==============================

ARTICLE_PATTERN = re.compile(
    r"\bl?['’]?\s*(?:article|art)\.?\s*(?:n[°o]?\.?\s*|num[eé]ro\s*)?(\d+)",
    re.IGNORECASE,
)


def _find_article_number(question):
    """Détecte un numéro d'article dans la question."""
    match = ARTICLE_PATTERN.search(question.lower())
    if match:
        return int(match.group(1))
    return None


DURATION_KEYWORDS = {
    "combien", "duree", "jours", "jour", "mois", "semaines",
    "semaine", "delai", "delais", "annees", "annee", "ans",
}


def _needs_wider_search(corrected_question):
    words = set(_normalize_text(corrected_question).split())
    return bool(words & DURATION_KEYWORDS) or _is_general_question(corrected_question)


GENERAL_QUESTION_KEYWORDS = {
    "droits", "droit", "obligations", "obligation", "regles", "règles",
    "tout", "generalites", "généralités",
}
GENERAL_QUESTION_PATTERNS = [
    re.compile(r"\bquels?\s+sont\b", re.IGNORECASE),
    re.compile(r"\bquelles?\s+sont\b", re.IGNORECASE),
    re.compile(r"\bque\s+dit\s+le\s+code\b", re.IGNORECASE),
]


def _is_general_question(question):
    normalized = _normalize_text(question)
    words = set(normalized.split())

    if words & GENERAL_QUESTION_KEYWORDS:
        return True

    return any(p.search(question) for p in GENERAL_QUESTION_PATTERNS)


def _dedupe_by_article(ranked_pairs, top_n):
    """
    Parcourt les paires (chunk, score) déjà triées par pertinence décroissante
    et ne garde qu'un seul chunk par numéro d'article (le mieux classé),
    jusqu'à obtenir top_n articles distincts.
    """
    seen_articles = set()
    deduped = []

    for chunk, score in ranked_pairs:
        article_num = chunk.get("metadata", {}).get("article_num", None)

        if article_num is not None and article_num in seen_articles:
            continue

        if article_num is not None:
            seen_articles.add(article_num)

        deduped.append((chunk, score))

        if len(deduped) >= top_n:
            break

    return deduped


def _rerank(question, candidate_chunks, top_n=RERANK_TOP_N):
    """
    Rerank les chunks candidats avec un cross-encoder pour affiner la
    pertinence sémantique, puis déduplique par article.
    """
    if not candidate_chunks:
        return [], []

    if not RERANKER_AVAILABLE:
        ranked = [(c, None) for c in candidate_chunks]
        deduped = _dedupe_by_article(ranked, top_n)
        return [c for c, _ in deduped], [s for _, s in deduped]

    pairs = [(question, c.get("page_content", "")) for c in candidate_chunks]
    scores = reranker_model.predict(pairs)

    ranked = sorted(zip(candidate_chunks, scores), key=lambda x: x[1], reverse=True)
    deduped = _dedupe_by_article(ranked, top_n)

    reranked_chunks = [c for c, _ in deduped]
    reranked_scores = [float(s) if s is not None else None for _, s in deduped]

    print(f"[Reranker] Top {len(reranked_chunks)} après reranking (dédupliqué) : "
          f"{[c['metadata'].get('article_num') for c in reranked_chunks]}")

    return reranked_chunks, reranked_scores


def search_documents(question, k=FAISS_TOP_K_CANDIDATES):
    """
    Recherche hybride :
    1. Correction orthographique + expansion par synonymes
    2. Recherche exacte article XX
    3. Recherche vectorielle FAISS (candidats larges)
    4. Reranking cross-encoder (précision fine)

    Retourne (results, corrected_question, low_confidence, max_score)
    """

    corrected_question = correct_spelling(question)
    enriched_question = expand_with_synonyms(corrected_question)

    if corrected_question != question:
        print(f"[Correction orthographique] '{question}' -> '{corrected_question}'")

    if enriched_question != corrected_question:
        print(f"[Expansion synonymes] -> '{enriched_question}'")

    top_n = RERANK_TOP_N

    if _needs_wider_search(corrected_question):
        k = max(k, FAISS_TOP_K_WIDE)
        top_n = RERANK_TOP_N_WIDE
        print(f"[Recherche élargie] question de durée/délai détectée (k={k}, top_n={top_n})")

    # ==========================
    # Recherche article exacte
    # ==========================

    article_num = _find_article_number(question)
    if article_num is None:
        article_num = _find_article_number(corrected_question)

    if article_num is not None:
        exact_results = [
            chunk for chunk in chunks
            if chunk["metadata"]["article_num"] == article_num
        ]

        if exact_results:
            print(f"[Recherche exacte] Article {article_num}")
            return exact_results[:1], corrected_question, False, None

    # ==========================
    # Recherche FAISS (candidats larges)
    # ==========================

    print("[Recherche FAISS]")

    vector = embedding_model.encode(
        [enriched_question],
        normalize_embeddings=True
    )
    vector = vector.astype("float32")

    scores, ids = index.search(vector, k)

    candidates = []
    max_score = None

    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue

        if IS_SIMILARITY_METRIC:
            if score < FAISS_MIN_SIMILARITY:
                continue
            if max_score is None or score > max_score:
                max_score = float(score)
        else:
            if score > FAISS_MAX_DISTANCE:
                continue

        candidates.append(chunks[idx])

    if not candidates:
        print("[Recherche FAISS] Aucun résultat suffisamment pertinent")
        return [], corrected_question, False, max_score

    # ==========================
    # Reranking
    # ==========================

    results, rerank_scores = _rerank(enriched_question, candidates, top_n=top_n)

    low_confidence = (
        IS_SIMILARITY_METRIC
        and max_score is not None
        and max_score < LOW_CONFIDENCE_THRESHOLD
    )

    return results, corrected_question, low_confidence, max_score

# ==============================
# FORMATAGE - VERSION NATURELLE (SANS MARKDOWN, SANS EMOJIS)
# ==============================

def format_article_response(article_content, article_num):
    """
    Formate la réponse pour un article spécifique - version naturelle.
    Le LLM n'est pas appelé, on affiche directement le contenu.
    """
    content = article_content.strip()

    # Nettoyer les en-têtes
    content = re.sub(r'^[A-Z\s]+>.*?\n', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^TITRE\s+[IVXLCDM]+\s*:.*?\n', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^CHAPITRE\s+[A-Z]+\s*:.*?\n', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^Section\s+\d+\s*:.*?\n', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^ARTICLE\s+\d+\s*\n', '', content, flags=re.IGNORECASE)
    content = re.sub(r'^Art\.?\s+\d+\s*\n', '', content, flags=re.IGNORECASE)
    content = content.strip()

    return f"""{content}

Références des articles : {article_num}."""


def format_general_response(answer, articles_list):
    """
    Formate une réponse générale - version naturelle.
    On ne fait que nettoyer la réponse du LLM.
    Le LLM gère lui-même les références.
    """
    answer = clean_response(answer)
    answer = re.sub(r'^\[[^\]]*\]\s*', '', answer)
    return answer


def format_error_response(message, suggestions=None):
    """
    Formate une réponse d'erreur - version naturelle.
    """
    if suggestions is None:
        suggestions = [
            "Reformulez votre question avec des termes plus précis",
            "Utilisez des mots-clés juridiques (licenciement, salaire, congé, etc.)",
            "Précisez le numéro d'article si vous le connaissez (ex: 'article 13')"
        ]

    suggestions_text = "\n".join(f"- {s}" for s in suggestions)

    return f"""{message}

Suggestions :
{suggestions_text}"""


def clean_response(answer):
    """Nettoie la réponse pour éviter les répétitions et le texte brut."""
    lines = answer.split('\n')
    cleaned_lines = []
    seen_content = set()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line in seen_content:
            continue
        line = re.sub(r'^\[[^\]]*\]\s*', '', line)
        seen_content.add(line)
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def add_footer(answer, model_used=None, low_confidence=False):
    """
    Ajoute uniquement un message de faible confiance si nécessaire.
    """
    if low_confidence:
        answer += "\n\nRemarque : cette réponse est basée sur des informations partiellement pertinentes. Vous pouvez préciser votre question pour obtenir une réponse plus précise."

    return answer


# ==============================
# APPEL GROQ AVEC RETRY + FALLBACK
# ==============================

def _call_groq(model, system_prompt, user_prompt, max_tokens=DEFAULT_MAX_TOKENS, temperature=0.1):
    return client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )


def call_groq_with_fallback(system_prompt, user_prompt, max_tokens=DEFAULT_MAX_TOKENS, temperature=0.1):
    """
    Essaie le modèle principal (avec retries sur erreurs réseau transitoires),
    puis bascule sur le modèle de secours en cas de rate limit ou d'échec
    persistant. Retourne (texte_reponse, modele_utilise).
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _call_groq(PRIMARY_MODEL, system_prompt, user_prompt, max_tokens, temperature)
            return response.choices[0].message.content, PRIMARY_MODEL

        except RateLimitError as e:
            logger.warning(f"[Groq] Rate limit atteint sur {PRIMARY_MODEL} : {e}")
            break

        except (APIConnectionError, APIError) as e:
            logger.warning(f"[Groq] Tentative {attempt}/{MAX_RETRIES} échouée sur {PRIMARY_MODEL} : {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    print(f"[Fallback] Basculement vers le modèle de secours : {FALLBACK_MODEL}")
    try:
        response = _call_groq(FALLBACK_MODEL, system_prompt, user_prompt, max_tokens, temperature)
        return response.choices[0].message.content, FALLBACK_MODEL

    except RateLimitError as e:
        raise RuntimeError(
            "Le quota quotidien de l'API Groq est dépassé pour les deux modèles. "
            "Merci de réessayer plus tard ou de vérifier votre quota sur console.groq.com."
        ) from e

    except (APIConnectionError, APIError) as e:
        raise RuntimeError(
            "Impossible de contacter l'API Groq (problème réseau ou service "
            "indisponible). Merci de réessayer dans quelques instants."
        ) from e

# ==============================
# VERIFICATION POST-REPONSE
# ==============================

CITED_ARTICLE_PATTERN = re.compile(r"article\s+(\d+)", re.IGNORECASE)


def _verify_answer(answer, articles_in_context):
    """
    Vérifie que tous les articles cités dans la réponse du LLM font bien
    partie du contexte fourni.
    """
    cited = {int(m) for m in CITED_ARTICLE_PATTERN.findall(answer)}
    unsupported = cited - set(a for a in articles_in_context if isinstance(a, int))

    if unsupported:
        unsupported_str = ", ".join(str(a) for a in sorted(unsupported))
        logger.warning(f"[Verification] Articles cités mais absents du contexte : {unsupported_str}")
        return (
            f"\n\nVérification : La réponse mentionne l'article "
            f"{unsupported_str} qui n'apparaît pas dans les documents consultés. "
            f"Veuillez vérifier cette information."
        )
    return ""

# ==============================
# GENERATION (RAG + GROQ)
# ==============================

def ask_legal_ai(question):
    """
    Fonction principale : répond à une question juridique
    en utilisant le RAG sur le Code du travail malgache.
    """
    original_question = question

    documents, corrected_question, low_confidence, max_score = search_documents(question)

    # ==========================
    # CAS 1 : AUCUN DOCUMENT TROUVÉ
    # ==========================

    if not documents:
        return add_footer(
            format_error_response(
                "Je ne trouve pas cette information dans le Code du travail malgache."
            ),
            low_confidence=low_confidence
        )

    # ==========================
    # CAS 2 : ARTICLE EXACT (ex: "art 13", "article 43")
    # ==========================

    article_num = _find_article_number(original_question)
    if article_num is None:
        article_num = _find_article_number(corrected_question)

    if article_num is not None and len(documents) == 1:
        content = documents[0].get("page_content", "")
        response = format_article_response(content, article_num)
        return add_footer(response, low_confidence=low_confidence)

    # ==========================
    # CAS 3 : QUESTION GÉNÉRALE OU PRÉCISE
    # ==========================

    context_parts = []
    articles_set = set()

    for doc in documents:
        if isinstance(doc, dict):
            content = doc.get("page_content", str(doc))
            metadata = doc.get("metadata", {})
            article = metadata.get("article_num", "inconnu")
            articles_set.add(article)
            # Nettoyer le contenu pour le contexte
            content = re.sub(r'^[A-Z\s]+>.*?\n', '', content, flags=re.IGNORECASE)
            content = re.sub(r'^TITRE\s+[IVXLCDM]+\s*:.*?\n', '', content, flags=re.IGNORECASE)
            content = re.sub(r'^CHAPITRE\s+[A-Z]+\s*:.*?\n', '', content, flags=re.IGNORECASE)
            content = re.sub(r'^Section\s+\d+\s*:.*?\n', '', content, flags=re.IGNORECASE)
            content = re.sub(r'^ARTICLE\s+\d+\s*\n', '', content, flags=re.IGNORECASE)
            content = re.sub(r'^Art\.?\s+\d+\s*\n', '', content, flags=re.IGNORECASE)
            context_parts.append(f"ARTICLE {article}\n{content.strip()}")
        else:
            context_parts.append(str(doc))

    context = "\n\n".join(context_parts)
    articles_str = ", ".join(str(a) for a in sorted(articles_set) if a != "inconnu")

    # ==========================
    # PROMPT SYSTEM - VERSION AMÉLIORÉE
    # ==========================

    system_prompt = """
Tu es LegalAI, un assistant juridique spécialisé dans le Code du travail malgache (Loi n°2024-014).

Règles de réponse :
- Réponds toujours de manière naturelle, claire et compréhensible pour un utilisateur non juriste.
- Commence directement par répondre à la question, sans formule d'introduction générique.
- N'utilise pas de titres en gras ni de structure en sections séparées.
- N'utilise pas de Markdown, d'émojis ou de caractères spéciaux.
- Explique d'abord le principe juridique en langage courant, puis intègre les articles qui le justifient directement dans le fil du texte.
- Reformule les dispositions légales avec tes propres mots pour les rendre plus accessibles, tout en restant fidèle au contenu des articles.
- Écris toujours "l'article X" en toutes lettres.

À la fin de chaque réponse, ajoute une seule ligne sous cette forme :
- Références des articles : 43.
- Références des articles : 44 et 45.
- Références des articles : 125, 126 et 130.

Ne cite que les articles réellement utilisés pour répondre à la question.
Ne fais jamais apparaître cette ligne deux fois.
N'invente jamais un article ou un contenu juridique qui n'est pas dans le contexte fourni.
Si le contexte fourni ne permet pas de répondre précisément, dis-le clairement.
"""

    # ==========================
    # PROMPT UTILISATEUR
    # ==========================

    user_prompt = f"""
Contexte juridique ({len(articles_set)} articles disponibles : {articles_str}) :

{context}

Question du client : {original_question}

Réponse :"""

    try:
        answer, used_model = call_groq_with_fallback(system_prompt, user_prompt, max_tokens=DEFAULT_MAX_TOKENS, temperature=0.1)

        # Nettoyer la réponse
        answer = clean_response(answer)

        # Vérifier les articles cités (warning seulement, pas de modification)
        _verify_answer(answer, articles_set)

        # Formater la réponse générale (ne fait que nettoyer)
        response = format_general_response(answer, articles_set)

        # Ajouter le footer si nécessaire
        response = add_footer(response, low_confidence=low_confidence)

        return response

    except RuntimeError as e:
        logger.error(f"[LegalAI] Échec définitif de la génération : {e}")
        return add_footer(
            format_error_response(
                f"Erreur technique : {e}",
                ["Réessayer dans quelques instants", "Contacter le support technique"]
            )
        )

    except Exception:
        logger.exception("[LegalAI] Erreur inattendue lors de la génération")
        return add_footer(
            format_error_response(
                "Une erreur inattendue est survenue.",
                ["Réessayer dans quelques instants", "Reformuler votre question"]
            )
        )

# ==============================
# MODE CHAT TERMINAL
# ==============================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" LegalAI - Assistant Juridique du Code du travail malgache")
    print("=" * 70)
    print("Posez vos questions sur le droit du travail malgache")
    print("Tapez 'exit' pour quitter\n")
    print("Exemples de questions :")
    print("  Article exact   : article 13, art 43, art.58")
    print("  Question précise: combien de jours de congé par an ?")
    print("  Question générale: quels sont les motifs de licenciement ?")
    print("-" * 70 + "\n")

    while True:
        try:
            question = input("Vous : ")
        except (KeyboardInterrupt, EOFError):
            print("\n\nAu revoir !")
            break

        if question.lower() in ["exit", "quit", "q"]:
            print("\nAu revoir !")
            break

        if question.strip() == "":
            continue

        print("\nRecherche en cours...")
        answer = ask_legal_ai(question)

        print("\n" + "=" * 70)
        print("LegalAI :")
        print("=" * 70)
        print(answer)
        print("\n" + "=" * 70 + "\n")