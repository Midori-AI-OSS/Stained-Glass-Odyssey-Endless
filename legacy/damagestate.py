"""Player damage and passive interactions.

This module governs player-only stat logic during combat. Enemy passives are
handled separately in :mod:`foe_passive_builder` when foes load at runtime.
"""

import random

from player import Player

from damage_over_time import dot as damageovertimetype
from healing_over_time import hot as healingovertimetype

from colorama import Fore, Style

from themedstuff import themed_names

from damagetypes import Light, Dark, Wind, Lightning, Fire, Ice, Generic

red = Fore.RED
green = Fore.GREEN
blue = Fore.BLUE
white = Fore.WHITE

def log(color, text):
    print(color + text + Style.RESET_ALL)
    return text

def debug_log(text):
    with open("debug_log.txt", "a") as f:
        f.write(f"\n{text}")
    
    return text

def check_damage_type_passive(alllist: list[Player], source: Player, target: Player, mited_damage_dealt: float):
        
    if source.Type == Light:
        mited_damage_dealt = mited_damage_dealt * (((source.MHP - source.HP) + 1) + 2)

        for player in alllist:
            if source.isplayer == player.isplayer:
                if player.PlayerName is not source.PlayerName:
                    if player.HP < player.MHP * 0.55:
                        player.heal_damage(source.deal_damage(1, player.Type) * 0.05)
            elif source.isplayer != player.isplayer:
                light_dot = damageovertimetype("Celestial Atrophy", mited_damage_dealt ** 1.5, 50000, source.Type, source.PlayerName, 1)
                light_dot.max_turns = 500000000
                player.gain_damage_over_time(light_dot, source.effecthittate())
    
    if source.Type == Dark:
        target.gain_damage_over_time(damageovertimetype("Abyssal Corruption", mited_damage_dealt ** 1.65, 325, source.Type, source.PlayerName, 1), source.effecthittate())

        if source.above_threshold_ticks > 100:
            source.above_threshold_ticks = 100

        for player in alllist:
            if source.isplayer == player.isplayer:
                if player.PlayerName is not source.PlayerName:
                    if player.HP > player.MHP * 0.25:
                        source.above_threshold_ticks += 1
                        player.gain_damage_over_time(damageovertimetype("Abyssal Weakness", source.above_threshold_ticks ** 1.05, round(55 * source.above_threshold_ticks), source.Type, source.PlayerName, 1), source.above_threshold_ticks ** 0.55)
                        source.Atk += source.check_base_stats(source.Atk, random.randint(95, 105) * source.above_threshold_ticks)
    
    if source.Type == Wind:
        target.gain_damage_over_time(damageovertimetype("Gale Erosion", mited_damage_dealt ** 1.05, 325, source.Type, source.PlayerName, 1), source.effecthittate())
        
        for dot in target.DOTS:
            dot.damage = (dot.damage * 1.001)
        
        target.damage_over_time()
    
    if source.Type == Lightning:

        if source.ActionPointsPerTick <= 150:
            source.ActionPointsPerTick += 1

        target.gain_damage_over_time(damageovertimetype("Charged Decay", mited_damage_dealt ** 1.05, 325, source.Type, source.PlayerName, 1), source.effecthittate())
    
    if source.Type == Ice:

        if target.ActionPointsPerTurn <= 1200:
            target.ActionPointsPerTurn += 100

        target.gain_damage_over_time(damageovertimetype("Frozen Wound", mited_damage_dealt ** 1.05, 700, source.Type, source.PlayerName, 1), source.effecthittate())

    if source.Type == Fire:
        for player in alllist:
            if source.isplayer != player.isplayer:
                player.gain_damage_over_time(damageovertimetype("Blazing Torment", mited_damage_dealt ** 1.5, 325, source.Type, source.PlayerName, 1), source.effecthittate())
    
    if source.Type == Generic:
        for player in alllist:
            if source.isplayer == player.isplayer:
                if player.PlayerName is not source.PlayerName:
                    player.gain_healing_over_time(healingovertimetype(f"{source.PlayerName}\'s Echo", round(source.deal_damage(0.2, target.Type)), 5, source.Type, source.PlayerName, 1))

    if target.Type == Light:
        mited_damage_dealt = mited_damage_dealt / 2

    if target.Type == Dark:
        mited_damage_dealt = mited_damage_dealt / 2

    if target.Type == Wind:
        mited_damage_dealt = mited_damage_dealt / 2

    if target.Type == Lightning:
        mited_damage_dealt = mited_damage_dealt / 2

    if target.Type == Ice:
        source.gain_damage_over_time(damageovertimetype("Cold Wound", target.deal_damage(1, source.Type) ** 1.65, 700, target.Type, target.PlayerName, 1), target.effecthittate())
        mited_damage_dealt = mited_damage_dealt / 2

    if target.Type == Fire:
        mited_damage_dealt = mited_damage_dealt / 2

    return mited_damage_dealt

