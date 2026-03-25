_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            # Fallback if not installed or some issue
            return None
    return _model

def embed(text: str) -> list[float]:
    model = get_model()
    if not model:
        return [0.0] * 384
    return model.encode(text).tolist()
