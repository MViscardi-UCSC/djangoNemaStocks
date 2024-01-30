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

from tqdm import tqdm

import bisect

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoNemaStocks.settings")
import django

django.setup()

from django.contrib.auth.models import User, Group
import ArribereNemaStocks.models as nema_models
import profiles.models as profile_models
from hardcoded import CAP_COLOR_OPTIONS, USER_INITIALS_DICT

import environ

env = environ.FileAwareEnv()
environ.Env.read_env()

def make_superuser(username):
    try:
        user = User.objects.get(username=username)
        user.is_superuser = True
        user.is_staff = True
        user.save()
    except User.DoesNotExist:
        print(f"User {username} does not exist.")


def parse_date(date_str, return_format="%Y-%m-%d", return_datetime_object=False):
    # Use dateutil.parser.parse to automatically detect and parse various date formats

    # Check if the string has two slashes
    if date_str.count('/') != 2:
        raise ValueError(f"Date {date_str} does not contain two slashes")

    parsed_date = parser.parse(date_str, )
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
    database_json_path = '../240123_OFFICIAL_WORMSTOCKS_export.json'
    database_json_Path = Path(database_json_path)
    ic(database_json_Path)
    with open(database_json_path, 'r') as f:
        database = json.load(f)  # The database is a list of dictionaries!
    # Let's just drop WJA 0000
    database = [x for x in database if x['WJA_NUMBER'] != 'WJA 0000']
    return database


def remove_dups(input_list):
    out_list = []
    for item in input_list:
        if item not in out_list:
            out_list.append(item)
    return out_list


def match_dates(list1, list2, max_delta):
    # Sort both lists
    list1.sort()
    list2.sort()

    matches = {}
    unmatched1 = list1.copy()  # Start with all dates from list1 as unmatched
    unmatched2 = list2.copy()  # Start with all dates from list2 as unmatched

    for date1 in list1:
        # Find the index of the closest date in list2 that is greater than or equal to date1
        index = bisect.bisect_left(list2, date1)

        # Check all dates in list2 that are within max_delta of date1 to find the closest date
        closest_date = None
        min_delta = max_delta + dt_delta(days=1)  # Initialize with a value larger than max_delta

        i = index
        while i < len(list2) and abs(list2[i] - date1) <= max_delta:
            delta = abs(list2[i] - date1)
            if delta < min_delta:
                min_delta = delta
                closest_date = list2[i]
            i += 1

        # If the closest date is within max_delta, add it to the matches and remove it from unmatched lists
        if min_delta <= max_delta:
            matches[date1] = closest_date
            unmatched1.remove(date1)
            unmatched2.remove(closest_date)

    return matches, unmatched1, unmatched2


def assert_no_duplicates(lst):
    assert len(lst) == len(set(lst)), "The list contains duplicates"


class SimpleStrain:
    def __init__(self, wja: int, description: str, phenotype: str, date_created: date, additional_comments: str,
                 build_dict=None):
        self.wja = wja
        self.description = description
        self.phenotype = phenotype
        self.date_created = date_created
        self.additional_comments = additional_comments
        self.build_dict = build_dict

    def to_dict(self):
        return {'wja': self.wja,
                'description': self.description,
                'phenotype': self.phenotype,
                'date_created': self.date_created,
                'formatted_wja': f"WJA{self.wja:04d}",
                'additional_comments': self.additional_comments,
                }

    def to_nemaStrain(self):
        return nema_models.Strain(wja=self.wja,
                                  description=self.description,
                                  phenotype=self.phenotype,
                                  date_created=self.date_created,
                                  additional_comments=self.additional_comments,
                                  )

    def get_nemaStrain(self):
        return nema_models.Strain.objects.get(wja=self.wja)


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
                 simple_strain: SimpleStrain,
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
        self.simple_strain = simple_strain
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

    def to_nemaFreezeGroup(self) -> nema_models.FreezeGroup:
        nema_strain = self.simple_strain.get_nemaStrain()
        try:
            nema_freeze = nema_models.FreezeGroup.objects.get_or_create(
                date_created=self.date_created,
                date_stored=self.date_stored,
                strain=nema_strain,
                freezer=self.freezer,
                started_test=self.started_test,
                completed_test=self.completed_test,
                passed_test=self.passed_test,
                tester=self.tester,
                tester_comments=self.tester_comments,
                test_check_date=self.test_check_date,
                stored=self.stored)
        except Exception as e:
            ic(self)
            raise e
        return nema_freeze

    def get_nemaFreezeGroup(self) -> nema_models.FreezeGroup:
        try:
            return nema_models.FreezeGroup.objects.get(date_stored=self.date_stored,
                                                       strain=self.simple_strain.get_nemaStrain(),
                                                       )
        except Exception as e:
            raise e


