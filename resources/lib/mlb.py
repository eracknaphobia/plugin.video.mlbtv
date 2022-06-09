from resources.lib.globals import *
from .account import Account
from .mlbmonitor import MLBMonitor


def categories():
    addDir(LOCAL_STRING(30360), 100, ICON, FANART)
    addDir(LOCAL_STRING(30361), 105, ICON, FANART)
    # see yesterday's scores at inning in the main menu
    addDir(LOCAL_STRING(30413), 108, ICON, FANART)
    addDir(LOCAL_STRING(30362), 200, ICON, FANART)
    # show Featured Videos in the main menu
    addDir(LOCAL_STRING(30363), 300, ICON, FANART)


def todays_games(game_day, start_inning='False'):
    today = localToEastern()
    if game_day is None:
        game_day = today

    settings.setSetting(id='stream_date', value=game_day)

    display_day = stringToDate(game_day, "%Y-%m-%d")
    #url_game_day = display_day.strftime('year_%Y/month_%m/day_%d')
    prev_day = display_day - timedelta(days=1)

    addDir('[B]<< %s[/B]' % LOCAL_STRING(30010), 101, PREV_ICON, FANART, prev_day.strftime("%Y-%m-%d"), start_inning)

    date_display = '[B][I]' + colorString(display_day.strftime("%A, %m/%d/%Y"), GAMETIME_COLOR) + '[/I][/B]'

    addPlaylist(date_display, str(game_day), 900, ICON, FANART)

    #url = 'http://gdx.mlb.com/components/game/mlb/' + url_game_day + '/grid_ce.json'
    url = API_URL + '/api/v1/schedule'
    # url += '?hydrate=broadcasts(all),game(content(all)),probablePitcher,linescore,team,flags'
    url += '?hydrate=game(content(media(epg))),probablePitcher,linescore,team,flags,gameInfo'
    url += '&sportId=1,51'
    url += '&date=' + game_day

    headers = {
        'User-Agent': UA_ANDROID
    }
    xbmc.log(url)
    r = requests.get(url,headers=headers, verify=VERIFY)
    json_source = r.json()

    favorite_games = []
    remaining_games = []

    fav_team_id = getFavTeamId()
    for game in json_source['dates'][0]['games']:
        if fav_team_id is not None and fav_team_id in [str(game['teams']['home']['team']['id']), str(game['teams']['away']['team']['id'])]:
            favorite_games.append(game)
        else:
            remaining_games.append(game)

    try:
        for game in favorite_games:
            create_game_listitem(game, game_day, start_inning, today)
    except:
        pass

    if ONLY_FREE_GAMES != 'true':
        create_big_inning_listitem(game_day)

    try:
        for game in remaining_games:
            create_game_listitem(game, game_day, start_inning, today)
    except:
        pass

    next_day = display_day + timedelta(days=1)
    addDir('[B]%s >>[/B]' % LOCAL_STRING(30011), 101, NEXT_ICON, FANART, next_day.strftime("%Y-%m-%d"), start_inning)


