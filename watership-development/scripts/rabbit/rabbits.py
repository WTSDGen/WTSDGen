from __future__ import annotations
from random import choice, randint, sample, random, choices, getrandbits, randrange
from typing import Dict, List, Any
import os.path
import itertools
import sys

from .history import History
from .skills import RabbitSkills
from ..housekeeping.datadir import get_save_dir
from ..events_module.generate_events import GenerateEvents

import ujson

from .names import Name
from .pelts import Pelt
from scripts.conditions import Illness, Injury, PermanentCondition, get_amount_rabbit_for_one_medic, \
    medical_rabbits_condition_fulfilled
import bisect

from scripts.utility import get_med_rabbits, get_personality_compatibility, event_text_adjust, update_sprite, \
    chief_rabbit_ceremony_text_adjust
from scripts.game_structure.game_essentials import game, screen
from scripts.rabbit_relations.relationship import Relationship
from scripts.game_structure import image_cache
from scripts.event_class import Single_Event
from .thoughts import Thoughts
from scripts.rabbit_relations.inheritance import Inheritance


class Rabbit():
    dead_rabbits = []
    used_screen = screen
    
    ages = [
        'newborn', 'kitten', 'adolescent', 'young adult', 'adult', 'senior adult',
        'senior'
    ]
    age_months = {
        'newborn': game.config["rabbit_ages"]["newborn"],
        'kitten': game.config["rabbit_ages"]["kitten"],
        'adolescent': game.config["rabbit_ages"]["adolescent"],
        'young adult': game.config["rabbit_ages"]["young adult"],
        'adult': game.config["rabbit_ages"]["adult"],
        'senior adult': game.config["rabbit_ages"]["senior adult"],
        'senior': game.config["rabbit_ages"]["senior"]
    }

    # This in is in reverse order: top of the list at the bottom
    rank_sort_order = [
        "newborn",
        "kitten",
        "elder",
        "rusasi",
        "rabbit",
        "healer rusasi",
        "healer",
        "owsla rusasi",
        "owsla",
        "captain",
        "chief rabbit"
    ]

    gender_tags = {'doe': 'F', 'buck': 'M'}

    # EX levels and ranges.
    # Ranges are inclusive to both bounds
    experience_levels_range = {
        "untrained": (0, 0),
        "trainee": (1, 50),
        "prepared": (51, 110),
        "competent": (110, 170),
        "proficient": (171, 240),
        "expert": (241, 320),
        "master": (321, 321)
    }

    default_pronouns = [
        {
            "subject": "they",
            "object": "them",
            "poss": "their",
            "inposs": "theirs",
            "self": "themself",
            "conju": 1
        },
        {
            "subject": "she",
            "object": "her",
            "poss": "her",
            "inposs": "hers",
            "self": "herself",
            "conju": 2
        },
        {
            "subject": "he",
            "object": "him",
            "poss": "his",
            "inposs": "his",
            "self": "himself",
            "conju": 2
        }
    ]

    all_rabbits: Dict[str, Rabbit] = {}  # ID: object
    outside_rabbits: Dict[str, Rabbit] = {}  # rabbits outside the warren
    id_iter = itertools.count()

    all_rabbits_list: List[Rabbit] = []

    grief_strings = {}

    def __init__(self,
                 prefix=None,
                 gender=None,
                 status="newborn",
                 backstory="warrenborn",
                 parent1=None,
                 parent2=None,
                 specsuffix_hidden=False,
                 ID=None,
                 months=None,
                 example=False,
                 faded=False,
                 skill_dict=None,
                 pelt:Pelt=None,
                 loading_rabbit=False,  # Set to true if you are loading a rabbit at start-up.
                 **kwargs
                 ):

        # This must be at the top. It's a smaller list of things to init, which is only for faded rabbits
        self.history = None
        if faded:
            self.ID = ID
            self.name = Name(status, prefix=prefix)
            self.parent1 = None
            self.parent2 = None
            self.adoptive_parents = []
            self.mate = []
            self.status = status
            self.pronouns = [self.default_pronouns[0].copy()]
            self.months = months
            self.dead_for = 0
            self.dead = True
            self.outside = False
            self.exiled = False
            self.inheritance = None # This should never be used, but just for safety
            if "df" in kwargs:
                self.df = kwargs["df"]
            else:
                self.df = False
            if months > 300:
                # Out of range, always elder
                self.age = 'senior'
            else:
                # In range
                for key_age in self.age_months.keys():
                    if months in range(self.age_months[key_age][0], self.age_months[key_age][1] + 1):
                        self.age = key_age

            self.set_faded()  # Sets the faded sprite and faded tag (self.faded = True)

            return

        self.generate_events = GenerateEvents()

        # Private attributes
        self._rusasirah = None  # plz
        self._experience = None
        self._months = None

        # Public attributes
        self.gender = gender
        self.status = status
        self.backstory = backstory
        self.age = None
        self.skills = RabbitSkills(skill_dict=skill_dict)
        self.personality = Personality(trait="troublesome", lawful=0, aggress=0,
                                       stable=0, social=0)
        self.parent1 = parent1
        self.parent2 = parent2
        self.adoptive_parents = []
        self.pelt = pelt if pelt else Pelt()
        self.former_rusasirah = []
        self.patrol_with_rusasirah = 0
        self.rusasi = []
        self.former_rusasis = []
        self.relationships = {}
        self.mate = []
        self.previous_mates = []
        self.pronouns = [self.default_pronouns[0].copy()]
        self.placement = None
        self.example = example
        self.dead = False
        self.exiled = False
        self.outside = False
        self.dead_for = 0  # months
        self.thought = ''
        self.genderalign = None
        self.birth_cooldown = 0
        self.illnesses = {}
        self.injuries = {}
        self.healed_condition = None
        self.also_got = False
        self.permanent_condition = {}
        self.df = False
        self.experience_level = None
        
        # Various behavior toggles
        self.no_kittens = False
        self.no_mates = False
        self.no_retire = False
        self.prevent_fading = False  # Prevents a rabbit from fading.
        
        self.faded_offspring = []  # Stores of a list of faded offspring, for relation tracking purposes

        self.faded = faded  # This is only used to flag rabbit that are faded, but won't be added to the faded list until
        # the next save.

        self.favourite = False

        self.specsuffix_hidden = specsuffix_hidden
        self.inheritance = None

        self.history = None

        # setting ID
        if ID is None:
            potential_id = str(next(Rabbit.id_iter))

            if game.warren:
                faded_rabbits = game.warren.faded_ids
            else:
                faded_rabbits = []

            while potential_id in self.all_rabbits or potential_id in faded_rabbits:
                potential_id = str(next(Rabbit.id_iter))
            self.ID = potential_id
        else:
            self.ID = ID

        # age and status
        if status is None and months is None:
            self.age = choice(self.ages)
        elif months is not None:
            self.months = months
            if months > 300:
                # Out of range, always elder
                self.age = 'senior'
            elif months == 0:
                self.age = 'newborn'
            else:
                # In range
                for key_age in self.age_months.keys():
                    if months in range(self.age_months[key_age][0], self.age_months[key_age][1] + 1):
                        self.age = key_age
        else:
            if status == 'newborn':
                self.age = 'newborn'
            elif status == 'kitten':
                self.age = 'kitten'
            elif status == 'elder':
                self.age = 'senior'
            elif status in ['rusasi', 'owsla rusasi', 'healer rusasi']:
                self.age = 'adolescent'
            else:
                self.age = choice(['young adult', 'adult', 'adult', 'senior adult'])
            self.months = randint(self.age_months[self.age][0], self.age_months[self.age][1])

        # backstory
        if self.backstory is None:
            self.backstory = 'warrenborn'
        else:
            self.backstory = self.backstory

        # sex!?!??!?!?!??!?!?!?!??
        if self.gender is None:
            self.gender = choice(["doe", "buck"])
        self.g_tag = self.gender_tags[self.gender]

        # These things should only run when generating a new rabbit, rather than loading one in.
        if not loading_rabbit:
            # trans rabbit chances
            trans_chance = randint(0, 50)
            nb_chance = randint(0, 75)
            if self.gender == "doe" and not self.status in ['newborn', 'kitten']:
                if trans_chance == 1:
                    self.genderalign = "trans buck"
                elif nb_chance == 1:
                    self.genderalign = "nonbinary"
                else:
                    self.genderalign = self.gender
            elif self.gender == "buck" and not self.status in ['newborn', 'kitten']:
                if trans_chance == 1:
                    self.genderalign = "trans doe"
                elif nb_chance == 1:
                    self.genderalign = "nonbinary"
                else:
                    self.genderalign = self.gender
            else:
                self.genderalign = self.gender

            """if self.genderalign in ["female", "trans female"]:
                self.pronouns = [self.default_pronouns[1].copy()]
            elif self.genderalign in ["male", "trans male"]:
                self.pronouns = [self.default_pronouns[2].copy()]"""

            # APPEARANCE
            self.pelt = Pelt.generate_new_pelt(self.gender, [Rabbit.fetch_rabbit(i) for i in (self.parent1, self.parent2) if i], self.age)
            
            #Personality
            self.personality = Personality(kitten_trait=self.is_baby())

            # experience and current patrol status
            if self.age in ['young', 'newborn']:
                self.experience = 0
            elif self.age in ['adolescent']:
                m = self.months
                self.experience = 0
                while m > Rabbit.age_months['adolescent'][0]:
                    ran = game.config["graduation"]["base_app_timeskip_ex"]
                    exp = choice(
                        list(range(ran[0][0], ran[0][1] + 1)) + list(range(ran[1][0], ran[1][1] + 1)))
                    self.experience += exp + 3
                    m -= 1
            elif self.age in ['young adult', 'adult']:
                self.experience = randint(Rabbit.experience_levels_range["prepared"][0],
                                          Rabbit.experience_levels_range["proficient"][1])
            elif self.age in ['senior adult']:
                self.experience = randint(Rabbit.experience_levels_range["competent"][0],
                                          Rabbit.experience_levels_range["expert"][1])
            elif self.age in ['senior']:
                self.experience = randint(Rabbit.experience_levels_range["competent"][0],
                                          Rabbit.experience_levels_range["master"][1])
            else:
                self.experience = 0
                
            if not skill_dict:
                self.skills = RabbitSkills.generate_new_rabbitskills(self.status, self.months)

        # In burrow status
        self.in_burrow = 1
        if "biome" in kwargs:
            biome = kwargs["biome"]
        elif game.warren is not None:
            biome = game.warren.biome
        else:
            biome = None
        # NAME
        # load_existing_name is needed so existing rabbits don't get their names changed/fixed for no reason
        if self.pelt is not None:
            self.name = Name(status,
                             prefix,
                             self.pelt.colour,
                             self.pelt.eye_colour,
                             self.pelt.name,
                             self.pelt.tortiepattern,
                             biome=biome,
                             specsuffix_hidden=self.specsuffix_hidden,
                             load_existing_name=loading_rabbit)
        else:
            self.name = Name(status, prefix, eyes=self.pelt.eye_colour, specsuffix_hidden=self.specsuffix_hidden,
                             load_existing_name = loading_rabbit)

        # Private Sprite
        self._sprite = None

        # SAVE RABBIT INTO ALL_RABBITS DICTIONARY IN RABBITS-CLASS
        self.all_rabbits[self.ID] = self

        if self.ID not in ["0", None]:
            Rabbit.insert_rabbit(self)

    def __repr__(self):
        return "RABBIT OBJECT:" + self.ID
    
    def __eq__(self, other):
        if not isinstance(other, Rabbit):
            return False
        
        return self.ID == other.ID
    
    def __hash__(self):
        return hash(self.ID)

    @property
    def rusasirah(self):
        """Return managed attribute '_rusasirah', which is the ID of the rabbit's rusasirah."""
        return self._rusasirah

    @rusasirah.setter
    def rusasirah(self, rusasirah_id: Any):
        """Makes sure Rabbit.rusasirah can only be None (no rusasirah) or a string (rusasirah ID)."""
        if rusasirah_id is None or isinstance(rusasirah_id, str):
            self._rusasirah = rusasirah_id
        else:
            print(f"Rusasirah ID {rusasirah_id} of type {type(rusasirah_id)} isn't valid :("
                  "\nRabbit.rusasirah has to be either None (no rusasirah) or the rusasirah's ID as a string.")

    def is_alive(self):
        return not self.dead

    def die(self, body: bool = True):
        """
        This is used to kill a rabbit.

        body - defaults to True, use this to mark if the body was recovered so
        that grief messages will align with body status

        May return some additional text to add to the death event.
        """
        if self.status == 'chief rabbit' and 'pregnant' in self.injuries:
            self.illnesses.clear()
            self.injuries = { key : value for (key, value) in self.injuries.items() if key == 'pregnant'}
        else:
            self.injuries.clear()
            self.illnesses.clear()
        
        # Deal with chief rabbit death
        text = ""
        if self.status == 'chief rabbit':
                self.dead = True
                game.just_died.append(self.ID)
                self.thought = 'Is surprised to see the Black Rabbit of Inlé.'
                if game.warren.instructor.df is False:
                    text = 'They\'ve lost their life and have travelled with the black rabbit.'
                else:
                    text = 'They\'ve lost their life and have travelled toward the dark.'
        else:
            self.dead = True
            game.just_died.append(self.ID)
            self.thought = 'Accepted their final sleep.'

        # Clear Relationships. 
        self.relationships = {}

        for app in self.rusasi.copy():
            fetched_rabbit = Rabbit.fetch_rabbit(app)
            if fetched_rabbit:
                fetched_rabbit.update_rusasirah()
        self.update_rusasirah()

        if game.warren.game_mode != 'classic' and not (self.outside or self.exiled):
            self.grief(body)

        if not self.outside:
            Rabbit.dead_rabbits.append(self)
            if game.warren.instructor.df is False:
                self.df = False
                game.warren.add_to_inle(self)
            elif game.warren.instructor.df is True:
                self.df = True
                self.thought = "Is startled to find themselves lost in the dark."
                game.warren.add_to_darkforest(self)
        else:
            self.thought = "Is fascinated by the new ghostly world they've stumbled into"
            game.warren.add_to_unknown(self)

        return text

    def exile(self):
        """This is used to send a rabbit into exile. This removes the rabbit's status and gives them a special 'exiled'
        status."""
        self.exiled = True
        self.outside = True
        self.status = 'exiled'
        if self.personality.trait == 'vengeful':
            self.thought = "Swears their revenge for being exiled"
        else:
            self.thought = "Is shocked that they have been exiled"
        for app in self.rusasi:
            fetched_rabbit = Rabbit.fetch_rabbit(app)
            if fetched_rabbit:
                fetched_rabbit.update_rusasirah()
        self.update_rusasirah()
    
    def grief(self, body: bool):
        """
        compiles grief month event text
        """
        if body is True:
            body_status = 'body'
        else:
            body_status = 'no_body'
    
        # Keep track is the body was treated with rosemary. 
        body_treated = False
    
        # apply grief to rabbits with high positive relationships to dead rabbit
        for rabbit in Rabbit.all_rabbits.values():
            if rabbit.dead or rabbit.outside or rabbit.months < 1:
                continue
            
            to_self = rabbit.relationships.get(self.ID)
            if not isinstance(to_self, Relationship):
                continue
            
            family_relation = self.familial_grief(living_rabbit=rabbit)
            very_high_values = []
            high_values = []
            
            if to_self.romantic_love > 55:
                very_high_values.append("romantic")
            if to_self.romantic_love > 40:
                high_values.append("romantic")
            
            if to_self.platonic_like > 50:
                very_high_values.append("platonic")
            if to_self.platonic_like > 30:
                high_values.append("platonic")
            
            if to_self.admiration > 70:
                very_high_values.append("admiration")
            if to_self.admiration > 50:
                high_values.append("admiration")
                
            if to_self.comfortable > 60:
                very_high_values.append("comfort")
            if to_self.comfortable > 40:
                high_values.append("comfort")
                
            if to_self.trust > 70:
                very_high_values.append("trust")
            if to_self.trust > 50:
                high_values.append("trust")
            
            
            major_chance = 0
            if very_high_values:
                # major grief eligible rabbits. 
                
                major_chance = 3
                if rabbit.personality.stability < 5:
                    major_chance -= 1
                
                # decrease major grief chance if grave herbs are used
                if not body_treated and "rosemary" in game.warren.herbs:  
                    body_treated = True
                    game.warren.herbs["rosemary"] -= 1
                    if game.warren.herbs["rosemary"] <= 0:
                        game.warren.herbs.pop("rosemary")
                    game.herb_events_list.append(f"Rosemary was used for {self.name}'s body.")
                
                if body_treated:
                    major_chance -= 1
                
            
            # If major_chance is not 0, there is a chance for major grief
            grief_type = None
            if major_chance and not int(random() * major_chance):
                
                grief_type = "major"
                
                possible_strings = []
                for x in very_high_values:
                    possible_strings.extend(
                        self.generate_events.possible_death_reactions(family_relation, x, rabbit.personality.trait,
                                                                body_status)
                    )
                
                if not possible_strings:
                    print("No grief strings")
                    continue
                
                text = choice(possible_strings)
                text += ' ' + choice(MINOR_MAJOR_REACTION["major"])
                text = event_text_adjust(Rabbit, text, self, rabbit)
                
                # grief the rabbit
                if game.warren.game_mode != 'classic':
                    rabbit.get_ill("grief stricken", event_triggered=True, severity="major")
            
            # If major grief fails, but there are still very_high or high values, 
            # it can fail to to minor grief. If they have a family relation, bypass the roll. 
            elif (very_high_values or high_values) and \
                    (family_relation != "general" or not int(random() * 5)):
            
                grief_type = "minor"
                
                # These minor grief message will be applied as thoughts. 
                minor_grief_messages = (
                            "Told a fond story at r_r's vigil",
                            "Bargains with Frith, begging them to send r_r back",
                            "Sat all night at r_r's vigil",
                            "Will never forget r_r",
                            "Prays that r_r is safe with Inlé-rah.",
                            "Misses the warmth that r_r brought to {PRONOUN/m_c/poss} life",
                            "Is mourning r_r"
                        )
                
                if body: 
                    minor_grief_messages += (
                        "Helped bury r_r, leaving {PRONOUN/r_r/poss} favorite flowers at the grave",
                        "Slips out of warren to visit r_r's grave"
                    )

                
                text = choice(minor_grief_messages)
                
            if grief_type:
                #Generate the event:
                if rabbit.ID not in Rabbit.grief_strings:
                    Rabbit.grief_strings[rabbit.ID] = []
                
                Rabbit.grief_strings[rabbit.ID].append((text, (self.ID, rabbit.ID), grief_type))
                continue
            
            
            # Negative "grief" messages are just for flavor. 
            high_values = []
            very_high_values = []
            if to_self.dislike > 50:
                high_values.append("dislike")
                
            if to_self.jealousy > 50:
                high_values.append("jealousy")
            
            if high_values:
                #Generate the event:
                possible_strings = []
                for x in high_values:
                    possible_strings.extend(
                        self.generate_events.possible_death_reactions(family_relation, x, rabbit.personality.trait,
                                                                body_status)
                    )
                
                text = event_text_adjust(Rabbit, choice(possible_strings), self, rabbit)
                if rabbit.ID not in Rabbit.grief_strings:
                    Rabbit.grief_strings[rabbit.ID] = []
                
                Rabbit.grief_strings[rabbit.ID].append((text, (self.ID, rabbit.ID), "negative"))
                

    def familial_grief(self, living_rabbit: Rabbit):
        """
        returns relevant grief strings for family members, if no relevant strings then returns None
        """
        dead_rabbit = self

        if dead_rabbit.is_parent(living_rabbit):
            return "child"
        elif living_rabbit.is_parent(dead_rabbit):
            return "parent"
        elif dead_rabbit.is_sibling(living_rabbit):
            return "sibling"
        else:
            return "general"

    def gone(self):
        """ Makes a Warren rabbit an "outside" rabbit. Handles removing them from special positions, and removing
        rusasirahs and rusasi. """
        self.outside = True
        
        if self.status in ['chief rabbit', 'rabbit']:
            self.status_change("rabbit")

        for app in self.rusasi.copy():
            app_ob = Rabbit.fetch_rabbit(app)
            if app_ob:
                app_ob.update_rusasirah()
        self.update_rusasirah()
        for x in self.rusasi:
            Rabbit.fetch_rabbit(x).update_rusasirah()
        game.warren.add_to_outside(self)

    def add_to_warren(self) -> list:
        """ Makes a "outside rabbit" a Warren rabbit. Returns a list of any additional rabbits that
            are coming with them. """
        self.outside = False

        game.warren.add_to_warren(self)

        # check if there are kittens under 12 months with this rabbit and also add them to the warren
        children = self.get_children()
        ids = []
        for child_id in children:
            child = Rabbit.all_rabbits[child_id]
            if child.outside and not child.exiled and child.months < 12:
                child.add_to_warren()
                ids.append(child_id)
        
        return ids

    def status_change(self, new_status, resort=False):
        """ Changes the status of a rabbit. Additional functions are needed if you want to make a rabbit a chief rabbit or captain.
            new_status = The new status of a rabbit. Can be 'rusasi', 'healer rusasi', 'rabbit'
                        'healer', 'elder'.
            resort = If sorting type is 'rank', and resort is True, it will resort the rabbit list. This should
                    only be true for non-timeskip status changes. """
        old_status = self.status
        self.status = new_status
        self.name.status = new_status

        self.update_rusasirah()
        for app in self.rusasi.copy():
            fetched_rabbit = Rabbit.fetch_rabbit(app)
            if isinstance(fetched_rabbit, Rabbit):
                fetched_rabbit.update_rusasirah()

        # If they have any rusasis, make sure they are still valid:
        if old_status == "healer":
            game.warren.remove_healer(self)

        # updates rusasirahs
        if self.status == 'rusasi':
            pass

        elif self.status == 'healer rusasi':
            pass

        elif self.status == 'rabbit':
            if old_status == 'chief rabbit':
                if game.warren.chief_rabbit:
                    if game.warren.chief_rabbit.ID == self.ID:
                        game.warren.chief_rabbit = None
                        game.warren.chief_rabbitpredecessors += 1

                    # don't remove the check for game.warren, this is needed for tests
            if game.warren and game.warren.captain:
                if game.warren.captain.ID == self.ID:
                    game.warren.captain = None
                    game.warren.captain_predecessors += 1

        elif self.status == 'healer':
            if game.warren is not None:
                game.warren.new_healer(self)

        elif self.status == 'elder':
            if old_status == 'chief rabbit':
                if game.warren.chief_rabbit:
                    if game.warren.chief_rabbit.ID == self.ID:
                        game.warren.chief_rabbit = None
                        game.warren.chief_rabbitpredecessors += 1

            if game.warren.captain:
                if game.warren.captain.ID == self.ID:
                    game.warren.captain = None
                    game.warren.captain_predecessors += 1

        elif self.status == 'owsla':
            pass

        elif self.status == 'owsla rusasi':
            pass

        # update class dictionary
        self.all_rabbits[self.ID] = self

        # If we have it sorted by rank, we also need to re-sort
        if game.sort_type == "rank" and resort:
            Rabbit.sort_rabbits()

    
    def rank_change_traits_skill(self, rusasirah):
        """Updates trait and skill upon ceremony"""  

        if self.status in ["rabbit", "healer", "owsla"]:
            # Give a couple doses of rusasirah influence:
            if rusasirah:
                max = randint(0, 2)
                i = 0
                while max > i:
                    i += 1
                    affect_personality = self.personality.rusasirah_influence(Rabbit.fetch_rabbit(rusasirah))
                    affect_skills = self.skills.rusasirah_influence(Rabbit.fetch_rabbit(rusasirah))
                    if affect_personality:
                        History.add_facet_rusasirah_influence(self, affect_personality[0], affect_personality[1], affect_personality[2])
                    if affect_skills:
                        History.add_skill_rusasirah_influence(self, affect_skills[0], affect_skills[1], affect_skills[2])
            
            History.add_rusasirah_skill_influence_strings(self)
            History.add_rusasirah_facet_influence_strings(self)
        return

    def manage_outside_trait(self):
        """To be run every month on outside rabbits
            to keep trait and skills making sense."""
        if not (self.outside or self.exiled):
            return
        
        self.personality.set_kitten(self.is_baby()) #Update kitten trait stuff
        

    def describe_rabbit(self, short=False):
        """ Generates a string describing the rabbit's appearance and gender. Mainly used for generating
        the allegiances. If short is true, it will generate a very short one, with the minimal amount of information. """
        output = Pelt.describe_appearance(self, short)
        # Add "a" or "an"
        if output[0].lower() in "aiou":
            output = f"an {output}"
        else:
            output = f"a {output}"

        return output

    def describe_eyes(self):
        colour = str(self.pelt.eye_colour).lower()
        colour2 = str(self.pelt.eye_colour2).lower()

        if colour == 'palegreen':
            colour = 'pale green'
        elif colour == 'darkblue':
            colour = 'dark blue'
        elif colour == 'paleblue':
            colour = 'pale blue'
        elif colour == 'paleyellow':
            colour = 'pale yellow'
        elif colour == 'heatherblue':
            colour = 'heather blue'
        elif colour == 'blue2':
            colour = 'blue'
        elif colour == 'sunlitice':
            colour = 'sunlit ice'
        elif colour == 'greenyellow':
            colour = 'green-yellow'
        if self.pelt.eye_colour2:
            if colour2 == 'palegreen':
                colour2 = 'pale green'
            if colour2 == 'darkblue':
                colour2 = 'dark blue'
            if colour2 == 'paleblue':
                colour2 = 'pale blue'
            if colour2 == 'paleyellow':
                colour2 = 'pale yellow'
            if colour2 == 'heatherblue':
                colour2 = 'heather blue'
            if colour2 == 'sunlitice':
                colour2 = 'sunlit ice'
            if colour2 == 'greenyellow':
                colour2 = 'green-yellow'
            colour = colour + ' and ' + colour2
        return colour

    def convert_history(self, died_by, scar_events):
        """
        this is to handle old history save conversions
        """
        deaths = []
        if died_by:
            for death in died_by:
                deaths.append(
                    {
                        "involved": None,
                        "text": death,
                        "month": "?"
                    }
                )
        scars = []
        if scar_events:
            for scar in scar_events:
                scars.append(
                    {
                        "involved": None,
                        "text": scar,
                        "month": "?"
                    }
                )
        self.history = History(
            died_by=deaths,
            scar_events=scars,
        )

    def load_history(self):
        try:
            if game.switches['warren_name'] != '':
                warrenname = game.switches['warren_name']
            else:
                warrenname = game.switches['warren_list'][0]
        except IndexError:
            print('WARNING: History failed to load, no Warren in game.switches?')
            return

        history_directory = get_save_dir() + '/' + warrenname + '/history/'
        rabbit_history_directory = history_directory + self.ID + '_history.json'

        if not os.path.exists(rabbit_history_directory):
            self.history = History(
                beginning={},
                rusasirah_influence={},
                app_ceremony={},
                lead_ceremony=None,
                possible_history={},
                died_by=[],
                scar_events=[],
                murder={},
            )
            return
        try:
            with open(rabbit_history_directory, 'r') as read_file:
                history_data = ujson.loads(read_file.read())
                self.history = History(
                    beginning=history_data["beginning"] if "beginning" in history_data else {},
                    rusasirah_influence=history_data[
                        'rusasirah_influence'] if "rusasirah_influence" in history_data else {},
                    app_ceremony=history_data['app_ceremony'] if "app_ceremony" in history_data else {},
                    lead_ceremony=history_data['lead_ceremony'] if "lead_ceremony" in history_data else None,
                    possible_history=history_data['possible_history'] if "possible_history" in history_data else {},
                    died_by=history_data['died_by'] if "died_by" in history_data else [],
                    scar_events=history_data['scar_events'] if "scar_events" in history_data else [],
                    murder=history_data['murder'] if "murder" in history_data else {},
                )
        except:
            self.history = None
            print(f'WARNING: There was an error reading the history file of rabbit #{self} or their history file was '
                  f'empty. Default history info was given. Close game without saving if you have save information '
                  f'you\'d like to preserve!')

    def save_history(self, history_dir):
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

        history_dict = History.make_dict(self)
        try:
            game.safe_save(history_dir + '/' + self.ID + '_history.json', history_dict)
        except:
            self.history = History(
                beginning={},
                rusasirah_influence={},
                app_ceremony={},
                lead_ceremony=None,
                possible_history={},
                died_by=[],
                scar_events=[],
                murder={},
            )

            print(f"WARNING: saving history of rabbit #{self.ID} didn't work")
            

    def generate_lead_ceremony(self):
        """
        here we create a chief rabbit ceremony and add it to the history
        :param rabbit: rabbit object
        """

        # determine which dict we're pulling from
        if game.warren.instructor.df:
            inle = False
            ceremony_dict = LEAD_CEREMONY_DF
        else:
            inle = True
            ceremony_dict = LEAD_CEREMONY_SC

        # ---------------------------------------------------------------------------- #
        #                                    INTRO                                     #
        # ---------------------------------------------------------------------------- #
        all_intros = ceremony_dict["intros"]

        # filter the intros
        possible_intros = []
        for intro in all_intros:
            tags = all_intros[intro]["tags"]

            if game.warren.age != 0 and "new_warren" in tags:
                continue
            elif game.warren.age == 0 and "new_warren" not in tags:
                continue

            if all_intros[intro]["lead_trait"]:
                if self.personality.trait not in all_intros[intro]["lead_trait"]:
                    continue
            possible_intros.append(all_intros[intro])

        # choose and adjust text
        chosen_intro = choice(possible_intros)
        if chosen_intro:
            intro = choice(chosen_intro["text"])
            intro = chief_rabbit_ceremony_text_adjust(Rabbit,
                                                intro,
                                                self,
                                                )
        else:
            intro = 'this should not appear'
        # ---------------------------------------------------------------------------- #
        #                                    OUTRO                                     #
        # ---------------------------------------------------------------------------- #

        # get the outro
        all_outros = ceremony_dict["outros"]

        possible_outros = []
        for outro in all_outros:
            tags = all_outros[outro]["tags"]

            if game.warren.age != 0 and "new_warren" in tags:
                continue
            elif game.warren.age == 0 and "new_warren" not in tags:
                continue

            if all_outros[outro]["lead_trait"]:
                if self.personality.trait not in all_outros[outro]["lead_trait"]:
                    continue
            possible_outros.append(all_outros[outro])

        chosen_outro = choice(possible_outros)

        if chosen_outro:

            giver = None
            outro = choice(chosen_outro["text"])
            outro = chief_rabbit_ceremony_text_adjust(Rabbit,
                                                outro,
                                                chief_rabbit=self,
                                                )
        else:
            outro = 'this should not appear'

        full_ceremony = "<br><br>".join([intro, outro])
        return full_ceremony

    # ---------------------------------------------------------------------------- #
    #                              month skip functions                             #
    # ---------------------------------------------------------------------------- #

    def one_month(self):
        """Handles a month skip for an alive rabbit. """
        
        
        old_age = self.age
        self.months += 1
        if self.months == 1 and self.status == "newborn":
            self.status = 'kitten'
        self.in_burrow = 1
        
        if self.exiled or self.outside:
            # this is handled in events.py
            self.personality.set_kitten(self.is_baby())
            self.thoughts()
            return

        if self.dead:
            self.thoughts()
            return
        
        if old_age != self.age:
            # Things to do if the age changes
            self.personality.facet_wobble(max=2)
        
        # Set personality to correct type
        self.personality.set_kitten(self.is_baby())
        # Upon age-change

        if self.status in ['rusasi', 'owsla rusasi', 'healer rusasi']:
            self.update_rusasirah()

    def thoughts(self):
        """ Generates a thought for the rabbit, which displays on their profile. """
        all_rabbits = self.all_rabbits
        other_rabbit = choice(list(all_rabbits.keys()))
        game_mode = game.switches['game_mode']
        biome = game.switches['biome']
        burrow = game.switches['burrow_bg']
        dead_chance = getrandbits(4)
        try:
            season = game.warren.current_season
        except:
            season = None

        # this figures out where the rabbit is
        where_kitty = None
        if not self.dead and not self.outside:
            where_kitty = "inside"
        elif self.dead and not self.df and not self.outside:
            where_kitty = 'inle'
        elif self.dead and self.df:
            where_kitty = 'hell'
        elif self.dead and self.outside:
            where_kitty = 'UR'
        elif not self.dead and self.outside:
            where_kitty = 'outside'
        # get other rabbit
        i = 0
        # for rabbits inside the warren
        if where_kitty == 'inside':
            while other_rabbit == self.ID and len(all_rabbits) > 1 \
                    or (all_rabbits.get(other_rabbit).dead and dead_chance != 1) \
                    or (other_rabbit not in self.relationships):
                other_rabbit = choice(list(all_rabbits.keys()))
                i += 1
                if i > 100:
                    other_rabbit = None
                    break
        # for dead rabbits
        elif where_kitty in ['inle', 'hell', 'UR']:
            while other_rabbit == self.ID and len(all_rabbits) > 1:
                other_rabbit = choice(list(all_rabbits.keys()))
                i += 1
                if i > 100:
                    other_rabbit = None
                    break
        # for rabbits currently outside
        # it appears as for now, pets and hlessis can only think about outsider rabbits
        elif where_kitty == 'outside':
            while other_rabbit == self.ID and len(all_rabbits) > 1 \
                    or (other_rabbit not in self.relationships):
                '''or (self.status in ['pet', 'hlessi'] and not all_rabbits.get(other_rabbit).outside):'''
                other_rabbit = choice(list(all_rabbits.keys()))
                i += 1
                if i > 100:
                    other_rabbit = None
                    break

        other_rabbit = all_rabbits.get(other_rabbit)

        # get chosen thought
        chosen_thought = Thoughts.get_chosen_thought(self, other_rabbit, game_mode, biome, season, burrow)

        chosen_thought = event_text_adjust(Rabbit, chosen_thought, self, other_rabbit)

        # insert thought
        self.thought = str(chosen_thought)

    def relationship_interaction(self):
        """Randomly choose a rabbit of the Warren and have a interaction with them."""
        # if the rabbit has no relationships, skip
        #if not self.relationships or len(self.relationships) < 1:
        #    return

        rabbits_to_choose = [iter_rabbit for iter_rabbit in Rabbit.all_rabbits.values() if iter_rabbit.ID != self.ID and \
                          not iter_rabbit.outside and not iter_rabbit.exiled and not iter_rabbit.dead]
        # if there are not rabbits to interact, stop
        if len(rabbits_to_choose) < 1:
            return

        chosen_rabbit = choice(rabbits_to_choose)
        if chosen_rabbit.ID not in self.relationships:
            self.create_one_relationship(chosen_rabbit)
        relevant_relationship = self.relationships[chosen_rabbit.ID]
        relevant_relationship.start_interaction()

        if game.game_mode == "classic":
            return
        # handle contact with ill rabbit if
        if self.is_ill():
            relevant_relationship.rabbit_to.contact_with_ill_rabbit(self)
        if relevant_relationship.rabbit_to.is_ill():
            self.contact_with_ill_rabbit(relevant_relationship.rabbit_to)

    def month_skip_illness(self, illness):
        """handles the month skip for illness"""
        if not self.is_ill():
            return True

        if self.illnesses[illness]["event_triggered"]:
            self.illnesses[illness]["event_triggered"] = False
            return True

        mortality = self.illnesses[illness]["mortality"]

        # chief rabbit should have a higher chance of death
        if self.status == "chief rabbit" and mortality != 0:
            mortality = int(mortality * 0.7)
            if mortality == 0:
                mortality = 1

        if mortality and not int(random() * mortality):
            if self.status == "chief rabbit":
                text = f"{self.name} died to {illness}."
                # game.health_events_list.append(text)
                # game.birth_death_events_list.append(text)
                game.cur_events_list.append(Single_Event(text, ["birth_death", "health"], game.warren.chief_rabbit.ID))
            self.die()
            return False

        months_with = game.warren.age - self.illnesses[illness]["month_start"]

        if self.illnesses[illness]["duration"] - months_with <= 0:
            self.healed_condition = True
            return False

    def month_skip_injury(self, injury):
        """handles the month skip for injury"""
        if not self.is_injured():
            return True

        if self.injuries[injury]["event_triggered"] is True:
            self.injuries[injury]["event_triggered"] = False
            return True

        mortality = self.injuries[injury]["mortality"]

        # chief rabbit should have a higher chance of death
        if self.status == "chief rabbit" and mortality != 0:
            mortality = int(mortality * 0.7)
            if mortality == 0:
                mortality = 1

        if mortality and not int(random() * mortality):
            self.die()
            return False

        months_with = game.warren.age - self.injuries[injury]["month_start"]

        # if the rabbit has an infected wound, the wound shouldn't heal till the illness is cured
        if not self.injuries[injury]["complirabbition"] and self.injuries[injury]["duration"] - months_with <= 0:
            self.healed_condition = True
            return False

    def month_skip_permanent_condition(self, condition):
        """handles the month skip for permanent conditions"""
        if not self.is_disabled():
            return "skip"

        if self.permanent_condition[condition]["event_triggered"]:
            self.permanent_condition[condition]["event_triggered"] = False
            return "skip"

        mortality = self.permanent_condition[condition]["mortality"]
        months_until = self.permanent_condition[condition]["months_until"]
        born_with = self.permanent_condition[condition]["born_with"]

        # handling the countdown till a congenital condition is revealed
        if months_until is not None and months_until >= 0 and born_with is True:
            self.permanent_condition[condition]["months_until"] = int(months_until - 1)
            self.permanent_condition[condition]["months_with"] = 0
            if self.permanent_condition[condition]["months_until"] != -1:
                return "skip"
        if self.permanent_condition[condition]["months_until"] == -1 and \
                self.permanent_condition[condition]["born_with"] is True:
            self.permanent_condition[condition]["months_until"] = -2
            return "reveal"

        # chief rabbit should have a LOWER chance of death -- currently, this is higher, fix later
        '''if self.status == "chief rabbit" and mortality != 0:
            mortality = int(mortality * 0.7)
            if mortality == 0:
                mortality = 1'''

        if mortality and not int(random() * mortality):
            self.die()
            return "continue"

    # ---------------------------------------------------------------------------- #
    #                                   relative                                   #
    # ---------------------------------------------------------------------------- #
    def get_parents(self):
        """Returns list containing parents of rabbit(id)."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return self.inheritance.parents.keys()

    def get_siblings(self):
        """Returns list of the siblings(id)."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return self.inheritance.siblings.keys()

    def get_children(self):
        """Returns list of the children (ids)."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return self.inheritance.kits.keys()

    def is_grandparent(self, other_rabbit: Rabbit):
        """Check if the rabbit is the grandparent of the other rabbit."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_rabbit.ID in self.inheritance.grand_kits.keys()

    def is_parent(self, other_rabbit: Rabbit):
        """Check if the rabbit is the parent of the other rabbit."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_rabbit.ID in self.inheritance.kits.keys()

    def is_sibling(self, other_rabbit: Rabbit):
        """Check if the rabbits are siblings."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_rabbit.ID in self.inheritance.siblings.keys()

    def is_littermate(self, other_rabbit: Rabbit):
        """Check if the rabbits are littermates."""
        if other_rabbit.ID not in self.inheritance.siblings.keys():
            return False
        litter_mates = [key for key, value in self.inheritance.siblings.items() if
                        "litter mates" in value["additional"]]
        return other_rabbit.ID in litter_mates

    def is_uncle_aunt(self, other_rabbit):
        """Check if the rabbits are related as uncle/aunt and niece/nephew."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_rabbit.ID in self.inheritance.siblings_kits.keys()

    def is_cousin(self, other_rabbit):
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        return other_rabbit.ID in self.inheritance.cousins.keys()

    def is_related(self, other_rabbit, cousin_allowed):
        """Checks if the given rabbit is related to the current rabbit, according to the inheritance."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        if cousin_allowed:
            return other_rabbit.ID in self.inheritance.all_but_cousins
        return other_rabbit.ID in self.inheritance.all_involved

    def get_relatives(self, cousin_allowed=True) -> list:
        """Returns a list of ids of all nearly related ancestors."""
        if not self.inheritance:
            self.inheritance = Inheritance(self)
        if cousin_allowed:
            return self.inheritance.all_involved
        return self.inheritance.all_but_cousins

    # ---------------------------------------------------------------------------- #
    #                                  conditions                                  #
    # ---------------------------------------------------------------------------- #

    def get_ill(self, name, event_triggered=False, lethal=True, severity='default'):
        """
        use to make a rabbit ill.
        name = name of the illness you want the rabbit to get
        event_triggered = make True to have this illness skip the illness_monthskip for 1 month
        lethal = set True to leave the illness mortality rate at its default level.
                 set False to force the illness to have 0 mortality
        severity = leave 'default' to keep default severity, otherwise set to the desired severity
                   ('minor', 'major', 'severe')
        """
        if game.warren.game_mode == "classic":
            return
        
        if name not in ILLNESSES:
            print(f"WARNING: {name} is not in the illnesses collection.")
            return
        if name == 'kittencough' and self.status != 'kitten':
            return

        illness = ILLNESSES[name]
        mortality = illness["mortality"][self.age]
        med_mortality = illness["medicine_mortality"][self.age]
        if severity == 'default':
            illness_severity = illness["severity"]
        else:
            illness_severity = severity

        duration = illness['duration']
        med_duration = illness['medicine_duration']

        amount_per_med = get_amount_rabbit_for_one_medic(game.warren)

        if medical_rabbits_condition_fulfilled(Rabbit.all_rabbits.values(), amount_per_med):
            duration = med_duration
        if severity != 'minor':
            duration += randrange(-1, 1)
        if duration == 0:
            duration = 1

        if game.warren.game_mode == "cruel season":
            if mortality != 0:
                mortality = int(mortality * 0.5)
                med_mortality = int(med_mortality * 0.5)

                # to prevent an illness gets no mortality, check and set it to 1 if needed
                if mortality == 0 or med_mortality == 0:
                    mortality = 1
                    med_mortality = 1
        if lethal is False:
            mortality = 0

        new_illness = Illness(
            name=name,
            severity=illness_severity,
            mortality=mortality,
            infectiousness=illness["infectiousness"],
            duration=duration,
            medicine_duration=illness["medicine_duration"],
            medicine_mortality=med_mortality,
            risks=illness["risks"],
            event_triggered=event_triggered
        )

        if new_illness.name not in self.illnesses:
            self.illnesses[new_illness.name] = {
                "severity": new_illness.severity,
                "mortality": new_illness.current_mortality,
                "infectiousness": new_illness.infectiousness,
                "duration": new_illness.duration,
                "month_start": game.warren.age if game.warren else 0,
                "risks": new_illness.risks,
                "event_triggered": new_illness.new
            }

    def get_injured(self, name, event_triggered=False, lethal=True, severity='default'):
        if game.warren.game_mode == "classic":
            return
        
        if name not in INJURIES:
            if name not in INJURIES:
                print(f"WARNING: {name} is not in the injuries collection.")
            return

        if name == 'mangled tail' and 'NOTAIL' in self.pelt.scars:
            return
        if name == 'torn ear' and 'NOEAR' in self.pelt.scars:
            return

        injury = INJURIES[name]
        mortality = injury["mortality"][self.age]
        duration = injury['duration']
        med_duration = injury['medicine_duration']

        if severity == 'default':
            injury_severity = injury["severity"]
        else:
            injury_severity = severity

        if medical_rabbits_condition_fulfilled(Rabbit.all_rabbits.values(), get_amount_rabbit_for_one_medic(game.warren)):
            duration = med_duration
        if severity != 'minor':
            duration += randrange(-1, 1)
        if duration == 0:
            duration = 1

        if mortality != 0:
            if game.warren.game_mode == "cruel season":
                mortality = int(mortality * 0.5)

                if mortality == 0:
                    mortality = 1
        if lethal is False:
            mortality = 0

        new_injury = Injury(
            name=name,
            severity=injury_severity,
            duration=injury["duration"],
            medicine_duration=duration,
            mortality=mortality,
            risks=injury["risks"],
            illness_infectiousness=injury["illness_infectiousness"],
            also_got=injury["also_got"],
            cause_permanent=injury["cause_permanent"],
            event_triggered=event_triggered
        )

        if new_injury.name not in self.injuries:
            self.injuries[new_injury.name] = {
                "severity": new_injury.severity,
                "mortality": new_injury.current_mortality,
                "duration": new_injury.duration,
                "month_start": game.warren.age if game.warren else 0,
                "illness_infectiousness": new_injury.illness_infectiousness,
                "risks": new_injury.risks,
                "complirabbition": None,
                "cause_permanent": new_injury.cause_permanent,
                "event_triggered": new_injury.new
            }

        if len(new_injury.also_got) > 0 and not int(random() * 5):
            avoided = False
            if 'blood loss' in new_injury.also_got and len(get_med_rabbits(Rabbit)) != 0:
                warren_herbs = set()
                needed_herbs = {"horsetail", "raspberry", "marigold", "cobwebs"}
                warren_herbs.update(game.warren.herbs.keys())
                herb_set = needed_herbs.intersection(warren_herbs)
                usable_herbs = []
                usable_herbs.extend(herb_set)

                if usable_herbs:
                    # deplete the herb
                    herb_used = choice(usable_herbs)
                    game.warren.herbs[herb_used] -= 1
                    if game.warren.herbs[herb_used] <= 0:
                        game.warren.herbs.pop(herb_used)
                    avoided = True
                    text = f"{herb_used.capitalize()} was used to stop blood loss for {self.name}."
                    game.herb_events_list.append(text)

            if not avoided:
                self.also_got = True
                additional_injury = choice(new_injury.also_got)
                if additional_injury in INJURIES:
                    self.additional_injury(additional_injury)
                else:
                    self.get_ill(additional_injury, event_triggered=True)
        else:
            self.also_got = False

    def additional_injury(self, injury):
        self.get_injured(injury, event_triggered=True)

    def congenital_condition(self, rabbit):
        possible_conditions = []

        for condition in PERMANENT:
            possible = PERMANENT[condition]
            if possible["congenital"] in ['always', 'sometimes']:
                possible_conditions.append(condition)

        new_condition = choice(possible_conditions)

        if new_condition == "born without a leg":
            rabbit.pelt.scars.append('NOPAW')
        elif new_condition == "born without a tail":
            rabbit.pelt.scars.append('NOTAIL')

        self.get_permanent_condition(new_condition, born_with=True)

    def get_permanent_condition(self, name, born_with=False, event_triggered=False):
        if name not in PERMANENT:
            print(str(self.name), f"WARNING: {name} is not in the permanent conditions collection.")
            return

        # remove accessories if need be
        if 'NOTAIL' in self.pelt.scars and self.pelt.accessory in ['RED FEATHERS', 'BLUE FEATHERS', 'JAY FEATHERS']:
            self.pelt.accessory = None
        if 'HALFTAIL' in self.pelt.scars and self.pelt.accessory in ['RED FEATHERS', 'BLUE FEATHERS', 'JAY FEATHERS']:
            self.pelt.accessory = None

        condition = PERMANENT[name]
        new_condition = False
        mortality = condition["mortality"][self.age]
        if mortality != 0:
            if game.warren.game_mode == "cruel season":
                mortality = int(mortality * 0.65)

        if condition['congenital'] == 'always':
            born_with = True
        months_until = condition["months_until"]
        if born_with and months_until != 0:
            months_until = randint(months_until - 1, months_until + 1)  # creating a range in which a condition can present
            if months_until < 0:
                months_until = 0

        if born_with and self.status not in ['kitten', 'newborn']:
            months_until = -2
        elif born_with is False:
            months_until = 0

        if name == "paralyzed":
            self.pelt.paralyzed = True

        new_perm_condition = PermanentCondition(
            name=name,
            severity=condition["severity"],
            congenital=condition["congenital"],
            months_until=months_until,
            mortality=mortality,
            risks=condition["risks"],
            illness_infectiousness=condition["illness_infectiousness"],
            event_triggered=event_triggered
        )

        if new_perm_condition.name not in self.permanent_condition:
            self.permanent_condition[new_perm_condition.name] = {
                "severity": new_perm_condition.severity,
                "born_with": born_with,
                "months_until": new_perm_condition.months_until,
                "month_start": game.warren.age if game.warren else 0,
                "mortality": new_perm_condition.current_mortality,
                "illness_infectiousness": new_perm_condition.illness_infectiousness,
                "risks": new_perm_condition.risks,
                "complirabbition": None,
                "event_triggered": new_perm_condition.new
            }
            new_condition = True
        return new_condition

    def not_working(self):
        """returns True if the rabbit cannot work, False if the rabbit can work"""
        not_working = False
        for illness in self.illnesses:
            if self.illnesses[illness]['severity'] != 'minor':
                not_working = True
                break
        for injury in self.injuries:
            if self.injuries[injury]['severity'] != 'minor':
                not_working = True
                break
        return not_working

    
    def retire_rabbit(self):
        """This is only for rabbits that retire due to health condition"""
        
        #There are some special tasks we need to do for rusasi
        # Note that although you can unretire rabbits, they will be a full rabbit/med_rabbit/owsla
        if self.months > 6 and self.status in ["rusasi", "healer rusasi", "owsla rusasi"]:
            _ment = Rabbit.fetch_rabbit(self.rusasirah) if self.rusasirah else None
            self.status_change("rabbit") # Temp switch them to rabbit, so the following step will work
            self.rank_change_traits_skill(_ment)
            
        
        self.status_change("elder")
        return

    def is_ill(self):
        is_ill = True
        if len(self.illnesses) <= 0:
            is_ill = False
        return is_ill is not False

    def is_injured(self):
        is_injured = True
        if len(self.injuries) <= 0:
            is_injured = False
        return is_injured is not False

    def is_disabled(self):
        is_disabled = True
        if len(self.permanent_condition) <= 0:
            is_disabled = False
        return is_disabled is not False

    def contact_with_ill_rabbit(self, rabbit: Rabbit):
        """handles if one rabbit had contact with an ill rabbit"""

        infectious_illnesses = []
        if self.is_ill() or rabbit is None or not rabbit.is_ill():
            return
        elif rabbit.is_ill():
            for illness in rabbit.illnesses:
                if rabbit.illnesses[illness]["infectiousness"] != 0:
                    infectious_illnesses.append(illness)
            if len(infectious_illnesses) == 0:
                return

        for illness in infectious_illnesses:
            illness_name = illness
            rate = rabbit.illnesses[illness]["infectiousness"]
            if self.is_injured():
                for y in self.injuries:
                    illness_infect = list(
                        filter(lambda ill: ill["name"] == illness_name, self.injuries[y]["illness_infectiousness"]))
                    if illness_infect is not None and len(illness_infect) > 0:
                        illness_infect = illness_infect[0]
                        rate -= illness_infect["lower_by"]

                    # prevent rate lower 0 and print warning message
                    if rate < 0:
                        print(
                            f"WARNING: injury {self.injuries[y]['name']} has lowered chance of {illness_name} infection to {rate}")
                        rate = 1

            if not random() * rate:
                text = f"{self.name} had contact with {rabbit.name} and now has {illness_name}."
                # game.health_events_list.append(text)
                game.cur_events_list.append(Single_Event(text, "health", [self.ID, rabbit.ID]))
                self.get_ill(illness_name)

    def save_condition(self):
        # save conditions for each rabbit
        warrenname = None
        if game.switches['warren_name'] != '':
            warrenname = game.switches['warren_name']
        elif len(game.switches['warren_name']) > 0:
            warrenname = game.switches['warren_list'][0]
        elif game.warren is not None:
            warrenname = game.warren.name

        condition_directory = get_save_dir() + '/' + warrenname + '/conditions'
        condition_file_path = condition_directory + '/' + self.ID + '_conditions.json'

        if (not self.is_ill() and not self.is_injured() and not self.is_disabled()) or self.dead or self.outside:
            if os.path.exists(condition_file_path):
                os.remove(condition_file_path)
            return

        conditions = {}

        if self.is_ill():
            conditions["illnesses"] = self.illnesses

        if self.is_injured():
            conditions["injuries"] = self.injuries

        if self.is_disabled():
            conditions["permanent conditions"] = self.permanent_condition

        game.safe_save(condition_file_path, conditions)

    def load_conditions(self):
        if game.switches['warren_name'] != '':
            warrenname = game.switches['warren_name']
        else:
            warrenname = game.switches['warren_list'][0]

        condition_directory = get_save_dir() + '/' + warrenname + '/conditions/'
        condition_rabbit_directory = condition_directory + self.ID + '_conditions.json'
        if not os.path.exists(condition_rabbit_directory):
            return

        try:
            with open(condition_rabbit_directory, 'r') as read_file:
                rel_data = ujson.loads(read_file.read())
                self.illnesses = rel_data.get("illnesses", {})
                self.injuries = rel_data.get("injuries", {})
                self.permanent_condition = rel_data.get("permanent conditions", {})

            if "paralyzed" in self.permanent_condition and not self.pelt.paralyzed:
                self.pelt.paralyzed = True

        except Exception as e:
            print(f"WARNING: There was an error reading the condition file of rabbit #{self}.\n", e)

    # ---------------------------------------------------------------------------- #
    #                                    rusasirah                                    #
    # ---------------------------------------------------------------------------- #

    def is_valid_rusasirah(self, potential_rusasirah: Rabbit):
        # Dead or outside rabbits can't be rusasirahs
        if potential_rusasirah.dead or potential_rusasirah.outside:
            return False
        # Match jobs
        if self.status == 'healer rusasi' and potential_rusasirah.status != 'healer':
            return False
        if self.status == 'rusasi' and potential_rusasirah.status not in [
            'chief rabbit', 'captain', 'rabbit'
        ]:
            return False
        if self.status == 'owsla rusasi' and potential_rusasirah.status != 'owsla':
            return False

        # If not an app, don't need a rusasirah
        if 'rusasi' not in self.status:
            return False
        # Dead rabbits don't need rusasirahs
        if self.dead or self.outside or self.exiled:
            return False
        return True

    def __remove_rusasirah(self):
        """Should only be called by update_rusasirah, also sets fields on rusasirah."""
        if not self.rusasirah:
            return
        rusasirah_rabbit = Rabbit.fetch_rabbit(self.rusasirah)
        if not rusasirah_rabbit:
            return
        if self.ID in rusasirah_rabbit.rusasi:
            rusasirah_rabbit.rusasi.remove(self.ID)
        if self.months > 6 and self.ID not in rusasirah_rabbit.former_rusasis:
            rusasirah_rabbit.former_rusasis.append(self.ID)
        if self.months > 6 and rusasirah_rabbit.ID not in self.former_rusasirah:
            self.former_rusasirah.append(rusasirah_rabbit.ID)
        self.rusasirah = None

    def __add_rusasirah(self, new_rusasirah_id: str):
        """Should only be called by update_rusasirah, also sets fields on rusasirah."""
        # reset patrol number
        self.patrol_with_rusasirah = 0
        self.rusasirah = new_rusasirah_id
        rusasirah_rabbit = Rabbit.fetch_rabbit(self.rusasirah)
        if not rusasirah_rabbit:
            return
        if self.ID not in rusasirah_rabbit.rusasi:
            rusasirah_rabbit.rusasi.append(self.ID)

    def update_rusasirah(self, new_rusasirah: Any = None):
        """Takes rusasirah's ID as argument, rusasirah could just be set via this function."""
        # No !!
        if isinstance(new_rusasirah, Rabbit):
            print("Everything is terrible!! (new_rusasirah {new_rusasirah} is a Rabbit D:)")
            return
        # Check if rabbit can have a rusasirah
        illegible_for_rusasirah = self.dead or self.outside or self.exiled or self.status not in ["rusasi",
                                                                                               "owsla rusasi",
                                                                                               "healer rusasi"]
        if illegible_for_rusasirah:
            self.__remove_rusasirah()
            return
        # If eligible, rabbit should get a rusasirah.
        if new_rusasirah:
            self.__remove_rusasirah()
            self.__add_rusasirah(new_rusasirah)

        # Check if current rusasirah is valid
        if self.rusasirah:
            rusasirah_rabbit = Rabbit.fetch_rabbit(self.rusasirah)  # This will return None if there is no current rusasirah
            if rusasirah_rabbit and not self.is_valid_rusasirah(rusasirah_rabbit):
                self.__remove_rusasirah()

        # Need to pick a random rusasirah if not specified
        if not self.rusasirah:
            potential_rusasirahs = []
            priority_rusasirahs = []
            for rabbit in self.all_rabbits.values():
                if self.is_valid_rusasirah(rabbit):
                    potential_rusasirahs.append(rabbit)
                    if not rabbit.rusasi and not rabbit.not_working(): 
                        priority_rusasirahs.append(rabbit)
            # First try for a rabbit who currently has no rusasis and is working
            if priority_rusasirahs:  # length of list > 0
                new_rusasirah = choice(priority_rusasirahs)
            elif potential_rusasirahs:  # length of list > 0
                new_rusasirah = choice(potential_rusasirahs)
            if new_rusasirah:
                self.__add_rusasirah(new_rusasirah.ID)

    # ---------------------------------------------------------------------------- #
    #                                 relationships                                #
    # ---------------------------------------------------------------------------- #
    def is_potential_mate(self,
                          other_rabbit: Rabbit,
                          for_love_interest: bool = False,
                          age_restriction: bool = True,
                          first_cousin_mates:bool = False,
                          ignore_no_mates:bool=False):
        """
            Checks if this rabbit is potential mate for the other rabbit.
            There are no restrictions if the current rabbit already has a mate or not (this allows poly-mates).
        """
        
        try:
            first_cousin_mates = game.warren.warren_settings["first cousin mates"]
        except:
            if 'unittest' not in sys.modules:
                raise
                
        
        # just to be sure, check if it is not the same rabbit
        if self.ID == other_rabbit.ID:
            return False
        
        #No Mates Check
        if not ignore_no_mates and (self.no_mates or other_rabbit.no_mates):
            return False

        # Inheritance check
        if self.is_related(other_rabbit, first_cousin_mates):
            return False

        # check exiled, outside, and dead rabbits
        if (self.dead != other_rabbit.dead) or self.outside or other_rabbit.outside:
            return False

        # check for age
        if age_restriction:
            if (self.months < 14 or other_rabbit.months < 14) and not for_love_interest:
                return False

            # the +1 is necessary because both might not already aged up
            # if only one is aged up at this point, later they are more months apart than the setting defined
            # game_config boolian "override_same_age_group" disables the same-age group check.
            if game.config["mates"].get("override_same_age_group", False) or self.age != other_rabbit.age:
                if abs(self.months - other_rabbit.months)> game.config["mates"]["age_range"] + 1:
                    return False

        age_restricted_ages = ["newborn", "kitten", "adolescent"]
        if self.age in age_restricted_ages or other_rabbit.age in age_restricted_ages:
            if self.age != other_rabbit.age:
                return False

        # check for rusasirah
        
        # Current rusasirah
        if other_rabbit.ID in self.rusasi or self.ID in other_rabbit.rusasi:
            return False
        
        #Former rusasirah
        is_former_rusasirah = (other_rabbit.ID in self.former_rusasis or self.ID in other_rabbit.former_rusasi)
        if is_former_rusasirah and not game.warren.warren_settings['romantic with former rusasirah']:
            return False

        return True

    def unset_mate(self, other_rabbit: Rabbit, breakup: bool = False, fight: bool = False):
        """Unset the mate from both self and other_rabbit"""
        if not other_rabbit:
            return

        # Both rabbits must have mates for this to work
        if len(self.mate) < 1 or len(other_rabbit.mate) < 1:
            return

        # AND they must be mates with each other. 
        if self.ID not in other_rabbit.mate or other_rabbit.ID not in self.mate:
            print(f"Unsetting mates: These {self.name} and {other_rabbit.name} are not mates!")
            return

        # If only deal with relationships if this is a breakup. 
        if breakup:
            if not self.dead:
                if other_rabbit.ID not in self.relationships:
                    self.create_one_relationship(other_rabbit)
                    self.relationships[other_rabbit.ID].mate = True
                self_relationship = self.relationships[other_rabbit.ID]
                self_relationship.romantic_love -= 40
                self_relationship.comfortable -= 20
                self_relationship.trust -= 10
                self_relationship.mate = False
                if fight:
                    self_relationship.romantic_love -= 20
                    self_relationship.platonic_like -= 30

            if not other_rabbit.dead:
                if self.ID not in other_rabbit.relationships:
                    other_rabbit.create_one_relationship(self)
                    other_rabbit.relationships[self.ID].mate = True
                other_relationship = other_rabbit.relationships[self.ID]
                other_relationship.romantic_love -= 40
                other_relationship.comfortable -= 20
                other_relationship.trust -= 10
                other_relationship.mate = False
                if fight:
                    self_relationship.romantic_love -= 20
                    other_relationship.platonic_like -= 30

        self.mate.remove(other_rabbit.ID)
        other_rabbit.mate.remove(self.ID)

        # Handle previous mates:
        if other_rabbit.ID not in self.previous_mates:
            self.previous_mates.append(other_rabbit.ID)
        if self.ID not in other_rabbit.previous_mates:
            other_rabbit.previous_mates.append(self.ID)

        if other_rabbit.inheritance:
            other_rabbit.inheritance.update_all_mates()
        if self.inheritance:
            self.inheritance.update_all_mates()

    def set_mate(self, other_rabbit: Rabbit):
        """Sets up a mate relationship between self and other_rabbit."""
        if other_rabbit.ID not in self.mate:
            self.mate.append(other_rabbit.ID)
        if self.ID not in other_rabbit.mate:
            other_rabbit.mate.append(self.ID)

        # If the current mate was in the previous mate list, remove them. 
        if other_rabbit.ID in self.previous_mates:
            self.previous_mates.remove(other_rabbit.ID)
        if self.ID in other_rabbit.previous_mates:
            other_rabbit.previous_mates.remove(self.ID)

        if other_rabbit.inheritance:
            other_rabbit.inheritance.update_all_mates()
        if self.inheritance:
            self.inheritance.update_all_mates()

        # Set starting relationship values
        if not self.dead:
            if other_rabbit.ID not in self.relationships:
                self.create_one_relationship(other_rabbit)
                self.relationships[other_rabbit.ID].mate =  True
            self_relationship = self.relationships[other_rabbit.ID]
            self_relationship.romantic_love += 20
            self_relationship.comfortable += 20
            self_relationship.trust += 10
            self_relationship.mate = True

        if not other_rabbit.dead:
            if self.ID not in other_rabbit.relationships:
                other_rabbit.create_one_relationship(self)
                other_rabbit.relationships[self.ID].mate = True
            other_relationship = other_rabbit.relationships[self.ID]
            other_relationship.romantic_love += 20
            other_relationship.comfortable += 20
            other_relationship.trust += 10
            other_relationship.mate = True

    def create_inheritance_new_rabbit(self):
        """Creates the inheritance class for a new rabbit."""
        # set the born status to true, just for safety
        self.inheritance = Inheritance(self, True)

    def create_one_relationship(self, other_rabbit: Rabbit):
        """Create a new relationship between current rabbit and other rabbit. Returns: Relationship"""
        if other_rabbit.ID in self.relationships:
            return self.relationships[other_rabbit.ID]
        
        if other_rabbit.ID == self.ID:
            print(f"Attempted to create a relationship with self: {self.name}. Please report as a bug!")
            return None
        
        self.relationships[other_rabbit.ID] = Relationship(self, other_rabbit)
        return self.relationships[other_rabbit.ID]

    def create_relationships_new_rabbit(self):
        """Create relationships for a new generated rabbit."""
        for inter_rabbit in Rabbit.all_rabbits.values():
            # the inter_rabbit is the same as the current rabbit
            if inter_rabbit.ID == self.ID:
                continue
            # if the rabbit already has (somehow) a relationship with the inter rabbit
            if inter_rabbit.ID in self.relationships:
                continue
            # if they dead (dead rabbits have no relationships)
            if self.dead or inter_rabbit.dead:
                continue
            # if they are not outside of the Warren at the same time
            if self.outside and not inter_rabbit.outside or not self.outside and inter_rabbit.outside:
                continue
            inter_rabbit.relationships[self.ID] = Relationship(inter_rabbit, self)
            self.relationships[inter_rabbit.ID] = Relationship(self, inter_rabbit)

    def init_all_relationships(self):
        """Create Relationships to all current Warrenrabbits."""
        for id in self.all_rabbits:
            the_rabbit = self.all_rabbits.get(id)
            if the_rabbit.ID is not self.ID:
                mates = the_rabbit.ID in self.mate
                are_parents = False
                parents = False
                siblings = False

                if self.parent1 is not None and self.parent2 is not None and \
                        the_rabbit.parent1 is not None and the_rabbit.parent2 is not None:
                    are_parents = the_rabbit.ID in [self.parent1, self.parent2]
                    parents = are_parents or self.ID in [
                        the_rabbit.parent1, the_rabbit.parent2
                    ]
                    siblings = self.parent1 in [
                        the_rabbit.parent1, the_rabbit.parent2
                    ] or self.parent2 in [the_rabbit.parent1, the_rabbit.parent2]

                related = parents or siblings

                # set the different stats
                romantic_love = 0
                like = 0
                dislike = 0
                admiration = 0
                comfortable = 0
                jealousy = 0
                trust = 0
                if game.settings['random relation']:
                    if game.warren:
                        if the_rabbit == game.warren.instructor:
                            pass
                        elif randint(1, 20) == 1 and romantic_love < 1:
                            dislike = randint(10, 25)
                            jealousy = randint(5, 15)
                            if randint(1, 30) == 1:
                                trust = randint(1, 10)
                        else:
                            like = randint(0, 35)
                            comfortable = randint(0, 25)
                            trust = randint(0, 15)
                            admiration = randint(0, 20)
                            if randint(
                                    1, 100 - like
                            ) == 1 and self.months > 11 and the_rabbit.months > 11:
                                romantic_love = randint(15, 30)
                                comfortable = int(comfortable * 1.3)
                                trust = int(trust * 1.2)
                    else:
                        if randint(1, 20) == 1 and romantic_love < 1:
                            dislike = randint(10, 25)
                            jealousy = randint(5, 15)
                            if randint(1, 30) == 1:
                                trust = randint(1, 10)
                        else:
                            like = randint(0, 35)
                            comfortable = randint(0, 25)
                            trust = randint(0, 15)
                            admiration = randint(0, 20)
                            if randint(
                                    1, 100 - like
                            ) == 1 and self.months > 11 and the_rabbit.months > 11:
                                romantic_love = randint(15, 30)
                                comfortable = int(comfortable * 1.3)
                                trust = int(trust * 1.2)

                if are_parents and like < 60:
                    like = 60
                if siblings and like < 30:
                    like = 30

                rel = Relationship(rabbit_from=self,
                                   rabbit_to=the_rabbit,
                                   mates=mates,
                                   family=related,
                                   romantic_love=romantic_love,
                                   platonic_like=like,
                                   dislike=dislike,
                                   admiration=admiration,
                                   comfortable=comfortable,
                                   jealousy=jealousy,
                                   trust=trust)
                self.relationships[the_rabbit.ID] = rel

    def save_relationship_of_rabbit(self, relationship_dir):
        # save relationships for each rabbit

        rel = []
        for r in self.relationships.values():
            r_data = {
                "rabbit_from_id": r.rabbit_from.ID,
                "rabbit_to_id": r.rabbit_to.ID,
                "mates": r.mates,
                "family": r.family,
                "romantic_love": r.romantic_love,
                "platonic_like": r.platonic_like,
                "dislike": r.dislike,
                "admiration": r.admiration,
                "comfortable": r.comfortable,
                "jealousy": r.jealousy,
                "trust": r.trust,
                "log": r.log
            }
            rel.append(r_data)

        game.safe_save(f"{relationship_dir}/{self.ID}_relations.json", rel)

    def load_relationship_of_rabbit(self):
        if game.switches['warren_name'] != '':
            warrenname = game.switches['warren_name']
        else:
            warrenname = game.switches['warren_list'][0]

        relation_directory = get_save_dir() + '/' + warrenname + '/relationships/'
        relation_rabbit_directory = relation_directory + self.ID + '_relations.json'

        self.relationships = {}
        if os.path.exists(relation_directory):
            if not os.path.exists(relation_rabbit_directory):
                self.init_all_relationships()
                for rabbit in Rabbit.all_rabbits.values():
                    rabbit.create_one_relationship(self)
                return
            try:
                with open(relation_rabbit_directory, 'r') as read_file:
                    rel_data = ujson.loads(read_file.read())
                    for rel in rel_data:
                        rabbit_to = self.all_rabbits.get(rel['rabbit_to_id'])
                        if rabbit_to is None or rel['rabbit_to_id'] == self.ID:
                            continue
                        new_rel = Relationship(
                            rabbit_from=self,
                            rabbit_to=rabbit_to,
                            mates=rel['mates'] if rel['mates'] else False,
                            family=rel['family'] if rel['family'] else False,
                            romantic_love=rel['romantic_love'] if rel['romantic_love'] else 0,
                            platonic_like=rel['platonic_like'] if rel['platonic_like'] else 0,
                            dislike=rel['dislike'] if rel['dislike'] else 0,
                            admiration=rel['admiration'] if rel['admiration'] else 0,
                            comfortable=rel['comfortable'] if rel['comfortable'] else 0,
                            jealousy=rel['jealousy'] if rel['jealousy'] else 0,
                            trust=rel['trust'] if rel['trust'] else 0,
                            log=rel['log'])
                        self.relationships[rel['rabbit_to_id']] = new_rel
            except:
                print(f'WARNING: There was an error reading the relationship file of rabbit #{self}.')

    @staticmethod
    def mediate_relationship(chief, rabbit1, rabbit2, allow_romantic, sabotage=False):
        # Gather some important info

        # Gathering the relationships.
        if rabbit1.ID in rabbit2.relationships:
            rel1 = rabbit1.relationships[rabbit2.ID]
        else:
            rel1 = rabbit1.create_one_relationship(rabbit2)

        if rabbit2.ID in rabbit1.relationships:
            rel2 = rabbit2.relationships[rabbit1.ID]
        else:
            rel2 = rabbit2.create_one_relationship(rabbit1)

        # Output string.
        output = ""

        # Determine the chance of failure.
        if chief.experience_level == "untrained":
            chance = 15
        if chief.experience_level == "trainee":
            # Negative bonus for very low.
            chance = 20
        elif chief.experience_level == "prepared":
            chance = 35
        elif chief.experience_level == "proficient":
            chance = 55
        elif chief.experience_level == "expert":
            chance = 70
        elif chief.experience_level == "master":
            chance = 100
        else:
            chance = 40

        compat = get_personality_compatibility(rabbit1, rabbit2)
        if compat is True:
            chance += 10
        elif compat is False:
            chance -= 5

        # Rabbit's compatibility with owsla also has an effect on success chance.
        for rabbit in [rabbit1, rabbit2]:
            if get_personality_compatibility(rabbit, chief) is True:
                chance += 5
            elif get_personality_compatibility(rabbit, chief) is False:
                chance -= 5

        # Determine chance to fail, turning sabotage into mediate and mediate into sabotage
        if not int(random() * chance):
            apply_bonus = False
            if sabotage:
                output += "Sabotage Failed!\n"
                sabotage = False
            else:
                output += "Mediate Failed!\n"
                sabotage = True
        else:
            apply_bonus = True
            # EX gain on success
            EX_gain = randint(10, 24)

            gm_modifier = 1
            if game.warren.game_mode == 'expanded':
                    gm_modifier = 3
            elif game.warren.game_mode == 'cruel season':
                gm_modifier = 6

            if chief.experience_level == "average":
                    lvl_modifier = 1.25
            elif chief.experience_level == "high":
                    lvl_modifier = 1.75
            elif chief.experience_level == "master":
                    lvl_modifier = 2
            else:
                    lvl_modifier = 1
            chief.experience += EX_gain / lvl_modifier / gm_modifier

        # determine the traits to effect
        # Are they mates?
        if rel1.rabbit_from.ID in rel1.rabbit_to.mate:
            mates = True
        else:
            mates = False
        
        pos_traits = ["platonic", "respect", "comfortable", "trust"]
        if allow_romantic and (mates or rabbit1.is_potential_mate(rabbit2)):
            pos_traits.append("romantic")

        neg_traits = ["dislike", "jealousy"]

        # Determine the number of positive traits to effect, and choose the traits
        chosen_pos = sample(pos_traits, k=randint(2, len(pos_traits)))

        # Determine negative trains effected
        neg_traits = sample(neg_traits, k=randint(1, 2))

        if compat is True:
            personality_bonus = 2
        elif compat is False:
            personality_bonus = -2
        else:
            personality_bonus = 0

        # Effects on traits
        for trait in chosen_pos + neg_traits:

            # The EX bonus in not applied upon a fail.
            if apply_bonus:
                if chief.experience_level == "very low":
                    # Negative bonus for very low.
                    bonus = randint(-2, -1)
                elif chief.experience_level == "low":
                    bonus = randint(-2, 0)
                elif chief.experience_level == "high":
                    bonus = randint(1, 3)
                elif chief.experience_level == "master":
                    bonus = randint(3, 4)
                elif chief.experience_level == "max":
                    bonus = randint(4, 5)
                else:
                    bonus = 0  # Average gets no bonus.
            else:
                bonus = 0

            if trait == "romantic":
                if mates:
                    ran = (5, 10)
                else:
                    ran = (4, 6)

                if sabotage:
                    rel1.romantic_love = Rabbit.effect_relation(rel1.romantic_love, -(randint(ran[0], ran[1]) + bonus) +
                                                             personality_bonus)
                    rel2.romantic_love = Rabbit.effect_relation(rel1.romantic_love, -(randint(ran[0], ran[1]) + bonus) +
                                                             personality_bonus)
                    output += "Romantic interest decreased. "
                else:
                    rel1.romantic_love = Rabbit.effect_relation(rel1.romantic_love, (randint(ran[0], ran[1]) + bonus) +
                                                             personality_bonus)
                    rel2.romantic_love = Rabbit.effect_relation(rel2.romantic_love, (randint(ran[0], ran[1]) + bonus) +
                                                             personality_bonus)
                    output += "Romantic interest increased. "

            elif trait == "platonic":
                ran = (4, 6)

                if sabotage:
                    rel1.platonic_like = Rabbit.effect_relation(rel1.platonic_like, -(randint(ran[0], ran[1]) + bonus) +
                                                             personality_bonus)
                    rel2.platonic_like = Rabbit.effect_relation(rel2.platonic_like, -(randint(ran[0], ran[1]) + bonus) +
                                                             personality_bonus)
                    output += "Platonic like decreased. "
                else:
                    rel1.platonic_like = Rabbit.effect_relation(rel1.platonic_like, (randint(ran[0], ran[1]) + bonus) +
                                                             personality_bonus)
                    rel2.platonic_like = Rabbit.effect_relation(rel2.platonic_like, (randint(ran[0], ran[1]) + bonus) +
                                                             personality_bonus)
                    output += "Platonic like increased. "

            elif trait == "respect":
                ran = (4, 6)

                if sabotage:
                    rel1.admiration = Rabbit.effect_relation(rel1.admiration, -(randint(ran[0], ran[1]) + bonus) +
                                                          personality_bonus)
                    rel2.admiration = Rabbit.effect_relation(rel2.admiration, -(randint(ran[0], ran[1]) + bonus) +
                                                          personality_bonus)
                    output += "Respect decreased. "
                else:
                    rel1.admiration = Rabbit.effect_relation(rel1.admiration, (randint(ran[0], ran[1]) + bonus) +
                                                          personality_bonus)
                    rel2.admiration = Rabbit.effect_relation(rel2.admiration, (randint(ran[0], ran[1]) + bonus) +
                                                          personality_bonus)
                    output += "Respect increased. "

            elif trait == "comfortable":
                ran = (4, 6)

                if sabotage:
                    rel1.comfortable = Rabbit.effect_relation(rel1.comfortable, -(randint(ran[0], ran[1]) + bonus) +
                                                           personality_bonus)
                    rel2.comfortable = Rabbit.effect_relation(rel2.comfortable, -(randint(ran[0], ran[1]) + bonus) +
                                                           personality_bonus)
                    output += "Comfort decreased. "
                else:
                    rel1.comfortable = Rabbit.effect_relation(rel1.comfortable, (randint(ran[0], ran[1]) + bonus) +
                                                           personality_bonus)
                    rel2.comfortable = Rabbit.effect_relation(rel2.comfortable, (randint(ran[0], ran[1]) + bonus) +
                                                           personality_bonus)
                    output += "Comfort increased. "

            elif trait == "trust":
                ran = (4, 6)

                if sabotage:
                    rel1.trust = Rabbit.effect_relation(rel1.trust, -(randint(ran[0], ran[1]) + bonus) +
                                                     personality_bonus)
                    rel2.trust = Rabbit.effect_relation(rel2.trust, -(randint(ran[0], ran[1]) + bonus) +
                                                     personality_bonus)
                    output += "Trust decreased. "
                else:
                    rel1.trust = Rabbit.effect_relation(rel1.trust, (randint(ran[0], ran[1]) + bonus) +
                                                     personality_bonus)
                    rel2.trust = Rabbit.effect_relation(rel2.trust, (randint(ran[0], ran[1]) + bonus) +
                                                     personality_bonus)
                    output += "Trust increased. "

            elif trait == "dislike":
                ran = (4, 9)
                if sabotage:
                    rel1.dislike = Rabbit.effect_relation(rel1.dislike, (randint(ran[0], ran[1]) + bonus) -
                                                       personality_bonus)
                    rel2.dislike = Rabbit.effect_relation(rel2.dislike, (randint(ran[0], ran[1]) + bonus) -
                                                       personality_bonus)
                    output += "Dislike increased. "
                else:
                    rel1.dislike = Rabbit.effect_relation(rel1.dislike, -(randint(ran[0], ran[1]) + bonus) -
                                                       personality_bonus)
                    rel2.dislike = Rabbit.effect_relation(rel2.dislike, -(randint(ran[0], ran[1]) + bonus) -
                                                       personality_bonus)
                    output += "Dislike decreased. "

            elif trait == "jealousy":
                ran = (4, 6)

                if sabotage:
                    rel1.jealousy = Rabbit.effect_relation(rel1.jealousy, (randint(ran[0], ran[1]) + bonus) -
                                                        personality_bonus)
                    rel2.jealousy = Rabbit.effect_relation(rel2.jealousy, (randint(ran[0], ran[1]) + bonus) -
                                                        personality_bonus)
                    output += "Jealousy increased. "
                else:
                    rel1.jealousy = Rabbit.effect_relation(rel1.jealousy, -(randint(ran[0], ran[1]) + bonus) -
                                                        personality_bonus)
                    rel2.jealousy = Rabbit.effect_relation(rel2.jealousy, -(randint(ran[0], ran[1]) + bonus) -
                                                        personality_bonus)
                    output += "Jealousy decreased . "

        return output

    @staticmethod
    def effect_relation(current_value, effect):
        if effect < 0:
            if abs(effect) >= current_value:
                return 0

        if effect > 0:
            if current_value + effect >= 100:
                return 100

        return current_value + effect

    def set_faded(self):
        """This function is for rabbits that are faded. It will set the sprite and the faded tag"""
        self.faded = True

        # Silhouette sprite
        if self.age == 'newborn':
            file_name = "faded_newborn"
        elif self.age == 'kitten':
            file_name = "faded_kitten"
        elif self.age in ['adult', 'young adult', 'senior adult']:
            file_name = "faded_adult"
        elif self.age == "adolescent":
            file_name = "faded_adol"
        else:
            file_name = "faded_senior"

        if self.df:
            file_name += "_df"

        file_name += ".png"

        self.sprite = image_cache.load_image(f"sprites/faded/{file_name}").convert_alpha()

    @staticmethod
    def fetch_rabbit(rabbit_id: str):
        """Fetches a rabbit object. Works for both faded and non-faded rabbits. Returns none if no rabbit was found. """
        if not rabbit_id or isinstance(rabbit_id, Rabbit):  # Check if argument is None or Rabbit.
            return rabbit_id
        elif not isinstance(rabbit_id, str):  # Invalid type
            return None
        if rabbit_id in Rabbit.all_rabbits:
            return Rabbit.all_rabbits[rabbit_id]
        else:
            ob = Rabbit.load_faded_rabbit(rabbit_id)
            if ob:
                return ob
            else:
                return None

    @staticmethod
    def load_faded_rabbit(rabbit: str):
        """Loads a faded rabbit, returning the rabbit object. This object is saved nowhere else. """
        try:
            with open(get_save_dir() + '/' + game.warren.name + '/faded_rabbits/' + rabbit + ".json", 'r') as read_file:
                rabbit_info = ujson.loads(read_file.read())
        except AttributeError:  # If loading rabbits is attempted before the Warren is loaded, we would need to use this.
            with open(get_save_dir() + '/' + game.switches['warren_list'][0] + '/faded_rabbits/' + rabbit + ".json",
                      'r') as read_file:
                rabbit_info = ujson.loads(read_file.read())
        except:
            print("ERROR: in loading faded rabbit")
            return False

        rabbit_ob = Rabbit(ID=rabbit_info["ID"], prefix=rabbit_info["name_prefix"],
                     status=rabbit_info["status"], months=rabbit_info["months"], faded=True,
                     df=rabbit_info["df"] if "df" in rabbit_info else False)
        if rabbit_info["parent1"]:
            rabbit_ob.parent1 = rabbit_info["parent1"]
        if rabbit_info["parent2"]:
            rabbit_ob.parent2 = rabbit_info["parent2"]
        rabbit_ob.faded_offspring = rabbit_info["faded_offspring"]
        rabbit_ob.adoptive_parents = rabbit_info["adoptive_parents"] if "adoptive_parents" in rabbit_info else []
        rabbit_ob.faded = True
        rabbit_ob.dead_for = rabbit_info["dead_for"] if "dead_for" in rabbit_info else 1

        return rabbit_ob

    # ---------------------------------------------------------------------------- #
    #                                  Sorting                                     #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def sort_rabbits(given_list=[]):
        if not given_list:
            given_list = Rabbit.all_rabbits_list
        if game.sort_type == "age":
            given_list.sort(key=lambda x: Rabbit.get_adjusted_age(x))
        elif game.sort_type == "reverse_age":
            given_list.sort(key=lambda x: Rabbit.get_adjusted_age(x), reverse=True)
        elif game.sort_type == "id":
            given_list.sort(key=lambda x: int(x.ID))
        elif game.sort_type == "reverse_id":
            given_list.sort(key=lambda x: int(x.ID), reverse=True)
        elif game.sort_type == "rank":
            given_list.sort(key=lambda x: (Rabbit.rank_order(x), Rabbit.get_adjusted_age(x)), reverse=True)
        elif game.sort_type == "exp":
            given_list.sort(key=lambda x: x.experience, reverse=True)
        elif game.sort_type == "death":
            given_list.sort(key=lambda x: -1 * int(x.dead_for))

        return


    @staticmethod
    def insert_rabbit(c: Rabbit):
        try:
            if game.sort_type == "age":
                bisect.insort(Rabbit.all_rabbits_list, c, key=lambda x: Rabbit.get_adjusted_age(x))
            elif game.sort_type == "reverse_age":
                bisect.insort(Rabbit.all_rabbits_list, c, key=lambda x: -1 * Rabbit.get_adjusted_age(x))
            elif game.sort_type == "rank":
                bisect.insort(Rabbit.all_rabbits_list, c, key=lambda x: (-1 * Rabbit.rank_order(x), -1 *
                                                                   Rabbit.get_adjusted_age(x)))
            elif game.sort_type == "exp":
                bisect.insort(Rabbit.all_rabbits_list, c, key=lambda x: x.experience)
            elif game.sort_type == "id":
                bisect.insort(Rabbit.all_rabbits_list, c, key=lambda x: int(x.ID))
            elif game.sort_type == "reverse_id":
                bisect.insort(Rabbit.all_rabbits_list, c, key=lambda x: -1 * int(x.ID))
            elif game.sort_type == "death":
                bisect.insort(Rabbit.all_rabbits_list, c, key=lambda x: -1 * int(x.dead_for))
        except (TypeError, NameError):
            # If you are using python 3.8, key is not a supported parameter into insort. Therefore, we'll need to
            # do the slower option of adding the rabbit, then resorting
            Rabbit.all_rabbits_list.append(c)
            Rabbit.sort_rabbits()

    @staticmethod
    def rank_order(rabbit: Rabbit):
        if rabbit.status in Rabbit.rank_sort_order:
            return Rabbit.rank_sort_order.index(rabbit.status)
        else:
            return 0

    @staticmethod
    def get_adjusted_age(rabbit: Rabbit):
        """Returns the months + dead_for months rather than the months at death for dead rabbits, so dead rabbits are sorted by
        total age, rather than age at death"""
        if rabbit.dead:
            if game.config["sorting"]["sort_rank_by_death"]:
                if game.sort_type == "rank":
                    return rabbit.dead_for
                else:
                    if game.config["sorting"]["sort_dead_by_total_age"]:
                        return rabbit.dead_for + rabbit.months
                    else:
                        return rabbit.months
            else:
                if game.config["sorting"]["sort_dead_by_total_age"]:
                    return rabbit.dead_for + rabbit.months
                else:
                    return rabbit.months
        else:
            return rabbit.months
        
    # ---------------------------------------------------------------------------- #
    #                                  properties                                  #
    # ---------------------------------------------------------------------------- #

    @property
    def experience(self):
        return self._experience

    @experience.setter
    def experience(self, exp: int):
        if exp > self.experience_levels_range["master"][1]:
            exp = self.experience_levels_range["master"][1]
        self._experience = int(exp)

        for x in self.experience_levels_range:
            if self.experience_levels_range[x][0] <= exp <= self.experience_levels_range[x][1]:
                self.experience_level = x
                break

    @property
    def months(self):
        return self._months

    @months.setter
    def months(self, value: int):
        self._months = value
        
        updated_age = False
        for key_age in self.age_months.keys():
            if self._months in range(self.age_months[key_age][0], self.age_months[key_age][1] + 1):
                updated_age = True
                self.age = key_age
        try:
            if not updated_age and self.age is not None:
                self.age = "senior"
        except AttributeError:
            print("ERROR: rabbit has no age attribute! Rabbit ID: " + self.ID)
        
    @property
    def sprite(self):
        # Update the sprite
        update_sprite(self)
        return self._sprite

    @sprite.setter
    def sprite(self, new_sprite):
        self._sprite = new_sprite
        
    # ---------------------------------------------------------------------------- #
    #                                  other                                       #
    # ---------------------------------------------------------------------------- #
    
    def is_baby(self):
        return self.age in ["kitten", "newborn"]
    
    def get_save_dict(self, faded=False):
        if faded:
            return {
                "ID": self.ID,
                "name_prefix": self.name.prefix,
                "status": self.status,
                "months": self.months,
                "dead_for": self.dead_for,
                "parent1": self.parent1,
                "parent2": self.parent2,
                "adoptive_parents": self.adoptive_parents,
                "df": self.df,
                "faded_offspring": self.faded_offspring
            }
        else:
            return {
                "ID": self.ID,
                "name_prefix": self.name.prefix,
                "specsuffix_hidden": self.name.specsuffix_hidden,
                "gender": self.gender,
                "gender_align": self.genderalign,
                #"pronouns": self.pronouns,
                "birth_cooldown": self.birth_cooldown,
                "status": self.status,
                "backstory": self.backstory if self.backstory else None,
                "months": self.months,
                "trait": self.personality.trait,
                "facets": self.personality.get_facet_string(),
                "parent1": self.parent1,
                "parent2": self.parent2,
                "adoptive_parents": self.adoptive_parents,
                "rusasirah": self.rusasirah if self.rusasirah else None,
                "former_rusasirah": [rabbit for rabbit in self.former_rusasirah] if self.former_rusasirah else [],
                "patrol_with_rusasirah": self.patrol_with_rusasirah if self.patrol_with_rusasirah else 0,
                "mate": self.mate,
                "previous_mates": self.previous_mates,
                "dead": self.dead,
                "paralyzed": self.pelt.paralyzed,
                "no_kittens": self.no_kittens,
                "no_retire": self.no_retire,
                "no_mates": self.no_mates,
                "exiled": self.exiled,
                "pelt_name": self.pelt.name,
                "pelt_color": self.pelt.colour,
                "pelt_length": self.pelt.length,
                "sprite_kitten": self.pelt.rabbit_sprites['kitten'],
                "sprite_adolescent": self.pelt.rabbit_sprites['adolescent'],
                "sprite_adult": self.pelt.rabbit_sprites['adult'],
                "sprite_senior": self.pelt.rabbit_sprites['senior'],
                "sprite_para_adult": self.pelt.rabbit_sprites['para_adult'],
                "eye_colour": self.pelt.eye_colour,
                "eye_colour2": self.pelt.eye_colour2 if self.pelt.eye_colour2 else None,
                "reverse": self.pelt.reverse,
                "white_patches": self.pelt.white_patches,
                "vitiligo": self.pelt.vitiligo,
                "points": self.pelt.points,
                "white_patches_tint": self.pelt.white_patches_tint,
                "pattern": self.pelt.pattern,
                "tortie_base": self.pelt.tortiebase,
                "tortie_color": self.pelt.tortiecolour,
                "tortie_pattern": self.pelt.tortiepattern,
                "skin": self.pelt.skin,
                "tint": self.pelt.tint,
                "skill_dict": self.skills.get_skill_dict(),
                "scars": self.pelt.scars if self.pelt.scars else [],
                "accessory": self.pelt.accessory,
                "experience": self.experience,
                "dead_months": self.dead_for,
                "current_rusasi": [appr for appr in self.rusasi],
                "former_rusasi": [appr for appr in self.former_rusasis],
                "df": self.df,
                "outside": self.outside,
                "faded_offspring": self.faded_offspring,
                "opacity": self.pelt.opacity,
                "prevent_fading": self.prevent_fading,
                "favourite": self.favourite,
            }


        
