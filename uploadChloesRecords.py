"""
betterJSON_DBBuild.py
Marcus Viscardi,    January 19, 2024

Updated in Sept 2024 to work with the database recovery
"""
from __future__ import annotations

from pathlib import Path

from dateutil import parser

from django.db import transaction
from icecream import ic
from datetime import datetime as dt

from tqdm import tqdm

import os
import sys
import pandas as pd


SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_DIR = SCRIPT_DIR
print(SCRIPT_DIR, PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoNemaStocks.settings")
import django

django.setup()

import ArribereNemaStocks.models as nema_models
import profiles.models as profile_models

import environ

env = environ.FileAwareEnv()
environ.Env.read_env()


def timestamp_ic_prefix():
    return dt.now().strftime("ic: %I:%M:%S %p | ")


ic.configureOutput(prefix=timestamp_ic_prefix)
ic("Imports Successful.")


def load_chloe_format_freezes(tsv_path: Path):
    df = pd.read_csv(tsv_path, sep="\t")
    df.columns = [col.strip() for col in df.columns]
    tube_cols = ["# Tubes", "Tank", "Rack", "Rack-Box"]
    df_odd = df.iloc[1::2]
    df_odd = df_odd[tube_cols]
    df_odd.index = df_odd.index - 1
    df = pd.merge(df, df_odd, left_index=True, right_index=True, suffixes=("_1", "_2"))
    return df


def load_chloe_format_freeze_comments(tsv_path: Path):
    df = pd.read_csv(tsv_path, sep="\t")
    df.columns = [col.strip() for col in df.columns]
    df = df.iloc[::2]
    return df


def load_freezes_and_comments(freezes_path: Path, comments_path: Path):
    df_freezes = load_chloe_format_freezes(freezes_path)
    df_comments = load_chloe_format_freeze_comments(comments_path)
    df = pd.merge(df_freezes, df_comments, left_index=True, right_index=True, suffixes=("_freezes", "_comments"))
    wja_matches = (df['WJA_comments'] == df['WJA_freezes']).sum()
    assert wja_matches == df.shape[0]
    df['WJA'] = df['WJA_freezes']
    df.drop(columns=['WJA_freezes', 'WJA_comments'], inplace=True)
    return df


def load_chloe_format_thaws(tsv_path: Path):
    df = pd.read_csv(tsv_path, sep="\t")
    df.columns = [col.strip() for col in df.columns]
    return df


def load_freezes_and_thaws():
    # ic("Loading Freezes and Comments...")
    working_dir = Path(PROJECT_DIR) / "chloesDatabaseRecords"
    freezes_tsv = working_dir / "241003_Temp_Nemastocks_Records - Freezes.tsv"
    freeze_comments_tsv = working_dir / ("241003_Temp_Nemastocks_Records - Freeze Comments.tsv")
    thaws_tsv = working_dir / "241017_Temp_Nemastocks_Records - Thaws.tsv"
    assert working_dir.exists(), f"Working directory does not exist: {working_dir}"
    assert freezes_tsv.exists(), f"Freezes TSV does not exist: {freezes_tsv}"
    assert freeze_comments_tsv.exists(), f"Freeze Comments TSV does not exist: {freeze_comments_tsv}"
    assert thaws_tsv.exists(), f"Thaws TSV does not exist: {thaws_tsv}"
    # ic("All files found.")

    freezes_df = load_freezes_and_comments(freezes_tsv, freeze_comments_tsv)
    thaws_df = load_chloe_format_thaws(thaws_tsv)
    return freezes_df, thaws_df


@transaction.atomic
def make_freezes(freeze_df: pd.DataFrame, force_run: bool = False):
    for idx, row in tqdm(freeze_df.iterrows(), desc="Making Freezes and Tubes"):
        # We need to find the user who froze the tubes and the user that tested them
        # ic(f"Looking for users: {row['Who froze']} and CW")
        user_froze = profile_models.UserProfile.objects.get(initials=row['Who froze'])
        tester = profile_models.UserProfile.objects.get(initials="CW")

        # ic(f"Looking for strain: {row['WJA']}")
        wja_num = int(row['WJA'])
        try:
            strain = nema_models.Strain.objects.get(wja=wja_num)
        except nema_models.Strain.DoesNotExist:
            if force_run:
                ic("STRAIN NOT FOUND, SKIPPING", wja_num)
                continue
            else:
                raise ValueError(f"Strain not found for WJA: {row['WJA']}")
        # ic(strain)

        assert user_froze, f"User not found for initials: {row['Who froze']}"
        assert tester, f"User not found for initials: CW"
        assert strain, f"Strain not found for WJA: {row['WJA']}"

        freeze_group = nema_models.FreezeGroup(
            date_created=parser.parse(row['Date frozen']),
            date_stored=parser.parse(row['Date I moved to LN2']),
            test_check_date=parser.parse(row['Date checked']),
            freezer=user_froze,
            tester=tester,
            tester_comments=row['Comments'],
            strain=strain,
            started_test=True,
            completed_test=True,
            passed_test=True,
            stored=True,

        )
        # ic(freeze_group)
        freeze_group.save()
        # Freeze the tubes for Dewar 1:
        box1 = nema_models.Box.objects.get(dewar=row['Tank_1'][-1], rack=row['Rack_1'], box=row['Rack-Box_1'][-1])
        # ic(box1)
        for tube_index in range(row['# Tubes_1']):
            tube1 = nema_models.Tube(box=box1,
                                     cap_color=row['Cap color'],
                                     date_created=parser.parse(row['Date frozen']),
                                     strain=strain,
                                     freeze_group=freeze_group,
                                     set_number=tube_index,
                                     )
            # ic(tube1)
            tube1.save()
        # Freeze the tubes for Dewar 2:
        box2 = nema_models.Box.objects.get(dewar=row['Tank_2'][-1], rack=row['Rack_2'], box=row['Rack-Box_2'][-1])
        # ic(box2)
        for tube_index in range(row['# Tubes_2']):
            tube2 = nema_models.Tube(box=box2,
                                     cap_color=row['Cap color'],
                                     date_created=parser.parse(row['Date frozen']),
                                     strain=strain,
                                     freeze_group=freeze_group,
                                     set_number=tube_index,
                                     )
            # ic(tube2)
            tube2.save()


@transaction.atomic
def make_thaws(thaw_df: pd.DataFrame, force_run: bool = False):
    for idx, row in tqdm(thaw_df.iterrows(), desc="Making Thaws"):
        # ic(f"Looking for user: {row['Who requested']}")
        user_requested = profile_models.UserProfile.objects.get(initials=row['Who requested'])
        # ic(f"Looking for strain: {row['WJA']}")
        wja_num = int(row['WJA'])
        try:
            strain = nema_models.Strain.objects.get(wja=wja_num)
        except nema_models.Strain.DoesNotExist:
            if force_run:
                ic("STRAIN NOT FOUND, SKIPPING", wja_num)
                continue
            else:
                raise ValueError(f"Strain not found for WJA: {row['WJA']}")
        # ic(strain)
        assert user_requested, f"User not found for initials: {row['Who requested']}"
        tank = row['Tank'][-1]
        rack, box = row['Rack-Box'].split('-')
        # ic(tank, rack, box)
        
        potential_thaw_targets = nema_models.Tube.objects.filter(
            box__dewar=tank,
            box__rack=rack,
            box__box=box,
            strain=strain,
            thawed=False,
            cap_color=row['Cap color'],
        )
        all_strain_tubes = nema_models.Tube.objects.filter(strain=strain)
        ic(potential_thaw_targets, all_strain_tubes)
        if len(potential_thaw_targets) == 0:
            raise ValueError(f"No tubes found for strain: {strain}")
        if len(potential_thaw_targets) == 1 and len(all_strain_tubes) == 1:
            ic("WARNING: Only one tube found for strain, thawing anyway.", strain)
        # Pick the tube with the lowest set number
        thaw_target = min(potential_thaw_targets, key=lambda x: x.set_number)
        # ic(thaw_target)
        thaw_target.thawed = True
        thaw_target.date_thawed = parser.parse(row['When thawed'])
        thaw_target.thaw_requester = user_requested
        thaw_target.save()
        # ic(thaw_target)

if __name__ == '__main__':
    freezes_df, thaws_df = load_freezes_and_thaws()
    
    make_freezes(freezes_df)
    make_thaws(thaws_df)