def create_game_listitem(game, game_day, start_inning, today):
    #icon = ICON
    icon = 'https://img.mlbstatic.com/mlb-photos/image/upload/ar_167:215,c_crop/fl_relative,l_team:' + str(game['teams']['home']['team']['id']) + ':fill:spot.png,w_1.0,h_1,x_0.5,y_0,fl_no_overflow,e_distort:100p:0:200p:0:200p:100p:0:100p/fl_relative,l_team:' + str(game['teams']['away']['team']['id']) + ':logo:spot:current,w_0.38,x_-0.25,y_-0.16/fl_relative,l_team:' + str(game['teams']['home']['team']['id']) + ':logo:spot:current,w_0.38,x_0.25,y_0.16/w_750/team/' + str(game['teams']['away']['team']['id']) + '/fill/spot.png'
    # http://mlb.mlb.com/mlb/images/devices/ballpark/1920x1080/2681.jpg
    # B&W
    # fanart = 'http://mlb.mlb.com/mlb/images/devices/ballpark/1920x1080/'+game['venue_id']+'.jpg'
    # Color
    # fanart = 'http://www.mlb.com/mlb/images/devices/ballpark/1920x1080/color/' + str(game['venue']['id']) + '.jpg'
    fanart = 'http://cd-images.mlbstatic.com/stadium-backgrounds/color/light-theme/1920x1080/%s.png' % game['venue']['id']


    xbmc.log(str(game['gamePk']))

    if TEAM_NAMES == "0":
        away_team = game['teams']['away']['team']['teamName']
        home_team = game['teams']['home']['team']['teamName']
    else:
        away_team = game['teams']['away']['team']['abbreviation']
        home_team = game['teams']['home']['team']['abbreviation']

    title = away_team + ' at ' + home_team

    is_free = False
    if 'content' in game and 'media' in game['content'] and 'freeGame' in game['content']['media']:
        is_free = game['content']['media']['freeGame']

    fav_game = False
    if game['teams']['away']['team']['name'] in FAV_TEAM:
        fav_game = True
        away_team = colorString(away_team, getFavTeamColor())

    if game['teams']['home']['team']['name'] in FAV_TEAM:
        fav_game = True
        home_team = colorString(home_team, getFavTeamColor())

    game_time = ''
    suspended = 'False'
    display_time = 'TBD'
    relative_inning = None
    spoiler = 'True'
    today = localToEastern()
    if NO_SPOILERS == '1' or (NO_SPOILERS == '2' and fav_game) or (NO_SPOILERS == '3' and game_day == today) or (NO_SPOILERS == '4' and game_day < today):
        spoiler = 'False'

    if 'gameDate' in game:
        display_time = get_display_time(UTCToLocal(stringToDate(game['gameDate'], "%Y-%m-%dT%H:%M:%SZ")))

    game_state = game['status']['detailedState']

    scheduled_innings = 9
    if 'linescore' in game and 'scheduledInnings' in game['linescore']:
        scheduled_innings = int(game['linescore']['scheduledInnings'])
        if game_state.startswith('Completed Early') and 'currentInning' in game['linescore']:
            scheduled_innings = int(game['linescore']['currentInning'])

    #if game['status']['abstractGameState'] == 'Preview':
    if game['status']['detailedState'].lower() == 'scheduled' or game['status']['detailedState'].lower() == 'pre-game':
        if game['status']['startTimeTBD'] is True:
            game_time = 'TBD'
        else:
            game_time = display_time

        game_time = colorString(game_time, UPCOMING)

    else:
        #game_time = game['status']['abstractGameState']
        game_time = game_state

        if game_state != 'Postponed':
            # if we've requested to see scores at a particular inning
            if start_inning != 'False' and 'linescore' in game:
                relative_inning = (int(start_inning) - (9 - scheduled_innings))
                if relative_inning > len(game['linescore']['innings']):
                    relative_inning = len(game['linescore']['innings'])
                start_inning = relative_inning
                if relative_inning > 0:
                    game_time = 'T' + str(relative_inning)
                else:
                    game_time = display_time
            elif game_state != 'Final' and game['status']['abstractGameState'] == 'Live' and 'linescore' in game:
                if game['linescore']['isTopInning']:
                    # up triangle
                    # top_bottom = u"\u25B2"
                    top_bottom = "T"
                else:
                    # down triangle
                    # top_bottom = u"\u25BC"
                    top_bottom = "B"

                if game['linescore']['currentInning'] >= scheduled_innings and spoiler == 'False':
                    game_time = str(scheduled_innings) + 'th+'
                else:
                    game_time = top_bottom + ' ' + game['linescore']['currentInningOrdinal']

            try:
                if 'resumeGameDate' in game or 'resumedFromDate' in game:
                    suspended = 'archive'
                    if 'resumeGameDate' in game:
                        game_time += ' (Suspended)'
                    elif 'resumedFromDate' in game:
                        game_time += ' (Resumed)'
                    for epg in game['content']['media']['epg'][0]['items']:
                        if epg['mediaState'] == 'MEDIA_ON':
                            suspended = 'live'
                            break
                        elif epg['mediaState'] == 'MEDIA_OFF':
                            game_time = display_time + ' ' + game_time
                            break
            except:
                pass

        if game_state == 'Final' or game_state == 'Postponed':
            game_time = colorString(game_time, FINAL)

        elif game['status']['abstractGameState'] == 'Live':
            if 'linescore' in game and game['linescore']['currentInning'] >= scheduled_innings:
                color = CRITICAL
            else:
                color = LIVE

            game_time = colorString(game_time, color)

        else:
            game_time = colorString(game_time, LIVE)

    game_pk = game['gamePk']

    stream_date = str(game_day)

    desc = ''
    probables = ''
    if ('probablePitcher' in game['teams']['away'] and 'fullName' in game['teams']['away']['probablePitcher']) or ('probablePitcher' in game['teams']['home'] and 'fullName' in game['teams']['home']['probablePitcher']):
        probables = ' ('
        if 'probablePitcher' in game['teams']['away'] and 'fullName' in game['teams']['away']['probablePitcher']:
            desc += game['teams']['away']['probablePitcher']['fullName']
            probables += get_last_name(game['teams']['away']['probablePitcher']['fullName'])
        else:
            desc += 'TBD'
            probables += 'TBD'
        desc += ' vs. '
        probables += ' vs '
        if 'probablePitcher' in game['teams']['home'] and 'fullName' in game['teams']['home']['probablePitcher']:
            desc += game['teams']['home']['probablePitcher']['fullName']
            probables += get_last_name(game['teams']['home']['probablePitcher']['fullName'])
        else:
            desc += 'TBD'
            probables += 'TBD'
        probables += ')'

    if 'venue' in game and 'name' in game['venue']:
        desc += '[CR]From ' + game['venue']['name']
    if game['status']['abstractGameState'] == 'Preview' or (start_inning == 'False' and spoiler == 'False'):
        name = game_time + ' ' + away_team + ' at ' + home_team
    else:
        name = game_time + ' ' + away_team
        away_score = ''
        home_score = ''
        try:
            if 'linescore' in game and game_state != 'Postponed':
                away_score = 0
                home_score = 0
                if relative_inning is None:
                    away_score = game['linescore']['teams']['away']['runs']
                    home_score = game['linescore']['teams']['home']['runs']
                else:
                    for inning in game['linescore']['innings']:
                        if int(inning['num']) < relative_inning:
                            away_score += inning['away']['runs']
                            home_score += inning['home']['runs']
                        else:
                            break
                away_score = ' ' + colorString(str(away_score), SCORE_COLOR)
                home_score = ' ' + colorString(str(home_score), SCORE_COLOR)
        except:
            pass

        name += away_score + ' at ' + home_team + home_score

        # check flags
        if 'flags' in game:
            if game['flags']['perfectGame'] is True:
                name += ' ' + colorString('(Perfect Game)', CRITICAL)
            elif game['flags']['noHitter'] is True:
                name += ' ' + colorString('(No-Hitter)', CRITICAL)

    if game['doubleHeader'] != 'N':
        doubleheader_label = 'Game ' + str(game['gameNumber'])
        name += ' (' + doubleheader_label + ')'
        desc += '[CR]' + doubleheader_label

    if game['status']['abstractGameState'] == 'Final' and game_state != 'Final':
        desc += '[CR]' + game_state

    if 'description' in game and game['description'] != "":
        desc += '[CR]' + game['description']

    if scheduled_innings != 9:
        desc += '[CR]' + str(scheduled_innings) + '-inning game'

    # Check local/national blackout status
    blackout = 'False'
    try:
        if game_day >= today and game_state != 'Postponed':
            blackout_type, blackout_time = get_blackout_status(game, suspended, scheduled_innings)

            if blackout_type != 'False':
                name = blackoutString(name)
                desc += '[CR]' + blackout_type + ' video blackout until approx. 90 min. after the game'
                if blackout_time is None:
                    blackout = 'True'
                else:
                    blackout = blackout_time
                    blackout_display_time = get_display_time(UTCToLocal(blackout_time))
                    desc += ' (~' + blackout_display_time + ')'
    except:
        pass

    if fav_game:
        name = '[B]' + name + '[/B]'

    if is_free:
        name = colorString(name, FREE)

    name += colorString(probables, FINAL)

    # Get audio/video info
    audio_info, video_info = getAudioVideoInfo()
    # 'duration':length
    info = {'plot': desc, 'tvshowtitle': 'MLB', 'title': title, 'originaltitle': title, 'aired': game_day, 'genre': LOCAL_STRING(700), 'mediatype': 'video'}

    # If set only show free games in the list
    if ONLY_FREE_GAMES == 'true' and not is_free:
        return
    add_stream(name, title, desc, game_pk, icon, fanart, info, video_info, audio_info, stream_date, spoiler, suspended, start_inning, blackout)


