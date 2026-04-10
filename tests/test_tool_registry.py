import pytest
from aura.action.tool_registry import ToolRegistry


class TestToolRegistry:
    def test_registry_initialization(self):
        registry = ToolRegistry()
        assert registry is not None
        assert len(registry.tools) > 0

    def test_calculator_valid_expression(self):
        registry = ToolRegistry()
        result = registry.call("calculator", expression="2+2*3")
        assert result["success"] is True
        assert result["result"] == 8

    def test_calculator_invalid_characters(self):
        registry = ToolRegistry()
        result = registry.call("calculator", expression="2+2*exec('ls')")
        assert result["success"] is False

    def test_get_date(self):
        registry = ToolRegistry()
        result = registry.call("get_date")
        assert result is not None

    def test_list_tools(self):
        registry = ToolRegistry()
        tools_list = registry.list_tools()
        assert "Available tools:" in tools_list
        assert "calculator" in tools_list


class TestToolSecurity:
    def test_calculator_blocks_dangerous_expressions(self):
        registry = ToolRegistry()
        result = registry.call("calculator", expression="__import__('os').system('ls')")
        assert result["success"] is False
