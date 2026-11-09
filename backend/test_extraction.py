
from app.services.extraction_service import extract_assumptions

transcript = """
The Sales department initially planned the electric vehicle launch for July. During the latest management meeting, the team discussed postponing the launch to August because of infrastructure readiness concerns.

The Operations team expects the EV charging infrastructure to be ready by September. However, the Procurement team confirmed that transformer delivery is required before charging infrastructure installation can be completed.

The Finance department estimates the total infrastructure budget at ₹50 crore. The latest finance review indicates that the project may require ₹65 crore due to increased equipment and installation costs.

The Marketing team plans to begin the product awareness campaign in June. However, the campaign launch depends on final approval of the product specifications from the Engineering team.

The Engineering team expects product testing to be completed by May. If testing is delayed beyond May, the marketing campaign timeline and the planned July launch may need to be reconsidered.
"""

results = extract_assumptions(transcript)

print("\nTOTAL ASSUMPTIONS:", len(results))

for i, item in enumerate(results, 1):
    print(f"\n{i}. {item['subject']}")
    print("Department:", item["department"])
    print("Metric:", item["metric"])
    print("Value:", item["value"])
    print("Type:", item["assumption_type"])
    print("Evidence:", item["evidence"])
