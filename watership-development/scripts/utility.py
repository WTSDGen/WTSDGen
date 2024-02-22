# pylint: disable=line-too-long
"""

TODO: Docs


"""  # pylint: enable=line-too-long

import logging
import re
from random import choice, choices, randint, random, sample

import pygame
import ujson
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game, screen_x, screen_y
from scripts.rabbit.history import History
from scripts.rabbit.names import names
from scripts.rabbit.pelts import Pelt
from scripts.rabbit.sprites import sprites

logger = logging.getLogger(__name__)
from sys import exit as sys_exit
from typing import Dict

# ---------------------------------------------------------------------------- #
#                              Counting Rabbits                                   #
# ---------------------------------------------------------------------------- #

def get_alive_warren_queens(living_rabbits):
    living_kittens = [rabbit for rabbit in living_rabbits if not (rabbit.dead or rabbit.outside) and rabbit.status in ["kitten", "newborn"]]

    queen_dict = {}
    for rabbit in living_kittens.copy():
        parents = rabbit.get_parents()
        #Fetch parent object, only alive and not outside. 
        parents = [rabbit.fetch_rabbit(i) for i in parents if rabbit.fetch_rabbit(i) and not(rabbit.fetch_rabbit(i).dead or rabbit.fetch_rabbit(i).outside)]
        if not parents:
            continue
        
        if len(parents) == 1 or len(parents) > 2 or\
            all(i.gender == "buck" for i in parents) or\
            parents[0].gender == "doe":
            if parents[0].ID in queen_dict:
                queen_dict[parents[0].ID].append(rabbit)
                living_kittens.remove(rabbit)
            else:
                queen_dict[parents[0].ID] = [rabbit]
                living_kittens.remove(rabbit)
        elif len(parents) == 2:
            if parents[1].ID in queen_dict:
                queen_dict[parents[1].ID].append(rabbit)
                living_kittens.remove(rabbit)
            else:
                queen_dict[parents[1].ID] = [rabbit]
                living_kittens.remove(rabbit)
    return queen_dict, living_kittens

def get_alive_kittens(Rabbit):
    """
    returns a list of IDs for all living kittens in the warren
    """
    alive_kittens = [i for i in Rabbit.all_rabbits.values() if
                  i.age in ['kitten', 'newborn'] and not i.dead and not i.outside]

    return alive_kittens


def get_med_rabbits(Rabbit, working=True):
    """
    returns a list of all meds and med apps currently alive, in the warren, and able to work

    set working to False if you want all meds and med apps regardless of their work status
    """
    all_rabbits = Rabbit.all_rabbits.values()
    possible_med_rabbits = [i for i in all_rabbits if
                         i.status in ['healer rusasi', 'healer'] and not (i.dead or i.outside)]

    if working:
        possible_med_rabbits = [i for i in possible_med_rabbits if not i.not_working()]

    # Sort the rabbits by age before returning
    possible_med_rabbits = sorted(possible_med_rabbits, key=lambda rabbit: rabbit.months, reverse=True)

    return possible_med_rabbits


def get_living_rabbit_count(Rabbit):
    """
    TODO: DOCS
    """
    count = 0
    for the_rabbit in Rabbit.all_rabbits.values():
        if the_rabbit.dead:
            continue
        count += 1
    return count


def get_living_warren_rabbit_count(Rabbit):
    """
    TODO: DOCS
    """
    count = 0
    for the_rabbit in Rabbit.all_rabbits.values():
        if the_rabbit.dead or the_rabbit.exiled or the_rabbit.outside:
            continue
        count += 1
    return count


def get_rabbits_same_age(rabbit, range=10):  # pylint: disable=redefined-builtin
    """Look for all rabbits in the Warren and returns a list of rabbits, which are in the same age range as the given rabbit."""
    rabbits = []
    for inter_rabbit in rabbit.all_rabbits.values():
        if inter_rabbit.dead or inter_rabbit.outside or inter_rabbit.exiled:
            continue
        if inter_rabbit.ID == rabbit.ID:
            continue

        if inter_rabbit.ID not in rabbit.relationships:
            rabbit.create_one_relationship(inter_rabbit)
            if rabbit.ID not in inter_rabbit.relationships:
                inter_rabbit.create_one_relationship(rabbit)
            continue

        if inter_rabbit.months <= rabbit.months + range and inter_rabbit.months <= rabbit.months - range:
            rabbits.append(inter_rabbit)

    return rabbits


def get_free_possible_mates(rabbit):
    """Returns a list of available rabbits, which are possible mates for the given rabbit."""
    rabbits = []
    for inter_rabbit in rabbit.all_rabbits.values():
        if inter_rabbit.dead or inter_rabbit.outside or inter_rabbit.exiled:
            continue
        if inter_rabbit.ID == rabbit.ID:
            continue

        if inter_rabbit.ID not in rabbit.relationships:
            rabbit.create_one_relationship(inter_rabbit)
            if rabbit.ID not in inter_rabbit.relationships:
                inter_rabbit.create_one_relationship(rabbit)
            continue

        if inter_rabbit.is_potential_mate(rabbit, for_love_interest=True):
            rabbits.append(inter_rabbit)
    return rabbits


# ---------------------------------------------------------------------------- #
#                          Handling Outside Factors                            #
# ---------------------------------------------------------------------------- #
def get_current_season():
    """
    function to handle the math for finding the Warren's current season
    :return: the Warren's current season
    """

    if game.config['lock_season']:
        game.warren.current_season = game.warren.starting_season
        return game.warren.starting_season

    modifiers = {
        "Spring": 0,
        "Summer": 3,
        "Autumn": 6,
        "Winter": 9
    }
    index = game.warren.age % 12 + modifiers[game.warren.starting_season]

    if index > 11:
        index = index - 12

    game.warren.current_season = game.warren.seasons[index]

    return game.warren.current_season

def change_warren_reputation(difference):
    """
    will change the Warren's reputation with outsider rabbits according to the difference parameter.
    """
    game.warren.reputation += difference


def change_warren_relations(other_warren, difference):
    """
    will change the Warren's relation with other warrens according to the difference parameter.
    """
    # grab the warren that has been indirabbited
    other_warren = other_warren
    # grab the relation value for that warren
    y = game.warren.all_warrens.index(other_warren)
    warren_relations = int(game.warren.all_warrens[y].relations)
    # change the value
    warren_relations += difference
    # making sure it doesn't exceed the bounds
    if warren_relations > 30:
        warren_relations = 30
    elif warren_relations < 0:
        warren_relations = 0
    # setting it in the Warren save
    game.warren.all_warrens[y].relations = warren_relations

