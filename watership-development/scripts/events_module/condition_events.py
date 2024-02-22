import ujson
import random
from copy import deepcopy

from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit.history import History
from scripts.rabbit.pelts import Pelt
from scripts.conditions import medical_rabbits_condition_fulfilled, get_amount_rabbit_for_one_medic
from scripts.utility import event_text_adjust, get_med_rabbits, change_relationship_values, change_warren_relations, \
    history_text_adjust
from scripts.game_structure.game_essentials import game
from scripts.events_module.scar_events import Scar_Events
from scripts.events_module.generate_events import GenerateEvents
from scripts.event_class import Single_Event


# ---------------------------------------------------------------------------- #
#                             Condition Event Class                            #
# ---------------------------------------------------------------------------- #

class Condition_Events():
    """All events with a connection to conditions."""

    resource_directory = "resources/dicts/conditions/"

    ILLNESSES = None
    with open(f"{resource_directory}illnesses.json", 'r') as read_file:
        ILLNESSES = ujson.loads(read_file.read())

    INJURIES = None
    with open(f"{resource_directory}injuries.json", 'r') as read_file:
        INJURIES = ujson.loads(read_file.read())

    PERMANENT = None
    with open(f"resources/dicts/conditions/permanent_conditions.json", 'r') as read_file:
        PERMANENT = ujson.loads(read_file.read())
    # ---------------------------------------------------------------------------- #
    #                                    CHANCE                                    #
    # ---------------------------------------------------------------------------- #

    ILLNESSES_SEASON_LIST = None
    with open(f"resources/dicts/conditions/illnesses_seasons.json", 'r') as read_file:
        ILLNESSES_SEASON_LIST = ujson.loads(read_file.read())

    INJURY_DISTRIBUTION = None
    with open(f"resources/dicts/conditions/event_injuries_distribution.json", 'r') as read_file:
        INJURY_DISTRIBUTION = ujson.loads(read_file.read())

    # ---------------------------------------------------------------------------- #
    #                                   STRINGS                                    #
    # ---------------------------------------------------------------------------- #

    PERM_CONDITION_RISK_STRINGS = None
    with open(f"resources/dicts/conditions/risk_strings/permanent_condition_risk_strings.json", 'r') as read_file:
        PERM_CONDITION_RISK_STRINGS = ujson.loads(read_file.read())

    ILLNESS_RISK_STRINGS = None
    with open(f"resources/dicts/conditions/risk_strings/illness_risk_strings.json", 'r') as read_file:
        ILLNESS_RISK_STRINGS = ujson.loads(read_file.read())

    INJURY_RISK_STRINGS = None
    with open(f"resources/dicts/conditions/risk_strings/injuries_risk_strings.json", 'r') as read_file:
        INJURY_RISK_STRINGS = ujson.loads(read_file.read())

    CONGENITAL_CONDITION_GOT_STRINGS = None
    with open(f"resources/dicts/conditions/condition_got_strings/gain_congenital_condition_strings.json", 'r') as read_file:
        CONGENITAL_CONDITION_GOT_STRINGS = ujson.loads(read_file.read())

    PERMANENT_CONDITION_GOT_STRINGS = None
    with open(f"resources/dicts/conditions/condition_got_strings/gain_permanent_condition_strings.json", 'r') as read_file:
        PERMANENT_CONDITION_GOT_STRINGS = ujson.loads(read_file.read())

    ILLNESS_HEALED_STRINGS = None
    with open(f"resources/dicts/conditions/healed_and_death_strings/illness_healed_strings.json", 'r') as read_file:
        ILLNESS_HEALED_STRINGS = ujson.loads(read_file.read())

    INJURY_HEALED_STRINGS = None
    with open(f"resources/dicts/conditions/healed_and_death_strings/injury_healed_strings.json", 'r') as read_file:
        INJURY_HEALED_STRINGS = ujson.loads(read_file.read())

    INJURY_DEATH_STRINGS = None
    with open(f"resources/dicts/conditions/healed_and_death_strings/injury_death_strings.json", 'r') as read_file:
        INJURY_DEATH_STRINGS = ujson.loads(read_file.read())

    @staticmethod
    def handle_illnesses(rabbit, season=None):
        """ 
        This function handles overall the illnesses in 'expanded' (or 'cruel season') game mode
        """
        # return immediately if they're already dead or in the wrong game-mode
        triggered = False
        if rabbit.dead or game.warren.game_mode == "classic":
            if rabbit.dead:
                triggered = True
            return triggered

        event_string = None

        if rabbit.is_ill():
            event_string = Condition_Events.handle_already_ill(rabbit)
        else:
            # ---------------------------------------------------------------------------- #
            #                              make rabbits sick                                  #
            # ---------------------------------------------------------------------------- #
            random_number = int(
                random.random() * game.get_config_value("condition_related", f"{game.warren.game_mode}_illness_chance"))
            if not rabbit.dead and not rabbit.is_ill() and random_number <= 10 and not event_string:
                season_dict = Condition_Events.ILLNESSES_SEASON_LIST[season]
                possible_illnesses = []

                # pick up possible illnesses from the season dict
                for illness_name in season_dict:
                    possible_illnesses += [illness_name] * season_dict[illness_name]

                # pick a random illness from those possible
                random_index = int(random.random() * len(possible_illnesses))
                chosen_illness = possible_illnesses[random_index]
                # if a non-kittenten got kittencough, switch it to whitecough instead
                if chosen_illness == 'kittencough' and rabbit.status != 'kittenten':
                    chosen_illness = 'whitecough'
                # make em sick
                rabbit.get_ill(chosen_illness)

                # create event text
                if chosen_illness in ["running nose", "stomachache"]:
                    event_string = f"{rabbit.name} has gotten a {chosen_illness}."
                else:
                    event_string = f"{rabbit.name} has gotten {chosen_illness}."

        # if an event happened, then add event to cur_event_list and save death if it happened.
        if event_string:
            types = ["health"]
            if rabbit.dead:
                types.append("birth_death")
            game.cur_events_list.append(Single_Event(event_string, types, rabbit.ID))
            # game.health_events_list.append(event_string)

        # just double-checking that trigger is only returned True if the rabbit is dead
        if rabbit.dead:
            triggered = True
        else:
            triggered = False

        return triggered

    @staticmethod
    def handle_injuries(rabbit, other_rabbit=None, alive_kittens=None, war=None, enemy_warren=None, season=None):
        """ 
        This function handles overall the injuries in 'expanded' (or 'cruel season') game mode.
        Returns: boolean - if an event was triggered
        """
        has_other_warren = False
        triggered = False
        text = None
        random_number = int(random.random() * game.get_config_value("condition_related", f"{game.warren.game_mode}_injury_chance"))

        if rabbit.dead:
            triggered = True
            return triggered

        involved_rabbits = [rabbit.ID]

        # handle if the current rabbit is already injured
        if rabbit.is_injured() and game.warren.game_mode != 'classic':
            for injury in rabbit.injuries:
                if injury == 'pregnant':
                    return triggered
            triggered, event_string = Condition_Events.handle_already_injured(rabbit)
            text = event_string
        else:
            # EVENTS

            if not triggered and \
                    rabbit.personality.trait in ["adventurous",
                                            "bold",
                                            "daring",
                                            "confident",
                                            "ambitious",
                                            "bloodthirsty",
                                            "fierce",
                                            "strict",
                                            "troublesome",
                                            "vengeful",
                                            "impulsive"] and \
                    random_number <= 15:
                triggered = True
            elif not triggered and random_number <= 5:
                triggered = True

            if triggered:
                if war:
                    other_warren = enemy_warren
                else:
                    other_warren = random.choice(game.warren.all_warrens)
                if other_warren:
                    other_warren_name = f'{other_warren.name}warren'

                if other_warren_name == 'None':
                    other_warren = game.warren.all_warrens[0]
                    other_warren_name = f'{other_warren.name}warren'

                possible_events = GenerateEvents.possible_short_events(rabbit.status, rabbit.age, "injury")
                final_events = GenerateEvents.filter_possible_short_events(possible_events, rabbit, other_rabbit, war,
                                                                           enemy_warren, other_warren, alive_kittens)

                if len(final_events) > 0:
                    injury_event = random.choice(final_events)

                    if "other_warren" in injury_event.tags or "war" in injury_event.tags:
                        has_other_warren = True

                    if "rel_up" in injury_event.tags:
                        change_warren_relations(other_warren, difference=1)
                    elif "rel_down" in injury_event.tags:
                        change_warren_relations(other_warren, difference=-1)

                    # let's change some relationship values \o/ check if another rabbit is mentioned
                    if "other_rabbit" in injury_event.tags:
                        involved_rabbits.append(other_rabbit.ID)
                        Condition_Events.handle_relationship_changes(rabbit, injury_event, other_rabbit)

                    #print(injury_event.event_text)
                    text = event_text_adjust(Rabbit, injury_event.event_text, rabbit, other_rabbit, other_warren_name)

                    if game.warren.game_mode == "classic":
                        if "scar" in injury_event.tags and len(rabbit.pelt.scars) < 4:
                            # add tagged scar
                            for scar in Pelt.scars1 + Pelt.scars2 + Pelt.scars3:
                                if scar in injury_event.tags:
                                    rabbit.pelt.scars.append(scar)

                            # add scar history
                            if injury_event.history_text:
                                if "scar" in injury_event.history_text:
                                    history_text = history_text_adjust(injury_event.history_text['scar'],
                                                                              other_warren_name, game.warren)
                                    History.add_scar(rabbit, history_text, other_rabbit=other_rabbit)
                    else:
                        # record proper history text possibilities
                        if injury_event.history_text:
                            possible_scar = None
                            possible_death = None
                            if "scar" in injury_event.history_text:
                                possible_scar = history_text_adjust(injury_event.history_text['scar'],
                                                                   other_warren_name, game.warren, other_rabbit_rc = other_rabbit)
                            if rabbit.status == 'chief rabbit' and 'lead_death' in injury_event.history_text:
                                possible_death = history_text_adjust(injury_event.history_text['lead_death'],
                                                                    other_warren_name, game.warren, other_rabbit_rc = other_rabbit)
                            elif rabbit.status != 'chief rabbit' and 'reg_death' in injury_event.history_text:
                                possible_death = history_text_adjust(injury_event.history_text['reg_death'],
                                                                    other_warren_name, game.warren, other_rabbit_rc = other_rabbit)

                            if possible_scar or possible_death:
                                History.add_possible_history(rabbit, injury_event.injury, scar_text=possible_scar, 
                                                             death_text=possible_death, other_rabbit=other_rabbit)
                            
                        rabbit.get_injured(injury_event.injury)

        # just double-checking that trigger is only returned True if the rabbit is dead
        if rabbit.status != "chief rabbit":
            # only checks for non-chief rabbits, as chief rabbits will not be dead if they are just losing a life
            if rabbit.dead:
                triggered = True
            else:
                triggered = False

        if text is not None:
            types = ["health"]
            if rabbit.dead or triggered:
                types.append("birth_death")
            if has_other_warren:
                types.append("other_warrens")
            game.cur_events_list.append(Single_Event(text, types, involved_rabbits))

        return triggered

    @staticmethod
    def handle_relationship_changes(rabbit, injury_event, other_rabbit):
        rabbit_to = None
        rabbit_from = None
        n = 20
        romantic = 0
        platonic = 0
        dislike = 0
        admiration = 0
        comfortable = 0
        jealousy = 0
        trust = 0
        if "rc_to_mc" in injury_event.tags:
            rabbit_to = [rabbit.ID]
            rabbit_from = [other_rabbit]
        elif "mc_to_rc" in injury_event.tags:
            rabbit_to = [other_rabbit.ID]
            rabbit_from = [rabbit]
        elif "to_both" in injury_event.tags:
            rabbit_to = [rabbit.ID, other_rabbit.ID]
            rabbit_from = [other_rabbit, rabbit]
        if "romantic" in injury_event.tags:
            romantic = n
        elif "neg_romantic" in injury_event.tags:
            romantic = -n
        if "platonic" in injury_event.tags:
            platonic = n
        elif "neg_platonic" in injury_event.tags:
            platonic = -n
        if "dislike" in injury_event.tags:
            dislike = n
        elif "neg_dislike" in injury_event.tags:
            dislike = -n
        if "respect" in injury_event.tags:
            admiration = n
        elif "neg_respect" in injury_event.tags:
            admiration = -n
        if "comfort" in injury_event.tags:
            comfortable = n
        elif "neg_comfort" in injury_event.tags:
            comfortable = -n
        if "jealousy" in injury_event.tags:
            jealousy = n
        elif "neg_jealousy" in injury_event.tags:
            jealousy = -n
        if "trust" in injury_event.tags:
            trust = n
        elif "neg_trust" in injury_event.tags:
            trust = -n
        change_relationship_values(
            rabbit_to,
            rabbit_from,
            romantic,
            platonic,
            dislike,
            admiration,
            comfortable,
            jealousy,
            trust)

    @staticmethod
    def handle_permanent_conditions(rabbit,
                                    condition=None,
                                    injury_name=None,
                                    scar=None,
                                    born_with=False):
        """
        this function handles overall the permanent conditions of a rabbit.
        returns boolean if event was triggered
        """

        # dict of possible physical conditions that can be acquired from relevant scars
        scar_to_condition = {
            "LEGBITE": ["weak leg"],
            "THREE": ["one bad eye", "failing eyesight"],
            "NOPAW": ["lost a leg"],
            "TOETRAP": ["weak leg"],
            "NOTAIL": ["lost their tail"],
            "HALFTAIL": ["lost their tail"],
            "LEFTEAR": ["partial hearing loss"],
            "RIGHTEAR": ["partial hearing loss"],
            "MANLEG": ["weak leg", "twisted leg"],
            "BRIGHTHEART": ["one bad eye"],
            "NOLEFTEAR": ["partial hearing loss"],
            "NORIGHTEAR": ["partial hearing loss"],
            "NOEAR": ["partial hearing loss", "deaf"],
            "LEFTBLIND": ["one bad eye", "failing eyesight"],
            "RIGHTBLIND": ["one bad eye", "failing eyesight"],
            "BOTHBLIND": ["blind"],
            "RATBITE": ["weak leg"]
        }

        scarless_conditions = [
            "weak leg", "paralyzed", "raspy lungs", "wasting disease", "blind", "failing eyesight", "one bad eye",
            "partial hearing loss", "deaf", "constant joint pain", "constantly dizzy", "recurring shock",
            "lasting grief"
        ]

        got_condition = False
        perm_condition = None
        possible_conditions = []

        if injury_name is not None:
            if scar is not None and scar in scar_to_condition:
                possible_conditions = scar_to_condition.get(scar)
                perm_condition = random.choice(possible_conditions)
            elif scar is None:
                try:
                    if Condition_Events.INJURIES[injury_name] is not None:
                        conditions = Condition_Events.INJURIES[injury_name]["cause_permanent"]
                        for x in conditions:
                            if x in scarless_conditions:
                                possible_conditions.append(x)
                        if len(possible_conditions) > 0 and not int(random.random() * game.config["condition_related"]["permanent_condition_chance"]):
                            perm_condition = random.choice(possible_conditions)
                        else:
                            return perm_condition
                except KeyError:
                    print(f"WARNING: {injury_name} couldn't be found in injury dict! no permanent condition was given")
                    return perm_condition

        elif condition is not None:
            perm_condition = condition

        if perm_condition is not None:
            got_condition = rabbit.get_permanent_condition(perm_condition, born_with)

        if got_condition is True:
            return perm_condition

    # ---------------------------------------------------------------------------- #
    #                               helper functions                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def handle_already_ill(rabbit):

        rabbit.healed_condition = False
        event_list = []
        illness_progression = {
            "running nose": "whitecough",
            "kittencough": "whitecough",
            "whitecough": "greencough",
            "greencough": "chokecough",
            "chokecough": "bloody cough",
            "an infected wound": "a festering wound",
            "heat exhaustion": "heat stroke",
            "stomachache": "diarrhea",
            "grief stricken": "lasting grief"
        }
        # ---------------------------------------------------------------------------- #
        #                         handle currently sick rabbits                           #
        # ---------------------------------------------------------------------------- #

        # making a copy, so we can iterate through copy and modify the real dict at the same time
        illnesses = deepcopy(rabbit.illnesses)
        for illness in illnesses:
            if illness in game.switches['skip_conditions']:
                continue

            # use herbs
            Condition_Events.use_herbs(rabbit, illness, illnesses, Condition_Events.ILLNESSES)

            # month skip to try and kill or heal rabbit
            skipped = rabbit.month_skip_illness(illness)

            # if event trigger was true, events should be skipped for this illness
            if skipped is True:
                continue

            # death event text and break bc any other illnesses no longer matter
            if rabbit.dead and rabbit.status != '':
                event = f"{rabbit.name} died of {illness}."
                # clear event list to get rid of any healed or risk event texts from other illnesses
                event_list.clear()
                event_list.append(event)
                History.add_death(rabbit, event)
                game.herb_events_list.append(event)
                break

            # if the chief rabbit died, then break before handling other illnesses cus they'll be fully healed or dead dead
            elif rabbit.status == 'chief rabbit' and starting_life_count != game.warren.chief_rabbit_lives:
                History.add_death(rabbit, f"died to {illness}")
                break

            # heal the rabbit
            elif rabbit.healed_condition is True:
                History.remove_possible_history(rabbit, illness)
                game.switches['skip_conditions'].append(illness)
                # gather potential event strings for healed illness
                possible_string_list = Condition_Events.ILLNESS_HEALED_STRINGS[illness]

                # choose event string
                random_index = int(random.random() * len(possible_string_list))
                event = possible_string_list[random_index]
                event = event_text_adjust(Rabbit, event, rabbit, other_rabbit=None)
                event_list.append(event)
                game.herb_events_list.append(event)

                rabbit.illnesses.pop(illness)
                # make sure complications get reset if infection or fester were healed
                if illness in ['an infected wound', 'a festering wound']:
                    for injury in rabbit.injuries:
                        keys = rabbit.injuries[injury].keys()
                        if 'complication' in keys:
                            rabbit.injuries[injury]['complication'] = None
                    for condition in rabbit.permanent_condition:
                        keys = rabbit.permanent_condition[condition].keys()
                        if 'complication' in keys:
                            rabbit.permanent_condition[condition]['complication'] = None
                rabbit.healed_condition = False

                # move to next illness, the rabbit can't get a risk from an illness that has healed
                continue

            Condition_Events.give_risks(rabbit, event_list, illness, illness_progression, illnesses, rabbit.illnesses)

        # joining event list into one event string
        event_string = None
        if len(event_list) > 0:
            event_string = ' '.join(event_list)
        return event_string

    @staticmethod
    def handle_already_injured(rabbit):
        """
        This function handles, when the rabbit is already injured
        Returns: boolean (if something happened) and the event_string
        """
        triggered = False
        event_list = []

        injury_progression = {
            "poisoned": "bloody cough",
            "shock": "lingering shock"
        }

        # need to hold this number so that we can check if the chief rabbit has died
        starting_life_count = game.warren.chief_rabbit_lives

        if game.warren.game_mode == "classic":
            return triggered

        injuries = deepcopy(rabbit.injuries)
        for injury in injuries:
            if injury in game.switches['skip_conditions']:
                continue

            Condition_Events.use_herbs(rabbit, injury, injuries, Condition_Events.INJURIES)

            skipped = rabbit.month_skip_injury(injury)
            if skipped:
                continue

            if rabbit.dead or (rabbit.status == 'chief rabbit' and starting_life_count != game.warren.chief_rabbit_lives):
                triggered = True

                try:
                    possible_string_list = Condition_Events.INJURY_DEATH_STRINGS[injury]
                    event = random.choice(possible_string_list)
                except:
                    print(f'WARNING: {injury} does not have an injury death string, placeholder used')
                    event = "m_c was killed by their injuries."

                event = event_text_adjust(Rabbit, event, rabbit)

                if rabbit.status == 'chief rabbit':
                    history_text = event.replace(str(rabbit.name), " ")
                    History.add_death(rabbit, condition=injury, death_text=history_text.strip())
                    if not rabbit.dead:
                        event = event.replace('.', ', losing a life.')
                else:
                    History.add_death(rabbit, condition=injury, death_text=event)

                # clear event list first to make sure any heal or risk events from other injuries are not shown
                event_list.clear()
                event_list.append(event)
                game.herb_events_list.append(event)
                break
            elif rabbit.healed_condition is True:
                game.switches['skip_conditions'].append(injury)
                triggered = True
                scar_given = None

                # Try to give a scar, and get the event text to be displayed
                event, scar_given = Scar_Events.handle_scars(rabbit, injury)
                # If a scar was not given, we need to grab a seperate healed event
                if not scar_given:
                    try:
                        event = random.choice(Condition_Events.INJURY_HEALED_STRINGS[injury])
                    except KeyError:
                        print(f"WARNING: {injury} couldn't be found in the healed strings dict! placeholder string was used.")
                        event = f"m_c's injury {injury} has healed"
                event = event_text_adjust(Rabbit, event, rabbit, other_rabbit=None)
                
                game.herb_events_list.append(event)
                    
                History.remove_possible_history(rabbit, injury)
                rabbit.injuries.pop(injury)
                rabbit.healed_condition = False

                # try to give a permanent condition based on healed injury and new scar if any
                condition_got = Condition_Events.handle_permanent_conditions(rabbit, injury_name=injury, scar=scar_given)

                if condition_got is not None:
                    # gather potential event strings for gotten condition
                    possible_string_list = Condition_Events.PERMANENT_CONDITION_GOT_STRINGS[injury][condition_got]

                    # choose event string and ensure warren's med rabbit number aligns with event text
                    random_index = random.randrange(0, len(possible_string_list))
                    
                    med_list = get_med_rabbits(Rabbit)
                    #If the rabbit is a med rabbit, don't conister them as one for the event. 
                    if rabbit in med_list:
                        med_list.remove(rabbit)
                    
                    #Choose med rabbit, if you can
                    if med_list:
                        med_rabbit = random.choice(med_list)
                    else:
                        med_rabbit = None
                    
                    if not med_rabbit and random_index < 2 and len(possible_string_list) >= 3:
                        random_index = 2
        
                    event = possible_string_list[random_index]
                    event = event_text_adjust(Rabbit, event, rabbit, other_rabbit=med_rabbit)  # adjust the text
                if event is not None:
                    event_list.append(event)
                continue

            Condition_Events.give_risks(rabbit, event_list, injury, injury_progression, injuries, rabbit.injuries)

        if len(event_list) > 0:
            event_string = ' '.join(event_list)
        else:
            event_string = None
        return triggered, event_string

    @staticmethod
    def handle_already_disabled(rabbit):
        """
        this function handles what happens if the rabbit already has a permanent condition.
        Returns: boolean (if something happened) and the event_string
        """
        triggered = False
        event_types = ["health"]

        if game.warren.game_mode == "classic":
            return triggered

        event_list = []

        condition_progression = {
            "one bad eye": "failing eyesight",
            "failing eyesight": "blind",
            "partial hearing loss": "deaf"
        }

        conditions = deepcopy(rabbit.permanent_condition)
        for condition in conditions:

            # checking if the rabbit has a congenital condition to reveal and handling duration and death
            status = rabbit.month_skip_permanent_condition(condition)

            # if rabbit is dead, break
            if rabbit.dead:
                triggered = True
                event_types.append("birth_death")
                event = f"{rabbit.name} died from complications caused by {condition}."
                event_list.append(event)

                if rabbit.status != 'chief rabbit':
                    History.add_death(rabbit, death_text=event)
                else:
                    History.add_death(rabbit, death_text=f"killed by complications caused by {condition}")

                game.herb_events_list.append(event)
                break

            # skipping for whatever reason
            if status == 'skip':
                continue

            # revealing perm condition
            if status == 'reveal':
                # gather potential event strings for gotten risk
                possible_string_list = Condition_Events.CONGENITAL_CONDITION_GOT_STRINGS[condition]

                # choose event string and ensure warren's med rabbit number aligns with event text
                random_index = int(random.random() * len(possible_string_list))
                med_list = get_med_rabbits(Rabbit)
                med_rabbit = None
                has_parents = False
                if rabbit.parent1 is not None and rabbit.parent2 is not None:
                    # Check if the parent is in Rabbit.all_rabbits. If not, they are faded are dead.

                    med_parent = False  # If they have a med parent, this will be flicked to True in the next couple lines.
                    if rabbit.parent1 in Rabbit.all_rabbits:
                        parent1_dead = Rabbit.all_rabbits[rabbit.parent1].dead
                        if Rabbit.all_rabbits[rabbit.parent1].status == "healer":
                            med_parent = True
                    else:
                        parent1_dead = True

                    if rabbit.parent2 in Rabbit.all_rabbits:
                        parent2_dead = Rabbit.all_rabbits[rabbit.parent2].dead
                        if Rabbit.all_rabbits[rabbit.parent2].status == "healer":
                            med_parent = True
                    else:
                        parent2_dead = True

                    if not parent1_dead or not parent2_dead and not med_parent:
                        has_parents = True

                if len(med_list) == 0 or not has_parents:
                    if random_index == 0:
                        random_index = 1
                    else:
                        med_rabbit = None
                else:
                    med_rabbit = random.choice(med_list)
                    if med_rabbit == rabbit:
                        random_index = 1
                event = possible_string_list[random_index]
                event = event_text_adjust(Rabbit, event, rabbit, other_rabbit=med_rabbit)  # adjust the text
                event_list.append(event)
                continue

            # trying herbs
            chance = 0
            if conditions[condition]["severity"] == 'minor':
                chance = 10
            elif conditions[condition]["severity"] == 'major':
                chance = 6
            elif conditions[condition]["severity"] == 'severe':
                chance = 3
            if not int(random.random() * chance):
                Condition_Events.use_herbs(rabbit, condition, conditions, Condition_Events.PERMANENT)

            # give risks
            Condition_Events.give_risks(rabbit, event_list, condition, condition_progression, conditions, rabbit.permanent_condition)

        Condition_Events.determine_retirement(rabbit, triggered)

        if len(event_list) > 0:
            event_string = ' '.join(event_list)
            game.cur_events_list.append(Single_Event(event_string, event_types, rabbit.ID))
        return

    @staticmethod
    def determine_retirement(rabbit, triggered):
        
        if game.warren.warren_settings['retirement'] or rabbit.no_retire:
            return

        if not triggered and not rabbit.dead and rabbit.status not in \
                ['chief rabbit', 'healer', 'kittenten', 'newborn', 'healer apprentice', 'owsla',
                 'owsla apprentice', 'elder']:
            for condition in rabbit.permanent_condition:
                if rabbit.permanent_condition[condition]['severity'] not in ['major', 'severe']:
                    continue
                    
                if rabbit.permanent_condition[condition]['severity'] == "severe":
                    # Higher changes for "severe". These are meant to be nearly 100% without
                    # being 100%
                    retire_chances = {
                        'newborn': 0,
                        'kittenten': 0,
                        'adolescent': 50,  # This is high so instances where an rabbit retires the same month they become an apprentice is rare
                        'young adult': 10,
                        'adult': 5,
                        'senior adult': 5,
                        'senior': 5
                    }
                else:
                    retire_chances = {
                        'newborn': 0,
                        'kittenten': 0,
                        'adolescent': 100,
                        'young adult': 80,
                        'adult': 70,
                        'senior adult': 50,
                        'senior': 10
                    }
                
                chance = int(retire_chances.get(rabbit.age))
                if not int(random.random() * chance):
                    retire_involved = [rabbit.ID]
                    if rabbit.age == 'adolescent':
                        event = f"{rabbit.name} decides they'd rather spend their time helping around underground and entertaining the " \
                                f"kittentens, they're warmly welcomed into the elder's burrow."
                    elif game.warren.chief_rabbit is not None:
                        if not game.warren.chief_rabbit.dead and not game.warren.chief_rabbit.exiled and \
                                not game.warren.chief_rabbit.outside and rabbit.months < 120:
                            retire_involved.append(game.warren.chief_rabbit.ID)
                            event = f"{game.warren.chief_rabbit.name}, seeing {rabbit.name} struggling the last few months " \
                                    f"approaches them and promises them that no one would think less of them for " \
                                    f"retiring early and that they would still be a valuable member of the warren " \
                                    f"as an elder. {rabbit.name} agrees and later that day they are relieved from duty. " \

                    if rabbit.age == 'adolescent':
                        event += f" They are given the name {rabbit.name.prefix}{rabbit.name.suffix} in honor " \
                                    f"of their contributions to {game.warren.name}warren."

                    rabbit.retire_rabbit()
                    # Don't add this to the condition event list: instead make it it's own event, a ceremony. 
                    game.cur_events_list.append(
                            Single_Event(event, "ceremony", retire_involved))

    @staticmethod
    def give_risks(rabbit, event_list, condition, progression, conditions, dictionary):
        event_triggered = False
        if dictionary == rabbit.permanent_condition:
            event_triggered = True
        for risk in conditions[condition]["risks"]:
            if risk["name"] in (rabbit.injuries or rabbit.illnesses):
                continue
            if risk["name"] == 'an infected wound' and 'a festering wound' in rabbit.illnesses:
                continue

            # adjust chance of risk gain if warren has enough meds
            chance = risk["chance"]
            if medical_rabbits_condition_fulfilled(Rabbit.all_rabbits.values(),
                                                get_amount_rabbit_for_one_medic(game.warren)):
                chance += 10  # lower risk if enough meds
            if game.warren.healer is None and chance != 0:
                chance = int(chance * .75)  # higher risk if no meds and risk chance wasn't 0
                if chance <= 0:  # ensure that chance is never 0
                    chance = 1

            # if we hit the chance, then give the risk if the rabbit does not already have the risk
            if chance != 0 and not int(random.random() * chance) and risk['name'] not in dictionary:
                # check if the new risk is a previous stage of a current illness
                skip = False
                if risk['name'] in progression:
                    if progression[risk['name']] in dictionary:
                        skip = True
                # if it is, then break instead of giving the risk
                if skip is True:
                    break

                new_condition_name = risk['name']

                # lower risk of getting it again if not a perm condition
                if dictionary != rabbit.permanent_condition:
                    saved_condition = dictionary[condition]["risks"]
                    for old_risk in saved_condition:
                        if old_risk['name'] == risk['name']:
                            if new_condition_name in ['an infected wound', 'a festering wound']:
                                # if it's infection or festering, we're removing the chance completely
                                # this is both to prevent annoying infection loops
                                # and bc the illness/injury difference causes problems
                                old_risk["chance"] = 0
                            else:
                                old_risk['chance'] = risk["chance"] + 10

                med_rabbit = None
                removed_condition = False
                try:
                    # gather potential event strings for gotten condition
                    if dictionary == rabbit.illnesses:
                        possible_string_list = Condition_Events.ILLNESS_RISK_STRINGS[condition][new_condition_name]
                    elif dictionary == rabbit.injuries:
                        possible_string_list = Condition_Events.INJURY_RISK_STRINGS[condition][new_condition_name]
                    else:
                        possible_string_list = Condition_Events.PERM_CONDITION_RISK_STRINGS[condition][new_condition_name]

                    # if it is a progressive condition, then remove the old condition and keep the new one
                    if condition in progression and new_condition_name == progression.get(condition):
                        removed_condition = True
                        dictionary.pop(condition)

                    # choose event string and ensure warren's med rabbit number aligns with event text
                    random_index = int(random.random() * len(possible_string_list))
                    med_list = get_med_rabbits(Rabbit)
                    if len(med_list) == 0:
                        if random_index == 0:
                            random_index = 1
                        else:
                            med_rabbit = None
                    else:
                        med_rabbit = random.choice(med_list)
                        if med_rabbit == rabbit:
                            random_index = 1
                    event = possible_string_list[random_index]
                except KeyError:
                    print(f"WARNING: {condition} couldn't be found in the risk strings! placeholder string was used")
                    event = "m_c's condition has gotten worse."

                event = event_text_adjust(Rabbit, event, rabbit, other_rabbit=med_rabbit)  # adjust the text
                event_list.append(event)

                # we add the condition to this game switch, this is so we can ensure it's skipped over for this month
                game.switches['skip_conditions'].append(new_condition_name)
                # here we give the new condition
                if new_condition_name in Condition_Events.INJURIES:
                    rabbit.get_injured(new_condition_name, event_triggered=event_triggered)
                    break
                elif new_condition_name in Condition_Events.ILLNESSES:
                    rabbit.get_ill(new_condition_name, event_triggered=event_triggered)
                    if dictionary == rabbit.illnesses or removed_condition:
                        break
                    keys = dictionary[condition].keys()
                    complication = None
                    if new_condition_name == 'an infected wound':
                        complication = 'infected'
                    elif new_condition_name == 'a festering wound':
                        complication = 'festering'
                    if complication is not None:
                        if 'complication' in keys:
                            dictionary[condition]['complication'] = complication
                        else:
                            dictionary[condition].update({'complication': complication})
                    break
                elif new_condition_name in Condition_Events.PERMANENT:
                    rabbit.get_permanent_condition(new_condition_name, event_triggered=event_triggered)
                    break

                # break out of risk giving loop cus we don't want to give multiple risks for one condition
                break

    @staticmethod
    def use_herbs(rabbit, condition, conditions, source):
        # herbs that can be used for the condition and the warren has available
        warren_herbs = set()
        needed_herbs = set()
        warren_herbs.update(game.warren.herbs.keys())
        try:
            needed_herbs.update(source[condition]["herbs"])
        except KeyError:
            print(f"WARNING: {condition} does not exist in it's condition dict! if the condition is 'thorn in paw' or "
                  "'splinter', disregard this! otherwise, check that your condition is in the correct dict or report "
                  "this as a bug.")
            return
        herb_set = warren_herbs.intersection(needed_herbs)
        usable_herbs = list(herb_set)

        if not source[condition]["herbs"]:
            return

        if usable_herbs:
            keys = conditions[condition].keys()
            # determine the effect of the herb
            possible_effects = []
            if conditions[condition]['mortality'] != 0:
                possible_effects.append('mortality')
            if conditions[condition]["risks"]:
                possible_effects.append('risks')
            if 'duration' in keys:
                if conditions[condition]['duration'] > 1:
                    possible_effects.append('duration')
            if not possible_effects:
                return

            effect = random.choice(possible_effects)

            herb_used = usable_herbs[0]
            # Failsafe, since I have no idea why we are getting 0-herb entries.
            while game.warren.herbs[herb_used] <= 0:
                print(f"Warning: {herb_used} was chosen to use, although you currently have "
                      f"{game.warren.herbs[herb_used]}. Removing {herb_used} from herb dict, finding a new herb...")
                game.warren.herbs.pop(herb_used)
                usable_herbs.pop(0)
                if usable_herbs:
                    herb_used = usable_herbs[0]
                else:
                    print("No herbs to use for this injury")
                    return
                print(f"New herb found: {herb_used}")

            # deplete the herb
            amount_used = 1
            game.warren.herbs[herb_used] -= amount_used
            if game.warren.herbs[herb_used] <= 0:
                game.warren.herbs.pop(herb_used)

            # applying a modifier for herb priority. herbs that are better for the condition will have stronger effects
            count = 0
            for herb in source[condition]['herbs']:
                count += 1
                if herb == herb_used:
                    break
            modifier = count
            if rabbit.status in ['elder', 'kittenten']:
                modifier = modifier * 2

            effect_message = 'this should not show up'
            if effect == 'mortality':
                effect_message = 'They will be less likely to die.'
                conditions[condition]["mortality"] += 11 - modifier + int(amount_used * 1.5)
                if conditions[condition]["mortality"] < 1:
                    conditions[condition]["mortality"] = 1
            elif effect == 'duration':
                effect_message = 'They will heal sooner.'
                conditions[condition]["duration"] -= 1
            elif effect == 'risks':
                effect_message = 'The risks associated with their condition are lowered.'
                for risk in conditions[condition]["risks"]:
                    risk["chance"] += 11 - modifier + int(amount_used * 1.5)
                    if risk["chance"] < 0:
                        risk["chance"] = 0

            text = f"{rabbit.name} was given {herb_used.replace('_', ' ')} as treatment for {condition}. {effect_message}"
            game.herb_events_list.append(text)
        else:
            # if they didn't get any herbs, make them more likely to die!! kill the kittenties >:)
            if conditions[condition]["mortality"] > 2:
                conditions[condition]["mortality"] -= 1
            for risk in conditions[condition]["risks"]:
                if risk['chance'] > 2:
                    risk['chance'] -= 1


# ---------------------------------------------------------------------------- #
#                                LOAD RESOURCES                                #
# ---------------------------------------------------------------------------- #


