import os
import sys
import json
import pygame
import random
import threading

from halo import Halo

from screendata import Screen

from timerhelper import timmer

from damagestate import check_passive_mod

from load_photos import set_bg_photo
from load_photos import set_bg_music
from load_photos import resource_path

from themedstuff import themed_ajt
from themedstuff import themed_names

from damagetypes import all_damage_types, Generic


from colorama import Fore, Style

from damage_over_time import dot as damageovertimetype

spinner = Halo(text='Loading', spinner='dots', color='green')
    
red = Fore.RED
green = Fore.GREEN
blue = Fore.BLUE
white = Fore.WHITE
yellow = Fore.YELLOW

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

photo_size = 128 * 3

CONFIG_FILE = "config.json"

enrage_timer = timmer()

def log(color, text):
    print(color + text + Style.RESET_ALL)
    return text

def debug_log(filename, text):
    with open(filename, "a") as f:
        f.write(f"\n{text}")
    
    return text

def kill_person(dead, killer):
    if dead.isplayer:
        spinner.fail(text=f"Your {dead.Type.colorama_color}{dead.PlayerName}{white} at {blue}{dead.level}{white} kill by {killer.Type.colorama_color}{killer.PlayerName}{white}")
    else:
        spinner.succeed(text=f"The {dead.Type.colorama_color}{dead.PlayerName}{white} at {blue}{dead.level}{white} kill by {killer.Type.colorama_color}{killer.PlayerName}{white}")
        return

    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"{killer.PlayerName} killed {dead.PlayerName}, Below are stats for both...")

    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), "Dead Person")

    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Name: {dead.PlayerName}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Level: {dead.level}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"MHP: {dead.MHP}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"HP: {dead.HP}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Defense: {dead.Def}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Attack: {dead.Atk}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Regain: {dead.Regain}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"True Vitality: {dead.Vitality}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Crit Rate: {dead.CritRate}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Crit Damage Modifier: {dead.CritDamageMod}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Dodge Odds: {dead.DodgeOdds}")
    
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), "Killer")

    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Name: {killer.PlayerName}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Level: {killer.level}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"MHP: {killer.MHP}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"HP: {killer.HP}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Defense: {killer.Def}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Attack: {killer.Atk}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Regain: {killer.Regain}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"True Vitality: {killer.Vitality}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Crit Rate: {killer.CritRate}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Crit Damage Modifier: {killer.CritDamageMod}")
    debug_log(os.path.join("logs", f"{dead.PlayerName.lower()}.txt"), f"Dodge Odds: {killer.DodgeOdds}")

