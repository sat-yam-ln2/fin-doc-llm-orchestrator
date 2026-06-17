import streamlit as st
import tempfile
import os
import time
from pipeline import run_pipeline, run_pipeline_from_pdf
from vector_store import query_documents
from synthetic_docs import SAMPLE_DOCS

st.set_page_config(
    page_title="Financial Document Intelligence",
    page_icon="🏦",
    layout="wide"
)

if "processed_docs" not in st.session_state:
    st.session_state.processed_docs = []
if "pipeline_logs" not in st.session_state:
    st.session_state.pipeline_logs = []

st.title("Financial Document Intelligence Pipeline")
st.caption("classify, extract, detect anomalies, and query financial documents")
st.divider()



tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Process Documents",
    "Anomaly Flags",
    "Pipeline Logs",
    "Search Documents",
    "Trend View",
    "Entity Cross-Reference",
    "Model Confidence Demo"
])

# ── TAB 1: Process Documents ──────────────────────────────────────────────────
with tab1:
    st.subheader("Process a Financial Document")

    input_mode = st.radio("Input method", ["Upload PDF", "Load Sample", "Paste Text"], horizontal=True)

    doc_text = ""
    pdf_uploaded = False

    if input_mode == "Upload PDF":
        st.markdown("**Quick load a sample PDF**")

        sample_pdf_map = {
            "-- select a sample --": None,
            "Bank Statement — January 2024 (Normal)": "sample_pdfs/sample_bank_jan.pdf",
            "Bank Statement — February 2024 (Normal)": "sample_pdfs/sample_bank_feb.pdf",
            "Bank Statement — March 2024 (ANOMALY MONTH)": "sample_pdfs/sample_bank_mar.pdf",
            "Bank Statement — April 2024 (Recovery)": "sample_pdfs/sample_bank_apr.pdf",
            "Invoice (Rapid Logistics Ltd, $16,000)": "sample_pdfs/sample_invoice.pdf",
            "Dispute Letter (Angela Torres, $3,450)": "sample_pdfs/sample_dispute_letter.pdf",
            "News Snippet (Omega Capital Partners, FinCEN)": "sample_pdfs/sample_news_snippet.pdf",
            "Ambiguous Memo (Dispute + News overlap)": "sample_pdfs/sample_ambiguous.pdf",
        }

        selected_sample = st.selectbox("Sample PDFs", list(sample_pdf_map.keys()))

        st.markdown("**Or upload your own PDF**")
        uploaded_file = st.file_uploader("Upload any financial PDF", type=["pdf"])

        # Resolve which source to use
        if uploaded_file:
            st.success(f"Loaded: {uploaded_file.name} ({round(uploaded_file.size/1024, 1)} KB)")
            pdf_uploaded = True
        elif sample_pdf_map[selected_sample]:
            st.info(f"Sample selected: {selected_sample}")
            pdf_uploaded = True

    elif input_mode == "Load Sample":
        sample_choice = st.selectbox(
            "Choose a sample",
            options=["-- select --"] + list(SAMPLE_DOCS.keys()),
            format_func=lambda x: x.replace("_", " ").title()
        )
        if sample_choice != "-- select --":
            doc_text = SAMPLE_DOCS[sample_choice]
            st.text_area("Document preview", value=doc_text, height=220, disabled=True)

    else:
        doc_text = st.text_area(
            "Paste document text",
            height=220,
            placeholder="Paste any financial document here..."
        )

    run_btn = st.button(
        "Run Pipeline",
        type="primary",
        disabled=not (bool(doc_text.strip()) or pdf_uploaded)
    )

    if run_btn:
        with st.status("Running pipeline...", expanded=True) as status:
            try:
                t0 = time.time()

                if input_mode == "Upload PDF" and pdf_uploaded:
                    st.write("Parsing PDF...")
                    if uploaded_file:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uploaded_file.read())
                            tmp_path = tmp.name
                        result = run_pipeline_from_pdf(tmp_path)
                        os.unlink(tmp_path)
                    else:
                        # sample PDF selected
                        sample_path = sample_pdf_map[selected_sample]
                        result = run_pipeline_from_pdf(sample_path)
                else:
                    result = run_pipeline(doc_text)

                total_time = round(time.time() - t0, 2)
                status.update(label=f"Done in {total_time}s", state="complete")

                st.session_state.processed_docs.append(result)
                st.session_state.pipeline_logs.append(result["logs"])

                st.divider()

                # ── Metrics row ──
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Document Type", result["doc_type"].replace("_", " ").title())

                confidence = result.get("confidence", 0)
                conf_color = "🟢" if confidence >= 85 else "🟡" if confidence >= 60 else "🔴"
                m2.metric("Classifier Confidence", f"{conf_color} {confidence}%")

                risk_level = result["risk_summary"]["risk_level"]
                risk_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_level.lower(), "⚪")
                m3.metric("Risk Level", f"{risk_color} {risk_level.upper()}")

                anomaly_count = len(result.get("anomalies", []))
                m4.metric("Anomalies Detected", anomaly_count, delta=None)

                with st.expander("How is Risk Level calculated?"):
                    st.markdown("""
                    | Level | Criteria |
                    |---|---|
                    | HIGH | Wire transfer flagged + debits exceed credits by 3x, or critical risk keywords present |
                    | MEDIUM | Single large transaction or payment method restriction detected |
                    | LOW | No anomalies, normal debit/credit ratio, no risk keywords |
                    
                    Risk level is determined by the LLM summarizer reading the structured extracted fields.
                    Anomaly flags are determined separately by deterministic rule-based code with no LLM involved.
                    """)

                st.divider()

                left, right = st.columns(2)

                with left:
                    st.markdown("**Extracted Entities**")
                    st.json(result["extracted"])

                with right:
                    st.markdown("**Risk Summary**")
                    risk = result["risk_summary"]
                    st.markdown(f"**Risk Level:** {risk_color} {risk['risk_level'].upper()}")
                    st.markdown(f"**Recommended Action:** {risk['recommended_action']}")
                    st.markdown("**Key Findings:**")
                    for f in risk["key_findings"]:
                        st.markdown(f"- {f}")

                    if result.get("anomalies"):
                        st.divider()
                        st.markdown("**Rule-Based Anomaly Flags**")
                        # Sort by severity: high first, cap at top 3 to avoid alert fatigue
                        sorted_flags = sorted(
                            result["anomalies"],
                            key=lambda x: 0 if x["severity"] == "high" else 1
                        )[:3]
                        for flag in sorted_flags:
                            sev = flag["severity"]
                            icon = "🔴" if sev == "high" else "🟡"
                            st.markdown(f"{icon} **{flag['rule']}** — {flag['detail']}")

                        total = len(result["anomalies"])
                        if total > 3:
                            st.caption(f"Showing top 3 of {total} flags. See Anomaly Flags tab for full list.")

            except Exception as e:
                status.update(label="Pipeline failed", state="error")
                st.error(f"Error: {str(e)}")

