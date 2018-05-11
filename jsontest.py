import json

# example dictionary that contains data like you want to have in json
dic={'age': 100, 'name': 'mkyong.com', 'messages': ['msg 1', 'msg 2', 'msg 3']}
#1second data:
# wavespectra
#   period
#   response
# wakespectra
#   boatlength
#   response
# waterheight
# seawaveheight

# get json string from that dictionary
json=json.dumps(dic)
print json
