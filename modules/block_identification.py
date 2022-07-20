"""
block identification modules to divide the track into blocks (identification in track)
"""
from dataclasses import dataclass, field

import library.parser as parse
from library.utils import get_absolute_kilometrage


@dataclass
class Fahrstrassenabschnitt:
    """
    data class for Fahrstrassenabschnitt:
    """
    start_abschnitt_id: int = field(default=None)
    start_abschnitt_pos: int = field(default=None)
    end_abschnitt_id: int = field(default=None)
    end_abschnitt_pos: int = field(default=None)


@dataclass
class Block:
    """
    Block -> space between two hauptsignals
    """
    block_id: int = field(default=None)
    vorsignal_id: int = field(default=None)
    vorsignal_pos: float = field(default=None)
    start_hauptsignal_id: int = field(default=None)
    start_hauptsignal_pos: float = field(default=None)
    fahrstrassenabschnitte: list = field(default=None)
    end_hauptsignal_id: int = field(default=None)
    end_hauptsignal_pos: float = field(default=None)
    zugschlussstelle_id: int = field(default=None)
    zugschlussstelle_pos: float = field(default=None)
    zugschlussstelle_aufloesezeit: float = field(default=None)
    distance_a: float = field(default=None)
    distance_b: float = field(default=None)
    distance_d: float = field(default=None)


def find_last_hs(id_of_prev_node, name_of_prev_node, pos_of_prev_node, direction):
    """
    Function to find last 'Hauptsignal' of a journey and return id and position accordingly
    :param id_of_prev_node: id of the node we want to find the next Hauptsignal for
    :param name_of_prev_node: name of the node we want to find the next Hauptsignal for
    :param pos_of_prev_node: position of the node we want to find the next Hauptsignal for
    :param direction: The direction the train is driving along ("F" or "S")
    :return: id and position of the next 'Hauptsignal' in the given direction.
    In case no 'Hauptsignal' is in the section, id and position of the previous node is returned
    """
    hs_node_id = None
    spurplan_betriebsstellen = parse.get_spurplan_betriebsstelle()
    hs_id = None
    hs_pos = None
    spurplanknoten_id = 0

    for betriebsstelle in spurplan_betriebsstellen:
        spurplan_abschnitte = betriebsstelle.find('Spurplanabschnitte')
        for spurplan_abschnitt in spurplan_abschnitte:
            spurplanknoten_id += 1
            nodes = spurplan_abschnitt.find('Spurplanknoten')

            for node in nodes:
                # If direction is Fallend we save the newest seen Hauptsignal until we reached our target element
                if direction == "F" and node.tag == "HauptsignalF":
                    hs_id = node.find("ID").text
                    hs_pos = get_absolute_kilometrage(node)
                    hs_node_id = spurplanknoten_id
                if node.tag == name_of_prev_node and int(node.find('ID').text) == id_of_prev_node:
                    # If the direction is Fallend  -> return last seen Hauptsignal
                    # If the direction is Steigend -> search for the next occurring Hauptsignal by setting search_hs
                    if direction == "S" and node.tag == "HauptsignalS":
                        # Return the first seen Hauptsignal when search_hs is set to True
                        hs_id = node.find('ID').text
                        hs_pos = get_absolute_kilometrage(node)
                        return hs_id, hs_pos

                    if hs_node_id == spurplanknoten_id:
                        return hs_id, hs_pos

                    # Return previous node id and position if hs_node is not found in spurplanknoten
                    return id_of_prev_node, pos_of_prev_node

