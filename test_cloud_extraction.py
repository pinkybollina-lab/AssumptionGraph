
from app.services.extraction_service import extract_assumptions

transcript = """
The Finance team expects the cloud migration budget to be ₹30 crore.
The latest review suggests that additional security requirements may increase the budget to ₹38 crore.

The Marketing team plans to launch the customer campaign in October.
The Engineering team expects integration testing to finish by September.

If integration testing is delayed beyond September, the customer campaign launch may need to be postponed.
"""

results = extract_assumptions(transcript)

print("\nTOTAL ASSUMPTIONS:", len(results))

for i, item in enumerate(results, 1):
    print(f"\n{i}. {item['subject']}")
    print("Department:", item["department"])
    print("Metric:", item["metric"])
    print("Value:", item["value"])
    print("Unit:", item["unit"])
    print("Type:", item["assumption_type"])
    print("Evidence:", item["evidence"])
