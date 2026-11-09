
from collections import defaultdict
from itertools import combinations

from sqlalchemy.orm import Session

from ..models import Assumption


def normalize(value):
    """Normalize values before comparison."""
    if value is None:
        return ""

    return " ".join(
        str(value).strip().lower().split()
    )


def find_potential_contradictions(db: Session) -> list:
    """
    Find potential conflicts between comparable assumptions.

    Comparison dimensions:
    - Subject
    - Metric
    - Unit
    - Reporting period

    Different values are flagged for human review.
    This does not automatically establish a genuine contradiction.
    """

    assumptions = db.query(Assumption).all()

    groups = defaultdict(list)

    # Step 1: Group comparable assumptions.
    for item in assumptions:

        key = (
            normalize(item.subject),
            normalize(item.metric),
            normalize(item.unit),
            normalize(item.period),
        )

        if not key[0] or not key[1]:
            continue

        groups[key].append(item)

    findings = []

    # Step 2: Compare values within each group.
    for key, items in groups.items():

        value_groups = defaultdict(list)

        for item in items:
            value = normalize(item.value)

            if value:
                value_groups[value].append(item)

        # No conflict if all values are identical.
        if len(value_groups) < 2:
            continue

        # Step 3: Compare distinct values.
        for value_a, value_b in combinations(
            sorted(value_groups.keys()), 2
        ):

            records_a = value_groups[value_a]
            records_b = value_groups[value_b]

            types_a = {
                normalize(item.assumption_type)
                for item in records_a
            }

            types_b = {
                normalize(item.assumption_type)
                for item in records_b
            }

            # Same assumption type is a stronger conflict signal.
            same_type = bool(types_a.intersection(types_b))

            claims = []

            for records in [records_a, records_b]:

                claims.append({
                    "value": records[0].value,

                    "departments": sorted({
                        item.department
                        for item in records
                        if item.department
                    }),

                    "assumption_types": sorted({
                        item.assumption_type
                        for item in records
                        if item.assumption_type
                    }),

                    "assumption_ids": [
                        item.id for item in records
                    ],

                    "evidence": [
                        item.evidence
                        for item in records
                        if item.evidence
                    ],
                })

            all_ids = (
                [item.id for item in records_a]
                + [item.id for item in records_b]
            )

            findings.append({

                "finding_type": (
                    "potential_contradiction"
                    if same_type
                    else "cross_type_tension"
                ),

                "severity": (
                    "medium" if same_type else "low"
                ),

                "subject": records_a[0].subject,

                "metric": records_a[0].metric,

                "unit": records_a[0].unit,

                "period": records_a[0].period,

                "explanation": (
                    f"Different values were recorded for "
                    f"'{records_a[0].subject}' and "
                    f"'{records_a[0].metric}': "
                    f"'{records_a[0].value}' versus "
                    f"'{records_b[0].value}'. "
                    f"Review the source evidence to determine "
                    f"whether these claims genuinely conflict."
                ),

                "assumption_ids": all_ids,

                "claims": claims,

                "status": "requires_review",
            })

    return findings
