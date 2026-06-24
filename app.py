import streamlit as st
import tempfile
import os
import re
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

def clean_for_markdown(text: str) -> str:
    text = text.replace("*", "").replace("_", " ").replace("$", "\\$")
    return text

st.title("Financial Document Intelligence Pipeline")
st.caption("classify, extract, verify, detect anomalies, and investigate financial documents")
st.divider()

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Process Documents",
    "Anomaly Flags",
    "Pipeline Logs",
    "Search Documents",
    "Trend View",
    "Entity Cross-Reference",
    "Model Confidence Demo",
    "Investigation Agent"
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
                        sample_path = sample_pdf_map[selected_sample]
                        result = run_pipeline_from_pdf(sample_path)
                else:
                    result = run_pipeline(doc_text)

                total_time = round(time.time() - t0, 2)
                status.update(label=f"Done in {total_time}s", state="complete")

                st.session_state.processed_docs.append(result)
                st.session_state.pipeline_logs.append(result["logs"])

                st.divider()

                verification = result.get("verification")
                if verification:
                    v_status = verification["status"]

                    v_config = {
                        "verified": ("🟢", "VERIFIED", "success"),
                        "partially_verified": ("🟡", "PARTIALLY VERIFIED", "warning"),
                        "unverified": ("🔴", "UNVERIFIED", "error")
                    }
                    icon, label, alert_type = v_config.get(
                        v_status, ("⚪", "UNKNOWN", "info")
                    )

                    badge_col, conf_col = st.columns([3, 1])
                    with badge_col:
                        if alert_type == "success":
                            st.success(f"{icon} **Extraction {label}** — {verification['reason']}")
                        elif alert_type == "warning":
                            st.warning(f"{icon} **Extraction {label}** — {verification['reason']}")
                            if verification.get("flagged_fields"):
                                st.caption(f"Flagged fields: {', '.join(verification['flagged_fields'])}")
                        else:
                            st.error(f"{icon} **Extraction {label}** — {verification['reason']}")
                            if verification.get("flagged_fields"):
                                st.caption(f"Flagged fields: {', '.join(verification['flagged_fields'])}")
                    with conf_col:
                        st.metric("Verification Confidence", f"{verification['confidence']}%")

                    st.caption(
                        "An independent LLM-as-a-judge call checked whether every "
                        "extracted value is actually supported by the source document. "
                        "This catches hallucinated fields before they reach risk "
                        "scoring or get stored."
                    )

                st.divider()

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
                st.divider()
                st.markdown("**Tone and Sentiment Analysis**")
                st.caption(
                    "Independent linguistic signal — does not look at facts, "
                    "only how the document is written."
                )

                tone = result["tone"]
                t1, t2, t3 = st.columns(3)

                t1.metric("Urgency Score", f"{tone['urgency_score']}/10")
                t1.progress(tone['urgency_score'] / 10)

                t2.metric("Evasiveness Score", f"{tone['evasiveness_score']}/10")
                t2.progress(tone['evasiveness_score'] / 10)

                combined = tone['combined_risk_signal']
                combined_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(combined, "⚪")
                t3.metric("Combined Tone Signal", f"{combined_icon} {combined.upper()}")

                st.caption(f"**Analysis:** {tone['tone_summary']}")

                if combined == "high":
                    st.warning(
                        "**High urgency combined with high evasiveness.** "
                        "This pattern is a stronger fraud indicator than either "
                        "signal alone — genuine claims are typically urgent AND "
                        "specific, while fraudulent claims tend to be urgent but vague."
                    )
                with st.expander("How is Risk Level calculated?"):
                    st.markdown("""
                    | Level | Criteria |
                    |---|---|
                    | HIGH | Wire transfer flagged + debits exceed credits by 3x, or critical risk keywords present |
                    | MEDIUM | Single large transaction or payment method restriction detected |
                    | LOW | No anomalies, normal debit/credit ratio, no risk keywords |

                    Risk level is determined by the LLM summarizer reading the structured extracted fields.
                    Anomaly flags are determined separately by deterministic rule-based code with no LLM involved.
                    Verification status is determined by a separate LLM-as-a-judge call that checks the
                    extraction against the source document, independent of risk scoring.
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
                        st.write(f"• {f}")

                    if result.get("anomalies"):
                        st.divider()
                        st.markdown("**Rule-Based and Statistical Anomaly Flags**")

                        if_flags = [f for f in result["anomalies"] if f.get("source") == "isolation_forest"]
                        rule_flags = [f for f in result["anomalies"] if f.get("source") == "rule"]

                        if rule_flags:
                            st.markdown("*Deterministic Rules*")
                            for flag in rule_flags:
                                icon = "🔴" if flag["severity"] == "high" else "🟡"
                                st.markdown(f"{icon} **{flag['rule']}** — {flag['detail']}")

                        if if_flags:
                            st.markdown("*Isolation Forest — Statistical Outliers*")
                            for flag in if_flags:
                                score = flag.get("anomaly_score", 0)
                                icon = "🔴" if flag["severity"] == "high" else "🟡"
                                txn_clean = clean_for_markdown(flag["transaction"])
                                col_a, col_b = st.columns([3, 1])
                                with col_a:
                                    st.markdown(
                                        f"{icon} **Transaction:** {txn_clean} — "
                                        f"\\${flag['amount']:,.2f} flagged as statistical outlier"
                                    )
                                with col_b:
                                    st.metric("Anomaly Score", f"{score:.2f}")
                                st.progress(score)

                        total = len(result["anomalies"])
                        if total > 4:
                            st.caption(f"Showing all {total} flags. See Anomaly Flags tab for full breakdown.")

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
                    "Severity": flag["severity"].upper(),
                    "Source": flag.get("source", "rule").replace("_", " ").title()
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
            verification = st.session_state.processed_docs[i].get("verification", {})
            v_status = verification.get("status", "N/A")

            with st.expander(
                f"Document {i+1} — {doc_type.replace('_', ' ').title()} — "
                f"Confidence {confidence}% — Verification: {v_status}",
                expanded=(i == len(st.session_state.pipeline_logs) - 1)
            ):
                steps = {
                    "Classification": log.get("classification", {}),
                    "Extraction": log.get("extraction", {}),
                    "Verification": log.get("verification", {}),
                    "Tone Analysis": log.get("tone", {}),
                    "Summarization": log.get("summary", {})
                }

                cols = st.columns(len(steps))
                for col, (step_name, step_data) in zip(cols, steps.items()):
                    with col:
                        st.markdown(f"**{step_name}**")
                        st.markdown(f"Model: `{step_data.get('model', 'N/A')}`")
                        st.markdown(f"Input tokens: `{step_data.get('input_tokens', 'N/A')}`")
                        st.markdown(f"Latency: `{step_data.get('latency_seconds', 'N/A')}s`")

                st.markdown("**Token Usage**")
                token_data = {
                    "Step": ["Classification", "Extraction", "Verification", "Tone", "Summarization"],
                    "Tokens": [
                        log.get("classification", {}).get("input_tokens", 0),
                        log.get("extraction", {}).get("input_tokens", 0),
                        log.get("verification", {}).get("input_tokens", 0),
                        log.get("tone", {}).get("input_tokens", 0),
                        log.get("summary", {}).get("input_tokens", 0),
                    ]
                }
                st.bar_chart(token_data, x="Step", y="Tokens", height=180)

                st.markdown("**Total Pipeline Latency**")
                total_latency = sum(step_data.get("latency_seconds", 0) for step_data in steps.values())
                st.metric("Sum of all step latencies", f"{round(total_latency, 2)}s")

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

# ── TAB 5: Trend View — Statistical Z-Score Anomaly Detection ──────────────────
with tab5:
    st.subheader("Trend View — Statistical Temporal Analysis")
    st.caption(
        "Process the monthly bank statements to see Z-score based anomaly "
        "detection. No LLM involved — pure statistics on the account's own "
        "transaction history."
    )

    bank_docs = [d for d in st.session_state.processed_docs if d["doc_type"] == "bank_statement"]

    if len(bank_docs) < 2:
        st.info("Process at least 2 bank statement PDFs to see the trend. Load January through April from the sample PDF dropdown in Tab 1.")
    else:
        import pandas as pd
        from trend_analyzer import detect_temporal_anomalies

        def parse_amt(val):
            if not val:
                return 0.0
            return float(re.sub(r"[^\d.]", "", str(val)) or 0)

        statements = []
        for i, doc in enumerate(bank_docs):
            ext = doc["extracted"]
            statements.append({
                "label": f"Statement {i+1}",
                "credits": parse_amt(ext.get("total_credits")),
                "debits": parse_amt(ext.get("total_debits")),
                "anomaly_count": len(doc.get("anomalies", []))
            })

        z_result = detect_temporal_anomalies(statements, threshold=2.5)

        if not z_result["reliable"]:
            st.warning("Fewer than 3 statements processed. Z-scores are shown but reliability improves with more data points.")

        st.markdown("**Z-Score Summary**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Mean Monthly Debits", f"${z_result['mean_debits']:,.2f}")
        c2.metric("Std Deviation", f"${z_result['std_debits']:,.2f}")
        c3.metric("Anomaly Threshold", f"±{z_result['threshold_used']} std dev")

        if z_result["flagged_months"]:
            for flag in z_result["flagged_months"]:
                st.error(f"**Temporal anomaly detected:** {flag['annotation']}")
        else:
            st.success("No statistically significant temporal anomalies across processed statements.")

        st.divider()

        df = pd.DataFrame(z_result["statements"])

        st.markdown("**Debits Over Time**")
        st.line_chart(df.set_index("label")[["debits"]], height=280)

        st.markdown("**Z-Score Per Statement** — values beyond ±2.5 are statistical outliers")
        z_df = df.set_index("label")[["z_score"]]
        st.bar_chart(z_df, height=220)
        st.caption(f"Threshold: |Z-score| ≥ {z_result['threshold_used']} flags a statement as anomalous")

        st.markdown("**Full Statistical Breakdown**")
        display_df = df.rename(columns={
            "label": "Statement",
            "credits": "Total Credits ($)",
            "debits": "Total Debits ($)",
            "z_score": "Z-Score",
            "is_temporal_anomaly": "Anomaly"
        })
        st.dataframe(display_df, use_container_width=True)


# ── TAB 6: Entity Cross-Reference ─────────────────────────────────────────────
with tab6:
    st.subheader("Entity Relationship Network")
    st.caption(
        "Each node is an entity extracted from your documents. "
        "Each edge means two entities appeared in the same document. "
        "Red nodes appear across multiple documents — these are your "
        "highest-priority investigative leads."
    )

    if not st.session_state.processed_docs:
        st.info("No documents processed yet. Process at least 2 documents to see connections form between entities.")
    else:
        from entity_network import build_entity_graph, render_graph_html, get_graph_stats
        from entity_crossref import build_crossref_table
        import pandas as pd
        import streamlit.components.v1 as components

        G = build_entity_graph(st.session_state.processed_docs)
        stats = get_graph_stats(G)

        if not stats:
            st.warning("No entities extracted yet.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Entities", stats["total_nodes"])
            c2.metric("Connections", stats["total_edges"])
            c3.metric(
                "Cross-Doc Entities",
                stats["cross_doc_entities"],
                delta="HIGH RISK" if stats["cross_doc_entities"] > 0 else None,
                delta_color="inverse"
            )
            c4.metric(
                "Most Connected",
                stats["most_connected_entity"] or "N/A",
                help="Entity with the most connections — in AML this signals a hub account or shell entity"
            )

            if stats["cross_doc_entities"] > 0:
                st.error(
                    f"**{stats['cross_doc_entities']} entities appear across multiple documents:** "
                    + ", ".join(f"`{e}`" for e in stats["cross_doc_names"])
                    + " — these connections would take an analyst hours to find manually."
                )

            st.divider()

            st.markdown(
                "🔴 **Red node** = appears in multiple documents (key lead)&nbsp;&nbsp;"
                "🔴 **Red edge** = connection seen across multiple documents&nbsp;&nbsp;"
                "**Node size** = number of documents it appears in&nbsp;&nbsp;"
                "**Hover** any node or edge for details"
            )

            html_content = render_graph_html(G)
            if html_content:
                components.html(html_content, height=620, scrolling=False)
            else:
                st.warning("Graph could not be rendered.")

            st.divider()

            st.markdown("#### Cross-Document Entity Matches")
            st.caption("These are the same connections shown visually above, in table form for reporting and audit purposes.")

            all_entities = build_crossref_table(st.session_state.processed_docs)
            cross_doc = [e for e in all_entities if e["is_cross_doc"]]

            if cross_doc:
                seen = set()
                rows = []
                for e in cross_doc:
                    key = (e["value"], tuple(sorted(e["appears_in_docs"])))
                    if key not in seen:
                        seen.add(key)
                        rows.append({
                            "Entity Type": e["entity_type"],
                            "Value": e["value"],
                            "Appears In": ", ".join([f"Doc {d}" for d in sorted(e["appears_in_docs"])]),
                        })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No cross-document matches yet. Process more documents to see entity connections.")

            with st.expander("All extracted entities"):
                rows = []
                for node, attrs in G.nodes(data=True):
                    rows.append({
                        "Entity": node,
                        "Type": attrs["entity_type"],
                        "Appears In": attrs["doc_count"],
                        "Cross-Doc": "YES" if attrs["doc_count"] > 1 else ""
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

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

# ── TAB 8: Investigation Agent — ReAct Autonomous Reasoning ────────────────────
with tab8:
    st.subheader("Investigation Agent — Autonomous Multi-Tool Reasoning")
    st.caption(
        "This is a ReAct agent, not a fixed pipeline. Ask a question and "
        "the agent decides on its own which tools to call, in what order, "
        "based on what it learns from each step."
    )

    if len(st.session_state.processed_docs) < 1:
        st.info("Process at least one document before using the investigation agent.")
    else:
        st.markdown(f"**{len(st.session_state.processed_docs)} documents** available for investigation.")

        with st.expander("Available tools the agent can choose from"):
            st.markdown("""
            - **search_documents** — semantic search across the vector store
            - **check_entity_connections** — checks if an account, name, or company appears across multiple documents
            - **get_anomaly_flags** — retrieves rule-based and statistical anomaly flags
            - **get_risk_summaries** — retrieves risk levels and recommended actions

            The agent is not told which tool to use. It reasons about the question
            and decides the sequence itself.
            """)

        suggested_questions = [
            "Is there anything suspicious about account 4821-0093-2211 across all documents?",
            "Are there any entities that appear in more than one document?",
            "Which documents have the highest risk and why?",
            "Summarize all anomaly flags found so far.",
            "Is there any connection between the bank statement and the dispute letter?",
        ]

        chosen_q = st.selectbox(
            "Suggested investigation questions",
            ["-- type your own --"] + suggested_questions
        )

        question = st.text_input(
            "Ask the investigation agent",
            value=chosen_q if chosen_q != "-- type your own --" else "",
            placeholder="e.g. Is there anything suspicious about this account?"
        )

        run_agent = st.button("Run Investigation", type="primary", disabled=not bool(question.strip()))

        if run_agent and question.strip():
            with st.spinner("Agent is reasoning and calling tools..."):
                try:
                    from investigation_agent import run_investigation
                    result = run_investigation(st.session_state.processed_docs, question.strip())

                    st.divider()
                    st.markdown("### Final Answer")
                    st.success(result["answer"])

                    st.divider()
                    st.markdown(f"### Reasoning Trace — {result['steps_taken']} tool calls")
                    st.caption(
                        "This is the agent's actual decision path. Each step shows "
                        "what it reasoned, which tool it chose, and what it learned "
                        "before deciding the next step."
                    )

                    for i, step in enumerate(result["trace"]):
                        with st.expander(f"Step {i+1}: called `{step['tool']}`", expanded=True):
                            st.markdown(f"**Thought:** {step['thought']}")
                            st.markdown(f"**Tool called:** `{step['tool']}`")
                            st.markdown(f"**Input given to tool:** `{step['tool_input']}`")
                            st.markdown(f"**Observation returned:**")
                            st.code(step["observation"], language=None)

                    if result["steps_taken"] == 0:
                        st.info("The agent answered directly without needing any tool calls.")

                except Exception as e:
                    st.error(f"Investigation failed: {str(e)}")