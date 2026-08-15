#!/usr/bin/env python3
"""
Locality-sensitive hashing (LSH) index for approximate nearest-neighbor search
over SimHash fingerprints, using Hamming-distance banding.

Why: find_overlaps() in simhash_dedupe.py compares every new hash against every
hash seen so far -- O(n^2) total comparisons. At a few hundred images that's
free; at ~9,000 images that's tens of millions of Hamming-distance calls, and
it only gets worse as the pool grows. Banding turns "compare against everyone"
into "compare against the handful of images that share at least one band" --
close to O(n) overall.

How banding guarantees recall (no missed matches up to the threshold):
  Split the BITS-bit hash into NUM_BANDS contiguous bands. If two hashes differ
  in at most `threshold` bits total, those differing bits can "spoil" at most
  `threshold` bands (each differing bit lives in exactly one band). So as long
  as NUM_BANDS > threshold, at least one band is guaranteed to match exactly
  between the two hashes -- pigeonhole principle. Indexing every item under all
  of its band values, and probing the same bands at query time, therefore
  surfaces every true match within the threshold as a candidate. The actual
  Hamming distance is only computed for that (small) candidate set, never the
  full pool, and non-matches among the candidates are filtered out.

  More bands -> narrower bands -> more false-positive candidates (narrow bands
  collide by chance more often), but guarantees recall at higher thresholds.
  Fewer bands -> wider bands -> fewer, more precise candidates, but only
  guarantees recall up to (num_bands - 1) bits of difference. Use
  recommended_num_bands(threshold) unless you have a specific reason to
  trade recall for speed.
"""

from collections import defaultdict


def recommended_num_bands(threshold: int) -> int:
    """Minimum band count that guarantees catching every match within `threshold` bits."""
    return threshold + 1


class HammingLSHIndex:
    """Bucket SimHash fingerprints by band so near-duplicates can be found without
    scanning the whole index."""

    def __init__(self, bits: int, num_bands: int):
        if num_bands < 1:
            raise ValueError("num_bands must be >= 1")
        if num_bands > bits:
            raise ValueError("num_bands cannot exceed bits")
        self.bits = bits
        self.num_bands = num_bands
        self._band_bounds = self._make_bands(bits, num_bands)
        self._buckets = [defaultdict(list) for _ in range(num_bands)]
        self._hashes = {}

    @staticmethod
    def _make_bands(bits, num_bands):
        base, remainder = divmod(bits, num_bands)
        bounds = []
        start = 0
        for i in range(num_bands):
            width = base + (1 if i < remainder else 0)
            bounds.append((start, width))
            start += width
        return bounds

    def _band_value(self, h: int, band_idx: int) -> int:
        start, width = self._band_bounds[band_idx]
        mask = (1 << width) - 1
        return (h >> start) & mask

    def insert(self, key, h: int) -> None:
        """Add an item to the index under every one of its band buckets."""
        self._hashes[key] = h
        for band_idx in range(self.num_bands):
            self._buckets[band_idx][self._band_value(h, band_idx)].append(key)

    def candidates(self, h: int) -> set:
        """Union of everything sharing at least one band with `h` -- the pruned
        candidate set, not yet filtered by actual Hamming distance."""
        found = set()
        for band_idx in range(self.num_bands):
            bucket = self._buckets[band_idx].get(self._band_value(h, band_idx))
            if bucket:
                found.update(bucket)
        return found

    def query_within(self, h: int, threshold: int, hamming_distance_fn):
        """Candidates whose true Hamming distance to `h` is <= threshold, closest first."""
        results = []
        for key in self.candidates(h):
            d = hamming_distance_fn(h, self._hashes[key])
            if d <= threshold:
                results.append((key, d))
        results.sort(key=lambda pair: pair[1])
        return results
