"""
parser module to work with given train line and journey id
"""
from datetime import datetime
from os import path
from pathlib import Path
from xml.etree import ElementTree as ET

from library.train_schedule_parser import Train

package_root_dir = path.dirname(Path(__file__).parent)


def parse_date_time(date_time_str, get_date=False, get_time=False):
    """
    Function to get datetime corresponding to a date_time_string in one of the formats emitted by date.isoformat() and
    datetime.isoformat()
    :param get_time:
    :param get_date:
    :param date_time_str: string input format -> 2020-07-22T07:59:59.999000
    :return: datetime format -> 2020-07-22 07:59:59.999000 as <class 'datetime.datetime'>
    """
    date_time = datetime.fromisoformat(date_time_str)
    if get_date and (not get_time):
        return date_time.date()
    elif get_time and (not get_date):
        return date_time.time()
    else:
        return date_time


def get_spurplan_betriebsstellen():
    """
    Function to get Spurplanbetriebsstellen tag from Spurplanbetriebsstellen_ZDBU-ZDW.xml
    :return: type ElementTree.Element
    """
    spurplan_betriebsstelle_path = path.join(package_root_dir, Path(
        'resources/betriebsstellen/Spurplanbetriebsstellen_ZDBU-ZDW.xml'))
    root = ET.parse(spurplan_betriebsstelle_path).getroot()
    spurplan_betriebsstelle = root.find('Spurplanbetriebsstellen')
    return spurplan_betriebsstelle


def get_departure_time(train_line, train_journey_id):
    """
    Function to return dict type with link id (counter) as key and departure time (min_abfahrt) of train as value from
    given train
    :param train_line: train line id
    :param train_journey_id: train journey id
    :return: link id as key and 'datetime.datetime' as value
    """
    train = Train(train_line, train_journey_id)
    train_origin = train.get_origin()
    abfahrt_in_link = {}
    for link, origin in train_origin.items():
        abfahrt = origin.find('min_abfahrt').find('abfahrtzeit')
        abfahrt_in_link[link] = parse_date_time(abfahrt.text)
    return abfahrt_in_link


def get_trajectory_records(train_line, train_journey_id):
    """
    Function to get all records within trajectory tag from schedule_esf.xml
    :param train_line:
    :param train_journey_id:
    :return: record nodes from schedule_esf.xml as list
    """
    train = Train(train_line, train_journey_id)
    train_trajectory = train.get_trajectory()
    records_list = [trajectory_nodes.find('records') for trajectory_nodes in train_trajectory.values()]
    return records_list


def get_all_verlauf_nodes(train_line, train_journey_id):
    """
    Function to return all verlauf nodes from schedule_esf.xml
    :param train_line:
    :param train_journey_id:
    :return: verlauf nodes from schedule_esf.xml as list
    """
    train = Train(train_line, train_journey_id)
    train_verlauf_links = train.get_verlauf()
    verlauf = [train_verlauf for train_verlauf in train_verlauf_links.values()]
    return verlauf


def path_generator(train_line, train_journey_id):
    """
    Function to generate a absolute path to schedule file of given train line and journey_id, working for complete
    project scope
    :param train_line:
    :param train_journey_id:
    :return: absolute path to corresponding schedule_esf.xml file
    """
    return path.join(package_root_dir, Path('resources/schedules/'), train_line, train_journey_id,
                     "schedule_esf.xml")
