import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import string
import sys

osm_file = open("../minneapolis-saint-paul_minnesota.osm", "r")

amenity_dirty_counts = defaultdict(int)
amenity_clean_counts = defaultdict(int)


def audit_amenity(counts, amenity):
    if counts.has_key(amenity):
        counts[amenity] = counts.get(amenity) + 1
    else:
        counts[amenity] = 1


def clean_amenity(amenity):
    # Perform general string cleanup first.  Replace blanks with underscores...
    # https://wiki.openstreetmap.org/wiki/Key:amenity
    amenity = amenity.strip().replace(' ','_')

    # Fix observed typos...
    if amenity == 'community_center':
        amenity = 'community_centre'
    elif amenity == 'parking_enterance':
        amenity = 'parking_entrance'

    return amenity


def is_amenity_element(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "amenity")


def perform_work(audit_flag=True, clean_flag=False):
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way" or elem.tag == "relation":
            for tag in elem.iter("tag"):
                if is_amenity_element(tag):
                    amenity = tag.attrib['v']

                    if audit_flag:
                        audit_amenity(amenity_dirty_counts, amenity)

                    if clean_flag:
                        amenity = clean_amenity(amenity)
                        audit_amenity(amenity_clean_counts, amenity)

    if audit_flag:
        pprint.pprint(dict(amenity_dirty_counts))

    if clean_flag:
        pprint.pprint(dict(amenity_clean_counts))


if __name__ == '__main__':
    count = len(sys.argv) - 1
    valid = True

    if count == 0:
        perform_work()

    elif count == 1:
        if sys.argv[1] == 'audit':
            perform_work()

        elif sys.argv[1] == 'clean':
            perform_work(False, True)

        else:
            valid = False

    else:
        valid = False

    if not valid:
        print 'Unexpected arguments.  Exiting...'
        exit()