def create_new_rabbit(Rabbit,
                   Relationship,
                   new_name:bool=False,
                   loner:bool=False,
                   pet:bool=False,
                   kitten:bool=False,
                   litter:bool=False,
                   other_warren:bool=None,
                   backstory:bool=None,
                   status:str=None,
                   age:int=None,
                   gender:str=None,
                   thought:str='Is exploring the whole burrow',
                   alive:bool=True,
                   outside:bool=False,
                   parent1:str=None,
                   parent2:str=None
    ) -> list:
    """
    This function creates new rabbits and then returns a list of those rabbits
    :param Rabbit: pass the Rabbit class
    :params Relationship: pass the Relationship class
    :param new_name: set True if rabbit(s) is a loner/rogue receiving a new Warren name - default: False
    :param loner: set True if rabbit(s) is a loner or rogue - default: False
    :param pet: set True if rabbit(s) is a pet - default: False
    :param kitten: set True if the rabbit is a lone kitten - default: False
    :param litter: set True if a litter of kittens needs to be generated - default: False
    :param other_warren: if new rabbit(s) are from a neighboring warren, set true
    :param backstory: a list of possible backstories.json for the new rabbit(s) - default: None
    :param status: set as the rank you want the new rabbit to have - default: None (will cause a random status to be picked)
    :param age: set the age of the new rabbit(s) - default: None (will be random or if kitten/litter is true, will be kitten.
    :param gender: set the gender (BIRTH SEX) of the rabbit - default: None (will be random)
    :param thought: if you need to give a custom "welcome" thought, set it here
    :param alive: set this as False to generate the rabbit as already dead - default: True (alive)
    :param outside: set this as True to generate the rabbit as an outsider instead of as part of the Warren - default: False (Warren rabbit)
    :param parent1: Rabbit ID to set as the biological parent1
    :param parent2: Rabbit ID object to set as the biological parert2
    """
    accessory = None
    if isinstance(backstory, list):
        backstory = choice(backstory)

    if backstory in (
            BACKSTORIES["backstory_categories"]["former_warrenrabbit_backstories"] or BACKSTORIES["backstory_categories"]["otherwarren_categories"]):
        other_warren = True

    created_rabbits = []

    if not litter:
        number_of_rabbits = 1
    else:
        number_of_rabbits = choices([2, 3, 4, 5], [5, 4, 1, 1], k=1)[0]
    
    
    if not isinstance(age, int):
        if status == "newborn":
            age = 0
        elif litter or kitten:
            age = randint(1, 5)
        elif status in ('rusasi', 'healer rusasi', 'owsla rusasi'):
            age = randint(6, 11)
        elif status == 'rabbit':
            age = randint(23, 120)
        elif status == 'healer':
            age = randint(23, 140)
        elif status == 'elder':
            age = randint(120, 130)
        else:
            age = randint(6, 120)
    
    # setting status
    if not status:
        if age == 0:
            status = "newborn"
        elif age < 6:
            status = "kitten"
        elif 6 <= age <= 11:
            status = "rusasi"
        elif age >= 12:
            status = "rabbit"
        elif age >= 120:
            status = 'elder'

    # rabbit creation and naming time
    for index in range(number_of_rabbits):
        # setting gender
        if not gender:
            _gender = choice(['doe', 'buck'])
        else:
            _gender = gender

        # other Warren rabbits, apps, and kittens (kittens and apps get indoctrinated lmao no old names for them)
        if other_warren or kitten or litter or age < 12:
            new_rabbit = Rabbit(months=age,
                          status=status,
                          gender=_gender,
                          backstory=backstory,
                          parent1=parent1,
                          parent2=parent2)
        else:
            # grab starting names and accs for loners/pets
            if pet:
                name = choice(names.names_dict["loner_names"])
                if choice([1, 2]) == 1:
                    accessory = choice(Pelt.collars)
            elif loner and choice([1, 2]) == 1:  # try to give name from full loner name list
                name = choice(names.names_dict["loner_names"])
            else:
                name = choice(
                    names.names_dict["normal_prefixes"])  # otherwise give name from prefix list (more nature-y names)

            # now we make the rabbits
            if new_name:  # these rabbits get new names
                if choice([1, 2]) == 1:  # adding suffix to OG name
                    spaces = name.count(" ")
                    if spaces > 0:
                        # make a list of the words within the name, then add the OG name back in the list
                        words = name.split(" ")
                        words.append(name)
                        new_prefix = choice(words)  # pick new prefix from that list
                        name = new_prefix
                    new_rabbit = Rabbit(months=age,
                                  prefix=name,
                                  status=status,
                                  gender=_gender,
                                  backstory=backstory,
                                  parent1=parent1,
                                  parent2=parent2)
                else:  # completely new name
                    new_rabbit = Rabbit(months=age,
                                  status=status,
                                  gender=_gender,
                                  backstory=backstory,
                                  parent1=parent1,
                                  parent2=parent2)
            # these rabbits keep their old names
            else:
                new_rabbit = Rabbit(months=age,
                              prefix=name,
                              suffix="",
                              status=status,
                              gender=_gender,
                              backstory=backstory,
                              parent1=parent1,
                              parent2=parent2)

        # give em a collar if they got one
        if accessory:
            new_rabbit.pelt.accessory = accessory

        # give rusasi aged rabbit a rusasirah
        if new_rabbit.age == 'adolescent':
            new_rabbit.update_rusasirah()

        # Remove disabling scars, if they generated.
        not_allowed = ['NOPAW', 'NOTAIL', 'HALFTAIL', 'NOEAR', 'BOTHBLIND', 'RIGHTBLIND', 
                       'LEFTBLIND', 'BRIGHTHEART', 'NOLEFTEAR', 'NORIGHTEAR', 'MANLEG']
        for scar in new_rabbit.pelt.scars:
            if scar in not_allowed:
                new_rabbit.pelt.scars.remove(scar)

        # chance to give the new rabbit a permanent condition, higher chance for found kittens and litters
        if game.warren.game_mode != 'classic':
            if kitten or litter:
                chance = int(game.config["rabbit_generation"]["base_permanent_condition"] / 11.25)
            else:
                chance = game.config["rabbit_generation"]["base_permanent_condition"] + 10
            if not int(random() * chance):
                possible_conditions = []
                for condition in PERMANENT:
                    if (kitten or litter) and PERMANENT[condition]['congenital'] not in ['always', 'sometimes']:
                        continue
                    # next part ensures that a kitten won't get a condition that takes too long to reveal
                    age = new_rabbit.months
                    leeway = 5 - (PERMANENT[condition]['months_until'] + 1)
                    if age > leeway:
                        continue
                    possible_conditions.append(condition)
                    
                if possible_conditions:
                    chosen_condition = choice(possible_conditions)
                    born_with = False
                    if PERMANENT[chosen_condition]['congenital'] in ['always', 'sometimes']:
                        born_with = True

                    new_rabbit.get_permanent_condition(chosen_condition, born_with)
                    if new_rabbit.permanent_condition[chosen_condition]["months_until"] == 0:
                        new_rabbit.permanent_condition[chosen_condition]["months_until"] = -2

                    # assign scars
                    if chosen_condition in ['lost a leg', 'born without a leg']:
                        new_rabbit.pelt.scars.append('NOPAW')
                    elif chosen_condition in ['lost their tail', 'born without a tail']:
                        new_rabbit.pelt.scars.append("NOTAIL")

        if outside:
            new_rabbit.outside = True
        if not alive:
            new_rabbit.die()

        # newbie thought
        new_rabbit.thought = thought

        # and they exist now
        created_rabbits.append(new_rabbit)
        game.warren.add_rabbit(new_rabbit)
        history = History()
        history.add_beginning(new_rabbit)

        # create relationships
        new_rabbit.create_relationships_new_rabbit()
        # Note - we always update inheritance after the rabbits are generated, to
        # allow us to add parents. 
        #new_rabbit.create_inheritance_new_rabbit() 

    return created_rabbits


