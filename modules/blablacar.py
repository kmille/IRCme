import yaml
import arrow
import pickle
import os

from blablacarapi import BlaBlaCarApi
from ipdb import set_trace

from blablacar_secrets import api_key

DATA_DIR = "data"
settings = "settings.yaml"
#settings = { 'from': 'Darmstadt', 'to': 'Würzburg', 'starting_at_date': '2019-01-06', 'starting_at_time': 14 }


def get_trips(trip):
    blablacar = BlaBlaCarApi(api_key=api_key, locale="de_DE", currency="cur=EUR")
    # format starting_at_date: '2019-01-06' 
    # format starting_at_time: 17 (int)
    api_response = blablacar.trips(frm=trip['from'], to=trip['to'], date_from=trip['starting_at_date'], hour_from=trip['starting_at_time'])
    return api_response.trips


def dump(filename, trips):
    results = []
    for trip in trips:
        notify_print(trip)
        msg = "Blablacar: um {} für {} € {}".format(trip.departure_date, trip.price['value'], trip.links['_front'])
        results.append(msg)
    with open(filename, "wb") as f:
        pickle.dump(trips, f)
    return results 


def notify_print(trip):
    print(" Found new Fahrt: {}".format(trip.links['_front']))


def check_new(filename, trips):
    # check if there is a new trip
    results = []
    with open(filename, "rb") as f:
        last_data = pickle.load(f)
    last_data_all_ids = [t.permanent_id for t in last_data]
    #last_data_all_ids = last_data_all_ids[1:] # for testing
    for trip in trips:
        if trip.permanent_id not in last_data_all_ids:
            notify_print(trip)
            msg = "Blablacar: um {} für {} € {}".format(trip.departure_date, trip.price['value'], trip.links['_front'])
            results.append(msg)
    return results 


def find_trips():
    result = []
    trip_searches = yaml.safe_load(open(settings))
    for search in trip_searches['blablacar']:
        if arrow.now() > arrow.get(search['starting_at_date']):
            print("Fahrt from {} to {} liegt in der Vergangenheit".format(search['from'], search['to']))
        else:
            trips = get_trips(search)
            print("API gave us {} trips".format(len(trips)))
            filename = os.path.join(DATA_DIR, "{}-{}-{}-{}.pickl".format(search['from'], 
                                                                         search['to'], 
                                                                         search['starting_at_date'], 
                                                                         search['starting_at_time'], 
                                                                         search['starting_at_time']))
            if not os.path.exists(filename):
                # first run: all are new
                result.extend(dump(filename, trips))
            else:
                result.extend(check_new(filename, trips))
    return result


def go():
    return find_trips()

if __name__ == '__main__':
    find_trips()
