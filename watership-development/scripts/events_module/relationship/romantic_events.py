
from copy import deepcopy
from random import choice
import random

import ujson

from scripts.rabbit.history import History
from scripts.utility import (
    get_highest_romantic_relation,
    event_text_adjust,
    get_personality_compatibility,
    process_text

)
from scripts.game_structure.game_essentials import game
from scripts.event_class import Single_Event
from scripts.rabbit.rabbits import Rabbit
from scripts.rabbit_relations.relationship import (
    INTERACTION_MASTER_DICT,
    rel_fulfill_rel_constraints,
    rabbits_fulfill_single_interaction_constraints
)


class Romantic_Events():
    """All events which are related to mate's such as becoming mates and breakups, but also for possible mates and romantic interactions."""

    # ---------------------------------------------------------------------------- #
    #                                LOAD RESOURCES                                #
    # ---------------------------------------------------------------------------- #

    resource_directory = "resources/dicts/relationship_events/"

    MATE_DICTS = None
    with open(f"{resource_directory}become_mates.json", 'r') as read_file:
        MATE_DICTS = ujson.loads(read_file.read())

    POLY_MATE_DICTS = None
    with open(f"{resource_directory}become_mates_poly.json", 'r') as read_file:
        POLY_MATE_DICTS = ujson.loads(read_file.read())

    # ---------------------------------------------------------------------------- #
    #            build up dictionaries which can be used for month events           #
    #         because there may be less romantic/mate relevant interactions,       #
    #        the dictionary will be ordered in only 'positive' and 'negative'      #
    # ---------------------------------------------------------------------------- #

    # ---------------------------------------------------------------------------- #
    #                                     MATE                                     #
    # ---------------------------------------------------------------------------- #

    # Use the overall master interaction dictionary and filter for mate tag
    MATE_RELEVANT_INTERACTIONS = {}
    for val_type, dictionary in INTERACTION_MASTER_DICT.items():
        MATE_RELEVANT_INTERACTIONS[val_type] = {}
        MATE_RELEVANT_INTERACTIONS[val_type]["increase"] = list(
            filter(lambda inter: "mates" in inter.relationship_constraint and "not_mates" not in inter.relationship_constraint,
                dictionary["increase"]
            )
        )
        MATE_RELEVANT_INTERACTIONS[val_type]["decrease"] = list(
            filter(lambda inter: "mates" in inter.relationship_constraint and "not_mates" not in inter.relationship_constraint,
                dictionary["decrease"]
            )
        )

    # resort the first generated overview dictionary to only "positive" and "negative" interactions
    MATE_INTERACTIONS = {
        "positive": [],
        "negative": []
    }
    for val_type, dictionary in MATE_RELEVANT_INTERACTIONS.items():
        if val_type in ["jealousy", "dislike"]:
            MATE_INTERACTIONS["positive"].extend(dictionary["decrease"])
            MATE_INTERACTIONS["negative"].extend(dictionary["increase"])
        else:
            MATE_INTERACTIONS["positive"].extend(dictionary["increase"])
            MATE_INTERACTIONS["negative"].extend(dictionary["decrease"])

    # ---------------------------------------------------------------------------- #
    #                                   ROMANTIC                                   #
    # ---------------------------------------------------------------------------- #

    # Use the overall master interaction dictionary and filter for any interactions, which requires a certain amount of romantic
    ROMANTIC_RELEVANT_INTERACTIONS = {}
    for val_type, dictionary in INTERACTION_MASTER_DICT.items():
        ROMANTIC_RELEVANT_INTERACTIONS[val_type] = {}

        # if it's the romantic interaction type add all interactions
        if val_type == "romantic":
            ROMANTIC_RELEVANT_INTERACTIONS[val_type]["increase"] = dictionary["increase"]
            ROMANTIC_RELEVANT_INTERACTIONS[val_type]["decrease"] = dictionary["decrease"]
        else:
            increase = []
            for interaction in dictionary["increase"]:
                romantic = ["romantic" in tag for tag in interaction.relationship_constraint]
                if any(romantic):
                    increase.append(interaction)
            ROMANTIC_RELEVANT_INTERACTIONS[val_type]["increase"] = increase

            decrease = []
            for interaction in dictionary["decrease"]:
                romantic = ["romantic" in tag for tag in interaction.relationship_constraint]
                if any(romantic):
                    decrease.append(interaction)
            ROMANTIC_RELEVANT_INTERACTIONS[val_type]["decrease"] = decrease

    # resort the first generated overview dictionary to only "positive" and "negative" interactions
    ROMANTIC_INTERACTIONS = {
        "positive": [],
        "negative": []
    }
    for val_type, dictionary in ROMANTIC_RELEVANT_INTERACTIONS.items():
        if val_type in ["jealousy", "dislike"]:
            ROMANTIC_INTERACTIONS["positive"].extend(dictionary["decrease"])
            ROMANTIC_INTERACTIONS["negative"].extend(dictionary["increase"])
        else:
            ROMANTIC_INTERACTIONS["positive"].extend(dictionary["increase"])
            ROMANTIC_INTERACTIONS["negative"].extend(dictionary["decrease"])


    @staticmethod
    def start_interaction(rabbit_from, rabbit_to):
        """
            Filters and triggers events which are connected to romance between these two rabbits.
            
            Returns
            -------
            bool : if an event is triggered or not
        """
        if rabbit_from.ID == rabbit_to.ID:
            return False

        relevant_dict = deepcopy(Romantic_Events.ROMANTIC_INTERACTIONS)
        if rabbit_to.ID in rabbit_from.mate and not rabbit_to.dead:
            relevant_dict = deepcopy(Romantic_Events.MATE_INTERACTIONS)

        # check if it should be a positive or negative interaction
        relationship = rabbit_from.relationships[rabbit_to.ID]
        positive = Romantic_Events.check_if_positive_interaction(relationship)

        # get the possible interaction list and filter them
        possible_interactions = relevant_dict["positive"] if positive else relevant_dict["negative"]
        filtered_interactions = []
        _season = [str(game.warren.current_season).casefold(), "Any", "any"]
        _biome = [str(game.warren.biome).casefold(), "Any", "any"]
        for interaction in possible_interactions:
            in_tags = [i for i in interaction.biome if i not in _biome]
            if len(in_tags) > 0:
                continue

            in_tags = [i for i in interaction.season if i not in _season]
            if len(in_tags) > 0:
                continue

            rel_fulfilled = rel_fulfill_rel_constraints(relationship, interaction.relationship_constraint, interaction.id)
            if not rel_fulfilled:
                continue

            rabbit_fulfill = rabbits_fulfill_single_interaction_constraints(rabbit_from, rabbit_to, interaction, game.warren.game_mode)
            if not rabbit_fulfill:
                continue

            filtered_interactions.append(interaction)

        if len(filtered_interactions) < 1:
            print(f"There were no romantic interactions for: {rabbit_from.name} to {rabbit_to.name}")
            return False
        
        # chose interaction
        chosen_interaction = choice(filtered_interactions)
        # check if the current interaction id is already used and us another if so
        chosen_interaction = choice(possible_interactions)
        while chosen_interaction.id in relationship.used_interaction_ids\
            and len(possible_interactions) > 2:
            possible_interactions.remove(chosen_interaction)
            chosen_interaction = choice(possible_interactions)

        # if the chosen_interaction is still in the TRIGGERED_SINGLE_INTERACTIONS, clean the list
        if chosen_interaction in relationship.used_interaction_ids:
            relationship.used_interaction_ids = []
        relationship.used_interaction_ids.append(chosen_interaction.id)

        # affect relationship - it should always be in a romantic way
        in_de_crease = "increase" if positive else "decrease"
        rel_type = "romantic"
        relationship.chosen_interaction = chosen_interaction
        relationship.interaction_affect_relationships(in_de_crease, chosen_interaction.intensity, rel_type)

        # give rabbits injuries if the game mode is not classic
        if len(chosen_interaction.get_injuries) > 0 and game.warren.game_mode != 'classic':
            for abbreviations, injury_dict in chosen_interaction.get_injuries.items():
                if "injury_names" not in injury_dict:
                    print(f"ERROR: there are no injury names in the chosen interaction {chosen_interaction.id}.")
                    continue

                injured_rabbit = rabbit_from
                if abbreviations != "m_c":
                    injured_rabbit = rabbit_to
                
                injuries = []
                for inj in injury_dict["injury_names"]:
                    injured_rabbit.get_injured(inj, True)
                    injuries.append(inj)

                possible_scar = injury_dict["scar_text"] if "scar_text" in injury_dict else None
                possible_death = injury_dict["death_text"] if "death_text" in injury_dict else None
                if injured_rabbit.status == "leader":
                    possible_death = injury_dict["death_leader_text"] if "death_leader_text" in injury_dict else None
                
                if possible_scar or possible_death:
                    for condition in injuries:
                        History.add_possible_history(injured_rabbit, condition, death_text=possible_death, scar_text=possible_scar)

        # get any possible interaction string out of this interaction
        interaction_str = choice(chosen_interaction.interactions)

        # prepare string for display
        rabbit_dict = {
            "m_c": (str(rabbit_from.name), choice(rabbit_from.pronouns)),
            "r_r": (str(rabbit_to.name), choice(rabbit_to.pronouns))
        }
        interaction_str = process_text(interaction_str, rabbit_dict)
        
        # extract intensity from the interaction
        intensity = getattr(chosen_interaction, 'intensity', 'neutral')

        effect = " (neutral effect)"
        if in_de_crease != "neutral" and positive:
            effect = f" ({intensity} positive effect)"
        if in_de_crease != "neutral" and not positive:
            effect = f" ({intensity} negative effect)"

        interaction_str = interaction_str + effect

        # send string to current month relationship events before adding age of rabbits
        relevant_event_tabs = ["relation", "interaction"]
        if len(chosen_interaction.get_injuries) > 0:
            relevant_event_tabs.append("health")
        game.cur_events_list.append(Single_Event(
            interaction_str, relevant_event_tabs, [rabbit_to.ID, rabbit_from.ID]
        ))

        # now add the age of the rabbits before the string is sent to the rabbits' relationship logs
        relationship.log.append(interaction_str + f" - {rabbit_from.name} was {rabbit_from.months} months old")

        if not relationship.opposite_relationship and rabbit_from.ID != rabbit_to.ID:
            relationship.link_relationship()
            relationship.opposite_relationship.log.append(interaction_str + f" - {rabbit_to.name} was {rabbit_to.months} months old")

        #print(f"ROMANTIC! {rabbit_from.name} to {rabbit_to.name}")
        return True

    @staticmethod
    def handle_mating_and_breakup(rabbit):
        """Handle events related to making new mates, and breaking up. """
        
        if rabbit.no_mates:
            return
        
        Romantic_Events.handle_moving_on(rabbit)
        Romantic_Events.handle_breakup_events(rabbit)
        Romantic_Events.handle_new_mate_events(rabbit)
        
        
    
    @staticmethod
    def handle_new_mate_events(rabbit):
        """Triggers and handles any events that result in a new mate """
        
        # First, check high love confession
        flag = Romantic_Events.handle_confession(rabbit)
        if flag:
            return
        
        # Then, handle more random mating
        # Choose some subset of rabbits that they have relationships with
        if not rabbit.relationships:
            return
        subset = [Rabbit.fetch_rabbit(x) for x in rabbit.relationships if isinstance(Rabbit.fetch_rabbit(x), Rabbit) and not (Rabbit.fetch_rabbit(x).dead or Rabbit.fetch_rabbit(x).outside)]
        if not subset:
            return
        
        subset = random.sample(subset, max(int(len(subset) / 3), 1))
        
        for other_rabbit in subset:
            relationship = rabbit.relationships.get(other_rabbit.ID)
            flag = Romantic_Events.handle_new_mates(rabbit, other_rabbit)
            if flag:
                return
        
    @staticmethod
    def handle_breakup_events(rabbit: Rabbit):
        """Triggers and handles any events that results in a breakup """
        
        for x in rabbit.mate:
            mate_ob = Rabbit.fetch_rabbit(x)
            if not isinstance(mate_ob, Rabbit):
                continue
                        
            flag = Romantic_Events.handle_breakup(rabbit, mate_ob)
            if flag:
                return
        
         
    @staticmethod
    def handle_moving_on(rabbit):
        """Handles moving on from dead or outside mates """
        for mate_id in rabbit.mate:
            if mate_id not in Rabbit.all_rabbits:
                print(f"WARNING: Rabbit #{rabbit} has a invalid mate. It will be removed.")
                rabbit.mate.remove(mate_id)
                continue

            rabbit_mate = Rabbit.fetch_rabbit(mate_id)
            if rabbit_mate.no_mates:
                return
            
            # Move on from dead mates
            if rabbit_mate and "grief stricken" not in rabbit.illnesses and ((rabbit_mate.dead and rabbit_mate.dead_for >= 4) or rabbit_mate.outside):
                # randint is a slow function, don't call it unless we have to.
                if not rabbit_mate.no_mates and random.random() > 0.5:
                    text = f'{rabbit.name} will always love {rabbit_mate.name} but has decided to move on.'
                    game.cur_events_list.append(Single_Event(text, "relation", [rabbit.ID, rabbit_mate.ID]))
                    rabbit.unset_mate(rabbit_mate)
    
    
    @staticmethod
    def handle_new_mates(rabbit_from, rabbit_to) -> bool:
        """More in depth check if the rabbits will become mates."""
        
        become_mates, mate_string = Romantic_Events.check_if_new_mate(rabbit_from, rabbit_to)

        if become_mates and mate_string:
            rabbit_from.set_mate(rabbit_to)
            game.cur_events_list.append(Single_Event(mate_string, ["relation", "misc"], [rabbit_from.ID, rabbit_to.ID]))
            return True
        
        return False

    @staticmethod
    def handle_breakup(rabbit_from: Rabbit, rabbit_to:Rabbit) -> bool:
        ''' Handles rabbits breaking up their relationship '''
        
        if rabbit_from.ID not in rabbit_to.mate:
            return False
        
        if rabbit_from.no_mates or rabbit_to.no_mates:
            return False
        
        if rabbit_to.no_mates or rabbit_from.no_mates:
            return False
        
        if not Romantic_Events.check_if_breakup(rabbit_from, rabbit_to):
            return False
        
        # Determine if this is a nice breakup or a fight breakup
        #TODO - make this better
        had_fight = not int(random.random() * 3)
    
        #TODO : more varied breakup text.
        rabbit_from.unset_mate(rabbit_to, breakup=False)
        
        if rabbit_to.ID in rabbit_from.relationships:
            relationship_from = rabbit_from.relationships[rabbit_to.ID]
        else:
            relationship_from = rabbit_from.create_one_relationship(rabbit_to)
            
        if rabbit_from.ID in rabbit_to.relationships:
            relationship_to = rabbit_to.relationships[rabbit_from.ID]
        else:
            relationship_to = rabbit_to.create_one_relationship(rabbit_from)
            
        # These are large decreases - they are to prevent becoming mates again on the same month.
        relationship_to.romantic_love -= 15
        relationship_from.romantic_love -= 15
        relationship_to.comfortable -= 10
        relationship_from.comfortable -= 10
        if had_fight:
            relationship_to.romantic_love -= 5
            relationship_from.romantic_love -= 5
            relationship_from.platonic_like -= 10
            relationship_to.platonic_like -= 10
            relationship_from.trust -= 10
            relationship_to.trust -= 10
            relationship_to.dislike += 10
            relationship_from.dislike += 10
        
        
        if had_fight:
            text = f"{rabbit_from.name} and {rabbit_to.name} had a huge fight and broke up."
        else:
            text = f"{rabbit_from.name} and {rabbit_to.name} broke up."
        game.cur_events_list.append(Single_Event(text, ["relation", "misc"], [rabbit_from.ID, rabbit_to.ID]))
        return True

    @staticmethod
    def handle_confession(rabbit_from) -> bool:
        """
        Check if the rabbit has a high love for another and mate them if there are in the boundaries 
        :param rabbit: rabbit in question

        return: bool if event is triggered or not
        """
        # get the highest romantic love relationships and
        rel_list = rabbit_from.relationships.values()
        highest_romantic_relation = get_highest_romantic_relation(rel_list, exclude_mate=True)
        if not highest_romantic_relation:
            return False

        condition = game.config["mates"]["confession"]["make_confession"]
        if not Romantic_Events.relationship_fulfill_condition(highest_romantic_relation, condition):
            return False

        rabbit_to = highest_romantic_relation.rabbit_to
        if not rabbit_to.is_potential_mate(rabbit_from) or not rabbit_from.is_potential_mate(rabbit_to):
            return False

        alive_inwarren_from_mates = [mate for mate in rabbit_from.mate if not rabbit_from.fetch_rabbit(mate).dead and not rabbit_from.fetch_rabbit(mate).outside]
        alive_inwarren_to_mates = [mate for mate in rabbit_to.mate if not rabbit_to.fetch_rabbit(mate).dead and not rabbit_to.fetch_rabbit(mate).outside]
        poly = len(alive_inwarren_from_mates) > 0 or len(alive_inwarren_to_mates) > 0

        if poly and not Romantic_Events.current_mates_allow_new_mate(rabbit_from, rabbit_to):
            return False

        become_mate = False
        condition = game.config["mates"]["confession"]["accept_confession"]
        rel_to_check = highest_romantic_relation.opposite_relationship
        if not rel_to_check:
            highest_romantic_relation.link_relationship()
            rel_to_check = highest_romantic_relation.opposite_relationship
        
        if Romantic_Events.relationship_fulfill_condition(rel_to_check, condition):
            become_mate = True
            mate_string = Romantic_Events.get_mate_string("high_romantic", poly, rabbit_from, rabbit_to)
        # second acceptance chance if the romantic is high enough
        elif "romantic" in condition and condition["romantic"] != 0 and\
            condition["romantic"] > 0 and rel_to_check.romantic_love >= condition["romantic"] * 1.5:
            become_mate = True
            mate_string = Romantic_Events.get_mate_string("high_romantic", poly, rabbit_from, rabbit_to)
        else:
            mate_string = Romantic_Events.get_mate_string("rejected", poly, rabbit_from, rabbit_to)
            rabbit_from.relationships[rabbit_to.ID].romantic_love -= 10
            rabbit_to.relationships[rabbit_from.ID].comfortable -= 10

        mate_string = Romantic_Events.prepare_relationship_string(mate_string, rabbit_from, rabbit_to)
        game.cur_events_list.append(Single_Event(mate_string, ["relation", "misc"], [rabbit_from.ID, rabbit_to.ID]))

        if become_mate:
            rabbit_from.set_mate(rabbit_to)

        return True

    # ---------------------------------------------------------------------------- #
    #                          check if event is triggered                         #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def check_if_positive_interaction(relationship) -> bool:
        """Returns if the interaction should be a positive interaction or not."""
        # base for non-existing platonic like / dislike
        list_to_choice = [True, False]

        # take personality in count
        comp = get_personality_compatibility(relationship.rabbit_from, relationship.rabbit_to)
        if comp is not None:
            list_to_choice.append(comp)

        # further influence the partition based on the relationship
        list_to_choice += [True] * int(relationship.platonic_like/15)
        list_to_choice += [True] * int(relationship.romantic_love/15)
        list_to_choice += [False] * int(relationship.dislike/10)

        return choice(list_to_choice)

    @staticmethod
    def check_if_breakup(rabbit_from, rabbit_to):
        """ More in depth check if the rabbits will break up.
            Returns:
                bool (True or False)
        """
        if rabbit_from.ID not in rabbit_to.mate:
            return False
        
        # Moving on, not breakups, occur when one mate is dead or outside. 
        if rabbit_from.dead or rabbit_from.outside or rabbit_to.dead or rabbit_to.outside:
            return False

        chance_number = Romantic_Events.get_breakup_chance(rabbit_from, rabbit_to)
        if chance_number == 0:
            return False
        
        return not int(random.random() * chance_number)

    @staticmethod
    def check_if_new_mate(rabbit_from, rabbit_to):
        """Checks if the two rabbits can become mates, or not. Returns: boolean and event_string"""
        become_mates = False
        young_age = ['newborn', 'kitten', 'adolescent']
        if not rabbit_from.is_potential_mate(rabbit_to):
            return False, None
        
        if rabbit_from.ID in rabbit_to.mate:
            return False, None
        
        # Gather relationships
        if rabbit_to.ID in rabbit_from.relationships:
            relationship_from = rabbit_from.relationships[rabbit_to.ID]
        else:
            relationship_from = rabbit_from.create_one_relationship(rabbit_to)
            
        if rabbit_from.ID in rabbit_to.relationships:
            relationship_to = rabbit_to.relationships[rabbit_from.ID]
        else:
            relationship_to = rabbit_to.create_one_relationship(rabbit_from)
        
        mate_string = None
        mate_chance = game.config["mates"]["chance_fulfilled_condition"]
        hit = int(random.random() * mate_chance)

        # has to be high because every month this will be checked for each relationship in the game
        friends_to_lovers = game.config["mates"]["chance_friends_to_lovers"]
        random_hit = int(random.random() * friends_to_lovers)

        # already return if there is 'no' hit (everything above 0), other checks are not necessary
        if hit > 0 and random_hit > 0:
            return False, None

        alive_inwarren_from_mates = [mate for mate in rabbit_from.mate if not rabbit_from.fetch_rabbit(mate).dead and not rabbit_from.fetch_rabbit(mate).outside]
        alive_inwarren_to_mates = [mate for mate in rabbit_to.mate if not rabbit_to.fetch_rabbit(mate).dead and not rabbit_to.fetch_rabbit(mate).outside]
        poly = len(alive_inwarren_from_mates) > 0 or len(alive_inwarren_to_mates) > 0

        if poly and not Romantic_Events.current_mates_allow_new_mate(rabbit_from, rabbit_to):
            return False, None

        if not hit and Romantic_Events.relationship_fulfill_condition(relationship_from, game.config["mates"]["mate_condition"]) and\
            Romantic_Events.relationship_fulfill_condition(relationship_to, game.config["mates"]["mate_condition"]):
            become_mates = True
            mate_string = Romantic_Events.get_mate_string("low_romantic", poly, rabbit_from, rabbit_to)
        if not random_hit and Romantic_Events.relationship_fulfill_condition(relationship_from, game.config["mates"]["platonic_to_romantic"]) and\
            Romantic_Events.relationship_fulfill_condition(relationship_to, game.config["mates"]["platonic_to_romantic"]):
            become_mates = True
            mate_string = Romantic_Events.get_mate_string("platonic_to_romantic", poly, rabbit_from, rabbit_to)

        if not become_mates:
            return False, None

        if poly:
            print("----- POLY-POLY-POLY", rabbit_from.name, rabbit_to.name)
            print(rabbit_from.mate)
            print(rabbit_to.mate)
        else:
            print("BECOME MATES")

        mate_string = Romantic_Events.prepare_relationship_string(mate_string, rabbit_from, rabbit_to)

        return become_mates, mate_string

    @staticmethod
    def relationship_fulfill_condition(relationship, condition):
        """
        Check if the relationship can fulfill the condition. 
        Example condition:
            {
            "romantic": 20,
            "platonic": 30,
            "dislike": -10,
            "admiration": 0,
            "comfortable": 20,
            "jealousy": 0,
            "trust": 0
            }

        VALUES: 
            - 0: no condition
            - positive number: value has to be higher than number
            - negative number: value has to be lower than number
        
        """
        if not relationship:
            return False
        if "romantic" in condition and condition["romantic"] != 0:
            if condition["romantic"] > 0 and relationship.romantic_love < condition["romantic"]:
                return False
            if condition["romantic"] < 0 and relationship.romantic_love > abs(condition["romantic"]):
                return False
        if "platonic" in condition and condition["platonic"] != 0:
            if condition["platonic"] > 0 and relationship.platonic_like < condition["platonic"]:
                return False
            if condition["platonic"] < 0 and relationship.platonic_like > abs(condition["platonic"]):
                return False
        if "dislike" in condition and condition["dislike"] != 0:
            if condition["dislike"] > 0 and relationship.dislike < condition["dislike"]:
                return False
            if condition["dislike"] < 0 and relationship.dislike > abs(condition["dislike"]):
                return False
        if "admiration" in condition and condition["admiration"] != 0:
            if condition["admiration"] > 0 and relationship.admiration < condition["admiration"]:
                return False
            if condition["admiration"] < 0 and relationship.admiration > abs(condition["admiration"]):
                return False
        if "comfortable" in condition and condition["comfortable"] != 0:
            if condition["comfortable"] > 0 and relationship.comfortable < condition["comfortable"]:
                return False
            if condition["comfortable"] < 0 and relationship.comfortable > abs(condition["comfortable"]):
                return False
        if "jealousy" in condition and condition["jealousy"] != 0:
            if condition["jealousy"] > 0 and relationship.jealousy < condition["jealousy"]:
                return False
            if condition["jealousy"] < 0 and relationship.jealousy > abs(condition["jealousy"]):
                return False
        if "trust" in condition and condition["trust"] != 0:
            if condition["trust"] > 0 and relationship.trust < condition["trust"]:
                return False
            if condition["trust"] < 0 and relationship.trust > abs(condition["trust"]):
                return False
        return True

    @staticmethod
    def current_mates_allow_new_mate(rabbit_from, rabbit_to) -> bool:
        """Check if all current mates are fulfill the given conditions."""
        current_mate_condition = game.config["mates"]["poly"]["current_mate_condition"]
        current_to_new_condition = game.config["mates"]["poly"]["mates_to_each_other"]

        # check relationship from current mates from rabbit_from
        all_mates_fulfill_current_mate_condition = True
        all_mates_fulfill_current_to_new = True
        alive_inwarren_from_mates = [mate for mate in rabbit_from.mate if not rabbit_from.fetch_rabbit(mate).dead and not rabbit_from.fetch_rabbit(mate).outside]
        if len(alive_inwarren_from_mates) > 0:
            for mate_id in alive_inwarren_from_mates:
                mate_rabbit = rabbit_from.fetch_rabbit(mate_id)
                if mate_rabbit.dead:
                    continue
                if mate_id in rabbit_from.relationships and rabbit_from.ID in mate_rabbit.relationships:
                    if not Romantic_Events.relationship_fulfill_condition(rabbit_from.relationships[mate_id], current_mate_condition) or\
                        not Romantic_Events.relationship_fulfill_condition(mate_rabbit.relationships[rabbit_from.ID], current_mate_condition):
                        all_mates_fulfill_current_mate_condition = False
                
                if mate_id in rabbit_to.relationships and rabbit_to.ID in mate_rabbit.relationships:
                    if not Romantic_Events.relationship_fulfill_condition(rabbit_to.relationships[mate_id], current_to_new_condition) or\
                        not Romantic_Events.relationship_fulfill_condition(mate_rabbit.relationships[rabbit_to.ID], current_to_new_condition):
                        all_mates_fulfill_current_to_new = False
        if not all_mates_fulfill_current_mate_condition or\
            not all_mates_fulfill_current_to_new:
            return False

        # check relationship from current mates from rabbit_to
        all_mates_fulfill_current_mate_condition = True
        all_mates_fulfill_current_to_new = True
        alive_inwarren_to_mates = [mate for mate in rabbit_to.mate if not rabbit_to.fetch_rabbit(mate).dead and not rabbit_to.fetch_rabbit(mate).outside]
        if len(alive_inwarren_to_mates) > 0:
            for mate_id in alive_inwarren_to_mates:
                mate_rabbit = rabbit_to.fetch_rabbit(mate_id)
                if mate_rabbit.dead:
                    continue
                if mate_id in rabbit_to.relationships and rabbit_to.ID in mate_rabbit.relationships:
                    if not Romantic_Events.relationship_fulfill_condition(rabbit_to.relationships[mate_id], current_mate_condition) or\
                        not Romantic_Events.relationship_fulfill_condition(mate_rabbit.relationships[rabbit_to.ID], current_mate_condition):
                        all_mates_fulfill_current_mate_condition = False

                if mate_id in rabbit_from.relationships and rabbit_from.ID in mate_rabbit.relationships:
                    if not Romantic_Events.relationship_fulfill_condition(rabbit_from.relationships[mate_id], current_to_new_condition) or\
                        not Romantic_Events.relationship_fulfill_condition(mate_rabbit.relationships[rabbit_from.ID], current_to_new_condition):
                        all_mates_fulfill_current_to_new = False
        if not all_mates_fulfill_current_mate_condition or\
            not all_mates_fulfill_current_to_new:
            return False

        return True

    @staticmethod
    def prepare_relationship_string(mate_string, rabbit_from, rabbit_to):
        """Prepares the relationship event string for display"""
        # replace mates with their names
        if "[m_c_mates]" in mate_string:
            mate_names = [str(rabbit_from.fetch_rabbit(mate_id).name) for mate_id in rabbit_from.mate]
            mate_name_string = mate_names[0]
            if len(mate_names) == 2:
                mate_name_string = mate_names[0] + " and " + mate_names[1]
            if len(mate_names) > 2:
                mate_name_string = ", ".join(mate_names[:-1]) + ", and " + mate_names[-1]
            mate_string = mate_string.replace("[m_c_mates]", mate_name_string)

        if "[r_r_mates]" in mate_string:
            mate_names = [str(rabbit_to.fetch_rabbit(mate_id).name) for mate_id in rabbit_to.mate]
            mate_name_string = mate_names[0]
            if len(mate_names) == 2:
                mate_name_string = mate_names[0] + " and " + mate_names[1]
            if len(mate_names) > 2:
                mate_name_string = ", ".join(mate_names[:-1]) + ", and " + mate_names[-1]
            mate_string = mate_string.replace("[r_r_mates]", mate_name_string)

        if "(m_c_mate/mates)" in mate_string:
            insert = "mate"
            if len(rabbit_from.mate) > 1:
                insert = "mates"
            mate_string = mate_string.replace("(m_c_mate/mates)", insert)

        if "(r_r_mate/mates)" in mate_string:
            insert = "mate"
            if len(rabbit_to.mate) > 1:
                insert = "mates"
            mate_string = mate_string.replace("(r_r_mate/mates)", insert)

        mate_string = event_text_adjust(Rabbit, mate_string, rabbit_from, rabbit_to)
        return mate_string

    @staticmethod
    def get_mate_string(key, poly, rabbit_from, rabbit_to):
        """Returns the mate string with the certain key, rabbits and poly."""
        if not poly:
            return choice(Romantic_Events.MATE_DICTS[key])
        else:
            poly_key = ""
            alive_inwarren_from_mates = [mate for mate in rabbit_from.mate if not rabbit_from.fetch_rabbit(mate).dead and not rabbit_from.fetch_rabbit(mate).outside]
            alive_inwarren_to_mates = [mate for mate in rabbit_to.mate if not rabbit_to.fetch_rabbit(mate).dead and not rabbit_to.fetch_rabbit(mate).outside]
            if len(alive_inwarren_from_mates) > 0 and len(alive_inwarren_to_mates) > 0:
                poly_key = "both_mates"
            elif len(alive_inwarren_from_mates) > 0 and len(alive_inwarren_to_mates) <= 0:
                poly_key = "m_c_mates"
            elif len(alive_inwarren_from_mates) <= 0 and len(alive_inwarren_to_mates) > 0:
                poly_key = "r_r_mates"
            return choice(Romantic_Events.POLY_MATE_DICTS[key][poly_key])

    # ---------------------------------------------------------------------------- #
    #                             get/calculate chances                            #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_breakup_chance(rabbit_from:Rabbit, rabbit_to:Rabbit) -> int:
        """ Looks into the current values and calculate the chance of breaking up. The lower, the more likely they will break up.
            Returns:
                integer (number)
        """
        # Gather relationships
        if rabbit_to.ID in rabbit_from.relationships:
            relationship_from = rabbit_from.relationships[rabbit_to.ID]
        else:
            relationship_from = rabbit_from.create_one_relationship(rabbit_to)
            
        if rabbit_from.ID in rabbit_to.relationships:
            relationship_to = rabbit_to.relationships[rabbit_from.ID]
        else:
            relationship_to = rabbit_to.create_one_relationship(rabbit_from)
        
        # No breakup chance if the rabbit is a good deal above the make-confession requirments.
        condition = game.config["mates"]["confession"]["make_confession"].copy()
        for x in condition:
            if condition[x] > 0:
                condition[x] += 16
        if Romantic_Events.relationship_fulfill_condition(relationship_from, condition):
            return 0
        if Romantic_Events.relationship_fulfill_condition(relationship_to, condition):
            return 0
        
        
        chance_number = 30
        chance_number += int(relationship_from.romantic_love / 20)
        chance_number += int(relationship_from.romantic_love / 20)
        chance_number += int(relationship_from.platonic_like / 20)
        chance_number += int(relationship_to.platonic_like / 20)
        chance_number -= int(relationship_from.dislike / 15)
        chance_number -= int(relationship_from.jealousy / 15)
        chance_number -= int(relationship_to.dislike / 15)
        chance_number -= int(relationship_to.jealousy / 15)

        # change the change based on the personality
        get_along = get_personality_compatibility(rabbit_from, rabbit_to)
        if get_along is not None and get_along:
            chance_number += 5
        if get_along is not None and not get_along:
            chance_number -= 10

        # Then, at least a 1/5 chance
        chance_number = max(chance_number, 5)

        #print(f"BREAKUP CHANCE - {rabbit_to.name}, {rabbit_from.name}: {chance_number}")
        return chance_number
