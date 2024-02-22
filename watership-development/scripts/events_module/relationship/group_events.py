import os
import ujson
from random import choice, shuffle
from copy import deepcopy

from scripts.rabbit.history import History
from scripts.utility import change_relationship_values, process_text
from scripts.rabbit.rabbits import Rabbit
from scripts.event_class import Single_Event
from scripts.rabbit_relations.interaction import create_group_interaction, Group_Interaction, rel_fulfill_rel_constraints
from scripts.game_structure.game_essentials import game
from scripts.rabbit_relations.relationship import Relationship

class Group_Events():

    # ---------------------------------------------------------------------------- #
    #                   build master dictionary for interactions                   #
    # ---------------------------------------------------------------------------- #


    base_path = os.path.join(
        "resources",
        "dicts",
        "relationship_events",
        "group_interactions"
    )

    GROUP_INTERACTION_MASTER_DICT = {}
    for rabbit_amount in os.listdir(base_path):
        if rabbit_amount == "group_types.json":
            continue
        file_path = os.path.join(base_path, rabbit_amount, "neutral.json")
        GROUP_INTERACTION_MASTER_DICT[rabbit_amount] = {}
        with open(file_path, 'r') as read_file:
            welcome_list = ujson.load(read_file)
            GROUP_INTERACTION_MASTER_DICT[rabbit_amount]["neutral"] = create_group_interaction(welcome_list)
        
        file_path = os.path.join(base_path, rabbit_amount, "positive.json")
        with open(file_path, 'r') as read_file:
            welcome_list = ujson.load(read_file)
            GROUP_INTERACTION_MASTER_DICT[rabbit_amount]["positive"] = create_group_interaction(welcome_list)

        file_path = os.path.join(base_path, rabbit_amount, "negative.json")
        with open(file_path, 'r') as read_file:
            welcome_list = ujson.load(read_file)
            GROUP_INTERACTION_MASTER_DICT[rabbit_amount]["negative"] = create_group_interaction(welcome_list)
            
    del base_path

    abbreviations_rabbit_id = {}
    rabbit_abbreviations_counter = {}
    chosen_interaction = None

    @staticmethod
    def start_interaction(rabbit: Rabbit, interact_rabbits: list) -> list:
        """Start to define the possible group interactions.

            Parameters
            ----------
            rabbit : Rabbit
                the main rabbit
            interact_rabbits : list
                a list of rabbits, which are open to interact with the main rabbit

            Returns
            -------
            list
                returns the list of the rabbit id's, which interacted with each other
        """
        Group_Events.abbreviations_rabbit_id = {} # keeps track of which abbreviation is which rabbit
        Group_Events.rabbit_abbreviations_counter = {} # will be needed to check which rabbit is the best fit for which abbreviation
        Group_Events.abbreviations_rabbit_id["m_c"] = rabbit.ID # set the main rabbit
        Group_Events.chosen_interaction = None

        rabbit_amount = choice(list(Group_Events.GROUP_INTERACTION_MASTER_DICT.keys()))
        inter_type = choice(["negative", "positive", "neutral"])

        # if the chosen amount is bigger than the given interaction rabbits,
        # there will be no possible solution and it will be returned
        if len(interact_rabbits) < int(rabbit_amount):
            return []

        # setup the abbreviations_rabbit_id dictionary
        for integer in range(int(rabbit_amount)-1):
            new_key = "r_r" + str(integer+1)
            Group_Events.abbreviations_rabbit_id[new_key] = None

        # get all possibilities
        possibilities = Group_Events.GROUP_INTERACTION_MASTER_DICT[rabbit_amount][inter_type]
        
        # get some filters premisses
        biome = str(game.warren.biome).casefold()
        season = str(game.warren.current_season).casefold()

        # start filter for main rabbit / basic checks
        # - this might reduce the amount of checks which will be needed when checking for other rabbits 
        possibilities = Group_Events.get_main_rabbit_interactions(possibilities,biome,season)

        # get possible interactions, considering the possible interacting rabbits 
        possibilities = Group_Events.get_filtered_interactions(possibilities, int(rabbit_amount), interact_rabbits)

        # if there is no possibility return
        if len(possibilities) < 1:
            return []
        # choose one interaction and 
        Group_Events.chosen_interaction = choice(possibilities)

        # TRIGGER ALL NEEDED FUNCTIONS TO REFLECT THE INTERACTION
        if game.warren.game_mode != 'classic':
            Group_Events.injuring_rabbits()
        amount = game.config["relationship"]["in_decrease_value"][Group_Events.chosen_interaction.intensity]

        if len(Group_Events.chosen_interaction.general_reaction) > 0:
            # if there is a general reaction in the interaction, then use this
            Group_Events.influence_general_relationship(amount)
        else:
            Group_Events.influence_specific_relationships(amount)

        # choose the interaction text and display 
        interaction_str = choice(Group_Events.chosen_interaction.interactions)
        interaction_str = Group_Events.prepare_text(interaction_str)
        # TODO: add the interaction to the relationship log?

        interaction_str = interaction_str + f" ({inter_type} effect)"
        ids = list(Group_Events.abbreviations_rabbit_id.values())
        relevant_event_tabs = ["relation", "interaction"]
        if Group_Events.chosen_interaction.get_injuries:
            relevant_event_tabs.append("health")

        game.cur_events_list.append(Single_Event(
            interaction_str, relevant_event_tabs, ids
        ))
        return ids

    # ---------------------------------------------------------------------------- #
    #                  functions to filter and decide interaction                  #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_main_rabbit_interactions(interactions: list, biome : str, season : str) -> list:
        """Filter interactions for MAIN rabbit.
            
            Parameters
            ----------
            interactions : list
                the interactions which need to be filtered
            biome : str
                biome of the warren
            season : str
                current season of the warren

            Returns
            -------
            filtered : list
                a list of interactions, which fulfill the criteria
        """
        filtered_interactions = []
        allowed_season = [season, "Any", "any"]
        allowed_biome = [biome, "Any", "any"]
        main_rabbit = Rabbit.all_rabbits[Group_Events.abbreviations_rabbit_id["m_c"]]
        for interact in interactions:
            in_tags = [i for i in interact.biome if i in allowed_biome] 
            if len(in_tags) < 1:
                continue

            in_tags = [i for i in interact.season if i in allowed_season]
            if len(in_tags) < 1:
                continue

            if len(interact.status_constraint) >= 1 and "m_c" in interact.status_constraint:
                if main_rabbit.status not in interact.status_constraint["m_c"]:
                    continue

            if len(interact.trait_constraint) >= 1 and "m_c" in interact.trait_constraint:
                if main_rabbit.personality.trait not in interact.trait_constraint["m_c"]:
                    continue

            if len(interact.skill_constraint) >= 1 and "m_c" in interact.skill_constraint:
                if not main_rabbit.skills.check_skill_requirement_list(interact.skill_constraint):
                    continue
            
            if len(interact.backstory_constraint) >= 1 and "m_c" in interact.backstory_constraint:
                if main_rabbit.backstory not in interact.backstory_constraint["m_c"]:
                    continue

            filtered_interactions.append(interact)
        return filtered_interactions

    @staticmethod
    def get_filtered_interactions(interactions: list, amount: int, interact_rabbits: list):
        """ First assign which rabbit is which abbreviation, then filtered interaction list based on all constraints, which include the other rabbits.

            Parameters
            ----------
            interactions : list
                the interactions which need to be filtered
            amount : int
                the amount of rabbits which are be needed for these interactions
            interact_rabbits : list
                a list of rabbits, which are open to interact with the main rabbit

            Returns
            -------
            filtered : list
                a list of interactions, which fulfill the criteria
        
        """
        # first handle the abbreviations possibilities for the rabbits
        abbr_per_interaction = Group_Events.get_abbreviations_possibilities(interactions, int(amount), interact_rabbits)
        abbr_per_interaction = Group_Events.remove_abbreviations_missing_rabbits(abbr_per_interaction)
        Group_Events.set_abbreviations_rabbits(interact_rabbits)

        # check if any abbreviations_rabbit_ids is None, if so return 
        not_none = [abbr != None for abbr in Group_Events.abbreviations_rabbit_id.values()]
        if not all(not_none):
            return []

        # last filter based on relationships between the rabbits
        filtered = []
        for interact in interactions:
            # if this interaction is not in the  abbreviations dictionary,
            # there is no solution for the rabbit-abbreviations problem and thus, this
            # interaction is not possible
            if interact.id not in abbr_per_interaction.keys():
                continue

            # check how the rabbits are and if they are fulfill the constraints like: status, trait, skill, ...
            rabbit_allow_interaction = Group_Events.rabbit_allow_interaction(interact)
            if not rabbit_allow_interaction:
                continue

            # now check for relationship constraints
            relationship_allow_interaction = Group_Events.relationship_allow_interaction(interact)
            if not relationship_allow_interaction:
                continue

            filtered.append(interact)

        return filtered

    @staticmethod
    def get_abbreviations_possibilities(interactions: list, amount: int, interact_rabbits: list):
        """ Iterate over all pre-filtered interactions and 
            check which rabbit fulfills skill/trait/status condition of which abbreviation.

            Parameters
            ----------
            interactions : list
                the interactions which need to be filtered
            amount : int
                the amount of rabbits for the current interaction
            interact_rabbits : list
                a list of rabbits, which are open to interact with the main rabbit
        """
        possibilities = {}
        # prepare how the base dictionary should look, 
        # this depends on the chosen rabbit amount -> which abbreviation are needed
        base_dictionary = {}
        for integer in range(amount):
            new_key = "r_r" + str(integer+1)
            base_dictionary[new_key] = []

        # iterate over all interactions and checks for each abbreviation, which rabbit is possible
        for interact in interactions:
            dictionary = deepcopy(base_dictionary)

            for abbreviation in dictionary:
                dictionary[abbreviation] = []
                status_ids = []
                skill_ids = []
                trait_ids = []

                # if the abbreviation has a status constraint, check in details
                if abbreviation in interact.status_constraint:
                    # if the rabbit status is in the status constraint, add the id to the list
                    status_ids = [rabbit.ID for rabbit in interact_rabbits if rabbit.status in interact.status_constraint[abbreviation]]
                else:
                    # if there is no constraint, add all ids to the list 
                    status_ids = [rabbit.ID for rabbit in interact_rabbits]

                # same as status
                if abbreviation in interact.skill_constraint:
                    skill_ids = [rabbit.ID for rabbit in interact_rabbits if rabbit.skill in interact.skill_constraint[abbreviation]]
                else:
                    skill_ids = [rabbit.ID for rabbit in interact_rabbits]

                if abbreviation in interact.trait_constraint:
                    trait_ids = [rabbit.ID for rabbit in interact_rabbits if rabbit.personality.trait in interact.trait_constraint[abbreviation]]
                else:
                    trait_ids = [rabbit.ID for rabbit in interact_rabbits]

                # only add the id if it is in all other lists
                for rabbit_id in [rabbit.ID for rabbit in interact_rabbits]:
                    if rabbit_id in status_ids and rabbit_id in skill_ids and rabbit_id in trait_ids:
                        dictionary[abbreviation].append(rabbit_id)

                        if rabbit_id in Group_Events.rabbit_abbreviations_counter and\
                            abbreviation in Group_Events.rabbit_abbreviations_counter[rabbit_id]:
                            Group_Events.rabbit_abbreviations_counter[rabbit_id][abbreviation] +=1
                        elif rabbit_id in Group_Events.rabbit_abbreviations_counter and\
                            abbreviation not in Group_Events.rabbit_abbreviations_counter[rabbit_id]:
                            Group_Events.rabbit_abbreviations_counter[rabbit_id][abbreviation] = 1
                        else:
                            Group_Events.rabbit_abbreviations_counter[rabbit_id] = {}
                            Group_Events.rabbit_abbreviations_counter[rabbit_id][abbreviation] = 1

            possibilities[interact.id] = dictionary
        return possibilities

    @staticmethod
    def remove_abbreviations_missing_rabbits(abbreviations_per_interaction: dict):
        """
        Check which combinations of abbreviations are allowed and possible and which are not, only return a dictionary,
        with possible combinations together with the id for the interaction.
        """
        filtered_abbreviations = {}
        for interaction_id, dictionary in abbreviations_per_interaction.items():
            # check if there is any abbreviation, which is empty
            abbr_length = [len(val) for abr,val in dictionary.items()]
            # if one length is 0 the all function returns false
            if not all(abbr_length):
                continue

            filtered_abbreviations[interaction_id] = dictionary
        return filtered_abbreviations

    @staticmethod
    def set_abbreviations_rabbits(interact_rabbits: list):
        """Choose which rabbit is which abbreviations."""
        free_to_choose = [rabbit.ID for rabbit in interact_rabbits]
        # shuffle the list to prevent choosing the same rabbits every time
        shuffle(free_to_choose)

        for abbr_key in list(Group_Events.abbreviations_rabbit_id.keys()):
            if abbr_key == "m_c":
                continue
            highest_value = 0
            highest_id = None

            # gets the rabbit id which fits the abbreviations most of the time
            for rabbit_id in free_to_choose:
                # first set some values if there are none
                if rabbit_id not in Group_Events.rabbit_abbreviations_counter:
                    Group_Events.rabbit_abbreviations_counter[rabbit_id] = {}
                if abbr_key not in Group_Events.rabbit_abbreviations_counter[rabbit_id]:
                    Group_Events.rabbit_abbreviations_counter[rabbit_id][abbr_key] = 0

                # find the highest value
                curr_value = Group_Events.rabbit_abbreviations_counter[rabbit_id][abbr_key]
                if highest_value < curr_value:
                    highest_value = curr_value
                    highest_id = rabbit_id
            
            Group_Events.abbreviations_rabbit_id[abbr_key] = highest_id
            if highest_id in free_to_choose:
                free_to_choose.remove(highest_id)

    # ---------------------------------------------------------------------------- #
    #                  helper functions for filtering interactions                 #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def relationship_allow_interaction(interaction: Group_Interaction):
        """Check if the interaction is allowed with the current chosen rabbits."""
        fulfilled_list = []

        for name, rel_constraint in interaction.relationship_constraint.items():
            abbre_from = name.split('_to_')[0]
            abbre_to = name.split('_to_')[1]

            rabbit_from_id = Group_Events.abbreviations_rabbit_id[abbre_from]
            rabbit_to_id = Group_Events.abbreviations_rabbit_id[abbre_to]
            rabbit_from = Rabbit.all_rabbits[rabbit_from_id]
            rabbit_to = Rabbit.all_rabbits[rabbit_to_id]

            if rabbit_to_id not in rabbit_from.relationships:
                rabbit_from.create_one_relationship(rabbit_to)
                if rabbit_from.ID not in rabbit_to.relationships:
                    rabbit_to.create_one_relationship(rabbit_from)
                continue

            relationship = rabbit_from.relationships[rabbit_to_id]
            
            fulfilled = rel_fulfill_rel_constraints(relationship, rel_constraint, interaction.id)
            fulfilled_list.append(fulfilled)

        return all(fulfilled_list)

    @staticmethod
    def rabbit_allow_interaction(interaction: Group_Interaction):
        """Check if the assigned rabbits fulfill the constraints of the interaction."""

        all_fulfilled = True
        for abbr, constraint in interaction.status_constraint.items():
            # main rabbit is already filtered
            if abbr == "m_c":
                continue
            # check if the current abbreviations rabbit fulfill the constraint
            relevant_rabbit = Rabbit.all_rabbits[Group_Events.abbreviations_rabbit_id[abbr]]
            if relevant_rabbit.status not in constraint:
                all_fulfilled = False
        if not all_fulfilled:
            return False

        # check if all rabbits fulfill the skill constraints
        all_fulfilled = True
        for abbr, constraint in interaction.skill_constraint.items():
            # main rabbit is already filtered
            if abbr == "m_c":
                continue
            # check if the current abbreviations rabbit fulfill the constraint
            relevant_rabbit = Rabbit.all_rabbits[Group_Events.abbreviations_rabbit_id[abbr]]
            if relevant_rabbit.skill not in constraint:
                all_fulfilled = False
        if not all_fulfilled:
            return False

        # check if all rabbits fulfill the trait constraints
        all_fulfilled = True
        for abbr, constraint in interaction.trait_constraint.items():
            # main rabbit is already filtered
            if abbr == "m_c":
                continue
            # check if the current abbreviations rabbit fulfill the constraint
            relevant_rabbit = Rabbit.all_rabbits[Group_Events.abbreviations_rabbit_id[abbr]]
            if relevant_rabbit.personality.trait not in constraint:
                all_fulfilled = False
        if not all_fulfilled:
            return False

        # check if all rabbits fulfill the backstory constraints
        all_fulfilled = True
        for abbr, constraint in interaction.backstory_constraint.items():
            # main rabbit is already filtered
            if abbr == "m_c":
                continue
            # check if the current abbreviations rabbit fulfill the constraint
            relevant_rabbit = Rabbit.all_rabbits[Group_Events.abbreviations_rabbit_id[abbr]]
            if relevant_rabbit.backstory not in constraint:
                all_fulfilled = False
        if not all_fulfilled:
            return False

        # if the interaction has injuries constraints, but the warren is in classic mode
        if game.warren.game_mode == 'classic' and len(interaction.has_injuries) > 0:
            return False
        # check if all rabbits fulfill the injuries constraints
        all_fulfilled = True
        for abbr, constraint in interaction.has_injuries.items():
            # main rabbit is already filtered
            if abbr == "m_c":
                continue
            # check if the current abbreviations rabbit fulfill the constraint
            relevant_rabbit = Rabbit.all_rabbits[Group_Events.abbreviations_rabbit_id[abbr]]
            injuries_in_needed = list(
                filter(lambda inj: inj in constraint, relevant_rabbit.injuries.keys())
            )
            if len(injuries_in_needed) <= 0:
                all_fulfilled = False
        if not all_fulfilled:
            return False
        return True


    # ---------------------------------------------------------------------------- #
    #                      functions after interaction decision                    #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def influence_general_relationship(amount):
        """
        Influence the relationship between all rabbits with the same amount, defined by the chosen group relationship.
        """
        dictionary = Group_Events.chosen_interaction.general_reaction

        # set the amount
        romantic = 0
        platonic = 0
        dislike = 0
        admiration = 0
        comfortable = 0
        jealousy = 0
        trust = 0
        if "romantic" in dictionary and dictionary["romantic"] != "neutral":
            romantic = amount if dictionary["romantic"] == "increase" else amount *-1
        if "platonic" in dictionary and dictionary["platonic"] != "neutral":
            platonic = amount if dictionary["platonic"] == "increase" else amount *-1
        if "dislike" in dictionary and dictionary["dislike"] != "neutral":
            platonic = amount if dictionary["dislike"] == "increase" else amount *-1
        if "admiration" in dictionary and dictionary["admiration"] != "neutral":
            platonic = amount if dictionary["admiration"] == "increase" else amount *-1
        if "comfortable" in dictionary and dictionary["comfortable"] != "neutral":
            platonic = amount if dictionary["comfortable"] == "increase" else amount *-1
        if "jealousy" in dictionary and dictionary["jealousy"] != "neutral":
            platonic = amount if dictionary["jealousy"] == "increase" else amount *-1
        if "trust" in dictionary and dictionary["trust"] != "neutral":
            platonic = amount if dictionary["trust"] == "increase" else amount *-1


        for inter_rabbit_id in Group_Events.abbreviations_rabbit_id.values():
            inter_rabbit = Rabbit.all_rabbits[inter_rabbit_id]
            change_relationship_values(
                rabbits_from=[inter_rabbit],
                rabbits_to=list(Group_Events.abbreviations_rabbit_id.values()),
                romantic_love=romantic,
                platonic_like=platonic,
                dislike=dislike,
                admiration=admiration,
                comfortable=comfortable,
                jealousy=jealousy,
                trust=trust
            )

    @staticmethod
    def influence_specific_relationships(amount):
        """
        Influence the relationships based on the list of the reaction of the chosen group interaction.
        """
        if len(Group_Events.chosen_interaction.specific_reaction) <= 0:
            return

        for name, dictionary in Group_Events.chosen_interaction.specific_reaction.items():
            abbre_from = name.split('_to_')[0]
            abbre_to = name.split('_to_')[1]

            rabbit_from_id = Group_Events.abbreviations_rabbit_id[abbre_from]
            rabbit_to_id = Group_Events.abbreviations_rabbit_id[abbre_to]
            rabbit_from = Rabbit.all_rabbits[rabbit_from_id]

            # set all values to influence the relationship
            romantic = 0
            platonic = 0
            dislike = 0
            admiration = 0
            comfortable = 0
            jealousy = 0
            trust = 0
            if "romantic" in dictionary and dictionary["romantic"] != "neutral":
                romantic = amount if dictionary["romantic"] == "increase" else amount *-1
            if "platonic" in dictionary and dictionary["platonic"] != "neutral":
                platonic = amount if dictionary["platonic"] == "increase" else amount *-1
            if "dislike" in dictionary and dictionary["dislike"] != "neutral":
                dislike = amount if dictionary["dislike"] == "increase" else amount *-1
            if "admiration" in dictionary and dictionary["admiration"] != "neutral":
                admiration = amount if dictionary["admiration"] == "increase" else amount *-1
            if "comfortable" in dictionary and dictionary["comfortable"] != "neutral":
                comfortable = amount if dictionary["comfortable"] == "increase" else amount *-1
            if "jealousy" in dictionary and dictionary["jealousy"] != "neutral":
                jealousy = amount if dictionary["jealousy"] == "increase" else amount *-1
            if "trust" in dictionary and dictionary["trust"] != "neutral":
                trust = amount if dictionary["trust"] == "increase" else amount *-1

            change_relationship_values(
                rabbits_from=[rabbit_from],
                rabbits_to=[rabbit_to_id],
                romantic_love=romantic,
                platonic_like=platonic,
                dislike=dislike,
                admiration=admiration,
                comfortable=comfortable,
                jealousy=jealousy,
                trust=trust
            )

    @staticmethod
    def injuring_rabbits():
        """
        Injuring the rabbits based on the list of the injuries of the chosen group interaction.
        """
        if not Group_Events.chosen_interaction.get_injuries.items:
            return

        for abbreviations, injury_dict in Group_Events.chosen_interaction.get_injuries.items():
            if "injury_names" not in injury_dict:
                print(f"ERROR: there are no injury names in the chosen interaction {Group_Events.chosen_interaction.id}.")
                continue
            injured_rabbit = Rabbit.all_rabbits[Group_Events.abbreviations_rabbit_id[abbreviations]]

            injuries = []
            for inj in injury_dict["injury_names"]:
                injured_rabbit.get_injured(inj, True)
                injuries.append(inj)

            possible_scar = Group_Events.prepare_text(injury_dict["scar_text"]) if "scar_text" in injury_dict else None
            possible_death = Group_Events.prepare_text(injury_dict["death_text"]) if "death_text" in injury_dict else None
            if injured_rabbit.status == "leader":
                possible_death = Group_Events.prepare_text(injury_dict["death_leader_text"]) if "death_leader_text" in injury_dict else None
            
            if possible_death or possible_scar:
                for condition in injuries:
                    History.add_possible_history(injured_rabbit, condition, death_text=possible_death, scar_text=possible_scar)

    @staticmethod
    def prepare_text(text: str) -> str:
        """Prep the text based of the amount of rabbits and the assigned abbreviations."""
        
        replace_dict = {}
        for abbr, rabbit_id in Group_Events.abbreviations_rabbit_id.items():
            replace_dict[abbr] = (str(Rabbit.all_rabbits[rabbit_id].name), choice(Rabbit.all_rabbits[rabbit_id].pronouns))
        
        return process_text(text, replace_dict)
