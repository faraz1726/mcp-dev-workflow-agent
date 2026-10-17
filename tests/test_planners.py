import pytest

from devflow import planners
from devflow.validation import (ValidationError, validate_feature_request,
                                validate_project_key, validate_risk_level)


def test_detects_capabilities():
    caps = planners.detect_capabilities("Add login and let users upload a photo")
    assert "authentication" in caps and "file_upload" in caps


def test_fallback_to_core_when_nothing_detected():
    reqs = planners.build_requirements("Make the thing better for everyone")
    assert reqs.functional_requirements and reqs.user_stories
    assert "core_crud" in reqs.detected_capabilities[0]


def test_requirements_structure():
    reqs = planners.build_requirements("Add payment checkout for orders")
    assert "payments" in reqs.detected_capabilities
    assert len(reqs.acceptance_criteria) >= 2
    assert reqs.open_questions


def test_tickets_keys_points_and_file(tmp_path, monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(planners, "DATA_DIR", tmp_path)
    bundle = planners.build_tickets("Add search with filters for products", "SHOP")
    assert bundle.tickets[0].key == "SHOP-1"
    assert bundle.total_story_points == sum(t.story_points for t in bundle.tickets)
    saved_name = Path(bundle.saved_to).name
    assert (tmp_path / saved_name).exists()
    assert planners.list_saved(tmp_path) == [saved_name]

def test_backend_plan_has_endpoints_and_models():
    plan = planners.build_backend_plan("User login and password reset")
    assert any(e.path == "/auth/login" for e in plan.endpoints)
    assert any(m.name == "User" for m in plan.data_models)


def test_high_risk_checklist_is_longer():
    low = planners.build_checklist("Add payment checkout", "low")
    high = planners.build_checklist("Add payment checkout", "high")
    assert len(high.items) > len(low.items)
    assert any("feature flag" in i.item.lower() for i in high.items)


def test_read_saved_blocks_path_traversal(tmp_path):
    with pytest.raises(FileNotFoundError):
        planners.read_saved("../../etc/passwd", tmp_path)


@pytest.mark.parametrize("bad", ["", "short", "x" * 2001, None])
def test_bad_feature_request(bad):
    with pytest.raises(ValidationError):
        validate_feature_request(bad)


def test_project_key_and_risk_validation():
    assert validate_project_key(" proj ") == "PROJ"
    with pytest.raises(ValidationError):
        validate_project_key("1bad key")
    with pytest.raises(ValidationError):
        validate_risk_level("extreme")