# fetch a list of featured videos
def get_video_list(list_url=None):
    # use the Featured on MLB.TV list (included Big Inning) if no list is specified
    if list_url == None:
        list_url = 'https://dapi.cms.mlbinfra.com/v2/content/en-us/sel-mlbtv-featured-svod-video-list'

    headers = {
        'User-Agent': UA_PC,
        'Origin': 'https://www.mlb.com',
        'Referer': 'https://www.mlb.com',
        'Content-Type': 'application/json'
    }
    r = requests.get(list_url, headers=headers, verify=VERIFY)
    json_source = r.json()
    return json_source


# display a list of featured videos
def featured_videos(featured_video=None):
    # if no list is specified, use the master list of lists
    if featured_video == None:
        featured_video = 'https://mastapi.mobile.mlbinfra.com/api/video/v1/playlist'

    video_list = get_video_list(featured_video)
    if 'items' in video_list:
        for item in video_list['items']:
            #xbmc.log(str(item))
            if 'title' in item:
                title = item['title']
                liz=xbmcgui.ListItem(title)

                # check if a video url is provided
                if 'fields' in item:
                    description = title
                    if 'description' in item['fields']:
                        description = item['fields']['description']
                    liz.setInfo( type="Video", infoLabels={ "Title": title, "plot": description } )
                    video_url = None
                    if 'playbackScenarios' in item['fields']:
                        for playback in item['fields']['playbackScenarios']:
                            if playback['playback'] == 'hlsCloud':
                                video_url = playback['location']
                                break
                    elif 'url' in item['fields']:
                        video_url = item['fields']['url']
                    if video_url is not None:
                        xbmc.log('video url : ' + video_url)
                        if 'thumbnail' in item and 'thumbnailUrl' in item['thumbnail']:
                            thumbnail = item['thumbnail']['thumbnailUrl']
                            # modify thumnail URL for use as icon and fanart
                            icon = thumbnail.replace('w_250,h_250,c_thumb,g_auto,q_auto,f_jpg', 't_16x9/t_w1080')
                            fanart = thumbnail.replace('w_250,h_250,c_thumb,g_auto,q_auto,f_jpg', 'g_auto,c_fill,ar_16:9,q_60,w_1920/e_gradient_fade:15,x_0.6,b_black')
                        else:
                            icon = ICON
                            fanart = FANART
                        liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
                        liz.setProperty("IsPlayable", "true")
                        u=sys.argv[0]+"?mode="+str(301)+"&featured_video="+urllib.quote_plus(video_url)+"&name="+urllib.quote_plus(title)
                        isFolder=False
                # if no video url is provided, we assume it is just another list
                else:
                    liz.setInfo( type="Video", infoLabels={ "Title": title } )
                    list_url = item['url']
                    xbmc.log('list url : ' + list_url)
                    if list_url == "":
                        continue
                    u=sys.argv[0]+"?mode="+str(300)+"&featured_video="+urllib.quote_plus(list_url)
                    isFolder=True

                xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
                xbmcplugin.setContent(addon_handle, 'episodes')

        # if it's a long list, display a "Next" link if provided
        if 'pagination' in video_list and 'nextUrl' in video_list['pagination']:
            title = '[B]%s >>[/B]' % LOCAL_STRING(30011)
            liz=xbmcgui.ListItem(title)
            liz.setInfo( type="Video", infoLabels={ "Title": title } )
            list_url = video_list['pagination']['nextUrl']
            if list_url != "":
                u=sys.argv[0]+"?mode="+str(300)+"&featured_video="+urllib.quote_plus(list_url)
                isFolder=True
                xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
                xbmcplugin.setContent(addon_handle, 'episodes')


