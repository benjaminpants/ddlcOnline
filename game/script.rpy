## script.rpy

# This is the main script that Ren'Py calls upon to start
# your mod's story! 

label start:

    # This label configures the anticheat number for the game after Act 1.
    # It is recommended to leave this as-is and use the following in your script:
    #   $ persistent.anticheat = renpy.random.randint(X, Y) 
    #   X - The minimum number | Y - The maximum number
    $ anticheat = persistent.anticheat

    # This variable sets the chapter number to 0 to use in the mod.
    $ chapter = 0

    # This variable controls whether the player can dismiss a pause in-game.
    $ _dismiss_pause = config.developer

    ## Names of the Characters
    # These variables set up the names of the characters in the game.
    # To add a character, use the following example below: 
    #   $ mi_name = "Mike". 
    # Don't forget to add the character to 'definitions.rpy'!
    $ s_name = "???"
    $ m_name = "Girl 3"
    $ n_name = "Girl 2"
    $ y_name = "Girl 1"

    # This variable controls whether the quick menu in the textbox is enabled.
    $ quick_menu = True

    # This variable c ontrols whether we want normal or glitched dialogue
    # For glitched dialogue, use 'style.edited'.
    $ style.say_dialogue = style.normal

    # This variable controls whether Sayori is dead. It is recommended to leave
    # this as-is.
    $ in_sayori_kill = None
    
    # These variables controls whether the player can skip dialogue or transitions.
    $ allow_skipping = True
    $ config.allow_skipping = True

    ## The Main Part of the Script
    # This is where your script code is called!
    # 'persistent.playthrough' controls the playthrough number the player is on i.e (Act 1, 2, 3, 4)

    # REMOVE THIS LINE WHEN YOU HAVE MADE A STORY SCRIPT FILE AND CALLED IT HERE
    # call screen dialog(message="It seems that you are trying to run the mod template as a new game with no story.\nThis is a template, not an actual mod. Please code a story for your mod, call it in \'script.rpy\', and try again.", ok_action=MainMenu(confirm=False))

    play music t4
    $ ip = renpy.input("IP Address:",default=persistent.last_ip,length=16)
    $ port = int(renpy.input("Port:",default=persistent.last_port,length=8))
    $ persistent.last_ip = ip
    $ persistent.last_port = port
    "About to attempt a connection.\nPlease note that once this starts you wont be able to go back to the main menu."
    "If the game freezes, close it with ALT+F4"

    $ network_objects = []

    $ room_messages = {}

    $ in_net_loop = False

    $ waiting_for_update = False

    # testing
    python:
        from shared import *
        from network import *
        import json

        def get_object_from_id(id):
            for obj in network_objects:
                if (obj.id == id):
                    return obj
            return None

        def get_player_actor(ply_id):
            return get_object_from_id(get_object_from_id(ply_id).actor_id)

        def return_to_network():
            waiting_for_update = False

        def print_network_objs():
            print("-OBJECT LIST-")
            for x in network_objects:
                print(x)

        def on_packet(self,id,data):
            if (id == "chat"):
                room_messages[data["room"]] = (data["name"],data["message"])
                return_to_network()
                return True
            elif (id == "add_object"):
                print("Being told to add Object by server...")
                network_objects.append(network_deserialize_object_no_base(json.loads(data["object"])))
                print_network_objs()
                return True
            elif (id == "delete_object"):
                print("Being told to delete Object by server...")
                network_objects.remove(get_object_from_id(data["object"]))
                print_network_objs()
                return True
            elif (id == "changeusername"):
                print(str(data["sender_id"]) + " changing names...")
                get_object_from_id(data["sender_id"]).username = data["username"]
                return True
            elif (id == "change_char"):
                print(str(data["sender_id"]) + " changing outfit...")
                get_player_actor(data["sender_id"]).character = data["character"]
                return_to_network()
                return True
            elif (id == "change_room"):
                print(str(data["sender_id"]) + " changing room...")
                get_player_actor(data["sender_id"]).room = data["room"]
                return_to_network()
                if data["sender_id"] == net.id:
                    update_room()
                return True
            elif (id == "change_net"):
                print(str(data["id"]) + " changing data...")
                data_to_change = data["data"]
                print(data_to_change)
                the_obj = get_object_from_id(data["id"])
                for key in data_to_change.keys():
                    setattr(the_obj,key,data_to_change[key])
                    print("setting attribute:" + key)
            return False

        net = Network((ip,port),on_packet)
        js_dat = json.loads(net.greetingpacket)
        print(net.greetingpacket)
        net.id = js_dat["player"] #get my player id
        net.key = js_dat["secret"]
        cur_map = Map(0,{}).deserialize(json.loads(js_dat["map"])) #deserialize the map
        network_objects = network_deserialize_objects(js_dat["netobjs"])
        room_messages_temp = json.loads(js_dat["room_messages"])
        for rm in room_messages_temp.keys():
            room_messages[rm] = tuple(room_messages_temp[rm])
        print_network_objs()
        
        # welp, the servers given us the data we wanted, lets send our data.
        net.send(network_create_packet({
            "type":"changeusername",
            "username":persistent.playername
            #"secret":net.key, #is the private key system even needed?
        }),False)

    $ in_net_loop = True
    $ my_actor = get_player_actor(net.id)

    python:
        #import atexit
        def update_room():
            renpy.scene()
            renpy.show(cur_map.rooms[my_actor.room].asset[1])
        update_room()
        #atexit.unregister(disconnect_network)
        #atexit.register(disconnect_network)

    # define this because i hate my life
    python:
        characters_InScene = []
        old_characters_InScene = []
        def update_all_characters(focused_char): # i copied this directly from ddlc AI fuck you.
            renpy.scene("ch_preview")
            renpy.show(my_actor.character,[globals()["tinycorner"]],layer="ch_preview")
            for old in old_characters_InScene:
                if not (old in characters_InScene):
                    renpy.hide(old[1])
            for i in range(len(characters_InScene)):
                curAtChar = characters_InScene[i][1]
                animType = "t"
                if characters_InScene[i][0] == focused_char:
                    animType = "f"
                
                renpy.show(curAtChar,[globals()[animType + str(len(characters_InScene)) + str(i + 1)]],tag="CH_" + str(i))
        
        def update_characters_list():
            global characters_InScene
            global old_characters_InScene
            old_characters_InScene = characters_InScene
            characters_InScene = []
            for obj in network_objects:
                if (obj.id == my_actor.id):
                    continue
                elif (obj.type == "playeractor"):
                    if obj.room == my_actor.room:
                        char_tuple = (obj.name,obj.character)
                        characters_InScene.append(char_tuple)
