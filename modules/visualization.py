"""
Module to visualize the occupancy times (plots) of given trains
"""
import datetime
import os
from datetime import timedelta
from os import path
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from elements.trajectory import get_waypoints
from library import parser
from library.train_schedule_parser import Train
from library.utils import determine_direction, get_absolute_kilometrage

from occupancy_times import get_times

START_TIME = parser.parse_date_time("2020-07-22T07:30:00.000000")
END_TIME = parser.parse_date_time("2020-07-22T09:15:00.000000")

PLOT_ONLY_FIRST = False
PLOT_ONLY_ONE_DIR = True
DIR_TO_PLOT = 0
HEIGHT = 5


def visualize_lines(lines_to_plot, plot_first_journey_only=False, plot_one_dir_only=True, dir_to_plot=0,
                    start_time=None, end_time="2020-07-22T09:15:00.000000"):
    """
    Creates pdf file containing all plotted occupancy times for given lines
    :param lines_to_plot: List containing the name of all lines that should be plotted
    :param plot_first_journey_only: Plot the first journey of each line only
    :param plot_one_dir_only: Plot journey(s) in either steigende or fallende Richtung only
    :param dir_to_plot: If plot one dir only: Select Direction: 0 for Steigend and 1 for Fallend
    :param start_time: First time to plot
    :param end_time: last time to plot
    """
    package_dir = path.dirname(Path(__file__).parent)
    global START_TIME, END_TIME, PLOT_ONLY_FIRST, PLOT_ONLY_ONE_DIR, DIR_TO_PLOT, HEIGHT
    END_TIME = parser.parse_date_time(end_time)
    PLOT_ONLY_FIRST = plot_first_journey_only
    PLOT_ONLY_ONE_DIR = plot_one_dir_only
    DIR_TO_PLOT = dir_to_plot
    if start_time is not None:
        START_TIME = parser.parse_date_time(start_time)
    else:
        earliest_departure_time = datetime.datetime.max
        for line in lines_to_plot:
            line_folder = path.join(package_dir, Path('resources/schedules/'), line)
            for _, dirs, _ in os.walk(line_folder):
                for directory in dirs:
                    try:
                        abfahrt_zeit = list(parser.get_departure_time(line, directory).values())[0].replace(tzinfo=None)
                    except FileNotFoundError:
                        continue
                    if (abfahrt_zeit - earliest_departure_time).total_seconds() < 0:
                        earliest_departure_time = abfahrt_zeit
        START_TIME = (earliest_departure_time - timedelta(minutes=10))

    # Y-Axis height in minutes
    HEIGHT = (END_TIME - START_TIME).total_seconds() / 60

    _, ax = plt.subplots(figsize=(64, 36), dpi=300)

    for line in lines_to_plot:
        print(f'Visualizing line: {line}')
        line_folder = path.join(package_dir, Path('resources/schedules/'), line)

        for _, dirs, _ in os.walk(line_folder):
            for directory in dirs:
                try:
                    train = Train(train_line=line, train_journey_id=directory)
                except FileNotFoundError:
                    continue
                nodes_list = train.get_verlauf()
                records_list = train.get_trajectory()

                link_id = 0
                last_block_driving_time = None
                last_block_vorbelegungszeit_height = None
                last_block_fahrzeit_height = None

                abfahrt_zeit = parser.get_departure_time(line, directory)
                # Abfahrtzeit of the current link in minutes since plot start time
                base_time = (list(abfahrt_zeit.values())[0].replace(tzinfo=None) - START_TIME).total_seconds() / 60

                for (nodes, records) in zip(nodes_list.values(), records_list.values()):
                    records = records[0]
                    # For visualization
                    direction = determine_direction(nodes)
                    if PLOT_ONLY_ONE_DIR:
                        if (DIR_TO_PLOT == 0 and direction == "F") or (DIR_TO_PLOT == 1 and direction == "S"):
                            break

                    belegungszeiten, vorbelegungszeiten, driving_times, nachbelegungszeiten, blocks = get_times(
                        line + " " + directory, link_id)
                    # Dont plot journeys that are outside the plot dimensions
                    if (HEIGHT - base_time) < sum(belegungszeiten):
                        break

                    # The position of the first element of the link
                    if nodes[0].tag == "Weichenanfang":
                        base_position = get_absolute_kilometrage(nodes[1])
                    else:
                        base_position = get_absolute_kilometrage(nodes[0])

                    base_time = (list(abfahrt_zeit.values())[link_id].replace(
                        tzinfo=None) - START_TIME).total_seconds() / 60
                    # Used for connecting last and first point of trajectory
                    if link_id == 0:
                        last_traj_pos, last_traj_time = plot_driving_dynamic(records, direction, base_time,
                                                                             base_position)
                    else:
                        last_traj_pos, last_traj_time = plot_driving_dynamic(records, direction, base_time,
                                                                             base_position, last_traj_pos,
                                                                             last_traj_time)

                    last_block_driving_time, last_block_vorbelegungszeit_height, last_block_fahrzeit_height = visualize_blocking_times(
                        ax, link_id, abfahrt_zeit,
                        vorbelegungszeiten, driving_times,
                        nachbelegungszeiten, blocks, records, base_position,
                        direction, last_block_driving_time, last_block_vorbelegungszeit_height,
                        last_block_fahrzeit_height)

                    plt.text(base_position, base_time,
                             line + " / " + directory, fontsize=50)

                    link_id += 1

                if PLOT_ONLY_FIRST and link_id != 0:
                    break
    # Plot configurations
    plt.style.use('Solarize_Light2')  # plot style
    ax.set_xlabel(r'Kilometrage $n$')
    ax.set_ylabel(r'Time $t$')
    ax.set_ylim(HEIGHT, -2)
    ax.tick_params(labelbottom=False, labeltop=True, labelleft=True, labelright=False)
    ax.tick_params(bottom=True, top=True, left=True, right=True)
    ax.grid(True)

    plt.rcParams.update({'font.size': 60})
    ax.xaxis.label.set_size(100)
    ax.yaxis.label.set_size(100)
    ax.tick_params(axis='both', which='major', labelsize=50)
    ax.tick_params(axis='both', which='minor', labelsize=50)
    # Map absolute time values(minutes) from y-axis to timestamps
    ax.yaxis.set_major_formatter(lambda y, pos: (START_TIME + timedelta(minutes=y)).strftime('%H:%M:%S.%f'))

    plt.legend(['Vorbelegungszeit', 'Fahrzeit', 'Nachbelegungszeit'])

    if DIR_TO_PLOT == 0:
        direction = "_Steigend"
    else:
        direction = "_Fallend"
    export_path = '../output/visualisations/occupancy_times_' + '_'.join(lines_to_plot) + direction + '.pdf'
    Path('..\\output\\visualisations').mkdir(parents=True, exist_ok=True)
    plt.savefig(export_path, dpi=300)


