
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Assumption, Dependency, Scenario
from app.schemas import ScenarioCreate
from app.services.graph_service import get_downstream_paths
from app.routers.scenarios import simulate_scenario


@pytest.fixture
def db():
    """
    Create an isolated in-memory database.
    This never connects to the project's actual database.
    """

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create_assumption(db, subject, department="Engineering", value="September"):
    assumption = Assumption(
        department=department,
        subject=subject,
        metric="completion_date",
        value=value,
        evidence=f"Test evidence for {subject}",
    )

    db.add(assumption)
    db.commit()
    db.refresh(assumption)

    return assumption


def add_dependency(db, prerequisite, dependent, rationale="Test dependency"):
    dependency = Dependency(
        from_assumption_id=dependent.id,
        to_assumption_id=prerequisite.id,
        relation="DEPENDS_ON",
        rationale=rationale,
    )

    db.add(dependency)
    db.commit()

    return dependency


def test_direct_dependency_path(db):
    prerequisite = create_assumption(db, "Transformer Delivery")
    dependent = create_assumption(db, "Charging Infrastructure")

    add_dependency(db, prerequisite, dependent)

    paths = get_downstream_paths(db, prerequisite.id)

    assert len(paths) == 1
    assert paths[0]["assumption_ids"] == [
        prerequisite.id,
        dependent.id,
    ]
    assert paths[0]["depth"] == 1

    print("PASS: Direct dependency path")


def test_multi_step_dependency_chain(db):
    first = create_assumption(db, "GPU Server Delivery", "Procurement")
    second = create_assumption(db, "Infrastructure Installation", "Operations")
    third = create_assumption(db, "AI Platform Testing", "Engineering")

    add_dependency(db, first, second)
    add_dependency(db, second, third)

    paths = get_downstream_paths(db, first.id)

    path_to_third = next(
        path for path in paths
        if path["assumption_ids"][-1] == third.id
    )

    assert path_to_third["assumption_ids"] == [
        first.id,
        second.id,
        third.id,
    ]

    assert path_to_third["depth"] == 2
    assert len(path_to_third["steps"]) == 2

    print("PASS: Multi-step dependency chain")


def test_disconnected_assumptions_have_no_paths(db):
    first = create_assumption(db, "Project A")
    create_assumption(db, "Unrelated Project B")

    paths = get_downstream_paths(db, first.id)

    assert paths == []

    print("PASS: Disconnected assumptions")


def test_cycle_does_not_repeat_nodes(db):
    first = create_assumption(db, "Task A")
    second = create_assumption(db, "Task B")

    add_dependency(db, first, second)
    add_dependency(db, second, first)

    paths = get_downstream_paths(db, first.id)

    assert paths

    for path in paths:
        ids = path["assumption_ids"]
        assert len(ids) == len(set(ids))

    print("PASS: Cycle-safe path traversal")


def test_max_depth_limit(db):
    first = create_assumption(db, "Step A")
    second = create_assumption(db, "Step B")
    third = create_assumption(db, "Step C")

    add_dependency(db, first, second)
    add_dependency(db, second, third)

    paths = get_downstream_paths(
        db,
        first.id,
        max_depth=1,
    )

    assert all(path["depth"] <= 1 for path in paths)
    assert not any(
        path["assumption_ids"][-1] == third.id
        for path in paths
    )

    print("PASS: Maximum depth limit")


def test_scenario_returns_paths_without_changing_original(db):
    first = create_assumption(
        db,
        "Transformer Delivery",
        "Procurement",
        "September",
    )

    second = create_assumption(
        db,
        "Charging Infrastructure",
        "Operations",
        "October",
    )

    add_dependency(db, first, second)

    payload = ScenarioCreate(
        assumption_id=first.id,
        new_value="November",
    )

    result = simulate_scenario(payload, db)

    assert result["success"] is True
    assert result["original_assumption_modified"] is False

    scenario_data = result["scenario"]

    assert scenario_data["old_value"] == "September"
    assert scenario_data["new_value"] == "November"
    assert scenario_data["affected_count"] == 1

    assert scenario_data["dependency_paths"]
    assert scenario_data["dependency_paths"][0]["assumption_ids"] == [
        first.id,
        second.id,
    ]

    db.refresh(first)

    assert first.value == "September"

    saved_scenario = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_data["id"])
        .first()
    )

    assert saved_scenario is not None

    print("PASS: Scenario returns dependency paths")
    print("PASS: Original assumption remains unchanged")


def test_unknown_assumption_returns_no_paths(db):
    paths = get_downstream_paths(db, 999999)

    assert paths == []

    print("PASS: Unknown assumption handling")
