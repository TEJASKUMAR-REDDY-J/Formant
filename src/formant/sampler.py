"""Language mixture and the deterministic, resumable sampler (TR1; 01-data/DATA_PLAN.md sections 5 and 6)."""
import random

LANGS = ["hi", "en", "bn", "mr", "ta", "te", "hi-en"]
V01_HOURS = {"hi": 800, "en": 400, "bn": 300, "mr": 300, "ta": 300, "te": 300, "hi-en": 71}


def mixture(hours, temperature=0.5, epochs=3.0, cap=4.0):
    """Share of batches per language: hours^temperature, with no language repeated more than `cap` times.
    Returns {lang: share}. Raises if the cap makes the epoch budget impossible."""
    budget = epochs * sum(hours.values())
    if cap * sum(hours.values()) < budget:
        raise ValueError(f"{epochs} epochs cannot be met with a cap of {cap}")
    fixed = {}
    while True:
        free = [k for k in hours if k not in fixed]
        left, total = budget - sum(fixed.values()), sum(hours[k] ** temperature for k in free)
        want = {k: left * hours[k] ** temperature / total for k in free}
        over = [k for k in free if want[k] > cap * hours[k] + 1e-9]
        if not over:
            return {k: {**fixed, **want}[k] / budget for k in hours}
        fixed.update({k: cap * hours[k] for k in over})


class Sampler:
    """Yields (language, item) for each micro-batch. One micro-batch = one language; the languages of each global batch are
    stratified (largest remainder), so the global batch matches the mixture exactly. Order depends only on (seed, position)."""

    def __init__(self, items, shares, micro_per_global=32, seed=0):
        self.items, self.shares, self.m, self.seed, self.pos = items, shares, micro_per_global, seed, 0
        self.carry = {k: 0.0 for k in shares}
        self.order = {k: self._shuffle(k, 0) for k in shares}
        self.cursor = {k: [0, 0] for k in shares}                         # [epoch, index]
        self.queue = []
        for k in shares:
            if not items.get(k):
                raise ValueError(f"no items for {k}")

    def _shuffle(self, lang, epoch):
        idx = list(range(len(self.items[lang])))
        random.Random(f"{self.seed}/{lang}/{epoch}").shuffle(idx)
        return idx

    def _plan(self):
        want = {k: self.m * s + self.carry[k] for k, s in self.shares.items()}
        n = {k: int(v) for k, v in want.items()}
        for k in sorted(want, key=lambda k: n[k] - want[k])[: self.m - sum(n.values())]:
            n[k] += 1
        self.carry = {k: want[k] - n[k] for k in want}
        plan = [k for k, c in n.items() for _ in range(c)]
        random.Random(f"{self.seed}/plan/{self.pos}").shuffle(plan)
        return plan

    def next(self):
        if not self.queue:
            self.queue = self._plan()
        lang = self.queue.pop(0)
        epoch, i = self.cursor[lang]
        if i == len(self.order[lang]):
            epoch, i = epoch + 1, 0
            self.order[lang] = self._shuffle(lang, epoch)
        self.cursor[lang] = [epoch, i + 1]
        self.pos += 1
        return lang, self.items[lang][self.order[lang][i]]

    def epochs(self):
        return {k: e + i / len(self.order[k]) for k, (e, i) in self.cursor.items()}

    def state_dict(self):
        return {"pos": self.pos, "carry": dict(self.carry), "queue": list(self.queue),
                "cursor": {k: list(v) for k, v in self.cursor.items()}, "seed": self.seed, "m": self.m, "shares": dict(self.shares)}

    def load_state_dict(self, s):
        if (s["seed"], s["m"], s["shares"]) != (self.seed, self.m, self.shares):
            raise ValueError("sampler state is from a different seed, batch size or mixture")
        self.pos, self.carry, self.queue = s["pos"], dict(s["carry"]), list(s["queue"])
        self.cursor = {k: list(v) for k, v in s["cursor"].items()}
        self.order = {k: self._shuffle(k, e) for k, (e, _) in self.cursor.items()}
