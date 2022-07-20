"""
Main module example for testing/calling other modules' functionalities
"""
from library.model_trains import get_train_total_length
from library.parser import get_departure_time

from modules.conflict_identification import identify_conflicts
from modules.minimum_headways import write_minimum_headways
from modules.occupancy_times import get_times
from modules.train_pairs import get_relevant_train_pairs
from modules.visualization import visualize_lines

PRINT_OUTPUTS = True

####################################
####### EXAMPLES FOR USAGE #########
####################################

# Getting train length
train_total_length = get_train_total_length("S1")

# Calling occupancy times calculation
vorbelegungszeiten, driving_times, nachbelegungszeiten, belegungszeiten, blocks \
    = get_times("S1 1112")
if PRINT_OUTPUTS:
    print(f'Train Length: {train_total_length}')
    print("abfahrt : ", get_departure_time("S1", "1112"))
    print(vorbelegungszeiten, driving_times, nachbelegungszeiten, belegungszeiten, blocks)

# Calling visualization
lines_to_plot = ["S1", "S2"]
visualize_lines(lines_to_plot, plot_one_dir_only=True, plot_first_journey_only=False, dir_to_plot=0,
                end_time="2020-07-22T09:35:00.000000")

# Calling minimum headway generation of all XML files
# write_minimum_headways()

# Calling relevant train pairs
relevant_train_pairs = get_relevant_train_pairs()

# Calling conflict identification
identify_conflicts(relevant_train_pairs)

####################################

if PRINT_OUTPUTS:  # Outputs in the console
    print(f'Train Length: {train_total_length}')
    print("abfahrt : ", get_departure_time("S1", "1112"))
    print(vorbelegungszeiten, driving_times, nachbelegungszeiten, belegungszeiten, blocks)
