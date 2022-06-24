import json
import pypco
from datetime import datetime, timedelta
import logging

class CHECKINS:
    def __init__(self, pco, debug=False):
        self.pco = pco
        self.debug = debug

    def logger(self, msg):
        time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        if self.debug:
            print(f"{time} - {msg}")

    # get_current_checkins
    # created_at (str/ISO8601): only get events that were created after a specified date
    # shows_at: not implemented
    # curr_time (str/ISO8601): override the current date with the specified date. Helpful for testing.
    # updated_at: not implemented
    # checkouts_only (bool): only return checkins with the checkout value set
    # location_id (str): Only return checkins from a specific location or locations

    def get_current_checkins(self, created_at=None, shows_at=None, curr_time=None, updated_at=None, checkouts_only=False, location_id=None):
        if created_at is None:
            event_time_query = f"/check-ins/v2/event_times?per_page=100&include=event"
        else:
            event_time_query = f"/check-ins/v2/event_times?per_page=100&include=event&where[created_at][gt]={created_at}"
        if curr_time is None:
                curr_time = datetime.now()
        checkins = [] # gets appended and returned later

        self.logger(f"event_time_resp uri: {event_time_query}")
        for event_time_resp in self.pco.iterate(event_time_query):
            shows_at = datetime.strptime(event_time_resp['data']['attributes']['shows_at'], "%Y-%m-%dT%H:%M:%SZ")
            hides_at = datetime.strptime(event_time_resp['data']['attributes']['hides_at'], "%Y-%m-%dT%H:%M:%SZ")

            if shows_at < curr_time and hides_at > curr_time:
                self.logger(f"{event_time_resp['data']['id']}: {event_time_resp['data']['attributes']['shows_at']} -> {event_time_resp['data']['attributes']['hides_at']}")
                
                # get the associated event
                event_time_event_resp = self.pco.get(event_time_resp['data']['relationships']['event']['links']['related'])
                event = event_time_event_resp['data']
                
                params = {
                    'include': 'locations,person,checked_in_by',
                }
                # for the /check-ins/v2/event_times call, it would be helpful if you could filter by updated_at
                #  - requested here: https://github.com/planningcenter/developers/issues/997
                checkin_query = f"/check-ins/v2/event_times/{event_time_resp['data']['id']}/check_ins"
                self.logger(f"checkin query: {checkin_query}")
                for checkin in self.pco.iterate(checkin_query, **params):
                    append = True
                    self.logger(f"{checkin['data']['id']}: {checkin['data']['attributes']['first_name']} {checkin['data']['attributes']['last_name']}")

                    # Structure the includes in a more friendly way
                    for included in checkin['included']:
                        if included['type'] == 'Person' and included['id'] == checkin['data']['relationships']['person']['data']['id']:
                            checkin['data']['person'] = included
                        elif included['type'] == 'Location':
                            checkin['data']['location'] = included
                        elif included['type'] == 'Person' and included['id'] != checkin['data']['relationships']['person']['data']['id']:
                            checkin['data']['checked_in_by'] = included

                    # Check for reasons to not include this checkin
                    if checkouts_only and checkin['data']['attributes']['checked_out_at'] is None:
                        append = False
                    if location_id and checkin['data']['location']['id'] not in location_id:
                        if not checkin['data']['location']['relationships']['parent']['data'] or checkin['data']['location']['relationships']['parent']['data']['id'] not in location_id:
                            append = False
                        
                    if append == True:
                        checkins.append(checkin['data'])
        return checkins

    def get_passes(self):
        passes = {}
        for pas in self.pco.iterate(f"/check-ins/v2/passes?include=person"):
            if(pas['data']['attributes']['kind'] == 'barcode'):
                #print( json.dumps(pas,indent=4) )
                code = pas['data']['attributes']['code']
                passes[code] = pas['included'][0]
        return passes

    def combine_checkins_data(self, checkin, locations):
        json_formatted_str = json.dumps(checkin,indent=4)
        print(json_formatted_str)
        lID = checkin['relationships']['location']['data']['id']
        for location in locations:
            if location['id'] == lID:
                checkin['location'] = location
        return checkin
