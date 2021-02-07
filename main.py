#!/usr/bin/env python3
import sys
import os
import json
assert sys.version_info >= (3,9), "This script requires at least Python 3.9"

# Helper functions

# import os,json
def load(l):
    f = open(os.path.join(sys.path[0], l))
    data = f.read()
    j = json.loads(data)
    return j

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def find_passage(game, pid):
    for p in game["passages"]:
        if p["pid"] == pid:
            return p
    # failed to find passage
    return {}

def get_links(node):
    try:
        return node["links"]
    except KeyError:
        return []

def checkmatch(msg, x, string):
    return msg[x : x + len(string)] == string

def whatitem(msg, x, string):
    return msg[x + len(string):].split(";",1)[0]

def format_link(string, number, game):
    #print("FORMATTING LINK: " + string)
    msg = string[2:-2]
    n = "(" + str(number) + ") "
    if "%" in msg:
        x = 0
        while x < len(msg):
            if checkmatch(msg, x, "%need:"):
                item = whatitem(msg, x, "%need:")
                if not item in game["inventory"]:
                    return ""
                msg = msg[:x] + msg[x + len("%need:" + item) + 1:]
                x = x - 1
            if checkmatch(msg, x, "%prohibit:"):
                item = whatitem(msg, x, "%remove:")
                if item in game["inventory"]:
                    return ""
                msg = msg[:x] + msg[x + len("%prohibit:" + item) + 1:]
                x = x - 1
            x = x + 1
    if "->" in msg:
        return n + msg.split("->")[0]
    elif "<-" in msg:
        return n + msg.split("<-")[1]
    else:
        return n + msg

def show_inv(game):
    msg = ""
    inventory = game["inventory"]
    for i in inventory:
        msg = msg + i + ", "
    if len(inventory) == 0:
        print("Your inventory is empty.")
        return
    print(msg[:-2])

def update_inventory(node, game):
    msg = node["text"]
    x = 0
    while x < len(msg):
        if checkmatch(msg, x, "%give:"):
            item = whatitem(msg, x, "%give:")
            game["inventory"].append(item)
        if checkmatch(msg, x, "%remove:"):
            item = whatitem(msg, x, "%remove:")
            game["inventory"].remove(item)
        x = x + 1

# Game Loop

def render(node, game):
    msg = node["text"]
    inbrackets = False
    bracketstart = 0
    x = 0
    linknumber = 0
    while x < len(msg):
        c = msg[x]
        if x < len(msg) - 1 and msg[x] + msg[x + 1] == "[[" and not inbrackets:
            inbrackets = True
            bracketstart = x
        if x < len(msg) - 1 and msg[x] + msg[x + 1] == "]]" and inbrackets:
            linknumber = linknumber + 1
            linktext = format_link(msg[bracketstart:x + 2], linknumber, game)
            inbrackets = False
            msg = msg[:bracketstart] + linktext + msg[x + 2:]
            x = bracketstart + len(linktext) - 1
        #   "%give:EGG;"
        #   12345678901
        if checkmatch(msg, x, "%give:"):
            item = whatitem(msg, x, "%give:")
            msg = msg[:x] + msg[x + len("%give:" + item) + 1:]
            x = x - 1
        if checkmatch(msg, x, "%remove:"):
            item = whatitem(msg, x, "%remove:")
            msg = msg[:x] + msg[x + len("%remove:" + item) + 1:]
            x = x - 1
        x = x + 1
    print(msg)

def get_input(node, game):
    answer = ""
    # input validation
    valid = []
    nlinks = len(get_links(node))
    for l in range(0, nlinks):
        keep = True
        name = get_links(node)[l]["name"]
        if "%" in name:
            x = 0
            while x < len(name):        # i probably should have deferred these to functions
                if checkmatch(name, x, "%need:"):
                    item = whatitem(name, x, "%need:")
                    if not item in game["inventory"]:
                        keep = False
                        break
                if checkmatch(name, x, "%prohibit:"):
                    item = whatitem(name, x, "%prohibit:")
                    if not item in game["inventory"]:
                        keep = False
                        break
                x = x + 1
        if keep:
            valid.append(str(l + 1)) # this gets me ["1", "2", "3"...]
    valid.append("quit")
    print(valid)
    pressenter = False
    while(answer not in valid and not pressenter):
        answer = input("> ")
        if answer == "inv":
            show_inv(game)
        if nlinks == 0:
            pressenter = True
    return answer

def update(node, game, choice):
    links = get_links(node)
    if len(links) == 0:
        return {}
    if (is_int(choice)):
        dest = links[int(choice) - 1]["pid"]
        nextnode = find_passage(game, dest)
        update_inventory(nextnode, game)
        return nextnode
    return node

# Main

def main():
    while(True):
        print("\n\n\nWhich game do you want to load?")
        msg = ""
        jsonfiles = []
        for f in os.listdir():
            if f.endswith(".json"):
                msg = msg + f + "\t"
                jsonfiles.append(f)
        print(msg)
        gamefilename = ""
        while (not gamefilename in jsonfiles):
            gamefilename = input("> ")
        game = load(gamefilename)
        print(game["name"] + " by " + game["creator"])
        print("Input 'inv' to check your inventory")
        print("Input 'quit' anytime to quit the game")
        print("Press enter to start")
        input("> ")
        node = find_passage(game, game["startnode"])
        choice = ""
        game["inventory"] = []
        update_inventory(node, game)
        while (choice != "quit" and node != {}):
            render(node, game)
            choice = get_input(node, game)
            node = update(node, game, choice)
        print("The game has ended.")
        if choice != "quit":
            input("> ")

if __name__ == "__main__":
    main()