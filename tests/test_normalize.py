from shellsensei.normalize import command_hash, normalize_command


def test_normalize_command_masks_common_dynamic_tokens() -> None:
    raw = 'curl "https://example.com/a/b" C:\\temp\\file.txt /var/log/app.log 123'
    normalized = normalize_command(raw)
    assert normalized.startswith("curl ")
    assert "<path>" in normalized
    assert "<num>" in normalized
    assert "<str>" in normalized


def test_command_hash_is_stable() -> None:
    norm = "git status"
    assert command_hash(norm) == command_hash(norm)
    assert len(command_hash(norm)) == 16