# ── TAB 2: Anomaly Flags ──────────────────────────────────────────────────────
with tab2:
    st.subheader("Rule-Based Anomaly Flags")
    st.caption("These flags come from deterministic Python rules, not the LLM. Fast, free, and fully explainable.")

    if not st.session_state.processed_docs:
        st.info("No documents processed yet.")
    else:
        all_high = []
        all_medium = []

        for i, doc in enumerate(st.session_state.processed_docs):
            for flag in doc.get("anomalies", []):
                entry = {
                    "Document": f"Doc {i+1} — {doc['doc_type'].replace('_', ' ').title()}",
                    "Rule": flag["rule"],
                    "Detail": flag["detail"],
                    "Severity": flag["severity"].upper()
                }
                if flag["severity"] == "high":
                    all_high.append(entry)
                else:
                    all_medium.append(entry)

        if all_high:
            st.markdown("#### High Severity")
            st.table(all_high)

        if all_medium:
            st.markdown("#### Medium Severity")
            st.table(all_medium)

        if not all_high and not all_medium:
            st.success("No anomalies detected across processed documents.")

# ── TAB 3: Pipeline Logs ──────────────────────────────────────────────────────
with tab3:
    st.subheader("Pipeline Logs — Cost and Latency Per Step")
    st.caption("Every step is tracked: model used, tokens consumed, time taken.")

    if not st.session_state.pipeline_logs:
        st.info("No documents processed yet.")
    else:
        for i, log in enumerate(st.session_state.pipeline_logs):
            doc_type = st.session_state.processed_docs[i]["doc_type"]
            confidence = st.session_state.processed_docs[i].get("confidence", 0)

            with st.expander(
                f"Document {i+1} — {doc_type.replace('_', ' ').title()} — Confidence {confidence}%",
                expanded=(i == len(st.session_state.pipeline_logs) - 1)
            ):
                steps = {
                    "Classification": log.get("classification", {}),
                    "Extraction": log.get("extraction", {}),
                    "Summarization": log.get("summary", {})
                }

                cols = st.columns(3)
                for col, (step_name, step_data) in zip(cols, steps.items()):
                    with col:
                        st.markdown(f"**{step_name}**")
                        st.markdown(f"Model: `{step_data.get('model', 'N/A')}`")
                        st.markdown(f"Input tokens: `{step_data.get('input_tokens', 'N/A')}`")
                        st.markdown(f"Latency: `{step_data.get('latency_seconds', 'N/A')}s`")

                st.markdown("**Token Usage**")
                token_data = {
                    "Step": ["Classification", "Extraction", "Summarization"],
                    "Tokens": [
                        log.get("classification", {}).get("input_tokens", 0),
                        log.get("extraction", {}).get("input_tokens", 0),
                        log.get("summary", {}).get("input_tokens", 0),
                    ]
                }
                st.bar_chart(token_data, x="Step", y="Tokens", height=180)

