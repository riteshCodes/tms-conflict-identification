"""
occupancy time calculations

"""

from os import makedirs, path
from pathlib import Path
from xml.etree import ElementTree as ET

import library.writer
from elements.constants import FAHRSTRASSEN_BILDEZEIT, SIGNAL_SICHTZEIT
from elements.d_weg import get_d_weg
from elements.trajectory import get_waypoints
from library.model_trains import get_train_total_length
from library.parser import get_all_verlauf_nodes, get_trajectory_records
from library.utils import determine_direction, get_absolute_kilometrage

from modules.block_identification import (Block, Fahrstrassenabschnitt,
                                          get_blocks)
from modules.train_pairs import get_relevant_directories

PACKAGE_DIR = path.dirname(Path(__file__).parent)
SCHEDULES_ROOT_DIR = path.join(PACKAGE_DIR, Path('resources/schedules'))
OCCUPANCY_TIMES_DIR = path.join(PACKAGE_DIR, Path('output/occupancy_times'))

PRINT_OUTPUTS = False


def calculate_vorbelegungszeit(records, vorsignal_position, hauptsignal_position, initial_position, direction):
    """
    Function to calculate the vorbelegungszeit in minutes
    :param vorsignal_position:
    :param records:
    :param vorsignal_pos, hauptsignal_position: The positions between we want to calculate the annaeherungsfahrzeit
    :param initial_position: The Kilometrierung of the first element of the schedule
    :param direction: The direction the train is driving along ("F" or "S")
    :return vorbelegungszeit in minutes
    :return 0 if no Vorsignal exists for this block
    """
    vorbelegungszeit = round((FAHRSTRASSEN_BILDEZEIT + SIGNAL_SICHTZEIT), 4)
    if vorsignal_position is None:
        if PRINT_OUTPUTS:
            print("Kein VS vorhanden")
    else:
        start_ts = get_waypoints(records, direction, initial_position, vorsignal_position).timestamp
        end_ts = get_waypoints(records, direction, initial_position, hauptsignal_position).timestamp
        annaeherungsfahrzeit = end_ts - start_ts
        vorbelegungszeit = round((FAHRSTRASSEN_BILDEZEIT + SIGNAL_SICHTZEIT + annaeherungsfahrzeit), 4)
    return vorbelegungszeit


def calculate_driving_time_block(records, fahrstrassenabschnitte, start_hs_pos, end_hs_pos, initial_position,
                                 direction):
    """
    Function to calculate the time to drive through a block in minutes
    :param records:
    :param start_hs_pos:
    :param fahrstrassenabschnitte: a list of fahrstrassenabschnitt of Dataclass Fahrsstrassenabschnitt
    :param start_hs_pos, end_hs_pos: The positions of the hauptsignale between we want to calculate the driving time
    :param initial_position: The Kilometrierung of the first element of the schedule
    :param direction: The direction the train is driving along ("F" or "S")
    :return driving time for whole block; list containing all driving times between elements
    (elements depend on calculate_fstr_abschnitte is set)
    """
    fahrzeiten = []

    try:
        start_ts = get_waypoints(records, direction, initial_position, start_hs_pos).timestamp
    except:
        start_ts = get_waypoints(records, direction, initial_position,
                                 initial_position).timestamp
    end_ts = get_waypoints(records, direction, initial_position, end_hs_pos).timestamp
    b_driving_time = round((end_ts - start_ts), 4)

    for fahrstrassenabschnitt in fahrstrassenabschnitte:
        try:
            start_ts = get_waypoints(records, direction, initial_position,
                                     fahrstrassenabschnitt.start_abschnitt_pos).timestamp
        except:
            start_ts = get_waypoints(records, direction, initial_position,
                                     initial_position).timestamp
        end_ts = get_waypoints(records, direction, initial_position,
                               fahrstrassenabschnitt.end_abschnitt_pos).timestamp
        driving_time = round((end_ts - start_ts), 4)
        fahrzeiten.append(driving_time)

    if PRINT_OUTPUTS:
        print("LIST DRIVING TIMES -> ", b_driving_time, fahrzeiten)
    return b_driving_time, fahrzeiten


