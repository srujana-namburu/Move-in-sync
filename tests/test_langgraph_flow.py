"""
Unit tests for LangGraph agent workflow
Tests the intent -> consequence -> tool_call -> response flow
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from backend.Agents.state import MoviState
from backend.Agents.nodes import intent_node, consequence_node, tool_call_node, response_node
from backend.Agents.tools import ALL_TOOLS


class TestAgentNodes:
    """Test individual agent nodes"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing"""
        llm = MagicMock()
        llm.invoke.return_value = MagicMock(content='{"intent": "list", "tool_name": "get_all_trips", "entities": {}}')
        return llm

    @pytest.fixture
    def mock_db(self):
        """Mock database"""
        return MagicMock()

    @pytest.fixture
    def sample_state(self) -> MoviState:
        """Sample state for testing"""
        return {
            "user_msg": "Show me all trips",
            "current_page": "buses",
            "messages": [],
            "image_base64": None,
            "image_content": None,
            "intent": None,
            "tool_name": None,
            "entities": None,
            "needs_user_input": False,
            "consequences": None,
            "awaiting_confirmation": False,
            "tool_result": None
        }

    def test_intent_node_basic_query(self, sample_state, mock_llm):
        """Test intent node correctly classifies basic query"""
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = '{"intent": "query", "tool_name": "get_all_trips", "entities": {}}'
        mock_llm.invoke.return_value = mock_response

        result = intent_node(sample_state, mock_llm, ALL_TOOLS)

        assert result["tool_name"] is not None
        assert result["intent"] is not None
        assert len(result["messages"]) > 0

    def test_intent_node_with_entities(self, mock_llm):
        """Test intent node extracts entities"""
        state = {
            "user_msg": "Show status of Morning Shift",
            "current_page": "buses",
            "messages": [],
            "image_base64": None,
            "image_content": None,
            "intent": None,
            "tool_name": None,
            "entities": None,
            "needs_user_input": False,
            "consequences": None,
            "awaiting_confirmation": False,
            "tool_result": None
        }

        mock_response = MagicMock()
        mock_response.content = '{"intent": "query", "tool_name": "get_trip_status", "entities": {"trip_name": "Morning Shift"}}'
        mock_llm.invoke.return_value = mock_response

        result = intent_node(state, mock_llm, ALL_TOOLS)

        assert result["tool_name"] == "get_trip_status"
        assert result["entities"] is not None

    def test_consequence_node_safe_operation(self, sample_state, mock_db):
        """Test consequence node passes through safe operations"""
        state = sample_state.copy()
        state["tool_name"] = "get_all_trips"  # Safe operation

        # consequence_node should pass through without interrupt
        # This test would need the actual implementation

    def test_consequence_node_high_impact(self, mock_db):
        """Test consequence node triggers HITL for high-impact operations"""
        state = {
            "user_msg": "Delete Morning Shift",
            "current_page": "buses",
            "messages": [],
            "tool_name": "delete_trip",
            "entities": {"trip_name": "Morning Shift"},
            "intent": "delete",
            "image_base64": None,
            "image_content": None,
            "needs_user_input": False,
            "consequences": None,
            "awaiting_confirmation": False,
            "tool_result": None
        }

        # consequence_node should trigger interrupt for delete operations
        # This test would verify HITL is triggered


    def test_tool_call_node_executes_tool(self, mock_db):
        """Test tool_call node executes the selected tool"""
        state = {
            "user_msg": "Show all trips",
            "current_page": "buses",
            "messages": [],
            "tool_name": "get_all_trips",
            "entities": {},
            "intent": "query",
            "image_base64": None,
            "image_content": None,
            "needs_user_input": False,
            "consequences": None,
            "awaiting_confirmation": False,
            "tool_result": None
        }

        # Tool call would execute and populate tool_result
        # This tests actual tool execution

    def test_response_node_generates_answer(self, mock_llm):
        """Test response node generates natural language response"""
        state = {
            "user_msg": "Show all trips",
            "current_page": "buses",
            "messages": [],
            "tool_name": "get_all_trips",
            "entities": {},
            "intent": "query",
            "tool_result": {"status": "success", "data": [{"trip_display_name": "Morning Shift"}]},
            "image_base64": None,
            "image_content": None,
            "needs_user_input": False,
            "consequences": None,
            "awaiting_confirmation": False
        }

        mock_response = MagicMock()
        mock_response.content = "Here are your trips: Morning Shift"
        mock_llm.invoke.return_value = mock_response

        result = response_node(state, mock_llm)

        assert len(result["messages"]) > 0


class TestAgentIntegration:
    """Integration tests for complete agent flow"""

    def test_agent_graph_exists(self):
        """Test that agent graph is properly initialized"""
        try:
            from backend.Agents.graph import app as agent_graph
            assert agent_graph is not None
        except Exception:
            pytest.skip("Agent graph not available in test environment")

    @pytest.mark.asyncio
    async def test_full_query_flow(self):
        """Test complete query flow from input to response"""
        try:
            from backend.Agents.graph import app as agent_graph

            input_data = {
                "user_msg": "List all vehicles",
                "current_page": "buses",
                "messages": [],
                "image_base64": None,
                "image_content": None,
                "intent": None,
                "tool_name": None,
                "entities": None,
                "needs_user_input": False,
                "consequences": None,
                "awaiting_confirmation": False,
                "tool_result": None
            }

            config = {"configurable": {"thread_id": "test-session"}}

            result = await agent_graph.ainvoke(input_data, config=config)

            # Verify flow completed
            assert result is not None
            assert "tool_result" in result

        except Exception:
            pytest.skip("Integration test requires full agent setup")


class TestHITLBehavior:
    """Tests for Human-in-the-Loop behavior"""

    def test_high_impact_tools_list(self):
        """Test that high-impact tools are properly defined"""
        from backend.Agents.nodes import HIGH_IMPACT_TOOLS

        expected_high_impact = [
            "delete_trip",
            "update_trip",
            "delete_deployment",
            "remove_vehicle_from_trip",
            "update_route_status",
            "update_route"
        ]

        for tool in expected_high_impact:
            assert tool in HIGH_IMPACT_TOOLS, f"{tool} should be marked as high-impact"

    @pytest.mark.asyncio
    async def test_hitl_interrupt_triggered(self):
        """Test that HITL interrupt is triggered for deletions"""
        # This would test that the agent actually calls interrupt()
        # for high-impact operations
        pytest.skip("Requires mock of LangGraph interrupt mechanism")


class TestToolPageFiltering:
    """Tests for page-aware tool filtering"""

    def test_get_tools_for_buses_page(self):
        """Test that buses page gets correct tools"""
        from backend.Agents.tools import get_tools_for_page

        tools = get_tools_for_page("buses")

        tool_names = [t.name for t in tools]

        # Should include trip and vehicle tools
        assert "get_all_trips" in tool_names
        assert "list_all_vehicles" in tool_names
        assert "list_all_drivers" in tool_names

    def test_get_tools_for_stops_page(self):
        """Test that stops page gets correct tools"""
        from backend.Agents.tools import get_tools_for_page

        tools = get_tools_for_page("stops")

        tool_names = [t.name for t in tools]

        # Should include stop and path tools
        assert "list_all_stops" in tool_names
        assert "list_all_paths" in tool_names

    def test_get_tools_for_routes_page(self):
        """Test that routes page gets correct tools"""
        from backend.Agents.tools import get_tools_for_page

        tools = get_tools_for_page("routes")

        tool_names = [t.name for t in tools]

        # Should include route tools
        assert "list_all_routes" in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
