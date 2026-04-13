"""Tests for the deprecated secure storage shim."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from wechat_summarizer.shared import secure_storage


@pytest.fixture(autouse=True)
def reset_secure_storage_singleton() -> None:
    """Keep singleton state isolated across tests."""
    secure_storage.SecureStorage._instance = None
    secure_storage.SecureStorage._key_file = None
    yield
    secure_storage.SecureStorage._instance = None
    secure_storage.SecureStorage._key_file = None


@pytest.mark.unit
class TestMaskSensitive:
    """Tests for value masking helpers."""

    def test_mask_sensitive_handles_empty_and_short_values(self) -> None:
        assert secure_storage.mask_sensitive("") == ""
        assert secure_storage.mask_sensitive("abcd") == "****"
        assert secure_storage.mask_sensitive("abcdefgh", visible_chars=2) == "ab****gh"

    def test_mask_sensitive_preserves_edges_for_long_values(self) -> None:
        assert secure_storage.mask_sensitive("sk-super-secret-token", visible_chars=3) == (
            "sk-" + "*" * 15 + "ken"
        )


@pytest.mark.unit
class TestSecureStorage:
    """Tests for the deprecated ``SecureStorage`` singleton."""

    def test_get_secure_storage_returns_singleton(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(secure_storage.Path, "home", lambda: tmp_path)
        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Linux")

        first = secure_storage.get_secure_storage()
        second = secure_storage.get_secure_storage()

        assert first is second
        assert first._key_file == tmp_path / ".wechat_summarizer" / ".secure_key"
        assert first._use_dpapi is False

    def test_initialize_logs_windows_dpapi_mode(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        mocker,
    ) -> None:
        debug_mock = mocker.patch.object(secure_storage.logger, "debug")

        monkeypatch.setattr(secure_storage.Path, "home", lambda: tmp_path)
        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Windows")
        monkeypatch.setitem(sys.modules, "win32crypt", SimpleNamespace())

        storage = secure_storage.SecureStorage()

        assert storage._use_dpapi is True
        assert any("DPAPI" in str(call.args[0]) for call in debug_mock.call_args_list)

    def test_check_dpapi_available_non_windows_returns_false(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        storage = object.__new__(secure_storage.SecureStorage)
        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Linux")

        assert storage._check_dpapi_available() is False

    def test_check_dpapi_available_windows_with_missing_dependency_returns_false(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        storage = object.__new__(secure_storage.SecureStorage)
        original_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
            if name == "win32crypt":
                raise ImportError("missing win32crypt")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Windows")
        monkeypatch.setattr("builtins.__import__", fake_import)

        assert storage._check_dpapi_available() is False

    def test_check_dpapi_available_windows_with_dependency_returns_true(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        storage = object.__new__(secure_storage.SecureStorage)
        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Windows")
        monkeypatch.setitem(sys.modules, "win32crypt", SimpleNamespace())

        assert storage._check_dpapi_available() is True

    def test_get_machine_key_uses_windows_disk_serial_when_available(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        storage = object.__new__(secure_storage.SecureStorage)

        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Windows")
        monkeypatch.setattr(secure_storage.platform, "node", lambda: "node-a")
        monkeypatch.setattr(secure_storage.platform, "machine", lambda: "x86_64")
        monkeypatch.setattr(secure_storage.Path, "home", lambda: tmp_path)

        class Result:
            returncode = 0
            stdout = "SerialNumber\r\nABC123\r\n"

        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: Result())

        key = storage._get_machine_key()

        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_get_machine_key_handles_subprocess_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        storage = object.__new__(secure_storage.SecureStorage)

        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Windows")
        monkeypatch.setattr(secure_storage.platform, "node", lambda: "node-b")
        monkeypatch.setattr(secure_storage.platform, "machine", lambda: "arm64")
        monkeypatch.setattr(secure_storage.Path, "home", lambda: tmp_path)
        monkeypatch.setattr(
            subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError())
        )

        key = storage._get_machine_key()

        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_get_encryption_key_persists_salt(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(secure_storage.Path, "home", lambda: tmp_path)
        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Linux")

        storage = secure_storage.SecureStorage()
        first = storage._get_encryption_key()
        second = storage._get_encryption_key()

        assert first == second
        assert storage._key_file is not None
        assert storage._key_file.exists()
        assert len(storage._key_file.read_bytes()) == 32

    def test_get_encryption_key_recovers_from_read_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        salt_file = tmp_path / "secure_key"
        salt_file.write_bytes(b"placeholder")

        storage = object.__new__(secure_storage.SecureStorage)
        storage._key_file = salt_file
        storage._machine_key = b"m" * 32

        monkeypatch.setattr(
            Path, "read_bytes", lambda self: (_ for _ in ()).throw(OSError("read failed"))
        )

        key = storage._get_encryption_key()

        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_get_encryption_key_logs_warning_when_save_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        mocker,
    ) -> None:
        warning_mock = mocker.patch.object(secure_storage.logger, "warning")

        storage = object.__new__(secure_storage.SecureStorage)
        storage._key_file = tmp_path / "nested" / "secure_key"
        storage._machine_key = b"k" * 32

        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Linux")
        monkeypatch.setattr(
            secure_storage.os,
            "chmod",
            lambda *args, **kwargs: (_ for _ in ()).throw(OSError("chmod failed")),
        )

        key = storage._get_encryption_key()

        assert isinstance(key, bytes)
        warning_mock.assert_called_once()

    def test_encrypt_and_decrypt_raise_not_implemented(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(secure_storage.Path, "home", lambda: tmp_path)
        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Linux")

        storage = secure_storage.SecureStorage()

        with pytest.raises(NotImplementedError):
            storage.encrypt("secret")

        with pytest.raises(NotImplementedError):
            storage.decrypt("cipher")

    def test_is_encrypted_detects_known_prefixes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setattr(secure_storage.Path, "home", lambda: tmp_path)
        monkeypatch.setattr(secure_storage.platform, "system", lambda: "Linux")

        storage = secure_storage.SecureStorage()

        assert storage.is_encrypted("DPAPI:token") is True
        assert storage.is_encrypted("XOR:token") is True
        assert storage.is_encrypted("plain-text") is False
