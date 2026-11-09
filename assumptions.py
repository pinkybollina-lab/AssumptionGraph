
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Source, Assumption
from ..schemas import SourceCreate
from ..services.extraction_service import extract_assumptions

router = APIRouter(
    prefix="/api/assumptions",
    tags=["Assumptions"]
)


@router.post("/analyze")
def analyze_source(
    payload: SourceCreate,
    db: Session = Depends(get_db)
):
    try:
        # Save the original transcript
        source = Source(
            department=payload.department,
            speaker=payload.speaker,
            source_type=payload.source_type,
            language=payload.language,
            transcript=payload.transcript
        )

        db.add(source)
        db.flush()

        # Extract structured assumptions
        extracted = extract_assumptions(
            payload.transcript,
            department=payload.department,
        )

        saved_assumptions = []

        for item in extracted:
            assumption = Assumption(
                source_id=source.id,
                **item
            )

            db.add(assumption)
            saved_assumptions.append(assumption)

        db.commit()

        for assumption in saved_assumptions:
            db.refresh(assumption)

        # Generate dependency proposals using only assumptions
        # extracted from this transcript.
        dependency_candidates = []

        for prerequisite in saved_assumptions:
            if (
                prerequisite.assumption_type != "dependency"
                or prerequisite.metric != "prerequisite"
            ):
                continue

            prerequisite_text = prerequisite.value.strip().lower()

            # Find assumptions whose subject is mentioned
            # in the prerequisite statement.
            matching_targets = [
                target
                for target in saved_assumptions
                if target.id != prerequisite.id
                and target.subject.strip().lower() in prerequisite_text
            ]

            # Do not guess when there are zero or multiple matches.
            if len(matching_targets) != 1:
                continue

            dependent = matching_targets[0]

            dependency_candidates.append({
                "prerequisite_assumption_id": prerequisite.id,
                "dependent_assumption_id": dependent.id,
                "rationale": prerequisite.evidence,
                "review_note": (
                    "The source states that this prerequisite is required "
                    "before installation can be completed. The proposed "
                    "relationship to the readiness assumption is an "
                    "interpretation. Please validate it before approval."
                ),
                "prerequisite": {
                    "subject": prerequisite.subject,
                    "department": prerequisite.department,
                    "metric": prerequisite.metric,
                    "value": prerequisite.value,
                },
                "dependent": {
                    "subject": dependent.subject,
                    "department": dependent.department,
                    "metric": dependent.metric,
                    "value": dependent.value,
                },
            })

        return {
            "success": True,
            "source_id": source.id,
            "extracted_count": len(saved_assumptions),
            "assumptions": [
                {
                    "id": item.id,
                    "source_id": item.source_id,
                    "department": item.department,
                    "subject": item.subject,
                    "metric": item.metric,
                    "value": item.value,
                    "unit": item.unit,
                    "assumption_type": item.assumption_type,
                    "extraction_confidence": item.extraction_confidence,
                    "evidence": item.evidence,
                    "review_status": item.review_status
                }
                for item in saved_assumptions
            ],
            "dependency_candidates": dependency_candidates
        }

    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Assumption analysis failed: {str(error)}"
        )
