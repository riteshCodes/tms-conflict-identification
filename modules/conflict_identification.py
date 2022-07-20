"""
Module for conflict identification of given two trains.
"""
from datetime import timedelta
from os import path
from pathlib import Path

import pandas as pd
from library.parser import get_departure_time

from modules.train_pairs import get_relevant_train_pairs
from modules.occupancy_times import get_times

PACKAGE_DIR = path.dirname(Path(__file__).parent)
CONFLICTS_PATH = path.join(PACKAGE_DIR, Path('output/conflicts.csv'))

PRINT_OUTPUTS = True


def identify_conflicts(train_pairs):
    """
    Identifies conflicts in relevant train pairs and writes the output to a csv.
    :param train_pairs: relevant train pairs to check for conflicts.
    """
    conflicts = {
        'train_pair': [],
        'start_abschnitt_id': [],
        'end_abschnitt_id': [],
        'start_abschnitt_pos': [],
        'end_abschnitt_pos': [],
        'delta': []
    }

    for pair in train_pairs:
        # check for conflicts for train pair
        conflict_blocks = get_conflict_blocks(pair[0], pair[1])
        for i in range(len(conflict_blocks['start_abschnitt_id'])):
            conflicts['train_pair'].append(pair)
            conflicts['start_abschnitt_id'].append(conflict_blocks['start_abschnitt_id'][i])
            conflicts['end_abschnitt_id'].append(conflict_blocks['start_abschnitt_id'][i])
            conflicts['start_abschnitt_pos'].append(conflict_blocks['start_abschnitt_pos'][i])
            conflicts['end_abschnitt_pos'].append(conflict_blocks['end_abschnitt_pos'][i])
            conflicts['delta'].append(conflict_blocks['delta'][i])

    conflicts_df = pd.DataFrame(data=conflicts)

    if PRINT_OUTPUTS:
        header = 'Conflict report\n\n' + 'Identified ' + str(len(conflicts_df)) + ' conflicts:\n'
        print(header, conflicts_df.to_string())

    # write output to csv
    conflicts_df.to_csv(CONFLICTS_PATH, index=True, sep='\t')


def get_conflict_blocks(first_train, second_train):
    """
    Checks if the given two trains have any conflicts in blocks on their journey.
    :param first_train: First train as string with format '<line> <journey_id>'
    :param second_train: Second train as string with format '<line> <journey_id>'
    :return: list of conflict block ids
    """
    first_blocks = calculate_block_entry_times(first_train)
    second_blocks = calculate_block_entry_times(second_train)

    conflict_blocks = {
        'start_abschnitt_id': [],
        'end_abschnitt_id': [],
        'start_abschnitt_pos': [],
        'end_abschnitt_pos': [],
        'delta': [],
    }

    for i in range(len(first_blocks['start_abschnitt_id'])):
        for j in range(len(second_blocks['start_abschnitt_id'])):
            if first_blocks['start_abschnitt_id'][i] == second_blocks['start_abschnitt_id'][j] \
                    and first_blocks['end_abschnitt_id'][i] == second_blocks['end_abschnitt_id'][j]:
                if first_blocks['start_time'][i] < second_blocks['start_time'][j]:
                    if second_blocks['start_time'][j] < first_blocks['end_time'][i]:
                        conflict_blocks['start_abschnitt_id'].append(first_blocks['start_abschnitt_id'][i])
                        conflict_blocks['end_abschnitt_id'].append(first_blocks['end_abschnitt_id'][i])
                        conflict_blocks['start_abschnitt_pos'].append(first_blocks['start_abschnitt_pos'][i])
                        conflict_blocks['end_abschnitt_pos'].append(first_blocks['end_abschnitt_pos'][i])
                        conflict_blocks['delta'].append(second_blocks['start_time'][j] - first_blocks['start_time'][i])
                else:
                    if first_blocks['start_time'][i] < second_blocks['end_time'][j]:
                        conflict_blocks['start_abschnitt_id'].append(first_blocks['start_abschnitt_id'][i])
                        conflict_blocks['end_abschnitt_id'].append(first_blocks['end_abschnitt_id'][i])
                        conflict_blocks['start_abschnitt_pos'].append(first_blocks['start_abschnitt_pos'][i])
                        conflict_blocks['end_abschnitt_pos'].append(first_blocks['end_abschnitt_pos'][i])
                        conflict_blocks['delta'].append(first_blocks['start_time'][i] - second_blocks['start_time'][j])
    return conflict_blocks


def calculate_block_entry_times(train):
    """
    Calculates the entry time of the train for every section of a block on the trains journey depending on the
    departure time of the train.
    :param train: Train as string with format '<line> <journey_id>'
    :return: A dictionary with the section id, position and entry and exit times as datetime
    """
    block_entry_times = {
        'start_abschnitt_id': [],
        'end_abschnitt_id': [],
        'start_abschnitt_pos': [],
        'end_abschnitt_pos': [],
        'start_time': [],
        'end_time': []
    }

    (line, journey_id) = train.split()
    departure_times = get_departure_time(line, journey_id)

    for link_id in departure_times:
        _, vorbelegungszeiten, driving_times, nachbelegungszeiten, blocks = \
            get_times(train, link_id=link_id - 1)

        entry_time = departure_times[link_id]

        for i, block in enumerate(blocks):
            for j, abschnitt in enumerate(block.fahrstrassenabschnitte):
                # if section is the last section of the last block in link
                if i == len(blocks) - 1 and j == len(block.fahrstrassenabschnitte) - 1 \
                        and link_id < len(departure_times):
                    # exit time is departure time of the next link
                    exit_time = departure_times[link_id + 1] + timedelta(minutes=sum(driving_times[i][:j + 1]))
                else:
                    # calculate exit time of the section
                    exit_time = entry_time + timedelta(minutes=sum(driving_times[i][:j + 1]))

                # add entry and exit time to dict
                block_entry_times['start_abschnitt_id'].append(abschnitt.start_abschnitt_id)
                block_entry_times['end_abschnitt_id'].append(abschnitt.end_abschnitt_id)
                block_entry_times['start_abschnitt_pos'].append(abschnitt.start_abschnitt_pos)
                block_entry_times['end_abschnitt_pos'].append(abschnitt.end_abschnitt_pos)
                block_entry_times['start_time'].append(entry_time - timedelta(minutes=vorbelegungszeiten[i]))
                block_entry_times['end_time'].append(exit_time + timedelta(minutes=nachbelegungszeiten[i][j]))

            # entry time of the next block is exit time of the last block
            entry_time = exit_time

    return block_entry_times


if __name__ == "__main__":
    relevant_pairs = get_relevant_train_pairs()
    identify_conflicts(relevant_pairs)
    # for identifying conflicts between any two given trains
    # relevant_pairs type: tuples of list, where a tuple consists of a pair of trains with their journey ids
    # identify_conflicts([('IC100 3103', 'RB40 2413')])
