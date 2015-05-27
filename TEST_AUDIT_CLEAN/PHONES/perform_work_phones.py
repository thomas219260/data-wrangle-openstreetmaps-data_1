import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint
import re
import string
import sys

osm_file = open("minneapolis-saint-paul_minnesota.osm", "r")

phone_dirty_counts = defaultdict(int)
phone_clean_counts = defaultdict(int)


def audit_phone(counts, phone):
    if counts.has_key(phone):
        counts[phone] = counts.get(phone) + 1
    else:
        counts[phone] = 1


def clean_phone(phone):
    save_phone = phone

    # Fix observed typos...
    if phone == '+1651762948':
         phone = '(651) 348-7571'                   # Casa Lupita
    elif phone == '+1612823289':
        phone = '(612) 823-5289'                    # Guse Green Grocer
    elif phone == '52-476-1717':
        phone = '(952) 476-1717'                    # Life Time Athletic
    elif phone == '+1 1-612-379-7669':
        phone = '(612) 379-7669'                    # Magus Books & Herbs

    # Fix observed cases of multiple phones by keeping just the local number.
    if phone == 'Toll Free: 800.473.4934 Main: 952.985.7200':
        phone = '(952) 985-7200'                    # Verified Credentials, Inc.
    elif phone == '+16123312127, +18007889808':
        phone = '(612) 331-2127'                    # Teleflora

    # Fix one observed "too long" vanity number...
    if phone == '800-rent-a-car':
        phone = '(800) 736-8222'                    # Enterprise

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

    #if phone != save_phone:
    #    print 'Replacing "{}" with "{}"'.format(save_phone, phone)

    return phone


def is_phone_element(elem):
    return (elem.tag == "tag") and (re.compile('phone').search(elem.attrib['k']))


def perform_work(audit_flag=True, clean_flag=False):
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way" or elem.tag == "relation":
            for tag in elem.iter("tag"):
                if is_phone_element(tag):
                    phone = tag.attrib['v']

                    if audit_flag:
                        audit_phone(phone_dirty_counts, phone)

                    if clean_flag:
                        phone = clean_phone(phone)
                        audit_phone(phone_clean_counts, phone)

    if audit_flag:
        pprint.pprint(dict(phone_dirty_counts))

    if clean_flag:
        pprint.pprint(dict(phone_clean_counts))


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
