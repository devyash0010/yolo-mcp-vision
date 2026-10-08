"""End-to-end integration tests connecting YOLO, Scene Engine, MCP Tools, and Agent Client."""

import os
import pytest
from app.agent.client import MCPVisionClient
from app.mcp import tools


@pytest.fixture(scope="module", autouse=True)
def init_sample_scene():
    """Ensure the sample image is detected and scene context populated."""
    sample_path = "sample_data/bus.jpg"
    if os.path.exists(sample_path):
        tools.detect_objects(image_path=sample_path)


def test_mcp_detect_objects_tool():
    sample_path = "sample_data/bus.jpg"
    res = tools.detect_objects(image_path=sample_path if os.path.exists(sample_path) else None)
    assert res.get("success") is True
    assert "scene_id" in res
    assert "detections_count" in res


def test_mcp_count_objects_tool():
    total_res = tools.count_objects()
    assert "total_count" in total_res
    assert total_res["total_count"] >= 0

    person_res = tools.count_objects(object_class="person")
    assert person_res["object_class"] == "person"
    assert "count" in person_res


def test_mcp_find_object_location_tool():
    loc_res = tools.find_object_location(object_class="bus")
    assert "found" in loc_res
    if loc_res["found"]:
        assert len(loc_res["locations"]) > 0
        assert "position" in loc_res["locations"][0]


def test_mcp_get_objects_by_position_tool():
    res = tools.get_objects_by_position(position="center")
    assert res["position"] == "center"
    assert isinstance(res["objects"], list)


def test_mcp_get_relationships_tool():
    rels = tools.get_relationships()
    assert "count" in rels
    assert isinstance(rels["relationships"], list)


def test_mcp_query_scene_tool():
    q_res = tools.query_scene(query="What objects do you see?")
    assert "answer" in q_res
    assert len(q_res["answer"]) > 0


@pytest.mark.anyio
async def test_mcp_agent_client_end_to_end():
    client = MCPVisionClient()
    answer = await client.ask("How many people are there?")
    assert isinstance(answer, str)
    assert len(answer) > 0

