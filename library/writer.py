"""
Library module for writing files in xml
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom


def write_et(et, path):
    data = ET.tostring(et, 'utf-8')
    dom = minidom.parseString(data)
    pretty_data = dom.toprettyxml(indent='  ')
    with open(path, 'w') as occupancy_times_file:
        occupancy_times_file.write(pretty_data)
