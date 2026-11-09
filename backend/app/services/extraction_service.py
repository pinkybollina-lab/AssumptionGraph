
import re


MONTH_PATTERN = (
    r"january|february|march|april|may|june|"
    r"july|august|september|october|november|december"
)

DEPARTMENTS = (
    "Finance", "Engineering", "Operations", "Procurement",
    "Marketing", "Sales", "HR", "IT",
)


def _get_sentences(transcript: str):
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", transcript)
        if sentence.strip()
    ]


def _detect_department(text: str, fallback: str = "Unassigned"):
    for name in DEPARTMENTS:
        if re.search(
            rf"\b{name}\s+(?:team|department)\b",
            text,
            re.IGNORECASE,
        ):
            return name
    return fallback


def _clean_subject(value: str):
    value = value.strip(" .,:;")
    value = re.sub(
        r"^(?:the|a|an|that|new|total|initial|latest)\s+",
        "",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"^(?:the\s+)?(?:finance|engineering|operations|procurement|"
        r"marketing|sales)\s+(?:team|department)\s+",
        "",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"^(?:(?:initially|originally|currently)\s+)?"
        r"(?:estimated|estimates|expects|expected|plans|planned|"
        r"indicated|suggests|suggested)\s+"
        r"(?:that\s+)?(?:the\s+)?",
        "",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"^(?:the|a|an|that|new|total)\s+",
        "",
        value,
        flags=re.I,
    )
    return value.strip(" .,:;").title()


def _budget_subject(text: str):
    patterns = (
        r"\b(?:estimated|estimates|expects|expected|plans|planned)\s+"
        r"(?:that\s+)?(?:the\s+)?(?:new\s+|total\s+)?"
        r"(?P<name>[\w -]+?)\s+budget\b",
        r"\b(?:budget for|budget of)\s+(?P<name>[\w -]+)",
    )

    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            name = _clean_subject(match.group("name"))
            if name:
                return f"{name} budget"

    if "cloud migration" in text:
        return "Cloud migration budget"
    if "infrastructure" in text:
        return "Infrastructure budget"

    return "Project budget"


