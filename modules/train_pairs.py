"""
Module to extract relevant train pairs by comparing signal attributes and time of arrivals and departures.
Possible cases of trains in lines and nodes are considered.
"""
import itertools
import os
import re
import string
from os import path
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
from library.parser import parse_date_time

package_dir = Path(__file__).parent.parent
schedules_root_dir = path.join(package_dir, Path('resources/schedules'))
parsed_schedules = {}


def get_relevant_directories():
    """
    Function to search for all directories with schedule_esf.xml and to build cartesian product of all possible train
    pairs directories with element name as corresponding train id and line

    :return: list of all possible (train id line) names as tuple of two trains (any)
    """
    relevant_directories = []
    for dir_name, _, file_list in os.walk(schedules_root_dir):
        if 'schedule_esf.xml' in file_list:
            schedule_path = path.join(dir_name, Path('schedule_esf.xml'))
            characters = re.escape(string.punctuation)
            train_dir = re.sub(r'[' + characters + ']', ' ',
                               (dir_name.split('schedules')[1])[1:])  # output-format
            relevant_directories.append(train_dir)
            parsed_schedules[train_dir] = ET.parse(schedule_path).getroot()
    return relevant_directories


def get_relevant_train_pairs():
    """
    Function to return all relevant pairs of trains from given resources

    :param with_time_constraint: False if used for minimum headways
    :return: list of relevant pairs of trains with ids and lines
    """
    relevant_directories = get_relevant_directories()
    relevant_pairs = []

    for pair in itertools.combinations(relevant_directories, 2):
        if is_relevant_pair(pair[0], pair[1]):
            relevant_pairs.append(pair)

    trains_pairs = {'Relevant_Trains_Pairs': relevant_pairs}
    relevant_trains_df = pd.DataFrame(data=trains_pairs)
    output_path = path.join(package_dir, Path('output/relevant_train_pairs.csv'))
    relevant_trains_df.to_csv(output_path, index=False, sep='\t')

    return relevant_pairs


def is_relevant_pair(first_train, second_train):
    """
    Function to check if given two trains have minimum one common intersecting id, whilst checking if both trains are in
    relevant time frames. Checks both directions Direction.STEIGEND and Direction.FALLEND
    :param with_time_constraint: False if used for minimum headways
    :param first_train: Train id and line as String
    :param second_train: Train id and line as String
    :return: True if given two trains are relevant, otherwise False
    """
    for link_of_first_train in parsed_schedules[first_train]:
        first_train_element_ids = [node[0].text for node in link_of_first_train.find('Verlauf')]
        for link_of_second_train in parsed_schedules[second_train]:
            second_train_element_ids = [node[0].text for node in link_of_second_train.find('Verlauf')]
            common_ids = set.intersection(set(first_train_element_ids), set(second_train_element_ids))
            if len(common_ids) != 0:
                first_train_departure = parse_date_time(
                    link_of_first_train.find('Origin')[0].find('abfahrtzeit').text)
                first_train_arrival = parse_date_time(
                    link_of_first_train.find('Destination')[2].find('ankunftzeit').text)
                second_train_departure = parse_date_time(
                    link_of_second_train.find('Origin')[0].find('abfahrtzeit').text)
                second_train_arrival = parse_date_time(
                    link_of_second_train.find('Destination')[2].find('ankunftzeit').text)
                if first_train_departure < second_train_departure:  # first train departs first
                    if second_train_departure < first_train_arrival:
                        # second train departs before first train arrives to destination if condition holds true
                        # second train departs after first train arrives to destination if condition holds false
                        return True
                        # else second train departs after first train arrives to destination

                else:  # second train departs first
                    if first_train_departure < second_train_arrival:
                        # first train departures before second train arrives to destination if condition holds true
                        # first train departures after second train arrives to destination if condition holds false
                        return True
                        # else first train departs after second train arrives to destination

    return False


if __name__ == '__main__':
    print(get_relevant_directories())