def create_outside_rabbit(Rabbit, status, backstory, alive=True, thought=None):
    """
        TODO: DOCS
        """
    suffix = ''
    if backstory in BACKSTORIES["backstory_categories"]["rogue_backstories"]:
        status = 'rogue'
    elif backstory in BACKSTORIES["backstory_categories"]["former_warrenrabbit_backstories"]:
        status = "defector"
    if status == 'pet':
        name = choice(names.names_dict["loner_names"])
    elif status in ['loner', 'rogue']:
        name = choice(names.names_dict["loner_names"] +
                      names.names_dict["normal_prefixes"])
    elif status == 'former Warrenrabbit':
        name = choice(names.names_dict["normal_prefixes"])
        suffix = choice(names.names_dict["normal_suffixes"])
    else:
        name = choice(names.names_dict["loner_names"])
    new_rabbit = Rabbit(prefix=name,
                  suffix=suffix,
                  status=status,
                  gender=choice(['doe', 'buck']),
                  backstory=backstory)
    if status == 'pet':
        new_rabbit.pelt.accessory = choice(Pelt.collars)
    new_rabbit.outside = True

    if not alive:
        new_rabbit.die()

    thought = "Wonders about those strange rabbits they just met"
    new_rabbit.thought = thought

    # create relationships - only with outsiders
    # (this function will handle, that the rabbit only knows other outsiders)
    new_rabbit.create_relationships_new_rabbit()
    new_rabbit.create_inheritance_new_rabbit()

    game.warren.add_rabbit(new_rabbit)
    game.warren.add_to_outside(new_rabbit)
    name = str(name + suffix)

    return name


# ---------------------------------------------------------------------------- #
#                             Rabbit Relationships                                #
# ---------------------------------------------------------------------------- #


def get_highest_romantic_relation(relationships, exclude_mate=False, potential_mate=False):
    """Returns the relationship with the highest romantic value."""
    max_love_value = 0
    current_max_relationship = None
    for rel in relationships:
        if rel.romantic_love < 0:
            continue
        if exclude_mate and rel.rabbit_from.ID in rel.rabbit_to.mate:
            continue
        if potential_mate and not rel.rabbit_to.is_potential_mate(rel.rabbit_from, for_love_interest=True):
            continue
        if rel.romantic_love > max_love_value:
            current_max_relationship = rel
            max_love_value = rel.romantic_love

    return current_max_relationship


def check_relationship_value(rabbit_from, rabbit_to, rel_value=None):
    """
    returns the value of the rel_value param given
    :param rabbit_from: the rabbit who is having the feelings
    :param rabbit_to: the rabbit that the feelings are directed towards
    :param rel_value: the relationship value that you're looking for,
    options are: romantic, platonic, dislike, admiration, comfortable, jealousy, trust
    """
    if rabbit_to.ID in rabbit_from.relationships:
        relationship = rabbit_from.relationships[rabbit_to.ID]
    else:
        relationship = rabbit_from.create_one_relationship(rabbit_to)

    if rel_value == "romantic":
        return relationship.romantic_love
    elif rel_value == "platonic":
        return relationship.platonic_like
    elif rel_value == "dislike":
        return relationship.dislike
    elif rel_value == "admiration":
        return relationship.admiration
    elif rel_value == "comfortable":
        return relationship.comfortable
    elif rel_value == "jealousy":
        return relationship.jealousy
    elif rel_value == "trust":
        return relationship.trust


def get_personality_compatibility(rabbit1, rabbit2):
    """Returns:
        True - if personalities have a positive compatibility
        False - if personalities have a negative compatibility
        None - if personalities have a neutral compatibility
    """
    personality1 = rabbit1.personality.trait
    personality2 = rabbit2.personality.trait

    if personality1 == personality2:
        if personality1 is None:
            return None
        return True

    lawfulness_diff = abs(rabbit1.personality.lawfulness - rabbit2.personality.lawfulness)
    sociability_diff = abs(rabbit1.personality.sociability - rabbit2.personality.sociability)
    aggression_diff = abs(rabbit1.personality.aggression - rabbit2.personality.aggression)
    stability_diff = abs(rabbit1.personality.stability - rabbit2.personality.stability)
    list_of_differences = [lawfulness_diff, sociability_diff, aggression_diff, stability_diff]

    running_total = 0
    for x in list_of_differences:
        if x <= 4:
            running_total += 1
        elif x >= 6:
            running_total -= 1

    if running_total >= 2:
        return True
    if running_total <= -2:
        return False

    return None


def get_rabbits_of_romantic_interest(rabbit):
    """Returns a list of rabbits, those rabbits are love interest of the given rabbit"""
    rabbits = []
    for inter_rabbit in rabbit.all_rabbits.values():
        if inter_rabbit.dead or inter_rabbit.outside or inter_rabbit.exiled:
            continue
        if inter_rabbit.ID == rabbit.ID:
            continue

        if inter_rabbit.ID not in rabbit.relationships:
            rabbit.create_one_relationship(inter_rabbit)
            if rabbit.ID not in inter_rabbit.relationships:
                inter_rabbit.create_one_relationship(rabbit)
            continue
        
        # Extra check to ensure they are potential mates
        if inter_rabbit.is_potential_mate(rabbit, for_love_interest=True) and rabbit.relationships[inter_rabbit.ID].romantic_love > 0:
            rabbits.append(inter_rabbit)
    return rabbits


