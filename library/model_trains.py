"""
module to retrieve train characteristics from given excel file in resources
"""
from os import path
from pathlib import Path

import pandas as pd

package_dir = path.dirname(Path(__file__).parent)
path_model_trains = path.join(package_dir, Path('resources/trains/Model_Trains.xlsx'))


def get_model_train_data(with_sheet_name, with_columns):
    """
    Function to get specified src-trains sheet as a complete data frame
    :param with_sheet_name: sheet name of .xlsx/.xls file
    :param with_columns: columns to retrieve from file
    :return: pandas.core.frame.DataFrame type
    """
    data_frame = pd.read_excel(path_model_trains, sheet_name=with_sheet_name, usecols=with_columns)
    return data_frame


def get_train_total_length(with_line_name):
    """
    Function to extract total train length from src trains
    :param with_line_name: line name of train
    :return: .2f precision float, total length of train on given line
    """
    model_train = pd.ExcelFile(path_model_trains)
    total_length = None

    for sheet in model_train.sheet_names:
        data_frame = pd.read_excel(path_model_trains, sheet_name=sheet, usecols=['Linien', 'Total lz [m]'],
                                   na_values=None)
        mask = data_frame['Linien'].eq(with_line_name.upper())
        found_frame = data_frame.loc[mask]
        if not found_frame.empty:
            found_value = (found_frame['Total lz [m]']).values
            total_length = float(format(found_value[0], '.4f'))

    return total_length