# display a Big Inning item within a game list
def create_big_inning_listitem(game_day):
    try:
        # check when we last fetched the Big Inning schedule
        today = localToEastern()
        big_inning_date = str(settings.getSetting(id="big_inning_date"))

        # if we've already fetched it today, use the cached schedule
        if big_inning_date == today:
            xbmc.log('Using cached Big Inning schedule')
            big_inning_schedule = json.loads(settings.getSetting(id="big_inning_schedule"))
        # otherwise, fetch a new big inning schedule
        else:
            xbmc.log('Fetching Big Inning schedule')
            settings.setSetting(id='big_inning_date', value=today)
            url = 'https://www.mlb.com/live-stream-games/big-inning'

            headers = {
                'User-Agent': UA_PC,
                'Origin': 'https://www.mlb.com',
                'Referer': 'https://www.mlb.com'
            }
            r = requests.get(url,headers=headers, verify=VERIFY)
            #xbmc.log(r.text)

            # parse the schedule table
            table = re.findall('<td>([^<]*)<\/td>', r.text)
            xbmc.log('Number of fields in Big Inning schedule table: ' + str(len(table)))

            counter = 0
            table_iter = iter(table)
            columns_in_table = 3
            big_inning_schedule = {}
            for field in table_iter:
                date_display = table[counter]
                xbmc.log('Checking date ' + date_display + ' from Big Inning schedule')
                big_inning_date = parse(date_display).strftime('%Y-%m-%d')
                xbmc.log('Formatted date ' + big_inning_date)
                # ignore dates in the past
                if big_inning_date >= today:
                    big_inning_start = str(UTCToLocal(easternToUTC(parse(big_inning_date + ' ' + table[counter+1]))))
                    big_inning_end = str(UTCToLocal(easternToUTC(parse(big_inning_date + ' ' + table[counter+2]))))
                    big_inning_schedule[big_inning_date] = {'start': big_inning_start, 'end': big_inning_end}
                counter = counter + columns_in_table
                for i in range(columns_in_table - 1):
                    next(table_iter, None)
            # save the scraped schedule
            settings.setSetting(id='big_inning_schedule', value=json.dumps(big_inning_schedule))

        if game_day in big_inning_schedule:
            xbmc.log(game_day + ' has a scheduled Big Inning broadcast')
            display_title = LOCAL_STRING(30368)

            big_inning_start = parse(big_inning_schedule[game_day]['start'])
            big_inning_end = parse(big_inning_schedule[game_day]['end'])

            # format the time for display

            game_time = get_display_time(big_inning_start) + ' - ' + get_display_time(big_inning_end)
            now = datetime.now()
            if now < big_inning_start:
                game_time = colorString(game_time, UPCOMING)
            elif now > big_inning_end:
                game_time = colorString(game_time, FINAL)
            elif now >= big_inning_start and now <= big_inning_end:
                display_title = LOCAL_STRING(30367) + LOCAL_STRING(30368)
                game_time = colorString(game_time, LIVE)
            name = game_time + ' ' + display_title

            desc = 'MLB Big Inning brings fans all the best action from around the league with live look-ins, breaking highlights and big moments as they happen all season long. Airing seven days a week on MLB.TV.'

            # create the list item
            liz=xbmcgui.ListItem(name)
            liz.setInfo( type="Video", infoLabels={ "Title": display_title, 'plot': desc } )
            liz.setProperty("IsPlayable", "true")
            icon = 'https://img.mlbstatic.com/mlb-images/image/private/ar_16:9,g_auto,q_auto:good,w_372,c_fill,f_jpg/mlb/uwr8vepua4t1fe8uwyki'
            fanart = 'https://img.mlbstatic.com/mlb-images/image/private/g_auto,c_fill,ar_16:9,q_60,w_1920/e_gradient_fade:15,x_0.6,b_black/mlb/uwr8vepua4t1fe8uwyki'
            liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
            u=sys.argv[0]+"?mode="+str(301)+"&featured_video="+urllib.quote_plus(LOCAL_STRING(30367) + LOCAL_STRING(30368))+"&name="+urllib.quote_plus(LOCAL_STRING(30367) + LOCAL_STRING(30368))
            xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=False)
            xbmcplugin.setContent(addon_handle, 'episodes')
        else:
            xbmc.log(game_day + ' does not have a scheduled Big Inning broadcast')
    except Exception as e:
        xbmc.log('big inning error : ' + str(e))
        pass