def check_passive_mod(foelist: list[Player], playerlist: list[Player], source: Player, target: Player, mited_damage_dealt: float):
    """
    Handles a player taking damage from another player.

    Args:
        foelist (list): A list of enemy Player objects.
        playerlist (list): A list of all Player objects.
        source (Player): The Player object inflicting the damage.
        target (Player): The Player object receiving the damage.
        fight_env_list (list): A list of unchangeable outside vars to impact damage.
    """
        
    alllist: list[Player] = []
    
    for player in foelist:
        alllist.append(player)
    
    for player in playerlist:
        alllist.append(player)

    if getattr(source, "BleedChance", 0) > 0:
        if random.random() < source.BleedChance:
            bleed_dot = damageovertimetype(
                "Bleed",
                source.deal_damage(0.05, target.Type),
                3,
                Generic,
                source.PlayerName,
                1,
            )
            target.gain_damage_over_time(bleed_dot, source.effecthittate())

    if themed_names[0] in source.PlayerName.lower():
        if source.Regain > 10:
            source.Regain -= 0.01 * source.above_threshold_ticks
            source.DodgeOdds += 0.001 * source.above_threshold_ticks
            source.MHP += 500 * source.above_threshold_ticks
            source.HP += 500 * source.above_threshold_ticks
            source.Atk += 50 * source.above_threshold_ticks
            source.Def += 1 * source.above_threshold_ticks
        
        if source.Mitigation > 1:
            source.DodgeOdds += 0.001 * source.above_threshold_ticks
            source.Mitigation -= 0.001 * source.above_threshold_ticks
            source.EffectRES += 0.01 * source.above_threshold_ticks
            source.EffectHitRate += 0.01 * source.above_threshold_ticks

        if themed_names[0] in target.PlayerName.lower():
            if random.random() > 0.999:
                log(random.choice([red, green, blue]), f"{source.PlayerName} tried to hit {target.PlayerName}! {random.choice([red, green, blue])}Why would I hit myself user... {random.choice([red, green, blue])}you think I am dumb?")
            
            mited_damage_dealt = mited_damage_dealt / 4
        else:
            if source.HP > source.MHP * 0.25:
                hp_diff = source.HP - source.MHP * 0.25
                reduction_factor = hp_diff / (source.MHP * 0.75)
                
                scaled_reduction = reduction_factor ** 0.65 * 0.05

                # Introduce a multiplier that increases with time above 25% HP
                source.above_threshold_ticks += 1
                
                multiplier = 1 + (source.above_threshold_ticks ** 0.5) * 0.01 
                
                source.HP -= round(source.MHP * scaled_reduction * multiplier)

                mited_damage_dealt = mited_damage_dealt * (((source.MHP - source.HP) + 1) * 4)
                target.gain_damage_over_time(damageovertimetype("Twilight Decay", mited_damage_dealt ** 0.65, 175, source.Type, source.PlayerName, 2), source.effecthittate())
            else:
                source.above_threshold_ticks = 1
                mited_damage_dealt = mited_damage_dealt * (((source.MHP - source.HP) + 1) * 2)
                target.gain_damage_over_time(damageovertimetype("Impact Echo", mited_damage_dealt ** 0.35, 175, source.Type, source.PlayerName, 1), source.effecthittate())

    if themed_names[1] in source.PlayerName.lower():
        hp_percentage = source.HP / source.MHP

        if source.DodgeOdds > 0.5:
            source.Def += source.check_base_stats(source.Def, round(source.DodgeOdds ** 2)) + round(source.DodgeOdds)
            source.DodgeOdds = 0

        for player in alllist:
            if source.isplayer == player.isplayer:
                if player.PlayerName is not source.PlayerName:
                    if player.HP < player.MHP * 0.65:
                        source.take_damage(1, source.MHP * 0.05)
                        player.heal_damage(source.deal_damage(1, Generic) * 0.025)

                    if player.Def > source.Def:
                        player.Def -= 1
                        source.Def += source.check_base_stats(source.Def, player.level)


    elif themed_names[1] in target.PlayerName.lower():
        hp_percentage = source.HP / source.MHP

        if hp_percentage < 0.75:
            damage_reduction = (1 - hp_percentage) * 0.95
            mited_damage_dealt *= (1 - damage_reduction)

        if hp_percentage < 0.55:
            mited_damage_dealt = carly_mit_adder(target, mited_damage_dealt)

        if hp_percentage < 0.25:
            mited_damage_dealt = carly_mit_adder(target, mited_damage_dealt)
        
        if mited_damage_dealt > 100:
            mited_damage_dealt = 100
            
    if themed_names[2] in source.PlayerName.lower():
        for player in alllist:
            if source.isplayer == player.isplayer:
                if player.PlayerName is not source.PlayerName:
                    if player.HP < source.MHP * 0.55:
                        player.heal_damage(source.Atk * 0.005)
                        player.gain_healing_over_time(healingovertimetype(f"{source.PlayerName}\'s Heal", round(player.MHP * 0.01), 5, player.Type, source.PlayerName, 1))
                    
                    if len(player.DOTS) > 0:
                        to_be_moved = random.choice(player.DOTS)

                        player.DOTS.remove(to_be_moved)

                        random.choice(foelist).gain_damage_over_time(to_be_moved, source.effecthittate())

    if themed_names[3] in source.PlayerName.lower():
        if target.MHP > source.MHP:
            source.MHP += random.randint(5, 15)
            target.MHP -= 1

    if themed_names[4] in source.PlayerName.lower():
        pass

    if themed_names[5] in source.PlayerName.lower():
        pass

    if themed_names[6] in source.PlayerName.lower():
        pass

    if themed_names[7] in source.PlayerName.lower():
        if source.HP < source.MHP * 0.85:
            mited_damage_dealt = mited_damage_dealt + ((source.MHP / 4) / (target.Def * 2))

    if themed_names[8] in source.PlayerName.lower():
        if source.Atk > 1000:
            source.Regain += 0.05
            source.Atk -= 1
        if source.Def > 1000:
            source.Regain += 0.05
            source.Def -= 1

    if themed_names[9] in source.PlayerName.lower():
        pass

    if themed_names[14].replace("_", " ") in source.PlayerName.lower():
        source.Type = Lightning

        if source.ActionPointsPerTick < 100:
            source.ActionPointsPerTick += 1

        if source.ActionPointsPerTurn > 600:
            source.ActionPointsPerTurn = 600
        
        if source.EXP < source.exp_to_levelup():
            source.EXP += max(source.exp_to_levelup() * 0.01, 1)

        if source.EffectHitRate <= 200:
            source.EffectHitRate += 0.25
        
        if len(source.DOTS) > 0:
            for dot in source.DOTS:
                dot.turns -= 1
            
    if themed_names[15] in source.PlayerName.lower():

        if random.random() > 0.95:
            source.Type = random.choice([Dark, Light, Lightning])

        for player in alllist:
            if source.isplayer == player.isplayer:
                if player.PlayerName is not source.PlayerName:
                    if source.Def > 1000:
                        player.Def += 10
                        source.Def -= 1
    
    mited_damage_dealt = check_damage_type_passive(alllist, source, target, mited_damage_dealt)
    
    return max(mited_damage_dealt, 1)

