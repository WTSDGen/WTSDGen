import itertools
import random
from random import choice, randint
import os
import ujson

from scripts.game_structure.game_essentials import game
from scripts.events_module.condition_events import Condition_Events
from scripts.rabbit.rabbits import Rabbit
from scripts.utility import get_rabbits_same_age, get_rabbits_of_romantic_interest, get_free_possible_mates
from scripts.event_class import Single_Event
from scripts.rabbit_relations.relationship import Relationship
from scripts.events_module.relationship.romantic_events import Romantic_Events
from scripts.events_module.relationship.welcoming_events import Welcoming_Events
from scripts.events_module.relationship.group_events import Group_Events

class Relation_Events():
    """All relationship events."""
    had_one_event = False
    rabbits_triggered_events = {}

    base_path = os.path.join(
        "resources",
        "dicts",
        "relationship_events"
    )

    GROUP_TYPES = {}
    types_path = os.path.join(base_path,"group_interactions" ,"group_types.json")
    with open(types_path, 'r') as read_file:
        GROUP_TYPES = ujson.load(read_file)       
    del base_path

    @staticmethod
    def handle_relationships(rabbit: Rabbit):
        """Checks the relationships of the rabbit and trigger additional events if possible.

            Parameters
            ----------
            rabbit : Rabbit
                the rabbit where the relationships should be checked

            Returns
            -------
        """
        if not rabbit.relationships:
            return
        Relation_Events.had_one_event = False

        # currently try to trigger every month, because there are not many group events
        # TODO: maybe change in future
        Relation_Events.group_events(rabbit)

        Relation_Events.same_age_events(rabbit)

        # 1/16 for an additional event
        if not random.getrandbits(4):
            Relation_Events.romantic_events(rabbit)
            
        Romantic_Events.handle_mating_and_breakup(rabbit)

        
    # ---------------------------------------------------------------------------- #
    #                                new event types                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def romantic_events(rabbit):
        """
            ONLY for rabbit OLDER than 12 months.
            To increase mating chance this function is used.
            It will boost the romantic values of either mate or possible mates.
            This also increase the chance of affairs.
        """
        if rabbit.months < 12:
            return

        if not Relation_Events.can_trigger_events(rabbit):
            return

        other_rabbit = None

        # get the rabbits which are relevant for romantic interactions
        free_possible_mates = get_free_possible_mates(rabbit)
        other_love_interest = get_rabbits_of_romantic_interest(rabbit)  
        possible_rabbits = free_possible_mates
        if len(other_love_interest) > 0 and len(other_love_interest) < 3:
            possible_rabbits.extend(other_love_interest)
            possible_rabbits.extend(other_love_interest)
        elif len(other_love_interest) >= 3:
            possible_rabbits = other_love_interest

        # only adding rabbits which already have SOME relationship with each other
        rabbit_to_choose_from = []
        for inter_rabbit in possible_rabbits:
            if inter_rabbit.ID not in rabbit.relationships:
                rabbit.create_one_relationship(inter_rabbit)
            if rabbit.ID not in inter_rabbit.relationships:
                inter_rabbit.create_one_relationship(rabbit)

            rabbit_to_inter = rabbit.relationships[inter_rabbit.ID].platonic_like > 10 or\
                rabbit.relationships[inter_rabbit.ID].comfortable > 10
            inter_to_rabbit = inter_rabbit.relationships[rabbit.ID].platonic_like > 10 or\
                inter_rabbit.relationships[rabbit.ID].comfortable > 10
            if rabbit_to_inter and inter_to_rabbit:
                rabbit_to_choose_from.append(inter_rabbit)

        # if the rabbit has one or more mates, check how high the chance is, 
        # that the rabbit interacts romantic with ANOTHER rabbit than their mate
        use_mate = False
        if rabbit.mate:
            chance_number = game.config["relationship"]["chance_romantic_not_mate"]
             
            # the more mates the rabbit has, the less likely it will be that they interact with another rabbit romantically
            for mate_id in rabbit.mate:
                chance_number -= int(rabbit.relationships[mate_id].romantic_love / 20)
            use_mate = int(random.random() * chance_number)  
            
        # If use_mate is falsey, or if the rabbit has been marked as "no_mates", only allow romantic 
        # relations with current mates
        if use_mate or rabbit.no_mates:
            rabbit_to_choose_from = [rabbit.all_rabbits[mate_id] for mate_id in rabbit.mate if\
                                    not rabbit.all_rabbits[mate_id].dead and not rabbit.all_rabbits[mate_id].outside]

        if not rabbit_to_choose_from:
            return
            
        other_rabbit = choice(rabbit_to_choose_from)
        if Romantic_Events.start_interaction(rabbit, other_rabbit):
            Relation_Events.trigger_event(rabbit)
            Relation_Events.trigger_event(other_rabbit)

    @staticmethod
    def same_age_events(rabbit):
        """	
            To increase the relationship amounts with rabbits of the same age. 
            This should lead to 'friends', 'enemies' and possible mates around the same age group.
        """
        if not Relation_Events.can_trigger_events(rabbit):
            return

        same_age_rabbits = get_rabbits_same_age(rabbit, game.config["mates"]["age_range"])
        if len(same_age_rabbits) > 0:
            random_rabbit = choice(same_age_rabbits)
            if Relation_Events.can_trigger_events(random_rabbit) and random_rabbit.ID in rabbit.relationships:
                rabbit.relationships[random_rabbit.ID].start_interaction()
                Relation_Events.trigger_event(rabbit)
                Relation_Events.trigger_event(random_rabbit)

    @staticmethod
    def group_events(rabbit):
        """
            This function triggers group events, based on the given rabbit. 
            First it will be decided if a special type of group (found in relationship_events/group_interactions/group_types.json).
            As default all rabbits will be a possible 'group' of interaction.
        """
        if not Relation_Events.can_trigger_events(rabbit):
            return

        chosen_type = "all"
        if len(Relation_Events.GROUP_TYPES) > 0 and randint(0,game.config["relationship"]["chance_of_special_group"]):
            types_to_choose = []
            for group, value in Relation_Events.GROUP_TYPES.items():
                types_to_choose.extend([group] * value["frequency"])
                chosen_type = choice(list(Relation_Events.GROUP_TYPES.keys()))

        if rabbit.status == "leader":
            chosen_type = "all"
        possible_interaction_rabbits = list(
            filter(
                lambda rabbit:
                (not rabbit.dead and not rabbit.outside and not rabbit.exiled),
                Rabbit.all_rabbits.values())
        )
        if rabbit in possible_interaction_rabbits:
            possible_interaction_rabbits.remove(rabbit)

        if chosen_type != "all":
            possible_interaction_rabbits = Relation_Events.rabbits_with_relationship_constraints(rabbit,
                                                                                           Relation_Events.GROUP_TYPES[chosen_type]["constraint"])

        interacted_rabbit_ids = Group_Events.start_interaction(rabbit, possible_interaction_rabbits)
        for id in interacted_rabbit_ids:
            inter_rabbit = Rabbit.all_rabbits[id]
            Relation_Events.trigger_event(inter_rabbit)

    @staticmethod
    def family_events(rabbit):
        """
            To have more family related events.
        """
        print("TODO")

    @staticmethod
    def outsider_events(rabbit):
        """
            ONLY for rabbit OLDER than 6 months and not major injured.
            This function will handle when the rabbit interacts with rabbit which are outside of the warren.
        """
        print("TODO")

    @staticmethod
    def welcome_new_rabbits(new_rabbits = None):
        """This function will handle the welcome of new rabbits, if there are new rabbits in the warren."""
        if new_rabbits is None or len(new_rabbits) <= 0:
            return

        for new_rabbit in new_rabbits:
            same_age_rabbits = get_rabbits_same_age(new_rabbit)
            alive_rabbits = [i for i in new_rabbit.all_rabbits.values() if not i.dead and not i.outside]
            number = game.config["new_rabbit"]["rabbit_amount_welcoming"]

            if len(alive_rabbits) == 0:
                return
            elif len(same_age_rabbits) < number and len(same_age_rabbits) > 0:
                for age_rabbit in same_age_rabbits:
                    Welcoming_Events.welcome_rabbit(age_rabbit, new_rabbit)
                
                rest_number = number - len(same_age_rabbits)
                same_age_ids = [c.ID for c in same_age_rabbits]
                alive_rabbits = [alive_rabbit for alive_rabbit in alive_rabbits if alive_rabbit.ID not in same_age_ids]
                
                chosen_rest = random.choices(population=alive_rabbits, k=len(alive_rabbits))
                if rest_number >= len(alive_rabbits):
                    chosen_rest = random.choices(population=alive_rabbits, k=rest_number)
                for inter_rabbit in chosen_rest:
                    Welcoming_Events.welcome_rabbit(inter_rabbit, new_rabbit)
            elif len(same_age_rabbits) >= number:
                chosen = random.choices(population=same_age_rabbits, k=number)
                for chosen_rabbit in chosen:
                    Welcoming_Events.welcome_rabbit(chosen_rabbit, new_rabbit)
            elif len(alive_rabbits) <= number:
                for alive_rabbit in alive_rabbits:
                    Welcoming_Events.welcome_rabbit(alive_rabbit, new_rabbit)
            else:
                chosen = random.choices(population=alive_rabbits, k=number)
                for chosen_rabbit in chosen:
                    Welcoming_Events.welcome_rabbit(chosen_rabbit, new_rabbit)

    # ---------------------------------------------------------------------------- #
    #                                helper function                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def rabbits_with_relationship_constraints(main_rabbit, constraint):
        """Returns a list of rabbits, where the relationship from main_rabbit towards the rabbit fulfill the given constraints."""
        rabbit_list = list(
            filter(
                lambda rabbit:
                (not rabbit.dead and not rabbit.outside and not rabbit.exiled),
                Rabbit.all_rabbits.values())
        )
        rabbit_list.remove(main_rabbit)
        filtered_rabbit_list = []
        
        for inter_rabbit in rabbit_list:
            rabbit_from = main_rabbit
            rabbit_to = inter_rabbit

            if inter_rabbit.ID == main_rabbit.ID:
                continue
            if rabbit_to.ID not in rabbit_from.relationships:
                rabbit_from.create_one_relationship(rabbit_to)
                if rabbit_from.ID not in rabbit_to.relationships:
                    rabbit_to.create_one_relationship(rabbit_from)
                continue

            relationship = rabbit_from.relationships[rabbit_to.ID]

            if "siblings" in constraint and not rabbit_from.is_sibling(rabbit_to):
                continue

            if "mates" in constraint and not relationship.mates:
                continue

            if "not_mates" in constraint and relationship.mates:
                continue

            if "parent/child" in constraint and not rabbit_from.is_parent(rabbit_to):
                continue

            if "child/parent" in constraint and not rabbit_to.is_parent(rabbit_from):
                continue

            value_types = ["romantic", "platonic", "dislike", "admiration", "comfortable", "jealousy", "trust"]
            fulfilled = True
            for v_type in value_types:
                tags = [i for i in constraint if v_type in i]
                if len(tags) < 1:
                    continue
                threshold = 0
                lower_than = False
                # try to extract the value/threshold from the text
                try:
                    splitted = tags[0].split('_')
                    threshold = int(splitted[1])
                    if len(splitted) > 3:
                        lower_than = True
                except:
                    print(f"ERROR: while creating a rabbit group, the relationship constraint for the value {v_type} follows not the formatting guidelines.")
                    break

                if threshold > 100:
                    print(f"ERROR: while creating a rabbit group, the relationship constraints for the value {v_type}, which is higher than the max value of a relationship.")
                    break

                if threshold <= 0:
                    print(f"ERROR: while creating a rabbit group, the relationship constraints for the value {v_type}, which is lower than the min value of a relationship or 0.")
                    break

                threshold_fulfilled = False
                if v_type == "romantic":
                    if not lower_than and relationship.romantic_love >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.romantic_love <= threshold:
                        threshold_fulfilled = True
                if v_type == "platonic":
                    if not lower_than and relationship.platonic_like >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.platonic_like <= threshold:
                        threshold_fulfilled = True
                if v_type == "dislike":
                    if not lower_than and relationship.dislike >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.dislike <= threshold:
                        threshold_fulfilled = True
                if v_type == "comfortable":
                    if not lower_than and relationship.comfortable >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.comfortable <= threshold:
                        threshold_fulfilled = True
                if v_type == "jealousy":
                    if not lower_than and relationship.jealousy >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.jealousy <= threshold:
                        threshold_fulfilled = True
                if v_type == "trust":
                    if not lower_than and relationship.trust >= threshold:
                        threshold_fulfilled = True
                    elif lower_than and relationship.trust <= threshold:
                        threshold_fulfilled = True

                if not threshold_fulfilled:
                    fulfilled = False
                    continue

            if not fulfilled:
                continue

            filtered_rabbit_list.append(inter_rabbit)
        return filtered_rabbit_list

    @staticmethod
    def trigger_event(rabbit):
        if rabbit.ID in Relation_Events.rabbits_triggered_events:
            Relation_Events.rabbits_triggered_events[rabbit.ID] += 1
        else:
            Relation_Events.rabbits_triggered_events[rabbit.ID] = 1

    @staticmethod
    def can_trigger_events(rabbit):
        """Returns if the given rabbit can still trigger events."""
        special_status = ["leader", "deputy", "medicine rabbit", "owsla"]
        
        # set the threshold correctly
        threshold = game.config["relationship"]["max_interaction"]
        if rabbit.status in special_status:
            threshold = game.config["relationship"]["max_interaction_special"]
        
        if rabbit.ID not in Relation_Events.rabbits_triggered_events:
            return True

        return Relation_Events.rabbits_triggered_events[rabbit.ID] < threshold
 
    @staticmethod
    def clear_trigger_dict():
        """Cleans the trigger dictionary, this function should be called every new month."""
        Relation_Events.rabbits_triggered_events = {}


# ---------------------------------------------------------------------------- #
#                                load resources                                #
# ---------------------------------------------------------------------------- #

