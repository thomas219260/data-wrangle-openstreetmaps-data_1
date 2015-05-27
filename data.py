#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET

import codecs
import json
import pprint
import re
import string

# ==============================================================================
# 
# My wrangling and transforming of the model data follows the requirements
# given in the last exercise of the last lesson, but with two deviations.
#
# First, to avoid colliding with tag elements with k="type" seen in my model
# data, I'm using osm_type instead of type to distinguish between nodes and
# ways.
#
# Second, to work correctly with the geospatial queries, I'm storing lon and
# lat (in that order) in the pos array, rather than lat and lon.
#
# ==============================================================================

"""
Your task is to wrangle the data and transform the shape of the data
into the model we mentioned earlier. The output should be a list of dictionaries
that look like this:

{
"id": "2406124091",
"type: "node",                                       # TPW: Here, I'm using osm_type...
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],                    # TPW: Here, I'm storing lon and lat...
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}

You have to complete the function 'shape_element'.
We have provided a function that will parse the map file, and call the function with the element
as an argument. You should return a dictionary, containing the shaped data for that element.
We have also provided a way to save the data in a file, so that you could use
mongoimport later on to import the shaped data into MongoDB. 

Note that in this exercise we do not use the 'update street name' procedures
you worked on in the previous exercise. If you are using this code in your final
project, you are strongly encouraged to use the code from previous exercise to 
update the street names before you save them to JSON. 

In particular the following things should be done:
- you should process only 2 types of top level tags: "node" and "way"
- all attributes of "node" and "way" should be turned into regular key/value pairs, except:
    - attributes in the CREATED array should be added under a key "created"
    - attributes for latitude and longitude should be added to a "pos" array,
      for use in geospacial indexing. Make sure the values inside "pos" array are floats
      and not strings. 
- if second level tag "k" value contains problematic characters, it should be ignored
- if second level tag "k" value starts with "addr:", it should be added to a dictionary "address"
- if second level tag "k" value does not start with "addr:", but contains ":", you can process it
  same as any other tag.
- if there is a second ":" that separates the type/direction of a street,
  the tag should be ignored, for example:

<tag k="addr:housenumber" v="5158"/>
<tag k="addr:street" v="North Lincoln Avenue"/>
<tag k="addr:street:name" v="Lincoln"/>
<tag k="addr:street:prefix" v="North"/>
<tag k="addr:street:type" v="Avenue"/>
<tag k="amenity" v="pharmacy"/>

  should be turned into:

{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}

- for "way" specifically:

  <nd ref="305896090"/>
  <nd ref="1719825889"/>

should be turned into
"node_refs": ["305896090", "1719825889"]
"""

osm_file = "minneapolis-saint-paul_minnesota.osm"

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def process_attributes(node, element):
    # Use 'osm_type' here to avoid colliding with tag elements with k="type"...
    node['osm_type'] = element.tag

    created = {}
    pos_lat = 0.0
    pos_lon = 0.0

    for k, v in element.attrib.iteritems():
        if k in CREATED:
            created[k] = v

        elif k == 'lat':
            if is_number(v):
                pos_lat = float(v)

        elif k == 'lon':
            if is_number(v):
                pos_lon = float(v)

        else:
            node[k] = v

        
    if created != {}:
        node['created'] = created

    if element.tag == 'node':
        # To support "near" searches, specify coordinates in this order:
        # longitude, latitude...
        # http://docs.mongodb.org/manual/reference/operator/query/near/

        # node['pos'] = [ pos_lat, pos_lon ]
        node['pos'] = [ pos_lon, pos_lat ]

    return node


def clean_city(city):
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

    return city


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


def clean_phone(phone):
    # Handle the observed cases of multiple phones up front and return.
    # Note that this method return an array...
    if phone == 'Toll Free: 800.473.4934 Main: 952.985.7200':
        return [ '(800) 473 4934', '(952) 985-7200' ]   # Verified Credentials, Inc.

    elif phone == '+16123312127, +18007889808':
        return [ '(612) 331-2127', '(800) 788-9808']    # Teleflora

    # Fix observed typos...
    if phone == '+1651762948':
        phone = '(651) 348-7571'                       # Casa Lupita
    elif phone == '+1612823289':
        phone = '(612) 823-5289'                        # Guse Green Grocer
    elif phone == '52-476-1717':
        phone = '(952) 476-1717'                        # Life Time Athletic
    elif phone == '+1 1-612-379-7669':
        phone = '(612) 379-7669'                        # Magus Books & Herbs

    # Fix one observed "too long" vanity number...
    if phone == '800-rent-a-car':
        phone = '(800) 736-8222'                        # Enterprise

    # Perform general string cleanup...
    for ch in [' ', '+', '-', '.', '(', ')', '/']:
        phone = phone.replace(ch,'')

    # If phone begins with a 1, strip it off...
    if re.compile('^1').match(phone):
        phone = phone[1:]

    # Fix the remaining vanity numbers.  However, skip one observed entry
    # for k = 'communication:mobile_phone', v = 'yes'...
    if phone != 'yes':
        phone = re.compile('[ABC]', re.IGNORECASE).sub('2', phone)
        phone = re.compile('[DEF]', re.IGNORECASE).sub('3', phone)
        phone = re.compile('[GHI]', re.IGNORECASE).sub('4', phone)
        phone = re.compile('[JKL]', re.IGNORECASE).sub('5', phone)
        phone = re.compile('[MNO]', re.IGNORECASE).sub('6', phone)
        phone = re.compile('[PQRS]', re.IGNORECASE).sub('7', phone)
        phone = re.compile('[TUV]', re.IGNORECASE).sub('8', phone)
        phone = re.compile('[WXYZ]', re.IGNORECASE).sub('9', phone)

    # If phone format is valid, then convert to canonical form...
    if re.compile('^\d{10}$').match(phone):
        phone = '(' + phone[0:3] + ') ' + phone[3:6] + '-' + phone[6:10]

    # Return an array...
    return [phone]


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


