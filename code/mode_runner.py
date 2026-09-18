"""
MT2 BOT - MODE RUNNER
Executes custom modes created via the Blockly editor.

A mode consists of:
  - A flow graph (visual nodes: Start → Procedure → ...)
  - Each Procedure node contains Blockly-generated Python code
  - Procedures have event types: on_start, on_frame, on_update, on_stop, on_call

The mode runner:
  1. Loads the mode JSON (flow_graph + procedures)
  2. Wraps each procedure's generated code in a function
  3. Sets up the execution context (imports for macro_runner, screen, overlay, bot, etc.)
  4. Executes the flow graph starting from the Start node
  5. Runs procedures based on their event type
"""
import os
import sys
import json
import time
import threading
import traceback
import importlib
import logging

log = logging.getLogger(__name__)

# ── State ──────────────────────────────────────────────────────
_runner_thread = None
_stop_event = threading.Event()
_active_mode = None
_procs = {}          # proc_id -> {name, code, event, interval, fn}
_frame_threads = []
_update_threads = []
_lock = threading.Lock()


def _build_exec_namespace():
    """Build the namespace that generated procedure code runs in.

    This gives the blocks access to all the bot's modules.
    """
    ns = {}

    # Core bot modules — these are already imported by the bot process
    try:
        import macro_runner
        ns['macro_runner'] = macro_runner
    except Exception:
        pass

    try:
        import screen
        ns['screen'] = screen
    except Exception:
        pass

    try:
        import overlay
        ns['overlay'] = overlay
    except Exception:
        pass

    try:
        import bot
        ns['bot'] = bot
    except Exception:
        pass

    try:
        import teleport_menu
        ns['teleport_menu'] = teleport_menu
    except Exception:
        pass

    try:
        import kraken_dodge
        ns['kraken_dodge'] = kraken_dodge
    except Exception:
        pass

    try:
        import delve_detector
        ns['delve_detector'] = delve_detector
    except Exception:
        pass

    try:
        from crater import loop as crater_loop
        ns['crater'] = type('crater', (), {'loop': crater_loop})()
    except Exception:
        pass

    # Standard library
    ns['time'] = time
    ns['threading'] = threading
    ns['os'] = os
    ns['json'] = json
    ns['log'] = log

    # Keyboard and mouse (for input blocks)
    try:
        import keyboard
        ns['keyboard'] = keyboard
    except Exception:
        pass

    try:
        import mouse
        ns['mouse'] = mouse
    except Exception:
        pass

    return ns


def _compile_proc(proc_id, proc_name, generated_code, event_type, interval_ms):
    """Compile a single procedure's generated code into a callable function."""
    if not generated_code or not generated_code.strip():
        return None

    ns = _build_exec_namespace()

    # The generated code defines functions like:
    #   def proc_Name():
    #       ...
    # We need to wrap it so it runs in our namespace
    fn_name = 'proc_' + proc_name.replace(' ', '_').replace('-', '_')

    # Prepend the function definition wrapper
    full_code = generated_code.strip()

    # If the code already starts with "def proc_..." (from the hat block generator),
    # we just exec it and grab the function
    # If not, wrap it in a function
    if not full_code.startswith('def '):
        # Indent the body
        lines = full_code.split('\n')
        indented = '\n'.join('    ' + line if line.strip() else line for line in lines)
        full_code = f"def {fn_name}():\n{indented}"

    try:
        exec(compile(full_code, f'<procedure:{proc_name}>', 'exec'), ns)
        fn = ns.get(fn_name)
        if fn is None:
            # Try to find any function that starts with proc_
            for key, val in ns.items():
                if key.startswith('proc_') and callable(val):
                    fn = val
                    break
        return fn
    except Exception as e:
        log.error(f"Failed to compile procedure '{proc_name}': {e}")
        traceback.print_exc()
        return None


def _run_proc(fn, proc_name):
    """Run a single procedure function with error handling."""
    if fn is None:
        return
    try:
        fn()
    except Exception as e:
        log.error(f"Error in procedure '{proc_name}': {e}")
        traceback.print_exc()


def _frame_loop(fn, proc_name, interval):
    """60 FPS frame loop for on_frame procedures."""
    while not _stop_event.is_set():
        _run_proc(fn, proc_name)
        time.sleep(interval)


def _update_loop(fn, proc_name, interval):
    """Update loop for on_update procedures."""
    while not _stop_event.is_set():
        _run_proc(fn, proc_name)
        time.sleep(interval)


def _run_flow_graph(flow_graph, compiled_procs):
    """Execute the flow graph: start from Start node, follow edges to procedures."""
    nodes = {n['id']: n for n in flow_graph.get('nodes', [])}
    edges = flow_graph.get('edges', [])
    start_id = flow_graph.get('startNodeId')

    if not start_id or start_id not in nodes:
        log.warning("No start node in flow graph")
        return

    # Build adjacency list
    children = {}
    for edge in edges:
        src = edge.get('from') or edge.get('source')
        dst = edge.get('to') or edge.get('target')
        if src and dst:
            children.setdefault(src, []).append(dst)

    # BFS/DFS from start node — execute procedures in order
    visited = set()
    queue = [start_id]

    while queue and not _stop_event.is_set():
        node_id = queue.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)

        node = nodes.get(node_id)
        if not node:
            continue

        if node.get('type') == 'procedure':
            proc_id = node.get('id')
            proc = compiled_procs.get(proc_id)
            if proc and proc.get('fn'):
                log.info(f"Running procedure: {proc.get('name', proc_id)}")
                _run_proc(proc['fn'], proc.get('name', proc_id))

        # Follow edges to children
        for child_id in children.get(node_id, []):
            if child_id not in visited:
                queue.append(child_id)


