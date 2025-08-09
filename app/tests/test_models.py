import pytest
from datetime import datetime
from uuid import uuid4
from logs.models import Log, Level
from repositories.mongo_repository import MongoLogDocument


def test_mongo_log_document_instantiation():
    doc = MongoLogDocument(
        tenant="tenant-xyz",
        log={"message": "test"},
        metadata={"env": "test"},
        tag="unit-test",
        level=Level.WARNING,
        group_path=["module", "submodule"],
        uid=str(uuid4()),
        created_at=datetime.now(),
    )

    assert doc.tenant == "tenant-xyz"
    assert doc.log == {"message": "test"}
    assert doc.level == Level.WARNING
    assert isinstance(doc.uid, str)
    assert isinstance(doc.created_at, datetime)


def test_mongo_log_document_accepts_string_log():
    doc = MongoLogDocument(
        tenant=None,
        log="simple log string",
        metadata={},
        tag=None,
        level=Level.INFO,
        group_path=None,
        uid=str(uuid4()),
        created_at=datetime.now(),
    )

    assert isinstance(doc.log, str)


def test_invalid_level_enum_raises_validation_error():
    with pytest.raises(ValueError):
        MongoLogDocument(
            tenant="x",
            log={},
            metadata={},
            tag=None,
            level="NOT_A_LEVEL",  # invalid
            group_path=[],
            uid=str(uuid4()),
            created_at=datetime.now(),
        )


def test_to_log_and_from_log_roundtrip():
    original_log = Log(
        tenant="tenant-abc",
        log={"msg": "testing"},
        metadata={"trace": "xyz"},
        tag="roundtrip",
        level=Level.DEBUG,
        group_path=["one", "two"],
    )

    doc = MongoLogDocument.from_log(original_log)
    log_back = doc.to_log()

    assert isinstance(log_back, Log)
    assert log_back.uid == original_log.uid
    assert log_back.level == original_log.level
    assert log_back.log == original_log.log
    assert log_back.group_path == ["one", "two"]
