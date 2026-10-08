"""MCP Client implementation demonstrating AI Agent interaction with MCP tools."""

import asyncio
import sys
from typing import Any, Dict
from app.agent.providers import get_agent_provider
from app.core.logging import logger
from app.mcp import tools


class MCPVisionClient:
    # """
    # Client connecting an AI Agent to MCP vision tools.
    # Can be run as an interactive CLI or invoked programmatically.
    # """

    def __init__(self):
        self.provider = get_agent_provider()
        self.tool_registry = {
            "detect_objects": lambda args: tools.detect_objects(**args),
            "get_current_scene": lambda args: tools.get_current_scene(),
            "get_scene_summary": lambda args: tools.get_scene_summary(),
            "count_objects": lambda args: tools.count_objects(**args),
            "find_objects": lambda args: tools.find_objects(**args),
            "find_object_location": lambda args: tools.find_object_location(**args),
            "get_objects_by_position": lambda args: tools.get_objects_by_position(**args),
            "get_relationships": lambda args: tools.get_relationships(**args),
            "query_scene": lambda args: tools.query_scene(**args),
            "get_detection_metrics": lambda args: tools.get_detection_metrics(),
            "get_system_status": lambda args: tools.get_system_status(),
        }

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Invokes registered MCP tool by name with arguments."""
        if tool_name not in self.tool_registry:
            raise ValueError(f"Unknown MCP tool: {tool_name}")
        return self.tool_registry[tool_name](arguments)

    async def ask(self, query: str) -> str:
        """Submits natural language query to the grounded agent provider."""
        return await self.provider.ask(query, self.call_tool)


async def interactive_cli():
    """Interactive command-line interface for the MCP Vision Client."""
    client = MCPVisionClient()

    tools.detect_objects(image_path="sample_data/bus.jpg")

    print("\n=======================================================")
    print("  YOLO + MCP Computer Vision - AI Agent Client")
    print("  Connected to MCP Server: yolo-vision")
    print("  Type your question or 'exit' / 'quit' to quit.")
    print("=======================================================\n")

    summary = tools.get_scene_summary()
    print(f"Current Scene: {summary.get('summary', 'Ready')}\n")

    sample_questions = [
        "How many people are visible?",
        "Where is the bus?",
        "What objects are on the left?",
        "Is there a laptop?",
        "What is in the center?",
    ]
    print("Try asking:")
    for sq in sample_questions:
        print(f"  - {sq}")
    print()

    while True:
        try:
            query = input("Agent > ")
            if not query.strip():
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("Exiting agent client.")
                break

            response = await client.ask(query)
            print(f"\nResponse: {response}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    asyncio.run(interactive_cli())

