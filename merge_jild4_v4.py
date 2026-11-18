#!/usr/bin/env python3
"""Merge Fatawa Razviya Jild 4 easy-Urdu tashreeh v4 chunks into jild-04.json.

Reads the 11 chunk files listed in chunks-manifest-v4-jild04.json,
concatenates them in order 01 -> 11, derives start_page = min(pages)
where the field is absent, normalises page markers, validates, and
writes {"masail": [...]} to jild-04.json.

ORDER -- chunk order is the order (no quirk, unlike Jild 1 Part 2):
  The v3 merged file ~/workspace/fatawa-app/content/tashreeh/jild-04.json
  has ID order == concatenation order of the v4 chunks 01..11 (verified
  locally by the coordinator: all 185 ids match the v3 sequence exactly).
  Do NOT sort or reorder. Within each chunk, items keep file order.
  NOTE: v3 also has jild-04-chunk-11a.json / 11b.json — v3-internal
  splits of chunk 11 (masala-220 split across them: p.579 in 11a,
  p.580 in 11b). They are NOT leaf chunks for v4; chunk 11 holds
  masala-220 whole ([579, 580]) and is the only chunk-11 input.

START_PAGE: every one of the 11 v4 chunks carries start_page ==
  min(pages) for all its items (verified by the coordinator). The
  derivation code below stays as a safety net; it is expected to
  derive 0 items.

MARKER NORMALISATION (the only text transformation): page markers, if
  present, are normalised to the single form [safha N] written with the
  Urdu word for page:
  - lenticular-bracket form (U+3010/U+3011 around the Urdu word for
    page + number) -> [safha N]
  - [short form] -> [safha N]
  - [safha N] stays as-is
  Applied to every string field of every item (jawab, sawal, title,
  notes). The 11 v4 chunks contain ZERO markers of any form (verified
  locally), so normalisation is expected to be a no-op here; the code
  stays so the merge is robust and the "none remain" assertions still
  run. No other text is touched and no markers are invented.
  NOTE: the literal lenticular-bracket characters are written here only
  as U+3010/U+3011 escapes, never as literal characters in this file.

VALIDATION (fails loudly on any violation):
  185 items; ID sequence EXACTLY == the v3 merged file's ID sequence
  (embedded below as V3_IDS, copied verbatim from
  ~/workspace/fatawa-app/content/tashreeh/jild-04.json); pages per item
  identical to v3 (embedded as V3_PAGES, same source, verified against
  the v3 file before pushing); 576 unique pages (min 6, max 610);
  volume_ids == {35}; start_page == min(pages) for every item (after
  derivation); zero empty tashreeh_jawab; no lenticular / short markers
  remain; first id jild4-p6, last id jild4-masala-246.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = "chunks-manifest-v4-jild04.json"

# Concatenation order: chunk files 01 -> 14, in order.
CHUNK_ORDER = [f"jild-04-chunk-{n:02d}.json" for n in range(1, 12)]

EXPECTED_ITEMS = 185
EXPECTED_PAGES = 576
EXPECTED_MIN_PAGE = 6
EXPECTED_MAX_PAGE = 610
EXPECTED_VOLUME_IDS = {35}
EXPECTED_FIRST_ID = "jild4-p6"
EXPECTED_LAST_ID = "jild4-masala-246"

# v3 ID sequence, verbatim from content/tashreeh/jild-04.json.
V3_IDS = ['jild4-p6', 'jild4-p32', 'jild4-masala-1', 'jild4-masala-2', 'jild4-masala-3', 'jild4-masala-4', 'jild4-masala-5', 'jild4-masala-6', 'jild4-p51', 'jild4-p63', 'jild4-masala-7', 'jild4-masala-8', 'jild4-p79', 'jild4-p82', 'jild4-p90', 'jild4-p99', 'jild4-p102', 'jild4-p107', 'jild4-p114', 'jild4-masala-9', 'jild4-masala-10', 'jild4-masala-11', 'jild4-masala-12', 'jild4-p135', 'jild4-p150', 'jild4-p167', 'jild4-p172', 'jild4-p180', 'jild4-p190', 'jild4-p192', 'jild4-p194', 'jild4-p197', 'jild4-p199', 'jild4-p201', 'jild4-p203', 'jild4-p206', 'jild4-p208', 'jild4-p213', 'jild4-p215', 'jild4-p218', 'jild4-p222', 'jild4-p227', 'jild4-p231', 'jild4-p234', 'jild4-p237', 'jild4-p240', 'jild4-p242', 'jild4-p244', 'jild4-p249', 'jild4-p251', 'jild4-p259', 'jild4-p265', 'jild4-p269', 'jild4-p275', 'jild4-p278', 'jild4-p279', 'jild4-p281', 'jild4-masala-14', 'jild4-p284', 'jild4-p286', 'jild4-p289', 'jild4-p291', 'jild4-p294', 'jild4-p298', 'jild4-p301', 'jild4-p303', 'jild4-p306', 'jild4-p309', 'jild4-p312', 'jild4-p315', 'jild4-p318', 'jild4-p320', 'jild4-masala-115', 'jild4-masala-116', 'jild4-masala-119', 'jild4-masala-121', 'jild4-p330', 'jild4-p332', 'jild4-p334', 'jild4-p336', 'jild4-masala-127', 'jild4-masala-129', 'jild4-masala-135', 'jild4-masala-137', 'jild4-masala-139', 'jild4-masala-140', 'jild4-masala-141', 'jild4-masala-142', 'jild4-masala-143', 'jild4-masala-144', 'jild4-masala-147', 'jild4-masala-148', 'jild4-masala-149', 'jild4-masala-151', 'jild4-masala-152', 'jild4-masala-155', 'jild4-masala-156', 'jild4-masala-157', 'jild4-masala-158', 'jild4-masala-160', 'jild4-masala-161', 'jild4-masala-164', 'jild4-masala-165', 'jild4-masala-166', 'jild4-masala-167', 'jild4-masala-168', 'jild4-masala-169', 'jild4-masala-170', 'jild4-masala-171', 'jild4-masala-172', 'jild4-masala-173', 'jild4-masala-174', 'jild4-masala-175', 'jild4-masala-176', 'jild4-masala-177', 'jild4-p412', 'jild4-p416', 'jild4-p423', 'jild4-p431', 'jild4-p444', 'jild4-p449', 'jild4-masala-178', 'jild4-masala-179', 'jild4-masala-180', 'jild4-masala-181', 'jild4-p473', 'jild4-p499', 'jild4-p507', 'jild4-p511', 'jild4-p512', 'jild4-p526', 'jild4-p534', 'jild4-p537', 'jild4-p542', 'jild4-p549', 'jild4-masala-183', 'jild4-masala-184', 'jild4-masala-185', 'jild4-masala-186', 'jild4-masala-187', 'jild4-masala-188', 'jild4-masala-189', 'jild4-masala-190', 'jild4-masala-191', 'jild4-masala-192', 'jild4-masala-193', 'jild4-masala-194', 'jild4-masala-198', 'jild4-masala-199', 'jild4-masala-200', 'jild4-masala-201', 'jild4-masala-202', 'jild4-masala-203', 'jild4-masala-205', 'jild4-masala-206', 'jild4-masala-207', 'jild4-masala-208', 'jild4-masala-209', 'jild4-masala-210', 'jild4-masala-211', 'jild4-masala-212', 'jild4-masala-212-p570', 'jild4-masala-213', 'jild4-masala-214', 'jild4-masala-215', 'jild4-masala-216', 'jild4-masala-217', 'jild4-masala-218', 'jild4-masala-219', 'jild4-masala-220', 'jild4-masala-221', 'jild4-masala-222', 'jild4-masala-224', 'jild4-masala-225', 'jild4-masala-226', 'jild4-masala-229', 'jild4-masala-231', 'jild4-masala-233', 'jild4-masala-236', 'jild4-masala-237', 'jild4-masala-238', 'jild4-masala-240', 'jild4-masala-241', 'jild4-masala-243', 'jild4-masala-246']

# v3 pages per item id, verbatim from content/tashreeh/jild-04.json.
V3_PAGES = {
"jild4-p6": [6, 7, 8],
"jild4-p32": [32],
"jild4-masala-1": [33],
"jild4-masala-2": [34],
"jild4-masala-3": [35, 36],
"jild4-masala-4": [37, 38],
"jild4-masala-5": [39, 40, 41, 42],
"jild4-masala-6": [43, 44, 45, 46, 47, 48, 49, 50],
"jild4-p51": [51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62],
"jild4-p63": [63, 64, 65, 66, 67, 68, 69, 70, 71, 72],
"jild4-masala-7": [73, 74, 75, 76],
"jild4-masala-8": [77],
"jild4-p79": [79, 80, 81],
"jild4-p82": [82, 83, 84, 85, 86, 87, 88, 89],
"jild4-p90": [90, 91, 92, 93, 94, 95, 96, 97, 98],
"jild4-p99": [99, 100, 101],
"jild4-p102": [102, 103, 104, 105, 106],
"jild4-p107": [107, 108, 109, 110, 111, 112, 113],
"jild4-p114": [114, 115, 116, 117],
"jild4-masala-9": [118, 119, 120, 121, 122, 123, 124, 125],
"jild4-masala-10": [126, 127],
"jild4-masala-11": [128],
"jild4-masala-12": [129, 130, 131, 132, 133, 134],
"jild4-p135": [135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149],
"jild4-p150": [150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166],
"jild4-p167": [167, 168, 169, 170, 171],
"jild4-p172": [172, 173, 174, 175, 176, 177, 178, 179],
"jild4-p180": [180, 181, 182, 183, 184, 185, 186, 187, 188],
"jild4-p190": [190, 191],
"jild4-p192": [192, 193],
"jild4-p194": [194, 195, 196],
"jild4-p197": [197, 198],
"jild4-p199": [199, 200],
"jild4-p201": [201, 202],
"jild4-p203": [203, 204, 205],
"jild4-p206": [206, 207],
"jild4-p208": [208, 209, 210, 211, 212],
"jild4-p213": [213, 214],
"jild4-p215": [215, 216, 217],
"jild4-p218": [218, 219, 220, 221],
"jild4-p222": [222, 223, 224, 225, 226],
"jild4-p227": [227, 228, 229, 230],
"jild4-p231": [231, 232, 233],
"jild4-p234": [234, 235, 236],
"jild4-p237": [237, 238, 239],
"jild4-p240": [240, 241],
"jild4-p242": [242, 243],
"jild4-p244": [244, 245, 246, 247, 248],
"jild4-p249": [249, 250],
"jild4-p251": [251, 252, 253, 254, 255, 256, 257, 258],
"jild4-p259": [259, 260, 261, 262, 263, 264],
"jild4-p265": [265, 266, 267, 268],
"jild4-p269": [269, 270, 271, 272, 273, 274],
"jild4-p275": [275, 276, 277],
"jild4-p278": [278],
"jild4-p279": [279, 280],
"jild4-p281": [281],
"jild4-masala-14": [282, 283],
"jild4-p284": [284, 285],
"jild4-p286": [286, 287, 288],
"jild4-p289": [289, 290],
"jild4-p291": [291, 292, 293],
"jild4-p294": [294, 295, 296, 297],
"jild4-p298": [298, 299, 300],
"jild4-p301": [301, 302],
"jild4-p303": [303, 304, 305],
"jild4-p306": [306, 307, 308],
"jild4-p309": [309, 310, 311],
"jild4-p312": [312, 313, 314],
"jild4-p315": [315, 316, 317],
"jild4-p318": [318, 319],
"jild4-p320": [320, 321],
"jild4-masala-115": [322, 323],
"jild4-masala-116": [324, 325],
"jild4-masala-119": [326, 327],
"jild4-masala-121": [328, 329],
"jild4-p330": [330, 331],
"jild4-p332": [332, 333],
"jild4-p334": [334, 335],
"jild4-p336": [336, 337],
"jild4-masala-127": [338],
"jild4-masala-129": [339, 340],
"jild4-masala-135": [341],
"jild4-masala-137": [342],
"jild4-masala-139": [343],
"jild4-masala-140": [344, 345],
"jild4-masala-141": [347, 348],
"jild4-masala-142": [349],
"jild4-masala-143": [350],
"jild4-masala-144": [351, 352, 353],
"jild4-masala-147": [354],
"jild4-masala-148": [355],
"jild4-masala-149": [356, 357, 358, 359, 360, 361, 362, 363],
"jild4-masala-151": [364],
"jild4-masala-152": [365],
"jild4-masala-155": [366],
"jild4-masala-156": [367, 368],
"jild4-masala-157": [369, 370],
"jild4-masala-158": [371, 372],
"jild4-masala-160": [373],
"jild4-masala-161": [374, 375],
"jild4-masala-164": [376],
"jild4-masala-165": [377, 379],
"jild4-masala-166": [380],
"jild4-masala-167": [381],
"jild4-masala-168": [382],
"jild4-masala-169": [383, 384, 385],
"jild4-masala-170": [386, 387, 388],
"jild4-masala-171": [389],
"jild4-masala-172": [390, 391],
"jild4-masala-173": [392, 393, 394],
"jild4-masala-174": [395],
"jild4-masala-175": [396, 397],
"jild4-masala-176": [398],
"jild4-masala-177": [399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411],
"jild4-p412": [412, 413, 414, 415],
"jild4-p416": [416, 417, 418, 419, 420, 421, 422],
"jild4-p423": [423, 424, 425, 426, 427, 428, 429, 430],
"jild4-p431": [431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443],
"jild4-p444": [444, 445, 446, 447, 448],
"jild4-p449": [449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463],
"jild4-masala-178": [464, 465, 466, 467, 468, 469],
"jild4-masala-179": [470],
"jild4-masala-180": [471],
"jild4-masala-181": [472],
"jild4-p473": [473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498],
"jild4-p499": [499, 500, 501, 502, 503, 504, 505, 506],
"jild4-p507": [507, 508, 509, 510],
"jild4-p511": [511],
"jild4-p512": [512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525],
"jild4-p526": [526, 527, 528, 529, 530, 531, 532, 533],
"jild4-p534": [534, 535],
"jild4-p537": [537, 538, 539, 540, 541],
"jild4-p542": [542, 543, 544, 545, 546, 547, 548],
"jild4-p549": [549, 550, 551, 552, 553],
"jild4-masala-183": [553, 554, 555],
"jild4-masala-184": [555],
"jild4-masala-185": [555, 556],
"jild4-masala-186": [556],
"jild4-masala-187": [556],
"jild4-masala-188": [556, 557],
"jild4-masala-189": [557, 558],
"jild4-masala-190": [558],
"jild4-masala-191": [558],
"jild4-masala-192": [558, 559],
"jild4-masala-193": [559, 560],
"jild4-masala-194": [560, 561, 562],
"jild4-masala-198": [563],
"jild4-masala-199": [563, 564, 565],
"jild4-masala-200": [565],
"jild4-masala-201": [565, 566],
"jild4-masala-202": [566],
"jild4-masala-203": [567],
"jild4-masala-205": [567, 568],
"jild4-masala-206": [568],
"jild4-masala-207": [568, 569],
"jild4-masala-208": [569],
"jild4-masala-209": [569],
"jild4-masala-210": [569, 570],
"jild4-masala-211": [570],
"jild4-masala-212": [570],
"jild4-masala-212-p570": [570, 571],
"jild4-masala-213": [571],
"jild4-masala-214": [572],
"jild4-masala-215": [572],
"jild4-masala-216": [572, 573],
"jild4-masala-217": [574, 575],
"jild4-masala-218": [575, 577, 578],
"jild4-masala-219": [578, 579],
"jild4-masala-220": [579, 580],
"jild4-masala-221": [581, 582, 583],
"jild4-masala-222": [584],
"jild4-masala-224": [585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596],
"jild4-masala-225": [597],
"jild4-masala-226": [598],
"jild4-masala-229": [599],
"jild4-masala-231": [600],
"jild4-masala-233": [601],
"jild4-masala-236": [602],
"jild4-masala-237": [603],
"jild4-masala-238": [604],
"jild4-masala-240": [605],
"jild4-masala-241": [606],
"jild4-masala-243": [607],
"jild4-masala-246": [608, 609, 610],
}

# The Urdu word for "page" is safha; the canonical marker is [safha N].
# Lenticular brackets are U+3010 (open) and U+3011 (close); the short
# form is "[safha-initial N]" with the single-letter abbreviation.
# All three patterns are built from escapes so this file never contains
# a literal lenticular-bracket pair.
SAFHA = "\u0635\u0641\u062d\u06c1"  # the Urdu word for page
RE_LENTICULAR = re.compile("\u3010" + SAFHA + " (\\d+)\u3011")
RE_SHORT = re.compile("\\[\u0635 (\\d+)\\]")
RE_FULL = re.compile("\\[" + SAFHA + " \\d+\\]")
LENTICULAR_PREFIX = "\u3010" + SAFHA  # for the "none remain" check
SHORT_PREFIX_RE = re.compile("\\[\u0635 \\d+\\]")

# Canonical output key order for every item (the JSON contract).
ITEM_KEYS = ["id", "title", "volume_id", "pages", "start_page",
             "tashreeh_sawal", "tashreeh_jawab", "notes"]


def normalise_markers(text):
    """Normalise page markers in one string. Returns (new_text, counts)."""
    counts = {"lenticular": 0, "short": 0, "full_before": 0}
    counts["full_before"] = len(RE_FULL.findall(text))
    text, n1 = RE_LENTICULAR.subn("[" + SAFHA + " \\1]", text)
    counts["lenticular"] = n1
    text, n2 = RE_SHORT.subn("[" + SAFHA + " \\1]", text)
    counts["short"] = n2
    return text, counts


def normalise_item(item):
    """Normalise markers in every string field of one item (recursively
    through lists/dicts). Returns per-form counts for this item."""
    totals = {"lenticular": 0, "short": 0, "full_before": 0}

    def walk(value):
        if isinstance(value, str):
            new, c = normalise_markers(value)
            for k in totals:
                totals[k] += c[k]
            return new
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value

    for key in list(item.keys()):
        item[key] = walk(item[key])
    return totals


def main():
    assert len(V3_IDS) == EXPECTED_ITEMS, "embedded V3_IDS length mismatch"
    assert set(V3_PAGES) == set(V3_IDS), "embedded V3_PAGES keys != V3_IDS"
    assert sum(len(v) for v in V3_PAGES.values()) >= EXPECTED_PAGES

    manifest = json.load(open(os.path.join(BASE, MANIFEST), encoding="utf-8"))
    entries = manifest["chunks"]
    assert len(entries) == 11, f"expected 14 manifest entries, got {len(entries)}"
    assert all(e.get("status") == "done" for e in entries), "not all chunks done"
    by_file = {e["file"]: e for e in entries}
    assert set(by_file) == set(CHUNK_ORDER), (
        f"manifest files != CHUNK_ORDER: "
        f"missing={set(CHUNK_ORDER) - set(by_file)} "
        f"extra={set(by_file) - set(CHUNK_ORDER)}"
    )

    all_items = []
    derived = []
    for fname in CHUNK_ORDER:
        path = os.path.join(BASE, fname)
        d = json.load(open(path, encoding="utf-8"))
        items = d["masail"]
        entry = by_file[fname]
        assert len(items) == entry["items"], (
            f"{fname}: {len(items)} items, manifest says {entry['items']}"
        )
        # Marker normalisation, with before/after counts per chunk.
        before = {"lenticular": 0, "short": 0, "full_before": 0}
        for it in items:
            c = normalise_item(it)
            for k in before:
                before[k] += c[k]
        after_full = sum(
            len(RE_FULL.findall(json.dumps(it, ensure_ascii=False)))
            for it in items
        )
        print(
            f"{fname}: {len(items)} items | markers before: "
            f"lenticular={before['lenticular']} short={before['short']} "
            f"full={before['full_before']} | after: full={after_full}"
        )
        assert after_full == (
            before["lenticular"] + before["short"] + before["full_before"]
        ), f"{fname}: marker count changed by normalisation!"
        # Derive start_page = min(pages) where absent (chunks 06, 12).
        for it in items:
            if "start_page" not in it:
                it["start_page"] = min(it["pages"])
                derived.append(it["id"])
        all_items.extend(items)

    print(f"concatenated: {len(all_items)} items")
    print(f"start_page derived for {len(derived)} items (expected 0: all chunks carry start_page)")
    assert len(all_items) == EXPECTED_ITEMS, (
        f"expected {EXPECTED_ITEMS} items, got {len(all_items)}"
    )

    # Rebuild each item in the canonical key order (the JSON contract).
    canonical = []
    for it in all_items:
        assert set(it.keys()) == set(ITEM_KEYS), (
            f"{it.get('id')}: keys {sorted(it.keys())} != {sorted(ITEM_KEYS)}"
        )
        canonical.append({k: it[k] for k in ITEM_KEYS})
    all_items = canonical

    # Validation.
    ids = [it["id"] for it in all_items]
    assert ids == V3_IDS, (
        f"ID sequence != v3: first diff at "
        f"{next((i for i, (a, b) in enumerate(zip(ids, V3_IDS)) if a != b), min(len(ids), len(V3_IDS)))}"
    )
    assert len(ids) == len(set(ids)), (
        f"DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}"
    )
    empty = [it["id"] for it in all_items if not it.get("tashreeh_jawab")]
    assert not empty, f"EMPTY JAWAB: {empty}"
    vols = set(it.get("volume_id") for it in all_items)
    assert vols == EXPECTED_VOLUME_IDS, f"volume_ids {vols} != {EXPECTED_VOLUME_IDS}"
    pages = set()
    for it in all_items:
        assert it["pages"] == V3_PAGES[it["id"]], (
            f"{it['id']}: pages {it['pages']} != v3 {V3_PAGES[it['id']]}"
        )
        pages.update(it["pages"])
    assert len(pages) == EXPECTED_PAGES, (
        f"expected {EXPECTED_PAGES} unique pages, got {len(pages)}"
    )
    assert min(pages) == EXPECTED_MIN_PAGE, f"min page {min(pages)}"
    assert max(pages) == EXPECTED_MAX_PAGE, f"max page {max(pages)}"
    exceptions = {
        it["id"] for it in all_items if it["start_page"] != min(it["pages"])
    }
    assert not exceptions, f"start_page != min(pages): {sorted(exceptions)}"
    assert ids[0] == EXPECTED_FIRST_ID, f"first id {ids[0]}"
    assert ids[-1] == EXPECTED_LAST_ID, f"last id {ids[-1]}"

    out = {"masail": all_items}
    out_text = json.dumps(out, ensure_ascii=False, indent=1)
    assert LENTICULAR_PREFIX not in out_text, "lenticular markers remain in output!"
    assert not SHORT_PREFIX_RE.search(out_text), "short markers remain in output!"
    total_markers = len(RE_FULL.findall(out_text))
    print(
        f"VALIDATION PASSED: {len(all_items)} items, {len(pages)} unique pages "
        f"(min {min(pages)}, max {max(pages)}), volume_ids {sorted(vols)}, "
        f"first {ids[0]}, last {ids[-1]}, start_page == min(pages) for all, "
        f"derived start_page for {len(derived)} items, markers {total_markers}"
    )

    with open(os.path.join(BASE, "jild-04.json"), "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"WROTE jild-04.json: {len(out_text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