class SimpleTube:
    def __init__(self,
                 cap_color: str,
                 date_created: date,
                 date_thawed: date | None,
                 box: nema_models.Box,
                 simple_strain: SimpleStrain,
                 thawed: bool,
                 set_number: int,
                 simple_freeze_group: SimpleFreeze = None,
                 thaw_requester: profile_models.UserProfile = None,
                 ):
        # I want to check if the cap_color is in our hardcoded list
        # If we find some that are not we should stop and add them
        simple_cap_color_options = [option[0] for option in CAP_COLOR_OPTIONS]
        if cap_color.lower() not in simple_cap_color_options:
            raise ValueError(f"cap_color {cap_color} not in CAP_COLOR_OPTIONS")
        self.cap_color = cap_color.lower()
        self.date_created = date_created
        self.date_thawed = date_thawed
        self.box = box
        self.simple_strain = simple_strain
        self.simple_freeze_group = simple_freeze_group
        self.thawed = thawed
        self.set_number = set_number
        self.thaw_requester = thaw_requester

    def to_dict(self):
        return {'cap_color': self.cap_color,
                'date_created': self.date_created,
                'date_thawed': self.date_thawed,
                'box': self.box,
                'strain': self.strain,
                'freeze_group': self.simple_freeze_group,
                'thawed': self.thawed,
                'thaw_requester': self.thaw_requester,
                }

    def to_nemaTube(self) -> nema_models.Tube:
        nema_strain = self.simple_strain.get_nemaStrain()
        nema_freeze_group = self.simple_freeze_group.get_nemaFreezeGroup()
        try:
            nema_tube = nema_models.Tube.objects.get_or_create(
                cap_color=self.cap_color,
                date_created=self.date_created,
                date_thawed=self.date_thawed,
                box=self.box,
                strain=nema_strain,
                freeze_group=nema_freeze_group,
                thawed=self.thawed,
                thaw_requester=self.thaw_requester,
                set_number=self.set_number)
        except Exception as e:
            ic(self)
            raise e
        return nema_tube

    def get_nemaTube(self) -> nema_models.Tube:
        return nema_models.Tube.objects.get(strain=self.simple_strain.get_nemaStrain(),
                                            box=self.box,
                                            freeze_group=self.simple_freeze_group.get_nemaFreezeGroup(),
                                            set_number=self.set_number,
                                            )


