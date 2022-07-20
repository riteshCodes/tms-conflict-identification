"""
Library module, that parses complete schedule_esf.xml of each train as Train object and the tags used in the file can be
called using functions of Train object
"""
from os import path
from pathlib import Path
from xml.etree import ElementTree as ET

from library.model_trains import get_train_total_length


class Train:
    root_dir = path.dirname(Path(__file__).parent)

    def __init__(self, train_line, train_journey_id):
        self.train_line = train_line
        self.train_journey_id = train_journey_id
        schedule_path = path.join(Train.root_dir,
                                  Path('resources/schedules/', train_line, train_journey_id, 'schedule_esf.xml'))
        self.root_schedule = ET.parse(schedule_path).getroot()
        self.train_length = get_train_total_length(train_line)

    def get_origin(self):
        link_count = 0
        origin = {}
        for link in self.root_schedule:  # for multiple links
            link_count += 1
            origin[link_count] = link.find('Origin')
        return origin

    def get_trajectory(self):
        link_count = 0
        trajectory = {}
        for link in self.root_schedule:  # for multiple links
            link_count += 1
            trajectory[link_count] = link.find('trajectory')
        return trajectory

    def get_betriebsstellenfahrwege(self):
        link_count = 0
        betriebsstellenfahrwege = {}
        for link in self.root_schedule:  # for multiple links
            link_count += 1
            betriebsstellenfahrwege[link_count] = link.find('Betriebsstellenfahrwege')
        return betriebsstellenfahrwege

    def get_verlauf(self):
        link_count = 0
        verlauf = {}
        for link in self.root_schedule:  # for multiple links
            link_count += 1
            verlauf[link_count] = link.find('Verlauf')
        return verlauf

    def get_destination(self):
        link_count = 0
        destination = {}
        for link in self.root_schedule:  # for multiple links
            link_count += 1
            destination[link_count] = link.find('Destination')
        return destination


# examples of creating train objects and getting their values from XML files
# supports efficient use of XML files by parsing it only once and using only train object
if __name__ == '__main__':
    test_train_object = Train(train_line='RE50', train_journey_id='2512')
    print(test_train_object.get_origin())
    print(test_train_object.get_verlauf())
    print(test_train_object.get_betriebsstellenfahrwege())
    print(test_train_object.get_trajectory())
    print(test_train_object.get_destination())
    print(test_train_object.root_schedule)
