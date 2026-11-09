import hashlib
from typing import Callable


class TraceSampler:
    """Deterministic trace sampler.

    A sampler is constructed with a rate in [0, 1] and an optional hash
    function.  The hash function maps a trace id (bytes) to a 64-bit unsigned
    integer.  The default hash is the first 8 bytes of SHA-256 interpreted as a
    big-endian unsigned integer.

    The decision for a trace id is deterministic: the same id and rate always
    produce the same keep/drop answer.  The rate is the probability of keeping a
    trace, assuming the hash function distributes ids uniformly.  Because the
    hash output space is finite, the achieved rate is the closest representable
    value to the requested rate.
    """

    def __init__(
        self,
        rate: float,
        hash_fn: Callable[[bytes], int] | None = None,
    ) -> None:
        if not isinstance(rate, (int, float)):
            raise TypeError("rate must be a number")
        if rate < 0.0 or rate > 1.0:
            raise ValueError("rate must be between 0.0 and 1.0 inclusive")
        self._rate = float(rate)
        self._hash_fn = hash_fn if hash_fn is not None else _default_hash

    @property
    def rate(self) -> float:
        """The configured sampling rate."""
        return self._rate

    def should_keep(self, trace_id: bytes) -> bool:
        """Return True if the trace should be kept, False otherwise.

        ``trace_id`` must be bytes-like.  The decision is deterministic for a
        given sampler configuration and trace id.
        """
        if not isinstance(trace_id, (bytes, bytearray, memoryview)):
            raise TypeError("trace_id must be bytes-like")
        raw = bytes(trace_id)
        value = self._hash_fn(raw)
        if not isinstance(value, int):
            raise TypeError("hash function must return an int")
        if value < 0:
            raise ValueError("hash function must return a non-negative integer")
        # Map the 64-bit hash to a fraction in [0, 1).  Using the full 64-bit
        # range keeps the threshold calculation exact for all rates that are
        # representable as floats with denominator 2**64.
        threshold = int(self._rate * (1 << 64))
        return value < threshold


MAX_HASH = (1 << 64) - 1


def _default_hash(data: bytes) -> int:
    """Return the first 8 bytes of SHA-256 as a big-endian unsigned int.

    SHA-256 is used because it is available in the standard library and its
    output is well-distributed.  Taking the first 8 bytes gives a 64-bit value
    without any additional mixing; the bytes are already uniformly distributed.
    """
    digest = hashlib.sha256(data).digest()
    return int.from_bytes(digest[:8], "big")


def should_keep(trace_id: bytes, rate: float) -> bool:
    """Convenience wrapper that builds a default sampler and decides.

    This is equivalent to ``TraceSampler(rate).should_keep(trace_id)``.
    """
    return TraceSampler(rate).should_keep(trace_id)
