import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import string
import sys

osm_file = open("../minneapolis-saint-paul_minnesota.osm", "r")

street_dirty_counts = defaultdict(int)
street_clean_counts = defaultdict(int)

word_dirty_counts = defaultdict(int)
word_clean_counts = defaultdict(int)

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_types = defaultdict(set)

expected = []
expected.append("Avenue")
expected.append("Bay")
expected.append("Boulevard")
expected.append("Center")
expected.append("Circle")
expected.append("Commons")
expected.append("Court")
expected.append("Crossing")
expected.append("Curve")
expected.append("Drive")
expected.append("Freeway")
expected.append("Galleria")
expected.append("Highway")
expected.append("Knoll")
expected.append("Lane")
expected.append("Mainstreet")
expected.append("Parkway")
expected.append("Path")
expected.append("Place")
expected.append("Plaza")
expected.append("Road")
expected.append("Spur")
expected.append("Square")
expected.append("Street")
expected.append("Terrace")
expected.append("Trail")
expected.append("Vista")
expected.append("Way")

# No Change:
# Blaine Pet Area Hospital              # miscoded
# East Broadway                         # Mall of America, Bloomington (1)
# Galleria                              # Edina (1)
# Nicollet Mall                         # Minneapolis (1)
# Pierce Butler Route                   # St Paul (1)
# Washington Avenue Bridge              # U of MN campus (1)


