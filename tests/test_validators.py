from src.validators import (
    is_valid_email,
    is_valid_phone,
    normalize_tech_stack,
    parse_csv_list,
    parse_years_of_experience,
)


def test_email_validator() -> None:
    assert is_valid_email("candidate@example.com")
    assert not is_valid_email("candidate@")


def test_phone_validator() -> None:
    assert is_valid_phone("+1 415-555-7788")
    assert not is_valid_phone("invalid-phone")


def test_experience_parser() -> None:
    assert parse_years_of_experience("4") == 4.0
    assert parse_years_of_experience("4.5") == 4.5
    assert parse_years_of_experience("-1") is None


def test_csv_parser() -> None:
    assert parse_csv_list("backend engineer, ml engineer") == [
        "backend engineer",
        "ml engineer",
    ]


def test_tech_normalization() -> None:
    assert normalize_tech_stack("Python, python, Django, PYTHON") == [
        "Python",
        "Django",
    ]
