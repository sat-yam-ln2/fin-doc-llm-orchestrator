from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_groq import ChatGroq
from config import GROQ_API_KEY, EXTRACTOR_MODEL
from vector_store import query_documents
from entity_crossref import build_crossref_table
import json


def build_investigation_agent(processed_docs: list):
    """
    Builds a ReAct agent with three tools, all scoped to the
    documents processed in this session.

    The agent decides on its own which tools to call and in what
    order, based on the question it is asked. This is different
    from the fixed pipeline — there is no hardcoded sequence here.
    """

    # ── Tool 1: Vector search ────────────────────────────────────
    def search_documents_tool(query: str) -> str:
        """Searches the vector database for documents semantically
        related to the query. Use this to find documents mentioning
        specific topics, amounts, or activities."""
        results = query_documents(query, k=3)
        if not results:
            return "No matching documents found in the vector store."
        output = []
        for r in results:
            doc_type = r["metadata"].get("doc_type", "unknown")
            preview = r["content"][:300].replace("\n", " ")
            output.append(f"[{doc_type}] {preview}")
        return "\n\n".join(output)

    # ── Tool 2: Entity cross-reference lookup ────────────────────
    def check_entity_connections_tool(entity_value: str) -> str:
        """Checks if a specific entity (account number, person name,
        or company name) appears in more than one processed document.
        Use this to find connections between documents for a given
        account, name, or company."""
        all_entities = build_crossref_table(processed_docs)
        matches = [
            e for e in all_entities
            if entity_value.lower() in e["value"].lower()
        ]
        if not matches:
            return f"No entity matching '{entity_value}' found in processed documents."

        seen = set()
        lines = []
        for e in matches:
            key = (e["value"], tuple(sorted(e["appears_in_docs"])))
            if key not in seen:
                seen.add(key)
                cross = "YES — appears in multiple documents" if e["is_cross_doc"] else "No, single document only"
                lines.append(
                    f"Entity: {e['value']} ({e['entity_type']}) | "
                    f"Found in documents: {e['appears_in_docs']} | "
                    f"Cross-document match: {cross}"
                )
        return "\n".join(lines)

    # ── Tool 3: Anomaly flags lookup ─────────────────────────────
    def get_anomaly_flags_tool(filter_text: str) -> str:
        """Returns all anomaly flags (rule-based and Isolation Forest)
        detected across processed documents. Pass 'all' to see
        everything, or a document type like 'bank_statement' to filter."""
        lines = []
        for i, doc in enumerate(processed_docs):
            if filter_text.strip().lower() not in ["all", ""] and \
               filter_text.strip().lower() not in doc["doc_type"].lower():
                continue
            flags = doc.get("anomalies", [])
            if not flags:
                continue
            for f in flags:
                lines.append(
                    f"Doc {i+1} ({doc['doc_type']}): {f['rule']} "
                    f"[{f['severity']}] — {f['detail']}"
                )
        if not lines:
            return "No anomaly flags found matching that filter."
        return "\n".join(lines)

    # ── Tool 4: Risk summary lookup ──────────────────────────────
    def get_risk_summaries_tool(filter_text: str) -> str:
        """Returns the risk level and recommended action for processed
        documents. Pass 'all' to see everything or a document type to filter."""
        lines = []
        for i, doc in enumerate(processed_docs):
            if filter_text.strip().lower() not in ["all", ""] and \
               filter_text.strip().lower() not in doc["doc_type"].lower():
                continue
            risk = doc["risk_summary"]
            lines.append(
                f"Doc {i+1} ({doc['doc_type']}): risk_level={risk['risk_level']} "
                f"| action={risk['recommended_action']}"
            )
        if not lines:
            return "No risk summaries found matching that filter."
        return "\n".join(lines)

    tools = [
        Tool(
            name="search_documents",
            func=search_documents_tool,
            description=(
                "Search the vector database for documents related to a topic "
                "or keyword. Input should be a natural language query, e.g. "
                "'wire transfers' or 'suspicious activity'."
            )
        ),
        Tool(
            name="check_entity_connections",
            func=check_entity_connections_tool,
            description=(
                "Check if an account number, person name, or company name "
                "appears across multiple documents. Input should be the "
                "exact or partial entity value, e.g. '4821-0093-2211' or "
                "'Omega Capital'."
            )
        ),
        Tool(
            name="get_anomaly_flags",
            func=get_anomaly_flags_tool,
            description=(
                "Get all anomaly flags detected across documents. Input "
                "should be 'all' or a document type like 'bank_statement'."
            )
        ),
        Tool(
            name="get_risk_summaries",
            func=get_risk_summaries_tool,
            description=(
                "Get risk levels and recommended actions for processed "
                "documents. Input should be 'all' or a document type."
            )
        ),
    ]

    # ── LLM for the agent — uses the strong model since reasoning ──
    # over multiple tool calls is a harder task than classification
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=EXTRACTOR_MODEL,
        temperature=0
    )

    # ── ReAct prompt template ────────────────────────────────────
    # This is the standard ReAct format: the model must output
    # Thought, Action, Action Input, Observation in a loop until
    # it reaches Final Answer.
    react_prompt = PromptTemplate.from_template("""
You are a fraud investigation assistant with access to tools that search
processed financial documents. Answer the question using the tools available.
Reason step by step about what you need to find out before answering.

You have access to the following tools:

{tools}

Use the following format strictly:

Question: the input question you must answer
Thought: you should always think about what to do next
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original question, written for a
fraud analyst, citing specific documents, entities, and risk levels found

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")

    agent = create_react_agent(llm, tools, react_prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6,
        return_intermediate_steps=True
    )

    return agent_executor


def run_investigation(processed_docs: list, question: str) -> dict:
    """
    Runs the ReAct agent on a question and returns both the final
    answer and the full reasoning trace (which tools it called,
    in what order, with what results).
    
    The reasoning trace is what proves this is a real agent and
    not a single LLM call pretending to be one.
    """
    agent_executor = build_investigation_agent(processed_docs)

    result = agent_executor.invoke({"input": question})

    trace = []
    for step in result.get("intermediate_steps", []):
        action, observation = step
        trace.append({
            "tool": action.tool,
            "tool_input": action.tool_input,
            "thought": action.log.split("Action:")[0].replace("Thought:", "").strip(),
            "observation": str(observation)[:500]
        })

    return {
        "answer": result.get("output", "No answer generated."),
        "trace": trace,
        "steps_taken": len(trace)
    }