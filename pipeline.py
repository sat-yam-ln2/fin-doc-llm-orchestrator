import json
import uuid
from classifier import classify_document
from extractor import extract_entities
from vector_store import add_document
from summarizer import summarize_risk
from anomaly_detector import detect_anomalies


def parse_pdf(file_path: str) -> str:
    import pdfplumber
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def run_pipeline(raw_text: str) -> dict:
    doc_id = str(uuid.uuid4())
    logs = {}

    # Step 1: Classify
    classification = classify_document(raw_text)
    doc_type = classification["label"]
    confidence = classification["confidence"]
    logs["classification"] = classification
    print(f"[CLASSIFY] type={doc_type} | confidence={confidence}% | tokens={classification['input_tokens']} | latency={classification['latency_seconds']}s")

    # Step 2: Extract
    extraction = extract_entities(raw_text, doc_type)
    extracted = extraction["extracted"]
    logs["extraction"] = extraction
    print(f"[EXTRACT] tokens={extraction['input_tokens']} | latency={extraction['latency_seconds']}s")

    # Step 3: Anomaly detection (no LLM)
    anomalies = detect_anomalies(doc_type, extracted)
    logs["anomalies"] = anomalies
    print(f"[ANOMALY] {len(anomalies)} flags detected")

    # Step 4: Store in vector DB
    add_document(
        doc_id=doc_id,
        raw_text=raw_text,
        metadata={"doc_type": doc_type}
    )
    print(f"[STORE] doc_id={doc_id} stored in vector DB")

    # Step 5: Summarize risk
    extracted_str = extracted.model_dump_json()
    summary = summarize_risk(doc_type, extracted_str)
    logs["summary"] = summary
    print(f"[SUMMARIZE] risk_level={summary['summary'].risk_level} | latency={summary['latency_seconds']}s")

    return {
        "doc_id": doc_id,
        "doc_type": doc_type,
        "confidence": confidence,
        "extracted": extracted.model_dump(),
        "anomalies": anomalies,
        "risk_summary": summary["summary"].model_dump(),
        "logs": logs
    }


def run_pipeline_from_pdf(file_path: str) -> dict:
    raw_text = parse_pdf(file_path)
    if not raw_text.strip():
        raise ValueError("PDF appears to be empty or could not be parsed")
    return run_pipeline(raw_text)