def stream_select(game_pk, spoiler, suspended, start_inning, blackout, description, name, icon, fanart, from_context_menu=False, autoplay=False):
    # fetch the epg content using the game_pk
    url = API_URL + '/api/v1/game/' + game_pk + '/content'
    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()
    # start with just video content, assumed to be at index 0
    epg = json_source['media']['epg'][0]['items']

    # define some default variables
    selected_content_id = None
    selected_media_state = None
    stream_url = ''
    broadcast_start_offset = '1' # offset to pass to inputstream adaptive
    broadcast_start_timestamp = None # to pass to skip monitor
    stream_type = 'video'
    skip_possible = True # to determine if possible to show skip options dialog
    skip_type = 0
    is_live = False # to pass to skip monitor
    # convert start inning values to integers
    if start_inning == 'False':
        start_inning = 0
    else:
        start_inning = int(start_inning)
    start_inning_half = 'top'
    if blackout != 'False' and blackout != 'True':
        utc=pytz.UTC
        now = utc.localize(datetime.now())
        blackout = parse(blackout)
    # define a dialog that we can use as needed
    dialog = xbmcgui.Dialog()

    # auto select stream if enabled and not bypassed with context menu item and it's not an archived suspended game, or if autoplay is forced
    # and if it's not blacked out or the blackout time has passed
    if ((AUTO_SELECT_STREAM == 'true' and from_context_menu is False and suspended != 'archive') or autoplay is True) and (blackout == 'False' or (blackout != 'True' and blackout < now)):
        # loop through the streams to determine the best match
        for item in epg:
            # ignore streams that haven't started yet, audio streams (without a mediaFeedType), and in-market streams
            if item['mediaState'] != 'MEDIA_OFF' and 'mediaFeedType' in item and not item['mediaFeedType'].startswith('IN_'):
                # check if our favorite team (if defined) is associated with this stream
                # or if no favorite team match, look for the home or national streams
                if (FAV_TEAM != 'None' and 'mediaFeedSubType' in item and item['mediaFeedSubType'] == getFavTeamId()) or (selected_content_id is None and 'mediaFeedType' in item and (item['mediaFeedType'] == 'HOME' or item['mediaFeedType'] == 'NATIONAL' )):
                    # prefer live streams (suspended games can have both a live and archived stream available)
                    if item['mediaState'] == 'MEDIA_ON':
                        selected_content_id = item['contentId']
                        selected_media_state = item['mediaState']
                        # once we've found a fav team live stream, we don't need to search any further
                        if FAV_TEAM != 'None' and 'mediaFeedSubType' in item and item['mediaFeedSubType'] == getFavTeamId():
                            break
                    # fall back to the first available archive stream, but keep search in case there is a live stream (suspended)
                    elif item['mediaState'] == 'MEDIA_ARCHIVE' and selected_content_id is None:
                        selected_content_id = item['contentId']
                        selected_media_state = item['mediaState']

    # fallback to manual stream selection if auto selection is disabled, bypassed, or didn't find anything, and we're not looking to force autoplay
    if selected_content_id is None and autoplay is False:
        # default stream selection list starts with highlights option
        stream_title = [LOCAL_STRING(30391)]
        highlight_offset = 1
        content_id = []
        media_state = []
        # if using Kodi's default resume ability, we'll omit highlights from our stream selection prompt
        if sys.argv[3] == 'resume:true':
            stream_title = []
            highlight_offset = 0

        # define some more variables used to handle suspended games
        airings = None
        game_date = None

        # if not live, if suspended, or if live and not resuming, add audio streams to the video streams
        if epg[0]['mediaState'] != "MEDIA_ON" or suspended != 'False' or (epg[0]['mediaState'] == "MEDIA_ON" and sys.argv[3] != 'resume:true'):
            epg += json_source['media']['epg'][2]['items']

        for item in epg:
            #xbmc.log(str(item))
            
            # video and audio streams use different fields to indicate home/away
            if 'mediaFeedType' in item:
                media_feed_type = str(item['mediaFeedType'])
            else:
                media_feed_type = str(item['type'])

            # only display if the stream is available (either live or archive) and not in_market
            if item['mediaState'] != 'MEDIA_OFF' and not media_feed_type.startswith('IN_'):
                title = media_feed_type.title()
                title = title.replace('_', ' ')

                # add TV to video stream
                if 'mediaFeedType' in item:
                    title += LOCAL_STRING(30392)
                # add language to audio stream
                else:
                    if item['language'] == 'en':
                        title += LOCAL_STRING(30394)
                    elif item['language'] == 'es':
                        title += LOCAL_STRING(30395)
                    title += LOCAL_STRING(30393)
                title = title + " (" + item['callLetters'] + ")"

                # modify stream title based on suspension status, if necessary
                if suspended != 'False':
                    suspended_label = 'partial'
                    try:
                        # if the game hasn't finished, we can simply tell the status from the mediaState
                        if suspended == 'live' and item['mediaState'] == 'MEDIA_ARCHIVE':
                            suspended_label = 'Suspended'
                        elif suspended == 'live':
                            suspended_label = 'Resumed'
                        # otherwise if the game is complete, we need to check the airings data
                        else:
                            if game_date is None and 'gameDate' in item:
                                game_date = item['gameDate']
                            if airings is None and game_date is not None:
                                airings = get_airings_data(game_pk=game_pk)
                            if game_date is not None and airings is not None and 'data' in airings and 'Airings' in airings['data']:
                                for airing in airings['data']['Airings']:
                                    if airing['contentId'] == item['contentId']:
                                        # compare the start date of the airing with the provided game_date
                                        start_date = get_eastern_game_date(parse(airing['startDate']))
                                        # same day means it is resumed
                                        if game_date == start_date:
                                            suspended_label = 'Resumed'
                                        # different day means it was suspended
                                        else:
                                            suspended_label = 'Suspended'
                                        break
                    except:
                        pass
                    title += ' (' + suspended_label + ')'

                # display blackout status for video, if available
                if 'mediaFeedType' in item and blackout != 'False':
                    title = blackoutString(title)
                    title += ' (blackout until ~'
                    if blackout == 'True':
                        title += '90 min. after'
                    else:
                        blackout_display_time = get_display_time(UTCToLocal(blackout))
                        title += blackout_display_time
                    title += ')'

                # insert home/national video streams at the top of the list
                if 'mediaFeedType' in item and ('HOME' in title.upper() or 'NATIONAL' in title.upper()):
                    content_id.insert(0, item['contentId'])
                    media_state.insert(0, item['mediaState'])
                    stream_title.insert(highlight_offset, title)
                # otherwise append other streams to end of list
                else:
                    content_id.append(item['contentId'])
                    media_state.append(item['mediaState'])
                    stream_title.append(title)

                # add an option to directly play live YouTube streams in YouTube add-on
                #if 'youtube' in item and 'videoId' in item['youtube']:
                #    content_id.insert(0, item['youtube']['videoId'])
                #    media_state.insert(0, item['mediaState'])
                #    stream_title.insert(highlight_offset, LOCAL_STRING(30414))

        # if we didn't find any streams, display an error and exit
        if len(stream_title) == 0:
            dialog.notification(LOCAL_STRING(30383), LOCAL_STRING(30384), ICON, 5000, False)
            xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
            sys.exit()

        # stream selection dialog
        n = dialog.select(LOCAL_STRING(30390), stream_title)
        # highlights selection will go to that function and stop processing here
        if n == 0 and highlight_offset == 1:
            highlight_select_stream(json_source['highlights']['highlights']['items'], from_context_menu=from_context_menu)
        # stream selection
        elif n > -1 and stream_title[n] != LOCAL_STRING(30391):
            # check if selected stream is a radio stream
            if LOCAL_STRING(30393) in stream_title[n]:
                stream_type = 'audio'
            # directly play live YouTube streams in YouTube add-on, if requested
            #if stream_title[n] == LOCAL_STRING(30414):
            #    xbmc.executebuiltin('RunPlugin("plugin://plugin.video.youtube/play/?video_id=' + content_id[n-highlight_offset] + '")')
            #    xbmcplugin.endOfDirectory(addon_handle)
            #else:
            selected_content_id = content_id[n-highlight_offset]
            selected_media_state = media_state[n-highlight_offset]
        # cancel will exit
        elif n == -1:
            sys.exit()

    # only proceed with start/skip dialogs if we have a content_id, either from auto-selection or the stream selection dialog
    if selected_content_id is not None:
        # need to log in to get the stream url and headers
        account = Account()
        # get the broadcast start offset and timestamp too, to know where to start playback and calculate skip markers, if necessary
        stream_url, headers, broadcast_start_offset, broadcast_start_timestamp = account.get_stream(selected_content_id)

        if selected_media_state == 'MEDIA_ON':
            is_live = True

        if stream_type == 'audio':
            skip_possible = False

        # only show the start point dialog if not using Kodi's default resume ability, the "ask to catch up" option is enabled, no start inning is specified, and we're not looking to autoplay
        if sys.argv[3] != 'resume:true' and CATCH_UP == 'true' and start_inning == 0 and autoplay is False:

            # for live video streams
            if selected_media_state == "MEDIA_ON" and stream_type == 'video':
                # begin with catch up, beginning, and live as start point options
                start_options = [LOCAL_STRING(30397), LOCAL_STRING(30398), LOCAL_STRING(30399)]
                # add inning start options
                start_options += get_inning_start_options()

                # start point selection dialog
                p = dialog.select(LOCAL_STRING(30396), start_options)
                # catch up
                if p == 0:
                    # create an item for the video stream
                    listitem = stream_to_listitem(stream_url, headers, description, name, icon, fanart)
                    # pass along the highlights and the video stream item to play as a playlist and stop processing here
                    highlight_select_stream(json_source['highlights']['highlights']['items'], catchup=listitem)
                    sys.exit()
                # beginning or inning
                elif p == 1 or p > 2:
                    # inning top/bottom calculation
                    if p > 2:
                        p = p - 2
                        start_inning, start_inning_half = calculate_inning_from_index(p)
                # live
                elif p == 2:
                    broadcast_start_offset = '-1'
                    skip_possible = False
                # cancel will exit
                elif p == -1:
                    sys.exit()

            # for live audio streams
            elif selected_media_state == "MEDIA_ON" and stream_type == 'audio':
                # start point selection dialog, with only catch up and live
                # omitting the beginning and inning start options (they don't work for live audio)
                p = dialog.select(LOCAL_STRING(30396), [LOCAL_STRING(30397), LOCAL_STRING(30399)])
                # catch up
                if p == 0:
                    # create an item for the audio stream
                    listitem = stream_to_listitem(stream_url, headers, description, name, icon, fanart, stream_type='audio', music_type_unset=True)
                    # pass along the highlights and the audio stream item to play as a playlist and stop processing here
                    highlight_select_stream(json_source['highlights']['highlights']['items'], catchup=listitem)
                    sys.exit()
                # cancel will exit
                elif p == -1:
                    sys.exit()

            # for archive video streams
            elif stream_type == 'video':
                # beginning is initial start point option
                start_options = [LOCAL_STRING(30398)]
                # add inning start options
                start_options += get_inning_start_options()
                # start point selection dialog
                p = dialog.select(LOCAL_STRING(30396), start_options)
                # inning
                if p > 0:
                    start_inning, start_inning_half = calculate_inning_from_index(p)
                # cancel will exit
                elif p == -1:
                    sys.exit()

        # show automatic skip dialog, if possible, enabled, and we're not looking to autoplay
        if skip_possible is True and ASK_TO_SKIP == 'true' and autoplay is False:
            # automatic skip dialog with options to skip nothing, breaks, breaks + idle time, breaks + idle time + non-action pitches
            skip_type = dialog.select(LOCAL_STRING(30403), [LOCAL_STRING(30404), LOCAL_STRING(30408), LOCAL_STRING(30405), LOCAL_STRING(30406)])
            # cancel will exit
            if skip_type == -1:
                sys.exit()

        # if autoplay, join live
        if autoplay is True:
            broadcast_start_offset = '-1'
        # if not live and no spoilers and not audio, generate a random number of segments to pad at end of proxy stream url
        elif is_live is False and spoiler == 'False' and stream_type != 'audio':
            pad = random.randint((3600 / SECONDS_PER_SEGMENT), (7200 / SECONDS_PER_SEGMENT))
            headers += '&pad=' + str(pad)
            stream_url = 'http://127.0.0.1:43670/' + stream_url

        # valid stream url
        if '.m3u8' in stream_url:
            play_stream(stream_url, headers, description, title=name, icon=icon, fanart=fanart, start=broadcast_start_offset, stream_type=stream_type, music_type_unset=from_context_menu)
            # start the skip monitor if a skip type or start inning has been requested and we have a broadcast start timestamp
            if (skip_type > 0 or start_inning > 0) and broadcast_start_timestamp is not None:
                mlbmonitor = MLBMonitor()
                mlbmonitor.skip_monitor(skip_type, game_pk, broadcast_start_timestamp, is_live, start_inning, start_inning_half)
        # otherwise exit
        else:
            sys.exit()