class OldStrainEntry:
    def __init__(self, entry_dict):

        # Things from entry dict:
        self.wja = entry_dict['WJA_NUMBER']
        self.formatted_wja = self.wja
        self.stripped_wja = int(self.wja.split(' ')[-1])
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

        self.perform_manual_fixes()

        self.creation_date = self.get_creation_date()

        # if len(self.date_frozen_list) != 0 or len(self.tube_no_list) != 0:
        self.simplify_cap_colors()

        if len(self.tube_no_list) != len(self.date_frozen_list):
            print(self.wja, self.cap_color_list, self.date_frozen_list, self.tube_no_list, sep='\n')
            if self.wja != "WJA 0639":
                raise ValueError(f"tube_no_list and date_frozen_list have different lengths for {self.wja}")

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

    def to_simple_strain(self, build_dict=None):
        wja_int = int(self.wja.split(' ')[-1])
        return SimpleStrain(wja=wja_int,
                            description=self.description,
                            phenotype=self.phenotype,
                            date_created=self.creation_date,
                            additional_comments=self.get_non_freeze_comments(),
                            build_dict=build_dict,
                            )

    def simplify_cap_colors(self):
        if len(self.date_frozen_list) == 0 and len(self.tube_no_list) == 0:
            # Don't worry about it. There area no freezes or tubes
            return
        if len(self.date_frozen_list) == 0 and len(self.tube_no_list) != 0:
            # This is an edge case for a few strains that DO NOT HAVE DATES
            # Examples include:
            known_examples = ['1201', '3065', '3066', '3067', '3068', '3070', '1197']
            special_dt_delta = {'WJA 3070': 15}
            known_examples = [f"WJA {example}" for example in known_examples]
            try:
                delta_days = special_dt_delta.get(self.wja, 25)
                created_date = self.get_creation_date() + dt_delta(days=delta_days)
                if self.wja not in known_examples:
                    print(f"Found a strain without a freeze date: {self.wja}")
                self.date_frozen_list = [created_date.strftime("%m/%d/%Y") for _ in self.tube_no_list]
            except ValueError:
                ic(self)
                self.pprint_lists()
                raise ValueError

        try:
            first_cap_color = self.cap_color_list[0]
            split_first_cap_color = first_cap_color.split(' ')
            if len(split_first_cap_color) > 2 and split_first_cap_color[-1] == split_first_cap_color[-2]:
                # This is the case where we have extra copies of the date in the cap color
                split_first_cap_color = split_first_cap_color[:2]
            color, creation_date = split_first_cap_color
            parse_date(creation_date, return_datetime_object=True)
            self.cap_color_list.pop(0)
        except ValueError:
            # So here we got an error trying to parse the date out of the cap color, so there is no date!
            if not len(self.cap_color_list) == len(set(self.date_frozen_list)):
                ic(self.wja)
                raise ValueError(f"cap_color_list and date_frozen_list have different lengths for {self.wja}")

        if len(self.cap_color_list) == len(set(self.date_frozen_list)):
            # return
            pass
        elif len(self.cap_color_list) == len(set(self.date_frozen_list)) + 1:
            self.cap_color_list.pop(0)
            if len(self.cap_color_list) == len(set(self.date_frozen_list)):
                # return
                pass
            else:
                raise ValueError(f"cap_color_list and date_frozen_list have different lengths for {self.wja}")
        else:
            raise ValueError(f"cap_color_list and date_frozen_list have different lengths for {self.wja}")

        # Now that we high the right number of matching cap colors and freeze dates based on sets,
        # lets expand the colors to match freezes:
        collapsed_freeze_dates = remove_dups(self.date_frozen_list)
        date_to_color_dict = dict(zip(collapsed_freeze_dates, self.cap_color_list))
        self.cap_color_list = [date_to_color_dict[date] for date in self.date_frozen_list]

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

    def get_non_freeze_comments(self):
        non_freeze_comments = []
        for comment in self.comments_list:
            try:
                date_thaw = comment.split(' ')[0]
                parse_date(date_thaw, return_datetime_object=True)
            except ValueError:
                non_freeze_comments.append(comment)
        non_freeze_comments = ' | '.join(non_freeze_comments)
        return non_freeze_comments

    def get_freeze_comments_and_testers(self):
        freeze_date_comments_testers_dict = {}
        for comment in self.comments_list:
            try:
                date_thaw = comment.split(' ')[0]
                parsed_date = parse_date(date_thaw, return_datetime_object=True)
                tester = comment.split(' ')[1]
                parsed_comments = ' '.join(comment.split(' ')[2:])
                if date_thaw not in freeze_date_comments_testers_dict:
                    freeze_date_comments_testers_dict[parsed_date] = {
                        'comments': parsed_comments,
                        'tester': tester,
                    }
                else:
                    raise ValueError

            except ValueError:
                continue
        return freeze_date_comments_testers_dict

    def match_freeze_and_freeze_comments(self, freeze_nest_dict, max_distance=dt_delta(days=10)):
        freeze_comments_and_tester = self.get_freeze_comments_and_testers()
        try:
            matches, unmatched_freezes, unmatched_tests = match_dates(list(freeze_nest_dict.keys()),
                                                                      list(freeze_comments_and_tester.keys()),
                                                                      max_delta=max_distance)
        except ValueError as e:
            # ic(freeze_nest_dict, freeze_comments_and_tester)
            raise e
        assert_no_duplicates(matches.keys())
        assert_no_duplicates(matches.values())
        if len(unmatched_freezes) > 0:
            # ic(unmatched_freezes)
            # self.pprint_lists()
            # raise ValueError(f"Unmatched freezes for {self.wja}: {unmatched_freezes}")
            # print(f"Unmatched freezes for {self.wja}: {unmatched_freezes}")
            pass
        if len(unmatched_tests) > 0:
            # ic(unmatched_tests)
            self.pprint_lists()
            raise ValueError(f"Unmatched tests for {self.wja}: {unmatched_tests}")
        if len(matches) > 1:
            # ic(matches)  # interesting but probably not important
            pass

        for freeze_date, freeze_dicts in freeze_nest_dict.items():
            if freeze_date not in matches:
                # This is the case that was caught above, where we do not have freeze comments for a freeze
                freeze_dicts['general']['tester_comments'] = None
                freeze_dicts['general']['tester'] = None
                freeze_dicts['general']['test_date'] = None
            else:
                tester = freeze_comments_and_tester[matches[freeze_date]]['tester']
                assert tester in USER_INITIALS_DICT, f"Tester {tester} not in USER_INITIALS_DICT"
                freeze_dicts['general']['tester_comments'] = freeze_comments_and_tester[
                    matches[freeze_date]]['comments']
                freeze_dicts['general']['tester'] = freeze_comments_and_tester[
                    matches[freeze_date]]['tester']
                freeze_dicts['general']['test_date'] = matches[freeze_date]
        return freeze_nest_dict

    def to_simple_freeze_and_tube_list(self) -> Tuple[List[SimpleFreeze], List[SimpleTube]] | None:
        # date_created: date,
        # date_stored: date,
        # strain: nema_models.Strain,
        # freezer: profile_models.UserProfile,
        # started_test: bool,
        # completed_test: bool,
        # passed_test: bool,
        # tester: profile_models.UserProfile,
        # tester_comments: str,
        # test_check_date: date,
        # stored: bool,
        # We need to create a parser to get the Freeze dates, and connect them to nearby comments
        if len(self.date_frozen_list) == 0:
            # print(f"No freeze dates for {self.wja}")
            return None
        if any([len(self.date_frozen_list) != len(self.tube_no_list),
                len(self.date_frozen_list) != len(self.tank_no_list),
                len(self.date_frozen_list) != len(self.rack_no_list),
                len(self.date_frozen_list) != len(self.rack_box_no_list),
                ]):
            self.pprint_lists()
            raise ValueError(f"date_frozen_list and tube_no_list have different lengths for {self.wja}")
        if len(self.date_frozen_list) != len(self.cap_color_list):
            raise ValueError(f"date_frozen_list and cap_color_list have different lengths for {self.wja}")
        freeze_nest_dict = {}
        for i, freeze_date in enumerate(self.date_frozen_list):
            try:
                parsed_freeze_date = parse_date(freeze_date, return_datetime_object=True)
                if parsed_freeze_date not in freeze_nest_dict:
                    freeze_nest_dict[parsed_freeze_date] = {'general': {},
                                                            0: {},
                                                            }
                    # General Freeze fields
                    freeze_nest_dict[parsed_freeze_date]['general']['date_created'] = parsed_freeze_date
                    freeze_nest_dict[parsed_freeze_date]['general']['date_stored'] = parsed_freeze_date
                    freeze_nest_dict[parsed_freeze_date]['general']['strain'] = self.to_simple_strain()
                    # Fields for tubes here
                    freeze_nest_dict[parsed_freeze_date][0]['tube_no'] = self.tube_no_list[i]
                    freeze_nest_dict[parsed_freeze_date][0]['tank_no'] = self.tank_no_list[i]
                    freeze_nest_dict[parsed_freeze_date][0]['rack_no'] = self.rack_no_list[i]
                    freeze_nest_dict[parsed_freeze_date][0]['rack_box_no'] = self.rack_box_no_list[i]
                    freeze_nest_dict[parsed_freeze_date][0]['cap_color'] = self.cap_color_list[i]
                else:
                    dict_index = len(freeze_nest_dict[parsed_freeze_date])
                    freeze_nest_dict[parsed_freeze_date][dict_index] = {}
                    freeze_nest_dict[parsed_freeze_date][dict_index]['tube_no'] = self.tube_no_list[i]
                    freeze_nest_dict[parsed_freeze_date][dict_index]['tank_no'] = self.tank_no_list[i]
                    freeze_nest_dict[parsed_freeze_date][dict_index]['rack_no'] = self.rack_no_list[i]
                    freeze_nest_dict[parsed_freeze_date][dict_index]['rack_box_no'] = self.rack_box_no_list[i]
                    freeze_nest_dict[parsed_freeze_date][dict_index]['cap_color'] = self.cap_color_list[i]

                freeze_nest_dict[parsed_freeze_date]['general']['strain'].build_dict = freeze_nest_dict
            except ValueError:
                # ic(freeze_date, self)
                self.pprint_lists()
                continue
            except TypeError:
                # ic(freeze_date, self)
                self.pprint_lists()
                continue
        # ic(self.wja, freeze_nest_dict)
        if len(freeze_nest_dict) > 3:
            # print("interesting")
            pass

        freeze_comments_plus_dict = self.match_freeze_and_freeze_comments(freeze_nest_dict)

        # Now we can build the list of simple freezes:
        simple_freeze_list = []
        simple_tube_list = []
        for freeze_date, freeze_dicts in freeze_comments_plus_dict.items():
            # First we need to check if we have test comments:
            if freeze_dicts['general']['tester_comments'] is None:
                test_comments = None
                test_date = None
                tester = None
                tester_profile = None
            else:
                test_comments = freeze_dicts['general']['tester_comments']
                test_date = freeze_dicts['general']['test_date']
                tester = freeze_dicts['general']['tester']
                try:
                    tester_profile = profile_models.UserProfile.objects.get(initials=tester)
                except profile_models.UserProfile.DoesNotExist as e:
                    ic(freeze_dicts['general']['tester'])
                    raise e
            try:
                unknown_freezer = profile_models.UserProfile.objects.get(initials='XXX')
            except profile_models.UserProfile.DoesNotExist as e:
                ic(freeze_dicts['general']['tester'])
                raise e
            simple_freeze = SimpleFreeze(
                date_created=freeze_dicts['general']['date_created'],
                date_stored=freeze_dicts['general']['date_stored'],
                simple_strain=freeze_dicts['general']['strain'],
                freezer=unknown_freezer,  # TODO: convert this to look up the owner?
                started_test=True,
                completed_test=True,
                passed_test=True,  # TODO: It would be smart to check for "refreeze" here!!
                tester=tester_profile,
                tester_comments=test_comments,
                test_check_date=test_date,
                stored=True,
            )
            simple_freeze_list.append(simple_freeze)
            for key, tube_set_dict in freeze_dicts.items():
                if key == 'general':
                    continue
                for tube_count in range(int(tube_set_dict['tube_no'])):
                    box = nema_models.Box.objects.get(
                        dewar=tube_set_dict['tank_no'][-1:],
                        rack=tube_set_dict['rack_no'],
                        box=tube_set_dict['rack_box_no'].split("-")[-1],
                    )
                    simple_tube = SimpleTube(
                        cap_color=tube_set_dict['cap_color'],
                        date_created=freeze_dicts['general']['date_created'],
                        date_thawed=None,
                        box=box,
                        simple_strain=freeze_dicts['general']['strain'],
                        thawed=False,
                        simple_freeze_group=simple_freeze,
                        thaw_requester=None,
                        set_number=tube_count,
                    )
                    simple_tube_list.append(simple_tube)
        # ic(simple_freeze_list, simple_tube_list)
        return simple_freeze_list, simple_tube_list

    def get_creation_date(self):
        first_cap_color = self.cap_color_list[0]
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
            freezes = [date for date in self.date_frozen.split('|') if date]
            creation_date = parse_date(freezes[0], return_datetime_object=True)
        return creation_date

    def perform_manual_fixes(self):
        # This is literally just a list of fixes that I found while parsing the data
        # They will be for individual strains, and will be applied here to avoid later issues:

        # All of these strains have the same issue with two tube freeze entries but only one date:
        early_strains_with_issues_list = [9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                                          25, 26, 28, 30, 35, 36, 41, 42, 44, 46, 47,
                                          49, 50, 51, 52, 53, 54, 55, 56, 66, 67, 68,
                                          69, 70, 78, 79, 80, 81, 82, 83, 86, 87, 88,
                                          89, 90, 93, 94, 98, 101, 102, 103, 104, 105,
                                          107, 108,  # ... forever... writing code below
                                          ]
        if self.wja in [f"WJA {strain:0>4}" for strain in early_strains_with_issues_list]:
            self.date_frozen_list.append(self.date_frozen_list[0])
        elif self.date_frozen_list:
            # This is ridiculous. There are too many cases like above, I am writing a rule for it:
            if self.date_frozen_list[0] == '11/22/2017' and len(self.date_frozen_list) == 1 and len(
                    self.tube_no_list) == 2:
                # print(f"{self.wja} is a early strain w/ one date (type A)")
                self.date_frozen_list.append(self.date_frozen_list[0])
            elif self.date_frozen_list[0] == '3/15/2018' and len(self.date_frozen_list) == 1 and len(
                    self.tube_no_list) == 2:
                # print(f"{self.wja} is a early strain w/ one date (type B)")
                self.date_frozen_list.append(self.date_frozen_list[0])
            # Revisionism (b/c I don't want to extend the acceptable freeze association window too far):
            elif self.date_frozen_list[-1] == '12/23/19' and self.comments_list[-1].startswith('01/06/20 AC'):
                comment = self.comments_list.pop(-1)
                self.comments_list.append(comment.replace('01/06/20 AC', '12/30/19 AC'))
        if self.comments_list:
            if self.comments_list[-1].startswith('8/9/18 MNP'):
                # ic(self.wja, "This strain we MNP's typo set (8/9/18 to 3/9/18)")
                self.comments_list[-1] = self.comments_list[-1].replace('8/9/18 MNP', '3/9/18 MNP')
            for i, comment in enumerate(self.comments_list):
                if comment.startswith('11/21/2017 JAA '):
                    if self.wja == 'WJA 0042':
                        self.comments_list[i] = comment.replace('11/21/2017 JAA ', '11/11/2017 JAA ')
                    else:
                        self.comments_list[i] = comment.replace('11/21/2017 JAA ', '11/25/2017 JAA ')
                elif comment.startswith('6/26/18 MNP'):
                    self.comments_list[i] = comment.replace('6/26/18 MNP', '5/26/18 MNP')

        # Type 2 list:
        # These have the same issue as our big list up above, but the strains were used more subsiquently
        # So we'll have to insert the correct dates in the middle of the list
        early_strains_with_issues_and_usage_list = [33, 40, 45, 65, 73,
                                                    84, 85, 111, 143, 168,
                                                    278, 330, 331, 573, 574,
                                                    578, 611, 612, 628, 629,
                                                    630, ]
        if self.wja in [f"WJA {strain:0>4}" for strain in early_strains_with_issues_and_usage_list]:
            self.date_frozen_list.insert(1, self.date_frozen_list[0])

        if self.wja == 'WJA 0639':
            # OUR WILDTYPE <3
            self.date_frozen_list.append('9/1/22')
            self.date_frozen_list.append('10/10/22')
            self.date_frozen_list.append('10/10/22')
            self.cap_color_list.append('unknown')
            self.cap_color_list.append('unknown')
            self.date_thawed_list[5] = '03/03/2021 XXX'

        if self.wja == 'WJA 2106':
            # OUR MALES
            self.comments_list[-1] = self.comments_list[-1].replace('3/29/18', '3/29/18 JAA')
        elif self.wja == 'WJA 0045':
            self.no_of_tubes_thawed_list.pop(4)
            self.date_thawed_list.pop(4)
        elif self.wja == 'WJA 0141':
            # This strain has 4 freezes but only one date_frozen
            self.date_frozen_list = ['12/27/2017', '12/27/2017',
                                     '01/30/2018', '01/30/2018']
        elif self.wja == 'WJA 0498':
            # This strain has 5 freezes and 3 dates
            # Based the middle date off when the thaw was done of the first tube
            self.date_frozen_list = ['11/22/2017',
                                     '10/20/2020', '10/20/2020',  # Inferred
                                     '03/16/2022', '03/16/2022']
        elif self.wja == 'WJA 0552':
            # This strain again has 5 freeze and 3 dates
            # It seems like there was a stretch in mid 2018-20 where new freezes were not recorded...
            # Based the middle date off when the thaw was done of the first tube
            self.date_frozen_list = ['11/22/2017',
                                     '02/01/2019', '02/01/2019',  # Inferred
                                     '11/16/2020', '11/16/2020']
            # Also a comment thing!
            self.comments_list[-2] = self.comments_list[-2].replace('11/21/2017 JAA', '11/25/2017 JAA')
            # And a tube color thing!!!!
            self.cap_color_list[1] = 'red'
            # AND a freeze tube thing!?!
            self.no_of_tubes_thawed_list[2] = '1(JA2 1-8)'
        elif self.wja == 'WJA 0572':
            # Same issue
            self.date_frozen_list = ['11/22/2017',
                                     '04/01/2018', '04/01/2018',  # Inferred
                                     '07/26/2019', '07/26/2019']
            # Also a comment thing!
            self.comments_list[-2] = self.comments_list[-2].replace('11/21/2017 JAA', '11/25/2017 JAA')
        elif self.wja == 'WJA 0097':
            # Weird cap colors
            self.cap_color_list = ['green 09/28/17']
        elif self.wja == 'WJA 3129':
            # 3/21/23- typo noticed in phenotype and comments. Phenotype is supposed to be srf1004, not srf0745.
            # Cross description is supposed to begin with 2016 males with 3107 hermaphrodites (not 3017).
            comment = self.comments_list.pop(-1)
            self.comments_list.append(comment.replace('3/21/23- ', 'CW (3/21/23):'))
        elif self.wja == 'WJA 1234':
            comment = self.comments_list.pop(-1)
            self.comments_list.append(comment.replace('10/21/22 CW', 'CW (10/21/22)'))
        elif self.wja == 'WJA 3069':
            # Was missing freeze date:
            self.date_frozen_list.append('4/11/22')
            self.date_frozen_list.append('4/11/22')
        elif self.wja == 'WJA 6014':
            # 9/20/21 NV WT and some dpy-uncs observed, very few survivors, refreeze recommended
            # 9/22/22 CW good- clean and ok amount of worms
            # 9/22/22 CW Comment above is error, meant for 6104
            self.comments_list.pop(-1)
            self.comments_list.pop(-1)
        elif self.wja == 'WJA 3013':
            # seems like an erroneous freeze comment?
            self.comments_list.pop(-1)
        elif self.wja == 'WJA 3015':
            # This comment was meant to be on 3105:
            # 7/21/22 CW ok- some contamination
            self.comments_list.pop(-1)
        elif self.wja == 'WJA 3105':
            self.comments_list.append('7/21/22 CW ok- some contamination')
        elif self.wja == 'WJA 4002':
            # Comment dated like freeze
            self.comments_list[-2] = self.comments_list[-2].replace('8/4/2021 MJV', 'MJV (8/4/2021)')
        elif self.wja == 'WJA 2107':
            # Comment dated like freeze
            self.comments_list[-1] = self.comments_list[-1].replace('05/18/18', 'Note (05/18/18)')
        elif self.wja == 'WJA 0682':
            self.comments_list[-3] = self.comments_list[-3].replace('1/16/18 MNP', '1/20/18 MNP')
        elif self.wja == 'WJA 0628':
            self.comments_list[-3] = self.comments_list[-3].replace('1/16/18 MNP', '1/20/18 MNP')
        elif self.wja == 'WJA 0654':
            self.comments_list[-1] = self.comments_list[-1].replace('1/5/2018 JAA', 'JAA (1/5/2018) Note:')
        elif self.wja == 'WJA 0680':
            self.comments_list[-1] = self.comments_list[-1].replace('1/7/22 note:', 'Note (1/7/22):')
        elif self.wja == 'WJA 0043':
            self.comments_list[4] = self.comments_list[-1].replace('1/16/18 MNP', '1/26/18 MNP')
        elif self.wja == 'WJA 0432':
            color_date = self.cap_color_list.pop(0)
            self.cap_color_list.append('unknown ' + color_date)
            self.cap_color_list.append('unknown')
        elif self.wja == 'WJA 0433':
            color_date = self.cap_color_list.pop(0)
            self.cap_color_list.append('unknown ' + color_date)
            self.cap_color_list.append('unknown')
        elif self.wja == 'WJA 0434':
            color_date = self.cap_color_list.pop(0)
            self.cap_color_list.append('unknown ' + color_date)
            self.cap_color_list.append('unknown')
        elif self.wja == 'WJA 0278':
            self.date_thawed_list[0] = "10/24/2020 SS"
        elif self.wja == 'WJA 0458':
            self.date_thawed_list[4] = '7/9/21 NB'
        elif self.wja == 'WJA 2126':
            self.date_thawed_list[2] = '10/8/20 JW'
        elif self.wja == 'WJA 2128':
            self.no_of_tubes_thawed_list[1] = '1(JA2 1-7)'
            self.date_thawed_list[8] = '5/5/22 XXX'
        elif self.wja == 'WJA 0780':
            self.date_thawed_list[3] = '6/6/23 XXX'
        elif self.wja == 'WJA 5106':
            self.no_of_tubes_thawed_list[0] = '1(JA1 5-6)'
        elif self.wja == 'WJA 6111':
            self.no_of_tubes_thawed_list[0] = '1(JA1 2-4)'
        elif self.wja == 'WJA 5051':
            self.date_thawed_list[2] = '10/8/2020 JW'
        elif self.wja == 'WJA 4005':
            self.date_thawed_list[0] = '12/10/19 AZ'
        elif self.wja == 'WJA ':
            pass

    def parse_thaws(self):
        def _parse_no_tubes_thaw(no_tubes_thawed_item):
            pattern = r"(\d+)\((JA\s?\d+)\s{1,2}(\d+)-(\d+)\)"
            match = re.match(pattern, no_tubes_thawed_item)
            assert match
            no_tubes, tank_no, rack_no, box_no = match.groups()
            return no_tubes, tank_no, rack_no, box_no

        thaws_dict = {}  # key: tank_rack_box: value: (date, user)
        assert len(self.date_thawed_list) == len(self.no_of_tubes_thawed_list)
        for i, (date_thawed_and_user, no_tubes_and_loc) in enumerate(zip(self.date_thawed_list,
                                                                         self.no_of_tubes_thawed_list)):
            try:
                no_tubes, tank_no, rack_no, box_no = _parse_no_tubes_thaw(no_tubes_and_loc)
            except AssertionError:
                ic(no_tubes_and_loc, self)
                self.pprint_lists()
                raise AssertionError(f"Could not parse no_tubes_and_loc ({no_tubes_and_loc}) for {self.wja}")
            try:
                date_thawed, user = date_thawed_and_user.split(' ', 1)
            except ValueError:
                ic(date_thawed_and_user, self)
                self.pprint_lists()
                raise ValueError(f"Could not split date and user ({date_thawed_and_user}) for {self.wja}")
            try:
                parsed_date = parse_date(date_thawed, return_datetime_object=True)
            except ValueError:
                ic(date_thawed, self)
                self.pprint_lists()
                raise ValueError(f"Could not parse date {date_thawed} for {self.wja}")
            box_tuple = (
                tank_no[-1],
                rack_no,
                box_no,
            )
            thaw_dict = {
                'date': parsed_date,
                'user_initials': user,
                'no_tubes': no_tubes,
                'dewar-rack-box': box_tuple,
            }
            if box_tuple in thaws_dict:
                thaws_dict[box_tuple].append(thaw_dict)
            else:
                thaws_dict[box_tuple] = [
                    thaw_dict
                ]

        for i, ((dewar, rack, box), thaw_list) in enumerate(thaws_dict.items()):
            # First lets find the right box:
            try:
                box = nema_models.Box.objects.get(
                    dewar=dewar,
                    rack=rack,
                    box=box,
                )
            except nema_models.Box.DoesNotExist:
                ic(dewar, rack, box)
                raise ValueError(f"The box {dewar}-{rack}-{box} does not exist!")
            # Now let's try to find the right tubes:
            box_tubes = nema_models.Tube.objects.filter(strain__wja=self.stripped_wja,
                                                        box=box)
            for thaw_dict, tube in zip(thaw_list, box_tubes):
                # Get user:
                try:
                    user = profile_models.UserInitials.objects.get(initials=thaw_dict['user_initials']).user_profile
                except profile_models.UserInitials.DoesNotExist:
                    ic(thaw_dict['user_initials'], self)
                    self.pprint_lists()
                    raise ValueError(f"Could not find a user with initials {thaw_dict['user_initials']}")
                thaw_dict['tube'] = tube
                if int(thaw_dict['no_tubes']) != 1:
                    ic(thaw_dict['no_tubes'], thaw_dict['tube'].set_number, thaw_dict['tube'].box)
                    raise ValueError(f"Found a thaw with more than one tube! This seems weird...")
                # Now I want to update the tube record with the thaw info:
                tube.date_thawed = thaw_dict['date']
                tube.thaw_requester = user
                tube.thawed = True
                tube.save()

        # Now let's quickly check the total number of tubes every frozen, and the total number of tubes thawed:
        strain_tubes = nema_models.Tube.objects.filter(strain__wja=self.stripped_wja)
        total_tubes_frozen = strain_tubes.count()
        total_tubes_thawed = strain_tubes.filter(thawed=True).count()
        total_tubes_remaining = strain_tubes.filter(thawed=False).count()
        # ic(total_tubes_frozen, total_tubes_thawed, total_tubes_remaining)


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
        default_pw = env('DEFAULT_USER_PASS')
        try:
            user = profile_models.User.objects.create_user(username=self.first_name.lower(),
                                                           first_name=self.first_name,
                                                           last_name=self.last_name,
                                                           password=default_pw,
                                                           )
        except django.db.utils.IntegrityError:
            user = profile_models.User.objects.get(username=self.first_name.lower())

        if user.username in ['marcus', 'joshua']:
            user.is_superuser = True
            user.is_staff = True
            user.save()

        try:
            user_profile = profile_models.UserProfile.objects.create(user=user,
                                                                     role=self.role,
                                                                     initials=self.initials,
                                                                     active_status=self.active_status,
                                                                     )
        except django.db.utils.IntegrityError:
            user_profile = profile_models.UserProfile.objects.get(user=user)
            if user_profile.initials != self.initials:
                # If this user was already made, try to add the new set of initials to the existing user:
                user_profile.add_initials(self.initials)
        for strain_numbers_set in self.strain_numbers_sets:
            # First lets check if the strain range already exists:
            strain_range = profile_models.StrainRange.objects.filter(
                user_profile=user_profile,
                strain_numbers_start=strain_numbers_set[0],
                strain_numbers_end=strain_numbers_set[1],
            )
            if strain_range:
                continue
            elif strain_numbers_set[0] == -1 and strain_numbers_set[1] == -1:
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
def create_boxes(delete_old=True):
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
    if delete_old:
        nema_models.Box.objects.all().delete()
        ic("Old boxes deleted.")
    nema_models.Box.objects.bulk_create(boxes_to_create)
    ic("New boxes created.", len(boxes_to_create))


