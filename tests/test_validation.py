"""Tests for the Advanced Input Validation skill."""

import pytest
from app.core.validation import (
    sanitize_text,
    strip_html,
    safe_str,
    validate_email,
    validate_strong_password,
    validate_no_sql_injection,
    PaginationParams,
    StrictPaginationParams,
)


class TestSanitization:
    def test_strip_html_encodes_tags(self):
        assert strip_html("<script>alert(1)</script>") != "<script>alert(1)</script>"

    def test_sanitize_text_strips_xss(self):
        result = sanitize_text('<script>alert("xss")</script>Hello')
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_text_strips_sql_injection(self):
        result = sanitize_text("admin' OR 1=1 --")
        assert "OR" not in result or "1=1" not in result

    def test_sanitize_text_strips_javascript_uri(self):
        result = sanitize_text("javascript:alert(1)")
        assert "javascript:" not in result

    def test_safe_str_converts_any_to_clean_string(self):
        assert safe_str(123) == "123"
        assert "<" not in safe_str("<b>bold</b>")


class TestEmailValidation:
    def test_valid_email(self):
        assert validate_email("user@example.com") == "user@example.com"

    def test_valid_email_lowercases(self):
        assert validate_email("User@Example.COM") == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email("not-an-email")

    def test_empty_email_raises(self):
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email("")


class TestPasswordValidation:
    def test_strong_password(self):
        assert validate_strong_password("Abcdef1!") == "Abcdef1!"

    def test_password_too_short(self):
        with pytest.raises(ValueError):
            validate_strong_password("Ab1!")

    def test_password_missing_digit(self):
        with pytest.raises(ValueError):
            validate_strong_password("Abcdefgh!")

    def test_password_missing_special_char(self):
        with pytest.raises(ValueError):
            validate_strong_password("Abcdefg1")

    def test_password_missing_upper(self):
        with pytest.raises(ValueError):
            validate_strong_password("abcdefg1!")

    def test_password_missing_lower(self):
        with pytest.raises(ValueError):
            validate_strong_password("ABCDEFG1!")


class TestSQLInjectionGuard:
    def test_clean_value_passes(self):
        assert validate_no_sql_injection("normal username") == "normal username"

    def test_select_raises(self):
        with pytest.raises(ValueError, match="SQL"):
            validate_no_sql_injection("SELECT * FROM users")

    def test_drop_raises(self):
        with pytest.raises(ValueError, match="SQL"):
            validate_no_sql_injection("DROP TABLE users")


class TestPagination:
    def test_defaults(self):
        p = PaginationParams()
        assert p.page == 1
        assert p.page_size == 20

    def test_invalid_page_rejected(self):
        with pytest.raises(Exception):
            PaginationParams(page=0)

    def test_invalid_page_size_rejected(self):
        with pytest.raises(Exception):
            PaginationParams(page_size=0)

    def test_strict_coerces_strings(self):
        p = StrictPaginationParams(page="3", page_size="50")
        assert p.page == 3
        assert p.page_size == 50

    def test_strict_rejects_bad_strings(self):
        with pytest.raises(ValueError):
            StrictPaginationParams(page="abc")