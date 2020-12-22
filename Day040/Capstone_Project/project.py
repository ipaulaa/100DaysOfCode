import pprint
import datetime as dt
import data_manager as dm
import flight_search as fs
import flight_data as fd
import notification_manager as nm

DEPARTURE_IATA = 'LON'
SIX_MONTHS_IN_DAYS = 180


def get_date(date, **kwargs):
    new_date = date + dt.timedelta(**kwargs)
    return new_date.strftime('%d/%m/%Y')


today = dt.datetime.now()
tomorrow = get_date(today, days=1)
future_date = get_date(today, days=SIX_MONTHS_IN_DAYS)

flight_params = {
    'apikey': fs.API_KEY,
    'fly_from': DEPARTURE_IATA,
    'date_from': tomorrow,
    'date_to': future_date,
    'nights_in_dst_from': 7,
    'nights_in_dst_to': 28,
    'flight_type': 'round',
    'one_for_city': 1,
    'adults': 1,
    'curr': 'GBP'
}

data_manager = dm.DataManager(dm.ENDPOINT, dm.SHEET, dm.TOKEN)
for row in data_manager.data['prices']:
    if len(row['iataCode']) != 0:
        continue
    city = row['city']
    params = {
        'apikey': fs.API_KEY,
        'location_types': 'city',
        'term': city
    }
    flight_search = fs.FlightSearch(fs.API_LOCATIONS, fs.ENDPOINT, params)
    row['iataCode'] = flight_search.search_locations('name', city, 'code')
    data_manager.put_data(row)

iata_codes = [row['iataCode'] for row in data_manager.data['prices']]

notification_manager = nm.NotificationManager()
for idx, iata_code in enumerate(iata_codes):
    flight_params.update(fly_to=iata_code, max_stopovers=0)
    print(flight_params)
    flight_search = fs.FlightSearch(fs.API_SEARCH, fs.ENDPOINT, flight_params)
    data = flight_search.data['data']
    stopped = False
    if len(data) == 0:
        flight_params.update(max_stopovers=1)
        flight_search = fs.FlightSearch(fs.API_SEARCH, fs.ENDPOINT, flight_params)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(flight_search.data['data'])
        data = flight_search.data['data']
        if len(data) == 0:
            continue
        stopped = True
    flight_data = fd.FlightData(data)
    if flight_data.data['price'] <= data_manager.data['prices'][idx]['lowestPrice']:
        data = flight_data.formatted_data
        message = '\n🚨Low price alert🚨'
        message += f'\n\nOnly £{data["price"]:.2f} to fly'
        message += f'\nfrom {data["from"]} to {data["to"]},'
        message += f'\nfrom {data["departure_date"]} to {data["arrival_date"]}.'
        if stopped:
            message += f'\n\nFlight has 1 stop over, via {data["via_city"]}.'

        message += f"\nhttps://www.google.co.uk/flights?hl=en#flt="
        message += f"{flight_data.data['flyTo']}.{flight_data.data['flyFrom']}."
        message += f"{data['departure_date']}*{flight_data.data['flyFrom']}."
        message += f"{flight_data.data['flyTo']}.{data['return_date']}"

        users = dm.DataManager(dm.ENDPOINT, dm.USERS_SHEET, dm.TOKEN)
        emails = [row['email'] for row in users.data[dm.USERS_SHEET]]
        notification_manager.send_email(message.encode('utf-8'), *emails)
