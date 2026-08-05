try:
    from sentence_transformers import SentenceTransformer
    import torch
except ImportError:
    SentenceTransformer = None
    torch = None

# We use BGE small for fast, high-quality embeddings. Dimension = 384
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Singleton model instance
_model = None

def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # Load on first use to avoid blocking startup if not needed
        # Use CPU by default unless CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
    return _model

def chunk_text(text: str, max_length: int = 512, overlap: int = 50) -> list[str]:
    """
    Simple fallback chunking by characters.
    For resumes, we can just split by newlines, then group them.
    This is a basic chunker, returning a list of strings.
    """
    lines = text.split("\n")
    chunks = []
    current_chunk = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if len(current_chunk) + len(line) > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + " "
        else:
            current_chunk += line + " "
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    # model.encode returns a numpy array, we convert to list of floats for Qdrant
    return model.encode(text).tolist()

def embed_chunks(chunks: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    embeddings = model.encode(chunks)
    return [emb.tolist() for emb in embeddings]
