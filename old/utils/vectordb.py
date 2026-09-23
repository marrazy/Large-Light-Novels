#vector database
import chromadb
import uuid
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./vectordb/current")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name="memory")

history_stack = []

def get_context(text, k=3):
    query_embedding = embedder.encode([text]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)
    docs = results.get("documents", [[]])[0]
    return docs

def store_info(jp_text, en_translation, extracted_info):
    doc = f"JP: {jp_text}\nEN: {en_translation}\nINFO: {extracted_info}"
    metadata = {
        "jp": jp_text,
        "en": en_translation,
        "info": extracted_info
    }
    embedding = embedder.encode([jp_text])[0].tolist()
    doc_id = str(uuid.uuid4())
    collection.add(
        documents=[doc],
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[doc_id]
    )
    history_stack.append(doc_id)

def undo_last_entry():
    if history_stack:
        doc_id = history_stack.pop()
        collection.delete(ids=[doc_id])
    