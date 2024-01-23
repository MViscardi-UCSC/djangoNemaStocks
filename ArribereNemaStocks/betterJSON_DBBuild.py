"""
betterJSON_DBBuild.py
Marcus Viscardi,    January 19, 2024


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

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoNemaStocks.settings")
import django

django.setup()

import ArribereNemaStocks.models as nema_models
import profiles.models as profile_models
from hardcoded import CAP_COLOR_OPTIONS

USER_INITIALS_DICT = {
    'AC': ("Annie", "Courney", ((4012, 4100),)),
    'AP': ("Audrey", "Piatt", ((7000, 7100),)),
    'BH': ("Benjamin", "Haag", ((-1, -1),)),
    'CD': ("Christian", "Dunn", ((6101, 6200),)),
    'CN': ("Celine", "N", ((-1, -1),)),
    'CW': ("Chloe", "Wohlenberg", ((3101, 3200),)),
    'DD': ("Dori", "D", ((5101, 5104),)),
    'ES': ("Enisha", "Sehgal", ((7101, 7200),)),
    'Giulio': ("Giulio", "unknown_Giulio", ((-1, -1),)),
    'HM': ("Heddy", "Menendez", ((1050, 1053),)),
    'Heddy': ("Heddy", "Menendez", ((1050, 1053),)),
    'HMN': ("Hannah", "Maul-Newby", ((1000, 1001),)),
    'JAA': ("Joshua", "Arribere", ((1, 999),)),
    'JA': ("Joshua", "Arribere", ((1, 999),)),
    'JK': ("John", "Kim", ((5105, 5150),
                           (5019, 5019),)),  # John also has strain 5019....
    'JS': ("unknown_JS", "unknown_JS", ((-1, -1),)),
    'KY': ("Kevin", "Yang", ((5000, 5001),)),
    'MG': ("Marissa", "Glover", ((3000, 3027),)),
    'mg': ("Marissa", "Glover", ((3000, 3027),)),
    'MM': ("Matthew", "Modena", ((5051, 5100),)),
    'MNP': ("Makenna", "Pule", ((2100, 2150),)),
    'MV': ("Marcus", "Viscardi", ((6000, 6100),)),
    'NV': ("Nitin", "Vidyasagar", ((1151, 1168),)),
    'PM': ("Parissa", "Monem", ((1002, 1049),
                                (1054, 1100),
                                (1169, 1300))),
    'RY': ("Rayka", "Yokoo", ((4000, 4011),)),
    'SN': ("Swathi", "Nair", ((1101, 1150),)),
    'Swathi': ("Swathi", "Nair", ((1101, 1150),)),
    'TE': ("Thea", "E", ((-1, -1),)),
}


def parse_date(date_str, return_format="%Y-%m-%d", return_datetime_object=False):
    # Use dateutil.parser.parse to automatically detect and parse various date formats
    parsed_date = parser.parse(date_str)
    return_value = parsed_date.strftime(return_format)
    if return_datetime_object:
        return_value = parsed_date
    return return_value


def timestamp_ic_prefix():
    return dt.now().strftime("ic: %I:%M:%S %p | ")


ic.configureOutput(prefix=timestamp_ic_prefix)
ic("Imports Successful.")


# Load the old database to memory:
def load_old_db():
    database_json_path = '/home/marcus/PycharmProjects/' \
                         'arribereWormDatabase/' \
                         '231114_OFFICIAL_WORMSTOCKS_databaseDownload.json'
    database_json_Path = Path(database_json_path)
    ic(database_json_Path)
    with open(database_json_path, 'r') as f:
        database = json.load(f)  # The database is a list of dictionaries!
    return database


class SimpleStrain:
    def __init__(self, wja: int, description: str, phenotype: str, date_created: date):
        self.wja = wja
        self.description = description
        self.phenotype = phenotype
        self.date_created = date_created

    def to_dict(self):
        return {'wja': self.wja,
                'description': self.description,
                'phenotype': self.phenotype,
                'date_created': self.date_created,
                'formatted_wja': f"WJA{self.wja:04d}",
                }


class SimpleFreeze:
    #     date_created = models.DateField(auto_now_add=True, editable=True)
    #     date_stored = models.DateField(null=True)
    #     strain = models.ForeignKey('Strain', on_delete=models.CASCADE)
    #     freezer = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
    #                                 related_name='freeze_groups',
    #                                 null=True, blank=True)
    #     # cap_color = models.CharField(max_length=50, default='N/A')
    #     started_test = models.BooleanField(default=False)
    #     completed_test = models.BooleanField(default=False)
    #     passed_test = models.BooleanField(default=False)
    #     tester = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
    #                                related_name='tested_freeze_groups',
    #                                null=True, blank=True)
    #     tester_comments = models.CharField(max_length=255, null=True)
    #     test_check_date = models.DateField(null=True)
    #     stored = models.BooleanField(default=False)
    def __init__(self,
                 date_created: date,
                 date_stored: date,
                 strain: nema_models.Strain,
                 freezer: profile_models.UserProfile,
                 started_test: bool,
                 completed_test: bool,
                 passed_test: bool,
                 tester: profile_models.UserProfile,
                 tester_comments: str,
                 test_check_date: date,
                 stored: bool,
                 ):
        self.date_created = date_created
        self.date_stored = date_stored
        self.strain = strain
        self.freezer = freezer
        self.started_test = started_test
        self.completed_test = completed_test
        self.passed_test = passed_test
        self.tester = tester
        self.tester_comments = tester_comments
        self.test_check_date = test_check_date
        self.stored = stored

    def to_dict(self):
        return {'date_created': self.date_created,
                'date_stored': self.date_stored,
                'strain': self.strain,
                'freezer': self.freezer,
                'started_test': self.started_test,
                'completed_test': self.completed_test,
                'passed_test': self.passed_test,
                'tester': self.tester,
                'tester_comments': self.tester_comments,
                'test_check_date': self.test_check_date,
                'stored': self.stored,
                }


class SimpleTube:
    def __init__(self,
                 cap_color: str,
                 date_created: date,
                 date_thawed: date,
                 box: nema_models.Box,
                 strain: nema_models.Strain,
                 thawed: bool,
                 freeze_group: nema_models.FreezeGroup = None,
                 thaw_requester: profile_models.UserProfile = None,
                 ):
        # I want to check if the cap_color is in our hardcoded list
        # If we find some that are not we should stop and add them
        if cap_color not in CAP_COLOR_OPTIONS:
            raise ValueError(f"cap_color {cap_color} not in CAP_COLOR_OPTIONS")
        self.cap_color = cap_color
        self.date_created = date_created
        self.date_thawed = date_thawed
        self.box = box
        self.strain = strain
        self.freeze_group = freeze_group
        self.thawed = thawed
        self.thaw_requester = thaw_requester

    def to_dict(self):
        return {'cap_color': self.cap_color,
                'date_created': self.date_created,
                'date_thawed': self.date_thawed,
                'box': self.box,
                'strain': self.strain,
                'freeze_group': self.freeze_group,
                'thawed': self.thawed,
                'thaw_requester': self.thaw_requester,
                }


class OldStrainEntry:
    def __init__(self, entry_dict):

        # Things from entry dict:
        self.wja = entry_dict['WJA_NUMBER']
        self.description = entry_dict['DESCRIPTION']
        self.phenotype = entry_dict['PHENOTYPE']
        self.received_from_date = entry_dict['RECEIVED_FROM_DATE']
        self.location = entry_dict['LOCATION']
        self.frozen = entry_dict['FROZEN']
        self.thawed = entry_dict['THAWED']
        self.date_frozen = entry_dict['DATE_FROZEN']
        self.tube_no = entry_dict['TUBE_NO']
        self.tank_no = entry_dict['TANK_NO']
        self.rack_no = entry_dict['RACK_NO']
        self.rack_box_no = entry_dict['RACK_BOX_NO']
        self.date_thawed = entry_dict['DATE_THAWED']
        self.no_of_tubes_thawed = entry_dict['NO_OF_TUBES_THAWED']
        self.comments = entry_dict['COMMENTS']
        self.cap_color = entry_dict['CAP_COLOR']
        self.original_dict = entry_dict

        splitable_columns = ['DATE_FROZEN', 'TUBE_NO', 'TANK_NO', 'RACK_NO', 'RACK_BOX_NO', 'DATE_THAWED',
                             'NO_OF_TUBES_THAWED', 'COMMENTS', 'CAP_COLOR']

        split_column_dict = {}
        for column in splitable_columns:
            try:
                split_col = self.original_dict[column].split('|')
            except AttributeError:
                split_col = []
            split_column_dict[column] = [item for item in split_col if item]
        self.split_column_dict = split_column_dict

        # Things we will parse out:
        # For strain:
        self.creation_date = None

        # For freezes/tubes
        self.date_frozen_list = self.split_column_dict['DATE_FROZEN']
        self.tube_no_list = self.split_column_dict['TUBE_NO']
        self.tank_no_list = self.split_column_dict['TANK_NO']
        self.rack_no_list = self.split_column_dict['RACK_NO']
        self.rack_box_no_list = self.split_column_dict['RACK_BOX_NO']
        self.cap_color_list = self.split_column_dict['CAP_COLOR']

        # For tubes/freezes
        self.date_thawed_list = self.split_column_dict['DATE_THAWED']
        self.no_of_tubes_thawed_list = self.split_column_dict['NO_OF_TUBES_THAWED']

        # For strain and freezes
        self.comments_list = self.split_column_dict['COMMENTS']

    def __repr__(self):
        return self.original_dict.__repr__()

    def pprint(self):
        for key, value in self.__dict__.items():
            if key.endswith('_dict'):
                continue
            print(f"{key}: {value}")

    def pprint_lists(self, len_per_item=10):
        print(f"\nPrinting lists for {self.wja}")
        for key, value in self.__dict__.items():
            if key.endswith('_dict'):
                continue
            if key.endswith('_list'):
                list_key_str = f"{key:>25} ({len(value):>2} items): "
                list_strs = [f"{i + 1:0>2}: {item:<{len_per_item}}"
                             if len(item) <= len_per_item + 1
                             else f"{i + 1:0>2}: {item[:len_per_item - 3]:<{len_per_item - 3}}..."
                             for i, item in enumerate(value)]
                print(list_key_str + ' | '.join(list_strs))

    def to_simple_strain(self):
        wja_int = int(self.wja.split(' ')[-1])
        return SimpleStrain(wja=wja_int,
                            description=self.description,
                            phenotype=self.phenotype,
                            date_created=self.creation_date,
                            )

    def simplify_cap_colors(self):
        if len(self.cap_color_list) == len(self.date_frozen_list):
            return
        elif len(self.cap_color_list) == len(self.date_frozen_list) + 1:
            self.cap_color_list.pop(0)
            return
        else:
            raise ValueError(f"cap_color_list and date_frozen_list have different lengths for {self.wja}")

    def return_tubes(self) -> Tuple[List[SimpleTube] | None, str]:
        self.simplify_cap_colors()
        if len(self.date_frozen_list) == 0:
            # print(f"No freeze dates for {self.wja}")
            return None, f"No freeze dates for {self.wja}"
        elif len(self.date_frozen_list) == 1:
            assert len(self.tube_no_list) == 1
            number_of_tubes = int(self.tube_no_list[0])
            tube_list = []
            for tube_to_be in range(number_of_tubes):
                tube_list.append(SimpleTube(cap_color=self.cap_color_list[0],
                                            date_created=self.creation_date,
                                            date_thawed=None,
                                            box=None,
                                            strain=self.to_simple_strain(),
                                            thawed=False,
                                            freeze_group=None,
                                            thaw_requester=None,
                                            ))

    def return_freezes(self) -> Tuple[List[SimpleFreeze] | None, str]:
        pass

    def return_user_initials(self):
        user_initials_set = set()
        for date_thawed_and_user in self.date_thawed_list:
            try:
                date_thaw, user = date_thawed_and_user.split(' ')
            except ValueError:
                ic(date_thawed_and_user, self)
                self.pprint_lists()
                continue
            try:
                parsed_thaw_date = parse_date(date_thaw, return_datetime_object=True)
                user_initials_set.add(user)
            except ValueError:
                ic(date_thaw, user, self)
                self.pprint_lists()
                continue
        return user_initials_set


class SimpleUserProfile:
    def __init__(self,
                 # user: profile_models.User,
                 first_name: str,
                 last_name: str,
                 role: str,
                 initials: str,
                 active_status: bool,
                 strain_numbers_sets: Tuple[Tuple[int, int]],
                 ):
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.initials = initials
        self.active_status = active_status
        self.strain_numbers_sets = strain_numbers_sets

    def __repr__(self):
        return f"{self.first_name} {self.last_name} ({self.initials})"

    def __str__(self):
        return self.__repr__()

    def to_UserProfile(self):
        default_pw = 'augMETuaaSTOP'
        try:
            user = profile_models.User.objects.create_user(username=self.first_name.lower(),
                                                           first_name=self.first_name,
                                                           last_name=self.last_name,
                                                           password=default_pw,
                                                           )
        except django.db.utils.IntegrityError:
            user = profile_models.User.objects.get(username=self.first_name.lower())
        try:
            user_profile = profile_models.UserProfile.objects.create(user=user,
                                                                     role=self.role,
                                                                     initials=self.initials,
                                                                     active_status=self.active_status,
                                                                     )
        except django.db.utils.IntegrityError:
            user_profile = profile_models.UserProfile.objects.get(user=user)
        for strain_numbers_set in self.strain_numbers_sets:
            # First lets check if the strain range already exists:
            strain_range = profile_models.StrainRange.objects.filter(
                user_profile=user_profile,
                strain_numbers_start=strain_numbers_set[0],
                strain_numbers_end=strain_numbers_set[1],
            )
            if strain_range:
                continue
            elif strain_numbers_set[0] == -1 and strain_numbers_set[1] == -1:\
                continue
            else:
                strain_range = profile_models.StrainRange.objects.create(
                    user_profile=user_profile,
                    strain_numbers_start=strain_numbers_set[0],
                    strain_numbers_end=strain_numbers_set[1],
                )
        return user_profile


# Let's just build models for ALL possible boxes:
from django.db import transaction


@transaction.atomic
def make_boxes():
    num_dewars = 2
    num_racks_per_dewar = 6
    num_boxes_per_rack = 8
    num_tubes_per_box = 81
    num_boxes = num_dewars * num_racks_per_dewar * num_boxes_per_rack

    boxes_to_create = []
    for dewar in range(1, num_dewars + 1):
        for rack in range(1, num_racks_per_dewar + 1):
            for box in range(1, num_boxes_per_rack + 1):
                box_name = f"D{dewar}R{rack}B{box}"
                boxes_to_create.append(nema_models.Box(dewar=dewar, rack=rack, box=box))

    nema_models.Box.objects.all().delete()
    ic("Old boxes deleted.")
    nema_models.Box.objects.bulk_create(boxes_to_create)
    ic("New boxes created.", len(boxes_to_create))


def build_simple_user_list(input_dict, ) -> List[SimpleUserProfile]:
    out_dict = {}
    for initials, (first, last, strain_num_sets) in input_dict.items():
        print(initials, first, last, strain_num_sets)
        if (first, last) in out_dict:
            continue
        out_dict[(first, last)] = SimpleUserProfile(first_name=first,
                                                    last_name=last,
                                                    role='o',
                                                    initials=initials,
                                                    active_status=False,
                                                    strain_numbers_sets=strain_num_sets,
                                                    )
    return list(out_dict.values())


# Example strain dictionary for Copilot:
# {'WJA_NUMBER': 'WJA 0066',
# 'DESCRIPTION': 'unc-54(unc-54(e1301)::gfp::TAA::NSUTR)I',
# 'PHENOTYPE': 'ts Unc',
# 'RECEIVED_FROM_DATE': 'Joshua Arribere/4/13/2015',
# 'LOCATION': None,
# 'FROZEN': None,
# 'THAWED': None,
# 'DATE_FROZEN': '|11/22/2017',
# 'TUBE_NO': '|1|1',
# 'TANK_NO': '|JA1|JA2',
# 'RACK_NO': '|2|4',
# 'RACK_BOX_NO': '|2-8|4-5',
# 'DATE_THAWED': None,
# 'NO_OF_TUBES_THAWED': None,
# 'COMMENTS': '|made by CRISPR using dpy-10 as marker in PD2859 background  Contains e1301 mutation conferring ts Unc behavior  JA from PD2859-74 21 4 2|9 120  9 150||formerly|PD 2883 |',
# 'CAP_COLOR': 'blue'}

# Another one:
# wja: WJA 0023
# description: wt/qC1 dpy-19(e1259) glp-1(q339) nIs189[myo-2::GFP] III|
# phenotype: |Green Pharynx, cross GFP hermaphrodites with 2106 to maintain.
# received_from_date: Joshua Arribere/9/2/2014
# location: None
# frozen: 
# thawed: 
# date_frozen: |11/22/2017|1/12/18|1/19/2018|8/02/19|8/02/19|03/05/21|03/05/21|7/18/22|7/18/22
# tube_no: |1|3|1|3|1|1|3|3|1
# tank_no: |JA2|JA1|JA2|JA1|JA2|JA1|JA2|JA1|JA2
# rack_no: |4|1|1|3|1|2|5|4|2
# rack_box_no: |4-5|1-1|1-1|3-4|1-5|2-6|5-6|4-3|2-3
# date_thawed: |11/21/2017 JAA|2/21/19 MNP|4/15/19 RY|7/9/19 PM|11/26/19 MG|02/06/20 AC|10/24/20 AP|2/9/21 AP|4/3/21 AP|5/25/21 AP|05/27/21 AC|6/15/22 MV|6/8/23 BH
# no_of_tubes_thawed: |1(JA2 4-5)|1(JA1 1-1)|1(JA1 1-1)|1(JA1 1-1)|1(JA1 3-4)|1(JA1 3-4)|1(JA2 1-1)|1(JA1 3-4)|1(JA2 1-5)|1(JA2 5-6)|1(JA2 5-6)|1(JA2 5-6)|1(JA1 4-3)
# comments: |PD5760 crossed with N2  pick wt GFP  to maintain|5 124|formerly|PD 2840 |1/16/18 MNP ok, some contamination|pink (test)|8/5/19 PM G+, good|3/8/21 AC good|7/21/22 CW ok- some contamination but good amount of G+ survivors|
# cap_color: grey|pink|pink|green|brown|blue|

def get_creation_date(strain_entry):
    first_cap_color = strain_entry.cap_color.split('|')[0]
    try:
        # Try to break up the first cap color, which is often "color date"
        split_first = first_cap_color.split(' ')
        if len(split_first) == 2:
            # If it is the expected format we'll land here
            color, date = split_first
            creation_date = parse_date(date, return_datetime_object=True)
        elif len(split_first) > 2:
            # Some strains have several dates?
            color, date = split_first[0], split_first[-1]
            creation_date = parse_date(date, return_datetime_object=True)
        elif len(split_first) == 1:
            # Some strains only have a date and no color?
            creation_date = parse_date(split_first[0], return_datetime_object=True)
        else:
            raise ValueError
    except ValueError:
        # The remaining strains do not have a date in their cap color
        # Instead we'll just grab the oldest freeze date and go with that
        freezes = [date for date in strain_entry.date_frozen.split('|') if date]
        creation_date = parse_date(freezes[0], return_datetime_object=True)
    return creation_date


def get_thaw_requester_initials(_old_strain_entries):
    user_initials_super_set = set()
    for i, entry in enumerate(_old_strain_entries):
        # tube_return = entry.return_tubes()
        # freeze_return = entry.return_freezes()
        user_initials_set = entry.return_user_initials()
        user_initials_super_set.update(user_initials_set)
    return user_initials_super_set


if __name__ == '__main__':
    ic(profile_models.UserProfile.objects.all().count())

    db = load_old_db()
    old_strain_entries = []
    new_strains = {}
    for entry in db:
        old_strain = OldStrainEntry(entry)
        old_strain_entries.append(old_strain)

    old_strain_entries[22].pprint()
    old_strain_entries[22].pprint_lists(len_per_item=20)
    # print(old_strain_entries[24].original_dict)
    for i, entry in enumerate(old_strain_entries):
        entry.creation_date = get_creation_date(entry)
        new_strains[entry.wja] = (entry.to_simple_strain())

    # ic(get_thaw_requester_initials(old_strain_entries))
    userrprofiles_list = []
    for simple_user in build_simple_user_list(USER_INITIALS_DICT):
        # profile_models.UserProfile.objects.filter(initials=simple_user.initials).delete()
        profile_models.StrainRange.objects.filter(user_profile__initials=simple_user.initials).delete()
        userrprofiles_list.append(simple_user.to_UserProfile())
    # 
    # # old_strain_entries[22].pprint()
    # # make_boxes()
    # 
    # for col, entries in old_strain_entries[25].split_column_dict.items():
    #     ic(col, len(entries), entries)
    # 
    # no_entry_count, single_entry_count, match_count, two_match_count, fail_count = 0, 0, 0, 0, 0
    # for entry in old_strain_entries:
    #     if (
    #                 len(entry.split_column_dict['TANK_NO']) ==
    #                 len(entry.split_column_dict['TUBE_NO']) ==
    #                 len(entry.split_column_dict['RACK_NO']) ==
    #                 len(entry.split_column_dict['RACK_BOX_NO']) ==
    #                 len(entry.split_column_dict['DATE_FROZEN'])
    #                 ):
    #         if len(entry.split_column_dict['DATE_FROZEN']) == 0:
    #             no_entry_count += 1
    #         elif len(entry.split_column_dict['DATE_FROZEN']) == 1:
    #             # ic("One entry:", entry.wja, entry.date_frozen, entry.tube_no)
    #             single_entry_count += 1
    #         elif entry.split_column_dict['DATE_FROZEN'][-2] != entry.split_column_dict['DATE_FROZEN'][-1]:
    #             ic("Not dup", entry.wja, entry.date_frozen, entry.tube_no)
    #             fail_count += 1
    #         else:
    #             match_count += 1
    #     elif (
    #                 len(entry.split_column_dict['TANK_NO']) ==
    #                 len(entry.split_column_dict['TUBE_NO']) ==
    #                 len(entry.split_column_dict['RACK_NO']) ==
    #                 len(entry.split_column_dict['RACK_BOX_NO']) ==
    #                 len(entry.split_column_dict['DATE_FROZEN'])*2
    #                 ):
    #         two_match_count += 1
    #     else:
    #         ic(entry.wja, entry.date_frozen, entry.tube_no)
    #         fail_count += 1
    # #                                      Same number
    # ic(no_entry_count, single_entry_count, match_count, two_match_count, fail_count)
    # 
    # color_match_dates, color_off_one, color_mismatch_dates = 0, 0, 0
    # for entry in old_strain_entries:
    #     # Using "sets" here lets us collapse cases where we have two copies of the same date for each freeze event
    #     # 1 freeze event has 1 color, but it'll have two entries of the same date
    #     if len(entry.split_column_dict['CAP_COLOR']) == len(set(entry.split_column_dict['DATE_FROZEN'])):
    #         color_match_dates += 1
    #     elif len(entry.split_column_dict['CAP_COLOR']) == len(set(entry.split_column_dict['DATE_FROZEN']))+1:
    #         color_off_one += 1
    #         entry.cap_color_list.pop(0)
    #         # entry.pprint_lists(len_per_item=20)
    #     else:
    #         color_mismatch_dates += 1
    #         ic(entry.wja, entry.split_column_dict['CAP_COLOR'], entry.split_column_dict['DATE_FROZEN'])
    #         # entry.pprint_lists(len_per_item=20)
    # ic(color_match_dates, color_off_one, color_mismatch_dates)
    # 
    # color_match_dates, color_off_one, color_mismatch_dates = 0, 0, 0
    # for entry in old_strain_entries:
    #     # Using "sets" here lets us collapse cases where we have two copies of the same date for each freeze event
    #     # 1 freeze event has 1 color, but it'll have two entries of the same date
    #     if len(entry.split_column_dict['CAP_COLOR']) == len(set(entry.split_column_dict['DATE_FROZEN'])):
    #         color_match_dates += 1
    #     elif len(entry.split_column_dict['CAP_COLOR']) == len(set(entry.split_column_dict['DATE_FROZEN']))+1:
    #         color_off_one += 1
    #         entry.cap_color_list.pop(0)
    #         entry.pprint_lists(len_per_item=20)
    #     else:
    #         color_mismatch_dates += 1
    #         ic(entry.wja, entry.split_column_dict['CAP_COLOR'], entry.split_column_dict['DATE_FROZEN'])
    #         entry.pprint_lists(len_per_item=20)
    # ic(color_match_dates, color_off_one, color_mismatch_dates)