def _run_mode_impl(mode_data):
    """Main mode execution thread."""
    global _procs

    try:
        mode_name = mode_data.get('name', 'Unknown')
        log.info(f"Starting custom mode: {mode_name}")

        flow_graph = mode_data.get('flow_graph', {})
        procedures = mode_data.get('procedures', {})

        # Compile all procedures
        compiled = {}
        for proc_id, proc_info in procedures.items():
            code = proc_info.get('generated_code', '') or proc_info.get('code', '')
            name = proc_info.get('name', proc_id)
            event = proc_info.get('event', 'on_start')
            interval = proc_info.get('interval', 100)

            fn = _compile_proc(proc_id, name, code, event, interval)
            if fn:
                compiled[proc_id] = {
                    'name': name,
                    'fn': fn,
                    'event': event,
                    'interval': interval,
                }
                log.debug(f"Compiled procedure: {name} (event={event})")

        _procs = compiled

        # Run on_start procedures (from flow graph order)
        on_start_procs = {pid: p for pid, p in compiled.items() if p['event'] == 'on_start'}
        if on_start_procs:
            # If there's a flow graph with Start node, follow it
            if flow_graph.get('nodes'):
                # Filter compiled to only on_start + on_call procs for flow execution
                flow_procs = {pid: p for pid, p in compiled.items()
                              if p['event'] in ('on_start', 'on_call', 'none')}
                _run_flow_graph(flow_graph, flow_procs)
            else:
                # No flow graph — just run on_start procs
                for pid, proc in on_start_procs.items():
                    if _stop_event.is_set():
                        break
                    _run_proc(proc['fn'], proc['name'])

        if _stop_event.is_set():
            _do_stop()
            return

        # Start on_frame procedures (60 FPS)
        for pid, proc in compiled.items():
            if _stop_event.is_set():
                break
            if proc['event'] == 'on_frame':
                interval = 16 / 1000.0  # ~60fps
                t = threading.Thread(
                    target=_frame_loop,
                    args=(proc['fn'], proc['name'], interval),
                    daemon=True,
                    name=f"frame-{proc['name']}"
                )
                t.start()
                _frame_threads.append(t)
                log.info(f"Started on_frame: {proc['name']} (60fps)")

        # Start on_update procedures (user interval)
        for pid, proc in compiled.items():
            if _stop_event.is_set():
                break
            if proc['event'] == 'on_update':
                interval = proc['interval'] / 1000.0
                t = threading.Thread(
                    target=_update_loop,
                    args=(proc['fn'], proc['name'], interval),
                    daemon=True,
                    name=f"update-{proc['name']}"
                )
                t.start()
                _update_threads.append(t)
                log.info(f"Started on_update: {proc['name']} (every {proc['interval']}ms)")

        # Main loop — wait for stop signal
        while not _stop_event.is_set():
            time.sleep(0.1)

    except Exception as e:
        log.error(f"Mode runner error: {e}")
        traceback.print_exc()

    _do_stop()


def _do_stop():
    """Run on_stop procedures and clean up."""
    global _frame_threads, _update_threads

    log.info("Stopping custom mode...")

    # Run on_stop procedures
    for pid, proc in _procs.items():
        if proc['event'] == 'on_stop':
            try:
                log.info(f"Running on_stop: {proc['name']}")
                _run_proc(proc['fn'], proc['name'])
            except Exception as e:
                log.error(f"Error in on_stop {proc['name']}: {e}")

    # Wait for frame/update threads to finish
    for t in _frame_threads:
        if t.is_alive():
            t.join(timeout=1.0)
    for t in _update_threads:
        if t.is_alive():
            t.join(timeout=1.0)

    _frame_threads = []
    _update_threads = []
    log.info("Custom mode stopped")


def start_mode(mode_data):
    """Start running a custom mode. Returns True on success."""
    global _runner_thread, _active_mode, _stop_event

    if _runner_thread and _runner_thread.is_alive():
        log.warning("Mode already running — stop first")
        return False

    _stop_event = threading.Event()
    _active_mode = mode_data.get('name', 'Unknown')

    _runner_thread = threading.Thread(
        target=_run_mode_impl,
        args=(mode_data,),
        daemon=True,
        name=f"mode-{_active_mode}"
    )
    _runner_thread.start()
    return True


def stop_mode():
    """Stop the currently running custom mode."""
    global _active_mode
    _stop_event.set()
    if _runner_thread and _runner_thread.is_alive():
        _runner_thread.join(timeout=3.0)
    _active_mode = None
    log.info("Mode runner stopped")


def is_running():
    """Check if a custom mode is currently running."""
    return _runner_thread is not None and _runner_thread.is_alive()


def get_active_mode():
    """Return the name of the currently running mode, or None."""
    return _active_mode
