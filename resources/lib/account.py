import requests
from resources.lib.utils import Util
from resources.lib.globals import *
from kodi_six import xbmc, xbmcaddon, xbmcgui
import time, uuid
import random
import string

if sys.version_info[0] > 2:
    from urllib.parse import quote
else:
    from urllib import quote


class Account:
    addon = xbmcaddon.Addon()
    username = ''
    password = ''    
    icon = addon.getAddonInfo('icon')
    verify = False

    def __init__(self):
        self.username = self.addon.getSetting('username')
        self.password = self.addon.getSetting('password')        
        self.did = self.device_id()
        self.util = Util()
        self.media_url = 'https://media-gateway.mlb.com/graphql'

    def device_id(self):
        if self.addon.getSetting('device_id') == '':
            self.addon.setSetting('device_id', str(uuid.uuid4()))

        return self.addon.getSetting('device_id')

    def login(self):
        # Check if username and password are provided
        if self.username == '':
            dialog = xbmcgui.Dialog()
            self.username = dialog.input(LOCAL_STRING(30140), type=xbmcgui.INPUT_ALPHANUM)
            self.addon.setSetting(id='username', value=self.username)

        if self.password == '':
            dialog = xbmcgui.Dialog()
            self.password = dialog.input(LOCAL_STRING(30150), type=xbmcgui.INPUT_ALPHANUM,
                                    option=xbmcgui.ALPHANUM_HIDE_INPUT)
            self.addon.setSetting(id='password', value=self.password)

        if self.username == '' or self.password == '':
            sys.exit()
        else:
            url = 'https://ids.mlb.com/oauth2/aus1m088yK07noBfh356/v1/token'
            headers = {'User-Agent': UA_ANDROID,
                       'Content-Type': 'application/x-www-form-urlencoded'
                       }
            payload = ('grant_type=password&username=%s&password=%s&scope=openid offline_access'
                       '&client_id=0oa3e1nutA1HLzAKG356') % (quote(self.username),
                                                             quote(self.password))

            r = requests.post(url, headers=headers, data=payload, verify=self.verify)
            if r.ok:
                login_token = r.json()['access_token']
                login_token_expiry = datetime.now() + timedelta(seconds=int(r.json()['expires_in']))
                self.addon.setSetting('login_token', login_token)
                self.addon.setSetting('login_token_expiry', str(login_token_expiry))
            else:
                dialog = xbmcgui.Dialog()
                msg = LOCAL_STRING(30263)
                if 'error_description' in r.json():
                    msg = r.json()['error_description']
                dialog.notification(LOCAL_STRING(30262), msg, ICON, 5000, False)
                self.addon.setSetting('login_token', '')
                self.addon.setSetting('login_token_expiry', '')
                sys.exit()


    def logout(self):
        self.util.delete_cookies()
        self.addon.setSetting('login_token', '')
        self.addon.setSetting('login_token_expiry', '')
        self.addon.setSetting('username', '')
        self.addon.setSetting('password', '')

    def media_entitlement(self):
        url = 'https://media-entitlement.mlb.com/api/v3/jwt?os=Android&appname=AtBat&did=' + self.device_id()
        headers = {'User-Agent': UA_ANDROID,
                   'Authorization': 'Bearer ' + self.login_token()
                   }

        r = requests.get(url, headers=headers, verify=self.verify)

        return r.text

    # need to login to access featured videos like Big Inning and MiLB games
    def login_token(self):
        if self.addon.getSetting('login_token_expiry') == '' or \
                parse(self.addon.getSetting('login_token_expiry')) < datetime.now():
            self.login()

        return self.addon.getSetting('login_token')


    def access_token(self):
        return self.login_token()

    def get_playback_url(self, content_id):
        auth = self.access_token()
        url = 'https://search-api-mlbtv.mlb.com/svc/search/v2/graphql/persisted/query/core/Airings' \
              '?variables=%7B%22contentId%22%3A%22' + content_id + '%22%7D'

        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + auth,
            'X-BAMSDK-Version': 'v4.3.0',
            'X-BAMSDK-Platform': 'android-tv',
            'User-Agent': 'BAMSDK/v4.3.0 (mlbaseball-7993996e 8.1.0; v2.0/v4.3.0; android; tv)'
        }

        r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)
        if not r.ok:
            dialog = xbmcgui.Dialog()
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(LOCAL_STRING(30270), msg, self.icon, 5000, False)
            sys.exit()

        json_source = r.json()

        playback_url = json_source['data']['Airings'][0]['playbackUrls'][0]['href']

        broadcast_start_offset = '1'
        broadcast_start_timestamp = None
        try:
            # make sure we have milestone data
            if 'data' in json_source and 'Airings' in json_source['data'] and len(json_source['data']['Airings']) > 0 and 'milestones' in json_source['data']['Airings'][0]:
                for milestone in json_source['data']['Airings'][0]['milestones']:
                    if milestone['milestoneType'] == 'BROADCAST_START':
                        offset_index = 1
                        startDatetime_index = 0
                        if milestone['milestoneTime'][0]['type'] == 'offset':
                            offset_index = 0
                            startDatetime_index = 1
                        broadcast_start_offset = str(milestone['milestoneTime'][offset_index]['start'])
                        broadcast_start_timestamp = parse(milestone['milestoneTime'][startDatetime_index]['startDatetime']) - timedelta(seconds=milestone['milestoneTime'][offset_index]['start'])
                        break
        except:
            pass

        return auth, playback_url, broadcast_start_offset, broadcast_start_timestamp

    def get_stream(self, content_id):
        device_id, session_id = self.get_device_session_id()
        headers = {
            'User-Agent': UA_PC,
            'Authorization': 'Bearer ' + self.login_token(),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        data = {
            "operationName": "initPlaybackSession",
            "query": '''mutation initPlaybackSession(
                $adCapabilities: [AdExperienceType]
                $mediaId: String!
                $deviceId: String!
                $sessionId: String!
                $quality: PlaybackQuality
            ) {
                initPlaybackSession(
                    adCapabilities: $adCapabilities
                    mediaId: $mediaId
                    deviceId: $deviceId
                    sessionId: $sessionId
                    quality: $quality
                ) {
                    playbackSessionId
                    playback {
                        url
                        token
                        expiration
                        cdn
                    }
                    adScenarios {
                        adParamsObj
                        adScenarioType
                        adExperienceType
                    }
                    adExperience {
                        adExperienceTypes
                        adEngineIdentifiers {
                            name
                            value
                        }
                        adsEnabled
                    }
                    heartbeatInfo {
                        url
                        interval
                    }
                    trackingObj
                }
            }''',
            "variables": {
                "adCapabilities": ["GOOGLE_STANDALONE_AD_PODS"],                
                "mediaId": content_id,
                "quality": "PLACEHOLDER",
                "deviceId": device_id,
                "sessionId": session_id
            }
        }
        xbmc.log(str(data))
        r = requests.post(self.media_url, headers=headers, json=data, verify=VERIFY)
        xbmc.log(r.text)
        #r = requests.get(url, headers=headers, cookies=self.util.load_cookies(), verify=self.verify)
        if not r.ok:
            dialog = xbmcgui.Dialog()
            msg = ""
            for item in r.json()['errors']:
                msg += item['code'] + '\n'
            dialog.notification(LOCAL_STRING(30270), msg, self.icon, 5000, False)
            sys.exit()

        stream_url = r.json()['data']['initPlaybackSession']['playback']['url']
        xbmc.log(f'Stream URL: {stream_url}')
        headers = 'User-Agent=' + UA_PC
        return stream_url, headers, '1', None
    
    def get_device_session_id(self):
        headers = {
            'User-Agent': UA_PC,
            'Authorization': 'Bearer ' + self.login_token(),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        data = {
            "operationName": "initSession",
            "query": '''mutation initSession($device: InitSessionInput!, $clientType: ClientType!, $experience: ExperienceTypeInput) {
                initSession(device: $device, clientType: $clientType, experience: $experience) {
                    deviceId
                    sessionId
                    entitlements {
                        code
                    }
                    location {
                        countryCode
                        regionName
                        zipCode
                        latitude
                        longitude
                    }
                    clientExperience
                    features
                }
            }''',
            "variables": {
                "device": {
                    "appVersion": "7.8.2",
                    "deviceFamily": "desktop",
                    "knownDeviceId": "",
                    "languagePreference": "ENGLISH",
                    "manufacturer": "Google Inc.",
                    "model": "",
                    "os": "windows",
                    "osVersion": "10"
                },
                "clientType": "WEB"
            }
        }

        r = requests.post(self.media_url, headers=headers, json=data)
        device_id = r.json()['data']['initSession']['deviceId']
        session_id = r.json()['data']['initSession']['sessionId']

        return device_id, session_id