@transaction.atomic
def make_strains_from_simple_strains(strains_dict, delete_old=True):
    if delete_old:
        nema_models.Strain.objects.all().delete()
    for wja, simple_strain in strains_dict.items():
        strain_dict = simple_strain.to_dict()
        try:
            db_strain = nema_models.Strain.objects.create(**strain_dict)
        except django.db.utils.IntegrityError:
            db_strain = nema_models.Strain.objects.get(wja=wja)
        # ic(db_strain)
    ic(nema_models.Strain.objects.all().count())


def create_strains(old_db_entries, delete_old=True):
    new_strain_dict = {}
    
    iterator = tqdm(enumerate(old_db_entries), total=len(old_db_entries),
                    desc="Building database strain list")
    for i, entry in iterator:
        # entry.creation_date = entry.get_creation_date()  # added this to __init__
        new_strain = entry.to_simple_strain()
        new_strain_dict[entry.wja] = new_strain

    make_strains_from_simple_strains(new_strain_dict)


def build_simple_user_list(input_dict, ) -> List[SimpleUserProfile]:
    out_dict = {}
    out_list = []
    iterator = tqdm(input_dict.items(), total=len(input_dict),
                    desc="Building initial user list")
    for initials, (first, last, strain_num_sets) in iterator:
        # print(initials, first, last, strain_num_sets)
        out_list.append(SimpleUserProfile(first_name=first,
                                          last_name=last,
                                          role='o',
                                          initials=initials,
                                          active_status=False,
                                          strain_numbers_sets=strain_num_sets,
                                          ))
    return out_list


