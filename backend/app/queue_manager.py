"""
Priority request queue — the anti-crash layer.

WHY THIS EXISTS
---------------
FastAPI can accept hundreds of simultaneous connections, but a single local
GPU can only generate one or two answers at a time. Every LLM call is funnelled
through a bounded priority queue served by MAX_CONCURRENT_LLM workers. Extra
requests WAIT; when the wait line is full we shed load with HTTP 503.

FIX (BUG #2, critical): in v2.0 the worker resolved the future as soon as
`stream_chat()` returned — but token generation happens lazily while the SSE
endpoint consumes the generator, i.e. OUTSIDE the queue. N clients could still
generate concurrently, defeating the whole layer. Now each job carries a
`released` event: the worker keeps its slot BUSY until the endpoint finishes
consuming the stream (or GENERATION_TIMEOUT expires). The concurrency cap is
therefore enforced end-to-end, retrieval + generation.

FIX (BUG #11): if a caller times out while waiting, its future is cancelled;
the worker now detects cancelled jobs and skips them instead of burning GPU
time on an answer nobody will read.

PRIORITISATION
--------------
Lower number = served first. Follow-ups in a live conversation beat brand-new
questions; short questions get a small boost. Ties break by arrival order
(FIFO), so equal-priority requests cannot starve. Note: FIFO fairness only
holds WITHIN a priority level — under sustained load, a stream of follow-ups
can delay new conversations. If that shows up in practice, add priority aging
(subtract waited-time from priority) in compute_priority.
"""
import asyncio
import itertools
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import get_settings

logger = logging.getLogger("norma.queue")


class QueueFullError(RuntimeError):
    """Raised when the wait line is full at enqueue time (-> caller returns 503).
    Distinct from any exception raised by the job itself, which propagates
    through the future unchanged instead of being mistaken for overload."""


@dataclass(order=True)
class _Job:
    priority: int
    seq: int                                        # FIFO tiebreaker
    enqueued_at: float = field(compare=False)
    run: Callable[[], Any] = field(compare=False)   # blocking callable (thread)
    future: asyncio.Future = field(compare=False)
    released: asyncio.Event = field(compare=False)  # set by caller when stream is done


class LLMQueue:
    def __init__(self):
        s = get_settings()
        self._pq: asyncio.PriorityQueue[_Job] = asyncio.PriorityQueue(maxsize=s.max_queue_size)
        self._counter = itertools.count()
        self._workers: list[asyncio.Task] = []
        self._n_workers = s.max_concurrent_llm
        self._wait_timeout = s.queue_timeout
        self._generation_timeout = s.generation_timeout

    async def start(self):
        self._workers = [asyncio.create_task(self._worker(i)) for i in range(self._n_workers)]
        logger.info("Queue started with %d worker(s)", self._n_workers)

    async def stop(self):
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)

    @property
    def depth(self) -> int:
        return self._pq.qsize()

    @property
    def is_full(self) -> bool:
        return self._pq.full()

    async def submit(self, run: Callable[[], Any], priority: int = 100):
        """
        Enqueue a blocking callable and await its result.

        Returns (result, release) — the caller MUST call release() (idempotent)
        once it has finished consuming any stream inside `result`, so the
        worker slot is freed. Use try/finally.

        Raises QueueFullError when the wait line is full (-> 503) and
        TimeoutError when the wait exceeds QUEUE_TIMEOUT. Any exception raised
        by `run` itself propagates unchanged (it is not mistaken for overload).
        """
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        job = _Job(priority=priority, seq=next(self._counter),
                   enqueued_at=time.monotonic(), run=run, future=fut,
                   released=asyncio.Event())
        try:
            self._pq.put_nowait(job)
        except asyncio.QueueFull:
            raise QueueFullError("overloaded")

        logger.info("Enqueued job seq=%d prio=%d depth=%d", job.seq, priority, self.depth)
        try:
            result = await asyncio.wait_for(fut, timeout=self._wait_timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            job.released.set()      # never leave a worker waiting on a dead client
            raise
        return result, job.released.set

    async def _worker(self, wid: int):
        while True:
            job = await self._pq.get()
            try:
                # BUG #11: caller already timed out / disconnected -> skip.
                if job.future.done():
                    logger.info("worker=%d skipping cancelled seq=%d", wid, job.seq)
                    continue

                waited = time.monotonic() - job.enqueued_at
                logger.info("worker=%d running seq=%d (waited %.1fs)", wid, job.seq, waited)
                try:
                    # Retrieval + first LLM setup are blocking -> off the loop.
                    result = await asyncio.to_thread(job.run)
                except Exception as e:  # noqa: BLE001
                    if not job.future.done():
                        job.future.set_exception(e)
                    continue

                if job.future.done():   # cancelled while running
                    continue
                job.future.set_result(result)

                # BUG #2: hold this slot until the caller finishes streaming,
                # so at most MAX_CONCURRENT_LLM generations run at once.
                try:
                    await asyncio.wait_for(job.released.wait(),
                                           timeout=self._generation_timeout)
                except asyncio.TimeoutError:
                    logger.warning("worker=%d seq=%d generation timeout after %ds; "
                                   "freeing slot", wid, job.seq, self._generation_timeout)
            finally:
                self._pq.task_done()


def compute_priority(is_followup: bool, question: str) -> int:
    """Lower = served sooner."""
    base = 50 if is_followup else 100   # keep live conversations snappy
    if len(question) < 120:             # quick lookups first
        base -= 5
    return base
