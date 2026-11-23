import csv

from src.schemas.research import ResearchRecord
from src.pipeline.prepare_data import prepare
from src.analysis.metrics import verification_metrics

path=prepare()
with path.open("r",encoding="utf-8",newline="") as f:
    rows=list(csv.DictReader(f))
assert len(rows)==100
assert len({r["id"] for r in rows})==100
assert len({r["app_name"] for r in rows})==100

record=ResearchRecord(id=1,app_name="Example",category="Test")
access=getattr(record.access_model,"value",record.access_model)
assert access=="unknown"

human_metrics=verification_metrics(
    [record,record],
    [],
    2,
    [
        {"human_decision":"correct","post_verification_decision":"correct"},
        {"human_decision":"incorrect","post_verification_decision":"correct"},
    ],
)
assert human_metrics["first_pass_accuracy"]==0.5
assert human_metrics["post_verification_accuracy"]==1.0
assert human_metrics["first_pass_outcome_matrix"]=={"correct":1,"incorrect":1,"unknown":0}
print("Smoke tests passed")
