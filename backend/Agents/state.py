from typing import TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage


class MoviState(TypedDict):
    """State schema for Movi AI agent using LangGraph"""

    # Raw user input
    user_msg: str
    current_page: str

    # Chat history for LLM
    messages: List[BaseMessage]

    # Image analysis (optional)
    image_base64: Optional[str]       # Input: base64 encoded image from frontend
    image_content: Optional[str]      # Output: LLM's description/analysis of the image

    # Intent classification
    intent: Optional[str]
    tool_name: Optional[str]
    entities: Optional[Dict[str, Any]]

    # Missing info / next-step requirements
    needs_user_input: bool

    # Consequence / confirmation flags
    consequences: Optional[Dict[str, Any]]
    awaiting_confirmation: bool

    # Results
    tool_result: Optional[Dict[str, Any]]