def calculate_nachbelegungszeit(records, fahrstrassenabschnitte, train_total_length, start_hs_pos, end_hs_pos,
                                sig_zugschluss_pos,
                                passed_aufloesezeit, initial_position,
                                direction):
    """
    Function to calculate the Nachbelegungszeit in minutes
    :param end_hs_pos:
    :param records:
    :param fahrstrassenabschnitte: a list of fahrstrassenabschnitt of Dataclass Fahrsstrassenabschnitt
    :param train_total_length: the total length of the current train in m
    :param start_hs_pos: The position of the start hauptsignal of the block to calculate the d_weg
    :param end_hs_pos, sig_zugschluss_pos: The positions between we want to calculate the Räumfahrzeit
    :param passed_aufloesezeit: The Auflloesezeit of the Signalzugschlussstelle
    :param initial_position: The Kilometrierung of the first element of the schedule
    :param direction: The direction the train is driving along ("F" or "S")
    :param calculate_fstr_abschnitte: Decides wether the whole block is considered or
    each fahrstrassenabschnitt is considered individually
    :return Nachbelegungszeit in minutes of last abschnitt, List of all Nachbelegungszeiten of each Blockabschnitt
    """
    # With no signal zugschlussstelle_id we have to calculate the d_weg manually
    nachbelegungszeiten = []
    last_fstr_abschnitt_pos = start_hs_pos
    aufloesezeit = 3 if sig_zugschluss_pos is None else passed_aufloesezeit

    for i in range(0, len(fahrstrassenabschnitte) - 1):
        if i != len(fahrstrassenabschnitte) - 1:
            try:
                speed_at_entrance = get_waypoints(records, direction, initial_position,
                                                  fahrstrassenabschnitte[i].start_abschnitt_pos).velocity
                d_weg = get_d_weg(speed_at_entrance)
                end_pos = fahrstrassenabschnitte[i].end_abschnitt_pos + d_weg / 1000 if direction == "S" else \
                    fahrstrassenabschnitte[i].end_abschnitt_pos - d_weg / 1000

            except (ArithmeticError, AttributeError):
                end_pos = fahrstrassenabschnitte[i].end_abschnitt_pos + 200 / 1000 if direction == "S" else \
                    fahrstrassenabschnitte[i].end_abschnitt_pos - 200 / 1000
                print("Nachbelegungszeit berechnen? Zug ist an Endhaltestelle angelangt")

            raeumfahrstecke = end_pos + train_total_length / 1000 if direction == "S" else end_pos - train_total_length / 1000

            start_ts = get_waypoints(records, direction, initial_position,
                                     fahrstrassenabschnitte[i].end_abschnitt_pos).timestamp
            end_ts = get_waypoints(records, direction, initial_position, raeumfahrstecke).timestamp
            d_driving_time = end_ts - start_ts

            nachbelegungszeit = round((d_driving_time + aufloesezeit / 60), 4)
            nachbelegungszeiten.append(nachbelegungszeit)
            if i == len(fahrstrassenabschnitte) - 2:
                last_fstr_abschnitt_pos = fahrstrassenabschnitte[i].start_abschnitt_pos
    if sig_zugschluss_pos is None:
        try:
            speed_at_entrance = get_waypoints(records, direction, initial_position, last_fstr_abschnitt_pos).velocity
            d_weg = get_d_weg(speed_at_entrance)
            end_pos = end_hs_pos + d_weg / 1000 if direction == "S" else end_hs_pos - d_weg / 1000

        except (ArithmeticError, AttributeError):
            end_pos = end_hs_pos + 200 / 1000 if direction == "S" else end_hs_pos - 200 / 1000
            print("Nachbelegungszeit berechnen? Zug ist an Endhaltestelle angelangt")
    else:
        end_pos = sig_zugschluss_pos

    raeumfahrstecke = end_pos + train_total_length / 1000 if direction == "S" else end_pos - train_total_length / 1000

    start_ts = get_waypoints(records, direction, initial_position, end_hs_pos).timestamp
    end_ts = get_waypoints(records, direction, initial_position, raeumfahrstecke).timestamp
    d_driving_time = end_ts - start_ts

    nachbelegungszeit = round((d_driving_time + aufloesezeit / 60), 4)
    nachbelegungszeiten.append(nachbelegungszeit)
    if PRINT_OUTPUTS:
        print("LIST NACHBELEGUNGZEITEN -> ", nachbelegungszeit, nachbelegungszeiten)
    return nachbelegungszeit, nachbelegungszeiten


