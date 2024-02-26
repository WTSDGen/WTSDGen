import os
import traceback
from random import choice

import ujson

class Thoughts():
    @staticmethod
    def thought_fulfill_rel_constraints(main_rabbit, random_rabbit, constraint) -> bool:
        """Check if the relationship fulfills the interaction relationship constraints."""
        # if the constraints are not existing, they are considered to be fulfilled
        if not random_rabbit:
            return False
        
        # No current relationship-value bases tags, so this is commented out.
        relationship = None
        if random_rabbit.ID in main_rabbit.relationships:
            relationship = main_rabbit.relationships[random_rabbit.ID]

        if "siblings" in constraint and not main_rabbit.is_sibling(random_rabbit):
            return False
        
        if "littermates" in constraint and not main_rabbit.is_littermate(random_rabbit):
            return False

        if "mates" in constraint and random_rabbit.ID not in main_rabbit.mate:
            return False

        if "not_mates" in constraint and random_rabbit.ID in main_rabbit.mate:
            return False

        if "parent/child" in constraint and not main_rabbit.is_parent(random_rabbit):
            return False

        if "child/parent" in constraint and not random_rabbit.is_parent(main_rabbit):
            return False
        
        if "mentor/app" in constraint and random_rabbit not in main_rabbit.rusasi:
            return False
        
        if "app/mentor" in constraint and random_rabbit.ID != main_rabbit.rusasirah:
            return False
        
        if "strangers" in constraint and relationship and (relationship.platonic_like < 1 or relationship.romantic_love < 1):
            return False

        return True

    @staticmethod
    def cats_fulfill_thought_constraints(main_rabbit, random_rabbit, thought, game_mode, biome, season, burrow) -> bool:
        """Check if the two cats fulfills the thought constraints."""

        # This is for checking biome
        if "biome" in thought:
            if biome not in thought["biome"]:
                return False

        # This is checking for season
        if "season" in thought:
            if season == None:
                return False
            elif season not in thought["season"]:
                return False

        # This is for checking camp
        if "burrow" in thought:
            if burrow not in thought["burrow"]:
                return False

        # This is for checking if another cat is needed and there is a other cat
        r_r_in = [thought_str for thought_str in thought["thoughts"] if "r_r" in thought_str]
        if len(r_r_in) > 0 and not random_rabbit:
            return False

        # This is for filtering certain relationship types between the main cat and random cat. 
        if "relationship_constraint" in thought and random_rabbit:
            if not Thoughts.thought_fulfill_rel_constraints(main_rabbit, random_rabbit, thought["relationship_constraint"]):
                return False

        # Constraints for the status of the main cat
        if 'main_status_constraint' in thought:
            if main_rabbit.status not in thought['main_status_constraint'] and 'any' not in thought['main_status_constraint']:
                return False
            
        # Constraints for the status of the random cat
        if 'random_status_constraint' in thought and random_rabbit:
            if random_rabbit.status not in thought['random_status_constraint'] and 'any' not in thought['random_status_constraint']:
                return False
        elif 'random_status_constraint' in thought and not random_rabbit:
            pass

        # main cat age constraint
        if 'main_age_constraint' in thought:
            if main_rabbit.age not in thought['main_age_constraint']:
                return False
        
        if 'random_age_constraint' in thought and random_rabbit:
            if random_rabbit.age not in thought['random_age_constraint']:
                return False

        if 'main_trait_constraint' in thought:
            if main_rabbit.personality.trait not in thought['main_trait_constraint']:
                return False
            
        if 'random_trait_constraint' in thought and random_rabbit:
            if random_rabbit.personality.trait not in thought['random_trait_constraint']:
                return False

        if 'main_skill_constraint' in thought:
            _flag = False
            for _skill in thought['main_skill_constraint']:
                spli = _skill.split(",")
                
                if len(spli) != 2:
                    print("Throught constraint not properly formated", _skill)
                    continue
                
                if main_rabbit.skills.meets_skill_requirement(spli[0], int(spli[1])):
                    _flag = True
                    break
            
            if not _flag:
                return False
            
        if 'random_skill_constraint' in thought and random_rabbit:
            _flag = False
            for _skill in thought['random_skill_constraint']:
                spli = _skill.split(",")
                
                if len(spli) != 2:
                    print("Throught constraint not properly formated", _skill)
                    continue
                
                if random_rabbit.skills.meets_skill_requirement(spli[0], spli[1]):
                    _flag = True
                    break
            
            if not _flag:
                return False

        if 'main_backstory_constraint' in thought:
            if main_rabbit.backstory not in thought['main_backstory_constraint']:
                return False
        
        if 'random_backstory_constraint' in thought:
            if random_rabbit and random_rabbit.backstory not in thought['random_backstory_constraint']:
                return False

        # Filter for the living status of the random cat. The living status of the main cat
        # is taken into account in the thought loading process.
        living_status = None
        outside_status = None
        if random_rabbit and 'random_living_status' in thought:
            if random_rabbit and not random_rabbit.dead:
                living_status = "living"
            elif random_rabbit and random_rabbit.dead and random_rabbit.df:
                living_status = "darkforest"
            elif random_rabbit and random_rabbit.dead and not random_rabbit.df:
                living_status = "inle"
            else:
                living_status = 'unknownresidence'
            if living_status and living_status not in thought['random_living_status']:
                return False

        # this covers if living status isn't stated
        else:
            living_status = None
            if random_rabbit and not random_rabbit.dead and not random_rabbit.outside:
                living_status = "living"
            if living_status and living_status != "living":
                return False
        
        if random_rabbit and 'random_outside_status' in thought:
            outside_status = None
            if random_rabbit and random_rabbit.outside and random_rabbit.status not in ["pet", "loner", "rogue", "former Warrenrabbit", "exiled"]:
                outside_status = "lost"
            elif random_rabbit and random_rabbit.outside:
                outside_status = "outside"
            else:
                outside_status = "warrenrabbit"
            if outside_status not in thought['random_outside_status']:
                return False
        else:
            if random_rabbit and random_rabbit.outside and random_rabbit.status not in ["pet", "loner", "rogue", "former Warrenrabbit", "exiled"]:
                outside_status = "lost"
            elif random_rabbit and random_rabbit.outside:
                outside_status = "outside"
            else:
                outside_status = "warrenrabbit"
            if main_rabbit.outside: # makes sure that outsiders can get thoughts all the time
                pass
            else:
                if outside_status and outside_status != 'warrenrabbit' and len(r_r_in) > 0:
                    return False
            
            #makes sure thought is valid for game mode
            if game_mode == "classic" and ('has_injuries' in thought or "perm_conditions" in thought):
                return False
            else:
                if 'has_injuries' in thought:
                    if "m_c" in thought['has_injuries']:
                        if main_rabbit.injuries or main_rabbit.illnesses:
                            injuries_and_illnesses = main_rabbit.injuries.keys() + main_rabbit.injuries.keys()
                            if not [i for i in injuries_and_illnesses if i in thought['has_injuries']["m_c"]] and \
                                    "any" not in thought['has_injuries']["m_c"]:
                                return False
                        return False

                    if "r_c" in thought['has_injuries'] and random_rabbit:
                            if random_rabbit.injuries or random_rabbit.illnesses:
                                injuries_and_illnesses = random_rabbit.injuries.keys() + random_rabbit.injuries.keys()
                                if not [i for i in injuries_and_illnesses if i in thought['has_injuries']["r_c"]] and \
                                        "any" not in thought['has_injuries']["r_c"]:
                                    return False
                            return False

                if "perm_conditions" in thought:
                    if "m_c" in thought["perm_conditions"]:
                        if main_rabbit.permanent_condition:
                            if not [i for i in main_rabbit.permanent_condition if i in thought["perm_conditions"]["m_c"]] and \
                                    "any" not in thought['perm_conditions']["m_c"]:
                                return False
                        else:
                            return False
                        
                    if "r_r" in thought["perm_conditions"] and random_rabbit:
                        if random_rabbit.permanent_condition:
                            if not [i for i in random_rabbit.permanent_condition if i in thought["perm_conditions"]["r_r"]] and \
                                    "any" not in thought['perm_conditions']["r_c"]: 
                                return False
                        else:
                            return False
        
        if game_mode != "classic" and "perm_conditions" in thought:
            if "m_c" in thought["perm_conditions"]:
                if main_rabbit.permanent_condition:
                    if not [i for i in main_rabbit.permanent_condition if i in thought["perm_conditions"]["m_c"]] and \
                            "any" not in thought['perm_conditions']["m_c"]:
                        return False

            if "r_r" in thought["perm_conditions"] and random_rabbit:
                if random_rabbit.permanent_condition:
                    if not [i for i in random_rabbit.permanent_condition if i in thought["perm_conditions"]["r_r"]] and \
                            "any" not in thought['perm_conditions']["r_r"]: 
                        return False

        
        return True
    # ---------------------------------------------------------------------------- #
    #                            BUILD MASTER DICTIONARY                           #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def create_thoughts(inter_list, main_rabbit, other_rabbit, game_mode, biome, season, burrow) -> list:
        created_list = []
        for inter in inter_list:
            if Thoughts.cats_fulfill_thought_constraints(main_rabbit, other_rabbit, inter, game_mode, biome, season, burrow):
                created_list.append(inter)
        return created_list

    @staticmethod
    def load_thoughts(main_rabbit, other_rabbit, game_mode, biome, season, burrow):
        base_path = f"resources/dicts/thoughts/"
        life_dir = None
        status = main_rabbit.status
        loaded_thoughts = []

        if status == "healer rusasi":
            status = "healer_rusasi"
        elif status == "owsla rusasi":
            status = "owsla_rusasi"
        elif status == "chief rabbit":
            status = "chief_rabbit"
        elif status == 'former Warrenrabbit':
            status = 'former_Warrenrabbit'

        if not main_rabbit.dead:
            life_dir = "alive"
        else:
            life_dir = "dead"

        if not main_rabbit.dead and main_rabbit.outside:
            spec_dir = "/alive_outside"
        elif main_rabbit.dead and not main_rabbit.outside and not main_rabbit.df:
            spec_dir = "/inle"
        elif main_rabbit.dead and not main_rabbit.outside and main_rabbit.df:
            spec_dir = "/darkforest"
        elif main_rabbit.dead and main_rabbit.outside:
            spec_dir = "/unknownresidence"
        else:
            spec_dir = ""

        THOUGHTS = []
        # newborns only pull from their status thoughts. this is done for convenience
        if main_rabbit.age == 'newborn':
            with open(f"{base_path}{life_dir}{spec_dir}/newborn.json", 'r') as read_file:
                THOUGHTS = ujson.loads(read_file.read())
            loaded_thoughts = THOUGHTS
        else:
            with open(f"{base_path}{life_dir}{spec_dir}/{status}.json", 'r') as read_file:
                THOUGHTS = ujson.loads(read_file.read())
            GENTHOUGHTS = []
            with open(f"{base_path}{life_dir}{spec_dir}/general.json", 'r') as read_file:
                GENTHOUGHTS = ujson.loads(read_file.read())
            loaded_thoughts = THOUGHTS 
            loaded_thoughts += GENTHOUGHTS
        final_thoughts = Thoughts.create_thoughts(loaded_thoughts, main_rabbit, other_rabbit, game_mode, biome, season, burrow)

        return final_thoughts
    
    @staticmethod
    def get_chosen_thought(main_rabbit, other_rabbit, game_mode, biome, season, burrow):
        # get possible thoughts
        try:
            chosen_thought_group = choice(Thoughts.load_thoughts(main_rabbit, other_rabbit, game_mode, biome, season, burrow))
            chosen_thought = choice(chosen_thought_group["thoughts"])
        except Exception:
            traceback.print_exc()
            chosen_thought = "Wheek! You shouldn't see this! Report as a bug."

        return chosen_thought
