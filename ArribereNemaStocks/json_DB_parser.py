"""
json_DB_parser.py
Marcus Viscardi,    November 20, 2023

This is a script to parse the WormStocks database json file into a more usable format!
"""

import json
from pathlib import Path
from dateutil import parser
import re
from icecream import ic
from datetime import datetime as dt
from datetime import timedelta as dt_delta

from .models import Strain, Tube, Box, FreezeGroup


def parse_date(date_str, return_format="%Y-%m-%d", return_datetime_object=False):
    try:
        # Use dateutil.parser.parse to automatically detect and parse various date formats
        parsed_date = parser.parse(date_str)
        return_value = parsed_date.strftime(return_format)
        if return_datetime_object:
            return_value = parsed_date
    except ValueError:
        print(f"Could not parse date: {date_str}")
        return_value = None
    return return_value


def timestamp_ic_prefix():
    return dt.now().strftime("%I:%M:%S %p | ")
ic.configureOutput(prefix=timestamp_ic_prefix,
                   includeContext=True)


database_json_path = '/home/marcus/PycharmProjects/' \
                     'arribereWormDatabase/' \
                     '231114_OFFICIAL_WORMSTOCKS_databaseDownload.json'
database_json_Path = Path(database_json_path)
ic(database_json_Path)

with open(database_json_path, 'r') as f:
    database = json.load(f)  # The database is a list of dictionaries!


