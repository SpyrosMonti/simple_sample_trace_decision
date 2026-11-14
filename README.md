# simple_sample_trace_decision

A deterministic sampler that hashes a trace id and returns a keep-or-drop boolean based on a configurable rate, so the same trace id always gets the same decision.

```python
from simple_sample_trace_decision import TraceSampler, should_keep

sampler = TraceSampler(rate=0.1)
keep = sampler.should_keep(b"my-trace-id")
assert keep == should_keep(b"my-trace-id", 0.1)
```

## Why this exists

When sampling traces, you often need the decision to be consistent: if the same trace id is evaluated twice, it must get the same answer. This library solves that by hashing the trace id with SHA-256 and comparing the first 8 bytes (as a big-endian unsigned integer) against a threshold derived from the rate. The trade-off is that the achieved rate is quantised to the nearest representable value out of 2**64, which for practical rates is indistinguishable from the requested rate. The alternative, a random sampler, would give inconsistent decisions and break trace stitching.

## Edge cases

- `rate` must be in `[0.0, 1.0]`; values outside that range raise `ValueError`.
- `trace_id` must be bytes-like (`bytes`, `bytearray`, or `memoryview`); anything else raises `TypeError`.
- A custom `hash_fn` must return a non-negative `int`; violations raise `TypeError` or `ValueError`.
- The default hash uses the first 8 bytes of SHA-256. If you supply your own hash function, it must return an integer in `[0, 2**64 - 1]`; values outside that range are not clamped and will simply fall on one side of the threshold.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