def get_amount_of_rabbits_with_relation_value_towards(rabbit, value, all_rabbits):
    """
    Looks how many rabbits have the certain value 
    :param rabbit: rabbit in question
    :param value: value which has to be reached
    :param all_rabbits: list of rabbits which has to be checked
    """

    # collect all true or false if the value is reached for the rabbit or not
    # later count or sum can be used to get the amount of rabbits
    # this will be handled like this, because it is easier / shorter to check
    relation_dict = {
        "romantic_love": [],
        "platonic_like": [],
        "dislike": [],
        "admiration": [],
        "comfortable": [],
        "jealousy": [],
        "trust": []
    }

    for inter_rabbit in all_rabbits:
        if rabbit.ID in inter_rabbit.relationships:
            relation = inter_rabbit.relationships[rabbit.ID]
        else:
            continue

        relation_dict['romantic_love'].append(relation.romantic_love >= value)
        relation_dict['platonic_like'].append(relation.platonic_like >= value)
        relation_dict['dislike'].append(relation.dislike >= value)
        relation_dict['admiration'].append(relation.admiration >= value)
        relation_dict['comfortable'].append(relation.comfortable >= value)
        relation_dict['jealousy'].append(relation.jealousy >= value)
        relation_dict['trust'].append(relation.trust >= value)

    return_dict = {
        "romantic_love": sum(relation_dict['romantic_love']),
        "platonic_like": sum(relation_dict['platonic_like']),
        "dislike": sum(relation_dict['dislike']),
        "admiration": sum(relation_dict['admiration']),
        "comfortable": sum(relation_dict['comfortable']),
        "jealousy": sum(relation_dict['jealousy']),
        "trust": sum(relation_dict['trust'])
    }

    return return_dict


def change_relationship_values(rabbits_to: list,
                               rabbits_from: list,
                               romantic_love:int=0,
                               platonic_like:int=0,
                               dislike:int=0,
                               admiration:int=0,
                               comfortable:int=0,
                               jealousy:int=0,
                               trust:int=0,
                               auto_romance:bool=False,
                               log:str=None
                               ):
    """
    changes relationship values according to the parameters.

    rabbits_from - a list of rabbits for the rabbits whose rel values are being affected
    rabbits_to - a list of rabbit IDs for the rabbits who are the target of that rel value
            i.e. rabbits in rabbits_from lose respect towards the rabbits in rabbits_to
    auto_romance - if this is set to False (which is the default) then if the rabbit_from already has romantic value
            with rabbit_to then the platonic_like param value will also be used for the romantic_love param
            if you don't want this to happen, then set auto_romance to False
    log - string to add to relationship log. 

    use the relationship value params to indirabbite how much the values should change.
    
    This is just for test prints - DON'T DELETE - you can use this to test if relationships are changing
    changed = False
    if romantic_love == 0 and platonic_like == 0 and dislike == 0 and admiration == 0 and \
            comfortable == 0 and jealousy == 0 and trust == 0:
        changed = False
    else:
        changed = True"""

    # pick out the correct rabbits
    for kitty in rabbits_from:
        relationships = [i for i in kitty.relationships.values() if i.rabbit_to.ID in rabbits_to]

        # make sure that rabbits don't gain rel with themselves
        for rel in relationships:
            if kitty.ID == rel.rabbit_to.ID:
                continue

            # here we just double-check that the rabbits are allowed to be romantic with each other
            if kitty.is_potential_mate(rel.rabbit_to, for_love_interest=True) or rel.rabbit_to.ID in kitty.mate:
                # if rabbit already has romantic feelings then automatically increase romantic feelings
                # when platonic feelings would increase
                if rel.romantic_love > 0 and auto_romance:
                    romantic_love = platonic_like

                # now gain the romance
                rel.romantic_love += romantic_love

            # gain other rel values
            rel.platonic_like += platonic_like
            rel.dislike += dislike
            rel.admiration += admiration
            rel.comfortable += comfortable
            rel.jealousy += jealousy
            rel.trust += trust

            '''# for testing purposes - DON'T DELETE - you can use this to test if relationships are changing
            print(str(kitty.name) + " gained relationship with " + str(rel.rabbit_to.name) + ": " +
                  "Romantic: " + str(romantic_love) +
                  " /Platonic: " + str(platonic_like) +
                  " /Dislike: " + str(dislike) +
                  " /Respect: " + str(admiration) +
                  " /Comfort: " + str(comfortable) +
                  " /Jealousy: " + str(jealousy) +
                  " /Trust: " + str(trust)) if changed else print("No relationship change")'''
                  
            if log and isinstance(log, str):
                rel.log.append(log)


# ---------------------------------------------------------------------------- #
#                               Text Adjust                                    #
# ---------------------------------------------------------------------------- #

def pronoun_repl(m, rabbit_pronouns_dict, raise_exception=False):
    """ Helper function for add_pronouns. If raise_exception is 
    False, any error in pronoun formatting will not raise an 
    exception, and will use a simple replacement "error" """
    
    # Add protection about the "insert" sometimes used
    if m.group(0) == "{insert}":
        return m.group(0)
    
    inner_details = m.group(1).split("/")
    
    try:
        d = rabbit_pronouns_dict[inner_details[1]][1]
        if inner_details[0].upper() == "PRONOUN":
            pro = d[inner_details[2]]
            if inner_details[-1] == "CAP":
                pro = pro.capitalize()
            return pro
        elif inner_details[0].upper() == "VERB":
            return inner_details[d["conju"] + 1]
        
        if raise_exception:
            raise KeyError(f"Pronoun tag: {m.group(1)} is not properly"
                           "indirabbited as a PRONOUN or VERB tag.")
        
        print("Failed to find pronoun:", m.group(1))
        return "error1"
    except (KeyError, IndexError) as e:
        if raise_exception:
            raise
        
        logger.exception("Failed to find pronoun: " + m.group(1))
        print("Failed to find pronoun:", m.group(1))
        return "error2"


def name_repl(m, rabbit_dict):
    ''' Name replacement '''
    return rabbit_dict[m.group(0)][0]