def extract_assumptions(
    transcript: str,
    department: str = "Unassigned",
):
    """Extract evidence-backed business assumptions."""

    sentences = _get_sentences(transcript)
    assumptions = []
    seen = set()

    def add(
        sentence,
        subject,
        metric,
        value,
        assigned_department,
        unit=None,
        assumption_type="forecast",
        confidence=0.80,
    ):
        if not subject or value is None or str(value).strip() == "":
            return

        key = (
            assigned_department.lower(),
            subject.lower(),
            metric.lower(),
            str(value).lower(),
            sentence.lower(),
        )

        if key in seen:
            return

        seen.add(key)

        assumptions.append({
            "department": assigned_department,
            "subject": subject,
            "metric": metric,
            "value": str(value).lower(),
            "unit": unit,
            "period": None,
            "assumption_type": assumption_type,
            "extraction_confidence": confidence,
            "speaker_confidence": None,
            "evidence": sentence,
            "review_status": "pending",
        })

    for i, sentence in enumerate(sentences):
        text = sentence.lower()
        previous = sentences[i - 1].lower() if i > 0 else ""
        context = previous + " " + text

        current_dept = _detect_department(sentence, department)

        # 1. Original budget.
        original_budget = re.search(
            r"\bbudget\b.*?"
            r"\b(?:to be|is|at|of|around|approximately)\s+"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)\s*"
            r"(crore|lakh|million|billion)\b",
            text,
        )

        if original_budget:
            add(
                sentence,
                _budget_subject(text),
                "estimated_budget",
                original_budget.group(1).replace(",", ""),
                "Finance",
                f"INR {original_budget.group(2)}",
                "target",
                0.85,
            )

        # 2. Revised budget.
        revised = re.search(
            r"(?:may\s+)?(?:increase|raise)\s+"
            r"(?:the\s+)?budget\s+to\s+"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)\s*"
            r"(crore|lakh|million|billion)\b",
            text,
        )

        if not revised:
            revised = re.search(
                r"(?:may\s+)?require\s+"
                r"(?:an\s+additional\s+)?"
                r"(?:₹|rs\.?|inr)?\s*"
                r"([\d,]+(?:\.\d+)?)\s*"
                r"(crore|lakh|million|billion)\b",
                text,
            )

        if revised:
            add(
                sentence,
                _budget_subject(context),
                "revised_budget",
                revised.group(1).replace(",", ""),
                "Finance",
                f"INR {revised.group(2)}",
                "forecast",
                0.85,
            )

        # 3. Original EV launch date.
        initial_ev = re.search(
            rf"(?:initially|originally)?\s*planned\s+"
            rf"(?:the\s+)?(?:ev|electric vehicle)\s+launch\s+"
            rf"(?:for|in)\s+({MONTH_PATTERN})\b",
            text,
        )

        if initial_ev:
            add(
                sentence, "EV launch", "launch_date",
                initial_ev.group(1), "Sales", "month", "target", 0.85,
            )

        # 4. EV launch postponement.
        postponed = re.search(
            rf"\b(?:postponed|postponing|delayed|moved|shifted)\s+"
            rf"(?:the\s+)?(?:ev\s+)?launch\s+(?:to|until)\s+"
            rf"({MONTH_PATTERN})\b",
            text,
        )

        if not postponed and re.search(r"\bev\s+launch\b", previous):
            postponed = re.search(
                rf"\b(?:postponed|postponing|delayed|moved|shifted)\s+"
                rf"(?:the\s+)?launch\s+to\s+({MONTH_PATTERN})\b",
                text,
            )

        if postponed:
            add(
                sentence, "EV launch", "launch_date",
                postponed.group(1), "Sales", "month", "forecast", 0.80,
            )

        # 5. General project milestones and readiness.
        milestone = re.search(
            rf"\b(?:expects|expected|plans|planned|aims|scheduled|"
            rf"targeted|estimates)\s+"
            rf"(?:that\s+)?(?:the\s+)?(?P<subject>.+?)\s+"
            rf"(?:(?:to\s+)?(?:be\s+)?)?"
            rf"(?:completed|finished|finish|ready|available)\s+by\s+"
            rf"({MONTH_PATTERN})\b",
            text,
        )

        if milestone:
            subject = _clean_subject(milestone.group("subject"))
            low_subject = subject.lower()

            metric = (
                "readiness_date"
                if "charging infrastructure" in low_subject
                else "completion_date"
            )

            if "charging infrastructure" in low_subject:
                subject = "Charging infrastructure"

            add(
                sentence, subject, metric, milestone.group(2),
                current_dept, "month", "forecast", 0.85,
            )

        # Legacy charging infrastructure readiness.
        readiness = re.search(
            rf"charging infrastructure.*?"
            rf"\b(?:ready|completed|available)\s+by\s+"
            rf"({MONTH_PATTERN})\b",
            text,
        )

        if readiness and not any(
            a["evidence"] == sentence
            and a["metric"] == "readiness_date"
            for a in assumptions
        ):
            add(
                sentence, "Charging infrastructure", "readiness_date",
                readiness.group(1), current_dept, "month", "forecast", 0.85,
            )

        # 6. Marketing campaign timelines.
        campaign = re.search(
            rf"\b(?:plans|planned|intends|expects)\s+to\s+"
            rf"(?:begin|start|launch)\s+(?:the\s+)?"
            rf"(?P<name>(?:[\w -]*?awareness|customer)\s+campaign|campaign)"
            rf"\s+(?:in|for|by)\s+({MONTH_PATTERN})\b",
            text,
        )

        if not campaign:
            campaign = re.search(
                rf"\b(?P<name>(?:[\w -]*?awareness|customer)\s+campaign|campaign)"
                rf"\s+(?:will\s+start|will\s+launch|starts|begins)\s+"
                rf"(?:in|for|by)\s+({MONTH_PATTERN})\b",
                text,
            )

        if campaign:
            subject = _clean_subject(campaign.group("name"))

            add(
                sentence, subject, "launch_date",
                campaign.group(2), "Marketing", "month", "target", 0.85,
            )

        # 7. General commercial and project launch timelines.
        launch = re.search(
            rf"\b(?P<subject>[\w -]*?"
            rf"(?:commercial|product|platform|project|business|ev|"
            rf"electric vehicle)\s+launch)"
            rf"\s+(?:to\s+take\s+place|will\s+take\s+place|"
            rf"is\s+expected\s+to\s+take\s+place|"
            rf"is\s+planned\s+for|is\s+expected\s+in|"
            rf"planned\s+for|expected\s+in)\s+"
            rf"(?:in|for|by)?\s*({MONTH_PATTERN})\b",
            text,
        )

        if launch:
            add(
                sentence,
                _clean_subject(launch.group("subject")),
                "launch_date",
                launch.group(2),
                current_dept,
                "month",
                "forecast",
                0.85,
            )

        # 8. General prerequisites and dependencies.
        dependency = re.search(
            r"\b(?P<prerequisite>[\w -]+?)\s+is\s+"
            r"(?:required|necessary|needed)\s+before\s+"
            r"(?P<dependent>[\w -]+?)"
            r"(?:\s+can\s+be\s+completed)?[.]?$",
            text,
        )

        if dependency:
            prerequisite_raw = dependency.group("prerequisite")

            prerequisite_raw = re.sub(
                r"^.*?\bthat\s+",
                "",
                prerequisite_raw,
                flags=re.I,
            ).strip()

            prerequisite = _clean_subject(prerequisite_raw)
            dependent = _clean_subject(dependency.group("dependent"))

            add(
                sentence, prerequisite, "prerequisite", dependent,
                current_dept, None, "dependency", 0.85,
            )

        # 9. Conditional business risks.
        risk = re.search(
            rf"\bif\s+(?P<cause>.+?)\s+(?:is\s+)?delayed\s+"
            rf"(?:beyond|after)\s+({MONTH_PATTERN})\s*,?\s*"
            rf"(?P<impact>.+)",
            text,
        )

        if not risk:
            risk = re.search(
                r"\bif\s+(?P<cause>.+?)\s+(?:is\s+)?delayed\s*,?\s*"
                r"(?P<impact>.+)",
                text,
            )

        if risk:
            cause = _clean_subject(risk.group("cause"))
            impact = risk.group("impact").strip(" .")

            if "integration testing" in context:
                cause = "Integration testing"
            elif "product testing" in context:
                cause = "Product testing"

            # Assign the risk to the department responsible for its cause.
            if "testing" in cause.lower():
                risk_dept = "Engineering"
            elif "server" in cause.lower() or "delivery" in cause.lower():
                risk_dept = "Procurement"
            elif "engineering" in impact.lower():
                risk_dept = "Engineering"
            else:
                risk_dept = current_dept

                if risk_dept == "Unassigned":
                    risk_dept = _detect_department(previous, department)

            add(
                sentence,
                f"{cause} delay",
                "conditional_business_impact",
                impact,
                risk_dept,
                None,
                "risk",
                0.85,
            )

    return assumptions
