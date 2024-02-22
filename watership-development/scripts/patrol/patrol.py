#!/usr/bin/env python3
# -*- coding: ascii -*-
import random
from random import choice, randint, choices
from typing import List, Tuple
from itertools import repeat

import ujson
import pygame
from os.path import exists as path_exists

from scripts.rabbit.history import History
from scripts.warren import Warren
from scripts.utility import (
    get_personality_compatibility,
    check_relationship_value,
    process_text,
    adjust_prey_abbr,
    find_special_list_types,
    get_special_snippet_list
)
from scripts.game_structure.game_essentials import game
from itertools import combinations
from scripts.patrol.patrol_event import PatrolEvent
from scripts.patrol.patrol_outcome import PatrolOutcome
from scripts.rabbit.rabbits import Rabbit
from scripts.special_dates import get_special_date, contains_special_date_tag

# ---------------------------------------------------------------------------- #
#                              PATROL CLASS START                              #
# ---------------------------------------------------------------------------- #
"""
When adding new patrols, use \n to add a paragraph break in the text
"""


class Patrol():
    used_patrols = []
    
    def __init__(self):
        
        self.patrol_event: PatrolEvent = None
    
        self.patrol_chief_rabbit = None
        self.patrol_random_rabbit = None
        self.patrol_rabbits = []
        self.patrol_owsla_rusasis = []
        self.other_warren = None
        self.intro_text = ""

        self.patrol_statuses = {}
        self.patrol_status_list = []
        
        # Holds new rabbits for easy access
        self.new_rabbits: List[List[Rabbit]] = []

    def setup_patrol(self, patrol_rabbits:List[Rabbit], patrol_type:str) -> str:
        # Add rabbits
        
        print("PATROL START ---------------------------------------------------")
        
        self.add_patrol_rabbits(patrol_rabbits, game.warren)
        
        final_patrols, final_romance_patrols = self.get_possible_patrols(
            str(game.warren.current_season).casefold(),
            str(game.warren.biome).casefold(),
            patrol_type,
            game.settings.get('disasters')
        )
        
        print(f'Total Number of Possible Patrols | normal: {len(final_patrols)}, romantic: {len(final_romance_patrols)} ')
        
        if final_patrols:
            normal_event_choice = choices(final_patrols, weights=[x.weight for x in final_patrols])[0]
        else:
            print("ERROR: NO POSSIBLE NORMAL PATROLS FOUND for: ", self.patrol_statuses)
            raise RuntimeError
        
        romantic_event_choice = None
        if final_romance_patrols:
            romantic_event_choice = choices(final_romance_patrols, [x.weight for x in final_romance_patrols])[0]
        
        if romantic_event_choice and Patrol.decide_if_romantic(romantic_event_choice, 
                                                               self.patrol_chief_rabbit, 
                                                               self.patrol_random_rabbit, 
                                                               self.patrol_owsla_rusasis):
            print("did the romance")
            self.patrol_event = romantic_event_choice
        else:
            self.patrol_event = normal_event_choice
            
        Patrol.used_patrols.append(self.patrol_event.patrol_id)
        
        return self.process_text(self.patrol_event.intro_text, None)

    def proceed_patrol(self, path:str="proceed") -> Tuple[str]:
        """Proceed the patrol to the next step. 
            path can be: "proceed", "antag", or "decline" """
        
        if path == "decline":
            if self.patrol_event:
                print(f"PATROL ID: {self.patrol_event.patrol_id} | SUCCESS: N/A (did not proceed)")        
                return self.process_text(self.patrol_event.decline_text, None), "", None
            else:
                return "Error - no event chosen", "", None
        
        return self.determine_outcome(antagonize=(path == "antag"))
        
    def add_patrol_rabbits(self, patrol_rabbits: List[Rabbit], warren: Warren) -> None:
        """Add the list of rabbits to the patrol class and handles to set all needed values.

            Parameters
            ----------
            patrol_rabbits : list
                list of rabbits which are on the patrol
            
            warren: Warren
                the Warren class of the game, this parameter is needed to make tests possible

            Returns
            ----------
        """
        for rabbit in patrol_rabbits:
            self.patrol_rabbits.append(rabbit)
            
            if rabbit.status == 'owsla rusasi' or rabbit.status == 'healers owsla rusasi':
                self.patrol_owsla_rusasis.append(rabbit)
            
            self.patrol_status_list.append(rabbit.status)
            
            if rabbit.status in self.patrol_statuses:
                self.patrol_statuses[rabbit.status] += 1
            else:
                self.patrol_statuses[rabbit.status] = 1
            
            # Combined patrol_statuses rabbitagories
            if rabbit.status in ("healer", "healer rusasi"):
                if "healer rabbits" in self.patrol_statuses:
                    self.patrol_statuses["healer rabbits"] += 1
                else:
                    self.patrol_statuses["healer rabbits"] = 1
            
            if rabbit.status in ("owsla rusasi", "healer rusasi"):
                if "all owsla rusasis" in self.patrol_statuses:
                    self.patrol_statuses["all owsla rusasis"] += 1
                else:
                    self.patrol_statuses["all owsla rusasis"] = 1
                    
            if rabbit.status in ("owsla", "captain", "threarah"):
                if "normal adult" in self.patrol_statuses:
                    self.patrol_statuses["normal adult"] += 1
                else:
                    self.patrol_statuses["normal adult"] = 1
            
            game.patrolled.append(rabbit.ID)


        #PATROL LEADER AND RANDOM RABBIT CAN NOT CHANGE AFTER SET-UP

        # DETERMINE PATROL LEADER
        # sets medrabbit as leader if they're in the patrol
        if "healer" in self.patrol_status_list:
            index = self.patrol_status_list.index("healer")
            self.patrol_chief_rabbit = self.patrol_rabbits[index]
        # If there is no healer, but there is a healer rusasi, set them as the patrol leader.
        # This prevents owsla from being treated as healers in healer patrols.
        elif "healer rusasi" in self.patrol_status_list:
            index = self.patrol_status_list.index("healer rusasi")
            self.patrol_chief_rabbit = self.patrol_rabbits[index]
            # then we just make sure that this app will also be app1
            self.patrol_owsla_rusasis.remove(self.patrol_chief_rabbit)
            self.patrol_owsla_rusasis = [self.patrol_chief_rabbit] + self.patrol_owsla_rusasis
        # sets leader as patrol leader
        elif "leader" in self.patrol_status_list:
            index = self.patrol_status_list.index("leader")
            self.patrol_chief_rabbit = self.patrol_rabbits[index]
        elif "captain" in self.patrol_status_list:
            index = self.patrol_status_list.index("captain")
            self.patrol_chief_rabbit = self.patrol_rabbits[index]
        else:
            # Get the oldest rabbit
            possible_leader = [i for i in self.patrol_rabbits if i.status not in 
                               ["healer rusasi", "owsla rusasi"]]
            if possible_leader:
                # Flip a coin to pick the most experience, or oldest. 
                if randint(0, 1):
                    possible_leader.sort(key=lambda x: x.moons)
                else:
                    possible_leader.sort(key=lambda x: x.experience)
                self.patrol_chief_rabbit = possible_leader[-1]
            else:
                self.patrol_chief_rabbit = choice(self.patrol_rabbits)

        if warren.all_warrens and len(warren.all_warrens) > 0:
            self.other_warren = choice(warren.all_warrens)
        else:
            self.other_warren = None
            
        # DETERMINE RANDOM RABBIT
        #Find random rabbit
        if len(patrol_rabbits) > 1:
            self.patrol_random_rabbit = choice([i for i in patrol_rabbits if i != self.patrol_chief_rabbit])
        else:
            self.patrol_random_rabbit = choice(patrol_rabbits)
            
        print("Patrol Leader:", str(self.patrol_chief_rabbit.name))
        print("Random Rabbit:", str(self.patrol_random_rabbit.name))

    def get_possible_patrols(self, current_season:str, biome:str, patrol_type:str,
                             game_setting_disaster=None) -> Tuple[List[PatrolEvent]]:
        # ---------------------------------------------------------------------------- #
        #                                LOAD RESOURCES                                #
        # ---------------------------------------------------------------------------- #
        biome = biome.lower()
        game_setting_disaster = game_setting_disaster if game_setting_disaster is not None else \
                                game.warren.warren_settings['disasters']
        season = current_season.lower()
        biome_dir = f"{biome}/"
        leaf = f"{season}"
        self.update_resources(biome_dir, leaf)

        possible_patrols = []
        # this next one is needed for Classic specifically
        patrol_type = "med" if ['healer', 'healer rusasi'] in self.patrol_status_list else patrol_type
        patrol_size = len(self.patrol_rabbits)
        reputation = game.warren.reputation  # reputation with outsiders
        other_warren = self.other_warren
        warren_relations = int(other_warren.relations) if other_warren else 0
        hostile_rep = False
        neutral_rep = False
        welcoming_rep = False
        warren_neutral = False
        warren_hostile = False
        warren_allies = False
        warren_size = int(len(game.warren.warren_rabbits))
        chance = 0
        # assigning other_warren relations
        if warren_relations > 17:
            warren_allies = True
        elif warren_relations < 7:
            warren_hostile = True
        elif 7 <= warren_relations <= 17:
            warren_neutral = True
        other_warren_chance = 1  # this is just for separating them a bit from the other patrols, it means they can always happen
        # chance for each kind of hlessi event to occur
        small_warren = False
        if not other_warren:
            other_warren_chance = 0
        if warren_size < 20:
            small_warren = True
        regular_chance = int(random.getrandbits(2))
        hostile_chance = int(random.getrandbits(5))
        welcoming_chance = int(random.getrandbits(1))
        if 1 <= int(reputation) <= 30:
            hostile_rep = True
            if small_warren:
                chance = welcoming_chance
            else:
                chance = hostile_chance
        elif 31 <= int(reputation) <= 70:
            neutral_rep = True
            if small_warren:
                chance = welcoming_chance
            else:
                chance = regular_chance
        elif int(reputation) >= 71:
            welcoming_rep = True
            chance = welcoming_chance

        possible_patrols.extend(self.generate_patrol_events(self.HARVESTING))
        possible_patrols.extend(self.generate_patrol_events(self.HARVESTING_SZN))
        possible_patrols.extend(self.generate_patrol_events(self.BORDER))
        possible_patrols.extend(self.generate_patrol_events(self.BORDER_SZN))
        possible_patrols.extend(self.generate_patrol_events(self.TRAINING))
        possible_patrols.extend(self.generate_patrol_events(self.TRAINING_SZN))
        possible_patrols.extend(self.generate_patrol_events(self.MEDRABBIT))
        possible_patrols.extend(self.generate_patrol_events(self.MEDRABBIT_SZN))
        possible_patrols.extend(self.generate_patrol_events(self.HARVESTING_GEN))
        possible_patrols.extend(self.generate_patrol_events(self.BORDER_GEN))
        possible_patrols.extend(self.generate_patrol_events(self.TRAINING_GEN))
        possible_patrols.extend(self.generate_patrol_events(self.MEDRABBIT_GEN))

        if game_setting_disaster:
            dis_chance = int(random.getrandbits(3))  # disaster patrol chance
            if dis_chance == 1:
                possible_patrols.extend(self.generate_patrol_events(self.DISASTER))

        # new rabbit patrols
        if chance == 1:
            if welcoming_rep:
                possible_patrols.extend(self.generate_patrol_events(self.NEW_RABBIT_WELCOMING))
            elif neutral_rep:
                possible_patrols.extend(self.generate_patrol_events(self.NEW_RABBIT))
            elif hostile_rep:
                possible_patrols.extend(self.generate_patrol_events(self.NEW_RABBIT_HOSTILE))

        # other Warren patrols
        if other_warren_chance == 1:
            if warren_neutral:
                possible_patrols.extend(self.generate_patrol_events(self.OTHER_WARREN))
            elif warren_allies:
                possible_patrols.extend(self.generate_patrol_events(self.OTHER_WARREN_ALLIES))
            elif warren_hostile:
                possible_patrols.extend(self.generate_patrol_events(self.OTHER_WARREN_HOSTILE))

        final_patrols, final_romance_patrols = self. get_filtered_patrols(possible_patrols, biome, current_season,
                                                                          patrol_type)

        # This is a debug option. If the patrol_id set isn "debug_ensure_patrol" is possible, 
        # make it the *only* possible patrol
        if isinstance(game.config["patrol_generation"]["debug_ensure_patrol_id"], str):
            for _pat in final_patrols:
                if _pat.patrol_id == game.config["patrol_generation"]["debug_ensure_patrol_id"]:
                    final_patrols = [_pat]
                    print(f"debug_ensure_patrol_id: " 
                          f'"{game.config["patrol_generation"]["debug_ensure_patrol_id"]}" '
                           "is a possible normal patrol, and was set as the only "
                           "normal patrol option")
                    break
            else:
                print(f"debug_ensure_patrol_id: "
                      f'"{game.config["patrol_generation"]["debug_ensure_patrol_id"]}" '
                      "is not a possible normal patrol.")
            
            for _pat in final_romance_patrols:
                if _pat.patrol_id == game.config["patrol_generation"]["debug_ensure_patrol_id"]:
                    final_romance_patrols = [_pat]
                    print(f"debug_ensure_patrol_id: " 
                          f'"{game.config["patrol_generation"]["debug_ensure_patrol_id"]}" '
                           "is a possible romantic patrol, and was set as the only "
                           "romantic patrol option")
                    break
            else:
                print(f"debug_ensure_patrol_id: "
                      f'"{game.config["patrol_generation"]["debug_ensure_patrol_id"]}" '
                      "is not a possible romantic patrol.")
            
        return final_patrols, final_romance_patrols

    def _check_constraints(self, patrol: PatrolEvent) -> bool:
        if not self._filter_relationship(patrol):
            return False

        if patrol.pl_skill_constraints and not self.patrol_chief_rabbit.skills.check_skill_requirement_list(patrol.pl_skill_constraints):
            return False
        
        if patrol.pl_trait_constraints and self.patrol_chief_rabbit.personality.trait not in patrol.pl_trait_constraints:
            return False
            
        return True

    def _filter_relationship(self, patrol:PatrolEvent):
        """
        Filter the incoming patrol list according to the relationship constraints, if there are constraints.

        """

        # filtering - relationship status
        # check if all are siblings
        if "siblings" in patrol.relationship_constraints:
            test_rabbit = self.patrol_rabbits[0]
            testing_rabbits = [rabbit for rabbit in self.patrol_rabbits if rabbit.ID != test_rabbit.ID]

            siblings = [test_rabbit.is_sibling(inter_rabbit) for inter_rabbit in testing_rabbits]
            if not all(siblings):
                return False
            
        # check if the rabbits are mates
        if "mates" in patrol.relationship_constraints:
            # First test if there is more then one rabbit
            if len(self.patrol_rabbits) == 1:
                return False
            
            # Then if rabbits don't have the needed number of mates. 
            if not all(len(i.mate) >= (len(self.patrol_rabbits) - 1) for i in self.patrol_rabbits):
                return False
            
            # Now the expensive test. We have to see if everyone is mates with each other
            # Hopefully the cheaper tests mean this is only needed on small patrols. 
            for x in combinations(self.patrol_rabbits, 2):
                if x[0].ID not in x[1].mate:
                    return False
                

        # check if the rabbits are in a parent/child relationship
        if "parent/child" in patrol.relationship_constraints:
            # it should be exactly two rabbits for a "parent/child" patrol
            if len(self.patrol_rabbits) != 2:
                return False
            # when there are two rabbits in the patrol, p_l and r_r are different rabbits per default
            if not self.patrol_chief_rabbit.is_parent(self.patrol_random_rabbit):
                return False

        # check if the rabbits are in a child/parent relationship
        if "child/parent" in patrol.relationship_constraints:
            # it should be exactly two rabbits for a "child/parent" patrol
            if len(self.patrol_rabbits) != 2:
                return False
            # when there are two rabbits in the patrol, p_l and r_r are different rabbits per default
            if not self.patrol_random_rabbit.is_parent(self.patrol_chief_rabbit):
                return False

        # filtering - relationship values
        # when there will be more relationship values or other tags, this should be updated
        value_types = ["romantic", "platonic", "dislike", "comfortable", "jealousy", "trust"]
        break_loop = False
        for v_type in value_types:
            patrol_id = patrol.patrol_id
            # first get all tags for the current value type
            tags = [constraint for constraint in patrol.relationship_constraints if v_type in constraint]

            # there is not such a tag for the current value type, check the next one
            if len(tags) == 0:
                continue

            # there should be only one value constraint for each value type
            elif len(tags) > 1:
                print(f"ERROR: patrol {patrol_id} has multiple relationship constraints for the value {v_type}.")
                break_loop = True
                break

            threshold = 0
            # try to extract the value/threshold from the text
            try:
                threshold = int(tags[0].split('_')[1])
            except Exception as e:
                print(
                    f"ERROR: patrol {patrol_id} with the relationship constraint for the value {v_type} follows not the formatting guidelines.")
                break_loop = True
                break

            if threshold > 100:
                print(
                    f"ERROR: patrol {patrol_id} has a relationship constraints for the value {v_type}, which is higher than the max value of a relationship.")
                break_loop = True
                break

            if threshold <= 0:
                print(
                    f"ERROR: patrol {patrol_id} has a relationship constraints for the value {v_type}, which is lower than the min value of a relationship or 0.")
                break_loop = True
                break

            # each rabbit has to have relationships with this relationship value above the threshold
            fulfilled = True
            for inter_rabbit in self.patrol_rabbits:
                rel_above_threshold = []
                patrol_rabbits_ids = [rabbit.ID for rabbit in self.patrol_rabbits]
                relevant_relationships = list(
                    filter(lambda rel: rel.rabbit_to.ID in patrol_rabbits_ids and rel.rabbit_to.ID != inter_rabbit.ID,
                           list(inter_rabbit.relationships.values())
                           )
                )

                # get the relationships depending on the current value type + threshold
                if v_type == "romantic":
                    rel_above_threshold = [i for i in relevant_relationships if i.romantic_love >= threshold]
                elif v_type == "platonic":
                    rel_above_threshold = [i for i in relevant_relationships if i.platonic_like >= threshold]
                elif v_type == "dislike":
                    rel_above_threshold = [i for i in relevant_relationships if i.dislike >= threshold]
                elif v_type == "comfortable":
                    rel_above_threshold = [i for i in relevant_relationships if i.comfortable >= threshold]
                elif v_type == "jealousy":
                    rel_above_threshold = [i for i in relevant_relationships if i.jealousy >= threshold]
                elif v_type == "trust":
                    rel_above_threshold = [i for i in relevant_relationships if i.trust >= threshold]

                # if the lengths are not equal, one rabbit has not the relationship value which is needed to another rabbit of the patrol
                if len(rel_above_threshold) + 1 != len(self.patrol_rabbits):
                    fulfilled = False
                    break

            if not fulfilled:
                break_loop = True
                break

        # if break is used in the loop, the condition are not fulfilled
        # and this patrol should not be added to the filtered list
        if break_loop:
            return False

        return True

    @staticmethod
    def decide_if_romantic(romantic_event, patrol_chief_rabbit, random_rabbit, patrol_owsla_rusasis:list) -> bool:
         # if no romance was available or the patrol lead and random rabbit aren't potential mates then use the normal event

        if not romantic_event:
            print("No romantic event")
            return False
        
        if "rom_two_apps" in romantic_event.tags:
            if len(patrol_owsla_rusasis) < 2:
                print('somehow, there are not enough owsla rusasis for romantic patrol')
                return False
            love1 = patrol_owsla_rusasis[0]
            love2 = patrol_owsla_rusasis[1]
        else:
            love1 = patrol_chief_rabbit
            love2 = random_rabbit
        
        if not love1.is_potential_mate(love2, for_love_interest=True) \
                and love1.ID not in love2.mate:
            print('not a potential mate or current mate')
            return False 
        

        print("attempted romance between:", love1.name, love2.name)
        chance_of_romance_patrol = game.config["patrol_generation"]["chance_of_romance_patrol"]

        if get_personality_compatibility(love1,
                                         love2) is True or love1.ID in love2.mate:
            chance_of_romance_patrol -= 10
        else:
            chance_of_romance_patrol += 10
        
        values = ["romantic", "platonic", "dislike", "admiration", "comfortable", "jealousy", "trust"]
        for val in values:
            value_check = check_relationship_value(love1, love2, val)
            if val in ["romantic", "platonic", "admiration", "comfortable", "trust"] and value_check >= 20:
                chance_of_romance_patrol -= 1
            elif val in ["dislike", "jealousy"] and value_check >= 20:
                chance_of_romance_patrol += 2
        if chance_of_romance_patrol <= 0:
            chance_of_romance_patrol = 1
        print("final romance chance:", chance_of_romance_patrol)
        return not int(random.random() * chance_of_romance_patrol)

    def _filter_patrols(self, possible_patrols: List[PatrolEvent], biome:str, current_season:str, patrol_type:str):
        filtered_patrols = []
        romantic_patrols = []
        special_date = get_special_date()
        # This make sure general only gets harvesting, border, or training patrols
		# chose fix type will make it not depending on the content amount
        if patrol_type == "general":
            patrol_type = random.choice(["harvesting", "border", "training"])

        # makes sure that it grabs patrols in the correct biomes, season, with the correct number of rabbits
        for patrol in possible_patrols:
            if not self._check_constraints(patrol):
                continue
            
            # Don't check for repeat patrols if ensure_patrol_id is being used. 
            if not isinstance(game.config["patrol_generation"]["debug_ensure_patrol_id"], str) and \
                    patrol.patrol_id in self.used_patrols:
                continue

            # filtering for dates
            if contains_special_date_tag(patrol.tags):
                if not special_date or special_date.patrol_tag not in patrol.tags:
                    continue

            if not (patrol.min_rabbits <= len(self.patrol_rabbits) <= patrol.max_rabbits):
                continue
        
            flag = False
            for sta, num in patrol.min_max_status.items():
                if len(num) != 2:
                    print(f"Issue with status limits: {patrol.patrol_id}")
                    continue
                
                if not (num[0] <= self.patrol_statuses.get(sta, -1) <= num[1]):
                    flag = True
                    break
            if flag:
                continue
            
            if biome not in patrol.biome and "Any" not in patrol.biome:
                continue
            if current_season not in patrol.season and "Any" not in patrol.season:
                continue

            if 'harvesting' not in patrol.types and patrol_type == 'harvesting':
                continue
            elif 'border' not in patrol.types and patrol_type == 'border':
                continue
            elif 'training' not in patrol.types and patrol_type == 'training':
                continue
            elif 'herb_gathering' not in patrol.types and patrol_type == 'med':
                continue

            # cruel season tag check
            if "cruel_season" in patrol.tags:
                if game.warren.game_mode != 'cruel_season':
                    continue

            if "romantic" in patrol.tags:
                romantic_patrols.append(patrol)
            else:
                filtered_patrols.append(patrol)

        # make sure the harvesting patrols are balanced
        if patrol_type == 'harvesting':
            filtered_patrols = self.balance_harvesting(filtered_patrols)

        return filtered_patrols, romantic_patrols

    def get_filtered_patrols(self, possible_patrols, biome, current_season, patrol_type):
        
        filtered_patrols, romantic_patrols = self._filter_patrols(possible_patrols, biome, current_season,
                                                                  patrol_type)
        
        if not filtered_patrols:
            print('No normal patrols possible. Repeating filter with used patrols cleared.')
            self.used_patrols.clear()
            print('used patrols cleared', self.used_patrols)
            filtered_patrols, romantic_patrols = self._filter_patrols(possible_patrols, biome,
                                                                      current_season, patrol_type)    
        
        return filtered_patrols, romantic_patrols

    def generate_patrol_events(self, patrol_dict):
        all_patrol_events = []
        for patrol in patrol_dict:
            patrol_event = PatrolEvent(
                patrol_id=patrol.get("patrol_id"),
                biome=patrol.get("biome"),
                season=patrol.get("season"),
                tags=patrol.get("tags"),
                types=patrol.get("types"),
                intro_text=patrol.get("intro_text"),
                patrol_art=patrol.get("patrol_art"),
                patrol_art_clean=patrol.get("patrol_art_clean"),
                success_outcomes=PatrolOutcome.generate_from_info(patrol.get("success_outcomes")),
                fail_outcomes=PatrolOutcome.generate_from_info(patrol.get("fail_outcomes"), success=False),
                decline_text=patrol.get("decline_text"),
                chance_of_success=patrol.get("chance_of_success"),
                min_rabbits=patrol.get("min_rabbits", 1),
                max_rabbits=patrol.get("max_rabbits", 6),
                min_max_status=patrol.get("min_max_status"),
                antag_success_outcomes=PatrolOutcome.generate_from_info(patrol.get("antag_success_outcomes"), antagonize=True),
                antag_fail_outcomes=PatrolOutcome.generate_from_info(patrol.get("antag_fail_outcomes"), success=False, 
                                                                     antagonize=True),
                relationship_constraints=patrol.get("relationship_constraint"),
                pl_skill_constraints=patrol.get("pl_skill_constraint"),
                pl_trait_constraints=patrol.get("pl_trait_constraints")
            )

            all_patrol_events.append(patrol_event)

        return all_patrol_events

    def determine_outcome(self, antagonize=False) -> Tuple[str]:
        
        if self.patrol_event is None:
            return
        
        # First Step - Filter outcomes and pick a fail and success outcome
        success_outcomes = self.patrol_event.antag_success_outcomes if antagonize else \
                           self.patrol_event.success_outcomes
        fail_outcomes = self.patrol_event.antag_fail_outcomes if antagonize else \
                        self.patrol_event.fail_outcomes
                        
        # Filter the outcomes. Do this only once - this is also where stat rabbits are determined
        success_outcomes = PatrolOutcome.prepare_allowed_outcomes(success_outcomes, self)
        fail_outcomes = PatrolOutcome.prepare_allowed_outcomes(fail_outcomes, self)
        
        # Choose a success and fail outcome
        chosen_success = choices(success_outcomes, weights=[x.weight for x in success_outcomes])[0]
        chosen_failure = choices(fail_outcomes, weights=[x.weight for x in fail_outcomes])[0]
        
        final_event, success = self.calculate_success(chosen_success, chosen_failure)
        
        print(f"PATROL ID: {self.patrol_event.patrol_id} | SUCCESS: {success}")        
        
        # Run the chosen outcome
        return final_event.execute_outcome(self)
        
    def calculate_success(self, success_outcome: PatrolOutcome, fail_outcome: PatrolOutcome) -> Tuple[PatrolOutcome, bool]:
        """Returns both the chosen event, and a boolian that's True if success, and False is fail."""
        
        patrol_size = len(self.patrol_rabbits)
        total_exp = sum([x.experience for x in self.patrol_rabbits])
        gm_modifier = game.config["patrol_generation"][f"{game.warren.game_mode}_difficulty_modifier"]
        
        exp_adustment = (1 + 0.10 * patrol_size) * total_exp / (
                patrol_size * gm_modifier * 2)
        
        success_chance = self.patrol_event.chance_of_success + int(exp_adustment)
        success_chance = min(success_chance, 90)
        
        # Now, apply success and fail skill 
        print('starting chance:', self.patrol_event.chance_of_success, "| EX_updated chance:", success_chance)
        skill_updates = ""
        
        # Skill and trait stuff
        for kitty in self.patrol_rabbits:
            hits = kitty.skills.check_skill_requirement_list(success_outcome.stat_skill)
            success_chance += hits * game.config["patrol_generation"]["win_stat_rabbit_modifier"] 
            
            hits = kitty.skills.check_skill_requirement_list(fail_outcome.stat_skill)
            success_chance -= hits * game.config["patrol_generation"]["fail_stat_rabbit_modifier"]
            
    
            if kitty.personality.trait in success_outcome.stat_trait:
                success_chance += game.config["patrol_generation"]["win_stat_rabbit_modifier"]
                
            if kitty.personality.trait in fail_outcome.stat_trait:
                success_chance += game.config["patrol_generation"]["fail_stat_rabbit_modifier"]

            skill_updates += f"{kitty.name} updated chance to {success_chance} | "
        
        if success_chance >= 120:
            success_chance = 115
            skill_updates += "success chance over 120, updated to 115"
        
        print(skill_updates)
        
        success = int(random.random() * 120) < success_chance
        return (success_outcome if success else fail_outcome, success)
        
    def update_resources(self, biome_dir, leaf):
        resource_dir = "resources/dicts/patrols/"
        # HARVESTING #
        self.HARVESTING_SZN = None
        with open(f"{resource_dir}{biome_dir}harvesting/{leaf}.json", 'r', encoding='ascii') as read_file:
            self.HARVESTING_SZN = ujson.loads(read_file.read())
        self.HARVESTING = None
        with open(f"{resource_dir}{biome_dir}harvesting/any.json", 'r', encoding='ascii') as read_file:
            self.HARVESTING = ujson.loads(read_file.read())
        # BORDER #
        self.BORDER_SZN = None
        with open(f"{resource_dir}{biome_dir}border/{leaf}.json", 'r', encoding='ascii') as read_file:
            self.BORDER_SZN = ujson.loads(read_file.read())
        self.BORDER = None
        with open(f"{resource_dir}{biome_dir}border/any.json", 'r', encoding='ascii') as read_file:
            self.BORDER = ujson.loads(read_file.read())
        # TRAINING #
        self.TRAINING_SZN = None
        with open(f"{resource_dir}{biome_dir}training/{leaf}.json", 'r', encoding='ascii') as read_file:
            self.TRAINING_SZN = ujson.loads(read_file.read())
        self.TRAINING = None
        with open(f"{resource_dir}{biome_dir}training/any.json", 'r', encoding='ascii') as read_file:
            self.TRAINING = ujson.loads(read_file.read())
        # MED #
        self.MEDRABBIT_SZN = None
        with open(f"{resource_dir}{biome_dir}med/{leaf}.json", 'r', encoding='ascii') as read_file:
            self.MEDRABBIT_SZN = ujson.loads(read_file.read())
        self.MEDRABBIT = None
        with open(f"{resource_dir}{biome_dir}med/any.json", 'r', encoding='ascii') as read_file:
            self.MEDRABBIT = ujson.loads(read_file.read())
        # NEW RABBIT #
        self.NEW_RABBIT = None
        with open(f"{resource_dir}new_rabbit.json", 'r', encoding='ascii') as read_file:
            self.NEW_RABBIT = ujson.loads(read_file.read())
        self.NEW_RABBIT_HOSTILE = None
        with open(f"{resource_dir}new_rabbit_hostile.json", 'r', encoding='ascii') as read_file:
            self.NEW_RABBIT_HOSTILE = ujson.loads(read_file.read())
        self.NEW_RABBIT_WELCOMING = None
        with open(f"{resource_dir}new_rabbit_welcoming.json", 'r', encoding='ascii') as read_file:
            self.NEW_RABBIT_WELCOMING = ujson.loads(read_file.read())
        # OTHER WARREN #
        self.OTHER_WARREN = None
        with open(f"{resource_dir}other_warren.json", 'r', encoding='ascii') as read_file:
            self.OTHER_WARREN = ujson.loads(read_file.read())
        self.OTHER_WARREN_ALLIES = None
        with open(f"{resource_dir}other_warren_allies.json", 'r', encoding='ascii') as read_file:
            self.OTHER_WARREN_ALLIES = ujson.loads(read_file.read())
        self.OTHER_WARREN_HOSTILE = None
        with open(f"{resource_dir}other_warren_hostile.json", 'r', encoding='ascii') as read_file:
            self.OTHER_WARREN_HOSTILE = ujson.loads(read_file.read())
        self.DISASTER = None
        with open(f"{resource_dir}disaster.json", 'r', encoding='ascii') as read_file:
            self.DISASTER = ujson.loads(read_file.read())
        # sighing heavily as I add general patrols back in
        self.HARVESTING_GEN = None
        with open(f"{resource_dir}general/harvesting.json", 'r', encoding='ascii') as read_file:
            self.HARVESTING_GEN = ujson.loads(read_file.read())
        self.BORDER_GEN = None
        with open(f"{resource_dir}general/border.json", 'r', encoding='ascii') as read_file:
            self.BORDER_GEN = ujson.loads(read_file.read())
        self.TRAINING_GEN = None
        with open(f"{resource_dir}general/training.json", 'r', encoding='ascii') as read_file:
            self.TRAINING_GEN = ujson.loads(read_file.read())
        self.MEDRABBIT_GEN = None
        with open(f"{resource_dir}general/medrabbit.json", 'r', encoding='ascii') as read_file:
            self.MEDRABBIT_GEN = ujson.loads(read_file.read())

    def balance_harvesting(self, possible_patrols: list):
        """Filter the incoming harvesting patrol list to balance the different kinds of harvesting patrols.
        With this filtering, there should be more prey possible patrols.

            Parameters
            ----------
            possible_patrols : list
                list of patrols which should be filtered

            Returns
            ----------
            filtered_patrols : list
                list of patrols which is filtered
        """
        filtered_patrols = []

        # get first what kind of prey size which will be chosen
        biome = game.warren.biome
        season = game.warren.current_season
        possible_prey_size = []
        idx = 0
        prey_size = ["very_small", "small", "medium", "large", "huge"]
        for amount in PATROL_BALANCE[biome][season]:
            possible_prey_size.extend(repeat(prey_size[idx],amount))
            idx += 1
        chosen_prey_size = choice(possible_prey_size)
        print(f"chosen filter prey size: {chosen_prey_size}")

        # filter all possible patrol depending on the needed prey size
        for patrol in possible_patrols:
            for adaption, needed_weight in PATROL_WEIGHT_ADAPTION.items():
                if needed_weight[0] <= patrol.weight < needed_weight[1]:
                    # get the amount of class sizes which can be increased
                    increment = int(adaption.split("_")[0])
                    new_idx = prey_size.index(chosen_prey_size) + increment
                    # check that the increment does not lead to a overflow
                    new_idx = new_idx if new_idx <= len(chosen_prey_size) else len(chosen_prey_size)
                    chosen_prey_size = prey_size[new_idx]

            # now count the outcomes + prey size
            prey_types = {}
            for outcome in patrol.success_outcomes:
                # ignore skill or trait outcomes
                if outcome.stat_trait or outcome.stat_skill:
                    continue
                if outcome.prey:
                    if outcome.prey[0] in prey_types:
                        prey_types[outcome.prey[0]] += 1
                    else:
                        prey_types[outcome.prey[0]] = 1
            
            # get the prey size with the most outcomes
            most_prey_size = ""
            max_occurrences = 0
            for prey_size, amount in prey_types.items():
                if amount >= max_occurrences and most_prey_size != chosen_prey_size:
                    most_prey_size = prey_size

            if chosen_prey_size == most_prey_size:
                filtered_patrols.append(patrol)

        # if the filtering results in an empty list, don't filter and return whole possible patrols
        if len(filtered_patrols) <= 0:
            print("---- WARNING ---- filtering to balance out the harvesting, didn't work.")
            filtered_patrols = possible_patrols
        return filtered_patrols

    def get_patrol_art(self) -> pygame.Surface:
        """Return's patrol art surface """
        if not self.patrol_event or not isinstance(self.patrol_event.patrol_art, str):
            return pygame.Surface((600, 600), flags=pygame.SRCALPHA)
        
        root_dir = "resources/images/patrol_art/"
        
        if game.settings.get("gore") and self.patrol_event.patrol_art_clean:
            file_name = self.patrol_event.patrol_art_clean
        else:
            file_name = self.patrol_event.patrol_art
            
        
        if not isinstance(file_name, str) or not path_exists(f"{root_dir}{file_name}.png"):
            if "herb_gathering" in self.patrol_event.types:
                file_name = 'med'
            elif "harvesting" in self.patrol_event.types:
                file_name = 'hunt'
            elif "border" in self.patrol_event.types:
                file_name = 'bord'
            else:
                file_name = 'train'
            
            file_name = f"{file_name}_general_intro"
            
        return pygame.image.load(f"{root_dir}{file_name}.png")
    
    def process_text(self, text, stat_rabbit:Rabbit) -> str:
        """Processes text """

        vowels = ['A', 'E', 'I', 'O', 'U']
        if not text:
            text = 'This should not appear, report as a bug please!'

        replace_dict = {
            "p_l": (str(self.patrol_chief_rabbit.name), choice(self.patrol_chief_rabbit.pronouns)),
            "r_r": (str(self.patrol_random_rabbit.name), choice(self.patrol_random_rabbit.pronouns)),
        }

        other_rabbits = [i for i in self.patrol_rabbits if i not in [self.patrol_chief_rabbit, self.patrol_random_rabbit]]
        if len(other_rabbits) >= 1:
            replace_dict['o_c1'] = (str(other_rabbits[0].name),
                                    choice(other_rabbits[0].pronouns))
        if len(other_rabbits) >= 2:
            replace_dict['o_c2'] = (str(other_rabbits[1].name),
                                    choice(other_rabbits[1].pronouns))
        if len(other_rabbits) >= 3:
            replace_dict['o_c3'] = (str(other_rabbits[2].name),
                                    choice(other_rabbits[2].pronouns))
        if len(other_rabbits) == 4:
            replace_dict['o_c4'] = (str(other_rabbits[3].name),
                                    choice(other_rabbits[3].pronouns))

        # New Rabbits
        for i, new_rabbits in enumerate(self.new_rabbits):
            if len(new_rabbits) == 1:
                names = str(new_rabbits[0].name)
                pronoun = choice(new_rabbits[0].pronouns)
            elif len(new_rabbits) == 1:
                names = f"{new_rabbits[0].name} and {new_rabbits[1].name}"
                pronoun = Rabbit.default_pronouns[0] # They/them for muliple rabbits
            else:
                names = ", ".join([str(x.name) for x in new_rabbits[:-1]]) +  f", and {new_rabbits[1].name}"
                pronoun = Rabbit.default_pronouns[0] # They/them for muliple rabbits
            
            replace_dict[f"n_c:{i}"] = (names, pronoun)
        
        if len(self.patrol_owsla_rusasis) > 0:
            replace_dict["app1"] = (str(self.patrol_owsla_rusasis[0].name), choice(self.patrol_owsla_rusasis[0].pronouns))
        if len(self.patrol_owsla_rusasis) > 1:
            replace_dict["app2"] = (str(self.patrol_owsla_rusasis[1].name), choice(self.patrol_owsla_rusasis[1].pronouns))
        if len(self.patrol_owsla_rusasis) > 2:
            replace_dict["app3"] = (str(self.patrol_owsla_rusasis[2].name), choice(self.patrol_owsla_rusasis[2].pronouns))
        if len(self.patrol_owsla_rusasis) > 3:
            replace_dict["app4"] = (str(self.patrol_owsla_rusasis[3].name), choice(self.patrol_owsla_rusasis[3].pronouns))
        if len(self.patrol_owsla_rusasis) > 4:
            replace_dict["app5"] = (str(self.patrol_owsla_rusasis[4].name), choice(self.patrol_owsla_rusasis[4].pronouns))
        if len(self.patrol_owsla_rusasis) > 5:
            replace_dict["app6"] = (str(self.patrol_owsla_rusasis[5].name), choice(self.patrol_owsla_rusasis[5].pronouns))

        if stat_rabbit:
            replace_dict['s_c'] = (str(stat_rabbit.name),
                                choice(stat_rabbit.pronouns))

        text = process_text(text, replace_dict)
        text = adjust_prey_abbr(text)

        other_warren_name = self.other_warren.name
        s = 0
        for x in range(text.count('o_c_n')):
            if 'o_c_n' in text:
                for y in vowels:
                    if str(other_warren_name).startswith(y):
                        modify = text.split()
                        pos = 0
                        if 'o_c_n' in modify:
                            pos = modify.index('o_c_n')
                        if "o_c_n's" in modify:
                            pos = modify.index("o_c_n's")
                        if 'o_c_n.' in modify:
                            pos = modify.index('o_c_n.')
                        if modify[pos - 1] == 'a':
                            modify.remove('a')
                            modify.insert(pos - 1, 'an')
                        text = " ".join(modify)
                        break

        text = text.replace('o_c_n', str(other_warren_name) + 'Warren')

        warren_name = game.warren.name
        s = 0
        pos = 0
        for x in range(text.count('c_n')):
            if 'c_n' in text:
                for y in vowels:
                    if str(warren_name).startswith(y):
                        modify = text.split()
                        if 'c_n' in modify:
                            pos = modify.index('c_n')
                        if "c_n's" in modify:
                            pos = modify.index("c_n's")
                        if 'c_n.' in modify:
                            pos = modify.index('c_n.')
                        if modify[pos - 1] == 'a':
                            modify.remove('a')
                            modify.insert(pos - 1, 'an')
                        text = " ".join(modify)
                        break

        text = text.replace('c_n', str(game.warren.name) + 'Warren')

        # Prey lists for forest random prey patrols
        fst_tinyprey_singlular = ['daisy', 'marigold', 'peach leaf', 'lettuce', 'turnip',
                                'apple leaf', 'creepvine', 'wood bark', 'cherry leaf', 'shrubleaf',
                                'dandelion', 'tomato', 'cabbage', 'big beetle', 'grass clump',
                                'moss', 'tallgrass', 'tree shoot', 'rose', ]
        text = text.replace('f_tp_s', str(fst_tinyprey_singlular))

        fst_tinyprey_plural = ['daisies', 'dandelions', 'sweetgrass', 'clover', 'cabbages', 'lettuces', 'hay', 'grasses',
                            'hay', 'sweetgrass', 'wood bark', 'leaves', 'spruce needles', 'fir needles',
                            'grasses', 'drygrass', 'shrub leaves', ]
        text = text.replace('f_tp_p', str(fst_tinyprey_plural))

        fst_midprey_singlular = ['root', 'bud', 'wood bark', 'willow branch', 'jasmine',
                                'bean', 'broccoli', 'kale', 'raspberry leaf', 'spinach',
                                'sunflower', 'alfalfa', 'blueberry', 'raspberry', 'strawberry', ]
        text = text.replace('f_mp_s', str(fst_midprey_singlular))

        fst_midprey_plural = ['roots', 'buds', 'wood bark', 'willow branches',
                            'jasmine', 'beans', 'broccoli', 'kale', 'strawberries',
                            'sunflowers', 'blueberries', 'raspberries', ]
        text = text.replace('f_mp_p', str(fst_midprey_plural))

        text, senses, list_type = find_special_list_types(text)
        if list_type:
            sign_list = get_special_snippet_list(list_type, amount=randint(1, 3), sense_groups=senses)
            text = text.replace(list_type, str(sign_list))

        return text
    # ---------------------------------------------------------------------------- #
    #                                   Handlers                                   #
    # ---------------------------------------------------------------------------- #

    def handle_history(self, rabbit, condition=None, possible=False, scar=False, death=False):
        """
        this handles the scar and death history of the rabbit
        :param rabbit: the rabbit gaining the history
        :param condition: if the history is related to a condition, include its name here
        :param possible: if you want the history added to the possible scar/death then set this to True, defaults to False
        :param scar: if you want the scar history added set this to True, default is False
        :param death: if you want the death history added set this to True, default is False
        """
        if not self.patrol_event.history_text:
            print(
                f"WARNING: No history found for {self.patrol_event.patrol_id}, it may not need one but double check please!")
        if scar and "scar" in self.patrol_event.history_text:
            adjust_text = self.patrol_event.history_text['scar']
            adjust_text = adjust_text.replace("r_r", str(rabbit.name))
            adjust_text = adjust_text.replace("o_c_n", str(self.other_warren.name))
            if possible:
                History.add_possible_history(rabbit, condition=condition, scar_text=adjust_text)
            else:
                History.add_scar(rabbit, adjust_text)
        if death:
            if rabbit.status == 'chief_rabbit':
                if "lead_death" in self.patrol_event.history_text:
                    adjust_text = self.patrol_event.history_text['lead_death']
                    adjust_text = adjust_text.replace("r_r", str(rabbit.name))
                    adjust_text = adjust_text.replace("o_c_n", str(self.other_warren.name))
                    if possible:
                        History.add_possible_history(rabbit, condition=condition, death_text=adjust_text)
                    else:
                        History.add_death(rabbit, adjust_text)
            else:
                if "reg_death" in self.patrol_event.history_text:
                    adjust_text = self.patrol_event.history_text['reg_death']
                    adjust_text = adjust_text.replace("r_r", str(rabbit.name))
                    adjust_text = adjust_text.replace("o_c_n", str(self.other_warren.name))
                    if possible:
                        History.add_possible_history(rabbit, condition=condition, death_text=adjust_text)
                    else:
                        History.add_death(rabbit, adjust_text)



