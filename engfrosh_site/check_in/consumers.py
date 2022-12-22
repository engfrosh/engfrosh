from channels import Group
def ws_connect(message):
    Group('users').add(message.reply_channel)
    ws_publish('1','2','3')
def ws_disconnect(message):
    Group('users').discard(message.reply_channel)

def ws_publish(location, size, team):
    Group('users').send({
        json.dumps({
            'location': location,
            'size': size,
            'team': team
        })
