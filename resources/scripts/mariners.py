import xbmc
xbmc.log('TEDROMER hi favourite', level=xbmc.LOGNOTICE)
json = '{"jsonrpc": "2.0", "method": "Addons.ExecuteAddon","params": {"addonid": "plugin.video.mlbtv","params": {"mode" : "600"}},"id": 1}'
resp = xbmc.executeJSONRPC(json)
xbmc.log('TEDROMER resp %s ' % resp, level=xbmc.LOGNOTICE)
