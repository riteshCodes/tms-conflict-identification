"""
Utilities module to cope with schedule file and its characteristics
"""
import xml.etree.ElementTree

from library.parser import get_spurplan_betriebsstellen

BETRIEBSSTELLEN = get_spurplan_betriebsstellen()


def determine_direction(verlauf_node: xml.etree.ElementTree.ElementTree):
    """
    Takes a tree containing all Elements/nodes of <Verlauf>

    :param verlauf_node: node containing <Verlauf>
    :return: Returns driving direction of the train
    """
    i = 1
    diff = 0
    signal_list = [signals_verlauf for signals_verlauf in verlauf_node]
    while diff == 0:
        diff = get_absolute_kilometrage(signal_list[i]) - get_absolute_kilometrage(signal_list[i - 1])
        i += 1

    return 'S' if diff > 0 else 'F'
    # return Direction.STEIGEND if diff > 0 else Direction.FALLEND


def direction_of_node(node: xml.etree.ElementTree.ElementTree) -> str:
    """
    Takes a node, returns the direction that the node is relevant for.

    :param node: The node in question.
    :return: returns the direction that the node is relevant for
    """
    return node.tag[len(node.tag) - 1:]


def get_absolute_kilometrage(node: xml.etree.ElementTree.ElementTree):
    """
    returns an absolute kilometrage for sections that are not on the mainline

    :param node: The node for which to get the kilometrage
    :return: the kilometrage of that node
    """
    node_kilometrage = float(str.replace(node.find('Kilometrierung').text, ",", "."))
    if is_on_section_one(node):
        node_kilometrage = node_kilometrage + 11.67
    elif is_on_section_two(node):
        node_kilometrage = 28.499 - node_kilometrage
    return node_kilometrage


def is_on_section_one(node: xml.etree.ElementTree.ElementTree):
    """
    checks if a node is on the first section outside the mainline

    :param node: the node in question
    :return: true if on the first section
    """
    node_id = int(node.find('ID').text)
    return 73 >= node_id >= 66 or node_id == 26


def is_on_section_two(node: xml.etree.ElementTree.ElementTree):
    """
    checks if a node is on the second section outside the mainline

    :param node: the node in question
    :return: true if on the second section
    """
    node_id = int(node.find('ID').text)
    condition_section_two = (
            168 <= node_id <= 170 or node_id == 175 or 217 <= node_id <= 223 or node_id == 250 or 263 <= node_id <= 268 or node_id == 270 or 282 <= node_id <= 287 or node_id == 297 or 299 <= node_id <= 305 or node_id == 328 or 330 <= node_id <= 331 or 353 <= node_id <= 358 or node_id == 360 or 382 <= node_id <= 385 or node_id == 397)

    return condition_section_two


def find_node_by_id(node_id: int) -> xml.etree.ElementTree.ElementTree:
    """

    :param node_id: The id parameter of the node.
    :return: The node element with the id.
    """
    for betriebsstelle in BETRIEBSSTELLEN:
        spurplan_abschnitte = betriebsstelle[1]
        for spurplan_abschnitt in spurplan_abschnitte:
            spurplan_knoten = spurplan_abschnitt[1]
            for node in spurplan_knoten:
                if node.find('ID').text == node_id:
                    return node
    return None
