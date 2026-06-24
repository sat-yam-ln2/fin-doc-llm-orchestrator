from groq import Groq
from langchain.output_parsers import PydanticOutputParser
from schemas import VerificationResult
from config import CLASSIFIER_MODEL, GROQ_API_KEY
import time

client = Groq(api_key=GROQ_API_KEY)
parser = PydanticOutputParser(pydantic_object=VerificationResult)


def verify_extraction(original_document: str, extracted_json: str) -> dict:
    """
    LLM-as-a-judge: checks whether the extracted JSON is actually
    supported by the original document text, or whether the extractor
    hallucinated any values.

    Uses the fast model deliberately. This is a verification task,
    not a generation task, so it does not need the strong model.
    """
    format_instructions = parser.get_format_instructions()

    start = time.time()

    completion = client.chat.completions.create(
        model=CLASSIFIER_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a fact-checking auditor. You will be given an ORIGINAL "
                    "DOCUMENT and EXTRACTED DATA that was pulled from it. Your only job "
                    "is to verify whether every value in the extracted data actually "
                    "appears in or is directly supported by the original document.\n\n"
                    "Do not re-extract anything. Do not improve the extraction. "
                    "Only judge whether it is accurate.\n\n"
                    "status rules:\n"
                    "- 'verified': every extracted value is directly supported by the document\n"
                    "- 'partially_verified': most values are supported but one or two are "
                    "questionable, missing from the source, or slightly altered\n"
                    "- 'unverified': multiple values are not supported by the document, "
                    "or appear to be invented\n\n"
                    "flagged_fields: list the specific field names that look wrong or "
                    "unsupported. Leave empty if status is 'verified'.\n\n"
                    "Return valid JSON only, no markdown, no extra text.\n"
                    f"{format_instructions}"
                )
            },
            {
                "role": "user",
                "content": (
                    f"ORIGINAL DOCUMENT:\n{original_document}\n\n"
                    f"EXTRACTED DATA:\n{extracted_json}"
                )
            }
        ],
        temperature=0,
        max_completion_tokens=400,
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
        "verification": result,
        "input_tokens": completion.usage.prompt_tokens,
        "latency_seconds": latency,
        "model": CLASSIFIER_MODEL
    }