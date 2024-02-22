import random

from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit.history import History
from scripts.conditions import get_amount_rabbit_for_one_medic, medical_rabbits_condition_fulfilled
from scripts.game_structure.game_essentials import game


# ---------------------------------------------------------------------------- #
#                              Scar Event Class                                #
# ---------------------------------------------------------------------------- #

class Scar_Events():
    """All events with a connection to conditions."""

    # scar pools
    bite_scars = [
        "RABBITBITE"
    ]
    rat_scars = [
        "RATBITE"
    ]
    beak_scars = [
        'BEAKCHEEK', 'BEAKLOWER'
    ]
    canid_scars = [
        "LEGBITE", "NECKBITE", "TAILSCAR", "BRIGHTHEART"
    ]
    snake_scars = [
        "SNAKE"
    ]
    claw_scars = [
        "ONE", "TWO", "SNOUT", "TAILSCAR", "CHEEK",
        "SIDE", "THROAT", "TAILBASE", "BELLY", "FACE",
        "BRIDGE"
    ]
    leg_scars = [
        "NOPAW", "TOETRAP", "MANLEG",
    ]
    tail_scars = [
        "TAILSCAR", "TAILBASE", "NOTAIL", "HALFTAIL", "MANTAIL"
    ]
    ear_scars = [
        "LEFTEAR", "RIGHTEAR", 'NOLEFTEAR', 'NORIGHTEAR'
    ]
    frostbite_scars = [
        "HALFTAIL", "NOTAIL", "NOPAW", 'NOLEFTEAR', 'NORIGHTEAR', 'NOEAR',
        "FROSTFACE", "FROSTTAIL", "FROSTMITT", "FROSTSOCK",
    ]
    eye_scars = [
        "THREE", "RIGHTBLIND", "LEFTBLIND", "BOTHBLIND"
    ]
    burn_scars = [
        "BRIGHTHEART", "BURNPAWS", "BURNTAIL", "BURNBELLY", "BURNRUMP"
    ]
    quill_scars = [
        "QUILLCHUNK", "QUILLSCRATCH"
    ]
    head_scars = [
        "SNOUT", "CHEEK", "BRIDGE", "BEAKCHEEK"
    ]
    bone_scars = [
        "MANLEG",  "TOETRAP"
    ]
    back_scars = [
        "TWO", "TAILBASE"
    ]
    
    scar_allowed = {
        "bite-wound": canid_scars,
        "rabbit-bite": bite_scars,
        "severe burn": burn_scars,
        "rat bite": rat_scars,
        "snake bite": snake_scars,
        "mangled tail": tail_scars,
        "mangled leg": leg_scars,
        "torn ear": ear_scars,
        "frostbite": frostbite_scars,
        "torn pelt": claw_scars + beak_scars,
        "damaged eyes": eye_scars,
        "quilled by porcupine": quill_scars,
        "claw-wound": claw_scars,
        "beak bite": beak_scars,
        "broken jaw": head_scars,
        "broken back": back_scars,
        "broken bone": bone_scars,
        "head damage": head_scars
    }

    @staticmethod
    def handle_scars(rabbit, injury_name):
        """ 
        This function handles the scars
        """
        
        # If the injury can't give a scar, move return None, None
        if injury_name not in Scar_Events.scar_allowed:
            return None, None
        
        months_with = game.warren.age - rabbit.injuries[injury_name]["month_start"]
        chance = max(5 - months_with, 1)
        
        amount_per_med = get_amount_rabbit_for_one_medic(game.warren)
        if medical_rabbits_condition_fulfilled(game.rabbit_class.all_rabbits.values(), amount_per_med):
            chance += 2
        
        if len(rabbit.pelt.scars) < 4 and not int(random.random() * chance):
            
            # move potential scar text into displayed scar text
            

            specialty = None  # Scar to be set

            scar_pool = [i for i in Scar_Events.scar_allowed[injury_name] if i not in rabbit.pelt.scars]
            if 'NOPAW' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ['TOETRAP', 'RATBITE', "FROSTSOCK"]]
            if 'NOTAIL' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ["HALFTAIL", "TAILBASE", "TAILSCAR", "MANTAIL", "BURNTAIL", "FROSTTAIL"]]
            if 'HALFTAIL' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ["TAILSCAR", "MANTAIL", "FROSTTAIL"]]
            if "BRIGHTHEART" in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ["RIGHTBLIND", "BOTHBLIND"]]
            if 'BOTHBLIND' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ["THREE", "RIGHTBLIND", "LEFTBLIND", "BOTHBLIND", "BRIGHTHEART"]]
            if 'NOEAR' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ["LEFTEAR", "RIGHTEAR", 'NOLEFTEAR', 'NORIGHTEAR', "FROSTFACE"]]
            if 'MANTAIL' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ["BURNTAIL", 'FROSTTAIL']]
            if 'BURNTAIL' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ["MANTAIL", 'FROSTTAIL']]
            if 'FROSTTAIL' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ["MANTAIL", 'BURNTAIL']]
            if 'NOLEFT' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ['LEFTEAR']]
            if 'NORIGHT' in rabbit.pelt.scars:
                scar_pool = [i for i in scar_pool if i not in ['RIGHTEAR']]
                
            # Extra check for disabling scars.
            if int(random.random() * 3):
                condition_scars = {
                    "LEGBITE", "THREE", "NOPAW", "TOETRAP", "NOTAIL", "HALFTAIL", "LEFTEAR", "RIGHTEAR",
                    "MANLEG", "BRIGHTHEART", "NOLEFTEAR", "NORIGHTEAR", "NOEAR", "LEFTBLIND",
                    "RIGHTBLIND", "BOTHBLIND", "RATBITE"
                }
                
                scar_pool = list(set(scar_pool).difference(condition_scars))
                
                
            
            # If there are not new scars to give them, return None, None.
            if not scar_pool:
                return None, None
            
            # If we've reached this point, we can move foward with giving history. 
            History.add_scar(rabbit,
                                  f"m_c was scarred from an injury ({injury_name}).",
                                  condition=injury_name)


            specialty = random.choice(scar_pool)
            if specialty in ["NOTAIL", "HALFTAIL"]:
                if rabbit.pelt.accessory in ["RED FEATHERS", "BLUE FEATHERS", "JAY FEATHERS"]:
                    rabbit.pelt.accessory = None

            # combining left/right variations into the both version
            if "NOLEFTEAR" in rabbit.pelt.scars and specialty == 'NORIGHTEAR':
                rabbit.pelt.scars.remove("NOLEFTEAR")
                specialty = 'NOEAR'
            elif "NORIGHTEAR" in rabbit.pelt.scars and specialty == 'NOLEFTEAR':
                rabbit.pelt.scars.remove("NORIGHTEAR")
                specialty = 'NOEAR'

            if 'RIGHTBLIND' in rabbit.pelt.scars and specialty == 'LEFTBLIND':
                rabbit.pelt.scars.remove("LEFTBLIND")
                specialty = 'BOTHBLIND'
            elif 'LEFTBLIND' in rabbit.pelt.scars and specialty == 'RIGHTBLIND':
                rabbit.pelt.scars.remove("RIGHTBLIND")
                specialty = 'BOTHBLIND'

            
            rabbit.pelt.scars.append(specialty)

            scar_gain_strings = [
                f"{rabbit.name}'s {injury_name} has healed, but they'll always carry evidence of the incident on their pelt.",
                f"{rabbit.name} healed from their {injury_name} but will forever be marked by a scar.",
                f"{rabbit.name}'s {injury_name} has healed, but the injury left them scarred.",
            ]
            return random.choice(scar_gain_strings), specialty
        else:
            return None, None
           