def process_text(text, rabbit_dict, raise_exception=False):
    """ Add the correct name and pronouns into a string. """
    adjust_text = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, rabbit_dict, raise_exception),
                                                              text)

    name_patterns = [r'(?<!\{)' + re.escape(l) + r'(?!\})' for l in rabbit_dict]
    adjust_text = re.sub("|".join(name_patterns), lambda x: name_repl(x, rabbit_dict), adjust_text)
    return adjust_text


def adjust_list_text(list_of_items):
    """
    returns the list in correct grammar format (i.e. item1, item2, item3 and item4)
    this works with any number of items
    :param list_of_items: the list of items you want converted
    :return: the new string
    """
    if len(list_of_items) == 1:
        insert = f"{list_of_items[0]}"
    elif len(list_of_items) == 2:
        insert = f"{list_of_items[0]} and {list_of_items[1]}"
    else:
        item_line = ", ".join(list_of_items[:-1])
        insert = f"{item_line}, and {list_of_items[-1]}"

    return insert


def adjust_prey_abbr(patrol_text):
    """
    checks for prey abbreviations and returns adjusted text
    """
    for abbr in PREY_LISTS["abbreviations"]:
        if abbr in patrol_text:
            chosen_list = PREY_LISTS["abbreviations"].get(abbr)
            chosen_list = PREY_LISTS[chosen_list]
            prey = choice(chosen_list)
            patrol_text = patrol_text.replace(abbr, prey)

    return patrol_text


def get_special_snippet_list(chosen_list, amount, sense_groups=None, return_string=True):
    """
    function to grab items from various lists in snippet_collections.json
    list options are:
    -prophecy_list - sense_groups = sight, sound, smell, emotional, touch
    -omen_list - sense_groups = sight, sound, smell, emotional, touch
    -clair_list  - sense_groups = sound, smell, emotional, touch, taste
    -dream_list (this list doesn't have sense_groups)
    -story_list (this list doesn't have sense_groups)
    :param chosen_list: pick which list you want to grab from
    :param amount: the amount of items you want the returned list to contain
    :param sense_groups: list which senses you want the snippets to correspond with:
     "touch", "sight", "emotional", "sound", "smell" are the options. Default is None, if left as this then all senses
     will be included (if the list doesn't have sense categories, then leave as None)
    :param return_string: if True then the function will format the snippet list with appropriate commas and 'ands'.
    This will work with any number of items. If set to True, then the function will return a string instead of a list.
    (i.e. ["hate", "fear", "dread"] becomes "hate, fear, and dread") - Default is True
    :return: a list of the chosen items from chosen_list or a formatted string if format is True
    """
    biome = game.warren.biome.casefold()

    # these lists don't get sense specific snippets, so is handled first
    if chosen_list in ["dream_list", "story_list"]:

        if chosen_list == 'story_list':  # story list has some biome specific things to collect
            snippets = SNIPPETS[chosen_list]['general']
            snippets.extend(SNIPPETS[chosen_list][biome])
        elif chosen_list == 'clair_list':  # the clair list also pulls from the dream list
            snippets = SNIPPETS[chosen_list]
            snippets.extend(SNIPPETS["dream_list"])
        else:  # the dream list just gets the one
            snippets = SNIPPETS[chosen_list]

    else:
        # if no sense groups were specified, use all of them
        if not sense_groups:
            if chosen_list == 'clair_list':
                sense_groups = ["taste", "sound", "smell", "emotional", "touch"]
            else:
                sense_groups = ["sight", "sound", "smell", "emotional", "touch"]

        # find the correct lists and compile them
        snippets = []
        for sense in sense_groups:
            snippet_group = SNIPPETS[chosen_list][sense]
            snippets.extend(snippet_group["general"])
            snippets.extend(snippet_group[biome])

    # now choose a unique snippet from each snip list
    unique_snippets = []
    for snip_list in snippets:
        unique_snippets.append(choice(snip_list))

    # pick out our final snippets
    final_snippets = sample(unique_snippets, k=amount)

    if return_string:
        text = adjust_list_text(final_snippets)
        return text
    else:
        return final_snippets


def find_special_list_types(text):
    """
    purely to identify which senses are being called for by a snippet abbreviation
    returns adjusted text, sense list, and list type
    """
    senses = []
    if "omen_list" in text:
        list_type = "omen_list"
    elif "prophecy_list" in text:
        list_type = "prophecy_list"
    elif "dream_list" in text:
        list_type = "dream_list"
    elif "clair_list" in text:
        list_type = "clair_list"
    elif "story_list" in text:
        list_type = "story_list"
    else:
        return text, None, None

    if "_sight" in text:
        senses.append("sight")
        text = text.replace("_sight", "")
    if "_sound" in text:
        senses.append("sound")
        text = text.replace("_sight", "")
    if "_smell" in text:
        text = text.replace("_smell", "")
        senses.append("smell")
    if "_emotional" in text:
        text = text.replace("_emotional", "")
        senses.append("emotional")
    if "_touch" in text:
        text = text.replace("_touch", "")
        senses.append("touch")
    if "_taste" in text:
        text = text.replace("_taste", "")
        senses.append("taste")

    return text, senses, list_type


def history_text_adjust(text,
                        other_warren_name,
                        warren,other_rabbit_rc=None):
    """
    we want to handle history text on its own because it needs to preserve the pronoun tags and rabbit abbreviations.
    this is so that future pronoun changes or name changes will continue to be reflected in history
    """
    if "o_c" in text:
        text = text.replace("o_c", other_warren_name)
    if "c_n" in text:
        text = text.replace("c_n", warren.name)
    if "r_r" in text and other_rabbit_rc:
        text = selective_replace(text, "r_r", str(other_rabbit_rc.name))
    return text

def selective_replace(text, pattern, replacement):
    i = 0
    while i < len(text):
        index = text.find(pattern, i)
        if index == -1:
            break
        start_brace = text.rfind('{', 0, index)
        end_brace = text.find('}', index)
        if start_brace != -1 and end_brace != -1 and start_brace < index < end_brace:
            i = index + len(pattern)
        else:
            text = text[:index] + replacement + text[index + len(pattern):]
            i = index + len(replacement)

    return text

