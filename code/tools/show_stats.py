# ============================================================
# STATS VIEWER — show_stats.py
# Run any time to see your rebirth stats.
# Usage:  python tools/show_stats.py
# ============================================================
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from stats import StatsTracker
import json

st = StatsTracker()
st.print_summary()

gs = st.global_stats
if gs.run_history:
    print("Last 5 runs:")
    for r in gs.run_history[-5:]:
        m, s = divmod(int(r['duration_secs']), 60)
        print(f"  Run #{r['run_number']:>4}  {m}m{s:02d}s  errors: {r['error_count']}")
