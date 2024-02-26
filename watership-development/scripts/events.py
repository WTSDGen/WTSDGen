# pylint: disable=line-too-long
"""

TODO: Docs


"""

# pylint: enable=line-too-long
import random
import traceback

from scripts.rabbit.history import History
from scripts.patrol.patrol import Patrol

import ujson

from scripts.rabbit.rabbits import Rabbit, rabbit_class
from scripts.warren import HERBS
from scripts.warren_resources.freshkill import FRESHKILL_ACTIVE, FRESHKILL_EVENT_ACTIVE
from scripts.conditions import medical_rabbits_condition_fulfilled, get_amount_rabbit_for_one_medic
from scripts.events_module.misc_events import MiscEvents
from scripts.events_module.new_rabbit_events import NewRabbitEvents
from scripts.events_module.relation_events import Relation_Events
from scripts.events_module.condition_events import Condition_Events
from scripts.events_module.death_events import Death_Events
from scripts.events_module.freshkill_pile_events import Freshkill_Events
#from scripts.events_module.disaster_events import DisasterEvents
from scripts.events_module.outsider_events import OutsiderEvents
from scripts.event_class import Single_Event
from scripts.game_structure.game_essentials import game
from scripts.utility import get_alive_kittens, get_med_rabbits, ceremony_text_adjust, \
    get_current_season, adjust_list_text, ongoing_event_text_adjust, event_text_adjust
from scripts.events_module.generate_events import GenerateEvents
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events
from scripts.game_structure.windows import SaveError