# ── TAB 4: Search Documents ───────────────────────────────────────────────────
with tab4:
    st.subheader("Search Across Processed Documents")
    st.caption("Natural language search across the vector database. The LLM is not called here — this is pure embedding similarity search.")

    col_pre, col_info = st.columns([1, 2])
    with col_pre:
        if st.button("Load All Samples into Database"):
            with st.spinner("Processing all 4 sample documents..."):
                for doc_name, doc_text in SAMPLE_DOCS.items():
                    try:
                        result = run_pipeline(doc_text)
                        st.session_state.processed_docs.append(result)
                        st.session_state.pipeline_logs.append(result["logs"])
                    except Exception as e:
                        st.warning(f"Failed on {doc_name}: {e}")
            st.success("All samples processed and stored.")

    with col_info:
        st.info(f"Documents in session: {len(st.session_state.processed_docs)}")

    st.divider()

    suggested = [
        "Which documents mention wire transfers?",
        "Show me documents with high risk keywords",
        "Which documents involve account numbers?",
        "Find documents related to suspicious transactions",
        "Which documents mention international transfers?"
    ]

    chosen = st.selectbox("Suggested queries", ["-- type your own --"] + suggested)
    query_input = st.text_input(
        "Search query",
        value=chosen if chosen != "-- type your own --" else "",
        placeholder="e.g. which documents mention wire transfers?"
    )

    if st.button("Search", type="primary", disabled=not bool(query_input.strip())):
        with st.spinner("Searching..."):
            try:
                results = query_documents(query_input.strip(), k=3)
                if not results:
                    st.warning("No results found. Process some documents first.")
                else:
                    st.success(f"Found {len(results)} relevant documents")
                    for i, r in enumerate(results):
                        with st.expander(f"Result {i+1} — {r['metadata'].get('doc_type', 'unknown').replace('_', ' ').title()}"):
                            st.markdown(f"**Type:** {r['metadata'].get('doc_type', 'N/A')}")
                            st.text(r["content"][:500] + "..." if len(r["content"]) > 500 else r["content"])
            except Exception as e:
                st.error(f"Search failed: {str(e)}")