# select a stream for a featured video
def featured_stream_select(featured_video, name, description):
    xbmc.log('video select')
    account = Account()
    video_url = None
    # check if our request video is a URL
    if featured_video.startswith('http'):
        video_url = featured_video
    # otherwise assume it is a video title (used to call Big Inning from the schedule)
    else:
        xbmc.log('must search for video url with title')
        video_list = get_video_list()
        if 'items' in video_list:
            for item in video_list['items']:
                #xbmc.log(str(item))
                # live Big Inning title should start with LIVE and contain Big Inning
                if (featured_video == (LOCAL_STRING(30367) + LOCAL_STRING(30368)) and item['title'].startswith('LIVE') and 'Big Inning' in item['title']) or featured_video == item['title']:
                    xbmc.log('found match')
                    video_url = None
                    if 'fields' in item:
                        if 'playbackScenarios' in item['fields']:
                            for playback in item['fields']['playbackScenarios']:
                                if playback['playback'] == 'hlsCloud':
                                    video_url = playback['location']
                                    break
                        elif 'url' in item['fields']:
                            video_url = item['fields']['url']
    if video_url is None:
        xbmc.log('failed to find video URL for featured video')
        sys.exit()

    xbmc.log('video url : ' + video_url)
    video_stream_url = None
    # if it's not a Big Inning stream and it is HLS (M3U8) or MP4, we can simply stream the URL we already have
    if (not name.startswith('LIVE') or (name.startswith('LIVE') and 'Big Inning' not in name)) and (video_url.endswith('.m3u8') or video_url.endswith('.mp4')):
        video_stream_url = video_url
    # otherwise we need to authenticate and get the stream URL
    else:
        xbmc.log('fetching video stream from url')
        # need a special token for Big Inning
        okta_access_token = account.okta_access_token()
        if okta_access_token is None:
            xbmc.log('failed to get necessary okta access token')
            sys.exit()

        headers = {
            'User-Agent': UA_PC,
            'Authorization': 'Bearer ' + okta_access_token,
            'Accept': '*/*',
            'Origin': 'https://www.mlb.com',
            'Referer': 'https://www.mlb.com'
        }
        r = requests.get(video_url, headers=headers, verify=VERIFY)

        text_source = r.text
        #xbmc.log(text_source)

        # sometimes the returned content is already a stream playlist
        if text_source.startswith('#EXTM3U'):
            xbmc.log('video url is already a stream playlist')
            video_stream_url = video_url
        # otherwise it is JSON containing the stream URL
        else:
            json_source = r.json()
            if 'data' in json_source and len(json_source['data']) > 0 and 'value' in json_source['data'][0]:
                video_stream_url = json_source['data'][0]['value']
                xbmc.log('found video stream url : ' + video_stream_url)

    if video_stream_url is not None:
        headers = 'User-Agent=' + UA_PC
        if '.m3u8' in video_stream_url and QUALITY == 'Always Ask':
            video_stream_url = account.get_stream_quality(video_stream_url)
        # known issue warning: on Kodi 18 Leia WITHOUT inputstream adaptive, Big Inning starts at the beginning and can't seek
        # anyone with inputstream adaptive, or Kodi 19+, will not have this problem
        if name.startswith('LIVE') and 'Big Inning' in name and KODI_VERSION < 19 and not xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(30370), LOCAL_STRING(30369))
        play_stream(video_stream_url, headers, description, title=name, start='-1')
    else:
        xbmc.log('unable to find stream for featured video')


