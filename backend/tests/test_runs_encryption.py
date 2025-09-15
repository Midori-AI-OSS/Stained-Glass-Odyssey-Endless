from runs import encryption as enc
from runs.encryption import get_fernet
from runs.encryption import get_save_manager


def test_get_save_manager(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'db.sqlite'}")
    enc.SAVE_MANAGER = None
    enc.FERNET = None
    manager = get_save_manager()
    assert manager is not None
    assert get_fernet() is not None
