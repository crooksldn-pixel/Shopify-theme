"""Reading, in parallel where the reads do not depend on each other.

app/reads/scheduler.py takes a small graph of named reads and runs it: everything with no
outstanding dependency starts at once, within a per-source concurrency limit and a per-source
budget, and the results merge in the order the caller declared rather than the order they
landed. Nothing in here can write; the scheduler refuses a write tool by name.
"""

from app.reads.scheduler import Read, ReadPlan, ReadResult, run_plan

__all__ = ["Read", "ReadPlan", "ReadResult", "run_plan"]