def calculate_occupancy_time(records, block, train_total_length, initial_position, direction):
    """
    Function to calculate the Occupancy time in minutes
    :param records:
    :param block: block dataclass containing all elements of the block which we want to calculate the occupancy time for
    :param train_total_length: the total length of the current train in m
    :param initial_position: The Kilometrierung of the first element of the schedule
    :param direction: The direction the train is driving along ("F" or "S")
    :param calculate_fstr_abschnitte: Decides wether the whole block is considered or
    each fahrstrassenabschnitt is considered individually
    :return vorbelegungszeit, list of driving times, list of nachbelegungszeiten,
    occupancy time in minutes for the given block
    """
    vorbelegungszeit = calculate_vorbelegungszeit(records, block.vorsignal_pos,
                                                  block.start_hauptsignal_pos, initial_position,
                                                  direction)

    driving_time_block = calculate_driving_time_block(records, block.fahrstrassenabschnitte,
                                                      block.start_hauptsignal_pos,
                                                      block.end_hauptsignal_pos, initial_position, direction)
    nachbelegungszeit = calculate_nachbelegungszeit(records, block.fahrstrassenabschnitte, train_total_length,
                                                    block.start_hauptsignal_pos,
                                                    block.end_hauptsignal_pos,
                                                    block.zugschlussstelle_pos, block.zugschlussstelle_aufloesezeit,
                                                    initial_position, direction)

    occupancy_time = round((vorbelegungszeit + driving_time_block[0] + nachbelegungszeit[0]), 4)

    if PRINT_OUTPUTS:
        print('########################NEW BLOCK###############################')
        print(block)
        print(f'Vorbelegungszeit: {vorbelegungszeit}')
        print(f'Fahrzeit: {driving_time_block[0]}')
        print(f'Nachbelegungszeit: {nachbelegungszeit[0]}')
        print(f'Occupancy time: {occupancy_time}')
        print(driving_time_block)
        print('################################################################')
    return vorbelegungszeit, driving_time_block[1], nachbelegungszeit[1], occupancy_time


def calculate_times(nodes, records, train_total_length, last_fstr_id=None, last_fstr_pos=None):
    """
    calculated the occupancy time for each block of a journey
    :param train_total_length:
    :param records:
    :param nodes:
    :return all vorbelegungszeiten of journey(list),driving times through blocks(list), nachbelegungszeiten(list),
    occupancy times(list)
    """

    direction = determine_direction(nodes)
    blocks, last_fstr_id, last_fstr_pos = get_blocks(nodes, direction, last_fstr_id, last_fstr_pos)

    if nodes[0].tag == "Weichenanfang":
        initial_position = get_absolute_kilometrage(nodes[1])
    else:
        initial_position = get_absolute_kilometrage(nodes[0])

    vorbelegungszeiten = []
    driving_times = []
    nachbelegungszeiten = []
    belegungszeiten = []
    for block in blocks:
        vorbelegungszeit, driving_time, nachbelegungszeit, belegungszeit = calculate_occupancy_time(records,
                                                                                                    block,
                                                                                                    train_total_length,
                                                                                                    initial_position,
                                                                                                    direction)
        vorbelegungszeiten.append(vorbelegungszeit)
        driving_times.append(driving_time)
        nachbelegungszeiten.append(nachbelegungszeit)
        belegungszeiten.append(belegungszeit)

    return vorbelegungszeiten, driving_times, nachbelegungszeiten, belegungszeiten, blocks, last_fstr_id, last_fstr_pos


def write_occupancy_times(train):
    """
    Writes a xml-file with the occupancy times for a given train in the trains schedule directory.
    :param train: The train as string with format '<line> <journey_id>'
    """
    if PRINT_OUTPUTS:
        print('Write occupancy times of train ' + train + '...')

    train_info = train.split()

    # initialize root element of ET
    occupancy_times = ET.Element('occupancy_times')

    # get train information from schedule
    schedules_train_dir = path.join(SCHEDULES_ROOT_DIR, Path(train_info[0], train_info[1]))
    schedule_path = path.join(schedules_train_dir, Path('schedule.xml'))
    try:
        nodes_list = get_all_verlauf_nodes(train_info[0], train_info[1])
        records_list = get_trajectory_records(train_info[0], train_info[1])
        train_length = get_train_total_length(train_info[0])
    except FileNotFoundError:
        print('File not found:', schedule_path)

    last_fstr_id = None
    last_fstr_pos = None
    # calculate occupancy times
    for (nodes, records) in zip(nodes_list, records_list):

        vorbelegungszeiten, driving_times, nachbelegungszeiten, belegungszeiten, blocks, last_fstr_id, last_fstr_pos = \
            calculate_times(nodes, records, train_length, last_fstr_id, last_fstr_pos)

        # create the file structure
        link = ET.SubElement(occupancy_times, 'link')
        for i, b in enumerate(blocks):
            block = ET.SubElement(link, 'block', dict(id=b.block_id))

            belegungszeit = ET.SubElement(block, 'belegungszeit')
            belegungszeit.text = str(belegungszeiten[i])

            vorbelegungszeit = ET.SubElement(block, 'vorbelegungszeit')
            vorbelegungszeit.text = str(vorbelegungszeiten[i])

            driving_time = ET.SubElement(block, 'driving_time')
            driving_time.text = str(driving_times[i]) \
                .replace('[', '').replace(']', '').replace(',', '')

            nachbelegungszeit = ET.SubElement(block, 'nachbelegungszeit')
            nachbelegungszeit.text = str(nachbelegungszeiten[i]) \
                .replace('[', '').replace(']', '').replace(',', '')

            block_info = ET.SubElement(block, 'block_info')
            deconstruct_block(b, block_info)

    # create a new XML file
    times_dir = path.join(OCCUPANCY_TIMES_DIR, Path(train_info[0], train_info[1]))
    if not path.exists(times_dir):
        makedirs(times_dir)
    times_path = path.join(times_dir, Path('occupancy_times.xml'))
    library.writer.write_et(occupancy_times, times_path)

    if PRINT_OUTPUTS:
        print(times_path + ' successfully written.')