def visualize_blocking_times(ax, link_id, abfahrt_zeiten, vorbelegungszeiten, driving_times, nachbelegungszeiten,
                             blocks, records, base_position, direction, last_block_driving_time,
                             last_block_vorbelegungszeit_height, last_block_fahrzeit_height):
    """
    :param ax: axis object of the plot to plot bars on
    :param link_id: id of the current link
    :param abfahrt_zeiten: dict containing the abfahrtzeiten for links for this line
    :param vorbelegungszeiten: list containing the vorbelegungszeiten for the blocks to plot
    :param driving_times: list containing the driving_times for the blocks to plot
    :param nachbelegungszeiten: list containing the nachbelegungszeiten for the blocks to plot
    :param blocks: list containing the Blocks to plot
    :param records: see parser class
    :param base_position: the position of the first element of the link
    :param direction:driving direction "F" or "S"
    :param last_block_vorbelegungszeit_height: the vorbeleungszeit of the last block of previous link if there was one
    :param last_block_driving_time: the end of the driving time of the last block of previous link if there was one
    :param last_block_fahrzeit_height: the driving time of the last block of previous link if there was one
    """
    # Time when train reaches the first Block in minutes since abfahrtszeit at link
    try:
        hs_time = get_waypoints(records, direction, base_position, blocks[0].start_hauptsignal_pos).timestamp
    except Exception:
        hs_time = 0

    base_timestamp = (list(abfahrt_zeiten.values())[link_id].replace(tzinfo=None))
    # Abfahrtzeit of the current link in minutes since plot start time
    base_time = (list(abfahrt_zeiten.values())[link_id].replace(tzinfo=None) - START_TIME).total_seconds() / 60

    # Timestamp and time of the first block
    base_timestamp += timedelta(minutes=hs_time)
    base_time += hs_time
    # Handle basic block visualization
    # Applied to all but the last block -> reformatted to only use a list instead of nested list
    first_block_vorbelegungszeiten = [vorbelegungszeiten[0]]
    first_block_driving_times = [sum(driving_times[0])]
    first_block_nachbelegungszeiten = [nachbelegungszeiten[0][-1]]
    first_block = blocks[0]
    base_time = visualize_first_block(ax, records, link_id, last_block_driving_time, last_block_vorbelegungszeit_height,
                                      last_block_fahrzeit_height, base_time, first_block_vorbelegungszeiten,
                                      first_block_driving_times, first_block_nachbelegungszeiten, first_block,
                                      direction)

    # Second Block is the exit of the train station -> detailed visualisation
    if len(vorbelegungszeiten) > 2:
        second_block_vorbelegungszeiten = [vorbelegungszeiten[1] for d in driving_times[1]]
        second_block_driving_times = driving_times[1]
        second_block_nachbelegungszeiten = nachbelegungszeiten[1]
        second_block = blocks[1]
        end_block_driving_time, _, _ = visualize_detailed_blocking_times(ax, base_time, second_block_vorbelegungszeiten,
                                                                         second_block_driving_times,
                                                                         second_block_nachbelegungszeiten, second_block,
                                                                         direction)
        base_time = end_block_driving_time

    # Basic Visualisation for lines
    if len(vorbelegungszeiten) > 3:
        basic_vorbelegungszeiten = vorbelegungszeiten[2:len(vorbelegungszeiten) - 1]
        basic_driving_times = [sum(d) for d in driving_times[2:len(driving_times) - 1]]
        basic_nachbelegungszeiten = [n[-1] for n in nachbelegungszeiten[2:len(nachbelegungszeiten) - 1]]
        basic_blocks = blocks[2:len(blocks) - 1]

        visualize_basic_blocking_times(ax, base_time, basic_vorbelegungszeiten,
                                       basic_driving_times, basic_nachbelegungszeiten, basic_blocks,
                                       direction)

        base_time += sum(basic_driving_times)

    # Handle last block visualization -> entrance train station
    end_block_vorbelegungszeiten = [vorbelegungszeiten[-1] for d in driving_times[-1]]
    end_block_driving_times = driving_times[-1]
    end_nachbelegungszeiten = nachbelegungszeiten[-1]
    end_block = blocks[-1]

    end_block_driving_time, vorbelegungszeit_height, fahrzeit_height = visualize_detailed_blocking_times(ax, base_time,
                                                                                                         end_block_vorbelegungszeiten,
                                                                                                         end_block_driving_times,
                                                                                                         end_nachbelegungszeiten,
                                                                                                         end_block,
                                                                                                         direction)
    return end_block_driving_time, vorbelegungszeit_height, fahrzeit_height


