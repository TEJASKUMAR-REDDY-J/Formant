"""Find and mask personal data in transcripts before tokens are stored (RL1; used by DA2).

Covers numbers and addresses that have a shape: phone, Aadhaar, PAN, card, IFSC, UPI, email, URL, vehicle plate.
Names and street addresses have no shape; they need a named-entity tagger and are NOT caught here.
Digits in any Indian script are handled, as are numbers read out digit by digit in English or Hindi.
"""
import re
import unicodedata

_D = r"(?<![\d])"                                   # not inside a longer number
_E = r"(?![\d])"
_SEP = r"[\s.\-]?"


def _verhoeff(num):
    """Aadhaar's checksum."""
    d = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5], [2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
         [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1], [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
         [8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
    p = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4], [5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
         [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1], [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]]
    c = 0
    for i, ch in enumerate(reversed(num)):
        c = d[c][p[i % 8][int(ch)]]
    return c == 0


def _luhn(num):
    s = 0
    for i, ch in enumerate(reversed(num)):
        x = int(ch) * (1 + i % 2)
        s += x - 9 if x > 9 else x
    return s % 10 == 0


def _digits(s):
    return re.sub(r"\D", "", s)


WORDS = "zero one two three four five six seven eight nine oh double triple ek do teen char chaar paanch panch chhe chah saat aath nau shunya " \
        "शून्य ज़ीरो जीरो एक दो तीन चार पाँच पांच छह छः छे सात आठ नौ डबल ट्रिपल".split()
_W = "|".join(sorted(WORDS, key=len, reverse=True))
_SPOKEN = re.compile(rf"(?<!\w)(?:(?:{_W})[\s,.\-]+){{6,}}(?:{_W})(?!\w)", re.I)   # seven or more digit words in a row

RULES = [  # name, pattern, extra test on the match; order matters (longer identifiers first)
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), None),
    ("URL", re.compile(r"(?:https?://|www\.)\S+", re.I), None),
    ("UPI", re.compile(r"[\w.-]{2,}@[a-z]{2,}(?![\w.])", re.I), None),
    ("CARD", re.compile(_D + r"\d(?:[\s-]?\d){12,18}" + _E), lambda s: 13 <= len(_digits(s)) <= 19 and _luhn(_digits(s))),
    ("AADHAAR", re.compile(_D + r"[2-9]\d{3}" + _SEP + r"\d{4}" + _SEP + r"\d{4}" + _E), lambda s: _verhoeff(_digits(s))),
    ("PHONE", re.compile(_D + r"(?:(?:\+|00)?91" + _SEP + r"|0)?[6-9]\d{4}" + _SEP + r"\d{5}" + _E), None),
    ("PHONE", re.compile(_D + r"(?:(?:\+|00)?91" + _SEP + r"|0)?[6-9](?:" + _SEP + r"\d){9}" + _E), None),
    ("PHONE", re.compile(_D + r"0\d{2,4}" + _SEP + r"\d{6,8}" + _E), lambda s: 10 <= len(_digits(s)) <= 12),     # landline with STD code
    ("PAN", re.compile(r"(?<![A-Z0-9])[A-Z]{3}[ABCFGHLJPT][A-Z]\d{4}[A-Z](?![A-Z0-9])", re.I), None),
    ("IFSC", re.compile(r"(?<![A-Z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Z0-9])"), None),
    ("PLATE", re.compile(r"(?<![A-Z0-9])[A-Z]{2}[\s-]?\d{1,2}[\s-]?[A-Z]{1,3}[\s-]?\d{4}(?!\d)"), None),
    ("LONGNUM", re.compile(_D + r"\d(?:[\s-]?\d){8,}" + _E), None),                                              # any other 9+ digit number
    ("SPOKEN_NUMBER", _SPOKEN, None),
]


def _ascii_digits(t):
    """Same length as t, so match positions carry over."""
    return "".join(str(unicodedata.digit(c)) if unicodedata.category(c) == "Nd" else c for c in t)


def find(text):
    """[(kind, start, end)], left to right, not overlapping."""
    t, taken, hits = _ascii_digits(text), [False] * len(text), []
    for kind, pat, test in RULES:
        for m in pat.finditer(t):
            if any(taken[m.start():m.end()]) or (test and not test(m.group())):
                continue
            taken[m.start():m.end()] = [True] * (m.end() - m.start())
            hits.append((kind, m.start(), m.end()))
    return sorted(hits, key=lambda h: h[1])


def mask(text):
    """(masked text, [kinds]). DA2 drops the audio of any clip whose transcript has a hit."""
    out, pos, kinds = [], 0, []
    for kind, a, b in find(text):
        out += [text[pos:a], f"[{kind}]"]
        pos = b
        kinds.append(kind)
    return "".join(out) + text[pos:], kinds
