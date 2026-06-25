"""Tests for alarm_clock.storage"""

import json
import pytest
from pathlib import Path
from alarm_clock.alarm import Alarm
from alarm_clock.storage import Storage, StorageError


@pytest.fixture
def store(tmp_path):
    return Storage(path=tmp_path / "alarms.json")


@pytest.fixture
def sample_alarms():
    return [
        Alarm(hour=7, minute=30, id="aaa11111", label="wake up"),
        Alarm(hour=12, minute=0, id="bbb22222"),
    ]


class TestLoad:
    def test_missing_file_returns_empty(self, store):
        assert store.load() == []

    def test_empty_file_returns_empty(self, store):
        store.path.parent.mkdir(parents=True, exist_ok=True)
        store.path.write_text("", encoding="utf-8")
        assert store.load() == []

    def test_loads_alarms(self, store, sample_alarms):
        store.save(sample_alarms)
        loaded = store.load()
        assert len(loaded) == 2
        assert loaded[0].id == "aaa11111"
        assert loaded[1].id == "bbb22222"

    def test_corrupt_json_raises(self, store):
        store.path.parent.mkdir(parents=True, exist_ok=True)
        store.path.write_text("{bad json!!!", encoding="utf-8")
        with pytest.raises(StorageError, match="corrupt"):
            store.load()

    def test_wrong_structure_raises(self, store):
        store.path.parent.mkdir(parents=True, exist_ok=True)
        store.path.write_text(json.dumps([{"no_hour": True}]), encoding="utf-8")
        with pytest.raises(StorageError):
            store.load()


class TestSave:
    def test_creates_parent_dirs(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "c" / "alarms.json"
        store = Storage(path=deep_path)
        store.save([])
        assert deep_path.exists()

    def test_save_and_reload(self, store, sample_alarms):
        store.save(sample_alarms)
        loaded = store.load()
        assert len(loaded) == 2

    def test_save_empty_list(self, store):
        store.save([])
        loaded = store.load()
        assert loaded == []

    def test_atomic_write_leaves_no_tmp(self, store, sample_alarms):
        store.save(sample_alarms)
        tmp = store.path.with_suffix(".tmp")
        assert not tmp.exists()

    def test_overwrites_existing(self, store, sample_alarms):
        store.save(sample_alarms)
        store.save([sample_alarms[0]])
        loaded = store.load()
        assert len(loaded) == 1

    def test_preserves_inactive_alarms(self, store):
        alarm = Alarm(hour=7, minute=30, active=False)
        store.save([alarm])
        loaded = store.load()
        assert loaded[0].active is False

    def test_roundtrip_all_fields(self, store):
        alarm = Alarm(hour=9, minute=15, id="zzzzzzzz", label="test label", active=True)
        store.save([alarm])
        loaded = store.load()[0]
        assert loaded.hour == 9
        assert loaded.minute == 15
        assert loaded.id == "zzzzzzzz"
        assert loaded.label == "test label"
        assert loaded.active is True
