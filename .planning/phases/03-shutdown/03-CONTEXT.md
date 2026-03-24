# Phase 3: Shutdown - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

The pipeline terminates itself cleanly when the video file ends. All three processes (producer, blurrer, display) exit without manual intervention. SharedMemory blocks are released. No zombie processes or leaked semaphores remain.

</domain>

<decisions>
## Implementation Decisions

### Shutdown trigger & propagation
- The frame producer (source) detects EOF and initiates shutdown
- A `multiprocessing.Event` (passed to all processes at startup) is used as the stop flag
- Producer sets the Event when EOF is hit, then joins the other processes before exiting itself

### Process termination order
- Pipeline order: Producer exits first, then Blurrer, then Display
- The main script / entry point is responsible for calling `join()` on all child processes

### SharedMemory cleanup
- The main script owns the lifecycle: it creates SharedMemory and calls `shm.unlink()` after all processes have been joined
- Each process calls `shm.close()` on its own view before exiting
- Cleanup is wrapped in `try/finally` to ensure `unlink()` runs even if an exception occurs

### Hang / stuck process handling
- A timeout is used when joining: `join(timeout=N)`; if a process is still alive after the timeout, call `terminate()` (force-kill)
- After a force-kill, SharedMemory cleanup still runs (best-effort `shm.unlink()`)
- Timeout duration is a hardcoded constant (e.g. 5 seconds) — no config needed

### Claude's Discretion
- Exact timeout value (5 seconds suggested but Claude can adjust)
- Whether to log a warning when force-kill is triggered
- How to handle the case where `shm.unlink()` itself raises an error during cleanup

</decisions>

<specifics>
## Specific Ideas

- No specific references — open to standard multiprocessing patterns

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-shutdown*
*Context gathered: 2026-03-24*
