"""
Module with 'dweg' values for train journey, with respect to train speed at the railway-track.
"""


def get_d_weg(speed):
    """
    Function to return d_weg with respect to given speed of src train
    :param speed: driving speed of train in station according to schedule
    :return: d_weg for src trains
    """
    if speed <= 30:
        return 0
    if 30 < speed <= 40:
        return 50
    if 40 < speed <= 60:
        return 100
    if speed > 60:
        return 200
