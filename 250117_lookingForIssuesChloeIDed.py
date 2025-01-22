"""
250117_lookingForIssuesChloeIDed.py
Marcus Viscardi,    January 17, 2025

So Chloe identified that the WJA0707 strain had different information on
Nemastocks compared to the old data. This makes me really worried that there
could be a systemic issue. Plan is as follows:
1. Look at the differences between the two records
2. Check as it if 0707 might be one of the manually adjusted strains
3. If not, write a new comparator to check all the strains (from scratch)

Let's get started:
"""

# First, lets look at the old record:
old_record_0707 = {
    "WJA_NUMBER": "WJA 0707",
    "DESCRIPTION": "ttc-37(srf0707;3xFLAG)V;dpy-10(???)II",
    "PHENOTYPE": "~wt",
    "RECEIVED_FROM_DATE": "Joshua Arribere/4/10/2018",
    "LOCATION": None,  # null,
    "FROZEN": None,  # null,
    "THAWED": None,  # null,
    "DATE_FROZEN": "|4/13/18|4/13/18",
    "TUBE_NO": "|1|3",
    "TANK_NO": "|JA1|JA2",
    "RACK_NO": "|1|1",  # WHAT THE FUCK... WHY DOES THIS NOT MATCH WITH BELOW, NO WONDER WE'RE CONFUSED
    "RACK_BOX_NO": "|6-7|5-5",
    "DATE_THAWED": "|11/16/18 JAA",
    "NO_OF_TUBES_THAWED": "|1(JA2 5-5)",
    "COMMENTS": "|Made by CRISPR/Cas9 using dpy-10 as a marker  did not check dpy-10 locus   JAA from 284-14 3 1|JAA pg 24 80  24 89 |04/16/18 MNP ok",
    "CAP_COLOR": "brown 04/10/18|brown"
  }
# Pulling out the new record will be a little more awkard, but we can do it:
# Cap Color: Brown
# Box locations:
# 1x JA1-01-07
# 3x JA2-01-05

# Okay let's write a parser to see how bad this is:
import json
from pathlib import Path
from pprint import pprint
from tqdm.auto import tqdm
from itertools import filterfalse

old_database_json_path = Path("240821_OFFICIAL_WORMSTOCKS.json")


def quick_parse_old_db_for_rack_box_info(path_to_json: Path):
    old_database_json = json.loads(path_to_json.read_text())
    better_dict = {}
    for entry in tqdm(old_database_json):
        WJA = entry.pop("WJA_NUMBER")
        better_dict[WJA] = entry
        if not entry["RACK_NO"]:
            continue
        
        RACK_NOs = entry["RACK_NO"].split("|")
        RACK_NOs = list(filterfalse(lambda x: not x, RACK_NOs))
        RACK_BOX_NOs = entry["RACK_BOX_NO"].split("|")
        RACK_BOX_NOs = list(filterfalse(lambda x: not x, RACK_BOX_NOs))
        TANK_NOs = entry["TANK_NO"].split("|")
        TANK_NOs = list(filterfalse(lambda x: not x, TANK_NOs))
        
        RACK_AND_BOX_NOs = []
        RACK_NOs_2 = []
        BOX_NOs_2 = []
        for rack_box in RACK_BOX_NOs:
            if not rack_box:
                continue
            rack, box = rack_box.split("-")
            RACK_AND_BOX_NOs.append([rack, box])
            RACK_NOs_2.append(rack)
            BOX_NOs_2.append(box)
        better_dict[WJA]["RACK_NOs"] = RACK_NOs
        better_dict[WJA]["RACK_BOX_NOs"] = RACK_BOX_NOs
        better_dict[WJA]["RACK_AND_BOX_NOs"] = RACK_AND_BOX_NOs
        better_dict[WJA]["RACK_NOs_2"] = RACK_NOs_2
        better_dict[WJA]["BOX_NOs_2"] = BOX_NOs_2
        better_dict[WJA]["TANK_NOs"] = TANK_NOs
    return better_dict


def identify_bad_strains(better_dict: dict):
    bad_strains = []
    for WJA, entry in better_dict.items():
        wja_printed = False
        if "RACK_NOs_2" not in entry:
            continue
        for rack1, rack2, rack_box in zip(entry["RACK_NOs"], entry["RACK_NOs_2"],
                                          entry["RACK_BOX_NOs"]):
            if rack1 != rack2:
                if not wja_printed:
                    print(f"{WJA} has mismatched rack numbers:")
                    wja_printed = True
                print(f"\t{rack1} vs {rack2} ({rack_box})")
                bad_strains.append(WJA)
    print(f"Number of bad strains: {len(set(bad_strains))}")
    return bad_strains


if __name__ == '__main__':
    entries_dict = quick_parse_old_db_for_rack_box_info(old_database_json_path)
    identify_bad_strains(entries_dict)