def get_thaw_requester_initials(_old_strain_entries):
    # This was used to make the USER_INITIALS_DICT that's now in the hardcoded.py file
    user_initials_super_set = set()
    for i, entry in enumerate(_old_strain_entries):
        # tube_return = entry.return_tubes()
        # freeze_return = entry.return_freezes()
        user_initials_set = entry.return_user_initials()
        user_initials_super_set.update(user_initials_set)
    return user_initials_super_set


@transaction.atomic
def create_freezes(super_freeze_list, delete_old=False):
    if delete_old:
        nema_models.FreezeGroup.objects.all().delete()
        ic("Old freezes deleted.")
    
    nema_freezes = []
    iterator = tqdm(super_freeze_list, total=len(super_freeze_list),
                    desc="Building database freeze list")
    for freeze in iterator:
        nema_freeze = freeze.to_nemaFreezeGroup()
        nema_freezes.append(nema_freeze)
    ic("Freeze Groups Done!")
    return nema_freezes


@transaction.atomic
def create_tubes(super_tube_list, delete_old=False):
    if delete_old:
        nema_models.Tube.objects.all().delete()
        ic("Old tubes deleted.")
    
    nema_tubes = []
    iterator = tqdm(super_tube_list, total=len(super_tube_list),
                    desc="Building database tube list")
    for tube in iterator:
        nema_tube = tube.to_nemaTube()
        nema_tubes.append(nema_tube)
    ic("Tubes Done!")
    return nema_tubes


