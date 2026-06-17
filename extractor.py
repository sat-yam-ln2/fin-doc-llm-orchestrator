from groq import Groq
from langchain.output_parsers import PydanticOutputParser
from schemas import BankStatementData, InvoiceData, DisputeLetterData, NewsSnippetData
from config import EXTRACTOR_MODEL, GROQ_API_KEY
import time

client = Groq(api_key=GROQ_API_KEY)

SCHEMA_MAP = {
    "bank_statement": BankStatementData,
    "invoice": InvoiceData,
    "dispute_letter": DisputeLetterData,
    "news_snippet": NewsSnippetData
}

def extract_entities(document: str, doc_type: str) -> dict:
    schema = SCHEMA_MAP.get(doc_type)
    if not schema:
        raise ValueError(f"Unknown document type: {doc_type}")

    parser = PydanticOutputParser(pydantic_object=schema)
    format_instructions = parser.get_format_instructions()

    start = time.time()

    completion = client.chat.completions.create(
        model=EXTRACTOR_MODEL,
        messages=[
            {
                "role": "system",
                "content": f"You are a financial data extraction expert. Extract all relevant entities from the document and return them as valid JSON only. No extra text, no markdown.\n{format_instructions}"
            },
            {
                "role": "user",
                "content": document
            }
        ],
        temperature=0,
        max_completion_tokens=1024,
        stream=False
    )

    latency = round(time.time() - start, 3)
    raw = completion.choices[0].message.content.strip()

    # Strip markdown code fences if model wraps output in them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = parser.parse(raw)

    return {
        "extracted": result,
        "input_tokens": completion.usage.prompt_tokens,
        "latency_seconds": latency,
        "model": EXTRACTOR_MODEL
    }
