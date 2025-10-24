"""
shell_tool.py
=============

Expose a single `step()` function that lets an LLM Agent
 - start a shell script
 - observe its output
 - feed in user input when needed

Author: ChatGPT (o3)
"""


import pexpect
import shlex
import uuid
from typing import Dict, Optional, Any

# ---------------------------------------------------------------------------
# Internal session registry  {session_id: pexpect.spawn}
# ---------------------------------------------------------------------------
_SESSIONS: Dict[str, pexpect.spawn] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def step(
    *,
    cmd: Optional[str] = None,
    session_id: Optional[str] = None,
    user_input: Optional[str] = None,
    read_timeout: float = 0.3,
) -> Dict[str, Any]:
    """
    Execute *one* interaction step with a shell script running in a pseudo-TTY.

    Parameters
    ----------
    cmd : str | None
        Command line for the script.  **Provide this ONLY on the first call**
        (i.e. when session_id is None).  Later calls for the same session
        omit `cmd`.
    session_id : str | None
        The opaque ID returned on the first call.  Omit to start a new session.
    user_input : str | None
        Text to send to the script (newline automatically appended).
        Use when the previous call returned {"waiting": True}.
    read_timeout : float
        Seconds to wait for new output before deciding the process is idle /
        waiting for input.  Tweak per workload.

    Returns
    -------
    dict
        {
          "session_id": str,   # always returned
          "output": str,       # newly captured stdout/stderr since last call
          "waiting": bool,     # script is alive & appears to be blocking on input
          "finished": bool     # script has exited (you should drop the session)
        }

    Raises
    ------
    ValueError
        If you forgot to pass `cmd` on first call or used an invalid session_id.
    """
    # -----------------------------------------------------------------------
    # 1) Start or fetch the session
    # -----------------------------------------------------------------------
    if session_id is None:
        if not cmd:
            raise ValueError("`cmd` is required when starting a new session")

        new_id = uuid.uuid4().hex
        # Spawn under /bin/bash -c "<cmd>" so users can give a full shell line
        child = pexpect.spawn(
            "/bin/bash",
            ["-c", cmd],
            encoding="utf-8",
            echo=False,
            timeout=read_timeout,
        )
        _SESSIONS[new_id] = child
        session_id = new_id
    else:
        child = _SESSIONS.get(session_id)
        if child is None:
            raise ValueError(f"Session {session_id!r} not found or already closed")

    # -----------------------------------------------------------------------
    # 2) Feed user input (if any)
    # -----------------------------------------------------------------------
    if user_input is not None:
        child.sendline(user_input)

    # -----------------------------------------------------------------------
    # 3) Collect all output currently available
    # -----------------------------------------------------------------------
    output_chunks: list[str] = []
    waiting = False
    finished = False

    try:
        # Keep draining the PTY until TIMEOUT or EOF
        while True:
            chunk = child.read_nonblocking(size=1024, timeout=read_timeout)
            output_chunks.append(chunk)
    except pexpect.TIMEOUT:
        # No more output within timeout: assume script is idle
        waiting = child.isalive()
    except pexpect.EOF:
        finished = True
        waiting = False

    output = "\n".join(output_chunks)

    # -----------------------------------------------------------------------
    # 4) Clean up if the process is gone
    # -----------------------------------------------------------------------
    if finished:
        child.close(force=True)
        _SESSIONS.pop(session_id, None)

    return {
        "session_id": session_id,
        "output": output,
        "waiting": waiting,
        "finished": finished,
    }


# ---------------------------------------------------------------------------
# Convenience: optional helper to kill a session early
# ---------------------------------------------------------------------------
def terminate(session_id: str) -> None:
    """Force-kill a running session and remove it from the registry."""
    child = _SESSIONS.pop(session_id, None)
    if child and child.isalive():
        child.terminate(force=True)


# ---------------------------------------------------------------------------
# Minimal CLI smoke test: `python -m shell_tool ./demo.sh`
# ---------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m shell_tool '<command>'")
        sys.exit(1)

    cmd_line = " ".join(shlex.quote(a) for a in sys.argv[1:])
    resp = step(cmd=cmd_line)   
    session_id = resp["session_id"]           # start
    print(resp["output"], end="")

    # Simple REPL driver for manual testing
    while not resp["finished"]:
        if resp["waiting"]:
            inp = input("> ")
            resp = step(session_id=session_id, user_input=inp)
        else:
            resp = step(session_id=session_id)

        print(resp["output"], end="")

    print("\n[script finished]")