def gather_types(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def audit_street(counts, word_counts, street):
    if counts.has_key(street):
        counts[street] = counts.get(street) + 1
    else:
        counts[street] = 1

    for word in street.split(' '):
        if word_counts.has_key(word):
            word_counts[word] = word_counts.get(word) + 1
        else:
            word_counts[word] = 1


def clean_street(street):
    save_street = street

    # Perform general string cleanup first, including removal of all periods...
    street = street.strip().replace('`', '').replace(',','').replace('.','')

    # Convert multiple spaces to a single space...
    street = re.compile('  *', re.IGNORECASE).sub(' ', street)

    # Fix observed typos...
    street = street.replace('Bennet Dr', 'Bennett Dr')
    street = street.replace('Boulivard', 'Blvd')
    street = street.replace('Country Road', 'County Rd')
    street = street.replace('Mc Callum Dr', 'McCallum Dr')
    street = street.replace('Rahn Cliff Court', 'Rahncliff Ct')
    street = street.replace('Sreet', 'St')
    street = street.replace('Street Court', 'St')
    street = street.replace('Unviersity', 'University')
    street = street.replace('Wahington', 'Washington')
    street = street.replace('Wayzeta', 'Wayzata')
    street = street.replace('Yellow Cicle Dr', 'Yellow Cir Dr')

    # Fix observed cases of missing street types...
    street = re.compile('^Arkwright$', re.IGNORECASE).sub('Arkwright St', street)
    street = re.compile('^Maryland$', re.IGNORECASE).sub('Maryland Ave E', street)
    street = re.compile('^Roth$', re.IGNORECASE).sub('Roth Pl', street)
    street = re.compile('^St Peter$', re.IGNORECASE).sub('St Peter St', street)
    street = re.compile('^West Broadway$', re.IGNORECASE).sub('West Broadway Ave', street)

    # Expand observed cases of one abbreviation...
    street = re.compile(r'\bCR\b', re.IGNORECASE).sub('County Rd', street)

    # Convert points of the compass to their canonical forms.  Here, temporary
    # forms are used for the diagonal points, to avoid a conflict with the
    # invocation of "capwords" in the next step...
    street = re.compile(r'\bNortheast\b|\bNE\b', re.IGNORECASE).sub('N E', street)
    street = re.compile(r'\bNorthwest\b|\bNW\b', re.IGNORECASE).sub('N W', street)
    street = re.compile(r'\bSoutheast\b|\bSE\b', re.IGNORECASE).sub('S E', street)
    street = re.compile(r'\bSouthwest\b|\bSW\b', re.IGNORECASE).sub('S W', street)
    street = re.compile(r'\bNorth\b', re.IGNORECASE).sub('N', street)
    street = re.compile(r'\bSouth\b', re.IGNORECASE).sub('S', street)
    street = re.compile(r'\bEast\b', re.IGNORECASE).sub('E', street)
    street = re.compile(r'\bWest\b', re.IGNORECASE).sub('W', street)

    # Assure that the first letter of each word is capitalized and that the
    # remaining letters are not...
    street = string.capwords(street, ' ')

    # After the "capwords" invocation, convert the diagonal points to their
    # final canonical forms...
    street = re.compile(r'\bN E\b', re.IGNORECASE).sub('NE', street)
    street = re.compile(r'\bN W\b', re.IGNORECASE).sub('NW', street)
    street = re.compile(r'\bS E\b', re.IGNORECASE).sub('SE', street)
    street = re.compile(r'\bS W\b', re.IGNORECASE).sub('SW', street)

    # The invocation of "capwords" above "broke" several street names which
    # correctly contain one or more capital letters.  Fix those observed cases
    # now...
    street = re.compile(r'\bIkea\b', re.IGNORECASE).sub('IKEA', street)
    street = re.compile(r'\bLabeaux\b', re.IGNORECASE).sub('LaBeaux', street)
    street = re.compile(r'\bMarketpointe\b', re.IGNORECASE).sub('MarketPointe', street)
    street = re.compile(r'\bMcandrews\b', re.IGNORECASE).sub('McAndrews', street)
    street = re.compile(r'\bMccallum\b', re.IGNORECASE).sub('McCallum', street)
    street = re.compile(r'\bMccarrons\b', re.IGNORECASE).sub('McCarrons', street)
    street = re.compile(r'\bMcginty\b', re.IGNORECASE).sub('McGinty', street)
    street = re.compile(r'\bMckusick\b', re.IGNORECASE).sub('McKusick', street)
    street = re.compile(r'\bMn\b', re.IGNORECASE).sub('MN', street)
    street = re.compile(r'\bO\'leary\b', re.IGNORECASE).sub('O\'Leary', street)

    # Convert street types to their canonical forms...
    street = re.compile(r'\bAvenue\b|\bAv\b', re.IGNORECASE).sub('Ave', street)
    street = re.compile(r'\bBoulevard\b', re.IGNORECASE).sub('Blvd', street)
    street = re.compile(r'\bCircle\b', re.IGNORECASE).sub('Cir', street)
    street = re.compile(r'\bCourt\b', re.IGNORECASE).sub('Ct', street)
    street = re.compile(r'\bDrive\b', re.IGNORECASE).sub('Dr', street)
    street = re.compile(r'\bHighway\b', re.IGNORECASE).sub('Hwy', street)
    street = re.compile(r'\bLane\b', re.IGNORECASE).sub('Ln', street)
    street = re.compile(r'\bParkway\b|\bPky\b', re.IGNORECASE).sub('Pkwy', street)
    street = re.compile(r'\bPlace\b', re.IGNORECASE).sub('Pl', street)
    street = re.compile(r'\bRoad\b', re.IGNORECASE).sub('Rd', street)
    street = re.compile(r'\bStreet\b', re.IGNORECASE).sub('St', street)
    street = re.compile(r'\bTrail\b', re.IGNORECASE).sub('Trl', street)
    street = re.compile(r'\bTerrace\b', re.IGNORECASE).sub('Ter', street)

    # Convert ordinal names to their canonical forms...
    street = re.compile(r'\bFirst\b', re.IGNORECASE).sub('1st', street)
    street = re.compile(r'\bSecond\b', re.IGNORECASE).sub('2nd', street)
    street = re.compile(r'\bThird\b', re.IGNORECASE).sub('3rd', street)
    street = re.compile(r'\bFourth\b', re.IGNORECASE).sub('4th', street)
    street = re.compile(r'\bFifth\b', re.IGNORECASE).sub('5th', street)
    street = re.compile(r'\bSixth\b', re.IGNORECASE).sub('6th', street)
    street = re.compile(r'\bSeventh\b', re.IGNORECASE).sub('7th', street)
    street = re.compile(r'\bEighth\b', re.IGNORECASE).sub('8th', street)
    street = re.compile(r'\bNinth\b', re.IGNORECASE).sub('9th', street)
    street = re.compile(r'\bTenth\b', re.IGNORECASE).sub('10th', street)
    street = re.compile(r'\bEleventh\b', re.IGNORECASE).sub('11th', street)
    street = re.compile(r'\bTwelfth\b', re.IGNORECASE).sub('12th', street)
    street = re.compile(r'\bThirteenth\b', re.IGNORECASE).sub('13th', street)
    street = re.compile(r'\bFourteenth\b', re.IGNORECASE).sub('14th', street)
    street = re.compile(r'\bFifteenth\b', re.IGNORECASE).sub('15th', street)
    street = re.compile(r'\bSixteenth\b', re.IGNORECASE).sub('16th', street)
    street = re.compile(r'\bSeventeenth\b', re.IGNORECASE).sub('17th', street)
    street = re.compile(r'\bEighteenth\b', re.IGNORECASE).sub('18th', street)
    street = re.compile(r'\bNineteenth\b', re.IGNORECASE).sub('19th', street)
    street = re.compile(r'\bTwentieth\b', re.IGNORECASE).sub('20th', street)

    # Convert 'Saint' to its canonical form...
    street = re.compile(r'\bSaint\b', re.IGNORECASE).sub('St', street)

    # Move compass points from beginning to end of the string...
    for compass_point in [ 'N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SE' ]:
        pattern = re.compile('^' + compass_point + ' ')
        if pattern.match(street):
            street = pattern.sub('', street) + ' ' + compass_point

    #if street != save_street:
    #    print 'Replacing "{}" with "{}"'.format(save_street, street)

    return street


def is_street_element(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "addr:street")


def perform_work(gather_flag=True, audit_flag=False, clean_flag=False):
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way" or elem.tag == "relation":
            for tag in elem.iter("tag"):
                if is_street_element(tag):
                    street = tag.attrib['v']

                    if gather_flag:
                        gather_types(street_types, street)

                    elif audit_flag:
                        audit_street(street_dirty_counts, word_dirty_counts, street)

                    elif clean_flag:
                        street = clean_street(street)
                        audit_street(street_clean_counts, word_clean_counts, street)
                        
    if gather_flag:
        pprint.pprint(dict(street_types))

    elif audit_flag:
        pprint.pprint(dict(street_dirty_counts))
        pprint.pprint(dict(word_dirty_counts))
        
    elif clean_flag:
        pprint.pprint(dict(street_clean_counts))
        pprint.pprint(dict(word_clean_counts))


if __name__ == '__main__':
    count = len(sys.argv) - 1
    valid = True

    if count == 0:
        perform_work()

    elif count == 1:
        if sys.argv[1] == 'gather':
            perform_work()

        elif sys.argv[1] == 'audit':
            perform_work(False, True, False)

        elif sys.argv[1] == 'clean':
            perform_work(False, False, True)

        else:
            valid = False

    else:
        valid = False

    if not valid:
        print 'Unexpected arguments.  Exiting...'
        exit()
