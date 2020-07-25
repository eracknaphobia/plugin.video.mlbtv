from resources.lib.mlb import *

xbmc.log('TEDROMER main', level=xbmc.LOGNOTICE)
                             
params = get_params()
name = None
mode = None
game_day = None
game_pk = None
gid = None
teams_stream = None
stream_date = None

if 'name' in params:
    name = urllib.unquote_plus(params["name"])

if 'mode' in params:
    mode = int(params["mode"])

if 'game_day' in params:
    game_day = urllib.unquote_plus(params["game_day"])

if 'game_pk' in params:
    game_pk = urllib.unquote_plus(params["game_pk"])

if 'teams_stream' in params:
    teams_stream = urllib.unquote_plus(params["teams_stream"])

if 'stream_date' in params:
    stream_date = urllib.unquote_plus(params["stream_date"])

xbmc.log('TEDROMER mode is %s' % mode, level=xbmc.LOGNOTICE)
if mode is None:
    categories()
    xbmc.log('TEDROMER finished categories')
    xbmcplugin.endOfDirectory(addon_handle)

elif mode == 100:
    todays_games(None)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False)                  

elif mode == 101:
    # Prev and Next
    todays_games(game_day)
    xbmcplugin.endOfDirectory(addon_handle, cacheToDisc=False, updateListing=True)


elif mode == 104:
    stream_select(game_pk)

elif mode == 105:
    # Yesterday's Games
    game_day = localToEastern()
    display_day = stringToDate(game_day, "%Y-%m-%d")
    prev_day = display_day - timedelta(days=1)
    todays_games(prev_day.strftime("%Y-%m-%d"))
    xbmcplugin.endOfDirectory(addon_handle)

elif mode == 200:
    # Goto Date
    search_txt = ''
    dialog = xbmcgui.Dialog()
    game_day = dialog.input('Enter date (yyyy-mm-dd)', type=xbmcgui.INPUT_ALPHANUM)
    mat = re.match('(\d{4})-(\d{2})-(\d{2})$', game_day)
    if mat is not None:
        todays_games(game_day)
        xbmcplugin.endOfDirectory(addon_handle)
    else:
        if game_day != '':
            msg = "The date entered is not in the format required."
            dialog = xbmcgui.Dialog()
            dialog.ok('Invalid Date', msg)

        sys.exit()

elif mode == 400:
    account = Account()
    account.logout()
    dialog = xbmcgui.Dialog()
    title = "Logout Successful"
    dialog.notification(title, 'Logout completed successfully', ICON, 5000, False)

elif mode == 500:
    myTeamsGames()
    xbmcplugin.endOfDirectory(addon_handle)                   

elif mode == 600:
    xbmc.log('play_teams_game', level=xbmc.LOGNOTICE)
    play_teams_game('136', 'RSNW')
    # play_teams_game('142', 'MASN')  # orioles
    # play_teams_game('137', 'NBCSBA')  # giants
    

elif mode == 900:
    getGamesForDate(stream_date)
    playAllHighlights()
    # TODO needed?
    xbmcplugin.endOfDirectory(addon_handle)

elif mode == 999:
    sys.exit()