def plot_driving_dynamic(records, direction, base_time, base_position, last_traj_pos=None, last_traj_time=None):
    """
    Plots the trajectory of the train
    :param records: see parser class
    :param direction: driving direction "S" or "F"
    :param base_time: Abfahrtzeit of the current link in minutes since plot start time
    :param base_position: Position of the first element of the link
    :param last_traj_pos: position of last point of previous link
    :param last_traj_time: time of last point of previous link
    :return position, time of last point
    """

    # Determines the width of the line
    size = 7 * 0.9964 ** HEIGHT
    x_kilometrierungen = []
    y_times = []

    # Used to connect to previous link
    if last_traj_pos is not None:
        x_kilometrierungen.append(last_traj_pos)
        y_times.append(last_traj_time)

    for record in records:
        relative_time = float(record.find("Upper_absolute_ts").text) / 60
        relative_position = float(record.find("Lower_xs").text) / 1000

        relative_time += base_time
        if direction == "F":
            relative_position *= -1
        relative_position += base_position

        x_kilometrierungen.append(relative_position)
        y_times.append(relative_time)

    plt.scatter(x_kilometrierungen, y_times, zorder=2, s=0, c='black', label="_nolegend_")
    plt.plot(x_kilometrierungen, y_times, zorder=2, c='black', label="_nolegend_", linewidth=size)
    return relative_position, relative_time