# ---------------------------------------------------------------------------- #
#                               PATROL CLASS END                               #
# ---------------------------------------------------------------------------- #

PATROL_WEIGHT_ADAPTION = game.prey_config["patrol_weight_adaption"]
PATROL_BALANCE = game.prey_config["patrol_balance"]

# ---------------------------------------------------------------------------- #
#                              GENERAL INFORMATION                             #
# ---------------------------------------------------------------------------- #

"""
More Documentation: https://docs.google.com/document/d/1Vuyclyd40mjG7PFXtl0852DlkcxIiyi_uIWxyi41sbI/edit?usp=sharing


Patrol Template.
This is a good starting point for writing your own patrols. 

{
    "patrol_id": "some_unique_id",
    "biome": [],
    "season": [],
    "types": [],
    "tags": [],
    "patrol_art": null,
    "patrol_art_clean": null,
    "min_rabbits": 1,
    "max_rabbits": 6,
    "min_max_status": {
        "owsla rusasi": [0, 6],
        "healer rusasi": [0, 6],
        "healer": [0, 6],
        "captain": [0, 6]
        "owsla": [0, 6],
        "leader": [0, 6],
        "healer rabbits": [0, 6],
        "normal_adult": [1, 6],
        "all owsla rusasis": [1, 6]
    }
    "weight": 20,
    "chance_of_success": 50,
    "relationship_constraint": [],
    "pl_skill_constraint": [],
    "intro_text": "The patrol heads out.",
    "decline_text": "And they head right back!",
    "success_outcomes": [
        {
            SEE OUTCOME BLOCK TEMPLATE
        },
        {
            SEE OUTCOME BLOCK TEMPLATE
            
        },
    ],
    "fail_outcomes": [
        {
            SEE OUTCOME BLOCK TEMPLATE
        },
        {
            SEE OUTCOME BLOCK TEMPLATE
            
        },
    ],

    "antag_success_outcomes": [
        {
            SEE OUTCOME BLOCK TEMPLATE
        },
        {
            SEE OUTCOME BLOCK TEMPLATE
            
        },
    ],

    "antag_fail_outcomes": [
        {
            SEE OUTCOME BLOCK TEMPLATE
        },
        {
            SEE OUTCOME BLOCK TEMPLATE
            
        },
    ],

}



----------------------------------------------------------------------------------------

Outcome Block Template.
This is a good starting point for writing your own outcomes.
{
    "text": "The raw displayed outcome text.",
    "exp": 0,
    "weight": 20,
    "stat_skill": [],
    "stat_trait": [],
    "can_have_stat": [],
    "lost_rabbits": [],
    "dead_rabbits": [],
    "outsider_rep": null,
    "other_warren_rep": null,
    "injury": [
        {
            "rabbits": [],
            "injuries": [],
            "scars": [],
            "no_results": false
        },
        {
            "rabbits": [],
            "injuries": [],
            "scars": [],
            "no_results": false
        }
    ]
    "history_text": {
        "reg_death": "m_c died while on a patrol.",
        "leader_death": "died on patrol",
        "scar": "m_c was scarred on patrol",
    }
    "relationships": [
        {
            "rabbits_to": [],
            "rabbits_from": [],
            "mutual": false
            "values": [],
            "amount": 5
        },	
        {
            "rabbits_to": [],
            "rabbits_from": [],
            "mutual": false
            "values": [],
            "amount": 5
        }
    ],
    "new_rabbit" [
        [],
        []
    ],

}

"""