def list_highlights(game_pk, icon, fanart):
    url = API_URL + '/api/v1/game/' + game_pk + '/content'
    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    if 'highlights' in json_source and 'highlights' in json_source['highlights'] and 'items' in json_source['highlights']['highlights'] and len(json_source['highlights']['highlights']['items']) > 0:
        highlights = get_highlights(json_source['highlights']['highlights']['items'])
        if not highlights:
            msg = LOCAL_STRING(30383)
            dialog = xbmcgui.Dialog()
            dialog.notification(LOCAL_STRING(30391), msg, ICON, 5000, False)
            xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
            sys.exit()

        # play all
        liz=xbmcgui.ListItem(LOCAL_STRING(30411))
        liz.setInfo( type="Video", infoLabels={ "Title": LOCAL_STRING(30411), "plot": LOCAL_STRING(30411) } )
        if icon is None: icon = ICON
        if fanart is None: fanart = FANART
        liz.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
        liz.setProperty("IsPlayable", "true")
        u=sys.argv[0]+"?mode="+str(107)+"&game_pk="+urllib.quote_plus(str(game_pk))+"&fanart="+urllib.quote_plus(fanart)
        isFolder=False

        xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
        xbmcplugin.setContent(addon_handle, 'episodes')

        for clip in highlights:
            liz=xbmcgui.ListItem(clip['title'])
            liz.setInfo( type="Video", infoLabels={ "Title": clip['title'], "plot": clip['description'] } )
            liz.setArt({'icon': icon, 'thumb': clip['icon'], 'fanart': fanart})
            liz.setProperty("IsPlayable", "true")
            u=sys.argv[0]+"?mode="+str(301)+"&featured_video="+urllib.quote_plus(clip['url'])+"&name="+urllib.quote_plus(clip['title'])+"&description="+urllib.quote_plus(clip['description'])
            isFolder=False

            xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=isFolder)
            xbmcplugin.setContent(addon_handle, 'episodes')


def play_all_highlights_for_game(game_pk, fanart):
    url = API_URL + '/api/v1/game/' + game_pk + '/content'
    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    if 'highlights' in json_source and 'highlights' in json_source['highlights'] and 'items' in json_source['highlights']['highlights'] and len(json_source['highlights']['highlights']['items']) > 0:
        highlights = get_highlights(json_source['highlights']['highlights']['items'])
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        for clip in highlights:
            listitem = xbmcgui.ListItem(clip['url'])
            listitem.setArt({'icon': clip['icon'], 'thumb': clip['icon'], 'fanart': fanart})
            listitem.setInfo(type="Video", infoLabels={"Title": clip['title'], "plot": clip['description']})
            playlist.add(clip['url'], listitem)

        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=playlist[0])


def highlight_select_stream(json_source, catchup=None, from_context_menu=False):
    highlights = get_highlights(json_source)
    if not highlights and catchup is None:
        msg = LOCAL_STRING(30383)
        dialog = xbmcgui.Dialog()
        dialog.notification(LOCAL_STRING(30391), msg, ICON, 5000, False)
        xbmcplugin.setResolvedUrl(addon_handle, False, xbmcgui.ListItem())
        sys.exit()

    highlight_name = []
    highlight_url = []
    highlight_description = []
    if from_context_menu is False:
        highlight_name.append(LOCAL_STRING(30411))
        highlight_url.append('blank')
        highlight_description.append(LOCAL_STRING(30411))

    for clip in highlights:
        highlight_name.append(clip['title'])
        highlight_url.append(clip['url'])
        highlight_description.append(clip['description'])

    if catchup is None:
        dialog = xbmcgui.Dialog()
        a = dialog.select('Choose Highlight', highlight_name)
    else:
        a = 0

    if a > 0:
        headers = 'User-Agent=' + UA_PC
        play_stream(highlight_url[a], headers, highlight_description[a], highlight_name[a])
    elif a == 0:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()

        for clip in highlights:
            listitem = xbmcgui.ListItem(clip['url'])
            listitem.setArt({'icon': clip['icon'], 'thumb': clip['icon'], 'fanart': FANART})
            listitem.setInfo(type="Video", infoLabels={"Title": clip['title'], "plot": clip["description"]})
            playlist.add(clip['url'], listitem)

        if catchup is not None:
            playlist.add(catchup.getPath(), catchup)

        xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=playlist[0])
    elif a == -1:
        sys.exit()


def play_stream(stream_url, headers, description, title, icon=None, fanart=None, start='1', stream_type='video', music_type_unset=False):
    listitem = stream_to_listitem(stream_url, headers, description, title, icon, fanart, start=start, stream_type=stream_type, music_type_unset=music_type_unset)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=listitem)


def get_highlights(items):
    xbmc.log(str(items))
    highlights = []
    for item in sorted(items, key=lambda x: x['date']):
        for playback in item['playbacks']:
            if 'hlsCloud' in playback['name']:
                clip_url = playback['url']
                break
        headline = item['headline']
        icon = item['image']['cuts'][0]['src']
        description = item['blurb']
        highlights.append({'url': clip_url, 'title': headline, 'icon': icon, 'description': description})

    return highlights


# Play all recaps or condensed games when a date is selected
def playAllHighlights(stream_date):
    dialog = xbmcgui.Dialog()
    n = dialog.select(LOCAL_STRING(30400), [LOCAL_STRING(30401), LOCAL_STRING(30402)])
    if n == -1:
        sys.exit()

    url = API_URL + '/api/v1/schedule'
    url += '?hydrate=game(content(highlights(highlights)))'
    url += '&sportId=1,51'
    url += '&date=' + stream_date

    headers = {
        'User-Agent': UA_ANDROID
    }
    r = requests.get(url, headers, verify=VERIFY)
    json_source = r.json()

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()

    for game in json_source['dates'][0]['games']:
        try:
            fanart = 'http://cd-images.mlbstatic.com/stadium-backgrounds/color/light-theme/1920x1080/%s.png' % game['venue']['id']
            if 'highlights' in game['content']:
                for item in game['content']['highlights']['highlights']['items']:
                    try:
                        title = item['headline']
                        if (n == 0 and title.endswith(' Highlights')) or (n == 1 and item['headline'].startswith('CG: ')):
                            for playback in item['playbacks']:
                                if 'hlsCloud' in playback['name']:
                                    clip_url = playback['url']
                                    break
                            listitem = xbmcgui.ListItem(clip_url)
                            icon = item['image']['cuts'][0]['src']
                            listitem.setArt({'icon': icon, 'thumb': icon, 'fanart': fanart})
                            listitem.setInfo(type="Video", infoLabels={"Title": title})
                            xbmc.log('adding recap to playlist : ' + title)
                            playlist.add(clip_url, listitem)
                    except:
                        pass
        except:
            pass

    xbmc.Player().play(playlist)


