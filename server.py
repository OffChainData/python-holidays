import os
import holidays
import sys, inspect
from pprint import pprint
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import json


def check_classes():
    """
    Check all classes inside of package and return array
    :return: array
    """

    '''
    These subdivions do not have Code classes that extend HolidayBase so that wont be picked up
    '''
    append = [
        {
            "code": "ENG",
            "name": "England",
            "states" : False,
            "provinces" : False,
            "use_name" : True
        },
        {
            "code": "WLS",
            "name": "Wales",
            "states" : False,
            "provinces" : False,
            "use_name" : True
        },
        {
            "code": "SCT",
            "name": "Scotland",
            "states" : False,
            "provinces" : False,
            "use_name" : True
        },
        {
            "code": "NIR",
            "name": "NorthernIreland",
            "states" : False,
            "provinces" : False,
            "use_name" : True
        },
    ]

    # get all classes from holidays package
    cls_members = inspect.getmembers(sys.modules['holidays'], inspect.isclass)

    inspect_data = []

    for cls in cls_members:

        # check if the first letter of class is Uppercase.
        if cls[0][0].isupper() and not cls[0] == 'HolidayBase':
            # create new object with class
            obj = cls[1]()

            if not obj.__class__.__base__.__name__ == 'HolidayBase':
                continue
            is_provinces = False
            is_states = False

            # check if the object has PROVICES or not
            try:
                if obj.PROVINCES:
                    is_provinces = True
            except:
                pass

            try:
                if obj.STATES:
                    is_states = True
            except:
                pass

            inspect_data.append({
                "name": cls[0],
                "code": obj.country,
                "states": is_states,
                "provinces": is_provinces
            })

    inspect_data = inspect_data + append
    return inspect_data

def get_items(country, year, subdivision_type, subdivisions):
    items = []
    for subdivision in subdivisions:
        state = None
        prov = None
        if subdivision_type == "state":
            state = subdivision
            prov = None
        elif subdivision_type == "prov":           
            state = None
            prov = subdivision


        for ptr in holidays.CountryHoliday(country, state=state, prov=prov, years = year, expand = False).items():
            if (subdivision_type == "none"):
                location = country
            else:
                location = '{0}-{1}'.format(country, subdivision)
            
            items.append(
                {
                    "region" : location,
                    "name" : ptr[1],
                    "date" : ptr[0].isoformat(),
                    "req_year" : year
                }
            )
    return items;                            

def get_holidays(start, end, iso_codes, state = None):
    """
    Return holidays for all locations
    :return: array
    """

    #Location to skip
    skip = [
        'EU'
    ]
    #Countries with know issues with code mappings
    substitute = {
        'FR': 'FRA',
    }
    items = []
    errors = []

    try:
        for country in iso_codes:
            
            if country['code'] in skip:
                continue

            if country['code'] in substitute:
                country['code'] = substitute[country['code']]

            if 'use_name' in country and country['use_name']:
                country['code'] = country['name']

            print("Processing %s" % country['code'])

            for year in range(int(start), int(end) + 1):
                hol = holidays.CountryHoliday(country['code'])
                if country['states']:
                    subdivisions = hol.STATES
                    subdivision_type = 'state'; 
                    
                elif country['provinces']:
                    subdivisions = hol.PROVINCES
                    subdivision_type = 'prov'; 
                else:
                    subdivisions = [0]
                    subdivision_type = 'none'; 


                country_items = get_items(country['code'], year, subdivision_type, subdivisions)
                items = items + country_items
    except:
        errors.append(traceback.format_exc())

    return items, errors

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        #parsed_path = urlparse(self.path)
        parsed_path = urlparse.urlparse(self.path)
        print(parsed_path)
        print(urlparse.parse_qs(parsed_path.query))

        #Get a list of all countries supported by this package
        data = check_classes()
        #Get a list of holidays for all countries
        items, errors = get_holidays(
                        urlparse.parse_qs(parsed_path.query)['start'][0],
                        urlparse.parse_qs(parsed_path.query)['end'][0],
                        data)
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({
            'items': items,
            'errors': errors
        }).encode())
        return

if __name__ == '__main__':
    server = HTTPServer(('', 8000), RequestHandler)
    server.serve_forever()