def create_freezes_and_tubes(_old_strain_entries, delete_old=True):
    super_tube_list = []
    super_freeze_list = []
    
    iterator = tqdm(enumerate(_old_strain_entries), total=len(_old_strain_entries),
                    desc="Building database freeze and tube list")
    for i, entry in iterator:
        results = entry.to_simple_freeze_and_tube_list()
        if results is None:
            # ic(entry.wja, "No results")
            continue
        else:
            freezes, tubes = results
            freezes: List[SimpleFreeze]
            tubes: List[SimpleTube]
        if freezes is not None:
            super_freeze_list.extend(freezes)
            super_tube_list.extend(tubes)
    create_freezes(super_freeze_list, delete_old=delete_old)
    create_tubes(super_tube_list, delete_old=delete_old)


def create_users(user_initials_dict, delete_old=False, open_registration=True):
    if delete_old:
        _ = [user.delete() for user in profile_models.User.objects.all()]
        profile_models.UserProfile.objects.all().delete()
        profile_models.UserInitials.objects.all().delete()
        ic("Old users deleted.")
    simple_user_list = build_simple_user_list(user_initials_dict)
    user_profiles_list = []
    
    iterator = tqdm(simple_user_list, total=len(simple_user_list),
                    desc="Building database user list")
    for simple_user in iterator:
        user_profiles_list.append(simple_user.to_UserProfile())
    ic(profile_models.UserProfile.objects.all().count(),
       "Users Done!")
    profile_models.OpenRegistration.objects.all().delete()
    profile_models.OpenRegistration.objects.create(is_open=open_registration)
    return user_profiles_list