# get the airings data, which contains the start time of the broadcast(s)
def get_airings_data(content_id=None, game_pk=None):
    xbmc.log('Get airings data')
    url = 'https://search-api-mlbtv.mlb.com/svc/search/v2/graphql/persisted/query/core/Airings'
    headers = {
        'Accept': 'application/json',
        'X-BAMSDK-Version': '4.3',
        'X-BAMSDK-Platform': 'macintosh',
        'User-Agent': UA_PC,
        'Origin': 'https://www.mlb.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-type': 'application/json'
    }
    if content_id is not None:
        data = {
            'variables': '%7B%22contentId%22%3A%22' + content_id + '%22%7D'
        }
    else:
        data = {
            'variables': '{%22partnerProgramIds%22%3A[%22' + str(game_pk) + '%22]}'
        }
    r = requests.get(url, headers=headers, params=data, verify=VERIFY)
    json_source = r.json()

    return json_source


# check blackout status
def get_blackout_status(game, suspended='False', scheduled_innings=9):
    blackout_type = 'False'
    blackout_time = None
    if re.match('^[0-9]{5}$', ZIP_CODE) and 'content' in game and 'media' in game['content'] and 'epg' in game['content']['media'] and len(game['content']['media']['epg']) > 0 and 'items' in game['content']['media']['epg'][0] and len(game['content']['media']['epg'][0]['items']) > 0 and 'mediaFeedType' in game['content']['media']['epg'][0]['items'][0] and game['content']['media']['epg'][0]['items'][0]['mediaFeedType'] == 'NATIONAL':
        blackout_type = 'National'
    elif game['seriesDescription'] != 'Spring Training' and (game['teams']['away']['team']['abbreviation'] in BLACKOUT_TEAMS or game['teams']['home']['team']['abbreviation'] in BLACKOUT_TEAMS):
        blackout_type = 'Local'

    # also calculate a blackout time for non-suspended, non-TBD games
    if blackout_type != 'False' and suspended == 'False' and game['status']['startTimeTBD'] is False:
        # avg 9 inning game was 3:11 in 2021, or 21.22 minutes per inning
        gameDurationMinutes = 21.22 * scheduled_innings
        # default to assuming the scheduled game time is the first pitch time
        firstPitch = parse(game['gameDate'])
        if 'gameInfo' in game:
            # check if firstPitch has been updated with a valid time (later than the scheduled game time)
            if 'firstPitch' in game['gameInfo'] and game['gameInfo']['firstPitch'] >= game['gameDate']:
                firstPitch = parse(game['gameInfo']['firstPitch'])
            # for completed games, get the duration too
            if 'gameDurationMinutes' in game['gameInfo']:
                gameDurationMinutes = game['gameInfo']['gameDurationMinutes']
                # add any delays
                if 'delayDurationMinutes' in game['gameInfo']:
                    gameDurationMinutes += game['gameInfo']['delayDurationMinutes']
        gameDurationMinutes += 90
        blackout_time = firstPitch + timedelta(minutes=gameDurationMinutes)

    return blackout_type, blackout_time


def live_fav_game():
    game_day = localToEastern()

    auto_play_game_date = str(settings.getSetting(id='auto_play_game_date'))

    game_pk = None

    fav_team_id = getFavTeamId()

    # don't check if don't have a fav team id or if we've already flagged today's fav games as complete
    if fav_team_id is not None and auto_play_game_date != game_day:
        # don't check more often than 5 minute intervals
        auto_play_game_checked = str(settings.getSetting(id='auto_play_game_checked'))
        now = datetime.now()
        if auto_play_game_checked == '' or (parse(auto_play_game_checked) + timedelta(minutes=5)) < now:
            settings.setSetting(id='auto_play_game_checked', value=str(now))

            url = API_URL + '/api/v1/schedule'
            url += '?hydrate=game(content(media(epg)))'
            url += '&sportId=1,51'
            url += '&teamId=' + fav_team_id
            url += '&date=' + game_day

            headers = {
                'User-Agent': UA_ANDROID
            }
            r = requests.get(url,headers=headers, verify=VERIFY)
            json_source = r.json()

            upcoming_game = False

            if 'dates' in json_source and len(json_source['dates']) > 0 and 'games' in json_source['dates'][0]:
                for game in json_source['dates'][0]['games']:
                    try:
                        # only check games that aren't final
                        if game['status']['abstractGameState'] != 'Final':
                            # also only check games that aren't blacked out
                            blackout_type, blackout_time = get_blackout_status(game)
                            if blackout_type == 'False':
                                if 'content' in game and 'media' in game['content'] and 'epg' in game['content']['media'] and len(game['content']['media']['epg']) > 0 and 'items' in game['content']['media']['epg'][0]:
                                    for epg in game['content']['media']['epg'][0]['items']:
                                        # if media is off, assume it is still upcoming
                                        if epg['mediaState'] == 'MEDIA_OFF':
                                            upcoming_game = True
                                        # if media is on, that means it is live
                                        elif game_pk is None and epg['mediaState'] == 'MEDIA_ON':
                                            game_pk = str(game['gamePk'])
                                            xbmc.log('Found live fav game ' + game_pk)
                    except:
                        pass

            # set the date setting if there are no more upcoming fav games today
            if upcoming_game is False:
                xbmc.log('No more upcoming fav games today')
                settings.setSetting(id='auto_play_game_date', value=game_day)

    return game_pk
