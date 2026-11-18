"""Os mínimos são independentes: 80% das linhas E 70% das ramificações."""
import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else "coverage.json").read_text())
totals = report["totals"]
lines = totals["covered_lines"] / totals["num_statements"] * 100
branches = totals["covered_branches"] / max(totals["num_branches"], 1) * 100
print(f"Linhas: {lines:.2f}% (mínimo 80%) | Ramificações: {branches:.2f}% (mínimo 70%)")
raise SystemExit(0 if lines >= 80 and branches >= 70 else 1)
