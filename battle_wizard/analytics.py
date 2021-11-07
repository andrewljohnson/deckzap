import os
import json
import requests
import time


class Analytics:
    def __init__(self, api_key, api_uri="https://api2.amplitude.com/2/httpapi"):
        self.api_key = api_key
        self.api_uri = api_uri

    def create_event(self,**kwargs):
        user_id = kwargs.get('user_id',None)
        device_id = kwargs.get('device_id', None)
        username = kwargs.get('username', None)
        event_type = kwargs.get('event_type', None)

        event = {}
        event["event_type"] = event_type

        if user_id:
            event["user_id"] = username
            if len(username) < 5:
                event["user_id"] = user_id + 10000
            event["user_properties"] = {}
            event["user_properties"]["django_user_id"] = user_id
            event["user_properties"]["username"] = username
        if device_id:
            event["device_id"] = device_id
        if not user_id and not device_id:
            print("No user_id or device_id provided for analytics call " + event_type)
            return

        # integer epoch time in milliseconds
        event["time"] = int(time.time()*1000)

        event_properties = kwargs.get('event_properties', None)
        if event_properties is not None and type(event_properties) == dict:
            event["event_properties"] = event_properties

        event_package = {
            'api_key': self.api_key,
            'events': [event],
            }
        return event_package

    def log_event(self,event):
        result = requests.post(self.api_uri, data=json.dumps(event))
        return result

    @staticmethod
    def log_amplitude(request, event_name, event_props):
        amplitude_logger = Analytics(api_key = os.environ.get("AMPLITUDE_API_KEY"))
        event_args = {
            "event_type":event_name,
            "event_properties":event_props
        }
        if request.user.is_authenticated:
            event_args["user_id"] = request.user.id
            event_args["username"] = request.user.username
        event_args["device_id"] = request.session._get_or_create_session_key()
        event = amplitude_logger.create_event(**event_args)
        amplitude_logger.log_event(event)

