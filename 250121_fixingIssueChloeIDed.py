"""
250121_fixingIssueChloeIDed.py
Marcus Viscardi,    January 21, 2025

Chloe and I figured out that some freeze tubes have different rack number information in the database!
This is because the old method of entering the data required the user to enter the rack number twice,
once in the rack number field and once in the rack-box field. There are a subset of tube freezes from
around May 2018 that have mismatched rack numbers. When I wrote the original parser and uploader,
I was not aware of this issue and I just trusted the rack number in its own field and assumed it
matched the rack number in the rack-box field. This is not always the case.

This script will identify the strains that have those mismatched rack numbers, then it will print out
all of those strains and the tubes that have mismatched rack numbers. From there I want to bulk update
the tubes to have the correct rack number. I think I can do this with a single transaction, so that if
I botch it, I can just roll back the whole thing.

Importantly, I want to write the script in a way that if I run it a second time it doesn't compound the
issue further.

Additionally, I think Chloe thawed one of the tubes from the WJA 0707 strain, so I want to make sure
that I can identify that tube and fix it as well without its status as thawed being a problem.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from dateutil import parser
import re

from icecream import ic
from datetime import datetime as dt
from datetime import date
from datetime import timedelta as dt_delta

from tqdm import tqdm

import bisect

import os
import sys
OLD_DB_NAME = "240821_OFFICIAL_WORMSTOCKS.json"


SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_DIR = SCRIPT_DIR
print(SCRIPT_DIR, PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoNemaStocks.settings")
import django

django.setup()

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group, Permission
import ArribereNemaStocks.models as nema_models
import profiles.models as profile_models
from hardcoded import CAP_COLOR_OPTIONS, USER_INITIALS_DICT

from django.db import transaction

from importlib import import_module
identify_funcs = import_module("250117_lookingForIssuesChloeIDed")

import environ

env = environ.FileAwareEnv()
environ.Env.read_env()

@transaction.atomic
def look_at_erroneous_strains(database_path: str):
    entries = identify_funcs.quick_parse_old_db_for_rack_box_info(Path(database_path))
    erroneous_strains = []
    for WJA, entry in entries.items():
        wja_printed = False
        if "RACK_NOs_2" not in entry:
            continue
        for rack1, rack2, rack_box, tank_no in zip(entry["RACK_NOs"], entry["RACK_NOs_2"],
                                                   entry["RACK_BOX_NOs"], entry["TANK_NOs"]):
            if rack1 != rack2:
                if not wja_printed:
                    print(f"{WJA} has mismatched rack numbers:")
                    wja_printed = True
                    strain_entry = nema_models.Strain.objects.get(wja=WJA.lstrip("WJA "))
                    print(strain_entry)
                print(f"\tdatabase: {rack1} vs json: {rack2} ({rack_box}) - "
                      f"Looking for the tubes in the database: "
                      f"[tank: {tank_no}; rack: {rack1}; box: {rack_box[-1]}]")
                tubes = nema_models.Tube.objects.filter(strain=strain_entry,
                                                        box__dewar=tank_no[-1],
                                                        box__rack=rack1,
                                                        box__box=rack_box[-1])
                print(f"\t{len(tubes)} matching tubes in database: {tubes}")
                if len(tubes) > 0:
                    print(f"\tNow fixing these tubes:")
                    # Okay, so here we are. We have the erroneous tubes itentified in the database.
                    # TODO: Now we need to fix them! we really just need to change the rack num from rack1 to rack2
                    #       and then save the tube. It would be nice if we could make this whole process a single
                    #       transaction, so that if I botched it, I could just roll back the whole thing.
                    #       I think I can do that with the following:
                    #       https://docs.djangoproject.com/en/4.2/topics/db/transactions/#django.db.transaction.atomic
                    
                    for tube in tubes:
                        print(f"\t\tOld: {tube}")
                        correct_box = nema_models.Box.objects.get(dewar=tank_no[-1], rack=rack2, box=rack_box[-1])
                        tube.box = correct_box
                        tube.save()
                        print(f"\t\tNew: {tube}")
                else:
                    print("\tNo tubes found in database to fix. DID YOU ALREADY RUN THIS SCRIPT?! Terminating.")
                    break
                erroneous_strains.append(WJA)
    print(f"Number of bad strains: {len(set(erroneous_strains))}")
    

if __name__ == '__main__':
    look_at_erroneous_strains(OLD_DB_NAME)
