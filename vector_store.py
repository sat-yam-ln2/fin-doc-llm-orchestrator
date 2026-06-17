import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR

embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
collection = client.get_or_create_collection(
    name=CHROMA_COLLECTION_NAME,
    embedding_function=embedding_fn
)

def add_document(doc_id: str, raw_text: str, metadata: dict):
    collection.add(
        documents=[raw_text],
        metadatas=[{**metadata, "doc_id": doc_id}],
        ids=[doc_id]
    )

def query_documents(query: str, k: int = 3) -> list:
    results = collection.query(query_texts=[query], n_results=k)
    output = []
    for i, doc in enumerate(results["documents"][0]):
        output.append({
            "content": doc,
            "metadata": results["metadatas"][0][i]
        })
    return output
