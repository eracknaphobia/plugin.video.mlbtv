import xbmc
json = '{"jsonrpc": "2.0", "method": "Addons.ExecuteAddon","params": {"addonid": "plugin.video.mlbtv2","params": {"mode" : "101"}},"id": 1}'
xbmc.executeJSONRPC(json)