# ---------------------------------------------------------------------------- #
#                               END OF RABBIT CLASS                               #
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                               PERSONALITY CLASS                              #
# ---------------------------------------------------------------------------- #

class Personality():
    """Hold personality information for a rabbit, and functions to deal with it """
    facet_types = ["lawfulness", "sociability", "aggression", "stability"]
    facet_range = [0, 16]
    
    with open("resources/dicts/traits/trait_ranges.json", "r") as read_file:
        trait_ranges = ujson.loads(read_file.read())
    
    def __init__(self, trait:str=None, kitten_trait:bool=False, lawful:int=None, social:int=None, aggress:int=None, 
                 stable:int=None) -> Personality:
        """If trait is given, it will randomize facets within the range of the trait. It will ignore any facets given. 
            If facets are given and no trait, it will find a trait that matches the facets. NOTE: you can give
            only some facets: It will randomize any you don't specify.
            If both facets and trait are given, it will use the trait if it matched the facets. Otherwise it will
            find a new trait."""
        self._law = 0
        self._social = 0
        self._aggress = 0
        self._stable = 0
        self.trait = None
        self.kitten = kitten_trait #If true, use kitten trait. If False, use normal traits. 
        
        if self.kitten:
            trait_type_dict = Personality.trait_ranges["kitten_traits"]
        else:
            trait_type_dict = Personality.trait_ranges["normal_traits"]
        
        _tr = None
        if trait and trait in trait_type_dict:
            # Trait-given init
            self.trait = trait
            _tr = trait_type_dict[self.trait]
        
        # Set Facet Values
        # The priority of is: 
        # (1) Given value, from parameter. 
        # (2) If a trait range is assigned, pick from trait range
        # (3) Totally random. 
        if lawful is not None:
            self._law = Personality.adjust_to_range(lawful)
        elif _tr:
            self._law = randint(_tr["lawfulness"][0], _tr["lawfulness"][1])
        else:
            self._law = randint(Personality.facet_range[0], Personality.facet_range[1])
            
        if social is not None:
            self._social = Personality.adjust_to_range(social)
        elif _tr:
            self._social = randint(_tr["sociability"][0], _tr["sociability"][1])
        else:
            self._social = randint(Personality.facet_range[0], Personality.facet_range[1])
            
        if aggress is not None:
            self._aggress = Personality.adjust_to_range(aggress)
        elif _tr:
            self._aggress = randint(_tr["aggression"][0], _tr["aggression"][1])
        else:
            self._aggress = randint(Personality.facet_range[0], Personality.facet_range[1])
            
        if stable is not None:
            self._stable = Personality.adjust_to_range(stable)
        elif _tr:
            self._stable = randint(_tr["stability"][0], _tr["stability"][1])
        else:
            self._stable = randint(Personality.facet_range[0], Personality.facet_range[1])
                
        # If trait is still empty, or if the trait is not valid with the facets, change it. 
        if not self.trait or not self.is_trait_valid():
            self.choose_trait()
                
    def __repr__(self) -> str:
        """For debugging"""
        return f"{self.trait}: lawfulness {self.lawfulness}, aggression {self.aggression}, sociability {self.sociability}, stablity {self.stability}"
    
    def get_facet_string(self):
        """For saving the facets to file."""
        return f"{self.lawfulness},{self.sociability},{self.aggression},{self.stability}"
    
    def __getitem__(self, key):
        """Alongside __setitem__, Allows you to treat this like a dictionary if you want. """
        return getattr(self, key)
    
    def __setitem__(self, key, newval):
        """Alongside __getitem__, Allows you to treat this like a dictionary if you want. """
        setattr(self, key, newval)

    # ---------------------------------------------------------------------------- #
    #                               PROPERTIES                                     #
    # ---------------------------------------------------------------------------- #
    
    @property
    def lawfulness(self):
        return self._law
    
    @lawfulness.setter
    def lawfulness(self, new_val):
        """Do not use property in init"""
        self._law = Personality.adjust_to_range(new_val)
        if not self.is_trait_valid():
            self.choose_trait()
            
    @property
    def sociability(self):
        return self._social
    
    @sociability.setter
    def sociability(self, new_val):
        """Do not use property in init"""
        self._social = Personality.adjust_to_range(new_val)
        if not self.is_trait_valid():
            self.choose_trait()
            
    @property
    def aggression(self):
        return self._aggress
    
    @aggression.setter
    def aggression(self, new_val):
        """Do not use property in init"""
        self._aggress = Personality.adjust_to_range(new_val)
        if not self.is_trait_valid():
            self.choose_trait()
            
    @property
    def stability(self):
        return self._stable
    
    @stability.setter
    def stability(self, new_val):
        """Do not use property in init"""
        self._stable = Personality.adjust_to_range(new_val)
        if not self.is_trait_valid():
            self.choose_trait()
            

    # ---------------------------------------------------------------------------- #
    #                               METHODS                                        #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def adjust_to_range(val:int) -> int:
        """Take an integer and adjust it to be in the trait-range """
        
        if val < Personality.facet_range[0]:
            val = Personality.facet_range[0]
        elif val > Personality.facet_range[1]:
            val = Personality.facet_range[1]
        
        return val
    
    def set_kitten(self, kitten:bool):
        """Switch the trait-type. True for kitten, False for normal"""
        self.kitten = kitten
        if not self.is_trait_valid():
            self.choose_trait()
        
    def is_trait_valid(self) -> bool:
        """Return True if the current facets fit the trait ranges, false
        if it doesn't. Also returns false if the trait is not in the trait dict.  """
        
        if self.kitten:
            trait_type_dict = Personality.trait_ranges["kitten_traits"]
        else:
            trait_type_dict = Personality.trait_ranges["normal_traits"]
        
        if self.trait not in trait_type_dict:
            return False
        
        trait_range = trait_type_dict[self.trait]
        
        if not (trait_range["lawfulness"][0] <= self.lawfulness 
                <= trait_range["lawfulness"][1]):
            return False
        if not (trait_range["sociability"][0] <= self.sociability 
                <= trait_range["sociability"][1]):
            return False
        if not (trait_range["aggression"][0] <= self.aggression 
                <= trait_range["aggression"][1]):
            return False
        if not (trait_range["stability"][0] <= self.stability 
                <= trait_range["stability"][1]):
            return False
        
        return True
    
    def choose_trait(self):
        """Chooses trait based on the facets """
        
        if self.kitten:
            trait_type_dict = Personality.trait_ranges["kitten_traits"]
        else:
            trait_type_dict = Personality.trait_ranges["normal_traits"]
        
        possible_traits = []
        for trait, fac in trait_type_dict.items():
            if not (fac["lawfulness"][0] <= self.lawfulness <= fac["lawfulness"][1]):
                continue
            if not (fac["sociability"][0] <= self.sociability <= fac["sociability"][1]):
                continue
            if not (fac["aggression"][0] <= self.aggression <= fac["aggression"][1]):
                continue
            if not (fac["stability"][0] <= self.stability <= fac["stability"][1]):
                continue
            
            possible_traits.append(trait)
            
        if possible_traits:
            self.trait = choice(possible_traits)
        else:
            print("No possible traits! Using 'strange'")
            self.trait = "strange"
            
    def facet_wobble(self, max=5):
        """Makes a small adjustment to all the facets, and redetermines trait if needed."""        
        self.lawfulness += randint(-max, max)
        self.stability += randint(-max, max)
        self.aggression += randint(-max, max)
        self.sociability += randint(-max, max)
        
    def rusasirah_influence(self, rusasirah:Rabbit):
        """applies rusasirah influence after the pair go on a patrol together 
            returns history information in the form (rusasirah_id, facet_affected, amount_affected)"""
        rusasirah_personality = rusasirah.personality
        
        #Get possible facet values
        possible_facets = {i: rusasirah_personality[i] - self[i] for i in 
                           Personality.facet_types if rusasirah_personality[i] - self[i] != 0}
        
        if possible_facets:
            # Choice trait to effect, weighted by the abs of the difference (higher difference = more likely to effect)
            facet_affected = choices([i for i in possible_facets], weights=[abs(i) for i in possible_facets.values()], k=1)[0]
            # stupid python with no sign() function by default. 
            amount_affected = int(possible_facets[facet_affected]/abs(possible_facets[facet_affected]) * randint(1, 2))
            self[facet_affected] += amount_affected
            return (rusasirah.ID, facet_affected, amount_affected)
        else:
            #This will only trigger if they have the same personality. 
            return None

