# ============================================================
# CRATER - ESP OVERLAY (proxy)
#
# This used to spin up its OWN independent tkinter Tk() root on a
# background thread every time crater's ESP started/stopped (once per
# navigate cycle, and once per force-restart). That is not safe: Tcl's
# event loop is not designed to host two Tk() roots on two different
# threads within the same process, and the repeated create/destroy
# cycle (every force restart -> stop_esp_overlay() then start_esp_overlay()
# again) could wedge the MAIN status overlay's `self.root.after()`
# scheduling in overlay.py -- which showed up as the overlay's header/
# goal text (e.g. "HITTING | Crater: area=1596") freezing forever after
# a force restart, even though the bot kept running and re-entered the
# crater fine underneath.
#
# Fix: crater's rock/timer ESP now renders through the SAME Tk()
# instance/thread as the main overlay (see overlay.py's
# set_crater_esp() / _update_crater_esp()) -- exactly like kraken and
# delve mode's ESP already do. No second Tk() root is ever created.
#
# All functions below keep their original names/signatures so
# crater/loop.py needs no changes -- they just forward into overlay.py.
# ============================================================
from logger import get_logger

log = get_logger()


def set_esp(capture_rect=None, rock_boxes=None, target_box=None,
           timer_box=None, timer_state=None, rock_ids=None):
    try:
        from overlay import set_crater_esp
        set_crater_esp(capture_rect=capture_rect, rock_boxes=rock_boxes,
                       target_box=target_box, timer_box=timer_box,
                       timer_state=timer_state,
                       rock_ids=rock_ids)
    except Exception as e:
        log.debug(f"Crater ESP set_esp failed: {e}")


def clear_esp():
    """Clear ALL ESP state — capture box, rocks, target, timer."""
    try:
        from overlay import clear_crater_esp
        clear_crater_esp()
    except Exception as e:
        log.debug(f"Crater ESP clear_esp failed: {e}")


def start_esp_overlay():
    try:
        from overlay import set_crater_esp_active
        set_crater_esp_active(True)
    except Exception as e:
        log.debug(f"Crater ESP start failed: {e}")


def stop_esp_overlay():
    try:
        from overlay import set_crater_esp_active, clear_crater_esp
        clear_crater_esp()
        set_crater_esp_active(False)
    except Exception as e:
        log.debug(f"Crater ESP stop failed: {e}")