# ── TAB 5: Trend View ─────────────────────────────────────────────────────────
with tab5:
    st.subheader("Trend View — Bank Statement Analysis Over Time")
    st.caption("Process the 4 monthly bank statements to see how debits, credits, and anomalies change month over month.")

    bank_docs = [d for d in st.session_state.processed_docs if d["doc_type"] == "bank_statement"]

    if len(bank_docs) < 2:
        st.info("Process at least 2 bank statement PDFs to see the trend. Load January through April from the sample PDF dropdown in Tab 1.")
    else:
        import re
        import pandas as pd

        def parse_amt(val):
            if not val:
                return 0.0
            return float(re.sub(r"[^\d.]", "", str(val)) or 0)

        rows = []
        for i, doc in enumerate(bank_docs):
            ext = doc["extracted"]
            credits = parse_amt(ext.get("total_credits"))
            debits = parse_amt(ext.get("total_debits"))
            anomaly_count = len(doc.get("anomalies", []))
            rows.append({
                "Statement": f"Statement {i+1}",
                "Total Credits ($)": credits,
                "Total Debits ($)": debits,
                "Anomalies": anomaly_count,
                "Debit/Credit Ratio": round(debits / credits, 2) if credits > 0 else 0
            })

        df = pd.DataFrame(rows)

        # Find anomaly month
        max_debit_idx = df["Total Debits ($)"].idxmax()
        anomaly_statement = df.loc[max_debit_idx, "Statement"]

        st.warning(f"Anomaly detected: **{anomaly_statement}** has the highest debits and ratio — this is the month that would trigger a fraud alert.")

        st.markdown("**Credits vs Debits Over Time**")
        st.line_chart(df.set_index("Statement")[["Total Credits ($)", "Total Debits ($)"]], height=300)

        st.markdown("**Debit to Credit Ratio** — ratio above 3.0 triggers anomaly flag")
        ratio_chart = df.set_index("Statement")[["Debit/Credit Ratio"]]
        st.bar_chart(ratio_chart, height=220)

        st.markdown("**Anomaly Flags Per Statement**")
        st.bar_chart(df.set_index("Statement")[["Anomalies"]], height=200)

        st.markdown("**Full Data Table**")
        st.dataframe(df, use_container_width=True)


# ── TAB 6: Entity Cross-Reference ─────────────────────────────────────────────
with tab6:
    st.subheader("Entity Cross-Reference")
    st.caption("All account numbers, names, and companies extracted across every processed document. Entities appearing in more than one document are highlighted — this is what a fraud analyst spends hours doing manually.")

    if not st.session_state.processed_docs:
        st.info("No documents processed yet.")
    else:
        from entity_crossref import build_crossref_table
        import pandas as pd

        all_entities = build_crossref_table(st.session_state.processed_docs)

        if not all_entities:
            st.warning("No entities extracted yet.")
        else:
            cross_doc = [e for e in all_entities if e["is_cross_doc"]]
            single_doc = [e for e in all_entities if not e["is_cross_doc"]]

            if cross_doc:
                st.error(f"**{len(cross_doc)} entities appear across multiple documents — these require investigation**")
                st.markdown("#### Cross-Document Matches")

                cross_rows = []
                seen = set()
                for e in cross_doc:
                    key = (e["value"], tuple(sorted(e["appears_in_docs"])))
                    if key not in seen:
                        seen.add(key)
                        cross_rows.append({
                            "Entity Type": e["entity_type"],
                            "Value": e["value"],
                            "Appears In Documents": ", ".join([f"Doc {d}" for d in sorted(e["appears_in_docs"])]),
                            "Doc Types": e["doc_type"]
                        })

                df_cross = pd.DataFrame(cross_rows)
                st.dataframe(
                    df_cross,
                    use_container_width=True,
                    hide_index=True
                )
                st.divider()

            st.markdown("#### All Extracted Entities")
            rows = []
            for e in all_entities:
                rows.append({
                    "Doc #": f"Doc {e['doc_index']}",
                    "Doc Type": e["doc_type"],
                    "Entity Type": e["entity_type"],
                    "Value": e["value"],
                    "Cross-Doc Match": "YES" if e["is_cross_doc"] else ""
                })

            df_all = pd.DataFrame(rows)
            st.dataframe(df_all, use_container_width=True, hide_index=True)


