import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import string
import sys

osm_file = open("../minneapolis-saint-paul_minnesota.osm", "r")

denomination_dirty_counts = defaultdict(int)
denomination_clean_counts = defaultdict(int)


def audit_denomination(counts, denomination):
    if counts.has_key(denomination):
        counts[denomination] = counts.get(denomination) + 1
    else:
        counts[denomination] = 1


def clean_denomination(denomination):
    # Perform general string cleanup first.  Replace blanks with underscores...
    # https://wiki.openstreetmap.org/wiki/Key:denomination
    denomination = denomination.strip().replace(' ','_')

    # Fix observed typos...
    if denomination == 'Non_Denominational' or denomination == 'non-denominational':
        denomination = 'nondenominational'
    elif denomination == 'reform':
        denomination = 'reformed'

    return denomination.lower()


def is_denomination_element(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "denomination")


def perform_work(audit_flag=True, clean_flag=False):
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way" or elem.tag == "relation":
            for tag in elem.iter("tag"):
                if is_denomination_element(tag):
                    denomination = tag.attrib['v']

                    if audit_flag:
                        audit_denomination(denomination_dirty_counts, denomination)

                    if clean_flag:
                        denomination = clean_denomination(denomination)
                        audit_denomination(denomination_clean_counts, denomination)

    if audit_flag:
        pprint.pprint(dict(denomination_dirty_counts))

    if clean_flag:
        pprint.pprint(dict(denomination_clean_counts))


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