def process_tag_tags(node, element):
    address = {}

    for tag in element.iter('tag'):
        k = tag.attrib['k']
        v = tag.attrib['v']

        if problemchars.search(k):
            continue

        if k.startswith('addr:'):
            k_array = k.split(':')

            if len(k_array) > 2:
                continue

            if k == 'addr:city':
                v = clean_city(v)

            elif k == 'addr:street':
                v = clean_street(v)

            address[k_array[1]] = v

        elif re.compile('phone').search(k) and v != 'yes':
            # Append 's' to the key and store the returned array...
            node[k + 's'] = clean_phone(v)

        elif k == 'amenity':
            node[k] = clean_amenity(v)

        elif k == 'cuisine':
            node[k] = clean_cuisine(v)

        elif k == 'denomination':
            node[k] = clean_denomination(v)

        else:
            node[k] = v

    if address != {}:
        node['address'] = address
        
    return node


def clean_node(node):
    # This function performs some "post processing" cleaning on the node
    # itself to correct some observed problems spanning across individual
    # fields.  Two examples are a street field containing an entire address
    # and postcode fields containing house numbers...

    if not node.has_key('address'):
        return node

    address = node['address']

    if address.has_key('street'):
        street = address['street']
        if street == '2600 44th Ave N Minneapolis MN 55412':
            address['housenumber'] = '2600'
            address['street'] = '44th Ave N'
            address['city'] = 'Minneapolis'
            address['state'] = 'MN'
            address['postcode'] = '55412'

    if address.has_key('postcode'):
        postcode = address['postcode']

        pattern = re.compile('^\d{5}(?:-\d{4})?$')

        # If the postcode's format is valid, then we're done...
        if pattern.match(postcode):
            return node

        # Otherwise, fix the observed cases of invalid postcodes by updating several
        # fields in the address document.  In most cases, the postcode field
        # originally contained the housecode value...

        # Correct address is: 100 3rd Ave S, Minneapolis, MN 55401
        if postcode == '100':
            address['housenumber'] = '100'
            address['street'] = '3rd Ave S'
            address['city'] = 'Minneapolis'
            address['state'] = 'MN'
            address['postcode'] = '55401'

        # Correct address is: 211 Sargent Dr, Red Wing, MN 55066
        elif postcode == '211':
            address['housenumber'] = '211'
            address['street'] = 'Sargent Dr'
            address['city'] = 'Red Wing'
            address['state'] = 'MN'
            address['postcode'] = '55066'

        # Correct address is: 2418 University Ave W, St Paul, MN 55114
        elif postcode == '5114': 
            address['housenumber'] = '2418'
            address['street'] = 'University Ave W'
            address['city'] = 'St Paul'
            address['state'] = 'MN'
            address['postcode'] = '55114'

        # Correct address is: 822 W 98th St, Minneapolis, MN 55420
        elif postcode == '822':
            address['housenumber'] = '822'
            address['street'] = 'W 98th St'
            address['city'] = 'Minneapolis'
            address['state'] = 'MN'
            address['postcode'] = '55420'

        # Correct address is: 3021 Holmes Ave S, Minneapolis, MN 55408
        elif postcode == 'MN':
            address['housenumber'] = '3021'
            address['street'] = 'Holmes Ave S'
            address['city'] = 'Minneapolis'
            address['state'] = 'MN'
            address['postcode'] = '55408'

        # Correct address is: 1760 University Ave SE, Minneapolis, MN 55455
        # http://www1.umn.edu/pts/park/facilities/ebl.html#c39
        elif postcode == 'Pillsbury Dr':
            address['housenumber'] = '1760'
            address['street'] = 'University Ave SE'
            address['city'] = 'Minneapolis'
            address['state'] = 'MN'
            address['postcode'] = '55455'

    return node


def process_nd_tags(node, element):
    node_refs = []

    for tag in element.iter('nd'):
        node_refs.append(tag.attrib['ref'])

    node['node_refs'] = node_refs
    
    return node

        
def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        # YOUR CODE HERE
        node = process_attributes(node, element)
        node = process_tag_tags(node, element)

        if element.tag == "way":
            process_nd_tags(node, element)
            
        # Perform "post processing" on the node document...
        node = clean_node(node)
        
        return node

    else:
        return None


def process_map(file_in, pretty = False):
    # You do not need to change this file
    # file_out = "{0}.json".format(file_in)
    file_out = "data.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def test():
    # NOTE: if you are running this code on your computer, with a larger dataset, 
    # call the process_map procedure with pretty=False. The pretty=True option adds 
    # additional spaces to the output, making it significantly larger.

    data = process_map(osm_file, True)

if __name__ == "__main__":
    test()