def rewrite_all_occupancy_times():
    """
    recalculate and write all occupancy times xmls
    """
    trains = get_relevant_directories()
    for train in trains:
        write_occupancy_times(train)


def deconstruct_block(block, et):
    """
    Deconstructs the given block object to an ET subtree and appends it to the given ET.
    :param block: The block object which has to be deconstructed.
    :param et: The ElementTree where the block informations will be appended.
    """
    vorsignal_id = ET.SubElement(et, 'vorsignal_id')
    vorsignal_id.text = safe_str(block.vorsignal_id)
    vorsignal_pos = ET.SubElement(et, 'vorsignal_pos')
    vorsignal_pos.text = safe_str(block.vorsignal_pos)
    start_hauptsignal_id = ET.SubElement(et, 'start_hauptsignal_id')
    start_hauptsignal_id.text = safe_str(block.start_hauptsignal_id)
    start_hauptsignal_pos = ET.SubElement(et, 'start_hauptsignal_pos')
    start_hauptsignal_pos.text = safe_str(block.start_hauptsignal_pos)

    fahrstrassenabschnitte = block.fahrstrassenabschnitte
    for fahrstrassenabschnitt in fahrstrassenabschnitte:
        abschnitt = ET.SubElement(et, 'fahrstrassenabschnitt')
        start_abschnitt_id = ET.SubElement(abschnitt, 'start_abschnitt_id')
        start_abschnitt_id.text = safe_str(fahrstrassenabschnitt.start_abschnitt_id)
        start_abschnitt_pos = ET.SubElement(abschnitt, 'start_abschnitt_pos')
        start_abschnitt_pos.text = safe_str(fahrstrassenabschnitt.start_abschnitt_pos)
        end_abschnitt_id = ET.SubElement(abschnitt, 'end_abschnitt_id')
        end_abschnitt_id.text = safe_str(fahrstrassenabschnitt.end_abschnitt_id)
        end_abschnitt_pos = ET.SubElement(abschnitt, 'end_abschnitt_pos')
        end_abschnitt_pos.text = safe_str(fahrstrassenabschnitt.end_abschnitt_pos)

    end_hauptsignal_id = ET.SubElement(et, 'end_hauptsignal_id')
    end_hauptsignal_id.text = safe_str(block.end_hauptsignal_id)
    end_hauptsignal_pos = ET.SubElement(et, 'end_hauptsignal_pos')
    end_hauptsignal_pos.text = safe_str(block.end_hauptsignal_pos)
    zugschlussstelle_id = ET.SubElement(et, 'zugschlussstelle_id')
    zugschlussstelle_id.text = safe_str(block.zugschlussstelle_id)
    zugschlussstelle_pos = ET.SubElement(et, 'zugschlussstelle_pos')
    zugschlussstelle_pos.text = safe_str(block.zugschlussstelle_pos)
    zugschlussstelle_aufloesezeit = ET.SubElement(et, 'zugschlussstelle_aufloesezeit')
    zugschlussstelle_aufloesezeit.text = safe_str(block.zugschlussstelle_aufloesezeit)
    distance_a = ET.SubElement(et, 'distance_a')
    distance_a.text = safe_str(block.distance_a)
    distance_b = ET.SubElement(et, 'distance_b')
    distance_b.text = safe_str(block.distance_b)
    distance_d = ET.SubElement(et, 'distance_d')
    distance_d.text = safe_str(block.distance_d)