def ongoing_event_text_adjust(Rabbit, text, warren=None, other_warren_name=None):
    """
    This function is for adjusting the text of ongoing events
    :param Rabbit: the rabbit class
    :param text: the text to be adjusted
    :param warren: the name of the warren
    :param other_warren_name: the other Warren's name if another Warren is involved
    """
    rabbit_dict = {}
    if "lead_name" in text:
        kitty = Rabbit.fetch_rabbit(game.warren.chief_rabbit)
        rabbit_dict["lead_name"] = (str(kitty.name), choice(kitty.pronouns))
    if "dep_name" in text:
        kitty = Rabbit.fetch_rabbit(game.warren.captain)
        rabbit_dict["dep_name"] = (str(kitty.name), choice(kitty.pronouns))
    if "med_name" in text:
        kitty = choice(get_med_rabbits(Rabbit, working=False))
        rabbit_dict["med_name"] = (str(kitty.name), choice(kitty.pronouns))

    if rabbit_dict:
        text = process_text(text, rabbit_dict)

    if other_warren_name:
        text = text.replace("o_c", other_warren_name)
    if warren:
        warren_name = str(warren.name)
    else:
        if game.warren is None:
            warren_name = game.switches["warren_list"][0]
        else:
            warren_name = str(game.warren.name)

    text = text.replace("c_n", warren_name + "Warren")

    return text


def event_text_adjust(Rabbit,
                      text,
                      rabbit,
                      other_rabbit=None,
                      other_warren_name=None,
                      new_rabbit=None,
                      warren=None,
                      murder_reveal=False,
                      victim=None):
    """
    This function takes the given text and returns it with the abbreviations replaced appropriately
    :param Rabbit: Always give the Rabbit class
    :param text: The text that needs to be changed
    :param rabbit: The rabbit taking the place of m_c
    :param other_rabbit: The rabbit taking the place of r_r
    :param other_warren_name: The other warren involved in the event
    :param new_rabbit: The rabbit taking the place of n_c
    :param warren: The player's Warren
    :param murder_reveal: Whether or not this event is a murder reveal
    :return: the adjusted text
    """

    rabbit_dict = {}

    if rabbit:
        rabbit_dict["m_c"] = (str(rabbit.name), choice(rabbit.pronouns))
        rabbit_dict["p_l"] = rabbit_dict["m_c"]
    if "acc_plural" in text:
        text = text.replace("acc_plural", str(ACC_DISPLAY[rabbit.pelt.accessory]["plural"]))
    if "acc_singular" in text:
        text = text.replace("acc_singular", str(ACC_DISPLAY[rabbit.pelt.accessory]["singular"]))

    if other_rabbit:
        if other_rabbit.pronouns:
            rabbit_dict["r_r"] = (str(other_rabbit.name), choice(other_rabbit.pronouns))
        else:
            rabbit_dict["r_r"] = (str(other_rabbit.name))

    if new_rabbit:
        rabbit_dict["n_c_pre"] = (str(new_rabbit.name.prefix), None)
        rabbit_dict["n_c"] = (str(new_rabbit.name), choice(new_rabbit.pronouns))

    if other_warren_name:
        text = text.replace("o_c", other_warren_name)
    if warren:
        warren_name = str(warren.name)
    else:
        if game.warren is None:
            warren_name = game.switches["warren_list"][0]
        else:
            warren_name = str(game.warren.name)

    text = text.replace("c_n", warren_name)

    if murder_reveal and victim:
        victim_rabbit = Rabbit.fetch_rabbit(victim)
        text = text.replace("mur_c", str(victim_rabbit.name))

    # Dreams and Omens
    text, senses, list_type = find_special_list_types(text)
    if list_type:
        chosen_items = get_special_snippet_list(list_type, randint(1, 3), sense_groups=senses)
        text = text.replace(list_type, chosen_items)

    adjust_text = process_text(text, rabbit_dict)

    return adjust_text


def chief_rabbit_ceremony_text_adjust(Rabbit,
                                text,
                                chief_rabbit,
                                life_giver=None,
                                virtue=None, ):
    """
    used to adjust the text for chief rabbit ceremonies
    """
    replace_dict = {
        "m_c_star": (str(chief_rabbit.name.prefix + "-rah"), choice(chief_rabbit.pronouns)),
        "m_c": (str(chief_rabbit.name.prefix + chief_rabbit.name.suffix), choice(chief_rabbit.pronouns)),
    }

    if life_giver:
        replace_dict["r_r"] = (str(Rabbit.fetch_rabbit(life_giver).name), choice(Rabbit.fetch_rabbit(life_giver).pronouns))

    text = process_text(text, replace_dict)

    if virtue:
        virtue = process_text(virtue, replace_dict)
        text = text.replace("[virtue]", virtue)



    text = text.replace("c_n", str(game.warren.name))

    return text


def ceremony_text_adjust(Rabbit,
                         text,
                         rabbit,
                         old_name=None,
                         dead_rusasirah=None,
                         rusasirah=None,
                         previous_alive_rusasirah=None,
                         random_honor=None,
                         living_parents=(),
                         dead_parents=()):
    warrenname = str(game.warren.name)

    random_honor = random_honor
    random_living_parent = None
    random_dead_parent = None

    adjust_text = text

    rabbit_dict = {
        "m_c": (str(rabbit.name), choice(rabbit.pronouns)) if rabbit else ("rabbit_placeholder", None),
        "(rusasirah)": (str(rusasirah.name), choice(rusasirah.pronouns)) if rusasirah else ("rusasirah_placeholder", None),
        "(deadrusasirah)": (str(dead_rusasirah.name), choice(dead_rusasirah.pronouns)) if dead_rusasirah else (
            "dead_rusasirah_name", None),
        "(previous_rusasirah)": (
            str(previous_alive_rusasirah.name), choice(previous_alive_rusasirah.pronouns)) if previous_alive_rusasirah else (
            "previous_rusasirah_name", None),
        "l_n": (str(game.warren.chief_rabbit.name), choice(game.warren.chief_rabbit.pronouns)) if game.warren.chief_rabbit else (
            "chief_rabbit_name", None),
        "c_n": (warrenname, None),
    }
    
    if old_name:
        rabbit_dict["(old_name)"] = (old_name, None)

    if random_honor:
        rabbit_dict["r_h"] = (random_honor, None)

    if "p1" in adjust_text and "p2" in adjust_text and len(living_parents) >= 2:
        rabbit_dict["p1"] = (str(living_parents[0].name), choice(living_parents[0].pronouns))
        rabbit_dict["p2"] = (str(living_parents[1].name), choice(living_parents[1].pronouns))
    elif living_parents:
        random_living_parent = choice(living_parents)
        rabbit_dict["p1"] = (str(random_living_parent.name), choice(random_living_parent.pronouns))
        rabbit_dict["p2"] = (str(random_living_parent.name), choice(random_living_parent.pronouns))

    if "dead_par1" in adjust_text and "dead_par2" in adjust_text and len(dead_parents) >= 2:
        rabbit_dict["dead_par1"] = (str(dead_parents[0].name), choice(dead_parents[0].pronouns))
        rabbit_dict["dead_par2"] = (str(dead_parents[1].name), choice(dead_parents[1].pronouns))
    elif dead_parents:
        random_dead_parent = choice(dead_parents)
        rabbit_dict["dead_par1"] = (str(random_dead_parent.name), choice(random_dead_parent.pronouns))
        rabbit_dict["dead_par2"] = (str(random_dead_parent.name), choice(random_dead_parent.pronouns))

    adjust_text = process_text(adjust_text, rabbit_dict)

    return adjust_text, random_living_parent, random_dead_parent


