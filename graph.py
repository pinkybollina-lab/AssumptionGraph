import json

from ..models import Assumption, Dependency, Finding
from ..schemas import DependencyCreate, FindingStatusUpdate
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Assumption, Dependency
from ..schemas import DependencyCreate

from ..services.graph_service import (
    get_graph_data,
    get_downstream_impacts,
)

from ..services.contradiction_service import (
    find_potential_contradictions,
)


router = APIRouter(
    prefix="/api/graph",
    tags=["Assumption Graph"],
)


# --------------------------------------------------
# 1. GET COMPLETE ASSUMPTION GRAPH
# --------------------------------------------------

@router.get("")
def read_graph(
    db: Session = Depends(get_db),
):
    return get_graph_data(db)


# --------------------------------------------------
# 2. CREATE ASSUMPTION DEPENDENCY
# --------------------------------------------------

@router.post("/dependencies")
def create_dependency(
    payload: DependencyCreate,
    db: Session = Depends(get_db),
):
    prerequisite_id = payload.prerequisite_assumption_id
    dependent_id = payload.dependent_assumption_id

    # Prevent self-dependency.
    if prerequisite_id == dependent_id:
        raise HTTPException(
            status_code=400,
            detail="An assumption cannot depend on itself.",
        )

    # Verify prerequisite exists.
    prerequisite = db.query(Assumption).filter(
        Assumption.id == prerequisite_id
    ).first()

    # Verify dependent exists.
    dependent = db.query(Assumption).filter(
        Assumption.id == dependent_id
    ).first()

    if not prerequisite or not dependent:
        raise HTTPException(
            status_code=404,
            detail="One or both assumption IDs do not exist.",
        )

    # Prevent duplicate dependencies.
    existing = db.query(Dependency).filter(
        Dependency.from_assumption_id == dependent_id,
        Dependency.to_assumption_id == prerequisite_id,
        Dependency.relation == "DEPENDS_ON",
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This dependency already exists.",
        )

    # Save dependency.
    dependency = Dependency(
        from_assumption_id=dependent_id,
        to_assumption_id=prerequisite_id,
        relation="DEPENDS_ON",
        rationale=payload.rationale,
    )

    db.add(dependency)
    db.commit()
    db.refresh(dependency)

    return {
        "success": True,
        "message": "Dependency recorded successfully.",
        "dependency": {
            "id": dependency.id,
            "prerequisite_assumption_id": prerequisite_id,
            "dependent_assumption_id": dependent_id,
            "relation": dependency.relation,
            "rationale": dependency.rationale,
        },
    }


# --------------------------------------------------
# 3. GET DOWNSTREAM IMPACTS
# --------------------------------------------------

@router.get("/assumptions/{assumption_id}/impacts")
def read_impacts(
    assumption_id: int,
    db: Session = Depends(get_db),
):
    assumption = db.query(Assumption).filter(
        Assumption.id == assumption_id
    ).first()

    if not assumption:
        raise HTTPException(
            status_code=404,
            detail="Assumption not found.",
        )

    affected = get_downstream_impacts(
        db,
        assumption_id,
    )

    return {
        "success": True,
        "changed_assumption_id": assumption_id,
        "affected_count": len(affected),
        "affected_assumptions": affected,
    }


# --------------------------------------------------
# 4. DETECT POTENTIAL CONTRADICTIONS
# --------------------------------------------------

@router.get("/contradictions")
def read_contradictions(
    db: Session = Depends(get_db),
):
    findings = find_potential_contradictions(db)

    return {
        "success": True,
        "finding_count": len(findings),
        "findings": findings,
    }
# --------------------------------------------------
# 5. SCAN AND SAVE FINDINGS
# --------------------------------------------------

@router.post("/contradictions/scan")
def scan_and_save_findings(
    db: Session = Depends(get_db),
):
    detected_findings = find_potential_contradictions(db)

    # Load previously saved findings.
    existing_findings = db.query(Finding).all()

    # Create fingerprints to prevent duplicate records.
    existing_fingerprints = set()

    for finding in existing_findings:
        try:
            saved_ids = json.loads(
                finding.assumption_ids or "[]"
            )
        except (ValueError, TypeError):
            saved_ids = []

        fingerprint = (
            finding.finding_type,
            tuple(sorted(set(saved_ids))),
        )

        existing_fingerprints.add(fingerprint)

    created_count = 0

    for item in detected_findings:

        assumption_ids = sorted(
            set(item["assumption_ids"])
        )

        fingerprint = (
            item["finding_type"],
            tuple(assumption_ids),
        )

        if fingerprint in existing_fingerprints:
            continue

        saved_finding = Finding(
            finding_type=item["finding_type"],
            severity=item["severity"],
            explanation=item["explanation"],
            assumption_ids=json.dumps(assumption_ids),
            status="open",
        )

        db.add(saved_finding)

        existing_fingerprints.add(fingerprint)
        created_count += 1

    db.commit()

    return {
        "success": True,
        "detected_count": len(detected_findings),
        "created_count": created_count,
        "message": (
            f"Scan completed. {created_count} new findings saved."
        ),
    }


# --------------------------------------------------
# 6. GET ALL SAVED FINDINGS
# --------------------------------------------------

@router.get("/findings")
def read_saved_findings(
    db: Session = Depends(get_db),
):
    saved_findings = (
        db.query(Finding)
        .order_by(Finding.created_at.desc())
        .all()
    )

    results = []

    for finding in saved_findings:

        try:
            assumption_ids = json.loads(
                finding.assumption_ids or "[]"
            )
        except (ValueError, TypeError):
            assumption_ids = []

        assumptions = (
            db.query(Assumption)
            .filter(Assumption.id.in_(assumption_ids))
            .all()
            if assumption_ids
            else []
        )

        results.append({
            "id": finding.id,
            "finding_type": finding.finding_type,
            "severity": finding.severity,
            "explanation": finding.explanation,
            "status": finding.status,
            "assumption_ids": assumption_ids,
            "evidence": [
                {
                    "id": item.id,
                    "department": item.department,
                    "subject": item.subject,
                    "metric": item.metric,
                    "value": item.value,
                    "evidence": item.evidence,
                    "assumption_type": item.assumption_type,
                }
                for item in assumptions
            ],
            "created_at": finding.created_at,
        })

    return {
        "success": True,
        "finding_count": len(results),
        "findings": results,
    }


# --------------------------------------------------
# 7. UPDATE FINDING REVIEW STATUS
# --------------------------------------------------

@router.patch("/findings/{finding_id}/status")
def update_finding_status(
    finding_id: int,
    payload: FindingStatusUpdate,
    db: Session = Depends(get_db),
):
    allowed_statuses = {
        "open",
        "under_review",
        "confirmed",
        "resolved",
        "dismissed",
    }

    new_status = payload.status.strip().lower()

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid finding status.",
                "allowed_statuses": sorted(allowed_statuses),
            },
        )

    finding = db.query(Finding).filter(
        Finding.id == finding_id
    ).first()

    if not finding:
        raise HTTPException(
            status_code=404,
            detail="Finding not found.",
        )

    finding.status = new_status

    db.commit()
    db.refresh(finding)

    return {
        "success": True,
        "message": "Finding status updated successfully.",
        "finding": {
            "id": finding.id,
            "finding_type": finding.finding_type,
            "severity": finding.severity,
            "status": finding.status,
        },
    }
