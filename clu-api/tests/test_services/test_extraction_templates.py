import json
import os
import tempfile

from app.services.extraction_templates import (
    BUILT_IN_TEMPLATES,
    list_templates,
    get_template,
    build_schema_for_template,
    get_template_guidelines,
    load_template_from_file,
)


def test_list_templates():
    templates = list_templates()
    names = [t["name"] for t in templates]
    assert "default" in names
    assert "requirements-only" in names
    assert "decisions-only" in names
    assert len(templates) >= 3


def test_get_template_default():
    template = get_template("default")
    assert template["name"] == "default"
    assert "decisions" in template["sections"]
    assert "requirements" in template["sections"]
    assert len(template["sections"]) == 8


def test_get_template_requirements_only():
    template = get_template("requirements-only")
    assert "requirements" in template["sections"]
    assert "technicalConstraints" in template["sections"]
    assert "decisions" not in template["sections"]


def test_get_template_decisions_only():
    template = get_template("decisions-only")
    assert "decisions" in template["sections"]
    assert "actionItems" in template["sections"]
    assert "requirements" not in template["sections"]


def test_get_template_unknown():
    try:
        get_template("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "nonexistent" in str(e)


def test_build_schema_default():
    schema_str = build_schema_for_template("default")
    schema = json.loads(schema_str)
    assert "source" in schema
    assert "decisions" in schema
    assert "requirements" in schema
    assert "risks" in schema
    assert len(schema) == 9  # source + 8 sections


def test_build_schema_requirements_only():
    schema_str = build_schema_for_template("requirements-only")
    schema = json.loads(schema_str)
    assert "source" in schema
    assert "requirements" in schema
    assert "technicalConstraints" in schema
    assert "openQuestions" in schema
    assert "decisions" not in schema
    assert len(schema) == 4  # source + 3 sections


def test_build_schema_decisions_only():
    schema_str = build_schema_for_template("decisions-only")
    schema = json.loads(schema_str)
    assert "source" in schema
    assert "decisions" in schema
    assert "actionItems" in schema
    assert "participants" in schema
    assert "deferredItems" in schema
    assert "requirements" not in schema
    assert len(schema) == 5  # source + 4 sections


def test_get_template_guidelines():
    guidelines = get_template_guidelines("default")
    assert "EVERYTHING" in guidelines

    guidelines = get_template_guidelines("requirements-only")
    assert "requirements" in guidelines.lower()


def test_load_template_from_file():
    custom_template = {
        "name": "custom-test",
        "description": "Test template",
        "sections": ["decisions", "risks"],
        "guidelines": "Focus on decisions and risks only.",
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(custom_template, f)
        temp_path = f.name

    try:
        loaded = load_template_from_file(temp_path)
        assert loaded["name"] == "custom-test"
        assert "decisions" in loaded["sections"]

        # Should now be available via get_template
        assert get_template("custom-test")["name"] == "custom-test"
    finally:
        os.unlink(temp_path)
        # Clean up the registered template
        BUILT_IN_TEMPLATES.pop("custom-test", None)


def test_load_template_missing_file():
    try:
        load_template_from_file("/nonexistent/template.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass


def test_load_template_invalid_sections():
    custom_template = {
        "name": "bad-sections",
        "sections": ["decisions", "nonexistent_section"],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(custom_template, f)
        temp_path = f.name

    try:
        load_template_from_file(temp_path)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "nonexistent_section" in str(e)
    finally:
        os.unlink(temp_path)
