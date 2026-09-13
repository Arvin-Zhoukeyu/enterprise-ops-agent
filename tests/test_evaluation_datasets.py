import json
from pathlib import Path


DATASET_PATH = Path("evaluation/dataset.json")


def load_dataset() -> dict:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_unified_dataset_counts_are_correct():
    dataset = load_dataset()
    assert len(dataset["common_agent_cases"]) == 60
    assert len(dataset["workflow_extension_cases"]) == 30
    assert len(dataset["rag_cases"]) == 20
    assert dataset["metadata"]["unique_case_count"] == 110


def test_all_case_ids_are_unique():
    dataset = load_dataset()
    all_cases = (
        dataset["common_agent_cases"]
        + dataset["workflow_extension_cases"]
        + dataset["rag_cases"]
    )
    ids = [case["id"] for case in all_cases]
    assert len(ids) == len(set(ids))


def test_common_cases_support_both_agents():
    cases = load_dataset()["common_agent_cases"]
    required_fields = {
        "expected_routing",
        "expected_tool",
        "expected_arguments",
        "expected_route",
        "expected_tools",
        "role",
    }
    assert all(required_fields <= case.keys() for case in cases)


def test_workflow_extension_covers_advanced_capabilities():
    cases = load_dataset()["workflow_extension_cases"]
    assert any(len(case["expected_tools"]) > 1 for case in cases)
    assert any(
        case.get("expected_security_status") == "PERMISSION_DENIED"
        for case in cases
    )
    assert any(
        case.get("expected_security_status") == "APPROVAL_REQUIRED"
        for case in cases
    )


def test_rag_cases_have_relevance_labels():
    cases = load_dataset()["rag_cases"]
    assert all(case["expected_sources"] for case in cases)
