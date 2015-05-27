import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import string
import sys

osm_file = open("../minneapolis-saint-paul_minnesota.osm", "r")

cuisine_dirty_counts = defaultdict(int)
cuisine_clean_counts = defaultdict(int)


def audit_cuisine(counts, cuisine):
    if counts.has_key(cuisine):
        counts[cuisine] = counts.get(cuisine) + 1
    else:
        counts[cuisine] = 1


def clean_cuisine(cuisine):
    # Perform general string cleanup first...
    # https://wiki.openstreetmap.org/wiki/Key:cuisine
    cuisine = cuisine.strip()

    # Remove any terminating underscores or periods...
    cuisine = re.compile('_$', re.IGNORECASE).sub('', cuisine)
    cuisine = re.compile('\.$', re.IGNORECASE).sub('', cuisine)

    # Fix one observed irregular string...
    cuisine = cuisine.replace(',_','_')

    # Fix observed typos...
    if cuisine == 'Bar-B-Q' or cuisine == 'Bar-B-Que' or cuisine == 'Barbeque' or cuisine == 'barbeque':
        cuisine = 'barbecue'

    return cuisine.lower()


def is_cuisine_element(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "cuisine")


def perform_work(audit_flag=True, clean_flag=False):
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way" or elem.tag == "relation":
            for tag in elem.iter("tag"):
                if is_cuisine_element(tag):
                    cuisine = tag.attrib['v']

                    if audit_flag:
                        audit_cuisine(cuisine_dirty_counts, cuisine)

                    if clean_flag:
                        cuisine = clean_cuisine(cuisine)
                        audit_cuisine(cuisine_clean_counts, cuisine)

    if audit_flag:
        pprint.pprint(dict(cuisine_dirty_counts))

    if clean_flag:
        pprint.pprint(dict(cuisine_clean_counts))


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
