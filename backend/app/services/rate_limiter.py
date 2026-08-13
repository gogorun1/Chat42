from collections import defaultdict, deque
from collections.abc import Callable
from time import monotonic


class RateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._requests: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, user_id: int) -> bool:
        now = self._clock()
        requests = self._requests[user_id]
        while requests and requests[0] <= now - self._window:
            requests.popleft()

        if len(requests) >= self._limit:
            return False

        requests.append(now)
        return True
