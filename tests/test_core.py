import unittest

from simple_sample_trace_decision import TraceSampler, should_keep


class TestTraceSampler(unittest.TestCase):
    def test_rate_zero_always_drops(self):
        sampler = TraceSampler(0.0)
        self.assertFalse(sampler.should_keep(b"trace-1"))
        self.assertFalse(sampler.should_keep(b"trace-2"))

    def test_rate_one_always_keeps(self):
        sampler = TraceSampler(1.0)
        self.assertTrue(sampler.should_keep(b"trace-1"))
        self.assertTrue(sampler.should_keep(b"trace-2"))

    def test_deterministic(self):
        sampler = TraceSampler(0.5)
        first = sampler.should_keep(b"abc")
        second = sampler.should_keep(b"abc")
        self.assertEqual(first, second)

    def test_different_ids_can_differ(self):
        sampler = TraceSampler(0.5)
        decisions = {sampler.should_keep(bytes([i])) for i in range(256)}
        self.assertEqual(decisions, {True, False})

    def test_custom_hash_controls_decision(self):
        # A hash function that always returns 0 should keep for any rate > 0
        # and drop for rate 0.
        sampler = TraceSampler(0.5, hash_fn=lambda _: 0)
        self.assertTrue(sampler.should_keep(b"anything"))
        sampler0 = TraceSampler(0.0, hash_fn=lambda _: 0)
        self.assertFalse(sampler0.should_keep(b"anything"))

    def test_custom_hash_max_value_drops_unless_rate_one(self):
        max_hash = (1 << 64) - 1
        sampler = TraceSampler(0.5, hash_fn=lambda _: max_hash)
        self.assertFalse(sampler.should_keep(b"anything"))
        sampler1 = TraceSampler(1.0, hash_fn=lambda _: max_hash)
        self.assertTrue(sampler1.should_keep(b"anything"))

    def test_rate_property(self):
        sampler = TraceSampler(0.25)
        self.assertAlmostEqual(sampler.rate, 0.25)

    def test_should_keep_function(self):
        self.assertTrue(should_keep(b"abc", 1.0))
        self.assertFalse(should_keep(b"abc", 0.0))

    def test_invalid_rate_type(self):
        with self.assertRaises(TypeError):
            TraceSampler("0.5")

    def test_invalid_rate_range(self):
        with self.assertRaises(ValueError):
            TraceSampler(-0.1)
        with self.assertRaises(ValueError):
            TraceSampler(1.1)

    def test_invalid_trace_id_type(self):
        sampler = TraceSampler(0.5)
        with self.assertRaises(TypeError):
            sampler.should_keep("not bytes")

    def test_bytearray_and_memoryview_accepted(self):
        sampler = TraceSampler(0.5)
        self.assertEqual(
            sampler.should_keep(bytearray(b"abc")),
            sampler.should_keep(b"abc"),
        )
        self.assertEqual(
            sampler.should_keep(memoryview(b"abc")),
            sampler.should_keep(b"abc"),
        )

    def test_hash_function_must_return_int(self):
        sampler = TraceSampler(0.5, hash_fn=lambda _: "not an int")
        with self.assertRaises(TypeError):
            sampler.should_keep(b"abc")

    def test_hash_function_must_return_non_negative(self):
        sampler = TraceSampler(0.5, hash_fn=lambda _: -1)
        with self.assertRaises(ValueError):
            sampler.should_keep(b"abc")


if __name__ == "__main__":
    unittest.main()