def load_config():
    """Loads the configuration from config.json."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print("Config file not found. Using default settings.")
        return {"preferred_allies": []}  # Default empty list
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {CONFIG_FILE}. Using default settings.")
        return {"preferred_allies": []}  # Default empty list

def main(level):
    from player import Player
    from player import render_player_obj

    running = True
    is_deading = False

    wave_number = 0

    past_level = 1
    foes_killed = 1

    starting_spawn_rate = 0.95

    config = load_config()

    playerlist: list[Player] = []
    backup_players_list: list[Player] = []
    preferred_players_list: list[str] = []
    temp_themed_names: list[str] = []
    preferred_themed_names: list[str] = config.get("preferred_allies", [])

    if preferred_themed_names:
            preferred_name = preferred_themed_names[0].lower()
            for themed_name_pre in temp_themed_names:
                if preferred_name in themed_name_pre.lower():
                    themed_name = themed_name_pre.capitalize()
                    preferred_players_list.append(themed_name)
                    preferred_themed_names.pop(0)
                    break

    spinner.start(text="Loading Players, please wait...")

    for item in themed_names:
        if "mimic".lower() in item.lower():
            continue
        else:
            temp_themed_names.append(item)
    
    themed_name = "Player"

    player = Player(themed_name)

    player.load()
    player.set_photo(themed_name.lower())

    player.isplayer = True

    playerlist.append(player)
        
    while len(playerlist) < 5:
        if random.random() < starting_spawn_rate:
            if len(preferred_players_list) > 0:
                themed_name = preferred_players_list[0]
                preferred_players_list.pop(0)

            else:
                themed_name = temp_themed_names[0].capitalize()

            starting_spawn_rate /= 2
        else:
            themed_name = random.choice(temp_themed_names[1:]).capitalize()

        temp_themed_names.remove(themed_name.lower())

        player = Player(f"{themed_name.replace("_", " ")}")
        player.load()
        player.set_photo(themed_name.lower())

        player.isplayer = True

        playerlist.append(player)

    while len(temp_themed_names) > 0:
        themed_name = random.choice(temp_themed_names).capitalize()
        temp_themed_names.remove(themed_name.lower())

        player = Player(f"{themed_name.replace("_", " ")}")
        player.load()
        player.set_photo(themed_name.lower())

        player.isplayer = True

        backup_players_list.append(player)
        
    threads = []

    for player in playerlist:
        if player.level < 5:
            thread = threading.Thread(target=player.load_past_lives)
            threads.append(thread)
            thread.start()

    for player in backup_players_list:
        if player.level < 5:
            thread = threading.Thread(target=player.load_past_lives)
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    del threads
    
    spinner.succeed(text="Players: Fully Loaded")

    pygame.init()

    screen = Screen(SCREEN_WIDTH, SCREEN_HEIGHT).screen
    icon = pygame.image.load(resource_path(os.path.join("photos", "midoriai-logo.png")))
    pygame.display.set_icon(icon)
    
    pygame.display.set_caption("Midori AI Auto Fighter", "Welcome to the fighting zone!")

    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Arial', 44)

    background_file_name = set_bg_photo()
    background_image = pygame.image.load(background_file_name)
    background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    background_image.set_alpha(128)

    pygame.mixer.music.set_volume(0.05 / 2)
    pygame.mixer.music.load(set_bg_music())
    pygame.mixer.music.play(-1)  # -1 means loop the music indefinitely

    screen.fill((0, 0, 0))
    screen.blit(background_image, (0, 0))

    for player in playerlist:
        player.photodata = pygame.image.load(os.path.join(player.photo))
    for player in backup_players_list:
        player.photodata = pygame.image.load(os.path.join(player.photo))

    pygame.display.flip()

    while True:

        level_sum = 0
        wave_number += 1
        foelist: list[Player] = []
        backup_foes_list: list[Player] = []
        
        spinner.start(text=f"Wave :: {wave_number} :: Loading...")

        for player in playerlist:
            player.DamageDealt = 0
            player.DamageTaken = 0

            level_sum += player.level

        level = round((level_sum + foes_killed) / (len(playerlist)))

        if level < max(round(past_level / 2) - 10, 1):
            level = random.randint(max(round(past_level / 2) - 10, 1), round(past_level / 2) + 10)
        else:
            past_level = level

        number_of_foes = 4
        foes_killed += number_of_foes

        temp_foe_themed_names: list[str] = []

        for item in themed_names:
            temp_foe_themed_names.append(item)
        
        random.shuffle(temp_foe_themed_names)

        if level < 1000:
            temp_foe_themed_names.remove("Carly".lower())

        if level < 2000:
            temp_foe_themed_names.remove("Mezzy".lower())
            temp_foe_themed_names.remove("Mimic".lower())

        if level < 10000:
            temp_foe_themed_names.remove("Luna".lower())

        for i in range(number_of_foes):
            themed_name = random.choice(temp_foe_themed_names).capitalize()
            temp_foe_themed_names.remove(themed_name.lower())
            themed_title = random.choice(themed_ajt).capitalize()

            foe_pre_name = f"{themed_title} {themed_name.replace("_", " ")}"

            foe = Player(f"{foe_pre_name}")
            foe.set_photo(themed_name.lower())
            
            foelist.append(foe)
        
        while len(temp_foe_themed_names) > 0:
            themed_name = random.choice(temp_foe_themed_names).capitalize()
            temp_foe_themed_names.remove(themed_name.lower())
            themed_title = random.choice(themed_ajt).capitalize()

            foe_pre_name = f"{themed_title} {themed_name.replace("_", " ")}"

            foe = Player(f"{foe_pre_name}")
            foe.set_photo(themed_name.lower())

            backup_foes_list.append(foe)

        threads = []

        all_foes = foelist + backup_foes_list
        all_allys = playerlist + backup_players_list

        for foe in all_foes:
            thread = threading.Thread(target=foe.set_level, args=(random.randint(max(level - 10, 1), level + 55),))
            threads.append(thread)
            thread.start()

            if level > 20000:
                thread = threading.Thread(target=foe.load_past_lives)
                threads.append(thread)
                thread.start()

        for player in all_allys:
            thread = threading.Thread(target=player.level_up)
            threads.append(thread)
            thread.start()

        for player in all_allys:
            thread = threading.Thread(target=player.save)
            threads.append(thread)
            thread.start()

        for thread in threads:
            while thread.is_alive():

                pygame.display.flip()
                clock.tick(10)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

            thread.join()

        for foe in all_foes:
            try:
                foe.photodata = pygame.image.load(os.path.join(foe.photo))
                foe.photodata = pygame.transform.flip(foe.photodata, True, False)
                foe.photodata = pygame.transform.scale(foe.photodata, (photo_size, photo_size))
            except FileNotFoundError as e:
                print(f"Error loading image: {e}")
        
        spinner.succeed(text=f"Wave :: {wave_number} :: Fully Loaded")

        player.HP = player.MHP

        enrage_timer.reset()
        enrage_timer.start()

        # Main game loop
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_d: 
                    is_deading = True

                if event.type == pygame.KEYDOWN and event.key == pygame.K_b:  
                    for player in foelist:
                        player.Atk += round(player.HP * 0.35) + 1000

                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: 
                    for player in playerlist:
                        if player.PlayerName.lower() == "player":
                            player.Type = random.choice(all_damage_types)

            enrage_timer.tick()
            enrage_timer.check_timeout()
            
            fps = clock.get_fps()

            enrage_mod = enrage_timer.get_timeout_duration()
            level_base_enrage_mod = (level / max(min(level / 1000, 10000), 2))
            player_base_enrage_mod = (enrage_mod * level_base_enrage_mod)
            foe_base_enrage_mod = (enrage_mod * level_base_enrage_mod)

            if enrage_mod > 10:
                buffed_starter = ((enrage_mod - 10) * 0.0000004) + ((enrage_mod - 5) * 0.0000002)
                bleed_mod = ((0.0000002 + buffed_starter) * (player_base_enrage_mod * foe_base_enrage_mod)) + 1
            elif enrage_mod > 5:
                buffed_starter = ((enrage_mod - 5) * 0.0000002)
                bleed_mod = ((0.0000002 + buffed_starter) * (player_base_enrage_mod * foe_base_enrage_mod)) + 1
            else:
                bleed_mod = (0.0000002 * (player_base_enrage_mod * foe_base_enrage_mod)) + 1

            def_mod = max(1, (bleed_mod * 0.0005))

            if bleed_mod > 1.2:
                def_mod = max(1, (bleed_mod * 0.002) + (bleed_mod * 0.002) + (bleed_mod * 0.001) + 1)
            
            if bleed_mod > 2:
                def_mod = max(1, (bleed_mod * 0.004) + (bleed_mod * 0.004) + (bleed_mod * 0.002) + 1)
            
            if is_deading:
                for player in playerlist:
                    player.save_past_life()
                    playerlist.remove(player)
            
            for player in playerlist:
                if player.HP < 1:
                    player.save_past_life()
                    playerlist.remove(player)
            
            for foe in foelist:
                if foe.HP < 1:
                    foelist.remove(foe)

            if len(playerlist) < 5:
                if len(backup_players_list) > 1:
                    new_player = random.choice(backup_players_list)
                    backup_players_list.remove(new_player)
                    playerlist.append(new_player)

            if len(foelist) < 5:
                if len(backup_foes_list) > 0:
                    new_player = random.choice(backup_foes_list)
                    backup_foes_list.remove(new_player)
                    foelist.append(new_player)

            enrage_dot = damageovertimetype("Enrage Bleed", min(5000, (bleed_mod ** 5) * level), max(300, min(6000, round(25 * bleed_mod))), Generic, "Enrage Mech", 1)

            fps_cap = 65
    
            # Render the screen
            screen.fill((0, 0, 0))
            screen.blit(background_image, (0, 0))

            foe_top = 10
            player_bottom = 620
            photo_offset = 15
            side_offset = 15
            srink_setting = 0.95
            item_total_size = photo_size - (photo_size / 4)
            player_size = (item_total_size * srink_setting, item_total_size * srink_setting)
            foe_size = (item_total_size * srink_setting, item_total_size * srink_setting)
            
            if len(foelist) > 0:
                for i, foe in enumerate(foelist):
                    if foe.HP > 1:
                        item_total_position = ((photo_offset * i) + (side_offset + (item_total_size * i)), foe_top)
                        render_player_obj(pygame, foe, foe.photodata, screen, enrage_timer, def_mod, bleed_mod, item_total_position, foe_size, True)

                    if foe.tick(bleed_mod):
                        for foe_action in foe.ActionsPerTurn:
                            clock.tick(fps_cap)
                        
                            if bleed_mod > 1.5:
                                foe.RushStat = 0
                                foe.gain_damage_over_time(enrage_dot, 1.1 * bleed_mod)

                            if foe.HP > 1:
                                foe.do_pre_turn()

                                if len(playerlist) > 0:
                                    max_def = 0
                                    target_to_damage = random.choice(playerlist)

                                    for target in playerlist:
                                        if target.Def > max_def:
                                            max_def = target.Def
                                        else:
                                            target_to_damage = target

                                    if target_to_damage.HP > 0:
                                        target_to_damage.take_damage(bleed_mod, check_passive_mod(foelist, playerlist, foe, target_to_damage, foe.deal_damage(bleed_mod, target_to_damage.Type)))
                                    
                                    if target_to_damage.HP < 1:
                                        target_to_damage.save_past_life()
                                        kill_person(target_to_damage, foe)
                                        playerlist.remove(target_to_damage)
                    else:
                        if foe.HP > 0: foe.do_pre_turn()
            else:
                break

            if len(playerlist) > 0:
                for i, person in enumerate(playerlist):
                    if person.HP > 1:
                        item_total_position = ((photo_offset * i) + (side_offset + (item_total_size * i)), player_bottom)
                        render_player_obj(pygame, person, person.photodata, screen, enrage_timer, def_mod, bleed_mod, item_total_position, player_size, True)

                    if person.tick(bleed_mod):
                        for turn in person.ActionsPerTurn:
                            clock.tick(fps_cap)
                        
                            if bleed_mod > 1.5:
                                person.gain_damage_over_time(enrage_dot, 1.1 * bleed_mod)

                            if bleed_mod > 1.2:
                                person.RushStat = 0

                            if person.HP > 0:
                                person.do_pre_turn()

                                if len(foelist) > 0:
                                    target_to_damage = random.choice(foelist)

                                    if target_to_damage.HP > 0:
                                        pre_damage_to_deal = person.deal_damage(bleed_mod, target_to_damage.Type)
                                        damge_to_deal = check_passive_mod(foelist, playerlist, person, target_to_damage, pre_damage_to_deal)
                                        target_to_damage.take_damage(bleed_mod, damge_to_deal)

                                    if target_to_damage.HP < 1:
                                        foelist.remove(target_to_damage)
                                        kill_person(target_to_damage, person)
                                        person.Kills += 1
                                        total_rushmod = 0

                                        if bleed_mod < 100:
                                            person.RushStat += 1

                                        for player in playerlist:
                                            total_rushmod += max(1, player.RushStat)

                                        for player in playerlist:
                                            if person.PlayerName == player.PlayerName:
                                                player.gain_exp(mod=bleed_mod * total_rushmod, foe_level=target_to_damage.level)
                                            else:
                                                player.gain_exp(mod=bleed_mod * total_rushmod, foe_level=max(5, round(target_to_damage.level * 1.25)))
                                        for player in backup_players_list:
                                            player.gain_exp(mod=(bleed_mod * total_rushmod) * 0.25, foe_level=max(1, round(target_to_damage.level * 0.25)))

                                    elif target_to_damage.HP > target_to_damage.MHP:
                                        target_to_damage.HP = target_to_damage.MHP
                    else:
                        if person.HP > 0: person.do_pre_turn()

                    if person.HP > person.MHP:
                        person.HP = person.MHP
            else:
                spinner.fail(text="You lost!")
                log(red, "you lose... restart game to load a new buffed save file")
                pygame.quit()
                exit()
                
            if enrage_timer.timed_out:
                fps_stat = font.render(f"FPT: {int(fps)}", True, (255, 255, 255))
                fps_rect = fps_stat.get_rect(center=((SCREEN_WIDTH // 8) + 600, (SCREEN_HEIGHT // 2) - 0))
                screen.blit(fps_stat, fps_rect)

                enrage_timer_stat = font.render(f"Enrage: {(enrage_mod):.1f} ({(bleed_mod):.2f}x)", True, (255, 255, 255))
                enrage_timer_rect = fps_stat.get_rect(center=((SCREEN_WIDTH // 8) + 600, (SCREEN_HEIGHT // 2) + 50))
                screen.blit(enrage_timer_stat, enrage_timer_rect)
            else:
                fps_stat = font.render(f"FPT: {int(fps)}", True, (255, 255, 255))
                fps_rect = fps_stat.get_rect(center=((SCREEN_WIDTH // 8) + 600, (SCREEN_HEIGHT // 2) - 0))
                screen.blit(fps_stat, fps_rect)

            pygame.display.flip()