def visualize_first_block(ax, records, link_id, base_time, last_block_vorbelegungszeit_height,
                          last_block_fahrzeit_height, abfahrts_zeit, vorbelegungszeiten, driving_times,
                          nachbelegungszeiten, block,
                          direction):
    if link_id == 0:
        visualize_basic_blocking_times(ax, abfahrts_zeit, vorbelegungszeiten,
                                       driving_times, nachbelegungszeiten, [block],
                                       direction)
        return abfahrts_zeit + sum(driving_times)

    # Visualize first extended Block
    block_length = block.distance_b
    if direction == "S":
        block_start = block.start_hauptsignal_pos
    else:
        block_start = block.start_hauptsignal_pos - block_length

    abfahrts_zeit += float(records[0].find("Upper_absolute_ts").text.replace(",", ".")) / 60
    vorbelegungs_height = last_block_vorbelegungszeit_height
    bottom = base_time - vorbelegungs_height - last_block_fahrzeit_height
    # Plot data as bars, with x_start as x and x_end as width and y_start as bottom and y_end as height
    ax.bar(x=block_start, height=vorbelegungs_height, width=block_length, align='edge',
           bottom=bottom,
           color='#fdca00', edgecolor='orange', linewidth=0.3, label='Vorbelegungszeit')
    fahrzeit_height = (abfahrts_zeit - base_time) + sum(driving_times) + last_block_fahrzeit_height
    bottom = base_time - last_block_fahrzeit_height
    ax.bar(x=block_start, height=fahrzeit_height, width=block_length, align='edge',
           bottom=bottom,
           color='#b5b5b5', edgecolor='gray', linewidth=0.3, label='Fahrzeit')

    nachbelegungszeit_height = nachbelegungszeiten[0]
    bottom = abfahrts_zeit + driving_times[0]
    ax.bar(x=block_start, height=nachbelegungszeit_height, width=block_length, align='edge',
           bottom=bottom,
           color='#0085cc', edgecolor='blue', linewidth=0.3, label='Nachbelegungszeit')

    return bottom


def visualize_detailed_blocking_times(ax, base_time, vorbelegungszeiten, driving_times, nachbelegungszeiten, end_block,
                                      direction):
    """
    Visualize occupancy times for each Fahrstrassenabschnitt of one Block
    :param ax: axis element of plot
    :param base_time: start time of block. Ususally end of last basic blocks driving time in minutes
    :param vorbelegungszeiten: list containing the vorbelegungszeiten for the blocks to plot
    :param driving_times: list containing the driving_times for the blocks to plot
    :param nachbelegungszeiten: list containing the nachbelegungszeiten for the blocks to plot
    :param end_block: block that should be visualized (see Dataclass Block)
    :param direction: driving direction "F" or "S"
    """
    # List of relevant elements of blocks
    fstr_abschnitt_start = []
    fstr_abschnitt_end = []
    fstr_abschnitt_length = []
    for abschnitt in getattr(end_block, 'fahrstrassenabschnitte'):
        start_pos = (getattr(abschnitt, 'start_abschnitt_pos'))
        fstr_abschnitt_start.append(start_pos)
        end_pos = (getattr(abschnitt, 'end_abschnitt_pos'))
        fstr_abschnitt_end.append(end_pos)
        fstr_abschnitt_length.append(abs(end_pos - start_pos))

    # Store absolute differences between times
    t_0 = []
    for i in range(len(driving_times)):
        if i == 0:
            t_0.append(base_time)
        else:
            t_0.append(t_0[i - 1] + driving_times[i - 1])

    # Used to extend the driving times, each driving time is always the driving time of previous Abschnitt + current driving time
    driving_times = np.cumsum(driving_times)

    shifted_driving_time = np.roll(driving_times, 1)
    shifted_driving_time[0] = 0

    # Dataframe
    blocking_time = {'Abschnitt_Start': fstr_abschnitt_start,
                     'Abschnitt_End': fstr_abschnitt_end,
                     'Abschnitt_Length': fstr_abschnitt_length,
                     'Vorbelegungszeit': vorbelegungszeiten,
                     'Fahrzeit': driving_times,
                     'Nachbelegungszeit': nachbelegungszeiten,
                     'shifted_driving_time': shifted_driving_time,
                     't_0': t_0
                     }

    block_data = pd.DataFrame(data=blocking_time)
    pd.set_option('display.max_columns', None)

    for i in range(0, len(driving_times)):

        abschnitt_length = block_data["Abschnitt_Length"][i]
        if direction == "S":
            abschnitt_start = block_data["Abschnitt_Start"][i]
        else:
            abschnitt_start = block_data["Abschnitt_Start"][i] - abschnitt_length

        vorbelegungs_height = block_data["Vorbelegungszeit"][i]
        bottom = base_time - block_data["Vorbelegungszeit"][i]

        ax.bar(x=abschnitt_start, height=vorbelegungs_height, width=abschnitt_length, align='edge',
               bottom=bottom,
               color='#fdca00', edgecolor='orange', linewidth=0.3, label='Vorbelegungszeit')

        fahrzeit_height = block_data["Fahrzeit"][i]
        bottom = block_data["t_0"][i] - block_data["shifted_driving_time"][i]

        ax.bar(x=abschnitt_start, height=fahrzeit_height, width=abschnitt_length, align='edge',
               bottom=bottom,
               color='#b5b5b5', edgecolor='gray', linewidth=0.3, label='Fahrzeit')

        nachbelegungszeit_height = block_data["Nachbelegungszeit"][i]
        bottom = block_data["t_0"][i] + block_data["Fahrzeit"][i] - block_data.shifted_driving_time[i]
        ax.bar(x=abschnitt_start, height=nachbelegungszeit_height, width=abschnitt_length, align='edge',
               bottom=bottom,
               color='#0085cc', edgecolor='blue', linewidth=0.3, label='Nachbelegungszeit')
    return list(block_data["t_0"])[-1] + list(block_data["Fahrzeit"])[-1] - list(block_data["shifted_driving_time"])[
        -1], vorbelegungs_height, fahrzeit_height