# Twelve example rabbits
def create_example_rabbits():
    e = sample(range(12), 3)
    not_allowed = ['NOPAW', 'NOTAIL', 'HALFTAIL', 'NOEAR', 'BOTHBLIND', 'RIGHTBLIND', 'LEFTBLIND', 'BRIGHTHEART',
                   'NOLEFTEAR', 'NORIGHTEAR', 'MANLEG']
    for a in range(12):
        if a in e:
            game.choose_rabbits[a] = Rabbit(status='rabbit', biome=None)
        else:
            game.choose_rabbits[a] = Rabbit(status=choice(
                ['kitten', 'rusasi', 'rabbit', 'rabbit', 'elder']), biome=None)
        if game.choose_rabbits[a].months >= 160:
            game.choose_rabbits[a].months = choice(range(120, 155))
        elif game.choose_rabbits[a].months == 0:
            game.choose_rabbits[a].months = choice([1, 2, 3, 4, 5])
        for scar in game.choose_rabbits[a].pelt.scars:
            if scar in not_allowed:
                game.choose_rabbits[a].pelt.scars.remove(scar)
    
        #update_sprite(game.choose_rabbits[a])
    

# RABBIT CLASS ITEMS
rabbit_class = Rabbit(example=True)
game.rabbit_class = rabbit_class

# ---------------------------------------------------------------------------- #
#                                load json files                               #
# ---------------------------------------------------------------------------- #

resource_directory = "resources/dicts/conditions/"

with open(f"{resource_directory}illnesses.json", 'r') as read_file:
    ILLNESSES = ujson.loads(read_file.read())

with open(f"{resource_directory}injuries.json", 'r') as read_file:
    INJURIES = ujson.loads(read_file.read())

with open(f"{resource_directory}permanent_conditions.json", 'r') as read_file:
    PERMANENT = ujson.loads(read_file.read())

resource_directory = "resources/dicts/events/death/death_reactions/"

with open(f"{resource_directory}minor_major.json", 'r') as read_file:
    MINOR_MAJOR_REACTION = ujson.loads(read_file.read())

with open(f"resources/dicts/lead_ceremony_sc.json", 'r') as read_file:
    LEAD_CEREMONY_SC = ujson.loads(read_file.read())

with open(f"resources/dicts/lead_ceremony_df.json", 'r') as read_file:
    LEAD_CEREMONY_DF = ujson.loads(read_file.read())

with open(f"resources/dicts/backstories.json", 'r') as read_file:
    BACKSTORIES = ujson.loads(read_file.read())