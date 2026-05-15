"""Tests AUTH-MFA-003 — codes de recuperation MFA a usage unique."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
pytest.importorskip("forge_mvc_mfa")

from core.auth import (
    InvalidMfaRecoveryCodeError,
)
from forge_mvc_mfa import (
    AuthMfaRecoveryCode,
    RecoveryCodesSetup,
    consume_recovery_code,
    create_recovery_codes,
    generate_recovery_code,
    hash_recovery_code,
    is_valid_recovery_code_record,
    normalize_recovery_code,
    normalize_recovery_code_record,
    validate_recovery_code_contract,
    verify_recovery_code,
)


# ---------------------------------------------------------------------------
# generate_recovery_code
# ---------------------------------------------------------------------------


def test_generate_recovery_code_returns_string():
    assert isinstance(generate_recovery_code(), str)


def test_generate_recovery_code_returns_non_empty():
    assert generate_recovery_code() != ""


def test_generate_recovery_code_two_calls_differ():
    assert generate_recovery_code() != generate_recovery_code()


def test_generate_recovery_code_contains_dashes():
    code = generate_recovery_code()
    assert "-" in code


def test_generate_recovery_code_has_four_groups():
    code = generate_recovery_code()
    parts = code.split("-")
    assert len(parts) == 4


def test_generate_recovery_code_groups_are_four_chars():
    code = generate_recovery_code()
    for part in code.split("-"):
        assert len(part) == 4


def test_generate_recovery_code_no_ambiguous_chars():
    ambiguous = set("OI01")
    for _ in range(20):
        code = generate_recovery_code()
        assert not (set(code.replace("-", "")) & ambiguous), (
            f"Caractere ambigu trouve dans : {code}"
        )


def test_generate_recovery_code_uses_expected_alphabet():
    allowed = set("ABCDEFGHJKLMNPQRSTUVWXYZ23456789-")
    for _ in range(20):
        code = generate_recovery_code()
        assert all(c in allowed for c in code), f"Caractere inattendu dans : {code}"


# ---------------------------------------------------------------------------
# normalize_recovery_code
# ---------------------------------------------------------------------------


def test_normalize_recovery_code_accepts_valid_code():
    code = generate_recovery_code()
    result = normalize_recovery_code(code)
    assert isinstance(result, str)
    assert result != ""


def test_normalize_recovery_code_uppercases():
    result = normalize_recovery_code("abcd-efgh-ijkl-mnpq")
    assert result == "ABCD-EFGH-IJKL-MNPQ"


def test_normalize_recovery_code_strips_spaces():
    code = generate_recovery_code()
    result = normalize_recovery_code(f"  {code}  ")
    assert result == code


def test_normalize_recovery_code_rejects_empty_string():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        normalize_recovery_code("")


def test_normalize_recovery_code_rejects_whitespace_only():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        normalize_recovery_code("   ")


def test_normalize_recovery_code_rejects_none():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        normalize_recovery_code(None)


def test_normalize_recovery_code_rejects_non_string():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        normalize_recovery_code(12345)


# ---------------------------------------------------------------------------
# hash_recovery_code
# ---------------------------------------------------------------------------


def test_hash_recovery_code_returns_64_chars():
    code = generate_recovery_code()
    h = hash_recovery_code(code)
    assert len(h) == 64


def test_hash_recovery_code_is_hex():
    code = generate_recovery_code()
    h = hash_recovery_code(code)
    assert all(c in "0123456789abcdef" for c in h)


def test_hash_recovery_code_does_not_return_code():
    code = generate_recovery_code()
    h = hash_recovery_code(code)
    assert h != code


def test_hash_recovery_code_is_deterministic():
    code = generate_recovery_code()
    assert hash_recovery_code(code) == hash_recovery_code(code)


def test_hash_recovery_code_differs_for_different_codes():
    code1 = generate_recovery_code()
    code2 = generate_recovery_code()
    assert hash_recovery_code(code1) != hash_recovery_code(code2)


def test_hash_recovery_code_case_insensitive_via_normalize():
    code = generate_recovery_code()
    assert hash_recovery_code(code) == hash_recovery_code(code.lower())


# ---------------------------------------------------------------------------
# verify_recovery_code
# ---------------------------------------------------------------------------


def test_verify_recovery_code_returns_true_with_correct_code():
    code = generate_recovery_code()
    h = hash_recovery_code(code)
    assert verify_recovery_code(code, h) is True


def test_verify_recovery_code_returns_true_despite_case():
    code = generate_recovery_code()
    h = hash_recovery_code(code)
    assert verify_recovery_code(code.lower(), h) is True


def test_verify_recovery_code_returns_false_with_wrong_code():
    code = generate_recovery_code()
    h = hash_recovery_code(code)
    other = generate_recovery_code()
    assert verify_recovery_code(other, h) is False


def test_verify_recovery_code_returns_false_with_empty_code():
    code = generate_recovery_code()
    h = hash_recovery_code(code)
    assert verify_recovery_code("", h) is False


def test_verify_recovery_code_returns_false_with_empty_hash():
    code = generate_recovery_code()
    assert verify_recovery_code(code, "") is False


def test_verify_recovery_code_returns_false_with_invalid_hash():
    code = generate_recovery_code()
    assert verify_recovery_code(code, "not-a-valid-hash") is False


def test_verify_recovery_code_does_not_raise():
    verify_recovery_code("bad", "bad")


# ---------------------------------------------------------------------------
# validate_recovery_code_contract
# ---------------------------------------------------------------------------


def _valid_hash() -> str:
    return hash_recovery_code(generate_recovery_code())


def _valid_dict(**overrides):
    base = {"id": None, "user_id": 1, "code_hash": _valid_hash()}
    base.update(overrides)
    return base


def test_validate_accepts_auth_mfa_recovery_code():
    record = AuthMfaRecoveryCode(id=None, user_id=1, code_hash=_valid_hash())
    assert validate_recovery_code_contract(record) is None


def test_validate_accepts_valid_dict():
    assert validate_recovery_code_contract(_valid_dict()) is None


def test_validate_accepts_id_none():
    assert validate_recovery_code_contract(_valid_dict(id=None)) is None


def test_validate_accepts_id_positive_int():
    assert validate_recovery_code_contract(_valid_dict(id=5)) is None


def test_validate_rejects_id_zero():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(_valid_dict(id=0))


def test_validate_rejects_id_negative():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(_valid_dict(id=-1))


def test_validate_rejects_id_bool():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(_valid_dict(id=True))


def test_validate_rejects_user_id_zero():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(_valid_dict(user_id=0))


def test_validate_rejects_user_id_negative():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(_valid_dict(user_id=-1))


def test_validate_rejects_empty_code_hash():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(_valid_dict(code_hash=""))


def test_validate_rejects_short_code_hash():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(_valid_dict(code_hash="abc123"))


def test_validate_rejects_non_hex_code_hash():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(_valid_dict(code_hash="z" * 64))


def test_validate_rejects_missing_user_id():
    data = {k: v for k, v in _valid_dict().items() if k != "user_id"}
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(data)


def test_validate_rejects_missing_code_hash():
    data = {k: v for k, v in _valid_dict().items() if k != "code_hash"}
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(data)


def test_validate_rejects_non_dict_non_record():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract("bad")
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(None)
    with pytest.raises(InvalidMfaRecoveryCodeError):
        validate_recovery_code_contract(42)


# ---------------------------------------------------------------------------
# normalize_recovery_code_record
# ---------------------------------------------------------------------------


def test_normalize_from_dict():
    record = normalize_recovery_code_record(_valid_dict())
    assert isinstance(record, AuthMfaRecoveryCode)
    assert record.user_id == 1


def test_normalize_from_auth_mfa_recovery_code():
    original = AuthMfaRecoveryCode(id=None, user_id=1, code_hash=_valid_hash())
    result = normalize_recovery_code_record(original)
    assert result is original


def test_normalize_preserves_optional_fields():
    now = datetime.now(tz=timezone.utc)
    data = _valid_dict(used_at=now, created_at=now, updated_at=now)
    record = normalize_recovery_code_record(data)
    assert record.used_at == now
    assert record.created_at == now


def test_normalize_raises_on_invalid():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        normalize_recovery_code_record({"user_id": 1})


# ---------------------------------------------------------------------------
# is_valid_recovery_code_record
# ---------------------------------------------------------------------------


def test_is_valid_returns_true_for_valid_record():
    record = AuthMfaRecoveryCode(id=None, user_id=1, code_hash=_valid_hash())
    assert is_valid_recovery_code_record(record) is True


def test_is_valid_returns_false_for_dict():
    assert is_valid_recovery_code_record(_valid_dict()) is False


def test_is_valid_returns_false_for_none():
    assert is_valid_recovery_code_record(None) is False


def test_is_valid_returns_false_for_invalid_record():
    bad = AuthMfaRecoveryCode(id=None, user_id=0, code_hash=_valid_hash())
    assert is_valid_recovery_code_record(bad) is False


# ---------------------------------------------------------------------------
# create_recovery_codes
# ---------------------------------------------------------------------------


def test_create_recovery_codes_returns_setup():
    result = create_recovery_codes(user_id=1)
    assert isinstance(result, RecoveryCodesSetup)


def test_create_recovery_codes_generates_10_by_default():
    result = create_recovery_codes(user_id=1)
    assert len(result.raw_codes) == 10
    assert len(result.code_records) == 10


def test_create_recovery_codes_generates_count_records():
    result = create_recovery_codes(user_id=1, count=5)
    assert len(result.raw_codes) == 5
    assert len(result.code_records) == 5


def test_create_recovery_codes_raw_codes_are_strings():
    result = create_recovery_codes(user_id=1, count=3)
    for raw in result.raw_codes:
        assert isinstance(raw, str)
        assert raw != ""


def test_create_recovery_codes_no_raw_code_in_records():
    result = create_recovery_codes(user_id=1, count=5)
    for raw in result.raw_codes:
        for record in result.code_records:
            assert raw != record.code_hash


def test_create_recovery_codes_code_hashes_are_unique():
    result = create_recovery_codes(user_id=1, count=10)
    hashes = [r.code_hash for r in result.code_records]
    assert len(set(hashes)) == 10


def test_create_recovery_codes_records_have_correct_user_id():
    result = create_recovery_codes(user_id=42, count=3)
    for record in result.code_records:
        assert record.user_id == 42


def test_create_recovery_codes_records_id_is_none():
    result = create_recovery_codes(user_id=1, count=3)
    for record in result.code_records:
        assert record.id is None


def test_create_recovery_codes_used_at_is_none():
    result = create_recovery_codes(user_id=1, count=3)
    for record in result.code_records:
        assert record.used_at is None


def test_create_recovery_codes_fills_created_at():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    result = create_recovery_codes(user_id=1, count=2, now=now)
    for record in result.code_records:
        assert record.created_at == now


def test_create_recovery_codes_verify_codes_match_records():
    result = create_recovery_codes(user_id=1, count=5)
    for raw, record in zip(result.raw_codes, result.code_records):
        assert verify_recovery_code(raw, record.code_hash) is True


def test_create_recovery_codes_rejects_user_id_zero():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        create_recovery_codes(user_id=0)


def test_create_recovery_codes_rejects_user_id_negative():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        create_recovery_codes(user_id=-1)


def test_create_recovery_codes_rejects_user_id_bool():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        create_recovery_codes(user_id=True)


def test_create_recovery_codes_rejects_count_zero():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        create_recovery_codes(user_id=1, count=0)


def test_create_recovery_codes_rejects_count_negative():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        create_recovery_codes(user_id=1, count=-1)


def test_create_recovery_codes_rejects_count_bool():
    with pytest.raises(InvalidMfaRecoveryCodeError):
        create_recovery_codes(user_id=1, count=True)


# ---------------------------------------------------------------------------
# consume_recovery_code
# ---------------------------------------------------------------------------


def _make_record(user_id: int = 1) -> tuple[str, AuthMfaRecoveryCode]:
    setup = create_recovery_codes(user_id=user_id, count=1)
    return setup.raw_codes[0], setup.code_records[0]


def test_consume_recovery_code_returns_record_with_used_at():
    raw, record = _make_record()
    consumed = consume_recovery_code(raw, record)
    assert consumed is not None
    assert consumed.used_at is not None


def test_consume_recovery_code_sets_used_at_to_now():
    now = datetime(2025, 6, 1, tzinfo=timezone.utc)
    raw, record = _make_record()
    consumed = consume_recovery_code(raw, record, now=now)
    assert consumed.used_at == now
    assert consumed.updated_at == now


def test_consume_recovery_code_preserves_id():
    raw, record = _make_record()
    consumed = consume_recovery_code(raw, record)
    assert consumed.id == record.id


def test_consume_recovery_code_preserves_user_id():
    raw, record = _make_record(user_id=7)
    consumed = consume_recovery_code(raw, record)
    assert consumed.user_id == 7


def test_consume_recovery_code_preserves_code_hash():
    raw, record = _make_record()
    consumed = consume_recovery_code(raw, record)
    assert consumed.code_hash == record.code_hash


def test_consume_recovery_code_preserves_created_at():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    setup = create_recovery_codes(user_id=1, count=1, now=now)
    raw = setup.raw_codes[0]
    record = setup.code_records[0]
    consumed = consume_recovery_code(raw, record)
    assert consumed.created_at == now


def test_consume_recovery_code_returns_none_with_wrong_code():
    _, record = _make_record()
    assert consume_recovery_code("XXXX-XXXX-XXXX-XXXX", record) is None


def test_consume_recovery_code_returns_none_if_already_used():
    raw, record = _make_record()
    consumed = consume_recovery_code(raw, record)
    assert consumed is not None
    assert consume_recovery_code(raw, consumed) is None


def test_consume_recovery_code_does_not_modify_original():
    raw, record = _make_record()
    original_used_at = record.used_at
    consume_recovery_code(raw, record)
    assert record.used_at == original_used_at


def test_consume_recovery_code_accepts_dict():
    raw, record = _make_record()
    record_dict = {
        "id": record.id,
        "user_id": record.user_id,
        "code_hash": record.code_hash,
    }
    consumed = consume_recovery_code(raw, record_dict)
    assert consumed is not None
    assert consumed.status if hasattr(consumed, "status") else consumed.used_at is not None


def test_consume_recovery_code_returns_none_for_invalid_record():
    assert consume_recovery_code("XXXX-XXXX-XXXX-XXXX", None) is None
    assert consume_recovery_code("XXXX-XXXX-XXXX-XXXX", "bad") is None


# ---------------------------------------------------------------------------
# API importable depuis core.auth
# ---------------------------------------------------------------------------


def test_api_importable_from_forge_mvc_mfa():
    from forge_mvc_mfa import (
        AuthMfaRecoveryCode,
        RecoveryCodesSetup,
        consume_recovery_code,
        create_recovery_codes,
        generate_recovery_code,
        hash_recovery_code,
        is_valid_recovery_code_record,
        normalize_recovery_code,
        normalize_recovery_code_record,
        validate_recovery_code_contract,
        verify_recovery_code,
    )
    from core.auth.exceptions import InvalidMfaRecoveryCodeError
    assert callable(generate_recovery_code)
    assert callable(normalize_recovery_code)
    assert callable(hash_recovery_code)
    assert callable(verify_recovery_code)
    assert callable(create_recovery_codes)
    assert callable(consume_recovery_code)
    assert callable(validate_recovery_code_contract)
    assert callable(normalize_recovery_code_record)
    assert callable(is_valid_recovery_code_record)
    assert AuthMfaRecoveryCode is not None
    assert RecoveryCodesSetup is not None
    assert issubclass(InvalidMfaRecoveryCodeError, ValueError)


# ---------------------------------------------------------------------------
# Perimetres exclus
# ---------------------------------------------------------------------------


def test_no_mfa_challenge():
    import core.auth.session as session_module
    assert not hasattr(session_module, "mfa_challenge")
    assert not hasattr(session_module, "require_mfa")


def test_login_user_not_touched():
    from core.auth import login_user
    assert callable(login_user)


def test_no_qr_code():
    setup = create_recovery_codes(user_id=1)
    assert not hasattr(setup, "qr_code")
    assert not hasattr(setup, "provisioning_uri")


def test_no_db_access(monkeypatch):
    calls = []
    monkeypatch.setattr("mariadb.connect", lambda *a, **kw: calls.append(True), raising=False)
    setup = create_recovery_codes(user_id=1, count=3)
    raw = setup.raw_codes[0]
    consume_recovery_code(raw, setup.code_records[0])
    assert calls == []
