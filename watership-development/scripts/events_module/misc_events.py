import random

from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit.history import History
from scripts.rabbit.pelts import Pelt
from scripts.events_module.generate_events import GenerateEvents
from scripts.utility import event_text_adjust, change_warren_relations, change_relationship_values
from scripts.game_structure.game_essentials import game
from scripts.event_class import Single_Event

# ---------------------------------------------------------------------------- #
#                               Death Event Class                              #
# ---------------------------------------------------------------------------- #

class MiscEvents():
    """All events that do not fit in a different rabbitegory."""

    @staticmethod
    def handle_misc_events(rabbit, other_rabbit=None, war=False, enemy_warren=None, alive_kits=False, accessory=False, ceremony=False):
        """ 
        This function handles the misc events
        """
        involved_rabbits = [rabbit.ID]
        if war:
            other_warren = enemy_warren
        else:
            other_warren = random.choice(game.warren.all_warrens)
        
        other_warren_name = None
        if other_warren:
            other_warren_name = f'{other_warren.name}'

        possible_events = GenerateEvents.possible_short_events(rabbit.status, rabbit.age, "misc_events")
        acc_checked_events = []
        for event in possible_events:
            if (ceremony and "ceremony" not in event.tags) or (not ceremony and "ceremony" in event.tags):
                continue

            if (not accessory and event.accessories) or (accessory and not event.accessories):
                continue

            if "other_rabbit" in event.tags and not other_rabbit:
                other_rabbit = Rabbit.fetch_rabbit(random.choice(Rabbit.all_rabbits_list))
                if other_rabbit.dead or other_rabbit.outside:
                    other_rabbit = None

            acc_checked_events.append(event)
            
        reveal = False
        victim = None
        rabbit_history = History.get_murders(rabbit)
        if rabbit_history:
            if "is_murderer" in rabbit_history:
                murder_history = rabbit_history["is_murderer"]
                for murder in murder_history:
                    murder_index = murder_history.index(murder)
                    if murder_history[murder_index]["revealed"] is True:
                        continue
                    victim = murder_history[murder_index]["victim"]
                    reveal = True
                    break

        #print('misc event', rabbit.ID)
        final_events = GenerateEvents.filter_possible_short_events(acc_checked_events, rabbit, other_rabbit, war, enemy_warren, other_warren,
                                                                   alive_kits, murder_reveal=reveal)

        # ---------------------------------------------------------------------------- #
        #                                    event                                     #
        # ---------------------------------------------------------------------------- #
        try:
            misc_event = random.choice(final_events)
        except:
            print('ERROR: no misc events available for this rabbit')
            return

        if misc_event.accessories:
            MiscEvents.handle_accessories(rabbit, misc_event.accessories)

        # let's change some relationship values \o/ check if another rabbit is mentioned and if they live
        if "other_rabbit" in misc_event.tags:
            involved_rabbits.append(other_rabbit.ID)
            MiscEvents.handle_relationship_changes(rabbit, misc_event, other_rabbit)
        else:
            other_rabbit = None

        if "rel_down" in misc_event.tags:
            difference = -1
            change_warren_relations(other_warren, difference=difference)

        elif "rel_up" in misc_event.tags:
            difference = 1
            change_warren_relations(other_warren, difference=difference)

        event_text = event_text_adjust(Rabbit, misc_event.event_text, rabbit, other_rabbit, other_warren_name, murder_reveal=reveal, victim=victim)

        types = ["misc"]
        if "other_warren" in misc_event.tags:
            types.append("other_warrens")
        if ceremony:
            types.append("ceremony")
        game.cur_events_list.append(Single_Event(event_text, types, involved_rabbits))

        if reveal:
            History.reveal_murder(rabbit, other_rabbit, Rabbit, victim, murder_index)

    @staticmethod
    def handle_relationship_changes(rabbit, misc_event, other_rabbit):

        n = 5
        romantic = 0
        platonic = 0
        dislike = 0
        admiration = 0
        comfortable = 0
        jealousy = 0
        trust = 0
        if "rc_to_mc" in misc_event.tags:
            rabbit_to = [rabbit.ID]
            rabbit_from = [other_rabbit]
        elif "mc_to_rc" in misc_event.tags:
            rabbit_to = [other_rabbit.ID]
            rabbit_from = [rabbit]
        elif "to_both" in misc_event.tags:
            rabbit_to = [rabbit.ID, other_rabbit.ID]
            rabbit_from = [other_rabbit, rabbit]
        else:
            return
        if "romantic" in misc_event.tags:
            romantic = n
        elif "neg_romantic" in misc_event.tags:
            romantic = -n
        if "platonic" in misc_event.tags:
            platonic = n
        elif "neg_platonic" in misc_event.tags:
            platonic = -n
        if "dislike" in misc_event.tags:
            dislike = n
        elif "neg_dislike" in misc_event.tags:
            dislike = -n
        if "respect" in misc_event.tags:
            admiration = n
        elif "neg_respect" in misc_event.tags:
            admiration = -n
        if "comfort" in misc_event.tags:
            comfortable = n
        elif "neg_comfort" in misc_event.tags:
            comfortable = -n
        if "jealousy" in misc_event.tags:
            jealousy = n
        elif "neg_jealousy" in misc_event.tags:
            jealousy = -n
        if "trust" in misc_event.tags:
            trust = n
        elif "neg_trust" in misc_event.tags:
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
    def handle_accessories(rabbit, possible_accs):
        acc_list = []
        if "WILD" in possible_accs:
            acc_list.extend(Pelt.wild_accessories)
        if "PLANT" in possible_accs:
            acc_list.extend(Pelt.plant_accessories)
        if "COLLAR" in possible_accs:
            acc_list.extend(Pelt.collars)

        for acc in possible_accs:
            if acc not in ["WILD", "PLANT", "COLLAR"]:
                acc_list.append(acc)

        if "NOTAIL" in rabbit.pelt.scars or "HALFTAIL" in rabbit.pelt.scars:
            for acc in Pelt.tail_accessories:
                try:
                    acc_list.remove(acc)
                except ValueError:
                    print(f'attempted to remove {acc} from possible acc list, but it was not in the list!')


        rabbit.pelt.accessory = random.choice(acc_list)

    @staticmethod
    def handle_murder_self_reveals(rabbit):
        ''' Handles reveals for murders where the murderer reveals themself '''
        if rabbit.personality.lawfulness > 8:
            murderer_guilty = random.choice([True, False])
        chance_of_reveal = 120
        if murderer_guilty:
            chance_of_reveal = chance_of_reveal - 100

        # testing purposes
        chance_of_reveal = 1

        chance_roll = random.randint(0, chance_of_reveal)
        print(chance_roll)

        return bool(chance_roll = 1)

    @staticmethod
    def handle_murder_witness_reveals(rabbit, other_rabbit):
        ''' Handles reveals where the witness reveals the murderer '''