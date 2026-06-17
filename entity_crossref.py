import re
from typing import List, Dict


def extract_crossref_entities(doc_type: str, extracted: dict, doc_index: int) -> List[Dict]:
    entities = []

    def add(entity_type, value, field):
        if value and str(value).strip() and str(value).strip().lower() not in ["none", "null", ""]:
            entities.append({
                "entity_type": entity_type,
                "value": str(value).strip(),
                "field": field,
                "doc_index": doc_index,
                "doc_type": doc_type.replace("_", " ").title()
            })

    if doc_type == "bank_statement":
        add("Account Number", extracted.get("account_number"), "account_number")
        add("Person Name", extracted.get("account_holder"), "account_holder")
        for txn in extracted.get("transactions", []):
            acct_match = re.search(r"\d{4}-\d{4}", txn)
            if acct_match:
                add("Account Number", acct_match.group(), "transaction_reference")

    elif doc_type == "invoice":
        add("Company", extracted.get("vendor_name"), "vendor_name")
        add("Company", extracted.get("buyer_name"), "buyer_name")
        add("Invoice Number", extracted.get("invoice_number"), "invoice_number")

    elif doc_type == "dispute_letter":
        add("Person Name", extracted.get("claimant_name"), "claimant_name")
        add("Account Number", extracted.get("account_number"), "account_number")

    elif doc_type == "news_snippet":
        for entity in extracted.get("entities_mentioned", []):
            add("Company/Person", entity, "entities_mentioned")

    return entities


def build_crossref_table(processed_docs: List[Dict]) -> List[Dict]:
    all_entities = []
    for i, doc in enumerate(processed_docs):
        entities = extract_crossref_entities(
            doc["doc_type"],
            doc["extracted"],
            i + 1
        )
        all_entities.extend(entities)

    # Find values that appear in more than one document
    from collections import defaultdict
    value_to_docs = defaultdict(list)
    for e in all_entities:
        value_to_docs[e["value"].lower()].append(e["doc_index"])

    # Tag cross-document matches
    for e in all_entities:
        doc_indices = value_to_docs[e["value"].lower()]
        unique_docs = list(set(doc_indices))
        e["appears_in_docs"] = unique_docs
        e["is_cross_doc"] = len(unique_docs) > 1

    return all_entities