def read_occupancy_times(train):
    """
    Reads the occupancy times xml-file for a given train in the trains schedule directory.
    :param train: The train as string with format '<line> <journey_id>'
    """
    train_info = train.split()
    times_path = path.join(OCCUPANCY_TIMES_DIR, Path(train_info[0], train_info[1], 'occupancy_times.xml'))

    try:
        root = ET.parse(times_path).getroot()
    except FileNotFoundError:
        write_occupancy_times(train)
        root = ET.parse(times_path).getroot()

    return root


def get_times(train, link_id=None, update_times=False):
    """
    Reads the occupancy times from xml-file and returns them as lists.
    :param train: The train as string with format '<line> <journey_id>'
    :param link_id: if set -> return only times for specific link
    :param update_times: Update occupancy times xml-file
    :return All vorbelegungszeiten, driving times through blocks, nachbelegungszeiten, occupancy times and
    blocks as lists
    """

    # update occupancy times
    if update_times:
        write_occupancy_times(train)

    # read occupancy times file of the train
    root = read_occupancy_times(train)

    # init lists to return times
    blocks_info = []
    belegungszeiten = []
    vorbelegungszeiten = []
    driving_times = []
    nachbelegungszeiten = []

    # append times for each block in each link
    links = root.findall('link')
    if link_id is not None:
        links = [links[link_id]]

    for link in links:
        blocks = link.findall('block')

        for block in blocks:
            blocks_info.append(construct_block(block.find('block_info'), block.attrib['id']))
            belegungszeiten.append(float(block.find('belegungszeit').text))
            vorbelegungszeiten.append(float(block.find('vorbelegungszeit').text))
            driving_times.append(list(map(float, block.find('driving_time').text.split())))
            nachbelegungszeiten.append(list(map(float, block.find('nachbelegungszeit').text.split())))

    return belegungszeiten, vorbelegungszeiten, driving_times, nachbelegungszeiten, blocks_info


def construct_block(et, block_id):
    """
    Constructs a block object from a given ET subtree.

    :param et: ET Subtree with the block informations.
    :param block_id: The id of the block.
    :return: The constructed block object.
    """
    vorsignal_id = et.find('vorsignal_id').text
    vorsignal_pos = safe_float(et.find('vorsignal_pos').text)
    start_hauptsignal_id = et.find('start_hauptsignal_id').text
    start_hauptsignal_pos = safe_float(et.find('start_hauptsignal_pos').text)

    fahrstrassenabschnitte = []
    abschnitte = et.findall('fahrstrassenabschnitt')
    for abschnitt in abschnitte:
        start_abschnitt_id = abschnitt.find('start_abschnitt_id').text
        start_abschnitt_pos = safe_float(abschnitt.find('start_abschnitt_pos').text)
        end_abschnitt_id = abschnitt.find('end_abschnitt_id').text
        end_abschnitt_pos = safe_float(abschnitt.find('end_abschnitt_pos').text)
        fahrstrassenabschnitte.append(
            Fahrstrassenabschnitt(start_abschnitt_id, start_abschnitt_pos, end_abschnitt_id, end_abschnitt_pos)
        )

    end_hauptsignal_id = et.find('end_hauptsignal_id').text
    end_hauptsignal_pos = safe_float(et.find('end_hauptsignal_pos').text)
    zugschlussstelle_id = et.find('zugschlussstelle_id').text
    zugschlussstelle_pos = safe_float(et.find('zugschlussstelle_pos').text)
    zugschlussstelle_aufloesezeit = safe_float(et.find('zugschlussstelle_aufloesezeit').text)
    distance_a = safe_float(et.find('distance_a').text)
    distance_b = safe_float(et.find('distance_b').text)
    distance_d = safe_float(et.find('distance_d').text)

    return Block(block_id, vorsignal_id, vorsignal_pos, start_hauptsignal_id, start_hauptsignal_pos,
                 fahrstrassenabschnitte, end_hauptsignal_id, end_hauptsignal_pos, zugschlussstelle_id,
                 zugschlussstelle_pos, zugschlussstelle_aufloesezeit, distance_a, distance_b, distance_d)


def safe_str(element):
    """
    Parses any element to a string or returns "None" as a string if the element is None.
    :param element: Any element which can be parsed to a string.
    :return: The string representation of the element.
    """
    if element is not None:
        return str(element)

    return "None"


def safe_float(string):
    """
    Parses a string to float or returns None if the string equals "None".
    :param string: A string which will be parsed to float.
    :return: The string as float or None.
    """
    if string != "None":
        return float(string)


# example of getting occupancy times of given train with it's journey id, passed as String type
if __name__ == "__main__":
    print(get_times("S1 1111"))
