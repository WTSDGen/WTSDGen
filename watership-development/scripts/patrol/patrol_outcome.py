#!/usr/bin/env python3
# -*- coding: ascii -*-
import random
from random import choice, randint, choices
from typing import List, Dict, Union, TYPE_CHECKING
import re
import pygame
from os.path import exists as path_exists

if TYPE_CHECKING:
    from scripts.patrol.patrol import Patrol

from scripts.rabbit.history import History
from scripts.warren import HERBS
from scripts.utility import (
    change_warren_relations,
    change_warren_reputation,
    change_relationship_values, create_new_rabbit,
)
from scripts.game_structure.game_essentials import game
from scripts.rabbit.skills import SkillPath
from scripts.rabbit.rabbits import Rabbit, ILLNESSES, INJURIES, PERMANENT, BACKSTORIES
from scripts.rabbit.pelts import Pelt
from scripts.rabbit_relations.relationship import Relationship
from scripts.warren_resources.freshkill import ADDITIONAL_PREY, PREY_REQUIREMENT, HARVESTER_EXP_BONUS, HARVESTER_BONUS, \
    FRESHKILL_ACTIVE



class PatrolOutcome():
    """ Holds all info on patrol outcomes, and methods to handle that outcome """
    
    def __init__(self,
            success:bool = True,
            antagonize:bool = False,
            text: str = None, 
            weight: int = 20, 
            exp: int = 0, 
            stat_trait: List[str] = None,
            stat_skill: List[str] = None,
            can_have_stat: List[str] = None,
            dead_rabbits: List[str] = None,
            lost_rabbits: List[str] = None,
            injury: List[Dict] = None,
            history_reg_death: str = None,
            history_threarah_death: str = None,
            history_scar: str = None,
            new_rabbit: List[List[str]] = None,
            herbs: List[str] = None,
            prey: List[str] = None,
            outsider_rep: Union[int, None] = None,
            other_warren_rep: Union[int, None] = None,
            relationship_effects: List[dict] = None,
            relationship_constaints: List[str] = None,
            outcome_art: Union[str, None] = None,
            outcome_art_clean: Union[str, None] = None,
            stat_rabbit: Rabbit = None):
        
        self.success = success
        self.antagonize = antagonize
        self.text = text if text is not None else ""
        self.weight = weight
        self.exp = exp
        self.stat_trait = stat_trait if stat_trait is not None else []
        self.stat_skill = stat_skill if stat_skill is not None else []
        self.can_have_stat = can_have_stat if can_have_stat is not None else []
        self.dead_rabbits = dead_rabbits if dead_rabbits is not None else []
        self.lost_rabbits = lost_rabbits if lost_rabbits is not None else []
        self.injury = injury if injury is not None else []
        self.history_reg_death = history_reg_death if history_reg_death is not None else \
                                 "m_c died on patrol."
        self.history_threarah_death = history_threarah_death if history_threarah_death is not None else \
                                    "died on patrol."
        self.history_scar = history_scar if history_scar is not None else "m_c was scarred on patrol."
        self.new_rabbit = new_rabbit if new_rabbit is not None else []
        self.herbs = herbs if herbs is not None else []
        self.prey = prey if prey is not None else []
        self.outsider_rep = outsider_rep
        self.other_warren_rep = other_warren_rep
        self.relationship_effects = relationship_effects if relationship_effects is not None else []
        self.relationship_constaints = relationship_constaints if relationship_constaints is not None else []
        self.outcome_art = outcome_art
        self.outcome_art_clean = outcome_art_clean
        
        # This will hold the stat rabbit, for filtering purposes
        self.stat_rabbit = stat_rabbit 
    
    @staticmethod
    def prepare_allowed_outcomes(outcomes: List['PatrolOutcome'], patrol: 'Patrol') -> List['PatrolOutcome']:
        """Takes a list of patrol outcomes, and returns those which are possible. If "special" events, gated
        by stat rabbits or relationships, are possible, this function returns only those. Stat rabbits are also determined here. """
    
        # Determine which outcomes are possible 
        reg_outcomes = []
        special_outcomes = []
        for out in outcomes:
            
            # We want to gather special (ie, gated with stat or relationship constaints)
            # outcomes seperatly, so we can ensure that those occur if possible. 
            special = False
           
            if (out.stat_skill or out.stat_trait):
                special = True
                out._get_stat_rabbit(patrol)
                if not isinstance(out.stat_rabbit, Rabbit):
                    continue
             
            # TODO: outcome relationship constraints   
            #if not patrol._satify_relationship_constaints(patrol, out.relationship_constaints):
            #    continue
            #elif out.relationship_constaints:
            #    special = True
            
            if special:
                special_outcomes.append(out)
            else:
                reg_outcomes.append(out)
        
        # If there are somehow no possible outcomes, add a single default
        # outcome. Patrols should be written so this never has to occur
        if not (special_outcomes or reg_outcomes):
            reg_outcomes.append(
                PatrolOutcome(
                    text="There's nothing here, and that's a problem. Please report! ",
                )
            )
            
        return special_outcomes if special_outcomes else reg_outcomes
            
    @staticmethod
    def generate_from_info(info: List[dict], success:bool=True, antagonize:bool=False) -> List['PatrolOutcome']:
        """Factory method generates a list of PatrolOutcome objects based on the dicts"""
        
        outcome_list = []
        
        if not isinstance(info, list):
            return outcome_list
        
        for _d in info:
            outcome_list.append( 
                PatrolOutcome(
                    success=success,
                    antagonize=antagonize,
                    text=_d.get("text"),
                    weight=_d.get("weight"),
                    exp=_d.get("exp"),
                    stat_skill=_d.get("stat_skill"),
                    stat_trait=_d.get("stat_trait"),
                    can_have_stat=_d.get("can_have_stat"),
                    dead_rabbits=_d.get("dead_rabbits"),
                    injury=_d.get("injury"),
                    lost_rabbits=_d.get("lost_rabbits"),
                    history_threarah_death=_d["history_text"].get("threarah_death") if \
                                        isinstance(_d.get("history_text"), dict) else None,
                    history_reg_death=_d["history_text"].get("reg_death") if  
                                    isinstance(_d.get("history_text"), dict) else None,
                    history_scar=_d["history_text"].get("scar") if  
                                isinstance(_d.get("history_text"), dict) else None,
                    new_rabbit=_d.get("new_rabbit"),
                    herbs=_d.get("herbs"),
                    prey=_d.get("prey"),
                    outsider_rep=_d.get("outsider_rep"),
                    other_warren_rep=_d.get("other_warren_rep"),
                    relationship_effects=_d.get("relationships"),
                    relationship_constaints=_d.get("relationship_constraint"),
                    outcome_art=_d.get("art"),
                    outcome_art_clean=_d.get("art_clean")
                )
            )
        
        return outcome_list

    def execute_outcome(self, patrol:'Patrol') -> tuple:
        """ Excutes the outcome. Returns a tuple with the final outcome text, the results text, and any outcome art
        format: (Outcome text, results text, outcome art (might be None))
        """
        
        results = []
        
        # This order is important. 
        results.append(self._handle_new_rabbits(patrol))
        results.append(self._handle_death(patrol))
        results.append(self._handle_lost(patrol))
        results.append(self._handle_condition_and_scars(patrol))
        results.append(self._handle_relationship_changes(patrol))
        results.append(self._handle_rep_changes(patrol))
        results.append(self._handle_other_warren_relations(patrol))
        results.append(self._handle_prey(patrol))
        results.append(self._handle_herbs(patrol))
        results.append(self._handle_exp(patrol))
        results.append(self._handle_mentor_app(patrol))
        
        # Filter out empty results strings
        results = [x for x in results if x]
        
        processed_text = patrol.process_text(self.text, self.stat_rabbit)
        
        print("PATROL END -----------------------------------------------------")
        
        return (processed_text, " ".join(results), self.get_outcome_art())
    
    def _allowed_stat_rabbit_specfic(self, kitty:Rabbit, patrol:'Patrol', allowed_specfic) -> bool:
        """Helper that handled specfic stat rabbit requriments. """

        if "any" in allowed_specfic:
            # Special allowed_specfic that allows all. 
            return True
        
        # With allowed_specfic empty, that means the stat can can be anyone that's not patrol threarah
        # or stat rabbit. This can
        if not allowed_specfic or "no_pl_rc" in allowed_specfic:
            if kitty in (patrol.patrol_threarah, patrol.patrol_random_rabbit):
                return False
            return True
        
        # Otherwise, check to see if the rabbit matched any of the specfic rabbits
        if "p_l" in allowed_specfic and kitty == patrol.patrol_threarah:
            return True
        if "r_r" in allowed_specfic and kitty == patrol.patrol_random_rabbit:
            return True
        if "app1" in allowed_specfic and len(patrol.patrol_apprentices) >= 1 and \
                kitty == patrol.patrol_apprentices[0]:
            return True
        if "app2" in allowed_specfic and len(patrol.patrol_apprentices) >= 2 and \
                kitty == patrol.patrol_apprentices[1]:
            return True
        
        return False
    
    def _get_stat_rabbit(self, patrol: 'Patrol') -> bool:
        """Sets the stat rabbit. Returns true if a stat rabbit was found, and False is a stat rabbit was not found """
        
        print("---")
        print(f"Finding stat rabbit. Outcome Type: Success = {self.success}, Antag = {self.antagonize}")
        print(f"Can Have Stat: {self.can_have_stat}")
        
        # Grab any specfic stat rabbit requirements: 
        allowed_specfic = [x for x in self.can_have_stat if x in 
                           ("r_r", "p_l", "app1", "app2", "any", "not_pl_rc")]
        
        # Special default behavior for patrols less than two rabbits.
        # Patrol threarah is the only one allowed to be stat_rabbit in patrols equal to or less than than two rabbits 
        if not allowed_specfic and len(patrol.patrol_rabbits) <= 2:
            allowed_specfic = ["p_l"]

        
        possible_stat_rabbits = []
        for kitty in patrol.patrol_rabbits:
            # First, the blanet requirments
            if "app" in self.can_have_stat \
                    and kitty.status not in ['young rabbit', "healer rusasi"]:
                continue
            
            if "adult" in self.can_have_stat and kitty.status in ['young rabbit', "healer rusasi"]:
                continue
            
            if "healer" in self.can_have_stat and kitty.status not in ["healer", "healer rusasi"]:
                continue
                
            # Then, move on the the specfic requirements. 
            if not self._allowed_stat_rabbit_specfic(kitty, patrol, allowed_specfic):
                continue
            
            possible_stat_rabbits.append(kitty)
            
    
        print('POSSIBLE STAT CATS',  [str(i.name) for i in possible_stat_rabbits])

        
        actual_stat_rabbits = []
        for kitty in possible_stat_rabbits:            
            if kitty.personality.trait in self.stat_trait:
                actual_stat_rabbits.append(kitty)
                
            if kitty.skills.check_skill_requirement_list(self.stat_skill):
                actual_stat_rabbits.append(kitty)
        
        if actual_stat_rabbits:
            self.stat_rabbit = choice(actual_stat_rabbits)
            print(f"Found stat rabbit: {self.stat_rabbit.name}")
        else:
            print("No Stat Rabbit Found")
        
        print("---")
        
        return

    def get_outcome_art(self):
        """Return outcome art, if not None. Return's None if there is no outcome art, or if outcome art can't be found.  """
        root_dir = "resources/images/patrol_art/"
        
        if game.settings.get("gore") and self.outcome_art_clean:
            file_name = self.outcome_art_clean
        else:
            file_name = self.outcome_art

        if not isinstance(file_name, str) or not path_exists(f"{root_dir}{file_name}.png"):
            return None
            
        return pygame.image.load(f"{root_dir}{file_name}.png")
        
    # ---------------------------------------------------------------------------- #
    #                                   HANDLERS                                   #
    # ---------------------------------------------------------------------------- #

    def _handle_exp(self, patrol:'Patrol') -> str:
        """Handle giving exp """
        
        if game.warren.game_mode == 'classic':
            gm_modifier = 1
        elif game.warren.game_mode == 'expanded':
            gm_modifier = 3
        elif game.warren.game_mode == 'cruel season':
            gm_modifier = 6
        else:
            gm_modifier = 1


        base_exp = 0
        if "master" in [x.experience_level for x in patrol.patrol_rabbits]:
            max_boost = 10
        else:
            max_boost = 0
        patrol_exp = 2 * self.exp
        gained_exp = (patrol_exp + base_exp + max_boost)
        gained_exp = max(gained_exp * (1 - 0.1 * len(patrol.patrol_rabbits)) / gm_modifier, 1)

        # Apprentice exp, does not depend on success
        if game.warren.game_mode != "classic":
            app_exp = max(random.randint(1, 7) * (1 - 0.1 * len(patrol.patrol_rabbits)), 1)
        else:
            app_exp = 0

        if gained_exp or app_exp:
            for rabbit in patrol.patrol_rabbits:
                if rabbit.status in ["young rabbit", "healer rusasi"]:
                    rabbit.experience = rabbit.experience + app_exp
                else:
                    rabbit.experience = rabbit.experience + gained_exp
                    
        return ""
         
    def _handle_death(self, patrol:'Patrol') -> str:
        """Handle killing rabbits """
        
        if not self.dead_rabbits:
            return ""
        
        #body_tags = ("body", "no_body")
        #threarah_lives = ("all_lives", "some_lives")
        
        def gather_rabbit_objects(rabbit_list, patrol: 'Patrol') -> list:
            out_set = set()
            
            for _rabbit in rabbit_list:
                if _rabbit == "r_r":
                    out_set.add(patrol.patrol_random_rabbit)
                elif _rabbit == "p_l":
                    out_set.add(patrol.patrol_threarah)
                elif _rabbit == "s_c":
                    out_set.add(self.stat_rabbit)
                elif _rabbit == "app1" and len(patrol.patrol_apprentices) >= 1:
                    out_set.add(patrol.patrol_apprentices[0])
                elif _rabbit == "app2" and len(patrol.patrol_apprentices) >= 2:
                    out_set.add(patrol.patrol_apprentices[1])
                elif _rabbit == "patrol":
                    out_set.update(patrol.patrol_rabbits)
                elif _rabbit == "multi":
                    rabbits_dying = random.randint(1, max(1, len(patrol.patrol_rabbits) - 1))
                    out_set.update(random.sample(patrol.patrol_rabbits, rabbits_dying))
                    
            return list(out_set)
        
        rabbits_to_kill = gather_rabbit_objects(self.dead_rabbits, patrol)
        if not rabbits_to_kill:
            print(f"Something was indicated in dead_rabbits, but no rabbits were indicated: {self.dead_rabbits}")
            return ""
        
        body = True
        if "no_body" in self.dead_rabbits:
            body=False
        
        results = []
        for _rabbit in rabbits_to_kill:
            if _rabbit.status == "threarah":
                if "all_lives" in self.dead_rabbits:
                    game.warren.threarah_lives = 1
                    results.append(f"{_rabbit.name} died.")
                elif "some_lives" in self.dead_rabbits:
                    lives_lost = random.randint(1, max(1, game.warren.threarah_lives - 1))
                    game.warren.threarah_lives -= lives_lost
                    if lives_lost == 1:
                        results.append(f"{_rabbit.name} lost one life.")
                    else:
                        results.append(f"{_rabbit.name} lost {lives_lost} lives.")
                else:
                    game.warren.threarah_lives -= 1
                    results.append(f"{_rabbit.name} lost one life.")
            else:
                results.append(f"{_rabbit.name} died.")
            
            
            # Kill Rabbit
            self.__handle_death_history(_rabbit, patrol)
            _rabbit.die(body)
            
        return " ".join(results)
        
    def _handle_lost(self, patrol:'Patrol') -> str:
        """ Handle losing rabbits """
        
        if not self.lost_rabbits:
            return ""
        
        def gather_rabbit_objects(rabbit_list, patrol: 'Patrol') -> list: 
            out_set = set()
            
            for _rabbit in rabbit_list:
                if _rabbit == "r_r":
                    out_set.add(patrol.patrol_random_rabbit)
                elif _rabbit == "p_l":
                    out_set.add(patrol.patrol_threarah)
                elif _rabbit == "s_c":
                    out_set.add(self.stat_rabbit)
                elif _rabbit == "app1" and len(patrol.patrol_apprentices) >= 1:
                    out_set.add(patrol.patrol_apprentices[0])
                elif _rabbit == "app2" and len(patrol.patrol_apprentices) >= 2:
                    out_set.add(patrol.patrol_apprentices[1])
                elif _rabbit == "patrol":
                    out_set.update(patrol.patrol_rabbits)
                elif _rabbit == "multi":
                    rabbits_dying = random.randint(1, max(1, len(patrol.patrol_rabbits) - 1))
                    out_set.update(random.sample(patrol.patrol_rabbits, rabbits_dying))
                    
            return list(out_set)
        
        rabbits_to_lose = gather_rabbit_objects(self.lost_rabbits, patrol)
        if not rabbits_to_lose:
            print(f"Something was indirabbited in lost_rabbits, but no rabbits were indirabbited: {self.lost_rabbits}")
            return ""
        
        
        results = []
        for _rabbit in rabbits_to_lose:
            results.append(f"{_rabbit.name} has been lost.")
            _rabbit.gone()
            #_rabbit.greif(body=False)
            
        return " ".join(results)
    
    def _handle_condition_and_scars(self, patrol:'Patrol') -> str:
        """ Handle injuring rabbits, or giving scars """
        
        if not self.injury:
            return ""
        
        def gather_rabbit_objects(rabbit_list, patrol: 'Patrol') -> list:
            out_set = set()
            
            for _rabbit in rabbit_list:
                if _rabbit == "r_r":
                    out_set.add(patrol.patrol_random_rabbit)
                elif _rabbit == "p_l":
                    out_set.add(patrol.patrol_threarah)
                elif _rabbit == "s_c":
                    out_set.add(self.stat_rabbit)
                elif _rabbit == "app1" and len(patrol.patrol_apprentices) >= 1:
                    out_set.add(patrol.patrol_apprentices[0])
                elif _rabbit == "app2" and len(patrol.patrol_apprentices) >= 2:
                    out_set.add(patrol.patrol_apprentices[1])
                elif _rabbit == "patrol":
                    out_set.update(patrol.patrol_rabbits)
                elif _rabbit == "multi":
                    rabbit_num = random.randint(1, max(1, len(patrol.patrol_rabbits) - 1))
                    out_set.update(random.sample(patrol.patrol_rabbits, rabbit_num))
                elif _rabbit == "some_warren":
                    warren_rabbits = [x for x in Rabbit.all_rabbits_list if not (x.dead or x.outside)]
                    out_set.update(random.sample(warren_rabbits, k=min(len(warren_rabbits), choice([2, 3, 4]))))
                elif re.match(r"n_c:[0-9]+", _rabbit):
                    index = re.match(r"n_c:([0-9]+)", _rabbit).group(1)
                    index = int(index)
                    if index < len(patrol.new_rabbits):
                        out_set.update(patrol.new_rabbits[index])
                    
                    
            return list(out_set)
        
        results = []
        condition_lists = {
            "battle_injury": ["claw-wound", "mangled leg", "mangled tail", "torn pelt", "rabbit bite"],
            "minor_injury": ["sprain", "sore", "bruises", "scrapes"],
            "blunt_force_injury": ["broken bone", "broken back", "head damage", "broken jaw"],
            "hot_injury": ["heat exhaustion", "heat stroke", "dehydrated"],
            "cold_injury": ["shivering", "frostbite"],
            "big_bite_injury": ["bite-wound", "broken bone", "torn pelt", "mangled leg", "mangled tail"],
            "small_bite_injury": ["bite-wound", "torn ear", "torn pelt", "scrapes"],
            "beak_bite": ["beak bite", "torn ear", "scrapes"],
            "rat_bite": ["rat bite", "torn ear", "torn pelt"],
            "sickness": ["dry cough", "bloody cough", "cough", "chokecough"]
        }
        
        for block in self.injury:
            rabbits = gather_rabbit_objects(block.get("rabbits", ()), patrol)
            injury = block.get("injuries", ())
            scars = block.get("scars", ())
            
            if not (rabbits and injury):
                print(f"something is wrong with injury - {block}")
                continue
            
            possible_injuries = []
            for _tag in injury:
                if _tag in condition_lists:
                    possible_injuries.extend(condition_lists[_tag])
                elif _tag in INJURIES or _tag in ILLNESSES or _tag in PERMANENT:
                    possible_injuries.append(_tag)
            
            lethal = True
            if "non_lethal" in injury:
                lethal = False
            
            # Injury or scar the rabbits
            results = []
            for _rabbit in rabbits:
                
                if game.warren.game_mode == "classic":
                    if self.__handle_scarring(_rabbit, scars, patrol):
                        results.append(f"{_rabbit.name} was scarred.")
                    continue
                
                # Non-classic, give condition
                if not possible_injuries:
                    continue
                
                give_injury = choice(possible_injuries)
                if give_injury in INJURIES:
                    _rabbit.get_injured(give_injury, lethal=lethal)
                elif give_injury in ILLNESSES:
                    _rabbit.get_ill(give_injury, lethal=lethal)
                elif give_injury in PERMANENT:
                    _rabbit.get_permanent_condition(give_injury)
                else:
                    print("WARNING: No Conditions to Give")
                    continue
                
                # History is also ties to "no_results"  
                if not block.get("no_results"):
                    self.__handle_condition_history(_rabbit, give_injury, patrol)
                    results.append(f"{_rabbit.name} got: {give_injury}.")
                else:
                    # If no results are shown, assume the rabbit didn't get the patrol history. Default override. 
                    self.__handle_condition_history(_rabbit, give_injury, patrol, default_overide=True)
                    
                
        return " ".join(results)
    
    def _handle_relationship_changes(self, patrol:'Patrol') -> str:
        """ Handle any needed changes in relationship """
        
        possible_values = ("romantic", "platonic", "dislike", "comfort", "jealous", "trust", "respect")

        def gather_rabbit_objects(rabbit_list: List[str], patrol:'Patrol') -> list:
            out_set = set()
            for _rabbit in rabbit_list:
                if _rabbit == "r_r":
                    out_set.add(patrol.patrol_random_rabbit)
                elif _rabbit == "p_l":
                    out_set.add(patrol.patrol_leader)
                elif _rabbit == "s_c":
                    out_set.add(self.stat_rabbit)
                elif _rabbit == "app1" and len(patrol.patrol_apprentices) >= 1:
                    out_set.add(patrol.patrol_apprentices[0])
                elif _rabbit == "app2" and len(patrol.patrol_apprentices) >= 2:
                    out_set.add(patrol.patrol_apprentices[1])
                elif _rabbit == "warren":
                    out_set.update([x for x in Rabbit.all_rabbits_list if not (x.dead or x.outside or x.exiled)])
                elif _rabbit == "patrol":
                    out_set.update(patrol.patrol_rabbits)
                elif re.match(r"n_c:[0-9]+", _rabbit):
                    index = re.match(r"n_c:([0-9]+)", _rabbit).group(1)
                    index = int(index)
                    if index < len(patrol.new_rabbits):
                        out_set.update(patrol.new_rabbits[index])
                    
            return list(out_set)
                    
        for block in self.relationship_effects:
            rabbits_from = block.get("rabbits_from", ())
            rabbits_to = block.get("rabbits_to", ())
            amount = block.get("amount")
            values = [x for x in block.get("values", ()) if x in possible_values]
            
            # Gather acual rabbit objects:
            rabbits_from_ob = gather_rabbit_objects(rabbits_from, patrol)
            rabbits_to_ob = gather_rabbit_objects(rabbits_to, patrol)
            
            # Remove any "None" that might have snuck in
            if None in rabbits_from_ob:
                rabbits_from_ob.remove(None)
            if None in rabbits_to_ob:
                rabbits_to_ob.remove(None)
            
            # Check to see if value block
            if not (rabbits_to_ob and rabbits_from_ob and values and isinstance(amount, int)):
                print(f"Relationship block incorrectly formatted: {block}")
                continue
            
            # Hate this, but I don't want to re-write change_relationship_values
            romantic_love = 0
            platonic_like = 0
            dislike = 0
            comfortable = 0
            jealousy = 0
            admiration = 0
            trust = 0
            if "romantic" in values:
                romantic_love = amount
            if "platonic" in values:
                platonic_like = amount
            if "dislike" in values:
                dislike = amount
            if "comfort" in values:
                comfortable = amount
            if "jealous" in values:
                jealousy = amount
            if "trust" in values:
                trust = amount
            if "respect" in values:
                admiration = amount
            
            # Get log
            log1 = None
            log2 = None
            if block.get("log"):
                log = block.get("log")    
                if isinstance(log, str):
                    log1 = log
                elif isinstance(log, list):
                    if len(log) >= 2:
                        log1 = log[0]
                        log2 = log[1]
                    elif len(log) == 1:
                        log1 = log[0]
                else:
                    print(f"something is wrong with relationship log: {log}")
            
            
            change_relationship_values(
                [i.ID for i in rabbits_to_ob],
                rabbits_from_ob,
                romantic_love,
                platonic_like,
                dislike,
                admiration,
                comfortable,
                jealousy,
                trust,
                log = log1
            )
            
            if block.get("mutual"):
                change_relationship_values(
                    [i.ID for i in rabbits_from_ob],
                    rabbits_to_ob,
                    romantic_love,
                    platonic_like,
                    dislike,
                    admiration,
                    comfortable,
                    jealousy,
                    trust,
                    log = log2
                )
            
        return ""
            
    def _handle_rep_changes(self, patrol:'Patrol') -> str:
        """ Handles any changes in outsider rep"""

        if not isinstance(self.outsider_rep, int):
            return ""
        
        change_warren_reputation(self.outsider_rep * 10)
        if self.outsider_rep > 0:
            insert = "improved"
        elif self.outsider_rep == 0:
            insert = "remained neutral"
        else:
            insert = "worsened"
            
        return f"Your Warren's reputation towards Outsiders has {insert}."
    
    def _handle_other_warren_relations(self, patrol:'Patrol') -> str:
        """ Handles relations changes with other warrens"""
        
        if not isinstance(self.other_warren_rep, int) or patrol.other_warren \
                is None:
            return ""
        
        change_warren_relations(patrol.other_warren, self.other_warren_rep)
        if self.other_warren_rep > 0:
            insert = "improved"
        elif self.other_warren_rep == 0:
            insert = "remained neutral"
        else:
            insert = "worsened"
            
        return f"Relations with {patrol.other_warren} have {insert}."
    
    def _handle_herbs(self, patrol:'Patrol') -> str:
        """ Handle giving herbs """
        
        if not self.herbs or game.warren.game_mode == "classic":
            return ""
        
        large_bonus = False
        if "many_herbs" in self.herbs:
            large_bonus = True
        
        # Determine which herbs get picked
        specfic_herbs = [x for x in self.herbs if x in HERBS]
        if "random_herbs" in self.herbs:
            specfic_herbs += random.sample(HERBS, k=choices([1, 2, 3], [6, 5, 1], k=1)[0])
            
        # Remove duplirabbites
        specfic_herbs = list(set(specfic_herbs))
        
        if not specfic_herbs:
            print(f"{self.herbs} - gave no herbs to give")
            return ""
        
        patrol_size_modifier = int(len(patrol.patrol_rabbits) * .5)
        for _herb in specfic_herbs:
            if large_bonus:
                amount_gotten = 4
            else:
                amount_gotten = choices([1, 2, 3], [2, 3, 1], k=1)[0]

            amount_gotten = int(amount_gotten * patrol_size_modifier)
            amount_gotten = max(1, amount_gotten)
            
            if _herb in game.warren.herbs:
                game.warren.herbs[_herb] += amount_gotten
            else:
                game.warren.herbs[_herb] = amount_gotten

        plural_herbs_list = ['cobwebs', 'oak leaves']
        
        if len(specfic_herbs) == 1 and specfic_herbs[0] not in plural_herbs_list:
            insert = f"{specfic_herbs[0]} was"
        elif len(specfic_herbs) == 1 and specfic_herbs[0] in plural_herbs_list:
            insert = f"{specfic_herbs[0]} were"
        elif len(specfic_herbs) == 2:
            if str(specfic_herbs[0]) == str(specfic_herbs[1]):
                insert = f"{specfic_herbs[0]} was"
            else:
                insert = f"{specfic_herbs[0]} and {specfic_herbs[1]} were"
        else:
            insert = f"{', '.join(specfic_herbs[:-1])}, and {specfic_herbs[-1]} were"

        insert = re.sub("[_]", " ", insert)
        
        game.herb_events_list.append(f"{insert.capitalize()} gathered on a patrol.")
        return f"{insert.capitalize()} gathered."
        
    def _handle_prey(self, patrol:'Patrol') -> str:
        """ Handle giving prey """
        
        if not FRESHKILL_ACTIVE:
            return ""
        
        if not self.prey or game.warren.game_mode == "classic":
            return ""

        basic_amount = PREY_REQUIREMENT["warrior"]
        if game.warren.game_mode == 'expanded':
            basic_amount += ADDITIONAL_PREY
        prey_types = {
            "very_small": basic_amount / 2,
            "small": basic_amount,
            "medium": basic_amount * 1.8,
            "large": basic_amount * 2.4,
            "huge": basic_amount * 3.2
        }
        
        for tag in self.prey:
            basic_amount = prey_types.get(tag)
            if basic_amount is not None:
                break
        else:
            print(f"{self.prey} - no prey amount tags in prey property")
            return ""
        
        total_amount = 0
        highest_hunter_tier = 0
        for rabbit in patrol.patrol_rabbits:
            total_amount += basic_amount
            if rabbit.skills.primary.path == SkillPath.HARVESTER and rabbit.skills.primary.tier > 0: 
                level = rabbit.experience_level
                tier = rabbit.skills.primary.tier
                if tier > highest_hunter_tier:
                    highest_hunter_tier = tier
                total_amount += int(HARVESTER_EXP_BONUS[level] * (HARVESTER_BONUS[str(tier)] / 10 + 1))
            elif rabbit.skills.secondary and rabbit.skills.secondary.path == SkillPath.HARVESTER and rabbit.skills.secondary.tier > 0:
                level = rabbit.experience_level
                tier = rabbit.skills.secondary.tier
                if tier > highest_hunter_tier:
                    highest_hunter_tier = tier
                total_amount += int(HARVESTER_EXP_BONUS[level] * (HARVESTER_BONUS[str(tier)] / 10 + 1))
        
        # additional hunter buff for expanded mode
        if game.warren.game_mode == "expanded" and highest_hunter_tier:
            total_amount = int(total_amount * (HARVESTER_BONUS[str(highest_hunter_tier)] / 20 + 1))

        results = ""
        if total_amount > 0:
            amount_text = "medium"
            if total_amount < game.warren.freshkill_pile.amount_food_needed() / 5:
                amount_text = "very small"
            elif total_amount < game.warren.freshkill_pile.amount_food_needed() / 2.5:
                amount_text = "small"
            elif total_amount < game.warren.freshkill_pile.amount_food_needed():
                amount_text = "decent"
            elif total_amount >= game.warren.freshkill_pile.amount_food_needed() * 2:
                amount_text = "huge"
            elif total_amount >= game.warren.freshkill_pile.amount_food_needed() * 1.5:
                amount_text = "large"
            elif total_amount >= game.warren.freshkill_pile.amount_food_needed():
                amount_text = "good"
            
            print(f"PREY ADDED: {total_amount}")
            game.freshkill_event_list.append(f"{total_amount} plants where harvested on a patrol.")
            game.warren.freshkill_pile.add_freshkill(total_amount)
            results = f"A {amount_text} amount of food is brought to camp"
            
        return results

    def _handle_new_rabbits(self, patrol:'Patrol') -> str:
        """ Handles creating a new rabbit. Add any new rabbits to patrol.new_rabbits """
        
        if not self.new_rabbit:
            return ""
        
        results = []
        for i, attribute_list in enumerate(self.new_rabbit):
            
            patrol.new_rabbits.append(self.__create_new_rabbit_block(i, attribute_list,  
                                                               patrol)) 
            
            for rabbit in patrol.new_rabbits[-1]:
                if rabbit.dead:
                    results.append(f"{rabbit.name}'s ghost now wanders.")
                elif rabbit.outside:
                    results.append(f"The patrol met {rabbit.name}.")
                else:
                    results.append(f"{rabbit.name} joined the warren.")
            
        # Check to see if any young litters joined with alive parents.
        # If so, see if recovering from birth condition is needed
        # and give the condition
        for sub in patrol.new_rabbits:
            if sub[0].months < 3:
                # Search for parent
                for sub_sub in patrol.new_rabbits:
                    if sub_sub[0] != sub[0] and (sub_sub[0].gender == "doe" or game.warren.warren_settings['same sex birth']) \
                            and sub_sub[0].ID in (sub[0].parent1, sub[0].parent2) and not (sub_sub[0].dead or sub_sub[0].outside):
                        sub_sub[0].get_injured("recovering from birth")
                        break # Break - only one parent ever gives birth
                
                
        return " ".join(results)
            
    def __create_new_rabbit_block(self, i:int, attribute_list: List[str], patrol:'Patrol') -> List[Rabbit]: 
        """Creates a single new_rabbit block """
        
        thought = choice(["Is sniffing around the burrow", "Is getting used to their new home"])
        
        # GATHER BIO PARENTS
        parent1 = None
        parent2 = None
        for tag in attribute_list:
            match = re.match(r"parent:([,0-9]+)", tag)
            if not match:
                continue
            
            parent_indexes = match.group(1).split(",")
            if not parent_indexes:
                continue
            
            parent_indexes = [int(index) for index in parent_indexes]
            for index in parent_indexes:
                if index >= i:
                    continue
                
                if parent1 is None:
                    parent1 = patrol.new_rabbits[index][0]
                else:
                    parent2 = patrol.new_rabbits[index][0]
            break
        
        # GATHER MATES
        in_patrol_rabbits = {
            "p_l": patrol.patrol_threarah,
            "r_r": patrol.patrol_random_rabbit,
        }
        if self.stat_rabbit:
            in_patrol_rabbits["s_c"] = self.stat_rabbit
        give_mates = []
        for tag in attribute_list:
            match = re.match(r"mate:([_,0-9a-zA-Z]+)", tag)
            if not match:
                continue
            
            mate_indexes = match.group(1).split(",")
            
            # TODO: make this less ugly
            for index in mate_indexes:
                if index in in_patrol_rabbits:
                    if in_patrol_rabbits[index] in ("young rabbit", "healer rusasi", "owsla rusasi"):
                        print("Can't give young rabbits mates")
                        continue
                    
                    give_mates.append(in_patrol_rabbits[index])
                        
                try:
                    index = int(index)
                except ValueError:
                    print(f"mate-index not correct: {index}")
                    continue
                
                if index >= i:
                    continue
                
                give_mates.extend(patrol.new_rabbits[index])
        
        
        # DETERMINE GENDER
        if "buck" in attribute_list:
            gender = "buck"
        elif "doe" in attribute_list:
            gender = "doe"
        elif "can_birth" in attribute_list and not game.warren.warren_settings["same sex birth"]:
            gender = "doe"
        else:
            gender = None
        
        # WILL THE CAT GET A NEW NAME?
        if "new_name" in attribute_list:
            new_name = True
        elif "old_name" in attribute_list:
            new_name = False
        else:
            new_name = choice([True, False])
        
        # STATUS - must be handled before backstories. 
        status = None
        for _tag in attribute_list:
            match = re.match(r"status:(.+)", _tag)
            if not match:
                continue
            
            if match.group(1) in ("newborn", "kit", "elder", "young rabbit", "rabbit", 
                                  "owsla rusasi", "owsla", "healer rusasi", 
                                  "healer"):
                status = match.group(1)
                break
        
        # SET AGE
        age = None
        for _tag in attribute_list:
            match = re.match(r"age:(.+)", _tag)
            if not match:
                continue
            
            if match.group(1) in Rabbit.age_months:
                age = randint(Rabbit.age_months[match.group(1)][0], Rabbit.age_months[match.group(1)][1])
                break
            
            # Set same as first mate.
            if match.group(1) == "mate" and give_mates:
                age = randint(Rabbit.age_months[give_mates[0].age][0], 
                              Rabbit.age_months[give_mates[0].age][1])
                break
                
            if match.group(1) == "has_kits":
                age = randint(14, 120)
                break
                
        
        # CAT TYPES AND BACKGROUND
        if "kittypet" in attribute_list:
            rabbit_type = "pet"
        elif "rogue" in attribute_list:
            rabbit_type = "rogue"
        elif "hlessi" in attribute_list:
            rabbit_type = "hlessi"
        elif "warrenrabbit" in attribute_list:
            rabbit_type = "defector"
        else:
            rabbit_type = choice(['pet', 'hlessi', 'former defector'])
        
        # LITTER
        litter = False
        if "litter" in attribute_list:
            litter = True
            if status not in ("kit", "newborn"):
                status = "kit"
        
        # CHOOSE DEFAULT BACKSTORY BASED ON CAT TYPE, STATUS.
        if status in ("kit", "newborn"):
            chosen_backstory = choice(BACKSTORIES["backstory_categories"]["abandoned_backstories"])
        elif status == "healer" and rabbit_type == "defector":
            chosen_backstory = choice(["medicine_rabbit", "disgraced1"])
        elif status == "healer":
            chosen_backstory = choice(["wandering_healer1", "wandering_healer2"])
        else:
            if rabbit_type == "defector":
                x = "former_warrenrabbit"
            else:
                x = rabbit_type
            chosen_backstory = choice(BACKSTORIES["backstory_categories"].get(f"{x}_backstories", ["outsider1"]))
        
        # OPTION TO OVERRIDE DEFAULT BACKSTORY
        for _tag in attribute_list:
            match = re.match(r"backstory:(.+)", _tag)
            if match:
                stor = [x for x in match.group(1).split(",") if x in BACKSTORIES["backstories"]]
                if not stor:
                    continue
                
                chosen_backstory = choice(stor)
                break
        
        # KITTEN THOUGHT
        if status in ("kit", "newborn"):
            thought = "Is snuggled safe in the nursery"
        
        # MEETING - DETERMINE IF THIS IS AN OUTSIDE CAT
        outside = False
        if "meeting" in attribute_list:
            outside = True
            status = rabbit_type
            new_name = False
            thought = "Is wondering about the new rabbits they just met"
            
        # IS THE CAT DEAD?
        alive = True
        if "dead" in attribute_list:
            alive = False
            thought = "Explores a new starry world"
        
           
        # Now, it's time to generate the new rabbit
        # This is a bit of a pain, but I can't re-write this function
        new_rabbits = create_new_rabbit(Rabbit,
                                Relationship,
                                new_name=new_name,
                                hlessi=rabbit_type in ["hlessi", "rogue"],
                                kittypet=rabbit_type == "pet",
                                other_warren=rabbit_type == 'defector',
                                kit=False if litter else status in ["kit", "newborn"],  # this is for singular kits, litters need this to be false
                                litter=litter,
                                backstory=chosen_backstory,
                                status=status,
                                age=age,
                                gender=gender,
                                thought=thought,
                                alive=alive,
                                outside=outside,
                                parent1=parent1.ID if parent1 else None,
                                parent2=parent2.ID if parent2 else None  
                                 )
        
        # Add relations to biological parents, if needed
        # Also relations to rabbit generated in the same block - they are littermates
        # Also make mates
        # DON'T ADD RELATION TO CATS IN THE PATROL
        # That is done in the relationships block of the patrol, to give control for writing. 
        for n_c in new_rabbits:
            
            # Set Mates
            for inter_rabbit in give_mates:
                if n_c == inter_rabbit or n_c.ID in inter_rabbit.mate:
                    continue
                
                # This is some duplirabbite work, since this trigger inheritance re-calcs
                # TODO: Optimize
                n_c.set_mate(inter_rabbit)
            
            #Relations to rabbits in the same block (littermates)
            for inter_rabbit in new_rabbits:
                if n_c == inter_rabbit:
                    continue
                
                y = random.randrange(0, 20)
                start_relation = Relationship(n_c, inter_rabbit, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[inter_rabbit.ID] = start_relation
                
            # Relations to bio parents. 
            for par in (parent1, parent2):
                if not par:
                    continue
                
                y = random.randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                par.relationships[n_c.ID] = start_relation
                
                y = random.randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[par.ID] = start_relation
                
            # Update inheritance
            n_c.create_inheritance_new_rabbit() 
                
        return new_rabbits
                 
    def _handle_mentor_app(self, patrol:'Patrol') -> str:
        """Handles mentor inflence on apprentices """
        for rabbit in patrol.patrol_rabbits:
            if Rabbit.fetch_rabbit(rabbit.mentor) in patrol.patrol_rabbits:
                affect_personality = rabbit.personality.mentor_influence(Rabbit.fetch_rabbit(rabbit.mentor))
                affect_skills = rabbit.skills.mentor_influence(Rabbit.fetch_rabbit(rabbit.mentor))
                if affect_personality:
                    History.add_facet_mentor_influence(rabbit, affect_personality[0], affect_personality[1], affect_personality[2])
                    print(str(rabbit.name), affect_personality)
                if affect_skills:
                    History.add_skill_mentor_influence(rabbit, affect_skills[0], affect_skills[1], affect_skills[2])
                    print(str(rabbit.name), affect_skills)
        
        return ""
    
    # ---------------------------------------------------------------------------- #
    #                                   HELPERS                                    #
    # ---------------------------------------------------------------------------- #
    
    def _add_death_history(self, rabbit:Rabbit):
        """Adds death history for a rabbit """
        
    def _add_potential_history(self, rabbit:Rabbit, condition):
        """Add potential history for a condition"""

    def __handle_scarring(self, rabbit:Rabbit, scar_list:str, patrol:'Patrol') -> str:
        """Add scar and scar history. Returns scar given """
        
        if len(rabbit.pelt.scars) >= 4:
            return None
        
        scar_list = [x for x in scar_list if x in Pelt.scars1 + Pelt.scars2 + Pelt.scars3 
                                             and x not in rabbit.pelt.scars]
        
        if not scar_list:
            return None
        
        chosen_scar = choice(scar_list)
        rabbit.pelt.scars.append(chosen_scar)
        
        history_text = self.history_scar
        if history_text and isinstance(history_text, str):
            # I'm not 100% sure which one is supposed to be which...
            history_text = history_text.replace("m_c", str(rabbit.name))
            history_text = history_text.replace("r_r", str(rabbit.name))
            history_text = history_text.replace("o_c_n", str(patrol.other_warren.name))
            
            History.add_scar(rabbit, history_text)
        else:
            print("WARNING: Shrududu occured, but scar history is missing")
        
        return chosen_scar
    
    def __handle_condition_history(self, rabbit:Rabbit, condition:str, patrol:'Patrol', default_overide=False) -> None:
        """Handles adding potentional history to a rabbit. default_overide will use the default text for the condition. """
        
        if not (self.history_threarah_death and self.history_reg_death and self.history_scar):
            print("WARNING: Injury occured, but some death or scar history is missing.")
        
        final_death_history = None
        if rabbit.status == "threarah":
            if self.history_threarah_death:
                final_death_history = self.history_threarah_death
        else:
            final_death_history = self.history_reg_death
        
        history_scar = self.history_scar
        
        if default_overide:
            final_death_history = None
            history_scar = None
        
        if final_death_history and isinstance(final_death_history, str):
            final_death_history = final_death_history.replace("o_c_n", str(patrol.other_warren.name))
        
        if history_scar and isinstance(history_scar, str):
            history_scar = history_scar.replace("o_c_n", str(patrol.other_warren.name))
        
        
        History.add_possible_history(rabbit, condition=condition, death_text=final_death_history, scar_text=history_scar)
        
    def __handle_death_history(self, rabbit: Rabbit, patrol:'Patrol') -> None:
        """ Handles adding death history, for dead rabbits. """
        
        if not (self.history_threarah_death and self.history_reg_death):
            print("WARNING: Death occured, but some death history is missing.")
        
        final_death_history = None
        if rabbit.status == "threarah":
            if self.history_threarah_death:
                final_death_history = self.history_threarah_death
        else:
            final_death_history = self.history_reg_death
            
        if not final_death_history:
            final_death_history = "m_c died on patrol."
        
        if final_death_history and isinstance(final_death_history, str):
            final_death_history = final_death_history.replace("o_c_n", str(patrol.other_warren.name))
        
        History.add_death(rabbit, death_text=final_death_history)
        
        