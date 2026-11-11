"""Select one configured finding family from an actual scanner report."""
import copy
import json
import sys
from pathlib import Path

case_id, source, destination = sys.argv[1:]
spec = json.loads(Path("targeted-retest-cases.json").read_text())["cases"][case_id]
report = json.loads(Path(source).read_text())
selected = copy.deepcopy(report)
count = 0
for run in selected["runs"]:
    results = []
    for result in run.get("results", []):
        matches = any(result["ruleId"].endswith(suffix) for suffix in spec["rule_suffixes"])
        locations = [loc["physicalLocation"] for loc in result.get("locations", [])]
        in_scope = bool(locations) and all(
            loc["artifactLocation"]["uri"] == spec["path"]
            and loc["region"]["startLine"] in spec["lines"] for loc in locations
        )
        if matches and in_scope:
            results.append(result)
    run["results"] = results
    count += len(results)
if count != spec["expected"]:
    raise SystemExit(f"case={case_id} expected={spec['expected']} actual={count}; submit refused")
Path(destination).write_text(json.dumps(selected) + "\n")
print(json.dumps({"case": case_id, "findings": count, "path": spec["path"],
                  "rules": sorted({r["ruleId"] for run in selected["runs"] for r in run["results"]})}))
