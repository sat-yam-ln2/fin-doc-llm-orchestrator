import json
from pipeline import run_pipeline
from vector_store import query_documents
from synthetic_docs import SAMPLE_DOCS


def main():
    print("=== Processing all synthetic documents ===\n")

    for doc_name, doc_text in SAMPLE_DOCS.items():
        print(f"\n--- Processing: {doc_name} ---")
        result = run_pipeline(doc_text)
        print(json.dumps(result["risk_summary"], indent=2))

    print("\n=== RAG Query Demo ===")
    query = "Which documents mention wire transfers?"
    print(f"Query: {query}\n")
    results = query_documents(query, k=3)
    for r in results:
        print(f"Doc type: {r['metadata'].get('doc_type')} | Preview: {r['content'][:150]}\n")


if __name__ == "__main__":
    main()
