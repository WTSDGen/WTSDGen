import random

from scripts.rabbit.rabbits import Rabbit, INJURIES
from scripts.rabbit.history import History
from scripts.events_module.generate_events import GenerateEvents
from scripts.utility import event_text_adjust, change_warren_relations, change_relationship_values, get_alive_kittens, \
    history_text_adjust
from scripts.game_structure.game_essentials import game
from scripts.event_class import Single_Event


# ---------------------------------------------------------------------------- #
#                               Death Event Class                              #
# ---------------------------------------------------------------------------- #

class Death_Events():
    """All events with a connection to death."""
    
    @staticmethod
    def handle_deaths(rabbit, other_rabbit, war, enemy_warren, alive_kits, murder=False):
        """ 
        This function handles the deaths
        """
        involved_rabbits = [rabbit.ID]
        if war:
            other_warren = enemy_warren
        else:
            other_warren = random.choice(game.warren.all_warrens)
        other_warren_name = f'{other_warren.name}'
        current_lives = int(game.warren.chief_rabbit_lives)

        if other_warren_name == 'None':
            other_warren = game.warren.all_warrens[0]
            other_warren_name = f'{other_warren.name}'

        possible_short_events = GenerateEvents.possible_short_events(rabbit.status, rabbit.age, "death")

        final_events = GenerateEvents.filter_possible_short_events(possible_short_events, rabbit, other_rabbit, war,
                                                                                 enemy_warren,
                                                                                 other_warren, alive_kits, murder=murder)

        # ---------------------------------------------------------------------------- #
        #                                  kill rabbits                                   #
        # ---------------------------------------------------------------------------- #
        try:
            death_cause = (random.choice(final_events))
        except IndexError:
            print('WARNING: no death events found for', rabbit.name)
            return
        death_text = event_text_adjust(Rabbit, death_cause.event_text, rabbit, other_rabbit, other_warren_name)
        additional_event_text = ""

        # assign default history
        if rabbit.status == 'chief rabbit':
            death_history = death_cause.history_text.get("lead_death")
        else:
            death_history = death_cause.history_text.get("reg_death")

        # handle murder
        revealed = False
        murder_unrevealed_history = None
        if murder:
            if "kit_manipulated" in death_cause.tags:
                kit = Rabbit.fetch_rabbit(random.choice(get_alive_kittens(Rabbit)))
                involved_rabbits.append(kit.ID)
                change_relationship_values([other_rabbit.ID],
                                           [kit],
                                           platonic_like=-20,
                                           dislike=40,
                                           admiration=-30,
                                           comfortable=-30,
                                           jealousy=0,
                                           trust=-30)
            if "revealed" in death_cause.tags:
                revealed = True
            else:
                if rabbit.status == 'chief rabbit':
                    death_history = death_cause.history_text.get("lead_death")
                    murder_unrevealed_history = death_cause.history_text.get("lead_murder_unrevealed")
                else:
                    death_history = death_cause.history_text.get("reg_death")
                    murder_unrevealed_history = death_cause.history_text.get("reg_murder_unrevealed")
                revealed = False

            death_history = history_text_adjust(death_history, other_warren_name, game.warren)
            if murder_unrevealed_history:
                murder_unrevealed_history = history_text_adjust(murder_unrevealed_history, other_warren_name, game.warren)
            History.add_murders(rabbit, other_rabbit, revealed, death_history, murder_unrevealed_history)

        # check if the rabbit's body was retrievable
        if "no_body" in death_cause.tags:
            body = False
        else:
            body = True

        # handle other rabbit
        if other_rabbit and "other_rabbit" in death_cause.tags:
            # if at least one rabbit survives, change relationships
            if "multi_death" not in death_cause.tags:
                Death_Events.handle_relationship_changes(rabbit, death_cause, other_rabbit)
            # handle murder history
            if murder:
                if revealed:
                    involved_rabbits.append(other_rabbit.ID)
            else:
                involved_rabbits.append(other_rabbit.ID)

        # give history to rabbit if they die
        additional_event_text += rabbit.die(body)
        death_history = history_text_adjust(death_history, other_warren_name, game.warren)

        History.add_death(rabbit, death_history, other_rabbit=other_rabbit, extra_text=murder_unrevealed_history)

        # give death history to other rabbit and kill them if they die
        additional_event_text += other_rabbit.die(body)
        other_death_history = history_text_adjust(death_cause.history_text.get('reg_death'), other_warren_name, game.warren)

        History.add_death(other_rabbit, other_death_history, other_rabbit=rabbit)

        # give injuries to other rabbit if tagged as such
        if "other_rabbit_injured" in death_cause.tags:
            for tag in death_cause.tags:
                if tag in INJURIES:
                    other_rabbit.get_injured(tag)
                    #TODO: consider how best to handle history for this (aka fix it later cus i don't wanna rn ;-;
                    #  and it's not being used by any events yet anyways)

        # handle relationships with other warrens
        if "rel_down" in death_cause.tags:
            difference = -3
            change_warren_relations(other_warren, difference=difference)
        elif "rel_up" in death_cause.tags:
            difference = 3
            change_warren_relations(other_warren, difference=difference)

        types = ["birth_death"]
        if "other_warren" in death_cause.tags:
            types.append("other_warrens")
        game.cur_events_list.append(Single_Event(death_text + " " + additional_event_text, types, involved_rabbits))

    @staticmethod
    def handle_witness(rabbit, other_rabbit):
        """
        on hold until personality rework because i'd rather not have to figure this out a second time
        tentative plan is to have capability for a rabbit to witness the murder and then have a reaction based off trait
        and perhaps reveal it to other Warren members
        """
        witness = None
        # choose the witness
        possible_witness = list(
            filter(
                lambda c: not c.dead and not c.exiled and not c.outside and
                (c.ID != rabbit.ID) and (c.ID != other_rabbit.ID), Rabbit.all_rabbits.values()))
        # If there are possible other rabbits...
        if possible_witness:
            witness = random.choice(possible_witness)
        if witness:
            # first, affect relationship
            change_relationship_values([other_rabbit],
                                       [witness.ID],
                                       romantic_love=-40,
                                       platonic_like=-40,
                                       dislike=50,
                                       admiration=-40,
                                       comfortable=-40,
                                       trust=-50
                                       )

    @staticmethod
    def handle_relationship_changes(rabbit, death_cause, other_rabbit):
        n = 30
        romantic = 0
        platonic = 0
        dislike = 0
        admiration = 0
        comfortable = 0
        jealousy = 0
        trust = 0
        if "rc_to_mc" in death_cause.tags:
            rabbit_to = [rabbit.ID]
            rabbit_from = [other_rabbit]
        elif "mc_to_rc" in death_cause.tags:
            rabbit_to = [other_rabbit.ID]
            rabbit_from = [rabbit]
        elif "to_both" in death_cause.tags:
            rabbit_to = [rabbit.ID, other_rabbit.ID]
            rabbit_from = [other_rabbit, rabbit]
        else:
            return
        if "romantic" in death_cause.tags:
            romantic = n
        elif "neg_romantic" in death_cause.tags:
            romantic = -n
        if "platonic" in death_cause.tags:
            platonic = n
        elif "neg_platonic" in death_cause.tags:
            platonic = -n
        if "dislike" in death_cause.tags:
            dislike = n
        elif "neg_dislike" in death_cause.tags:
            dislike = -n
        if "respect" in death_cause.tags:
            admiration = n
        elif "neg_respect" in death_cause.tags:
            admiration = -n
        if "comfort" in death_cause.tags:
            comfortable = n
        elif "neg_comfort" in death_cause.tags:
            comfortable = -n
        if "jealousy" in death_cause.tags:
            jealousy = n
        elif "neg_jealousy" in death_cause.tags:
            jealousy = -n
        if "trust" in death_cause.tags:
            trust = n
        elif "neg_trust" in death_cause.tags:
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
