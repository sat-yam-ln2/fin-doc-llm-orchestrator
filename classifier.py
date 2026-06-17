from groq import Groq
from config import CLASSIFIER_MODEL, GROQ_API_KEY
import time

client = Groq(api_key=GROQ_API_KEY)

def classify_document(document: str) -> dict:
    start = time.time()

    completion = client.chat.completions.create(
        model=CLASSIFIER_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial document classifier. "
                    "Given a document, respond with exactly this format and nothing else: label|confidence\n"
                    "Where label is one of: bank_statement, invoice, dispute_letter, news_snippet\n"
                    "And confidence is your confidence percentage as an integer.\n"
                    "Example: bank_statement|94"
                )
            },
            {
                "role": "user",
                "content": document
            }
        ],
        temperature=0,
        max_completion_tokens=10,
        stream=False
    )

    latency = round(time.time() - start, 3)
    raw = completion.choices[0].message.content.strip().lower()

    # Parse label|confidence
    if "|" in raw:
        parts = raw.split("|")
        label = parts[0].strip()
        try:
            confidence = int(parts[1].strip().replace("%", ""))
        except:
            confidence = 0
    else:
        label = raw
        confidence = 0

    return {
        "label": label,
        "confidence": confidence,
        "input_tokens": completion.usage.prompt_tokens,
        "output_tokens": completion.usage.completion_tokens,
        "latency_seconds": latency,
        "model": CLASSIFIER_MODEL
    }