def find_prev_fstr(id_of_node, name_of_node, pos_of_node, direction):
    """
    Function to find last 'Hauptsignal' of a journey and return id and position accordingly
    :param id_of_prev_node: id of the node we want to find the next Hauptsignal for
    :param name_of_prev_node: name of the node we want to find the next Hauptsignal for
    :param pos_of_prev_node: position of the node we want to find the next Hauptsignal for
    :param direction: The direction the train is driving along ("F" or "S")
    :return: id and position of the next 'Hauptsignal' in the given direction.
    In case no 'Hauptsignal' is in the section, id and position of the previous node is returned
    """
    fstr_node_id = None
    spurplan_betriebsstellen = parse.get_spurplan_betriebsstellen()
    fstr_id = None
    fstr_pos = None
    spurplanknoten_id = 0

    for betriebsstelle in spurplan_betriebsstellen:
        spurplan_abschnitte = betriebsstelle.find('Spurplanabschnitte')
        for spurplan_abschnitt in spurplan_abschnitte:
            spurplanknoten_id += 1
            nodes = spurplan_abschnitt.find('Spurplanknoten')

            for node in nodes:
                # If direction is Fallend we save the newest seen Hauptsignal until we reached our target element
                if direction == "S" and node.tag in ["FstrZugschlussstelleS", "HauptsignalS"]:
                    fstr_id = node.find("ID").text
                    fstr_pos = get_absolute_kilometrage(node)
                    fstr_node_id = spurplanknoten_id
                if node.tag == name_of_node and int(node.find('ID').text) == id_of_node:
                    # If the direction is Fallend  -> return last seen Hauptsignal
                    # If the direction is Steigend -> search for the next occurring Hauptsignal by setting search_hs
                    if direction == "F" and node.tag in ["HauptsignalF", "FstrZugschlussstelleF"]:
                        # Return the first seen Hauptsignal when search_hs is set to True
                        fstr_id = node.find('ID').text
                        fstr_pos = get_absolute_kilometrage(node)
                        return fstr_id, fstr_pos

                    if fstr_node_id == spurplanknoten_id:
                        return fstr_id, fstr_pos

                    # Return previous node id and position if hs_node is not found in spurplanknoten
                    return id_of_node, pos_of_node


def determine_blocks(nodes, direction, last_fstr_abschnitt_id=None, last_fstr_abschnitt_pos=None):
    """
    :param nodes: ElementTree <Verlauf> containing all elements of a journey
    :param direction: The direction the train is driving along ("F" or "S")
    :return: list of Block dataclass containing all blocks of a journey
    """
    block_index = 0

    temp_blocks = []
    fahrstrassenabschnitte = []
    if last_fstr_abschnitt_id is not None:
        first_id = last_fstr_abschnitt_id
        first_pos = last_fstr_abschnitt_pos
    else:
        if nodes[0].tag != "Weichenanfang":
            first_id, first_pos = find_prev_fstr(int(nodes[0].find('ID').text), nodes[0].tag,
                                                 get_absolute_kilometrage(nodes[0]), direction)
        else:
            first_id, first_pos = find_prev_fstr(int(nodes[1].find('ID').text), nodes[1].tag,
                                                 get_absolute_kilometrage(nodes[1]), direction)

    if last_fstr_abschnitt_id is None:
        if direction == "F":
            if nodes[0].tag != "Weichenanfang":
                first_pos = max(first_pos, get_absolute_kilometrage(nodes[0]))
            else:
                first_pos = max(first_pos, get_absolute_kilometrage(nodes[1]))
        else:
            if nodes[0].tag != "Weichenanfang":
                first_pos = min(first_pos, get_absolute_kilometrage(nodes[0]))
            else:
                first_pos = min(first_pos, get_absolute_kilometrage(nodes[1]))
    fahrstrassenabschnitte.append(Fahrstrassenabschnitt(start_abschnitt_id=first_id, start_abschnitt_pos=first_pos))
    first_block = Block(start_hauptsignal_id=first_id, start_hauptsignal_pos=first_pos)
    temp_blocks.append(first_block)
    temp_blocks.append(Block())
    block_index += 1

    for node in nodes:
        if "Vorsignal" + direction in node.tag:
            id_tag = node.find('ID').text
            pos = get_absolute_kilometrage(node)
            if temp_blocks[block_index].start_hauptsignal_id is not None:
                block = Block(vorsignal_id=id_tag, vorsignal_pos=pos)
                temp_blocks.append(block)
                block_index += 1
            # If after the last occurrence of a Vorsignal no Hauptsignal occurred ->
            # overwrite the Vorsignal with the newest one
            else:
                temp_blocks[block_index].vorsignal_id = id_tag
                temp_blocks[block_index].vorsignal_pos = pos
        elif "Hauptsignal" + direction in node.tag:
            id_tag = node.find('ID').text
            pos = get_absolute_kilometrage(node)
            if temp_blocks[block_index].start_hauptsignal_id == id_tag:
                continue

            temp_blocks[block_index - 1].end_hauptsignal_id = id_tag
            temp_blocks[block_index - 1].end_hauptsignal_pos = pos
            fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].end_abschnitt_id = id_tag
            fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].end_abschnitt_pos = pos
            temp_blocks[block_index - 1].fahrstrassenabschnitte = fahrstrassenabschnitte
            # The end signal of the last block is also the start_signal of the current block
            temp_blocks[block_index].start_hauptsignal_id = id_tag
            temp_blocks[block_index].start_hauptsignal_pos = pos
            block_index += 1
            temp_blocks.append(Block())
            fahrstrassenabschnitte = []
            fahrstrassenabschnitt = Fahrstrassenabschnitt(start_abschnitt_id=id_tag, start_abschnitt_pos=pos)
            fahrstrassenabschnitte.append(fahrstrassenabschnitt)
            last_fstr_id = int(node.find('ID').text)
            last_fstr_pos = get_absolute_kilometrage(node)
        elif "SignalZugschlussstelle" + direction in node.tag:
            id_tag = node.find('ID').text
            pos = get_absolute_kilometrage(node)
            aufloesezeit = float(str.replace(node.find('FstrAufloesezeit').text, ",", "."))
            # SignalZugschlussstelle belongs to the newest "finished" block (both Hauptsignale found)
            if block_index < 2 or temp_blocks[block_index - 2].end_hauptsignal_id is None:
                pass
                # print("Error: Kein fertiger Block")
            elif temp_blocks[block_index - 2].zugschlussstelle_id is not None:
                pass
                # print("Error: Der letzte Block hat schon eine Zugschlussstelle")
            else:
                temp_blocks[block_index - 2].zugschlussstelle_id = id_tag
                temp_blocks[block_index - 2].zugschlussstelle_pos = pos
                temp_blocks[block_index - 2].zugschlussstelle_aufloesezeit = aufloesezeit
        elif "FstrZugschlussstelle" + direction in node.tag:
            if len(fahrstrassenabschnitte) != 0:
                id_tag = node.find('ID').text
                pos = get_absolute_kilometrage(node)
                if fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].start_abschnitt_pos == pos:
                    fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].start_abschnitt_id = id_tag
                    fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].start_abschnitt_pos = pos
                else:
                    fahrstrassenabschnitt = Fahrstrassenabschnitt(start_abschnitt_id=id_tag, start_abschnitt_pos=pos)
                    fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].end_abschnitt_id = id_tag
                    fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].end_abschnitt_pos = pos
                    fahrstrassenabschnitte.append(fahrstrassenabschnitt)
            last_fstr_id = int(node.find('ID').text)
            last_fstr_pos = get_absolute_kilometrage(node)

    fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].end_abschnitt_id = last_fstr_id
    fahrstrassenabschnitte[len(fahrstrassenabschnitte) - 1].end_abschnitt_pos = last_fstr_pos
    blocks = []
    # Remove unfinished blocks that consist only of a Vorsignal for example
    for block in temp_blocks:
        if block.end_hauptsignal_id is not None:
            block.block_id = str(block.start_hauptsignal_id) + '-' + str(block.end_hauptsignal_id)
            if block.start_hauptsignal_id != block.end_hauptsignal_id:
                blocks.append(block)
        else:
            block.end_hauptsignal_id = last_fstr_id
            block.end_hauptsignal_pos = last_fstr_pos
            block.fahrstrassenabschnitte = fahrstrassenabschnitte
            block.block_id = str(block.start_hauptsignal_id) + '-' + str(last_fstr_id)
            blocks.append(block)
            return blocks, last_fstr_id, last_fstr_pos