def visualize_basic_blocking_times(ax, base_time, vorbelegungszeiten, driving_times, nachbelegungszeiten, blocks,
                                   direction):
    """
    visualizes the occupancy times for each block contained in blocks list
    :param ax: axis element of plot
    :param base_time: start time of block. Ususally end of last basic blocks driving time in minutes
    :param vorbelegungszeiten: list containing the vorbelegungszeiten for the blocks to plot
    :param driving_times: list containing the driving_times for the blocks to plot
    :param nachbelegungszeiten: list containing the nachbelegungszeiten for the blocks to plot
    :param blocks: list containing all blocks that should be visualized (see Dataclass Block)
    :param direction: driving direction "F" or "S"
    :return time of the end of the driving time of last block in minutes since base_time
    """
    # List of relevant elements of blocks
    block_start = []
    block_end = []
    block_length = []
    for block in blocks:
        block_start.append((getattr(block, 'start_hauptsignal_pos')))
        block_end.append((getattr(block, 'end_hauptsignal_pos')))
        block_length.append((getattr(block, 'distance_b')))

    # Store absolute differences between times
    t_0 = []
    for i in range(len(driving_times)):
        if i == 0:
            t_0.append(base_time)
        else:
            t_0.append(t_0[i - 1] + driving_times[i - 1])

    # Dataframe
    blocking_time = {'Block_Start': block_start,
                     'Block_End': block_end,
                     'Block_Length': block_length,
                     # 'Vorbelegungszeit_Stamp': vorbelegung_time_stamp,
                     'Vorbelegungszeit': vorbelegungszeiten,
                     # 'Fahrzeit_Stamp': driving_time_stamp,
                     'Fahrzeit': driving_times,
                     # 'Nachbelegungszeit_Stamp': nachbelegung_time_stamp,
                     'Nachbelegungszeit': nachbelegungszeiten,
                     't_0': t_0
                     }
    block_data = pd.DataFrame(data=blocking_time)
    pd.set_option('display.max_columns', None)

    for i in range(0, len(blocks)):
        block_length = block_data["Block_Length"][i]
        if direction == "S":
            block_start = block_data["Block_Start"][i]
        else:
            block_start = block_data["Block_Start"][i] - block_length

        vorbelegungs_height = block_data["Vorbelegungszeit"][i]
        bottom = block_data["t_0"][i] - block_data["Vorbelegungszeit"][i]
        # Plot data as bars, with x_start as x and x_end as width and y_start as bottom and y_end as height
        ax.bar(x=block_start, height=vorbelegungs_height, width=block_length, align='edge',
               bottom=bottom,
               color='#fdca00', edgecolor='orange', linewidth=0.3, label='Vorbelegungszeit')

        fahrzeit_height = block_data["Fahrzeit"][i]
        bottom = block_data["t_0"][i]
        ax.bar(x=block_start, height=fahrzeit_height, width=block_length, align='edge',
               bottom=bottom,
               color='#b5b5b5', edgecolor='gray', linewidth=0.3, label='Fahrzeit')

        nachbelegungszeit_height = block_data["Nachbelegungszeit"][i]
        bottom = block_data["t_0"][i] + block_data["Fahrzeit"][i]
        ax.bar(x=block_start, height=nachbelegungszeit_height, width=block_length, align='edge',
               bottom=bottom,
               color='#0085cc', edgecolor='blue', linewidth=0.3, label='Nachbelegungszeit')

    return list(block_data["t_0"])[-1] + list(block_data["Fahrzeit"])[-1]


# example of S2 and ICE500
if __name__ == '__main__':
    lines = ["S2", "ICE500"]
    visualize_lines(lines, plot_one_dir_only=True, plot_first_journey_only=False, dir_to_plot=0,
                    start_time="2020-07-22T08:20:59.999000", end_time="2020-07-22T09:05:00.000000")
