import json
import pypco
from datetime import datetime, timedelta
import logging

class CHECKINS:
    def __init__(self, pco):
        self.pco = pco

    def get_current_checkins(self, created_at=None, shows_at=None, curr_time=None, updated_at=None, checkouts_only=False, location_id=None):
        if created_at is None:
            dateNow = datetime.today() - timedelta(hours=336, minutes=0, seconds=5)
            created_at = dateNow.replace(microsecond=0).isoformat()
        if curr_time is None:
                curr_time = datetime.now()
        checkins = []
        
        for event_time_resp in self.pco.iterate(f"/check-ins/v2/event_times?per_page=200&include=event&where[created_at][gt]={created_at}"):
            shows_at = datetime.strptime(event_time_resp['data']['attributes']['shows_at'], "%Y-%m-%dT%H:%M:%SZ")
            hides_at = datetime.strptime(event_time_resp['data']['attributes']['hides_at'], "%Y-%m-%dT%H:%M:%SZ")
            
            if shows_at < curr_time and hides_at > curr_time:
                # get the associated event
                event_time_event_resp = self.pco.get(event_time_resp['data']['relationships']['event']['links']['related'])
                event = event_time_event_resp['data']
                print(f"{event_time_resp['data']['attributes']['shows_at']} -> {event_time_resp['data']['attributes']['hides_at']}")
                params = {
                    'include': 'locations,person,checked_in_by',
                }
                print(f"/check-ins/v2/event_times/{event_time_resp['data']['id']}/check_ins")
                for checkin in self.pco.iterate(f"/check-ins/v2/event_times/{event_time_resp['data']['id']}/check_ins", **params):
                    append = True
                    if not checkouts_only or checkin['data']['attributes']['checked_out_at'] is not None:
                        for included in checkin['included']:
                            if included['type'] == 'Person' and included['id'] == checkin['data']['relationships']['person']['data']['id']:
                                checkin['data']['person'] = included
                            elif included['type'] == 'Location':
                                checkin['data']['location'] = included
                            elif included['type'] == 'Person' and included['id'] != checkin['data']['relationships']['person']['data']['id']:
                                checkin['data']['checked_in_by'] = included

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


