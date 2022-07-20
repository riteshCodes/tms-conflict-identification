"""
Module to get all elements of trajectory of given train
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Waypoint:
    velocity: float
    timestamp: float
    kilometrage: float
    time: datetime


def is_in_boundaries(kilometrage, start, end):
    """
    Function to check if kilometrage lies in interval [start, end]
    :param kilometrage: given kilometrage at moment
    :param start: start value
    :param end: end value
    :return: true if kilometrage is in between start and end
    """
    if start is None and end is None:
        return True
    if start <= kilometrage <= end or end <= kilometrage <= start:
        return True
    else:
        return False


def get_waypoints(records, direction, initial_pos, start=None, end=None):
    """
    :param records:
    :param direction: direction of the train (either "S" or "F")
    :param initial_pos: kilometrisierung at the start of the train journey
    :param start: kilometrisierung from where to start (default: None)
    :param end: kilometrisierung where to stop (default: None)
    :return a dictonary of all the waypoints at the kilometrisierungen between start and end
    (if start is given and end is left empty -> only return waypoint right before that specific point)
    """
    geschwindigkeiten = {}

    if start is not None and end is None:
        point = None
        for record in records:
            xs = float(str.replace(record.find('Lower_xs').text, ",", "."))
            kilometrage = initial_pos + xs / 1000 if direction == "S" else initial_pos - xs / 1000
            if (direction == "S" and kilometrage > start) or (direction == "F" and kilometrage < start):
                return point
            point = Waypoint(float(str.replace(record.find('Lower_vs').text, ",", ".")),
                             float(str.replace(record.find('Lower_ts').text, ",", ".")) / 60,
                             kilometrage,
                             datetime.strptime(record.find('Lower_timestamps').text, "%Y-%m-%d %H:%M:%S.%f"))
        return point

    for record in records:
        xs = float(str.replace(record.find('Lower_xs').text, ",", "."))
        kilometrage = initial_pos + xs / 1000 if direction == "S" else initial_pos - xs / 1000
        print(record.find('Lower_timestamps').text)
        point = Waypoint(float(str.replace(record.find('Lower_vs').text, ",", ".")),
                         float(str.replace(record.find('Lower_ts').text, ",", ".")) / 60,
                         kilometrage,
                         datetime.strptime(record.find('Lower_timestamps').text, "%Y-%m-%d %H:%M:%S.%f"))
        if is_in_boundaries(kilometrage, start, end):
            geschwindigkeiten[kilometrage] = point
    return geschwindigkeiten
