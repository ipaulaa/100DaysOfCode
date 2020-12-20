import requests
from twilio.rest import Client
import sys

account_sid = sys.argv[1]
auth_token = sys.argv[2]
client = Client(account_sid, auth_token)
twilio_number = sys.argv[3]
my_number = sys.argv[4]

LATITUDE = -22.338930
LONGITUDE = -49.055190

api_key = sys.argv[5]
api_url = "https://api.openweathermap.org/data/2.5/onecall"
params = {
    "lat": LATITUDE,
    "lon": LONGITUDE,
    "exclude": "current,minutely,daily,alerts",
    "appid": api_key
}

response = requests.get(api_url, params=params)
response.raise_for_status()

data = response.json()

for hourly_data in data["hourly"][:12]:
    condition_code = hourly_data["weather"][0]["id"]
    if condition_code < 700:
        message = client.messages.create(
            body="It's gonna rain! Don't forget to bring an ☔",
            from_=twilio_number,
            to=my_number
        )
        break