@transaction.atomic
def thaw_used_tubes(_old_strain_entries: List[OldStrainEntry], reset_all=False):
    if reset_all:
        nema_models.Tube.objects.all().update(thawed=False,
                                              thaw_requester=None,
                                              date_thawed=None,
                                              )
        ic("All tubes reset to unthawed")
    
    iterator = tqdm(_old_strain_entries, total=len(_old_strain_entries),
                    desc="Thawing used tubes")
    for old_strain in iterator:
        old_strain.parse_thaws()


if __name__ == '__main__':
    # Ideally we should be able to run this from a brand-new database and have it build everything!!

    # This is the actual load step. The OldStrainEntry class does all the parsing and cleaning
    
    json_db = load_old_db()
    iterator = tqdm(json_db, total=len(json_db),
                    desc="Parsing JSON database")
    old_strain_entries = []
    for entry in iterator:
        old_strain_entries.append(OldStrainEntry(entry))

    # Each of the following steps should be skip-able for databases that are already built:

    create_users(USER_INITIALS_DICT,
                 delete_old=True)

    create_boxes(delete_old=True)

    create_strains(old_strain_entries,
                   delete_old=True)

    create_freezes_and_tubes(old_strain_entries,
                             delete_old=True)

    thaw_used_tubes(old_strain_entries,
                    reset_all=True)

    ic("Done!")