def carly_mit_adder(target: Player, mited_damage_dealt: float):
    for item in target.Items:
        if not item:
            continue
        try:
            mited_damage_dealt = item.on_damage_taken(mited_damage_dealt)
        except Exception:
            continue
    
    return mited_damage_dealt

def apply_damage_item_effects(source: Player, target: Player, mited_damage_dealt: float):
        
        for item in source.Items:
            if not item:
                continue
            try:
                mited_damage_dealt = item.on_damage_dealt(mited_damage_dealt)
                source.DamageDealt += int(mited_damage_dealt)
            except Exception:
                continue

        for item in target.Items:
            if not item:
                continue
            try:
                mited_damage_dealt = item.on_damage_taken(mited_damage_dealt)
                target.DamageTaken += int(mited_damage_dealt)
            except Exception:
                continue

        return mited_damage_dealt

def take_damage(foelist: list[Player], playerlist: list[Player], source: Player, target: Player, mited_damage_dealt: float):
    """
    Handles a player taking damage from another player.

    Args:
        foelist (list): A list of enemy Player objects.
        playerlist (list): A list of all Player objects.
        source (Player): The Player object inflicting the damage.
        target (Player): The Player object receiving the damage.
        fight_env_list (list): A list of unchangeable outside vars to impact damage.
    """
    
    return check_passive_mod(foelist, playerlist, source, target, mited_damage_dealt)