def calculate_distances(blocks, direction):
    """
    :param blocks: blocks list returned by determine blocks function
    :param direction: The direction the train is driving along ("F" or "S")
    :return blocks list with updated distance attributes
    """
    for block in blocks:
        if block.vorsignal_id is not None:
            distance_a = block.start_hauptsignal_pos - block.vorsignal_pos
        else:
            distance_a = 0

        distance_b = block.end_hauptsignal_pos - block.start_hauptsignal_pos
        if block.zugschlussstelle_id is not None:
            distance_d = block.zugschlussstelle_pos - block.end_hauptsignal_pos
        else:
            distance_d = 0

        # When the direction is Fallend we get negative distances, so we have to multiply them by -1
        if direction == "F":
            distance_a *= -1
            distance_b *= -1
            distance_d *= -1
        # Update attributes
        block.distance_a = distance_a
        block.distance_b = distance_b
        block.distance_d = distance_d
    return blocks


def get_blocks(nodes, direction, last_fstr_id=None, last_fstr_pos=None):
    """
    :param direction: The direction the train is driving along ("F" or "S")
    :return: list of blocks dataclass
    """
    blocks, last_fstr_id, last_fstr_pos = determine_blocks(nodes, direction, last_fstr_id, last_fstr_pos)
    blocks = calculate_distances(blocks, direction)
    return blocks, last_fstr_id, last_fstr_pos
