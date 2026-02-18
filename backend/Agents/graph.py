import os
from typing import Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from Agents.nodes import intent_node, response_node, consequence_node, tool_call_node
from Agents.tools import ALL_TOOLS
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from Agents.state import MoviState
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangSmith Tracing Configuration
# Set environment variables for automatic tracing
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGSMITH_TRACING", "true")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "moveinsync-production")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# Enable tracing for observability
ENABLE_TRACING = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"

if ENABLE_TRACING and os.getenv("LANGSMITH_API_KEY"):
    print("✅ LangSmith tracing enabled")
    print(f"📊 Project: {os.getenv('LANGSMITH_PROJECT')}")
else:
    print("⚠️  LangSmith tracing disabled (no API key found)")


def build_movi_graph(llm: ChatOpenAI, ALL_TOOLS: List[BaseTool]) -> Any:
    """
    Builds the Movi agent graph with LangGraph's interrupt mechanism.

    The graph now uses interrupt() in the consequence_node to pause execution
    and wait for human approval. No separate confirmation nodes needed.
    """

    graph = StateGraph(MoviState)

    # 1. Add nodes
    graph.add_node("intent", lambda s: intent_node(s, llm, ALL_TOOLS))
    graph.add_node("consequence", consequence_node)
    graph.add_node("tool_call", lambda s: tool_call_node(s, ALL_TOOLS))
    graph.add_node("response", lambda s: response_node(s, llm))

    # 2. Entry → Intent
    graph.set_entry_point("intent")

    # 3. Intent → Consequence (check for high-impact tools)
    graph.add_edge("intent", "consequence")

    # 4. Consequence → Tool Call
    # Note: If consequence_node calls interrupt(), execution pauses here
    # The interrupt() returns when user calls graph.invoke(Command(resume=...))
    graph.add_edge("consequence", "tool_call")

    # 5. Tool_call → response
    graph.add_edge("tool_call", "response")

    # 6. Final node
    graph.set_finish_point("response")

    # 7. Compile with checkpointer for interrupt support
    # MemorySaver is for development - use a durable checkpointer in production
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)

# Initialize LLM with tracing metadata
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    model_kwargs={
        "metadata": {
            "service": "moveinsync",
            "component": "movi-agent",
            "version": "1.0.0"
        }
    } if ENABLE_TRACING else {}
)

# Build the graph with checkpointer
app = build_movi_graph(llm, ALL_TOOLS)

# Add metadata for graph-level tracing
if ENABLE_TRACING:
    print("🔍 Traces available at: https://smith.langchain.com/")