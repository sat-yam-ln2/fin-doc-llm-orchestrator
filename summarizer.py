from groq import Groq
from langchain.output_parsers import PydanticOutputParser
from schemas import RiskSummary
from config import SUMMARIZER_MODEL, GROQ_API_KEY
import time

client = Groq(api_key=GROQ_API_KEY)
parser = PydanticOutputParser(pydantic_object=RiskSummary)

def summarize_risk(doc_type: str, extracted_data: str) -> dict:
    format_instructions = parser.get_format_instructions()

    start = time.time()

    completion = client.chat.completions.create(
        model=SUMMARIZER_MODEL,
        messages=[
            {
                "role": "system",
                "content": f"You are a financial risk analyst. Given extracted data from a financial document, produce a risk summary as valid JSON only. No extra text, no markdown.\n{format_instructions}"
            },
            {
                "role": "user",
                "content": f"Document type: {doc_type}\nExtracted data: {extracted_data}"
            }
        ],
        temperature=0,
        max_completion_tokens=512,
        stream=False
    )

    latency = round(time.time() - start, 3)
    raw = completion.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = parser.parse(raw)

    return {
        "summary": result,
        "input_tokens": completion.usage.prompt_tokens,
        "latency_seconds": latency,
        "model": SUMMARIZER_MODEL
    }