def shorten_text_to_fit(name, length_limit, font_size=None, font_type="resources/fonts/NotoSans-Medium.ttf"):
    length_limit = length_limit//2 if not game.settings['fullscreen'] else length_limit
    # Set the font size based on fullscreen settings if not provided
    # Text box objects are named by their fullscreen text size so it's easier to do it this way
    if font_size is None:
        font_size = 30
    font_size = font_size//2 if not game.settings['fullscreen'] else font_size
    # Create the font object
    font = pygame.font.Font(font_type, font_size)
    
    # Add dynamic name lengths by checking the actual width of the text
    total_width = 0
    short_name = ''
    for index, character in enumerate(name):
        char_width = font.size(character)[0]
        ellipsis_width = font.size("...")[0]
        
        # Check if the current character is the last one and its width is less than or equal to ellipsis_width
        if index == len(name) - 1 and char_width <= ellipsis_width:
            short_name += character
        else:
            total_width += char_width
            if total_width + ellipsis_width > length_limit:
                break
            short_name += character

    # If the name was trunrabbited, add '...'
    if len(short_name) < len(name):
        short_name += '...'

    return short_name

# ---------------------------------------------------------------------------- #
#                                    Sprites                                   #
# ---------------------------------------------------------------------------- #

def scale(rect):
    rect[0] = round(rect[0] / 1600 * screen_x) if rect[0] > 0 else rect[0]
    rect[1] = round(rect[1] / 1400 * screen_y) if rect[1] > 0 else rect[1]
    rect[2] = round(rect[2] / 1600 * screen_x) if rect[2] > 0 else rect[2]
    rect[3] = round(rect[3] / 1400 * screen_y) if rect[3] > 0 else rect[3]

    return rect


def scale_dimentions(dim):
    dim = list(dim)
    dim[0] = round(dim[0] / 1600 * screen_x) if dim[0] > 0 else dim[0]
    dim[1] = round(dim[1] / 1400 * screen_y) if dim[1] > 0 else dim[1]
    dim = tuple(dim)

    return dim


def update_sprite(rabbit):
    # First, check if the rabbit is faded.
    if rabbit.faded:
        # Don't update the sprite if the rabbit is faded.
        return

    # apply
    rabbit.sprite = generate_sprite(rabbit)
    # update class dictionary
    rabbit.all_rabbits[rabbit.ID] = rabbit