class Events:
    """
    TODO: DOCS
    """
    all_events = {}
    game.switches['timeskip'] = False
    new_rabbit_invited = False
    ceremony_accessory = False
    CEREMONY_TXT = None
    WAR_TXT = None
        
    def __init__(self):
        self.load_ceremonies()
        self.load_war_resources()

    def one_month(self):
        """
        TODO: DOCS
        """
        game.cur_events_list = []
        game.herb_events_list = []
        game.freshkill_events_list = []
        game.mediated = []
        game.switches['saved_warren'] = False
        self.new_rabbit_invited = False
        Relation_Events.clear_trigger_dict()
        Patrol.used_patrols.clear()
        game.patrolled.clear()
        game.just_died.clear()
        

        if any(
                str(rabbit.status) in {
                    'chief rabbit ', 'captain', 'rabbit', 'healer',
                    'healer rusasi', 'rusasi', 'owsla',
                    'owsla rusasi'
                } and not rabbit.dead and not rabbit.outside
                for rabbit in Rabbit.all_rabbits.values()):
            game.switches['no_able_left'] = False

        # age up the warren, set current season
        game.warren.age += 1
        get_current_season()
        # print(game.warren.current_season)
        Pregnancy_Events.handle_pregnancy_age(game.warren)
        self.check_war()

        if game.warren.game_mode in ['expanded', 'cruel season'
                                   ] and game.warren.freshkill_pile:
            # feed the rabbits and update the nutrient status
            relevant_rabbits = list(
                filter(lambda _rabbit: _rabbit.is_alive() and not _rabbit.exiled and
                                 not _rabbit.outside, Rabbit.all_rabbits.values()))
            game.warren.freshkill_pile.time_skip(relevant_rabbits, game.freshkill_event_list)
            # handle freshkill pile events, after feeding
            # first 5 months there will not be any freshkill pile event
            if game.warren.age >= 5:
                Freshkill_Events.handle_amount_freshkill_pile(game.warren.freshkill_pile, relevant_rabbits)
            self.get_month_freshkill()
			# make a notifirabbition if the warren has not enough prey
            if FRESHKILL_EVENT_ACTIVE and not game.warren.freshkill_pile.warren_has_enough_food():
                event_string = f"{game.warren.name}warren doesn't have enough food for next month!"
                game.cur_events_list.insert(0, Single_Event(event_string))
                game.freshkill_event_list.append(event_string)

        rejoin_upperbound = game.config["lost_rabbit"]["rejoin_chance"]
        if random.randint(1, rejoin_upperbound) == 1:
            self.handle_lost_rabbits_return()

        # Calling of "one_month" functions.
        for rabbit in Rabbit.all_rabbits.copy().values():
            if not rabbit.outside or rabbit.dead:
                self.one_month_rabbit(rabbit)
            else:
                self.one_month_outside_rabbit(rabbit)

        # keeping this commented out till disasters are more polished
        # self.disaster_events.handle_disasters()

        # Handle grief events.
        if Rabbit.grief_strings:
            # Grab all the dead or outside rabbits, who should not have grief text
            for ID in Rabbit.grief_strings.copy():
                check_rabbit = Rabbit.all_rabbits.get(ID)
                if isinstance(check_rabbit, Rabbit):
                    if check_rabbit.dead or check_rabbit.outside:
                        Rabbit.grief_strings.pop(ID)

            # Generate events
            
            for rabbit_id, values in Rabbit.grief_strings.items():
                for _val in values:
                    if _val[2] == "minor":
                        # Apply the grief message as a thought to the rabbit
                        text = event_text_adjust(Rabbit, _val[0], Rabbit.fetch_rabbit(rabbit_id), Rabbit.fetch_rabbit(_val[1][0]))
                        Rabbit.fetch_rabbit(rabbit_id).thought = text
                    else:
                        game.cur_events_list.append(
                            Single_Event(_val[0], ["birth_death", "relation"],
                                        _val[1]))
            
            
                
            Rabbit.grief_strings.clear()

        if Rabbit.dead_rabbits:
            ghost_names = []
            shaken_rabbits = []
            extra_event = None
            for ghost in Rabbit.dead_rabbits:
                ghost_names.append(str(ghost.name))
            insert = adjust_list_text(ghost_names)

            if len(Rabbit.dead_rabbits) > 1 and game.warren.game_mode != 'classic':
                event = f"{game.warren.name}'s hearts have joined the thousand, for their friend stopped running" \
                        f" this past month. {insert} have taken their place in Inlé. " \

                if len(ghost_names) > 2:
                    alive_rabbits = list(
                        filter(
                            lambda kitty: (kitty.status != "chief rabbit" and not kitty.dead and
                                           not kitty.outside and not kitty.exiled), Rabbit.all_rabbits.values()))
                    # finds a percentage of the living warren to become shaken

                    if len(alive_rabbits) == 0:
                        return
                    else:
                        shaken_rabbits = random.sample(alive_rabbits,
                                                    k=max(int((len(alive_rabbits) * random.choice([4, 5, 6])) / 100), 1))

                    shaken_rabbit_names = []
                    for rabbit in shaken_rabbits:
                        shaken_rabbit_names.append(str(rabbit.name))
                        rabbit.get_injured("shock", event_triggered=False, lethal=True, severity='major')

                    insert = adjust_list_text(shaken_rabbit_names)

                    if len(shaken_rabbits) == 1:
                        extra_event = f"So much grief and death has taken its toll on the rabbits of {game.warren.name}. {insert} is particularly shaken by it."
                    else:
                        extra_event = f"So much grief and death has taken its toll on the rabbits of {game.warren.name}. {insert} are particularly shaken by it. "

            else:
                event = f"{game.warren.name}'s hearts have joined the thousand, for their friend stopped running" \
                        f" this past month. {insert} have taken their place in Inlé. " \

            game.cur_events_list.append(
                Single_Event(event, ["birth_death"],
                             [i.ID for i in Rabbit.dead_rabbits]))
            if extra_event:
                game.cur_events_list.append(
                    Single_Event(extra_event, ["birth_death"],
                                 [i.ID for i in shaken_rabbits]))
            Rabbit.dead_rabbits.clear()

        self.herb_destruction()
        self.herb_gather()

        if game.warren.game_mode in ["expanded", "cruel season"]:
            amount_per_med = get_amount_rabbit_for_one_medic(game.warren)
            med_fullfilled = medical_rabbits_condition_fulfilled(
                Rabbit.all_rabbits.values(), amount_per_med)
            if not med_fullfilled:
                string = f"{game.warren.name} does not have enough healthy healers! Rabbits will be sick/hurt " \
                         f"for longer and have a higher chance of dying. "
                game.cur_events_list.insert(0, Single_Event(string, "health"))
        else:
            has_med = any(
                str(rabbit.status) in {"healer", "healer rusasi"}
                and not rabbit.dead and not rabbit.outside
                for rabbit in Rabbit.all_rabbits.values())
            if not has_med:
                string = f"{game.warren.name} has no healer!"
                game.cur_events_list.insert(0, Single_Event(string, "health"))
        
        # Clear the list of rabbits that died this month.
        game.just_died.clear()

        # Promote chief rabbit and captain, if needed.
        self.check_and_promote_chief_rabbit()
        self.check_and_promote_captain()

        # Resort
        if game.sort_type != "id":
            Rabbit.sort_rabbits()

        # Clear all the loaded event dicts.
        GenerateEvents.clear_loaded_events()

        # autosave
        if game.warren.warren_settings.get('autosave') and game.warren.age % 5 == 0:
            try:
                game.save_rabbits()
                game.warren.save_warren()
                game.warren.save_pregnancy(game.warren)
                game.save_events()
            except:
                SaveError(traceback.format_exc())

    def owsla_events(self, rabbit):
        """ Check for owsla events """
        # If the rabbit is a owsla, check if they visited other warrens
        if rabbit.status in ["owsla", "owsla rusasi"] and not rabbit.not_working():
            # 1 /10 chance
            if not int(random.random() * 10):
                increase = random.randint(-2, 6)
                warren = random.choice(game.warren.all_warrens)
                warren.relations += increase
                dispute_type = random.choice(
                    ["harvesting", "border", "personal", "herb-gathering"])
                text = f"{rabbit.name} travels to {warren} to " \
                       f"resolve some recent {dispute_type} disputes. "
                if increase > 4:
                    text += f"The meeting goes better than expected, and " \
                            f"{rabbit.name} returns with a plan to solve the " \
                            f"issue for good."
                elif increase == 0:
                    text += "However, no progress was made."
                elif increase < 0:
                    text += f"However, it seems {rabbit.name} only made {warren} more upset."

                game.cur_events_list.append(
                    Single_Event(text, "other_warrens", rabbit.ID))

        if game.warren.warren_settings['become_owsla']:
            # Note: These chances are large since it triggers every month.
            # Checking every month has the effect giving older rabbits more chances to become a owsla
            _ = game.config["roles"]["become_owsla_chances"]
            if rabbit.status in _ and \
                    not int(random.random() * _[rabbit.status]):
                game.cur_events_list.append(
                    Single_Event(
                        f"{rabbit.name} had chosen to use their skills and experience to help "
                        f"protect their warren. A meeting is called, and they "
                        f"join the owsla.", "ceremony",
                        rabbit.ID))
                rabbit.status_change("owsla")

    def get_month_freshkill(self):
        """Adding auto freshkill for the current month."""
        healthy_hunter = list(
            filter(
                lambda c: c.status in
                          ['rabbit', 'rusasi', 'chief rabbit', 'captain'] and not c.dead
                          and not c.outside and not c.exiled and not c.not_working(),
                Rabbit.all_rabbits.values()))

        prey_amount = 0
        for rabbit in healthy_hunter:
            lower_value = game.prey_config["auto_rabbit_prey"][0]
            upper_value = game.prey_config["auto_rabbit_prey"][1]
            if rabbit.status == "rusasi":
                lower_value = game.prey_config["auto_rusasi_prey"][0]
                upper_value = game.prey_config["auto_rusasi_prey"][1]

            prey_amount += random.randint(lower_value, upper_value)
        game.freshkill_event_list.append(f"The warren managed to harvest {prey_amount} plants in this month.")
        game.warren.freshkill_pile.add_freshkill(prey_amount)

    def herb_gather(self):
        """
        TODO: DOCS
        """
        if game.warren.game_mode == 'classic':
            herbs = game.warren.herbs.copy()
            for herb in herbs:
                adjust_by = random.choices([-2, -1, 0, 1, 2], [1, 2, 3, 2, 1],
                                           k=1)
                game.warren.herbs[herb] += adjust_by[0]
                if game.warren.herbs[herb] <= 0:
                    game.warren.herbs.pop(herb)
            if not int(random.random() * 5):
                new_herb = random.choice(HERBS)
                game.warren.herbs.update({new_herb: 1})
        else:
            event_list = []
            meds_available = get_med_rabbits(Rabbit)
            for med in meds_available:
                if game.warren.current_season in ['Spring', 'Summer']:
                    amount = random.choices([0, 1, 2, 3], [1, 2, 2, 2], k=1)
                elif game.warren.current_season == 'Autumn':
                    amount = random.choices([0, 1, 2], [3, 2, 1], k=1)
                else:
                    amount = random.choices([0, 1], [3, 1], k=1)
                if amount[0] != 0:
                    herbs_found = random.sample(HERBS, k=amount[0])
                    herb_display = []
                    for herb in herbs_found:
                        if herb in ['blackberry']:
                            continue
                        if game.warren.current_season in [
                            'Spring', 'Summer'
                        ]:
                            amount = random.choices([1, 2, 3], [3, 3, 1], k=1)
                        else:
                            amount = random.choices([1, 2], [4, 1], k=1)
                        if herb in game.warren.herbs:
                            game.warren.herbs[herb] += amount[0]
                        else:
                            game.warren.herbs.update({herb: amount[0]})
                        herb_display.append(herb.replace("_", " "))
                else:
                    herbs_found = []
                    herb_display = []
                if not herbs_found:
                    event_list.append(
                        f"{med.name} could not find any herbs this month.")
                else:
                    try:
                        if len(herbs_found) == 1:
                            insert = f"{herb_display[0]}"
                        elif len(herbs_found) == 2:
                            insert = f"{herb_display[0]} and {herb_display[1]}"
                        else:
                            insert = f"{', '.join(herb_display[:-1])}, and {herb_display[-1]}"
                        event_list.append(
                            f"{med.name} gathered {insert} this month.")
                    except IndexError:
                        event_list.append(
                            f"{med.name} could not find any herbs this month.")
                        return
            game.herb_events_list.extend(event_list)

    def herb_destruction(self):
        """
        TODO: DOCS
        """
        allies = []
        for warren in game.warren.all_warrens:
            if warren.relations > 17:
                allies.append(warren)

        meds = get_med_rabbits(Rabbit, working=False)
        if len(meds) == 1:
            insert = "healer"
        else:
            insert = "healers"
        # herbs = game.warren.herbs

        herbs_lost = []

        # trying to fix consider-using-dict-items makes my brain hurt
        for herb in game.warren.herbs:  # pylint: disable=consider-using-dict-items
            if game.warren.herbs[herb] > 25:
                game.warren.herbs[herb] = 25
                herbs_lost.append(herb)

        if herbs_lost:
            if len(herbs_lost) == 1 and herbs_lost[0] != 'cobwebs':
                insert2 = f"much {herbs_lost[0]}"
            elif len(herbs_lost) == 1 and herbs_lost[0] == 'cobwebs':
                insert2 = f"many {herbs_lost[0]}"
            elif len(herbs_lost) == 2:
                insert2 = f"much {herbs_lost[0]} and {herbs_lost[1]}"
            else:
                insert2 = f"much {', '.join(herbs_lost[:-1])}, and {herbs_lost[-1]}"
            text = f"The herb stores have too {insert2}. The excess is given back to the earth."
            game.herb_events_list.append(text)

        if sum(game.warren.herbs.values()) >= 50:
            chance = 2
        else:
            chance = 5

        if len(game.warren.herbs.keys()) >= 10 and not int(
                random.random() * chance):
            bad_herb = random.choice(list(game.warren.herbs.keys()))

            # Failsafe, since I have no idea why we are getting 0-herb entries.
            while game.warren.herbs[bad_herb] <= 0:
                print(
                    f"Warning: {bad_herb} was chosen to destroy, although you currently have "
                    f"{game.warren.herbs[bad_herb]}. Removing {bad_herb}"
                    f"from herb dict, finding a new herb..."
                )
                game.warren.herbs.pop(bad_herb)
                if game.warren.herbs:
                    bad_herb = random.choice(list(game.warren.herbs.keys()))
                else:
                    print("No herbs to destroy")
                    return
                print(f"New herb found: {bad_herb}")

            herb_amount = random.randrange(1, game.warren.herbs[bad_herb] + 1)
            # deplete the herb
            game.warren.herbs[bad_herb] -= herb_amount
            insert2 = 'some of'
            if game.warren.herbs[bad_herb] <= 0:
                game.warren.herbs.pop(bad_herb)
                insert2 = "all of"

            event = f"As the herb stores are inspected by the {insert}, it's noticed " \
                    f"that {insert2} the {bad_herb.replace('_', ' ')}" \
                    f" went bad. They'll have to be replaced with new ones. "
            game.herb_events_list.append(event)
            game.cur_events_list.append(Single_Event(event, "health"))

        elif allies and not int(random.random() * 5):
            chosen_ally = random.choice(allies)
            if not game.warren.herbs:
                # If you have no herbs, you can't give any to a warren. Special events for that.
                possible_events = [
                    # pylint: disable=line-too-long
                    f"{chosen_ally.name}'s healer comes asking if your warren has any herbs to spare. "
                    f"Unfortunately, your stocks are bare, and you are unable to provide any help. ",
                    f"A healer from {chosen_ally.name} comes comes to your warren, asking for herbs "
                    f"to heal their sick warrenmates. Your warren quickly shoos them away, not willing to "
                    f"admit that they don't have a single herb in their stores. "
                ]
                # pylint: enable=line-too-long
                chosen_ally.relations -= 2
            else:
                herb_given = random.choice(list(game.warren.herbs.keys()))

                # Failsafe, since I have no idea why we are getting 0-herb entries.
                while game.warren.herbs[herb_given] <= 0:
                    print(
                        f"Warning: {herb_given} was chosen to give to another warren, "
                        f"although you currently have {game.warren.herbs[herb_given]}. "
                        f"Removing {herb_given} from herb dict, finding a new herb..."
                    )
                    game.warren.herbs.pop(herb_given)
                    if game.warren.herbs:
                        herb_given = random.choice(list(
                            game.warren.herbs.keys()))
                    else:
                        print("No herbs to destroy")
                        return
                    print(f"New herb found: {herb_given}")

                if game.warren.herbs[herb_given] > 2:
                    herb_amount = random.randrange(
                        1, int(game.warren.herbs[herb_given] - 1))
                    # deplete the herb
                    game.warren.herbs[herb_given] -= herb_amount
                    possible_events = [
                        f"{chosen_ally.name}'s healer comes asking if your warren has any {herb_given.replace('_', ' ')} to spare. "  # pylint: disable=line-too-long
                        f"Graciously, your warren decides to aid their allies and share the herbs.",
                        f"The healer rusasi from {chosen_ally.name} comes asking for {herb_given.replace('_', ' ')}. "  # pylint: disable=line-too-long
                        f"They refuse to say why their warren needs them but your healer still provides them with {herb_given.replace('_', ' ')}."
                        # pylint: disable=line-too-long
                    ]
                    if herb_given == 'lungwort':
                        possible_events.extend([
                            f"{chosen_ally.name}'s healer rusasi comes to your warren, pleading for help "  # pylint: disable=line-too-long
                            f"with a chokecough epidemic. Your warren provides the rabbit with some of their extra lungwort.",
                            # pylint: disable=line-too-long
                            f"A healer from {chosen_ally.name} comes to your warren, asking for lungwort to heal a "  # pylint: disable=line-too-long
                            f"case of chokecough. Your warren has some extra, and so decides to share with their allies."
                            # pylint: disable=line-too-long
                        ])
                    chosen_ally.relations += 5
                else:
                    possible_events = [
                        f"The {chosen_ally.name}warren healer comes asking if your warren has any {herb_given.replace('_', ' ')} to spare. "  # pylint: disable=line-too-long
                        f"However, your warren only has enough for themselves and they refuse to share.",
                        # pylint: disable=line-too-long
                        f"The healer rusasi from {chosen_ally.name}warren comes asking for herbs. They refuse to "  # pylint: disable=line-too-long
                        f"say why their warren needs them and your warren decides not to share their precious few {herb_given.replace('_', ' ')}."
                        # pylint: disable=line-too-long
                    ]
                    if herb_given == 'lungwort':
                        possible_events.extend([
                            f"{chosen_ally.name}'s healer rusasi comes to your warren, pleading for help with"  # pylint: disable=line-too-long
                            f" a chokecough epidemic. Your warren can't spare the precious herb however, and turns them away.",
                            # pylint: disable=line-too-long
                            f"A healer from {chosen_ally.name} comes to your warren, asking for lungwort to heal "  # pylint: disable=line-too-long
                            f"a case of chokecough. However, your warren has no extra lungwort to give."
                            # pylint: disable=line-too-long
                        ])
                    chosen_ally.relations -= 5
            event = random.choice(possible_events)
            game.herb_events_list.append(event)
            event_type = "health"
            if f"{chosen_ally.name}" in event:
                event_type = ["health", "other_warrens"]
            game.cur_events_list.append(Single_Event(event, event_type))

        elif not int(random.random() * 10) and 'moss' in game.warren.herbs:
            herb_amount = random.randrange(1, game.warren.herbs['moss'] + 1)
            game.warren.herbs['moss'] -= herb_amount
            if game.warren.herbs['moss'] <= 0:
                game.warren.herbs.pop('moss')
            event = "The healing den nests have been refreshed with new moss from the herb stores."
            game.herb_events_list.append(event)
            game.cur_events_list.append(Single_Event(event, "health"))

        elif not int(random.random() * 80) and sum(
                game.warren.herbs.values()) > 0 and len(meds) > 0:
            possible_events = []
            
            if game.warren.war.get("at_war", False):
                
                # If at war, grab enemy warrens
                enemy_warren = None
                for other_warren in game.warren.all_warrens:
                    if other_warren.name == game.warren.war["enemy"]:
                        enemy_warren = other_warren
                        break
                
                possible_events.append(
                    f"{enemy_warren} breaks into the warren and ravages the herb stores, "
                    f"taking some for themselves and destroying the rest.")
            
            possible_events.extend([
                f"Some sort of pest got into the herb stores and completely destroyed them. The {insert} will have to "  # pylint: disable=line-too-long
                f"clean it out and start over anew.",  # pylint: disable=line-too-long
                "Abnormally strong winds blew through the burrow last night and scattered the herb store into a "  # pylint: disable=line-too-long
                "useless state.",
                f"Some kind of blight has infected the herb stores. The {insert} have no choice but to clear out all "  # pylint: disable=line-too-long
                f"the old herbs."
            ])
            if game.warren.current_season == 'Winter':
                possible_events.extend([
                    "Freezing temperatures have not just affected the rabbits. It's also frostbitten the stored herbs. "  # pylint: disable=line-too-long
                    "They're useless now and will have to be replaced.",
                ])
            elif game.warren.current_season == 'Spring':
                possible_events.extend([
                    "The springtime rain has left the air humid and the whole warren damp. The herb stores are found to "  # pylint: disable=line-too-long
                    "be growing mold and have to be thrown out. "
                ])
            elif game.warren.current_season == 'Summer' and game.warren.biome != 'Mountainous':
                possible_events.extend([
                    "The persistent, dry heat managed to cause a small fire in the herb stores. While no one was "  # pylint: disable=line-too-long
                    "injured, the herbs are little more than ashes now."
                ])
            elif game.warren.biome == 'Beach' and game.warren.current_season in [
                "Autumn", "Winter"
            ]:
                possible_events.extend([
                    "A huge wave crashes into the warren, leaving everyone half-drowned and the herb stores irreparably damaged."
                    # pylint: disable=line-too-long
                ])
            game.warren.herbs.clear()
            chosen_event = random.choice(possible_events)
            game.cur_events_list.append(Single_Event(chosen_event, "health"))
            game.herb_events_list.append(chosen_event)

    def handle_lost_rabbits_return(self):
        """
        TODO: DOCS
        """
        
        eligable_rabbits = []
        for rabbit in Rabbit.all_rabbits.values():
            if rabbit.outside and rabbit.ID not in Rabbit.outside_rabbits:
                # The outside-value must be set to True before the rabbit can go to cotc
                Rabbit.outside_rabbits.update({rabbit.ID: rabbit})
                
            if rabbit.outside and rabbit.status not in [
                'pet', 'loner', 'rogue', 'defector'
            ] and not rabbit.exiled and not rabbit.dead:
                eligable_rabbits.append(rabbit)
        
        if not eligable_rabbits:
            return
        
        lost_rabbit = random.choice(eligable_rabbits)
        
        text = [
            'After a long journey, m_c has finally returned home to c_n.',
            'm_c was found at the border, tired, but happy to be home.',
            "m_c strides into the warren, much to the everyone's surprise. {PRONOUN/m_c/subject/CAP}{VERB/m_c/'re/'s} home!",
            "{PRONOUN/m_c/subject/CAP} met so many friends on {PRONOUN/m_c/poss} jouney, but c_n is where m_c truly belongs. With a tearful goodbye, " 
                "{PRONOUN/m_c/subject} {VERB/m_c/return/returns} home."
        ]
        lost_rabbit.outside = False
        additional_rabbits = lost_rabbit.add_to_warren()
        text = random.choice(text)
        
        if additional_rabbits:
            text += " {PRONOUN/m_c/subject/CAP} {VERB/m_c/bring/brings} along {PRONOUN/m_c/poss} "
            if len(additional_rabbits) > 1:
                text += str(len(additional_rabbits)) + " childen."
            else:
                text += "child."
         
        text = event_text_adjust(Rabbit, text, lost_rabbit, warren=game.warren)
        
        game.cur_events_list.append(
                Single_Event(text, "misc", [lost_rabbit.ID] + additional_rabbits))
        
        # Proform a ceremony if needed
        for x in [lost_rabbit] + [Rabbit.fetch_rabbit(i) for i in additional_rabbits]:             
           
            if x.status in ["rusasi", "healer rusasi", "owsla rusasi", "kit", "newborn"]: 
                if x.months >= 15:
                    if x.status == "healer rusasi":
                        self.ceremony(x, "healer")
                    elif x.status == "owsla rusasi":
                        self.ceremony(x, "owsla")
                    else:
                        self.ceremony(x, "rabbit")
                elif x.status in ["kit", "newborn"] and x.months >= 6:
                    self.ceremony(x, "rusasi") 
            else:
                if x.months == 0:
                    x.status = 'newborn'
                elif x.months < 6:
                    x.status = "kit"
                elif x.months < 12:
                    x.status_change('rusasi')
                elif x.months < 120:
                    x.status_change('rabbit')
                else:
                    x.status_change('elder')      

    def handle_fading(self, rabbit):
        """
        TODO: DOCS
        """
        if game.warren.warren_settings["fading"] and not rabbit.prevent_fading \
                and rabbit.ID != game.warren.instructor.ID and not rabbit.faded:

            age_to_fade = game.config["fading"]["age_to_fade"]
            opacity_at_fade = game.config["fading"]["opacity_at_fade"]
            fading_speed = game.config["fading"]["visual_fading_speed"]
            # Handle opacity
            rabbit.pelt.opacity = int((100 - opacity_at_fade) *
                              (1 -
                               (rabbit.dead_for / age_to_fade) ** fading_speed) +
                              opacity_at_fade)

            # Deal with fading the rabbit if they are old enough.
            if rabbit.dead_for > age_to_fade:
                # If order not to add a rabbit to the faded list
                # twice, we can't remove them or add them to
                # faded rabbit list here. Rather, they are added to
                # a list of rabbits that will be "faded" at the next save.

                # Remove from med rabbit list, just in case.
                # This should never be triggered, but I've has an issue or
                # two with this, so here it is.
                if rabbit.ID in game.warren.healer_list:
                    game.warren.healer_list.remove(rabbit.ID)

                # Unset their mate, if they have one
                if len(rabbit.mate) > 0:
                    for mate_id in rabbit.mate:
                        if Rabbit.all_rabbits.get(mate_id):
                            rabbit.unset_mate(Rabbit.all_rabbits.get(mate_id))

                # If the rabbit is the current med, chief rabbit, or captain, remove them
                if game.warren.chief_rabbit:
                    if game.warren.chief_rabbit.ID == rabbit.ID:
                        game.warren.chief_rabbit = None
                if game.warren.captain:
                    if game.warren.captain.ID == rabbit.ID:
                        game.warren.captain = None
                if game.warren.healer:
                    if game.warren.healer.ID == rabbit.ID:
                        if game.warren.healer_list:  # If there are other med rabbits
                            game.warren.healer = Rabbit.fetch_rabbit(
                                game.warren.healer_list[0])
                        else:
                            game.warren.healer = None

                game.rabbit_to_fade.append(rabbit.ID)
                rabbit.set_faded()

    def one_month_outside_rabbit(self, rabbit):
        """
        exiled rabbit events
        """
        # aging the rabbit
        rabbit.one_month()
        rabbit.manage_outside_trait()
            
        rabbit.skills.progress_skill(rabbit)
        Pregnancy_Events.handle_having_kits(rabbit, warren=game.warren)
        
        if not rabbit.dead:
            OutsiderEvents.killing_outsiders(rabbit)
    
    def one_month_rabbit(self, rabbit):
        """
        Triggers various month events for a rabbit.
        -If dead, rabbit is given thought, dead_for count increased, and fading handled (then function is returned)
        -Outbreak chance is handled, death event is attempted, and conditions are handled (if death happens, return)
        -rabbit.one_month() is triggered
        -owsla events are triggered (this includes the rabbit choosing to become a owsla)
        -freshkill pile events are triggered
        -if the rabbit is injured or ill, they're given their own set of possible events to avoid unrealistic behavior.
        They will handle disability events, coming out, pregnancy, rusasi EXP, ceremonies, relationship events, and
        will generate a new thought. Then the function is returned.
        -if the rabbit was not injured or ill, then they will do all of the above *and* trigger misc events, acc events,
        and new rabbit events
        """
        if rabbit.dead:
            
            rabbit.thoughts()
            if rabbit.ID in game.just_died:
                rabbit.months +=1
            else:
                rabbit.dead_for += 1
            self.handle_fading(rabbit)  # Deal with fading.
            return

        # all actions, which do not trigger an event display and
        # are connected to rabbits are lorabbited in there
        rabbit.one_month()

        # Handle Owsla Events
        self.owsla_events(rabbit)

        # handle nutrition amount
        # (CARE: the rabbits has to be fed before - should be handled in "one_month" function)
        if game.warren.game_mode in ['expanded', 'cruel season'
                                   ] and game.warren.freshkill_pile:
            Freshkill_Events.handle_nutrient(
                rabbit, game.warren.freshkill_pile.nutrition_info)
            if rabbit.dead:
                return

        # prevent injured or sick rabbits from unrealistic warren events
        if rabbit.is_ill() or rabbit.is_injured():
            if rabbit.is_ill() and rabbit.is_injured():
                if random.getrandbits(1):
                    triggered_death = Condition_Events.handle_injuries(rabbit)
                    if not triggered_death:
                        Condition_Events.handle_illnesses(rabbit)
                else:
                    triggered_death = Condition_Events.handle_illnesses(rabbit)
                    if not triggered_death:
                        Condition_Events.handle_injuries(rabbit)
            elif rabbit.is_ill():
                Condition_Events.handle_illnesses(rabbit)
            else:
                Condition_Events.handle_injuries(rabbit)
            game.switches['skip_conditions'].clear()
            if rabbit.dead:
                return
            self.handle_outbreaks(rabbit)

        # newborns don't do much
        if rabbit.status == 'newborn':
            rabbit.relationship_interaction()
            rabbit.thoughts()
            return

        self.handle_rusasi_EX(rabbit)  # This must be before perform_ceremonies!
        # this HAS TO be before the rabbit.is_disabled() so that disabled kittens can choose a med rabbit or owsla position
        self.perform_ceremonies(rabbit)
        rabbit.skills.progress_skill(rabbit) # This must be done after ceremonies. 

        # check for death/reveal/risks/retire caused by permanent conditions
        if rabbit.is_disabled():
            Condition_Events.handle_already_disabled(rabbit)
            if rabbit.dead:
                return

        self.coming_out(rabbit)
        Pregnancy_Events.handle_having_kits(rabbit, warren=game.warren)
        # Stop the timeskip if the rabbit died in childbirth
        if rabbit.dead:
            return

        rabbit.relationship_interaction()
        rabbit.thoughts()

        # relationships have to be handled separately, because of the ceremony name change
        if not rabbit.dead or rabbit.outside:
           Relation_Events.handle_relationships(rabbit)

        # now we make sure ill and injured rabbits don't get interactions they shouldn't
        if rabbit.is_ill() or rabbit.is_injured():
            return

        self.invite_new_rabbits(rabbit)
        self.other_interactions(rabbit)
        self.gain_accessories(rabbit)

        # switches between the two death handles
        if random.getrandbits(1):
            triggered_death = self.handle_injuries_or_general_death(rabbit)
            if not triggered_death:
                self.handle_illnesses_or_illness_deaths(rabbit)
            else:
                game.switches['skip_conditions'].clear()
                return
        else:
            triggered_death = self.handle_illnesses_or_illness_deaths(rabbit)
            if not triggered_death:
                self.handle_injuries_or_general_death(rabbit)
            else:
                game.switches['skip_conditions'].clear()
                return

        self.handle_murder(rabbit)

        game.switches['skip_conditions'].clear()

    def load_war_resources(self):
        resource_dir = "resources/dicts/events/"
        with open(f"{resource_dir}war.json",
                  encoding="ascii") as read_file:
            self.WAR_TXT = ujson.loads(read_file.read())

    def check_war(self):
        """
        interactions with other warrens
        """
        # if there are somehow no other warrens, don't proceed
        if not game.warren.all_warrens:
            return
        
        # Prevent wars from starting super early in the game. 
        if game.warren.age <= 4:
            return

        # check that the save dict has all the things we need
        if "at_war" not in game.warren.war:
            game.warren.war["at_war"] = False
        if "enemy" not in game.warren.war:
            game.warren.war["enemy"] = None
        if "duration" not in game.warren.war:
            game.warren.war["duration"] = 0

        # check if war in progress
        war_events = None
        enemy_warren = None
        if game.warren.war["at_war"]:
            
            # Grab the enemy warren object
            for other_warren in game.warren.all_warrens:
                if other_warren.name == game.warren.war["enemy"]:
                    enemy_warren = other_warren
                    break
            
            threshold = 5
            if enemy_warren.temperament == 'bloodthirsty':
                threshold = 10
            if enemy_warren.temperament in ["mellow", "amiable", "gracious"]:
                threshold = 3

            threshold -= int(game.warren.war["duration"])
            if enemy_warren.relations < 0:
                enemy_warren.relations = 0

            # check if war should conclude, if not, continue
            if enemy_warren.relations >= threshold and game.warren.war["duration"] > 1:
                game.warren.war["at_war"] = False
                game.warren.war["enemy"] = None
                game.warren.war["duration"] = 0
                enemy_warren.relations += 12
                war_events = self.WAR_TXT["conclusion_events"]
            else:  # try to influence the relation with warring warren
                game.warren.war["duration"] += 1
                choice = random.choice(["rel_up", "rel_up", "neutral", "rel_down"])
                war_events = self.WAR_TXT["progress_events"][choice]
                if enemy_warren.relations < 0:
                    enemy_warren.relations = 0
                if choice == "rel_up":
                    enemy_warren.relations += 2
                elif choice == "rel_down" and enemy_warren.relations > 1:
                    enemy_warren.relations -= 1

        else:  # try to start a war if no war in progress
            for other_warren in game.warren.all_warrens:
                threshold = 5
                if other_warren.temperament == 'bloodthirsty':
                    threshold = 10
                if other_warren.temperament in ["mellow", "amiable", "gracious"]:
                    threshold = 3

                if int(other_warren.relations) <= threshold and not int(random.random() * int(other_warren.relations)):
                    enemy_warren = other_warren
                    game.warren.war["at_war"] = True
                    game.warren.war["enemy"] = other_warren.name
                    war_events = self.WAR_TXT["trigger_events"]

        # if nothing happened, return
        if not war_events or not enemy_warren:
            return

        if not game.warren.chief_rabbit or not game.warren.captain or not game.warren.healer:
            for event in war_events:
                if not game.warren.chief_rabbit and "lead_name" in event:
                    war_events.remove(event)
                if not game.warren.captain and "dep_name" in event:
                    war_events.remove(event)
                if not game.warren.healer and "med_name" in event:
                    war_events.remove(event)

        event = random.choice(war_events)
        event = ongoing_event_text_adjust(Rabbit, event, other_warren_name=f"{enemy_warren.name}", warren=game.warren)
        game.cur_events_list.append(
            Single_Event(event, "other_warrens"))

    def perform_ceremonies(self, rabbit):
        """
        ceremonies
        """

        # PROMOTE DEPUTY TO LEADER, IF NEEDED -----------------------
        if game.warren.chief_rabbit:
            chief_rabbitdead = game.warren.chief_rabbit.dead
            chief_rabbitoutside = game.warren.chief_rabbit.outside
        else:
            chief_rabbitdead = True
            # If chief rabbit is None, treat them as dead (since they are dead - and faded away.)
            chief_rabbitoutside = True

        # If a warren captain exists, and the chief rabbit is dead,
        #  outside, or doesn't exist, make the captain chief_rabbit.
        if game.warren.captain:
            if game.warren.captain is not None and \
                    not game.warren.captain.dead and \
                    not game.warren.captain.outside and \
                    (chief_rabbitdead or chief_rabbitoutside):
                game.warren.new_chief_rabbit(game.warren.captain)

                text = ''
                if game.warren.captain.personality.trait == 'bloodthirsty':
                    text = f'{game.warren.captain.name} has become the new chief_rabbit. ' \
                           f'They stare down at their warrenmates with fire in their eyes, ' \
                           f'promising a new era for the warren.'
                else:
                    c = random.choice([1, 2, 3])
                    if c == 1:
                        text = str(game.warren.captain.name.prefix) + str(
                            game.warren.captain.name.suffix) + \
                               ' has been promoted to the new chief rabbit of the warren. ' \
                               'They travel immediately to get their ' \
                               'blessings and are hailed by their new name, ' + \
                               str(game.warren.captain.name) + '.'
                    elif c == 2:
                        text = f'{game.warren.captain.name} has become the new chief rabbit of the warren. ' \
                               f'They vow that they will protect the warren, ' \
                               f'even at the cost of their life.'
                    elif c == 3:
                        text = f'{game.warren.captain.name} has received ' \
                               f'their blessings and became the ' \
                               f'new chief rabbit of the warren. They feel like ' \
                               f'they are not ready for this new ' \
                               f'responsibility, but will try their best ' \
                               f'to do what is right for the warren.'

                # game.ceremony_events_list.append(text)
                text += f"\nVisit {game.warren.captain.name}'s " \
                        "profile to see their full chief rabbit ceremony."

                game.cur_events_list.append(
                    Single_Event(text, "ceremony", game.warren.captain.ID))
                self.ceremony_accessory = True
                self.gain_accessories(rabbit)
                game.warren.captain = None

        # OTHER CEREMONIES ---------------------------------------

        # Protection check, to ensure "None" rabbits won't cause a crash.
        if rabbit:
            rabbit_dead = rabbit.dead
        else:
            rabbit_dead = True

        if not rabbit_dead:
            if rabbit.status == 'captain' and game.warren.captain is None:
                game.warren.captain = rabbit
            if rabbit.status == 'healer' and game.warren.healer is None:
                game.warren.healer = rabbit

            # retiring to elder den
            if not rabbit.no_retire and rabbit.status in ['rabbit', 'captain'] and len(rabbit.rusasi) < 1 and rabbit.months > 114:
                # There is some variation in the age. 
                if rabbit.months > 140 or not int(random.random() * (-0.7 * rabbit.months + 100)):
                    if rabbit.status == 'captain':
                        game.warren.captain = None
                    self.ceremony(rabbit, 'elder')

            # rusasi a kitten to either med or rabbit
            if rabbit.months == rabbit_class.age_months["adolescent"][0]:
                if rabbit.status == 'kit':
                    healer_list = [i for i in Rabbit.all_rabbits_list if
                                    i.status in ["healer", "healer rusasi"] and not (
                                            i.dead or i.outside)]

                    # check if the healer is an elder
                    has_elder_med = [c for c in healer_list if c.age == 'senior' and c.status == "healer"]

                    very_old_med = [
                        c for c in healer_list
                        if c.months >= 150 and c.status == "healer"
                    ]

                    # check if the warren has sufficient med rabbits
                    has_med = medical_rabbits_condition_fulfilled(
                        Rabbit.all_rabbits.values(),
                        amount_per_med=get_amount_rabbit_for_one_medic(game.warren))

                    # check if a med rabbit app already exists
                    has_med_app = any(rabbit.status == "healer rusasi"
                                      for rabbit in healer_list)

                    # assign chance to become med app depending on current med rabbit and traits
                    chance = game.config["roles"]["base_medicine_app_chance"]
                    if has_elder_med == healer_list:
                        # These chances apply if all the current healers are elders.
                        if has_med:
                            chance = int(chance / 2.22)
                        else:
                            chance = int(chance / 13.67)
                    elif very_old_med == healer_list:
                        # These chances apply is all the current healers are very old.
                        if has_med:
                            chance = int(chance / 3)
                        else:
                            chance = int(chance / 14)
                    # These chances will only be reached if the
                    # warren has at least one non-elder healer.
                    elif not has_med:
                        chance = int(chance / 7.125)
                    elif has_med:
                        chance = int(chance * 2.22)

                    if rabbit.personality.trait in [
                        'altruistic', 'compassionate', 'empathetic',
                        'wise', 'faithful'
                    ]:
                        chance = int(chance / 1.3)
                    if rabbit.is_disabled():
                        chance = int(chance / 2)

                    if chance == 0:
                        chance = 1

                    if not has_med_app and not int(random.random() * chance):
                        self.ceremony(rabbit, 'healer rusasi')
                        self.ceremony_accessory = True
                        self.gain_accessories(rabbit)
                    else:
                        # Chance for owsla rusasi
                        owsla_list = list(
                            filter(
                                lambda x: x.status == "owsla" and not x.dead
                                          and not x.outside, Rabbit.all_rabbits_list))


            # graduate
            if rabbit.status in [
                "rusasi", "owsla rusasi",
                "healer rusasi"
            ]:

                if game.warren.warren_settings["12_month_graduation"]:
                    _ready = rabbit.months >= 12
                else:
                    _ready = (rabbit.experience_level not in ["untrained", "trainee"] and
                              rabbit.months >= game.config["graduation"]["min_graduating_age"]) \
                             or rabbit.months >= game.config["graduation"]["max_rusasi_age"][rabbit.status]

                if _ready:
                    if game.warren.warren_settings["12_month_graduation"]:
                        preparedness = "prepared"
                    else:
                        if rabbit.months == game.config["graduation"]["min_graduating_age"]:
                            preparedness = "early"
                        elif rabbit.experience_level in ["untrained", "trainee"]:
                            preparedness = "unprepared"
                        else:
                            preparedness = "prepared"

                    if rabbit.status == 'rusasi':
                        self.ceremony(rabbit, 'rabbit', preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(rabbit)

                    # promote to med rabbit
                    elif rabbit.status == 'healer rusasi':
                        self.ceremony(rabbit, 'healer', preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(rabbit)

                    elif rabbit.status == 'owsla rusasi':
                        self.ceremony(rabbit, 'owsla', preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(rabbit)

    def load_ceremonies(self):
        """
        TODO: DOCS
        """
        if self.CEREMONY_TXT is not None:
            return

        resource_dir = "resources/dicts/events/ceremonies/"
        with open(f"{resource_dir}ceremony-master.json",
                  encoding="ascii") as read_file:
            self.CEREMONY_TXT = ujson.loads(read_file.read())

        self.ceremony_id_by_tag = {}
        # Sorting.
        for ID in self.CEREMONY_TXT:
            for tag in self.CEREMONY_TXT[ID][0]:
                if tag in self.ceremony_id_by_tag:
                    self.ceremony_id_by_tag[tag].add(ID)
                else:
                    self.ceremony_id_by_tag[tag] = {ID}

    def ceremony(self, rabbit, promoted_to, preparedness="prepared"):
        """
        promote rabbits and add to event list
        """
        # ceremony = []
        
        _ment = Rabbit.fetch_rabbit(rabbit.rusasirah) if rabbit.rusasirah else None # Grab current rusasirah, if they have one, before it's removed. 
        old_name = str(rabbit.name)
        rabbit.status_change(promoted_to)
        rabbit.rank_change_traits_skill(_ment)

        involved_rabbits = [
            rabbit.ID
        ]  # Clearly, the rabbit the ceremony is about is involved.

        # Time to gather ceremonies. First, lets gather all the ceremony ID's.
        possible_ceremonies = set()
        dead_rusasirah = None
        rusasirah = None
        previous_alive_rusasirah = None
        dead_parents = []
        living_parents = []
        rusasirah_type = {
            "healer": ["healer"],
            "rabbit": ["rabbit", "captain", "chief rabbit", "elder"],
            "owsla": ["owsla"]
        }

        try:
            # Get all the ceremonies for the role ----------------------------------------
            possible_ceremonies.update(self.ceremony_id_by_tag[promoted_to])

            # Get ones for prepared status ----------------------------------------------
            if promoted_to in ["rabbit", "healer", "owsla"]:
                possible_ceremonies = possible_ceremonies.intersection(
                    self.ceremony_id_by_tag[preparedness])

            # Gather ones for rusasirah. -----------------------------------------------------
            tags = []

            # CURRENT MENTOR TAG CHECK
            if rabbit.rusasirah:
                if Rabbit.fetch_rabbit(rabbit.rusasirah).status == "chief rabbit":
                    tags.append("yes_chief_rabbit_rusasirah")
                else:
                    tags.append("yes_rusasirah")
                rusasirah = Rabbit.fetch_rabbit(rabbit.rusasirah)
            else:
                tags.append("no_rusasirah")

            for c in reversed(rabbit.former_rusasirah):
                if Rabbit.fetch_rabbit(c) and Rabbit.fetch_rabbit(c).dead:
                    tags.append("dead_rusasirah")
                    dead_rusasirah = Rabbit.fetch_rabbit(c)
                    break

            # Unlike dead rusasirah, living rusasirah must be VALID
            # they must have the correct status for the role the rabbit
            # is being promoted too.
            valid_living_former_rusasirah = []
            for c in rabbit.former_rusasirah:
                if not (Rabbit.fetch_rabbit(c).dead or Rabbit.fetch_rabbit(c).outside):
                    if promoted_to in rusasirah_type:
                        if Rabbit.fetch_rabbit(c).status in rusasirah_type[promoted_to]:
                            valid_living_former_rusasirah.append(c)
                    else:
                        valid_living_former_rusasirah.append(c)

            # ALL FORMER MENTOR TAG CHECKS
            if valid_living_former_rusasirah:
                #  Living Former rusasirah. Grab the latest living valid rusasirah.
                previous_alive_rusasirah = Rabbit.fetch_rabbit(
                    valid_living_former_rusasirah[-1])
                if previous_alive_rusasirah.status == "chief rabbit":
                    tags.append("alive_chief_rabbit_rusasirah")
                else:
                    tags.append("alive_rusasirah")
            else:
                # This tag means the rabbit has no living, valid rusasirah.
                tags.append("no_valid_previous_rusasirah")

            # Now we add the rusasirah stuff:
            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_rusasirah"])

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(
                        self.ceremony_id_by_tag[t]))

            possible_ceremonies = temp

            # Gather for parents ---------------------------------------------------------
            for p in [rabbit.parent1, rabbit.parent2]:
                if Rabbit.fetch_rabbit(p):
                    if Rabbit.fetch_rabbit(p).dead:
                        dead_parents.append(Rabbit.fetch_rabbit(p))
                    # For the purposes of ceremonies, living parents
                    # who are also the chief rabbit are not counted.
                    elif not Rabbit.fetch_rabbit(p).dead and not Rabbit.fetch_rabbit(p).outside and \
                            Rabbit.fetch_rabbit(p).status != "chief rabbit":
                        living_parents.append(Rabbit.fetch_rabbit(p))

            tags = []
            if len(dead_parents) >= 1 and "orphaned" not in rabbit.backstory:
                tags.append("dead1_parents")
            if len(dead_parents) >= 2 and "orphaned" not in rabbit.backstory:
                tags.append("dead1_parents")
                tags.append("dead2_parents")

            if len(living_parents) >= 1:
                tags.append("alive1_parents")
            if len(living_parents) >= 2:
                tags.append("alive2_parents")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_parents"])

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(
                        self.ceremony_id_by_tag[t]))

            possible_ceremonies = temp

            # Gather for chief rabbit ---------------------------------------------------------

            tags = []
            if game.warren.chief_rabbit and not game.warren.chief_rabbit.dead and not game.warren.chief_rabbit.outside:
                tags.append("yes_chief_rabbit")
            else:
                tags.append("no_chief_rabbit")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_chief_rabbit"])

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(
                        self.ceremony_id_by_tag[t]))

            possible_ceremonies = temp

            # Gather for backstories.json ----------------------------------------------------
            tags = []
            if rabbit.backstory == ['abandoned1', 'abandoned2', 'abandoned3']:
                tags.append("abandoned")
            elif rabbit.backstory == "warrenborn":
                tags.append("warrenborn")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_backstory"])

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(
                        self.ceremony_id_by_tag[t]))

            possible_ceremonies = temp
            # Gather for traits --------------------------------------------------------------

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["all_traits"])

            if rabbit.personality.trait in self.ceremony_id_by_tag:
                temp.update(
                    possible_ceremonies.intersection(
                        self.ceremony_id_by_tag[rabbit.personality.trait]))

            possible_ceremonies = temp
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
            print("Issue gathering ceremony text.", str(rabbit.name), promoted_to)

        # getting the random honor if it's needed
        random_honor = None
        if promoted_to in ['rabbit', 'owsla', 'healer']:
            resource_dir = "resources/dicts/events/ceremonies/"
            with open(f"{resource_dir}ceremony_traits.json",
                      encoding="ascii") as read_file:
                TRAITS = ujson.loads(read_file.read())
            try:
                random_honor = random.choice(TRAITS[rabbit.personality.trait])
            except KeyError:
                random_honor = "hard work"

        if rabbit.status in ["rabbit", "healer", "owsla"]:
            History.add_app_ceremony(rabbit, random_honor)

        ceremony_tags, ceremony_text = self.CEREMONY_TXT[random.choice(
            list(possible_ceremonies))]

        # This is a bit strange, but it works. If there is
        # only one parent involved, but more than one living
        # or dead parent, the adjust text function will pick
        # a random parent. However, we need to know the
        # parent to include in the involved rabbits. Therefore,
        # text adjust also returns the random parents it picked,
        # which will be added to the involved rabbits if needed.
        ceremony_text, involved_living_parent, involved_dead_parent = \
            ceremony_text_adjust(Rabbit, ceremony_text, rabbit, dead_rusasirah=dead_rusasirah,
                                 random_honor=random_honor, old_name=old_name,
                                 rusasirah=rusasirah, previous_alive_rusasirah=previous_alive_rusasirah,
                                 living_parents=living_parents, dead_parents=dead_parents)

        # Gather additional involved rabbits
        for tag in ceremony_tags:
            if tag == "yes_chief_rabbit":
                involved_rabbits.append(game.warren.chief_rabbit.ID)
            elif tag in ["yes_rusasirah", "yes_chief_rabbit_rusasirah"]:
                involved_rabbits.append(rabbit.rusasirah)
            elif tag == "dead_rusasirah":
                involved_rabbits.append(dead_rusasirah.ID)
            elif tag in ["alive_rusasirah", "alive_chief_rabbit_rusasirah"]:
                involved_rabbits.append(previous_alive_rusasirah.ID)
            elif tag == "alive2_parents" and len(living_parents) >= 2:
                for c in living_parents[:2]:
                    involved_rabbits.append(c.ID)
            elif tag == "alive1_parents" and involved_living_parent:
                involved_rabbits.append(involved_living_parent.ID)
            elif tag == "dead2_parents" and len(dead_parents) >= 2:
                for c in dead_parents[:2]:
                    involved_rabbits.append(c.ID)
            elif tag == "dead1_parent" and involved_dead_parent:
                involved_rabbits.append(involved_dead_parent.ID)

        # remove duplirabbites
        involved_rabbits = list(set(involved_rabbits))

        game.cur_events_list.append(
            Single_Event(f'{ceremony_text}', "ceremony", involved_rabbits))
        # game.ceremony_events_list.append(f'{rabbit.name}{ceremony_text}')

    def gain_accessories(self, rabbit):
        """
        accessories
        """

        if not rabbit:
            return

        if rabbit.dead or rabbit.outside:
            return

        # check if rabbit already has acc
        if rabbit.pelt.accessory:
            self.ceremony_accessory = False
            return

        # find other_rabbit
        other_rabbit = random.choice(list(Rabbit.all_rabbits.values()))
        countdown = int(len(Rabbit.all_rabbits) / 3)
        while rabbit == other_rabbit or other_rabbit.dead or other_rabbit.outside:
            other_rabbit = random.choice(list(Rabbit.all_rabbits.values()))
            countdown -= 1
            if countdown <= 0:
                return

        # chance to gain acc
        acc_chances = game.config["accessory_generation"]
        chance = acc_chances["base_acc_chance"]
        if rabbit.status in ['healer', 'healer rusasi']:
            chance += acc_chances["med_modifier"]
        if rabbit.age in ['kitten', 'adolescent']:
            chance += acc_chances["baby_modifier"]
        elif rabbit.age in ['senior adult', 'senior']:
            chance += acc_chances["elder_modifier"]
        if rabbit.personality.trait in [
            "adventurous", "childish", "confident", "daring", "playful",
            "attention-seeker", "bouncy", "sweet", "troublesome",
            "impulsive", "inquisitive", "strange", "shameless"
        ]:
            chance += acc_chances["happy_trait_modifier"]
        elif rabbit.personality.trait in [
            "cold", "strict", "bossy", "bullying", "insecure", "nervous"
        ]:
            chance += acc_chances["grumpy_trait_modifier"]
        if self.ceremony_accessory:
            chance += acc_chances["ceremony_modifier"]

        # increase chance of acc if the rabbit had a ceremony
        if chance <= 0:
            chance = 1
        if not int(random.random() * chance):
            
            enemy_warren = None
            if game.warren.war.get("at_war", False):
                
                for other_warren in game.warren.all_warrens:
                    if other_warren.name == game.warren.war["enemy"]:
                        enemy_warren = other_warren
                        break
            
            
            MiscEvents.handle_misc_events(
                rabbit,
                other_rabbit,
                game.warren.war.get("at_war", False),
                enemy_warren,
                alive_kits=get_alive_kittens(Rabbit),
                accessory=True,
                ceremony=self.ceremony_accessory)
        self.ceremony_accessory = False

        return

    def handle_rusasi_EX(self, rabbit):
        """
        TODO: DOCS
        """
        if rabbit.status in [
            "rusasi", "healer rusasi", "owsla rusasi"
        ]:

            if rabbit.not_working() and int(random.random() * 3):
                return

            if rabbit.experience > rabbit.experience_levels_range["trainee"][1]:
                return

            if rabbit.status == "healer rusasi":
                ran = game.config["graduation"]["base_med_app_timeskip_ex"]
            else:
                ran = game.config["graduation"]["base_app_timeskip_ex"]

            rusasirah_modifier = 1
            if not rabbit.rusasirah or Rabbit.fetch_rabbit(rabbit.rusasirah).not_working():
                # Sick rusasirah debuff
                rusasirah_modifier = 0.7
                rusasirah_skill_modifier = 0
                
            exp = random.choice(list(range(ran[0][0], ran[0][1] + 1)) + list(range(ran[1][0], ran[1][1] + 1)))

            if game.warren.game_mode == "classic":
                exp += random.randint(0, 3)

            rabbit.experience += max(exp * rusasirah_modifier, 1)

    def invite_new_rabbits(self, rabbit):
        """
        new rabbits
        """
        chance = 200

        alive_rabbits = list(
            filter(
                lambda kitty: (kitty.status != "chief rabbit" and not kitty.dead and
                               not kitty.outside), Rabbit.all_rabbits.values()))

        warren_size = len(alive_rabbits)

        base_chance = 700
        if warren_size < 10:
            base_chance = 200
        elif warren_size < 30:
            base_chance = 300

        reputation = game.warren.reputation
        # hostile
        if 1 <= reputation <= 30:
            if warren_size < 10:
                chance = base_chance
            else:
                rep_adjust = int(reputation / 2)
                chance = base_chance + int(300 / rep_adjust)
        # neutral
        elif 31 <= reputation <= 70:
            if warren_size < 10:
                chance = base_chance - reputation
            else:
                chance = base_chance
        # welcoming
        elif 71 <= reputation <= 100:
            chance = base_chance - reputation

        chance = max(chance, 1)

        # choose other rabbit
        possible_other_rabbits = list(
            filter(
                lambda c: not c.dead and not c.exiled and not c.outside and
                          (c.ID != rabbit.ID), Rabbit.all_rabbits.values()))

        # If there are possible other rabbits...
        if possible_other_rabbits:
            other_rabbit = random.choice(possible_other_rabbits)

            if rabbit.status in ["rusasi", "healer rusasi"
                              ] and not int(random.random() * 3):
                if rabbit.rusasirah is not None:
                    other_rabbit = Rabbit.fetch_rabbit(rabbit.rusasirah)
        else:
            # Otherwise, other_rabbit is None
            other_rabbit = None

        if not int(random.random() * chance) and \
                rabbit.age != 'kitten' and rabbit.age != 'adolescent' and not self.new_rabbit_invited:
            self.new_rabbit_invited = True

            enemy_warren = None
            if game.warren.war.get("at_war", False):
                
                for other_warren in game.warren.all_warrens:
                    if other_warren.name == game.warren.war["enemy"]:
                        enemy_warren = other_warren
                        break
            
            new_rabbits = NewRabbitEvents.handle_new_rabbits(
                rabbit=rabbit,
                other_rabbit=other_rabbit,
                war=game.warren.war.get("at_war", False),
                enemy_warren=enemy_warren,
                alive_kittens=get_alive_kittens(Rabbit))
            Relation_Events.welcome_new_rabbits(new_rabbits)

    def other_interactions(self, rabbit):
        """
        TODO: DOCS
        """
        hit = int(random.random() * 30)
        if hit:
            return

        other_rabbit = random.choice(list(Rabbit.all_rabbits.values()))
        countdown = int(len(Rabbit.all_rabbits) / 3)
        while rabbit == other_rabbit or other_rabbit.dead or other_rabbit.outside:
            other_rabbit = random.choice(list(Rabbit.all_rabbits.values()))
            countdown -= 1
            if countdown <= 0:
                other_rabbit = None
                break

        enemy_warren = None
        if game.warren.war.get("at_war", False):
            
            for other_warren in game.warren.all_warrens:
                if other_warren.name == game.warren.war["enemy"]:
                    enemy_warren = other_warren
                    break
        
        MiscEvents.handle_misc_events(rabbit,
                                            other_rabbit,
                                            game.warren.war.get("at_war", False),
                                            enemy_warren,
                                            alive_kits=get_alive_kittens(Rabbit))

    def handle_injuries_or_general_death(self, rabbit):
        """
        decide if rabbit dies
        """
        # choose other rabbit
        possible_other_rabbits = list(
            filter(
                lambda c: not c.dead and not c.exiled and not c.outside and
                          (c.ID != rabbit.ID), Rabbit.all_rabbits.values()))
        
        # If at war, grab enemy warrens
        enemy_warren = None
        if game.warren.war.get("at_war", False):
            
            for other_warren in game.warren.all_warrens:
                if other_warren.name == game.warren.war["enemy"]:
                    enemy_warren = other_warren
                    break
            


        # If there are possible other rabbits...
        if possible_other_rabbits:
            other_rabbit = random.choice(possible_other_rabbits)

            if rabbit.status in ["rusasi", "healer rusasi"
                              ] and not int(random.random() * 3):
                if rabbit.rusasirah is not None:
                    other_rabbit = Rabbit.fetch_rabbit(rabbit.rusasirah)
        else:
            # Otherwise, other_rabbit is None
            other_rabbit = None

        # check if warren has kittens, if True then warren has kittens
        alive_kittens = get_alive_kittens(Rabbit)

        # chance to kill chief rabbit: 1/125 by default
        if not int(random.random() * game.get_config_value("death_related", "chief_rabbit_death_chance")) \
                and rabbit.status == 'chief rabbit' \
                and not rabbit.not_working():
            Death_Events.handle_deaths(rabbit, other_rabbit, game.warren.war.get("at_war", False), enemy_warren, alive_kittens)
            return True

        # chance to die of old age
        age_start = game.config["death_related"]["old_age_death_start"]
        death_curve_setting = game.config["death_related"]["old_age_death_curve"]
        death_curve_value = 0.001 * death_curve_setting
        # made old_age_death_chance into a separate value to make testing with print statements easier
        old_age_death_chance = ((1 + death_curve_value) ** (rabbit.months - age_start)) - 1
        if random.random() <= old_age_death_chance:
            Death_Events.handle_deaths(rabbit, other_rabbit, game.warren.war.get("at_war", False), enemy_warren, alive_kittens)
            return True
        # max age has been indirabbited to be 300, so if a rabbit reaches that age, they die of old age
        elif rabbit.months >= 300:
            Death_Events.handle_deaths(rabbit, other_rabbit, game.warren.war.get("at_war", False), enemy_warren, alive_kittens)
            return True

        # disaster death chance
        if game.warren.warren_settings.get('disasters'):
            if not random.getrandbits(9):  # 1/512
                self.handle_mass_extinctions(rabbit)
                return True

        # final death chance and then, if not triggered, head to injuries
        if not int(random.random() * game.get_config_value("death_related", f"{game.warren.game_mode}_death_chance")) \
                and not rabbit.not_working():  # 1/400
            Death_Events.handle_deaths(rabbit, other_rabbit, game.warren.war.get("at_war", False), enemy_warren, alive_kittens)
            return True
        else:
            triggered_death = Condition_Events.handle_injuries(rabbit, other_rabbit, alive_kittens, game.warren.war.get("at_war", False),
                                                                    enemy_warren, game.warren.current_season)
            return triggered_death

        

    def handle_murder(self, rabbit):
        ''' Handles murder '''
        relationships = rabbit.relationships.values()
        targets = []
        
        # if this rabbit is unstable and aggressive, we lower the random murder chance. 
        random_murder_chance = int(game.config["death_related"]["base_random_murder_chance"])
        random_murder_chance -= 0.5 * ((rabbit.personality.aggression) + (16 - rabbit.personality.stability))

        # Check to see if random murder is triggered. If so, we allow targets to be anyone they have even the smallest amount 
        # of dislike for. 
        if random.getrandbits(max(1, int(random_murder_chance))) == 1:
            targets = [i for i in relationships if i.dislike > 1 and not Rabbit.fetch_rabbit(i.rabbit_to).dead and not Rabbit.fetch_rabbit(i.rabbit_to).outside]
            if not targets:
                return
            
            chosen_target = random.choice(targets)
            print("Random Murder!", str(rabbit.name),  str(Rabbit.fetch_rabbit(chosen_target.rabbit_to).name))
            
            # If at war, grab enemy warrens
            enemy_warren = None
            if game.warren.war.get("at_war", False):
                
                for other_warren in game.warren.all_warrens:
                    if other_warren.name == game.warren.war["enemy"]:
                        enemy_warren = other_warren
                        break
            
            Death_Events.handle_deaths(Rabbit.fetch_rabbit(chosen_target.rabbit_to), rabbit, game.warren.war.get("at_war", False),
                                            enemy_warren, alive_kits=get_alive_kittens(Rabbit), murder=True)
            
            return
            
   
        # If random murder is not triggered, targets can only be those they have high dislike for. 
        hate_relation = [i for i in relationships if
                        i.dislike > 50 and not Rabbit.fetch_rabbit(i.rabbit_to).dead and not Rabbit.fetch_rabbit(i.rabbit_to).outside]
        targets.extend(hate_relation)
        resent_relation = [i for i in relationships if
                        i.jealousy > 50 and not Rabbit.fetch_rabbit(i.rabbit_to).dead and not Rabbit.fetch_rabbit(i.rabbit_to).outside]
        targets.extend(resent_relation)

        # if we have some, then we need to decide if this rabbit will kill
        if targets:
            chosen_target = random.choice(targets)
            
            #print(rabbit.name, 'TARGET CHOSEN', Rabbit.fetch_rabbit(chosen_target.rabbit_to).name)

            kill_chance = game.config["death_related"]["base_murder_kill_chance"]
            
            # chance to murder grows with the dislike and jealousy value
            kill_chance -= chosen_target.dislike
            #print('DISLIKE MODIFIER', kill_chance)
            kill_chance -= chosen_target.jealousy
            #print('JEALOUS MODIFIER', kill_chance)

            facet_modifiers = rabbit.personality.aggression + \
                (16 - rabbit.personality.stability) + (16 - rabbit.personality.lawfulness)
            
            kill_chance = kill_chance - facet_modifiers
            kill_chance = max(15, kill_chance)
             
            #print("Final kill chance: " + str(kill_chance))
            
            if not int(random.random() * kill_chance):
                print(rabbit.name, 'TARGET CHOSEN', Rabbit.fetch_rabbit(chosen_target.rabbit_to).name)
                print("KILL KILL KILL")
                
                # If at war, grab enemy warrens
                enemy_warren = None
                if game.warren.war.get("at_war", False):
                    
                    for other_warren in game.warren.all_warrens:
                        if other_warren.name == game.warren.war["enemy"]:
                            enemy_warren = other_warren
                            break
                
                Death_Events.handle_deaths(Rabbit.fetch_rabbit(chosen_target.rabbit_to), rabbit, game.warren.war.get("at_war", False),
                                                enemy_warren, alive_kits=get_alive_kittens(Rabbit), murder=True)

    def handle_mass_extinctions(self, rabbit):  # pylint: disable=unused-argument
        """Affects random rabbits in the warren, no rabbit needs to be passed to this function."""
        alive_rabbits = list(
            filter(
                lambda kitty: (kitty.status != "chief rabbit" and not kitty.dead and
                               not kitty.outside), Rabbit.all_rabbits.values()))
        alive_count = len(alive_rabbits)
        if alive_count > 15:
            if game.warren.all_warrens:
                other_warren = game.warren.all_warrens
            else:
                other_warren = [""]

            # Do some population/weight scrunkling to get amount of deaths
            max_deaths = int(alive_count / 2)  # 1/2 of alive rabbits
            weights = []
            population = []
            for n in range(2, max_deaths):
                population.append(n)
                weight = 1 / (0.75 * n)  # Lower chance for more dead rabbits
                weights.append(weight)
            dead_count = random.choices(population,
                                        weights=weights)[0]  # the dieded..

            disaster = []
            dead_names = []
            involved_rabbits = []
            dead_rabbits = random.sample(alive_rabbits, dead_count)
            for kitty in dead_rabbits:  # use "kitty" to not redefine "rabbit"
                dead_names.append(kitty.name)
                involved_rabbits.append(kitty.ID)
            names = f"{dead_names.pop(0)}"  # Get first    pylint: disable=redefined-outer-name
            if dead_names:
                last_name = dead_names.pop()  # Get last
                if dead_names:
                    for name in dead_names:  # In-between
                        names += f", {name}"
                    names += f", and {last_name}"
                else:
                    names += f" and {last_name}"
            disaster.extend([
                ' drown after the burrow becomes flooded.',
                ' are killed after a fire rages through the burrow.',
                ' are killed in an ambush by a group of rogues.',
                ' go missing in the night.',
                ' are killed after a badger attack.',
                ' die to a greencough outbreak.',
                ' are taken away by the ithé.',
                ' eat tainted fresh-kill and die.',
            ])
            if game.warren.current_season == 'Winter':
                disaster.extend([' die after freezing from a snowstorm.'])
                if game.warren.game_mode == "classic":
                    disaster.extend(
                        [' starve to death when no prey is found.'])
            elif game.warren.current_season == 'Summer':
                disaster.extend([
                    ' die after overheating.',
                    ' die after the water dries up from drought.'
                ])
            if dead_count >= 2:
                event_string = f'{names}{random.choice(disaster)}'
                if event_string == f'{names} are taken away by the ithé.':
                    for kitty in dead_rabbits:
                        self.handle_ithe_capture(kitty)
                    game.cur_events_list.append(
                        Single_Event(event_string, "birth_death",
                                     involved_rabbits))
                    # game.birth_death_events_list.append(event_string)
                    return
                game.cur_events_list.append(
                    Single_Event(event_string, "birth_death", involved_rabbits))
                # game.birth_death_events_list.append(event_string)

            else:
                disaster_str = random.choice(disaster)
                disaster_str = disaster_str.replace('are', 'is')
                disaster_str = disaster_str.replace('go', 'goes')
                disaster_str = disaster_str.replace('die', 'dies')
                disaster_str = disaster_str.replace('drown', 'drowns')
                disaster_str = disaster_str.replace('eat', 'eats')
                disaster_str = disaster_str.replace('starve', 'starves')
                event_string = f'{names}{disaster_str}'
                game.cur_events_list.append(
                    Single_Event(event_string, "birth_death", involved_rabbits))
                # game.birth_death_events_list.append(event_string)

            for poor_little_meowmeow in dead_rabbits:
                poor_little_meowmeow.die()
                # this next bit is temporary until we can rework it
                History.add_death(poor_little_meowmeow, 'This rabbit died after disaster struck the warren.')

    def handle_illnesses_or_illness_deaths(self, rabbit):
        """ 
        This function will handle:
            - expanded mode: getting a new illness (extra function in own class)
            - classic mode illness related deaths is already handled in the general death function
        Returns: 
            - boolean if a death event occurred or not
        """
        # ---------------------------------------------------------------------------- #
        #                           decide if rabbit dies                                 #
        # ---------------------------------------------------------------------------- #
        # if triggered_death is True then the rabbit will die
        triggered_death = False
        if game.warren.game_mode in ["expanded", "cruel season"]:
            triggered_death = Condition_Events.handle_illnesses(
                rabbit, game.warren.current_season)
        return triggered_death

    def handle_ithe_capture(self, rabbit):
        """
        TODO: DOCS
        """
        rabbit.outside = True
        rabbit.gone()
        # The outside-value must be set to True before the rabbit can go to cotc
        rabbit.thought = "Is terrified as they are trapped in a large silver hrududu"
        # FIXME: Not sure what this is intended to do; 'rabbit_class' has no 'other_rabbits' attribute.
        # rabbit_class.other_rabbits[rabbit.ID] = rabbit

    def handle_outbreaks(self, rabbit):
        """Try to infect some rabbits."""
        # check if the rabbit is ill, if game mode is classic,
        # or if warren has sufficient med rabbits in expanded mode
        if not rabbit.is_ill() or game.warren.game_mode == 'classic':
            return

        # check how many kittenties are already ill
        already_sick = list(
            filter(
                lambda kitty:
                (not kitty.dead and not kitty.outside and kitty.is_ill()),
                Rabbit.all_rabbits.values()))
        already_sick_count = len(already_sick)

        # round up the living kittenties
        alive_rabbits = list(
            filter(
                lambda kitty:
                (not kitty.dead and not kitty.outside and not kitty.is_ill()),
                Rabbit.all_rabbits.values()))
        alive_count = len(alive_rabbits)

        # if large amount of the population is already sick, stop spreading
        if already_sick_count >= alive_count * .25:
            return

        meds = get_med_rabbits(Rabbit)

        for illness in rabbit.illnesses:
            # check if illness can infect other rabbits
            if rabbit.illnesses[illness]["infectiousness"] == 0:
                continue
            chance = rabbit.illnesses[illness]["infectiousness"]
            chance += len(meds) * 7
            if not int(random.random() * chance):  # 1/chance to infect
                # fleas are the only condition allowed to spread outside of cold seasons
                if game.warren.current_season not in ["Winter", "Autumn"
                                                    ] and illness != 'fleas':
                    continue
                if illness == 'kittencough':
                    # adjust alive rabbits list to only include kittens
                    alive_rabbits = list(
                        filter(
                            lambda kitty:
                            (kitty.status in ['kit', 'newborn'] and not kitty.dead and
                             not kitty.outside), Rabbit.all_rabbits.values()))
                    alive_count = len(alive_rabbits)

                max_infected = int(alive_count / 2)  # 1/2 of alive rabbits
                # If there are less than two rabbit to infect,
                # you are allowed to infect all the rabbits
                if max_infected < 2:
                    max_infected = alive_count
                # If, event with all the rabbits, there is less
                # than two rabbits to infect, cancel outbreak.
                if max_infected < 2:
                    return

                weights = []
                population = []
                for n in range(2, max_infected + 1):
                    population.append(n)
                    weight = 1 / (0.75 * n
                                  )  # Lower chance for more infected rabbits
                    weights.append(weight)
                infected_count = random.choices(
                    population, weights=weights)[0]  # the infected..

                infected_names = []
                involved_rabbits = []
                infected_rabbits = random.sample(alive_rabbits, infected_count)
                for sick_meowmeow in infected_rabbits:
                    infected_names.append(str(sick_meowmeow.name))
                    involved_rabbits.append(sick_meowmeow.ID)
                    sick_meowmeow.get_ill(
                        illness, event_triggered=True)  # SPREAD THE GERMS >:)

                illness_name = str(illness).capitalize()
                if illness == 'kittencough':
                    event = f'{illness_name} has spread around the nursery. ' \
                            f'{", ".join(infected_names[:-1])}, and ' \
                            f'{infected_names[-1]} have been infected.'
                elif illness == 'fleas':
                    event = f'Fleas have been hopping from pelt to pelt and now ' \
                            f'{", ".join(infected_names[:-1])}, ' \
                            f'and {infected_names[-1]} are all infested.'
                else:
                    event = f'{illness_name} has spread around the burrow. ' \
                            f'{", ".join(infected_names[:-1])}, and ' \
                            f'{infected_names[-1]} have been infected.'

                game.cur_events_list.append(
                    Single_Event(event, "health", involved_rabbits))
                # game.health_events_list.append(event)
                break

    def coming_out(self, rabbit):
        """turnin' the kittenties trans..."""
        if rabbit.genderalign == rabbit.gender:
            if rabbit.months < 6:
                return

            involved_rabbits = [rabbit.ID]
            if rabbit.age == 'adolescent':
                transing_chance = random.getrandbits(8)  # 2/256
            elif rabbit.age == 'young adult':
                transing_chance = random.getrandbits(9)  # 2/512
            else:
                # adult, senior adult, elder
                transing_chance = random.getrandbits(10)  # 2/1028

            if transing_chance:
                # transing_chance != 0, no trans kittenties today...    L
                return

            if random.getrandbits(1):  # 50/50
                if rabbit.gender == "male":
                    rabbit.genderalign = "trans doe"
                    # rabbit.pronouns = [rabbit.default_pronouns[1].copy()]
                else:
                    rabbit.genderalign = "trans buck"
                    # rabbit.pronouns = [rabbit.default_pronouns[2].copy()]
            else:
                rabbit.genderalign = "nonbinary"
                # rabbit.pronouns = [rabbit.default_pronouns[0].copy()]

            if rabbit.gender == 'male':
                gender = 'buck'
            else:
                gender = 'doe'
            text = f"{rabbit.name} has realized that {gender} doesn't describe how they feel anymore."
            game.cur_events_list.append(
                Single_Event(text, "misc", involved_rabbits))
            # game.misc_events_list.append(text)

    def check_and_promote_chief_rabbit(self):
        """ Checks if a new chief rabbit need to be promoted, and promotes them, if needed.  """
        # check for chief rabbit
        if game.warren.chief_rabbit:
            chief_rabbitinvalid = game.warren.chief_rabbit.dead or game.warren.chief_rabbit.outside
        else:
            chief_rabbitinvalid = True

        if chief_rabbitinvalid:
            self.perform_ceremonies(
                game.warren.chief_rabbit
            )  # This is where the captain will be make chief rabbit

            if game.warren.chief_rabbit:
                chief_rabbitdead = game.warren.chief_rabbit.dead
                chief_rabbitoutside = game.warren.chief_rabbit.outside
            else:
                chief_rabbitdead = True
                chief_rabbitoutside = True

            if chief_rabbitdead or chief_rabbitoutside:
                game.cur_events_list.insert(
                    0, Single_Event(f"{game.warren.name} has no chief rabbit!"))

    def check_and_promote_captain(self):
        """Checks if a new captain needs to be appointed, and appointed them if needed. """
        if (not game.warren.captain or game.warren.captain.dead
                or game.warren.captain.outside or game.warren.captain.status == "elder"):
            if game.warren.warren_settings.get('captain'):

                # This determines all the rabbits who are eligible to be captain.
                possible_deputies = list(
                    filter(
                        lambda x: not x.dead and not x.outside and x.status ==
                                  "rabbit" and (x.rusasi or x.former_rusasi),
                        Rabbit.all_rabbits_list))

                # If there are possible deputies, choose from that list.
                if possible_deputies:
                    random_rabbit = random.choice(possible_deputies)
                    involved_rabbits = [random_rabbit.ID]

                    # Gather captain and chief rabbit status, for determination of the text.
                    if game.warren.chief_rabbit:
                        if game.warren.chief_rabbit.dead or game.warren.chief_rabbit.outside:
                            chief_rabbitstatus = "not_here"
                        else:
                            chief_rabbitstatus = "here"
                    else:
                        chief_rabbitstatus = "not_here"

                    if game.warren.captain:
                        if game.warren.captain.dead or game.warren.captain.outside:
                            captain_status = "not_here"
                        else:
                            captain_status = "here"
                    else:
                        captain_status = "not_here"

                    if chief_rabbitstatus == "here" and captain_status == "not_here":

                        if random_rabbit.personality.trait == 'bloodthirsty':
                            text = f"{random_rabbit.name} has been chosen as the new captain. " \
                                   f"They look at the warren's chief rabbit with an odd glint in their eyes."
                            # No additional involved rabbits
                        else:
                            if game.warren.captain:
                                previous_captain_mention = random.choice([
                                    f"They know that {game.warren.captain.name} would approve.",
                                    f"They hope that {game.warren.captain.name} would approve.",
                                    f"They don't know if {game.warren.captain.name} would approve, "
                                    f"but life must go on. "
                                ])
                                involved_rabbits.append(game.warren.captain.ID)

                            else:
                                previous_captain_mention = ""

                            text = f"{game.warren.chief_rabbit.name} chooses " \
                                   f"{random_rabbit.name} to take over " \
                                   f"as captain. " + previous_captain_mention

                            involved_rabbits.append(game.warren.chief_rabbit.ID)
                    elif chief_rabbitstatus == "not_here" and captain_status == "here":
                        text = f"The warren is without a chief rabbit, but a " \
                               f"new captain must still be named.  " \
                               f"{random_rabbit.name} is chosen as the new captain. " \
                               f"The retired captain nods their approval."
                    elif chief_rabbitstatus == "not_here" and captain_status == "not_here":
                        text = f"Without a chief rabbit or captain, the warren has been directionless. " \
                               f"They all turn to {random_rabbit.name} with hope for the future."
                    elif chief_rabbitstatus == "here" and captain_status == "here":
                        possible_events = [
                            f"{random_rabbit.name} has been chosen as the new captain. "  # pylint: disable=line-too-long
                            f"The warren squeals their name in approval.",  # pylint: disable=line-too-long
                            f"{random_rabbit.name} has been chosen as the new captain. "  # pylint: disable=line-too-long
                            f"Some of the older warren members question the wisdom in this choice.",
                            # pylint: disable=line-too-long
                            f"{random_rabbit.name} has been chosen as the new captain. "  # pylint: disable=line-too-long
                            f"They hold their head up high and promise to do their best for the warren.",
                            # pylint: disable=line-too-long
                            f"{game.warren.chief_rabbit.name} has been thinking deeply all day who they would "  # pylint: disable=line-too-long
                            f"respect and trust enough to stand at their side, and at sunhigh makes the "  # pylint: disable=line-too-long
                            f"announcement that {random_rabbit.name} will be the warren's new captain.",
                            # pylint: disable=line-too-long
                            f"{random_rabbit.name} has been chosen as the new captain. They pray to "  # pylint: disable=line-too-long
                            f"Frith that they are the right choice for the warren.",  # pylint: disable=line-too-long
                            f"{random_rabbit.name} has been chosen as the new captain. Although"  # pylint: disable=line-too-long
                            f"they are nervous, they put on a brave front and look forward to serving"  # pylint: disable=line-too-long
                            f"the warren.",
                        ]
                        # No additional involved rabbits
                        text = random.choice(possible_events)
                    else:
                        # This should never happen. Failsafe.
                        text = f"{random_rabbit.name} becomes captain. "
                else:
                    # If there are no possible deputies, choose someone else, with special text.
                    all_rabbits = list(
                        filter(
                            lambda x: not x.dead and not x.outside and x.status
                                      == "rabbit", Rabbit.all_rabbits_list))
                    if all_rabbits:
                        random_rabbit = random.choice(all_rabbits)
                        involved_rabbits = [random_rabbit.ID]
                        text = f"No rabbit is truly fit to be captain, " \
                               f"but the position can't remain vacant. " \
                               f"{random_rabbit.name} is appointed as the new captain. "

                    else:
                        # Is there are no rabbits at all, no one is named captain.
                        game.cur_events_list.append(
                            Single_Event(
                                "There are no rabbits fit to become captain. ",
                                "ceremony"))
                        return

                random_rabbit.status_change("captain")
                game.warren.captain = random_rabbit

                game.cur_events_list.append(
                    Single_Event(text, "ceremony", involved_rabbits))

            else:
                game.cur_events_list.insert(
                    0, Single_Event(f"{game.warren.name}warren has no captain!"))

events_class = Events()