def parse_strain_2(target_strain: str):
    """
    Going to try and make this better! Gotta flex the classes!
    """
    ic.disable()
    # First let's find the target strain!
    strain_json = None
    for strain_dict in database:
        # print(strain_dict['WJA_NUMBER'])
        if strain_dict['WJA_NUMBER'] == target_strain:
            strain_json = strain_dict
            ic(f"Target strain ({target_strain}) found!")
            break
    if not strain_json:
        raise ValueError(f"ERROR: Target strain ({target_strain}) not found!")
    
    # Now let's parse the strain! Mainly focusing on the splitable columns!
    splitable_columns = ['DATE_FROZEN', 'TUBE_NO', 'TANK_NO', 'RACK_NO', 'RACK_BOX_NO', 'DATE_THAWED',
                         'NO_OF_TUBES_THAWED', 'COMMENTS', 'CAP_COLOR']

    split_column_dict = {}
    for column in splitable_columns:
        try:
            split_col = strain_json[column].split('|')
        except AttributeError:
            split_col = []
        split_column_dict[column] = [entry for entry in split_col if entry]

    working_strain = Strain.objects.create(wja=target_strain[-4:], description=strain_json['DESCRIPTION'])
    ic(working_strain)
    
    # Next we should parse the freeze dates and cap colors!
    freeze_date_set = set()
    for freeze_date in split_column_dict['DATE_FROZEN']:
        if freeze_date:
            freeze_date_set.add(freeze_date)
    if len(freeze_date_set) != len(split_column_dict['CAP_COLOR']):  # Handle edge cases with missmatched numbers
        if len(freeze_date_set) == len(split_column_dict['CAP_COLOR']) - 1:
            freeze_warning = f"WARNING: Freeze dates and cap colors do not match for strain {target_strain}! " \
                             f"You have {len(freeze_date_set)} freeze dates and " \
                             f"{len(split_column_dict['CAP_COLOR'])} cap colors! " \
                             f"(This is probably because someone entered a cap color when " \
                             f"they initially produced the strain, " \
                             f"but did not produce a freeze!)"
            freeze_warning_comment = f"\n\tTo amend this, I will remove the first cap color!" \
                                     f"\n\tOld cap colors: {split_column_dict['CAP_COLOR']}" \
                                     f"\n\tNew cap colors: {split_column_dict['CAP_COLOR'][1:]}"
            ic(freeze_warning, freeze_warning_comment)
            split_column_dict['CAP_COLOR'] = split_column_dict['CAP_COLOR'][1:]
        elif len(freeze_date_set) < len(split_column_dict['CAP_COLOR']):
            # This is a case where multiple storages were attempted before a freeze was made!
            # This error catch is directly due to WJA4014 by AC in Jan 2020!
            freeze_warning = f"WARNING: Freeze dates and cap colors do not match for strain {target_strain}! " \
                             f"You have {len(freeze_date_set)} freeze dates and " \
                             f"{len(split_column_dict['CAP_COLOR'])} cap colors! " \
                             f"(This is probably because someone entered a cap color when " \
                             f"they initially produced the strain, " \
                             f"but did not produce a freeze! - And this happened twice?!)"
            freeze_warning_comment = f"\n\tTo amend this, I will remove the first 2 colors!" \
                                     f"\n\tOld cap colors: {split_column_dict['CAP_COLOR']}" \
                                     f"\n\tNew cap colors: {split_column_dict['CAP_COLOR'][2:]}"
            ic(freeze_warning, freeze_warning_comment)
            split_column_dict['CAP_COLOR'] = split_column_dict['CAP_COLOR'][2:]
        else:
            raise ValueError(f"ERROR: Freeze dates and cap colors do not match for strain {target_strain}! "
                             f"You have {len(freeze_date_set)} freeze dates "
                             f"and {len(split_column_dict['CAP_COLOR'])} cap colors!")

    else:
        ic(f"Freeze dates and cap colors match for strain {target_strain}! "
              f"You have {len(freeze_date_set)} freeze dates and {len(split_column_dict['CAP_COLOR'])} cap colors!")

    freeze_date_to_color_dict = {}
    formatted_freeze_date_color_dict = {}
    freeze_dict = {}
    for i, freeze_date in enumerate(freeze_date_set):
        freeze_date_to_color_dict[freeze_date] = split_column_dict['CAP_COLOR'][i]
        formatted_freeze_date_color_dict[parse_date(freeze_date)] = split_column_dict['CAP_COLOR'][i]
        if parse_date(freeze_date) in freeze_dict:
            raise KeyError(f"There are two freeze events with matching dates (both {parse_date(freeze_date)})."
                           f"The code cannot currently handle this!! "
                           f"Talk to Marcus about adding times to dates for storages, comments, thaws, etc.")
        new_freeze = FreezeGroup.objects.create(strain=working_strain,
                                                stored=True,
                                                date_created=parse_date(freeze_date,
                                                                        return_datetime_object=True))
        freeze_dict[parse_date(freeze_date)] = new_freeze
        # working_strain.freeze_group.add(freeze_dict[parse_date(freeze_date)])
        working_strain.freezegroup_set.add(freeze_dict[parse_date(freeze_date)])
    ic(freeze_dict)
    
    # Now let's parse the freeze comments!
    # I want to try and parse out freeze comments from the comments column!
    # TODO: Let's add some check to not connect comments to freezes that are outside of 1 month!
    freeze_comment_dict = {}
    non_freeze_comments = []
    for i, comment in enumerate(split_column_dict['COMMENTS']):
        if comment:
            regex_pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4})(.+)?'
            match = re.search(regex_pattern, comment)
            if match:
                date, freeze_comment = match.groups()
                if parse_date(date) in freeze_comment_dict:
                    raise KeyError(f"MULTIPLE FREEZE COMMENT ERROR: "
                                   f"There are two freeze comments with matching dates (both {parse_date(date)}) "
                                   f"for strain {target_strain}. "
                                   f"The code cannot currently handle this!! "
                                   f"Talk to Marcus about adding times to dates for storages, comments, thaws, etc.")
                freeze_comment_dict[parse_date(date)] = freeze_comment
            else:
                non_freeze_comments.append(comment)
    ic(non_freeze_comments)
    ic(freeze_comment_dict)
    ic(formatted_freeze_date_color_dict)

    # Parse freeze comments, then (for each) calculate all the delta_times from the freezes
    freeze_comment_delta_dict = {}  # Each key will be parsedDT, the values will be lists with:
    #                                    [[freeze_comment_initials, freeze_comment],
    #                                    {freeze_date: [delta_time, freeze_group_object}]
    for freeze_comment_date, freeze_comment in freeze_comment_dict.items():
        freeze_comment_dt = parse_date(freeze_comment_date, return_datetime_object=True)
        for freeze_date, freeze_group_object in freeze_dict.items():
            freeze_dt = parse_date(freeze_date, return_datetime_object=True)
            delta = freeze_comment_dt - freeze_dt
            initial_pattern = r'^([A-Z]{2,3})(.+)'
            match = re.search(initial_pattern, freeze_comment.strip())
            if match:
                tester_initials = match.groups()[0]
                tester_comments = match.groups()[1].strip()
            else:
                tester_initials = 'N/A'
                tester_comments = freeze_comment.strip()
            if parse_date(freeze_comment_date) not in freeze_comment_delta_dict:
                freeze_comment_delta_dict[parse_date(freeze_comment_date)] = [[tester_initials, tester_comments],
                                                                              [(delta, freeze_group_object)]]
            else:
                freeze_comment_delta_dict[parse_date(freeze_comment_date)][1].append((delta, freeze_group_object))
    
    # Now we can pick out the nearest delta_time from the list!
    close_match_wiggle_room_days = 10  # This will be used to find a second close match for negative delta times
    #                                    (negative delta times would indicate a test thaw happening BEFORE a freeze)
    too_long_delta_time_days = 30  # This will be used to check for errors!
    for freeze_comment_date, [[tester_initials, tester_comments], delta_list] in freeze_comment_delta_dict.items():
        closest_delta, closest_freeze = min(delta_list, key=lambda x: abs(x[0]))
        second_freeze_used = False
        if closest_delta < dt.now() - dt.now() and len(delta_list) > 1:  # check for negative delta time!
            filtered_delta_list = [(delta, freeze) for delta, freeze in delta_list if delta is not closest_delta]
            second_closest_delta, second_closest_freeze = min(filtered_delta_list, key=lambda x: abs(x[0]))
            if second_closest_delta < abs(closest_delta) + dt_delta(days=close_match_wiggle_room_days):
                # The second date is likely the real deal!
                # This is becuase it is positive (so it was tested after being frozen)
                # And it's still pretty close (using the wiggle room of _delta_wiggle_room
                closest_delta, closest_freeze = second_closest_delta, second_closest_freeze
                second_freeze_used = True
        if closest_delta > dt_delta(days=too_long_delta_time_days):
            ic.enable()
            ic(working_strain,
               freeze_comment_date,
               tester_initials,
               tester_comments,
               closest_freeze,
               closest_delta,
               second_freeze_used)
            ic.disable()
            raise NotImplementedError(f"FREEZE COMMENT GAP ERROR: "
                                      f"The closest delta time is greater than "
                                      f"{too_long_delta_time_days} days for strain {target_strain}!")
        if closest_freeze.tester_initials or closest_freeze.tester_comments:
            raise KeyError(f"OVERWRITING FREEZE COMMENT ERROR: "
                           f"We already have a freeze comment for freeze {closest_freeze} "
                           f"\nStrain {target_strain} likely has something fishy going on!")
        closest_freeze.tester_initials = tester_initials
        closest_freeze.tester_comments = tester_comments
        closest_freeze.save()

    # Now let's parse the tubes!
    # There is a slight issue with some VERY early strains that have two freezes but only one date frozen!
    # We are going to ASSUME that those are the same freeze date!
    if len(split_column_dict['DATE_FROZEN']) + 1 == len(split_column_dict['TUBE_NO']):
        if len(split_column_dict['TUBE_NO']) > 2:
            raise ValueError(f"GAP IN FREEZE RECORD ERROR: "
                             f"There are more tube entries than freeze events for strain {target_strain}! "
                             f"Specifically, there are {len(split_column_dict['TUBE_NO'])} tubes and "
                             f"{len(split_column_dict['DATE_FROZEN'])} freeze events!")
        ic.enable()
        freeze_date_count_warning = f"WARNING: There are more tube entries than " \
                                    f"freeze events for strain {target_strain}! We " \
                                    f"are going to make the ASSUMPTION that the first " \
                                    f"freeze date is the same for the second!"
        ic(freeze_date_count_warning,
           strain_json)
        split_column_dict['DATE_FROZEN'].append(split_column_dict['DATE_FROZEN'][0])
        ic.disable()
    if len(split_column_dict['DATE_FROZEN']) != len(split_column_dict['TUBE_NO']):
        if len(split_column_dict['TUBE_NO']) > 2:
            raise ValueError(f"MISSING FREEZE DATE ERROR: "
                             f"There are more tube entries than freeze events for strain {target_strain}! "
                             f"Specifically, there are {len(split_column_dict['TUBE_NO'])} tubes and "
                             f"{len(split_column_dict['DATE_FROZEN'])} freeze events!")
        raise ValueError(f"FREEZE EVENT MISMATCH ERROR: "
                         f"There is a mismatched between tube entries than freeze events for "
                         f"strain {target_strain}! Specifically, there are "
                         f"{len(split_column_dict['TUBE_NO'])} tubes and "
                         f"{len(split_column_dict['DATE_FROZEN'])} freeze events!")
    tube_dict = {}
    for i, tube_number in enumerate(split_column_dict['TUBE_NO']):
        if tube_number:
            for tube in range(int(tube_number)):
                save_column_targets = ['DATE_FROZEN', 'RACK_BOX_NO', 'RACK_NO', 'TANK_NO']
                save_column_values = []
                for column_target in save_column_targets:
                    try:
                        save_column_values.append(split_column_dict[column_target][i])
                    except IndexError as e:
                        ic.enable()
                        ic(split_column_dict['TUBE_NO'], split_column_dict[column_target], i)
                        raise IndexError(f"ERROR: There are more tubes than freeze events for strain {target_strain}!"
                                         f"More specifically, there are more tubes than {column_target} entries!")
                save_column_values.append(freeze_date_to_color_dict[split_column_dict['DATE_FROZEN'][i]])
                tube_dict[f"{i} ({tube + 1}/{int(tube_number)})"] = save_column_values

    freeze_set_dict = {}
    for freeze_date in split_column_dict['DATE_FROZEN']:
        if freeze_date:
            freeze_date = parse_date(freeze_date)
            if freeze_date not in freeze_set_dict:
                freeze_set_dict[freeze_date] = 1
            else:
                freeze_set_dict[freeze_date] += 1
    # print(freeze_set_dict)

    freeze_set_tubes_dict = {}
    box_dict = {}
    for set_num, (freeze_date, num_freezes) in enumerate(freeze_set_dict.items()):
        for key, (date, rack_box, rack, tank, cap_color) in tube_dict.items():
            if parse_date(date) == freeze_date:
                if set_num not in freeze_set_tubes_dict:
                    freeze_set_tubes_dict[set_num] = []
                box_identifier = f"{tank} {int(rack)}-{int(rack_box[-1])}"
                if box_identifier not in box_dict:
                    new_box = Box.objects.create(dewar=int(tank[-1]),
                                                 rack=int(rack),
                                                 box=int(rack_box[-1]))
                    box_dict[box_identifier] = new_box
                new_tube = Tube.objects.create(cap_color=cap_color,
                                               date_created=parse_date(date, return_datetime_object=True),
                                               strain=working_strain,
                                               freeze_group=freeze_dict[freeze_date],
                                               box=box_dict[box_identifier])
                # freeze_dict[freeze_date].tubes.append(new_tube)
                # freeze_dict[freeze_date].save()
                freeze_dict[freeze_date].tube_set.add(new_tube)
                freeze_dict[freeze_date].save()
                working_strain.tube_set.add(freeze_dict[freeze_date].tube_set.last())
                working_strain.save()
                
                for freeze_group in working_strain.freezegroup_set.all():
                    if freeze_group.id == freeze_dict[freeze_date].id:
                        # freeze_group.tube_set.append(freeze_dict[freeze_date].tube_set.last())
                        freeze_group.tube_set.add(freeze_dict[freeze_date].tube_set.last())
                        freeze_group.save()
    for thaw, num_tube_string in zip(split_column_dict['DATE_THAWED'], split_column_dict['NO_OF_TUBES_THAWED']):
        if thaw:
            thaw_date, thaw_requester = thaw.split(' ', 1)
            tube_rack_box_pattern = r'(\d+)\((\w{2}\d+) (\d+-\d+)\)'
            match = re.search(tube_rack_box_pattern, num_tube_string)
            if match:
                num_tubes, tank, rack_box = match.groups()
                rack, box = rack_box.split('-')
            else:
                ic(f"WARNING: Could not parse num_tube_string: {num_tube_string}")
                continue
            ic(thaw_date, thaw_requester, num_tube_string, tank, rack_box)
            for thaw_tube_num in range(int(num_tubes)):
                for freeze_group in working_strain.freezegroup_set.all():
                    for tube in freeze_group.tube_set.all():
                        if tube.box.dewar == int(tank[-1]) and \
                                tube.box.rack == int(rack) and \
                                tube.box.box == int(box):
                            tube.date_thawed = parse_date(thaw_date, return_datetime_object=True)
                            tube.thawed = True
                            tube.thaw_requester = thaw_requester
                            tube.save()
                            ic("thawed", tube)
                            break
    ic.enable()
    ic(working_strain)
    # ic(working_strain.freeze_groups)
    # ic(working_strain.tubes)
    return working_strain


