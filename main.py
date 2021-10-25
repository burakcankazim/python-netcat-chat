import json
import nclib as nc
import asyncio
import PySimpleGUI as sg
import sys

ipaddress = sys.argv[1]
username = sys.argv[2]
ip_range = ipaddress[0:ipaddress.rfind(".")]

users = {}
messages = {}
upd = True
upd_chat = False


def listen():
    global upd
    global upd_chat
    listen = nc.Netcat(listen=12345, verbose=True, raise_eof=False)
    while True:
        packet = listen.read().decode('utf-8')
        try:
            response = json.loads(packet)
            if response["type"] == 1:
                listen.send('{ "type":2, "name":"'+username+'", "IP":"'+ipaddress+'"}')
                if response["name"] is not None and response["IP"] is not None:
                    users[response["name"]] = (response["IP"], [])
                    upd = True
            elif response["type"] == 3:
                if response["name"] is not None and response["body"] is not None and list(users.keys()).count(
                        response["name"]) != 0:
                    users[response["name"]][1].append((1, response["body"]))
                    upd_chat = True
        except:
            pass


def discover():
    global upd
    for octet in range(221, 224):
        try:
            sent = nc.Netcat((ip_range + "." + str(octet), 12345), raise_timeout=True)
            sent.send('{ "type":1, "name":"'+username+'", "IP":"'+ipaddress+'"}')

            packet = sent.read()
            try:
                response = json.loads(packet)
                if response["type"] == 2:
                    if response["name"] is not None and response["IP"] is not None:
                        users[response["name"]] = (response["IP"], [])
                        upd = True
            except:
                print(packet)

            sent.close()
        except Exception as e:
            print(e)


def chat_messages(user):
    try:
        result = []
        chat_log = users[user][1]
        for message in chat_log:
            if message[0] == 0:
                result.append("You:")
                result.append(message[1])
            if message[0] == 1:
                result.append(user + ":")
                result.append(message[1])
        return result
    except  Exception as e:
        print(e)

chatuser=""

def gui():
    global upd
    global upd_chat
    global chatuser
    user_list = [
        [
            sg.Text("Deneme"),
            sg.Button("Refresh", key="refresh")
        ],
        [
            sg.Listbox(
                values=list(users.values()),
                enable_events=True, size=(40, 20), key="userlist"
            )
        ]
    ]

    chat = [
        [
            sg.Text("Chat"),

        ],
        [
            sg.Listbox(
                values=[],
                key="chat",
                size=(60, 19)
            ),
        ],
        [
            sg.Input("Your message", size=(55, 1), k="chatbox"),
            sg.Button("Send", size=(5, 1), k="send", bind_return_key=True, disabled=True)
        ]
    ]

    layout = [
        [
            sg.Column(user_list),
            sg.VSeparator(),
            sg.Column(chat)
        ]
    ]

    window = sg.Window("Image Viewer", layout)
    while True:
        event, values = window.read(timeout=1)

        if event == "refresh":
            window["userlist"].update(users)

        if event == "userlist":
            try:
                chatuser=values["userlist"][0]
                window["chat"].update(chat_messages(values["userlist"][0]))
                window["send"].update(disabled=False)
                window["userlist"].update(users)
            except:
                pass

        if upd_chat:
            try:
                window["chat"].update(chat_messages(chatuser))
                window["userlist"].update(users)
                upd_chat = False
            except:
                pass

        if event == "send":
            try:
                if chatuser != "":
                    r = send_message(chatuser, values["chatbox"])
                    if r == 1:
                        window["chat"].update([])
                        window["chatbox"].update("")
                        window["send"].update(disabled=True)
                    else:
                        window["chat"].update(chat_messages(chatuser))
                        window["chatbox"].update("")
            except Exception as e:
                print(e)
        if event == "OK" or event == sg.WIN_CLOSED:
            break

def send_message(name, body):
    try:
        ip = users[name][0]
        sent = nc.Netcat((ip, 12345), raise_timeout=True)
        sent.send('{"type":3, "name":"' + username + '", "body":"' + body + '"}')
        sent.close()
        users[name][1].append((0, body))
    except Exception as e:
        if list(users.keys()).count(name) != 0:
            users.pop(name)
        return 1

async def main():
    await asyncio.gather(
        asyncio.to_thread(listen),
        asyncio.to_thread(discover),
        asyncio.to_thread(gui),
    )
asyncio.run(main())
