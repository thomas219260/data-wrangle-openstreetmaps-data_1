import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import string
import sys

osm_file = open("minneapolis-saint-paul_minnesota.osm", "r")

city_dirty_counts = defaultdict(int)
city_clean_counts = defaultdict(int)


def audit_city(counts, city):
    if counts.has_key(city):
        counts[city] = counts.get(city) + 1
    else:
        counts[city] = 1


def clean_city(city):
    save_city = city

    # Perform general string cleanup first, including removal of all periods...
    city = city.strip().replace('.','')

    # Fix observed typos:
    if city == 'Inver Grove':
        city = 'Inver Grove Heights'
    elif city == 'Saint Pal':
        city = 'St Paul'

    # Assure that the first letter of each word is capitalized and that the
    # remaining letters are not...
    city = string.capwords(city, ' ')

    # Strip off the abbreviation or full state name from the end of the city
    # name...
    city = re.compile(', MN$|, Minnesota$', re.IGNORECASE).sub('', city)
    
    # Convert 'Saint' to its canonical form...
    city = re.compile(r'\bSaint\b', re.IGNORECASE).sub('St', city)

    #if city != save_city:
    #    print 'Replacing "{}" with "{}"'.format(save_city, city)

    return city


def is_city_element(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "addr:city")


def perform_work(audit_flag=True, clean_flag=False):
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way" or elem.tag == "relation":
            for tag in elem.iter("tag"):
                if is_city_element(tag):
                    city = tag.attrib['v']

                    if audit_flag:
                        audit_city(city_dirty_counts, city)

                    if clean_flag:
                        city = clean_city(city)
                        audit_city(city_clean_counts, city)

    if audit_flag:
        pprint.pprint(dict(city_dirty_counts))

    if clean_flag:
        pprint.pprint(dict(city_clean_counts))


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