label network_loop:
    python:
        talk_tuple_og = room_messages[my_actor.room]
        talk_tuple = room_messages[my_actor.room]
        waiting_for_update = True
        update_characters_list()
        update_all_characters(talk_tuple[0])
        # handle the dialogue part
        if (talk_tuple[0] == ""):
            renpy.say(None,talk_tuple[1] + "{nw}")
        else:
            renpy.say(talk_tuple[0],talk_tuple[1] + "{nw}")
        while waiting_for_update and talk_tuple == talk_tuple_og and net.connected:
            update_characters_list()
            update_all_characters(talk_tuple[0])
            if (talk_tuple[0] == ""):
                renpy.say(None,talk_tuple[1] + "{fast}{w=1.0}{nw}{done}")
            else:
                renpy.say(talk_tuple[0],talk_tuple[1] + "{fast}{w=1.0}{nw}{done}")
            talk_tuple = room_messages[my_actor.room]
    if net.connected:
        jump network_loop #THERE IS NO ESCAPE!


label disconnect:
    $ in_net_loop = False

    $ net.disconnect()

    $ renpy.scene("ch_preview")
    "You've been disconnected.\nIf this disconnection was manual, please restart the game.\nManual disconnects are extremely buggy at the moment."
    return

    ## Example on calling scripts from DDLC.
    # if persistent.playthrough == 0:
    #     # This variable sets the chapter number to X depending on the chapter
    #     # your player is experiencing ATM.
    #     $ chapter = 0

    #     # This call statement calls your script label to be played.
    #     call ch0_main
        
    #     # This call statement calls the poem mini-game to be played.
    #     call poem

    #     ## Day 1
    #     $ chapter = 1
    #     call ch1_main

    #     # This call statement calls the poem sharing minigame to be played.
    #     call poemresponse_start
    #     call ch1_end

    #     call poem

    #     ## Day 2
    #     $ chapter = 2
    #     call ch2_main
    #     call poemresponse_start
    #     call ch2_end

    #     call poem

    #     ## Day 3
    #     $ chapter = 3
    #     call ch3_main
    #     call poemresponse_start
    #     call ch3_end

    #     ## Day 4
    #     $ chapter = 4
    #     call ch4_main

    #     # This python statement writes a file from within the game to the game folder
    #     # or to the Android/data/[modname]/files/game folder.
    #     python:
    #         if renpy.android and renpy.version_tuple == (6, 99, 12, 4, 2187):
    #             try: file(os.environ['ANDROID_PUBLIC'] + "/hxppy thxughts.png")
    #             except IOError: open(os.environ['ANDROID_PUBLIC'] + "/hxppy thxughts.png", "wb").write(renpy.file("hxppy thxughts.png").read())
    #         elif renpy.android:
    #             try: renpy.file(os.environ['ANDROID_PUBLIC'] + "/hxppy thxughts.png")
    #             except IOError: open(os.environ['ANDROID_PUBLIC'] + "/hxppy thxughts.png", "wb").write(renpy.file("hxppy thxughts.png").read())
    #         else:
    #             try: renpy.file(config.basedir + "/hxppy thxughts.png")
    #             except IOError: open(config.basedir + "/hxppy thxughts.png", "wb").write(renpy.file("hxppy thxughts.png").read())

    #     ## Day 5
    #     $ chapter = 5
    #     call ch5_main

    #     # This call statement ends the game but doesn't play the credits.
    #     call endgame
    #     return

    # elif persistent.playthrough == 1:
    #     $ chapter = 0
    #     call ch10_main
        
    #     # This jump statement jumps over to Act 2 from Act 1.
    #     jump playthrough2


    # elif persistent.playthrough == 2:
    #     ## Day 1 - Act 2
    #     $ chapter = 0
    #     call ch20_main
    #     label playthrough2:
    #         call poem

    #         python:
    #             if renpy.android and renpy.version_tuple == (6, 99, 12, 4, 2187):
    #                 try: file(os.environ['ANDROID_PUBLIC'] + "/CAN YOU HEAR ME.txt")
    #                 except IOError: open(os.environ['ANDROID_PUBLIC'] + "/CAN YOU HEAR ME.txt", "wb").write(renpy.file("CAN YOU HEAR ME.txt").read())
    #             elif renpy.android:
    #                 try: renpy.file(os.environ['ANDROID_PUBLIC'] + "/CAN YOU HEAR ME.txt")
    #                 except IOError: open(os.environ['ANDROID_PUBLIC'] + "/CAN YOU HEAR ME.txt", "wb").write(renpy.file("CAN YOU HEAR ME.txt").read())
    #             else:
    #                 try: renpy.file(config.basedir + "/CAN YOU HEAR ME.txt")
    #                 except IOError: open(config.basedir + "/CAN YOU HEAR ME.txt", "wb").write(renpy.file("CAN YOU HEAR ME.txt").read())

    #         ## Day 2 - Act 2
    #         $ chapter = 1
    #         call ch21_main
    #         call poemresponse_start
    #         call ch21_end

    #         # This call statement calls the poem mini-game with no transition.
    #         call poem(False)

    #         python:
    #             if renpy.android and renpy.version_tuple == (6, 99, 12, 4, 2187):
    #                 try: file(os.environ['ANDROID_PUBLIC'] + "/iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt")
    #                 except IOError: open(os.environ['ANDROID_PUBLIC'] + "/iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt", "wb").write(renpy.file("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt").read())
    #             elif renpy.android:
    #                 try: renpy.file(os.environ['ANDROID_PUBLIC'] + "/iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt")
    #                 except IOError: open(os.environ['ANDROID_PUBLIC'] + "/iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt", "wb").write(renpy.file("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt").read())
    #             else:
    #                 try: renpy.file(config.basedir + "/iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt")
    #                 except IOError: open(config.basedir + "/iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt", "wb").write(renpy.file("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii.txt").read())

    #         ## Day 3 - Act 2
    #         $ chapter = 2
    #         call ch22_main
    #         call poemresponse_start
    #         call ch22_end

    #         call poem(False)

    #         ## Day 4 - Act 2
    #         $ chapter = 3
    #         call ch23_main

    #         # This if statement calls either a special poem response game or play
    #         # as normal.
    #         if y_appeal >= 3:
    #             call poemresponse_start2
    #         else:
    #             call poemresponse_start

    #         # This if statement is leftover code from DDLC where if your game is
    #         # a demo that it ends the game fully.
    #         if persistent.demo:
    #             stop music fadeout 2.0
    #             scene black with dissolve_cg
    #             "End of demo"
    #             return

    #         call ch23_end
    #         return

    # elif persistent.playthrough == 3:
    #     jump ch30_main

    # elif persistent.playthrough == 4:
    #     ## Day 1 - Act 4
    #     $ chapter = 0
    #     call ch40_main
    #     jump credits
