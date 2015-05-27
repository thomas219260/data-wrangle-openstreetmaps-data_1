Each of the subdirectories contains code I used to test the
audit and cleaning of the individual field indicated by the
name of the subdirectory:

AMENITY
CITIES
CUISINE
DENOMINATION
PHONES
POSTCODES
STREETS

Each subdirectory contain a single python program with some
"dirty" and "clean" output files.  Each python program contains
a clean_xyz function that implements the cleaning logic.

Each of those clean_xyz functions was copied into my final
data.py program, which was then used to process the *.osm
dataset...