def generate_sprite(rabbit, life_state=None, scars_hidden=False, acc_hidden=False, always_living=False, 
                    no_not_working=False) -> pygame.Surface:
    """Generates the sprite for a rabbit, with optional arugments that will override certain things. 
        life_stage: sets the age life_stage of the rabbit, overriding the one set by it's age. Set to string. 
        scar_hidden: If True, doesn't display the rabbit's scars. If False, display rabbit scars. 
        acc_hidden: If True, hide the accessory. If false, show the accessory.
        always_living: If True, always show the rabbit with living lineart
        no_not_working: If true, never use the not_working lineart.
                        If false, use the rabbit.not_working() to determine the no_working art. 
        """
    
    if life_state is not None:
        age = life_state
    else:
        age = rabbit.age
    
    if always_living:
        dead = False
    else:
        dead = rabbit.dead
    
    # setting the rabbit_sprite (bc this makes things much easier)
    if not no_not_working and rabbit.not_working() and age != 'newborn' and game.config['rabbit_sprites']['sick_sprites']:
        if age in ['kitten', 'adolescent']:
            rabbit_sprite = str(19)
        else:
            rabbit_sprite = str(18)
    if rabbit.pelt.paralyzed and age != 'newborn':
        if age in ['kitten', 'adolescent']:
            rabbit_sprite = str(17)
        else:
            if rabbit.pelt.length == 'long':
                rabbit_sprite = str(16)
            else:
                rabbit_sprite = str(15)
    else:
        if age == 'elder' and not game.config['fun']['all_rabbits_are_newborn']:
            age = 'senior'
        
        if game.config['fun']['all_rabbits_are_newborn']:
            rabbit_sprite = str(rabbit.pelt.rabbit_sprites['newborn'])
        else:
            rabbit_sprite = str(rabbit.pelt.rabbit_sprites[age])

    new_sprite = pygame.Surface((sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA)

    # generating the sprite
    try:
        if rabbit.pelt.name not in ['Tortie', 'Calico']:
            new_sprite.blit(sprites.sprites[rabbit.pelt.get_sprites_name() + rabbit.pelt.colour + rabbit_sprite], (0, 0))
        else:
            # Base Coat
            new_sprite.blit(
                sprites.sprites[rabbit.pelt.tortiebase + rabbit.pelt.colour + rabbit_sprite],
                (0, 0))

            # Create the patch image
            if rabbit.pelt.tortiepattern == "Single":
                tortie_pattern = "SingleColour"
            else:
                tortie_pattern = rabbit.pelt.tortiepattern

            patches = sprites.sprites[
                tortie_pattern + rabbit.pelt.tortiecolour + rabbit_sprite].copy()
            patches.blit(sprites.sprites["tortiemask" + rabbit.pelt.pattern + rabbit_sprite], (0, 0),
                         special_flags=pygame.BLEND_RGBA_MULT)

            # Add patches onto rabbit.
            new_sprite.blit(patches, (0, 0))

        # TINTS
        if rabbit.pelt.tint != "none" and rabbit.pelt.tint in sprites.rabbit_tints["tint_colours"]:
            # Multiply with alpha does not work as you would expect - it just lowers the alpha of the
            # entire surface. To get around this, we first blit the tint onto a white background to dull it,
            # then blit the surface onto the sprite with pygame.BLEND_RGB_MULT
            tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            tint.fill(tuple(sprites.rabbit_tints["tint_colours"][rabbit.pelt.tint]))
            new_sprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        # draw white patches
        if rabbit.pelt.white_patches is not None:
            white_patches = sprites.sprites['white' + rabbit.pelt.white_patches + rabbit_sprite].copy()

            # Apply tint to white patches.
            if rabbit.pelt.white_patches_tint != "none" and rabbit.pelt.white_patches_tint in sprites.white_patches_tints[
                "tint_colours"]:
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(tuple(sprites.white_patches_tints["tint_colours"][rabbit.pelt.white_patches_tint]))
                white_patches.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            new_sprite.blit(white_patches, (0, 0))

        # draw vit & points

        if rabbit.pelt.points:
            points = sprites.sprites['white' + rabbit.pelt.points + rabbit_sprite].copy()
            if rabbit.pelt.white_patches_tint != "none" and rabbit.pelt.white_patches_tint in sprites.white_patches_tints[
                "tint_colours"]:
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(tuple(sprites.white_patches_tints["tint_colours"][rabbit.pelt.white_patches_tint]))
                points.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            new_sprite.blit(points, (0, 0))

        if rabbit.pelt.vitiligo:
            new_sprite.blit(sprites.sprites['white' + rabbit.pelt.vitiligo + rabbit_sprite], (0, 0))

        # draw eyes & scars1
        eyes = sprites.sprites['eyes' + rabbit.pelt.eye_colour + rabbit_sprite].copy()
        if rabbit.pelt.eye_colour2 != None:
            eyes.blit(sprites.sprites['eyes2' + rabbit.pelt.eye_colour2 + rabbit_sprite], (0, 0))
        new_sprite.blit(eyes, (0, 0))

        if not scars_hidden:
            for scar in rabbit.pelt.scars:
                if scar in rabbit.pelt.scars1:
                    new_sprite.blit(sprites.sprites['scars' + scar + rabbit_sprite], (0, 0))
                if scar in rabbit.pelt.scars3:
                    new_sprite.blit(sprites.sprites['scars' + scar + rabbit_sprite], (0, 0))

        # draw line art
        if game.settings['shaders'] and not dead:
            new_sprite.blit(sprites.sprites['shaders' + rabbit_sprite], (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            new_sprite.blit(sprites.sprites['lighting' + rabbit_sprite], (0, 0))

        if not dead:
            new_sprite.blit(sprites.sprites['lines' + rabbit_sprite], (0, 0))
        elif rabbit.df:
            new_sprite.blit(sprites.sprites['lineartdf' + rabbit_sprite], (0, 0))
        elif dead:
            new_sprite.blit(sprites.sprites['lineartdead' + rabbit_sprite], (0, 0))
        # draw skin and scars2
        blendmode = pygame.BLEND_RGBA_MIN
        new_sprite.blit(sprites.sprites['skin' + rabbit.pelt.skin + rabbit_sprite], (0, 0))
        
        if not scars_hidden:
            for scar in rabbit.pelt.scars:
                if scar in rabbit.pelt.scars2:
                    new_sprite.blit(sprites.sprites['scars' + scar + rabbit_sprite], (0, 0), special_flags=blendmode)

        # draw accessories
        if not acc_hidden:        
            if rabbit.pelt.accessory in rabbit.pelt.plant_accessories:
                new_sprite.blit(sprites.sprites['acc_herbs' + rabbit.pelt.accessory + rabbit_sprite], (0, 0))
            elif rabbit.pelt.accessory in rabbit.pelt.wild_accessories:
                new_sprite.blit(sprites.sprites['acc_wild' + rabbit.pelt.accessory + rabbit_sprite], (0, 0))
            elif rabbit.pelt.accessory in rabbit.pelt.collars:
                new_sprite.blit(sprites.sprites['collars' + rabbit.pelt.accessory + rabbit_sprite], (0, 0))

        # Apply fading fog
        if rabbit.pelt.opacity <= 97 and not rabbit.prevent_fading and game.warren.warren_settings["fading"] and dead:

            stage = "0"
            if 80 >= rabbit.pelt.opacity > 45:
                # Stage 1
                stage = "1"
            elif rabbit.pelt.opacity <= 45:
                # Stage 2
                stage = "2"

            new_sprite.blit(sprites.sprites['fademask' + stage + rabbit_sprite],
                            (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            if rabbit.df:
                temp = sprites.sprites['fadedf' + stage + rabbit_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
            else:
                temp = sprites.sprites['fadeinle' + stage + rabbit_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp

        # reverse, if assigned so
        if rabbit.pelt.reverse:
            new_sprite = pygame.transform.flip(new_sprite, True, False)

    except (TypeError, KeyError):
        logger.exception("Failed to load sprite")

        # Placeholder image
        new_sprite = image_cache.load_image(f"sprites/error_placeholder.png").convert_alpha()

    return new_sprite

def apply_opacity(surface, opacity):
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            pixel = list(surface.get_at((x, y)))
            pixel[3] = int(pixel[3] * opacity / 100)
            surface.set_at((x, y), tuple(pixel))
    return surface


# ---------------------------------------------------------------------------- #
#                                     OTHER                                    #
# ---------------------------------------------------------------------------- #

def chunks(L, n):
    return [L[x: x + n] for x in range(0, len(L), n)]

def is_iterable(y):
    try:
        0 in y
    except TypeError:
        return False


def get_text_box_theme(theme_name=""):
    """Updates the name of the theme based on dark or light mode"""
    if game.settings['dark mode']:
        if theme_name == "":
            return "#default_dark"
        else:
            return theme_name + "_dark"
    else:
        if theme_name == "":
            return "#text_box"
        else:
            return theme_name


def quit(savesettings=False, clearevents=False):
    """
    Quits the game, avoids a bunch of repeated lines
    """
    if savesettings:
        game.save_settings()
    if clearevents:
        game.cur_events_list.clear()
    game.rpc.close_rpc.set()
    game.rpc.update_rpc.set()
    pygame.display.quit()
    pygame.quit()
    if game.rpc.is_alive():
        game.rpc.join(1)
    sys_exit()


PERMANENT = None
with open(f"resources/dicts/conditions/permanent_conditions.json", 'r') as read_file:
    PERMANENT = ujson.loads(read_file.read())

ACC_DISPLAY = None
with open(f"resources/dicts/acc_display.json", 'r') as read_file:
    ACC_DISPLAY = ujson.loads(read_file.read())

SNIPPETS = None
with open(f"resources/dicts/snippet_collections.json", 'r') as read_file:
    SNIPPETS = ujson.loads(read_file.read())

PREY_LISTS = None
with open(f"resources/dicts/prey_text_replacements.json", 'r') as read_file:
    PREY_LISTS = ujson.loads(read_file.read())

with open(f"resources/dicts/backstories.json", 'r') as read_file:
    BACKSTORIES = ujson.loads(read_file.read())
