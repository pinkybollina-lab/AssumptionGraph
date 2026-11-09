
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Assumption, Scenario
from ..schemas import ScenarioCreate
from ..services.graph_service import (
    get_downstream_impacts,
    get_downstream_paths,
)

router = APIRouter(
    prefix="/api/scenarios",
    tags=["Scenario Simulation"],
)


@router.post("/simulate")
def simulate_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
):
    # 1. Find the original assumption
    assumption = (
        db.query(Assumption)
        .filter(Assumption.id == payload.assumption_id)
        .first()
    )

    if not assumption:
        raise HTTPException(
            status_code=404,
            detail="Assumption not found.",
        )

    # 2. Reject a scenario that does not change the value
    old_value = str(assumption.value)
    new_value = payload.new_value.strip()

    if not new_value:
        raise HTTPException(
            status_code=400,
            detail="New value cannot be empty.",
        )

    if old_value.strip().lower() == new_value.lower():
        raise HTTPException(
            status_code=400,
            detail="New value must differ from the current value.",
        )

    # 3. Find downstream assumptions
    affected = get_downstream_impacts(
        db,
        assumption.id,
    )

    affected_ids = sorted(
        item["id"] for item in affected
    )

    # 4. Find complete dependency paths
    dependency_paths = get_downstream_paths(
        db,
        assumption.id,
        max_depth=10,
        max_paths=100,
    )

    # 5. Create an explainable impact summary
    if affected:
        affected_names = [
            f'{item["subject"]} ({item["department"]})'
            for item in affected
        ]

        impact_summary = (
            f"Changing {assumption.subject} "
            f"from '{old_value}' to '{new_value}' "
            f"may affect {len(affected)} downstream assumption(s): "
            + ", ".join(affected_names)
            + ". These impacts require human review; "
              "they are not confirmed forecasts."
        )
    else:
        impact_summary = (
            f"Changing {assumption.subject} "
            f"from '{old_value}' to '{new_value}' "
            "has no recorded downstream dependencies "
            "in the current graph."
        )

    # 6. Save the scenario without changing the original assumption
    scenario = Scenario(
        changed_assumption_id=assumption.id,
        old_value=old_value,
        new_value=new_value,
        impact_summary=impact_summary,
        affected_assumption_ids=json.dumps(affected_ids),
    )

    try:
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save scenario.",
        )

    # 7. Return scenario and downstream impact details
    return {
        "success": True,
        "message": "Scenario simulated and saved successfully.",
        "scenario": {
            "id": scenario.id,
            "changed_assumption_id": scenario.changed_assumption_id,
            "subject": assumption.subject,
            "metric": assumption.metric,
            "old_value": scenario.old_value,
            "new_value": scenario.new_value,
            "impact_summary": scenario.impact_summary,
            "affected_count": len(affected_ids),
            "affected_assumption_ids": affected_ids,
            "affected_assumptions": affected,
            "dependency_paths": dependency_paths,
            "created_at": scenario.created_at,
        },
        "original_assumption_modified": False,
    }


@router.get("")
def get_scenarios(db: Session = Depends(get_db)):
    scenarios = (
        db.query(Scenario)
        .order_by(Scenario.created_at.desc())
        .all()
    )

    results = []

    for scenario in scenarios:
        assumption = (
            db.query(Assumption)
            .filter(
                Assumption.id == scenario.changed_assumption_id
            )
            .first()
        )

        try:
            affected_ids = json.loads(
                scenario.affected_assumption_ids or "[]"
            )
        except (TypeError, json.JSONDecodeError):
            affected_ids = []

        results.append({
            "id": scenario.id,
            "changed_assumption_id": scenario.changed_assumption_id,
            "subject": assumption.subject if assumption else None,
            "metric": assumption.metric if assumption else None,
            "old_value": scenario.old_value,
            "new_value": scenario.new_value,
            "impact_summary": scenario.impact_summary,
            "affected_assumption_ids": affected_ids,
            "created_at": scenario.created_at,
        })

    return {
        "success": True,
        "scenario_count": len(results),
        "scenarios": results,
    }
