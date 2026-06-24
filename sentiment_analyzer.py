from groq import Groq
from langchain.output_parsers import PydanticOutputParser
from schemas import ToneAnalysis
from config import CLASSIFIER_MODEL, GROQ_API_KEY
import time

client = Groq(api_key=GROQ_API_KEY)
parser = PydanticOutputParser(pydantic_object=ToneAnalysis)


def analyze_tone(document: str) -> dict:
    """
    Reads the document and scores it on urgency and evasiveness.
    
    Urgency: how much the writer pressures fast action
    Evasiveness: how much the writer avoids concrete specifics
    
    Uses the fast model since this is a simpler judgment task
    than structured field extraction.
    """
    format_instructions = parser.get_format_instructions()

    start = time.time()

    completion = client.chat.completions.create(
        model=CLASSIFIER_MODEL,  # fast model, reused for cost efficiency
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a linguistic risk analyst. Read the financial document "
                    "and score it on two axes only:\n\n"
                    "urgency_score (0-10): How much does the writer pressure for fast "
                    "action? 0 = no urgency, calm and procedural. 10 = extreme pressure, "
                    "demands immediate action, repeated urgency language.\n\n"
                    "evasiveness_score (0-10): How vague or non-specific is the writer "
                    "about concrete details (dates, amounts, names, what happened)? "
                    "0 = fully specific and detailed. 10 = vague, avoids specifics, "
                    "uses generic language to describe what happened.\n\n"
                    "combined_risk_signal: set to 'high' if BOTH urgency_score and "
                    "evasiveness_score are 6 or above. Set to 'medium' if only one "
                    "is 6 or above. Set to 'low' if both are below 6.\n\n"
                    "Return valid JSON only, no extra text, no markdown.\n"
                    f"{format_instructions}"
                )
            },
            {
                "role": "user",
                "content": document
            }
        ],
        temperature=0,
        max_completion_tokens=300,
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
        "tone": result,
        "input_tokens": completion.usage.prompt_tokens,
        "latency_seconds": latency,
        "model": CLASSIFIER_MODEL
    }