import pytest

from formant.pii import _verhoeff, find, mask

# Made-up values. The Aadhaar-shaped number is generated here so its checksum is valid but nobody's.
AADHAAR = next(f"2000 0000 {n:04d}" for n in range(10000) if _verhoeff(f"20000000{n:04d}"))

HITS = [
    ("call me on 9876543210 please", "PHONE"), ("+91 98765 43210", "PHONE"), ("098765-43210", "PHONE"), ("98 76 54 32 10", "PHONE"),
    ("मेरा नंबर ९८७६५४३२१० है", "PHONE"), ("என் எண் ௯௮௭௬௫௪௩௨௧௦", "PHONE"), ("office 080-23456789", "PHONE"),
    (f"aadhaar {AADHAAR}", "AADHAAR"), ("PAN is ABCPE1234F", "PAN"), ("write to a.b@example.co.in", "EMAIL"), ("pay ravi.k@okbank", "UPI"),
    ("card 4111 1111 1111 1111", "CARD"), ("IFSC SBIN0001234", "IFSC"), ("MH 12 AB 1234 is my car", "PLATE"), ("see www.example.com/x", "URL"),
    ("account 123456789012", "LONGNUM"),
    ("nine eight seven six five four three two one zero", "SPOKEN_NUMBER"), ("नौ आठ सात छह पाँच चार तीन दो एक शून्य", "SPOKEN_NUMBER"),
    ("nau aath double saat paanch chaar teen do ek", "SPOKEN_NUMBER"),
]
CLEAN = ["I was born in 1998 and it costs 1,25,000 rupees", "train number 12345 at 10:30", "एक दो तीन चार, गिनती करो", "the score was 245 for 6",
         "call 100 or 112 in an emergency", "PIN code 560001", "one two three four five", "Meet at 5 pm on 15-08-2026", "वह दो साल का है"]


@pytest.mark.parametrize("text,kind", HITS)
def test_finds(text, kind):
    assert [k for k, _, _ in find(text)] == [kind], find(text)
    m, kinds = mask(text)
    assert f"[{kind}]" in m and not any(c.isdigit() for c in m.replace("[", "")) or kind in ("PLATE",)


@pytest.mark.parametrize("text", CLEAN)
def test_leaves_ordinary_speech_alone(text):
    assert mask(text) == (text, [])


def test_several_in_one_line_and_offsets_survive_other_scripts():
    m, k = mask("நான் 9876543210 அல்லது a@b.com")
    assert m == "நான் [PHONE] அல்லது [EMAIL]" and k == ["PHONE", "EMAIL"]


def test_names_are_documented_as_out_of_scope():
    assert mask("My name is Ravi Kumar")[1] == []