# ── TAB 7: Model Confidence Demo ──────────────────────────────────────────────
with tab7:
    st.subheader("Model Confidence Demo — When the Model Gets It Wrong")
    st.caption("This tab demonstrates that the pipeline is not a black box. Low confidence scores surface documents that need human review. This is what separates a production ML system from a demo.")

    st.markdown("""
    The ambiguous memo below is a real compliance document that combines characteristics of both a 
    **dispute letter** (account holder complaint, account number, disputed amount) and a 
    **news snippet** (regulatory investigation, named company, FinCEN). 
    
    A good classifier should show low confidence. A good system should flag it for human review.
    """)

    st.divider()

    ambiguous_text = """INTERNAL MEMO — COMPLIANCE REVIEW
Ref: CMP-2024-0391 | Date: April 2, 2024

This memo documents a formal complaint received from account holder Marcus Webb 
(Account No. 5593-8821) regarding a disputed transaction of $7,200 on March 29, 2024. 
The account holder states the charge was unauthorized.

Separately, our adverse media team flagged news reports linking the merchant — 
Trident Payment Solutions — to an ongoing FinCEN investigation into cross-border 
wire fraud and money laundering. CEO Raymond Holt denied the allegations.

Risk Operations recommends escalation given the overlap between the customer 
dispute and the regulatory investigation into the merchant."""

    st.markdown("**Ambiguous Document**")
    st.text(ambiguous_text)
    st.divider()

    run_ambiguous = st.button("Run Classifier on Ambiguous Document", type="primary")

    if run_ambiguous:
        with st.spinner("Classifying..."):
            try:
                from classifier import classify_document
                result = classify_document(ambiguous_text)

                label = result["label"]
                confidence = result["confidence"]

                col1, col2, col3 = st.columns(3)
                col1.metric("Classified As", label.replace("_", " ").title())

                if confidence < 70:
                    col2.metric("Confidence", f"{confidence}%", delta="LOW — human review needed")
                    conf_msg = "low"
                elif confidence < 85:
                    col2.metric("Confidence", f"{confidence}%", delta="MEDIUM")
                    conf_msg = "medium"
                else:
                    col2.metric("Confidence", f"{confidence}%")
                    conf_msg = "high"

                col3.metric("Latency", f"{result['latency_seconds']}s")

                st.divider()

                if conf_msg in ["low", "medium"]:
                    st.warning(f"""
**Low confidence classification detected.**

The model labeled this as **{label.replace('_', ' ').title()}** with only **{confidence}% confidence**.

This document contains signals from two categories:
- Dispute letter signals: account number 5593-8821, disputed amount $7,200, unauthorized transaction
- News snippet signals: FinCEN investigation, Trident Payment Solutions, CEO name, money laundering

**What a production system should do:** route this to a human reviewer rather than auto-processing it. 
The confidence threshold for auto-processing should be set at 85%+. Below that, flag for review.

This is exactly the kind of edge case that breaks naive pipelines.
                    """)
                else:
                    st.success(f"Model classified with {confidence}% confidence. Note: this document was designed to be ambiguous — if confidence is high, consider whether the extracted fields match the true intent of the document.")

                st.markdown("**What would you correct this to?**")
                correction = st.selectbox(
                    "Human reviewer correction",
                    ["-- select correct label --", "dispute_letter", "news_snippet", "bank_statement", "invoice", "needs_manual_split"]
                )

                if correction != "-- select correct label --":
                    if correction == label:
                        st.success(f"You agreed with the model. Confidence was {confidence}%.")
                    else:
                        st.error(f"You corrected the model from **{label}** to **{correction}**. This disagreement at {confidence}% confidence would be logged as a model error and used to retrain or improve the prompt.")

            except Exception as e:
                st.error(f"Classification failed: {str(e)}")