def main():
    Strain.objects.all().delete()
    Tube.objects.all().delete()
    Box.objects.all().delete()
    FreezeGroup.objects.all().delete()
    
    all_strains_list = [strain['WJA_NUMBER'] for strain in database]
    all_strains_list.remove('WJA 0000')
    stain_raw_list = [23, 27, 6001, 6002, 5107, 668, 670, 1086, 1004, 6004, 6014]
    strain_list = [f"WJA {strain:0>4}" for strain in stain_raw_list]
    # TARGET_STRAIN = strain_list[-1]
    # parse_strain_2(TARGET_STRAIN)
    success_count = 0
    fail_count = 0
    fail_dict = {}  # This will store the strain and the error
    custom_fail_msg_list = []
    for strain in all_strains_list:
        try:
            strain_obj = parse_strain_2(strain)
            success_count += 1
        except Exception as e:
            ic.enable()
            ic(strain, e)
            ic.disable()
            fail_dict[strain] = e
            fail_count += 1
            custom_fail_msg_list.append(e.args[0].split(':')[0])
    ic(fail_dict)
    from collections import Counter
    ic(Counter(custom_fail_msg_list))
    ic(success_count, fail_count)

if __name__ == '__main__':
    main()
    
    # STRAIN 0000 has something weird going on with parsing the tube number
    # STRAIN 6014 has an issue due to multiple freeze comments with the same date
