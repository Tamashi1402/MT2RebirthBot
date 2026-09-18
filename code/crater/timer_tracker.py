# ============================================================
# CRATER - TIMER TRACKER
# Confirms we're actually inside the crater mining area via the
# countdown HUD ("M:SS", top-center) — it only ever counts DOWN,
# jumping back up to its start value once it resets on completion.
#
# The crater timer cycles: 1:00 -> 0:59 -> 0:58 -> ... -> 1:00 (reset).
# It can reset from ANY value back to 1:00, not just from near-zero.
# The tracker must accept any jump back to the start value (~60s)
# as a valid reset, while still rejecting garbage reads.
# ============================================================


class CraterTimerTracker:
    def __init__(self, miss_threshold=8, reset_grace_seconds=5):
        self.miss_threshold = max(1, int(miss_threshold))
        # Not used for the new reset logic, kept for compatibility
        self.reset_grace_seconds = max(0, int(reset_grace_seconds))
        self.last_value = None
        self.consecutive_bad = 0
        self.good_reads = 0

    def reset(self):
        self.last_value = None
        self.consecutive_bad = 0
        self.good_reads = 0

    def update(self, seconds):
        """Feed one OCR read (int seconds, or None on a miss).

        Returns True while we should still consider ourselves inside the
        crater (keep going / don't panic), and False only once we're
        confident we've actually left it (sustained bad reads) -- at which
        point the caller should abort and redo the teleport chain.
        """
        good = False
        if seconds is not None and 0 <= seconds <= 99 * 60:
            if self.last_value is None:
                good = True
            elif seconds <= self.last_value:
                # Normal countdown tick (or holding steady).
                good = True
            elif seconds >= 55:
                # Timer jumped back UP to near its start value (1:00).
                # The crater timer resets from ANY value back to 1:00,
                # not just from near-zero. Accept this as a valid reset.
                good = True
            # else: jumped up to a value below 55 from a lower value --
            # this is NOT a valid crater-timer transition, treat as bad.

        if good:
            self.last_value = seconds
            self.consecutive_bad = 0
            self.good_reads += 1
            return True

        self.consecutive_bad += 1
        return self.consecutive_bad < self.miss_threshold

    @property
    def confirmed_in_crater(self) -> bool:
        """True once we've had at least one good read and aren't currently
        mid-way through a bad streak that hasn't yet hit the threshold."""
        return self.good_reads > 0 and self.consecutive_bad == 0
