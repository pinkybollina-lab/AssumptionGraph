from app.services.extraction_service import extract_assumptions

transcript = """
The Finance team initially estimated the new AI platform development budget at ₹40 crore.
During the latest management review, the Finance team indicated that additional infrastructure and security requirements may increase the budget to ₹55 crore.
The Engineering team expects the AI platform development to be completed by December.
The Procurement team confirmed that GPU server delivery is required before infrastructure installation can be completed.
The Operations team expects infrastructure installation to be completed by November.
The Marketing team plans to launch the AI platform awareness campaign in January.
The Sales team expects the AI platform commercial launch to take place in February.
If GPU server delivery is delayed beyond October, infrastructure installation may be postponed, potentially affecting engineering completion and the planned commercial launch.
"""

assumptions = extract_assumptions(transcript)

print(f"\nTOTAL ASSUMPTIONS: {len(assumptions)}")

for i, item in enumerate(assumptions, 1):
    print(f"\n{i}. {item['subject']}")
    print(f"Department: {item['department']}")
    print(f"Metric: {item['metric']}")
    print(f"Value: {item['value']}")
    print(f"Type: {item['assumption_type']}")
    print(f"Evidence: {item['evidence']}")