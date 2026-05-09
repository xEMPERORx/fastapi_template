"""Tests for the Data Validation and Sanitization skill."""

import pytest
from pydantic import BaseModel, Field
from app.core.data_validation import (
    safe_filename,
    validate_model_fields,
    validate_required_fields,
    sanitize_dict,
)


class TestSafeFilename:
    def test_normal_filename_passes(self):
        assert safe_filename("report.pdf") == "report.pdf"

    def test_path_traversal_stripped(self):
        result = safe_filename("../../../etc/passwd")
        assert ".." not in result
        assert "etc" in result or "passwd" in result

    def test_special_chars_replaced(self):
        result = safe_filename("file<>:*?name.txt")
        for ch in ("<", ">", ":", "*", "?"):
            assert ch not in result

    def test_too_long_truncated(self):
        long_name = "a" * 300 + ".txt"
        result = safe_filename(long_name, max_len=255)
        assert len(result) <= 255
        assert result.endswith(".txt")

    def test_empty_parts_clean(self):
        result = safe_filename("...___file.txt")
        assert result.startswith("file")


class TestValidateModelFields:
    def test_valid_data(self):
        class UserModel(BaseModel):
            name: str
            age: int

        data = {"name": "Alice", "age": 30}
        model = validate_model_fields(data, UserModel)
        assert model.name == "Alice"
        assert model.age == 30

    def test_invalid_data_raises(self):
        class UserModel(BaseModel):
            name: str
            age: int

        with pytest.raises(Exception):
            validate_model_fields({"name": "Bob"}, UserModel)
        with pytest.raises(Exception):
            validate_model_fields({"name": "Bob", "age": "not-a-number"}, UserModel)


class TestValidateRequiredFields:
    def test_all_required_present(self):
        data = {"email": "a@b.com", "password": "secret123"}
        validate_required_fields(data, ["email", "password"])

    def test_missing_required_raises(self):
        with pytest.raises(ValueError, match="Missing required"):
            validate_required_fields({"email": "a@b.com"}, ["email", "password"])

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Missing required"):
            validate_required_fields({"email": "a@b.com", "password": ""}, ["email", "password"])

    def test_none_value_raises(self):
        with pytest.raises(ValueError):
            validate_required_fields({"email": None}, ["email"])


class TestSanitizeDict:
    def test_short_values_preserved(self):
        data = {"key": "short"}
        assert sanitize_dict(data) == {"key": "short"}

    def test_long_strings_truncated(self):
        data = {"long_key": "x" * 20_000}
        result = sanitize_dict(data, max_str_len=500)
        assert len(result["long_key"]) == 500

    def test_nested_dict_sanitized(self):
        data = {"outer": {"inner": "x" * 10_000}}
        result = sanitize_dict(data, max_str_len=100)
        assert len(result["outer"]["inner"]) == 100

    def test_list_of_strings_sanitized(self):
        data = {"items": ["a" * 1000, "b" * 2000]}
        result = sanitize_dict(data, max_str_len=100)
        assert len(result["items"][0]) == 100
        assert len(result["items"][1]) == 100

    def test_non_string_values_preserved(self):
        data = {"count": 42, "active": True, "none_val": None}
        assert sanitize_dict(data) == data