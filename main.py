import requests
import time
import datetime
import json
import csv
import logging
import logging.handlers
from math import radians, cos, sin, asin, sqrt
from src.jetList import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

airportcodes = open("src/AirportCodes.txt", "r")

with open('src/idtomodel.txt', mode='r') as inp:
    reader = csv.reader(inp)
    dict_from_csv = {rows[0]: rows[1] for rows in reader}


def idtomodel(icao):
    for each, val in dict_from_csv.items():
        model = "UFO"
        if each == icao:
            model = val
            return model
    return model


def fuel(model):
    for each in data:
        try:
            if model in each['Name']:
                return each["Fuel Burn (Hour)"]
            else:
                pass
        except:
            NoneType


def haversine(lon1, lat1, lon2, lat2):
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles.
    return c * r


def longlat(icao, firstSeen):
    if firstSeen is not None:
        r = requests.get(
            f'https://opensky-network.org/api/tracks/all?icao24={icao}&time={firstSeen}')
        flightrecord = json.loads(r.text)
        departureLong = flightrecord['path'][0][1]
        departureLat = flightrecord['path'][0][2]

        destinationlong = flightrecord['path'][-1][1]
        destinationlat = flightrecord['path'][-1][2]
        departure = f"{departureLong},{departureLat}"
        destination = f"{destinationlong},{destinationlat}"
        return haversine(departureLong, departureLat, destinationlong, destinationlat)


def main():
    arrived = []
    CarbonEmissions = 0
    # Epoch time for start->end of yesterday
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    start_of_yesterday = int(time.mktime(yesterday.timetuple()))
    end_of_yesterday = int(time.mktime(today.timetuple()))

    # Retrieve flight arrival data from every airport ICAO code in AirportCodes.txt, combining the API response into arrived list
    for codes in airportcodes.readlines():
        stripped_line = codes.rstrip()
        r = requests.get(
            f'https://opensky-network.org/api/flights/arrival?airport={stripped_line}&begin={start_of_yesterday}&end={end_of_yesterday}')
        arrived.extend(r.json())

    # Process each flight if firstSeen and lastSeen are not None
    for flight in arrived:

        if flight['firstSeen'] and flight['lastSeen'] != None:
            firstSeen = flight['firstSeen']
            lastSeen = flight['lastSeen']
            icao = flight['icao24']
            model = idtomodel(flight['icao24'])
            fuelburn = fuel(model)

            # Further process if fuelburn and model are not None
            if fuelburn != None and model != None:
                # distance = longlat(icao, firstSeen)
                flighttime = (lastSeen - firstSeen) / 360
                gallons = float(flighttime) * float(fuelburn)
                CO2 = (gallons * 21.1) / 2000
                CarbonEmissions += CO2

    logger.info(f'C02 emissions were: {(round(CarbonEmissions * 907.185, 2)):,} Kg')


if __name__ == "__main__":
    main()
