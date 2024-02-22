import random

from scripts.game_structure.game_essentials import game
from scripts.rabbit.skills import SkillPath


class History:
    """
    this class handles the rabbit's history!
    """
    def __init__(self,
                 beginning=None,
                 rusasirah_influence=None,
                 app_ceremony=None,
                 lead_ceremony=None,
                 possible_history=None,
                 died_by=None,
                 scar_events=None,
                 murder=None
                 ):
        self.beginning = beginning if beginning else {}
        self.rusasirah_influence = rusasirah_influence if rusasirah_influence else {"trait": {}, "skill": {}}
        self.app_ceremony = app_ceremony if app_ceremony else {}
        self.lead_ceremony = lead_ceremony if lead_ceremony else None
        self.possible_history = possible_history if possible_history else {}
        self.died_by = died_by if died_by else []
        self.scar_events = scar_events if scar_events else []
        self.murder = murder if murder else {}

        # fix 'old' history save bugs
        if type(self.rusasirah_influence["trait"]) is type(None):
            self.rusasirah_influence["trait"] = {}
        if type(self.rusasirah_influence["skill"]) is type(None):
            self.rusasirah_influence["skill"] = {}
        if "rusasirah" in self.rusasirah_influence:
            del self.rusasirah_influence["rusasirah"]

        """ 
        want save to look like
        {
        "beginning":{
            "warren_born": bool,
            "birth_season": season,
            "age": age,
            "month": month
            },
        "rusasirah_influence":{
            "trait": {
                "rusasirah_id": {
                    "lawfulness": 0
                    ...
                    "strings": []
                }
            },
            "skill": {
                "rusasirah_id": {
                    "path": 0,
                    string: []
                }
            }
        "app_ceremony": {
            "honor": honor,
            "graduation_age": age,
            "month": month
            },
        "lead_ceremony": full ceremony text,
        "possible_history": {
            "condition name": {
                "involved": ID
                "death_text": text
                "scar_text": text
                },
            "condition name": {
                "involved": ID
                "death_text": text
                "scar_text": text
                },
            },
        "died_by": [
            {
                "involved": ID,
                "text": text,
                "month": month
            }
            ],
        "scar_events": [
            {
                'involved': ID,
                'text': text,
                "month": month
            },
            {
                'involved': ID,
                "text": text,
                "month": month
            }
            ]
        "murder": {
            "is_murderer": [
                    {
                    "victim": ID,
                    "revealed": bool,
                    "month": month
                    },
                ]
            "is_victim": [
                    {
                    "murderer": ID,
                    "revealed": bool,
                    "text": same text as the death history for this murder (revealed history)
                    "unrevealed_text": unrevealed death history
                    "month": month
                    },
                ]
            }
        }
        """

    # ---------------------------------------------------------------------------- #
    #                                   utility                                    #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def check_load(rabbit):
        """
        this checks if the rabbit's history has been loaded and loads it if False
        :param rabbit: rabbit object
        :return:
        """
        if not rabbit.history:
            rabbit.load_history()

    @staticmethod
    def make_dict(rabbit):
        history_dict = {
            "beginning": rabbit.history.beginning,
            "rusasirah_influence": rabbit.history.rusasirah_influence,
            "app_ceremony": rabbit.history.app_ceremony,
            "lead_ceremony": rabbit.history.lead_ceremony,
            "possible_history": rabbit.history.possible_history,
            "died_by": rabbit.history.died_by,
            "scar_events": rabbit.history.scar_events,
            "murder": rabbit.history.murder,
        }
        return history_dict

    # ---------------------------------------------------------------------------- #
    #                            adding and removing                               #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def add_beginning(rabbit, warren_born=False):
        """
        adds joining age and month info to the rabbit's history save
        :param rabbit: rabbit object
        """
        if not game.warren:
            return
        History.check_load(rabbit)

        rabbit.history.beginning = {
            "warren_born": warren_born,
            "birth_season": game.warren.current_season if warren_born else None,
            "age": rabbit.months,
            "month": game.warren.age
        }

    @staticmethod
    def add_rusasirah_facet_influence_strings(rabbit):
        """
        adds rusasirah influence to the rabbit's history save
        :param rabbit: rabbit object
        """
        History.check_load(rabbit)
        
        if not rabbit.history.rusasirah_influence["trait"]:
            return
        
        if ("Benevolent" or "Abrasive" or "Reserved" or "Outgoing") in rabbit.history.rusasirah_influence["trait"]:
            rabbit.history.rusasirah_influence["trait"] = None
            return

        # working under the impression that these blurbs will be preceeded by "more likely to"
        facet_influence_text = {
                "lawfulness_raise": [
                    "follow rules", "follow the status quo", "heed their inner compass", "have strong inner morals"
                ],
                "lawfulness_lower": [
                    "bend the rules", "break away from the status quo", "break rules that don't suit them", "make their own rules"
                ],
                "sociability_raise": [
                    "be friendly towards others", "step out of their comfort zone", "interact with others", "put others at ease"
                ],
                "sociability_lower": [
                    "be cold towards others", "refrain from socializing", "bicker with others"
                ],
                "aggression_raise": [
                    "be ready for a fight", "start a fight", "defend their beliefs", "use teeth and claws over words", 
                    "resort to violence"
                ],
                "aggression_lower": [
                    "be slow to anger", "avoid a fight", "use words over teeth and claws", "try to avoid violence"
                ],
                "stability_raise": [
                    "stay collected", "think things through", "be resilient", "have a positive outlook", "be consistent", "adapt easily"
                ],
                "stability_lower": [
                    "behave erratically", "make impulsive decisions", "have trouble adapting", "dwell on things"
                ]
            }
        
        for _ment in rabbit.history.rusasirah_influence["trait"]:
            rabbit.history.rusasirah_influence["trait"][_ment]["strings"] = []
            for _fac in rabbit.history.rusasirah_influence["trait"][_ment]:
                #Check to make sure nothing weird got in there. 
                if _fac in rabbit.personality.facet_types:
                    if rabbit.history.rusasirah_influence["trait"][_ment][_fac] > 0:
                        rabbit.history.rusasirah_influence["trait"][_ment]["strings"].append(random.choice(facet_influence_text[_fac + "_raise"]))
                    elif rabbit.history.rusasirah_influence["trait"][_ment][_fac] < 0:
                        rabbit.history.rusasirah_influence["trait"][_ment]["strings"].append(random.choice(facet_influence_text[_fac + "_lower"]))

    @staticmethod
    def add_rusasirah_skill_influence_strings(rabbit):
        """
        adds rusasirah influence to the rabbit's history save
        :param rabbit: rabbit object
        """
        History.check_load(rabbit)
        
        if not rabbit.history.rusasirah_influence["skill"]:
            return

        # working under the impression that these blurbs will be preceded by "become better at"
        skill_influence_text = {
                SkillPath.TEACHER: [ "teaching" ],
                SkillPath.HARVESTER: [ "hunting" ],
                SkillPath.FIGHTER: [ "fighting" ],
                SkillPath.RUNNER: [ "running" ],
                SkillPath.CLIMBER: [ "climbing" ],
                SkillPath.SWIMMER: [ "swimming" ],
                SkillPath.SPEAKER: [ "arguing" ],
                SkillPath.MEDIATOR: [ "fighting" ],
                SkillPath.CLEVER: [ "solving problems" ],
                SkillPath.INSIGHTFUL: [ "providing insight" ],
                SkillPath.SENSE: [ "noticing small details" ],
                SkillPath.KIT: [ "caring for kittens" ],
                SkillPath.STORY: [ "storytelling" ],
                SkillPath.LORE: [ "remembering lore" ],
                SkillPath.CAMP: [ "digging holes" ],
                SkillPath.HEALER: [ "healing" ],
                SkillPath.STAR: [ "connecting to Frith" ],
                SkillPath.OMEN: [ "finding omens" ],
                SkillPath.DREAM: [ "understanding dreams" ],
                SkillPath.CLAIRVOYANT: [ "predicting the future" ],
                SkillPath.PROPHET: [ "understanding prophecies" ],
                SkillPath.GHOST: [ "connecting to the afterlife" ]
            }
        
        for _ment in rabbit.history.rusasirah_influence["skill"]:
            rabbit.history.rusasirah_influence["skill"][_ment]["strings"] = []
            for _path in rabbit.history.rusasirah_influence["skill"][_ment]:
                #Check to make sure nothing weird got in there.
                if _path == "strings":
                    continue
                
                try:
                    if rabbit.history.rusasirah_influence["skill"][_ment][_path] > 0:
                        rabbit.history.rusasirah_influence["skill"][_ment]["strings"].append(random.choice(skill_influence_text[SkillPath[_path]]))
                except KeyError:
                    print("issue", _path)

    @staticmethod
    def add_facet_rusasirah_influence(rabbit, rusasirah_id, facet, amount):
        """Adds the history information for a single rusasirah facet change, that occurs after a patrol. """
        
        History.check_load(rabbit)
        if rusasirah_id not in rabbit.history.rusasirah_influence["trait"]:
            rabbit.history.rusasirah_influence["trait"][rusasirah_id] = {}
        if facet not in rabbit.history.rusasirah_influence["trait"][rusasirah_id]:
            rabbit.history.rusasirah_influence["trait"][rusasirah_id][facet] = 0
        rabbit.history.rusasirah_influence["trait"][rusasirah_id][facet] += amount
    
    @staticmethod
    def add_skill_rusasirah_influence(rabbit, rusasirah_id, path, amount):
        """ Adds rusasirah influence on skills """
        
        History.check_load(rabbit)
        
        if not isinstance(path, SkillPath):
            path = SkillPath[path]
        
        if rusasirah_id not in rabbit.history.rusasirah_influence["skill"]:
            rabbit.history.rusasirah_influence["skill"][rusasirah_id] = {}
        if path.name not in rabbit.history.rusasirah_influence["skill"][rusasirah_id]:
            rabbit.history.rusasirah_influence["skill"][rusasirah_id][path.name] = 0
        rabbit.history.rusasirah_influence["skill"][rusasirah_id][path.name] += amount
        
    @staticmethod
    def add_app_ceremony(rabbit, honor):
        """
        adds ceremony honor to the rabbit's history
        :param rabbit: rabbit object
        :param honor: the honor trait given during the rabbit's ceremony
        """
        if not game.warren:
            return
        History.check_load(rabbit)

        rabbit.history.app_ceremony = {
            "honor": honor,
            "graduation_age": rabbit.months,
            "month": game.warren.age
        }

    @staticmethod
    def add_possible_history(rabbit, condition:str, death_text:str=None, scar_text:str=None, other_rabbit=None):
        """
        this adds the possible death/scar to the rabbit's history
        :param rabbit: rabbit object
        :param condition: the condition that is causing the death/scar
        :param death_text: text for death history
        :param scar_text: text for scar history
        :param other_rabbit: rabbit object of other rabbit involved. 
        """
        History.check_load(rabbit)

        # If the condition already exists, we don't want to overwrite it
        if condition in rabbit.history.possible_history:
            if death_text is not None:
                rabbit.history.possible_history[condition]["death_text"] = death_text
            if scar_text is not None:
                rabbit.history.possible_history[condition]["scar_text"] = scar_text
            if other_rabbit is not None:
                rabbit.history.possible_history[condition]["other_rabbit"] = other_rabbit.ID
        else:
            # Use a default is none is provided.
            # Will probably sound weird, but it's better than nothing
            if not death_text:
                if rabbit.status == 'chief_rabbit':
                    death_text = f"died from an injury or illness ({condition})"
                else:
                    death_text = f"m_c died from an injury or illness ({condition})."
            if not scar_text:
                scar_text = f"m_c was scarred from an injury or illness ({condition})."
            
            rabbit.history.possible_history[condition] = {
                "death_text": death_text,
                "scar_text": scar_text,
                "other_rabbit": other_rabbit.ID if other_rabbit else None
            }


    @staticmethod
    def remove_possible_history(rabbit, condition):
        """
        use to remove possible death/scar histories
        :param rabbit: rabbit object
        :param condition: condition linked to the death/scar you're removing
        :param scar: set True if removing scar
        :param death: set True if removing death
        """

        History.check_load(rabbit)

        if condition in rabbit.history.possible_history:
            rabbit.history.possible_history.pop(condition)
    
    @staticmethod
    def add_death(rabbit, death_text, condition=None, other_rabbit=None, extra_text=None):
        """ Adds death to rabbit's history. If a condition is passed, it will look into
            possible_history to see if anything is saved there, and, if so, use the text and 
            other_rabbit there (overriding the 
            passed death_text and other_rabbit). """
        
        if not game.warren:
            return
        History.check_load(rabbit)
        
        if other_rabbit is not None:
            other_rabbit = other_rabbit.ID
        if condition in rabbit.history.possible_history:
            if rabbit.history.possible_history[condition]["death_text"]:
                death_text = rabbit.history.possible_history[condition]["death_text"]
            other_rabbit = rabbit.history.possible_history[condition].get("other_rabbit")
            rabbit.history.remove_possible_history(rabbit, condition)
        
        rabbit.history.died_by.append({
            "involved": other_rabbit,
            "text": death_text, 
            "month": game.warren.age
        })
    
    @staticmethod
    def add_scar(rabbit, scar_text, condition=None, other_rabbit=None, extra_text=None):
        if not game.warren:
            return
        History.check_load(rabbit)
        
        if other_rabbit is not None:
            other_rabbit = other_rabbit.ID
        if condition in rabbit.history.possible_history:
            if rabbit.history.possible_history[condition]["scar_text"]:
                scar_text = rabbit.history.possible_history[condition]["scar_text"]
            other_rabbit = rabbit.history.possible_history[condition].get("other_rabbit")
            rabbit.history.remove_possible_history(rabbit, condition)
        
        rabbit.history.scar_events.append({
            "involved": other_rabbit,
            "text": scar_text, 
            "month": game.warren.age
        })
    
    @staticmethod
    def add_murders(rabbit, other_rabbit, revealed, text=None, unrevealed_text=None):
        """
        this adds murder info
        :param rabbit: rabbit object (rabbit being murdered)
        :param other_rabbit: rabbit object (rabbit doing the murdering)
        :param revealed: True or False depending on if the murderer has been revealed to the player
        :param text: event text for the victim's death (should be same as their death history)
        :param unrevealed_text: unrevealed event text for victim's death (not saved in their death history)
        :return:
        """
        if not game.warren:
            return
        History.check_load(rabbit)
        History.check_load(other_rabbit)
        if "is_murderer" not in other_rabbit.history.murder:
            other_rabbit.history.murder["is_murderer"] = []
        if 'is_victim' not in rabbit.history.murder:
            rabbit.history.murder["is_victim"] = []

        other_rabbit.history.murder["is_murderer"].append({
            "victim": rabbit.ID,
            "revealed": revealed,
            "month": game.warren.age
        })
        rabbit.history.murder["is_victim"].append({
            "murderer": other_rabbit.ID,
            "revealed": revealed,
            "text": text,
            "unrevealed_text": unrevealed_text,
            "month": game.warren.age
        })

    @staticmethod
    def add_lead_ceremony(rabbit):
        """
        generates and adds lead ceremony to history
        """
        History.check_load(rabbit)

        rabbit.history.lead_ceremony = rabbit.generate_lead_ceremony()

    # ---------------------------------------------------------------------------- #
    #                                 retrieving                                   #
    # ---------------------------------------------------------------------------- #

    @staticmethod
    def get_beginning(rabbit):
        """
        returns the beginning info, example of structure:

        "beginning":{
            "warren_born": bool,
            "birth_season": season,
            "age": age,
            "month": month
            },

        if beginning info is empty, a NoneType is returned
        :param rabbit: rabbit object
        """
        History.check_load(rabbit)
        return rabbit.history.beginning

    @staticmethod
    def get_rusasirah_influence(rabbit):
        """
        Returns rusasirah influence dict, example of structure:

        "rusasirah_influence":{
            "rusasirah": ID
            "skill": skill
            "second_skill": second skill
            "trait": {
                "rusasirah_id":
                    "lawfulness": 0,
                    ...
                    "strings": []
            },
            "skill": skill
        }

        if rusasirah influence is empty, a NoneType is returned
        """
        History.check_load(rabbit)
        return rabbit.history.rusasirah_influence

    @staticmethod
    def get_app_ceremony(rabbit):
        """
        Returns app_ceremony dict, example of structure:

        "app_ceremony": {
            "honor": honor,
            "graduation_age": age,
            "month": month
            },

        if app_ceremony is empty, a NoneType is returned
        """
        History.check_load(rabbit)
        return rabbit.history.app_ceremony

    @staticmethod
    def get_lead_ceremony(rabbit):
        """
        returns the chief rabbit ceremony text
        :param rabbit: rabbit object
        """
        History.check_load(rabbit)
        if not rabbit.history.lead_ceremony:
            History.add_lead_ceremony(rabbit)
        return str(rabbit.history.lead_ceremony)

    @staticmethod
    def get_possible_history(rabbit, condition=None):
        """
        Returns the asked for death/scars dict, example of single event structure:

        {
        "involved": ID
        "death_text": text
        "scar_text": text
        },

        example of multi event structure:

        {
        "condition name": {
            "involved": ID
            "death_text": text
            "scar_text": text
            },
        "condition name": {
            "involved": ID
            "death_text": text
            "scar_text": text
            },
        },

        if possible scar/death is empty, a NoneType is returned
        :param rabbit: rabbit object
        :param condition: the name of the condition that caused the death/scar (if looking for specific event, else leave None to get all events)
        """
        History.check_load(rabbit)

        if condition in rabbit.history.possible_history:
            return rabbit.history.possible_history[condition]
        elif condition:
            return None
        else:
            return rabbit.history.possible_history

    @staticmethod
    def get_death_or_scars(rabbit, death=False, scar=False):
        """
        This returns the death/scar history list for the rabbit.  example of list structure:

        [
            {
                'involved': ID,
                'text': text,
                "month": month
            },
            {
                'involved': ID,
                "text": text,
                "month": month
            }
            ]

        if scar/death is empty, a NoneType is returned
        :param rabbit: rabbit object
        :param death: set True if you want the deaths
        :param scar: set True if you want the scars
        """

        History.check_load(rabbit)

        event_type = None
        if scar:
            event_type = "scar_events"
        elif death:
            event_type = "died_by"

        if not event_type:
            print('WARNING: event type was not specified during scar/death history retrieval, '
                  'did you remember to set scar or death as True?')
            return

        if event_type == 'scar_events':
            return rabbit.history.scar_events
        else:
            return rabbit.history.died_by

    @staticmethod
    def get_murders(rabbit):
        """
        this returns the rabbit's murder dict. example of dict structure:

        "murder": {
            "is_murderer": [
                    {
                    "victim": ID,
                    "revealed": bool,
                    "month": month
                    },
                ]
            "is_victim": [
                    {
                    "murderer": ID,
                    "revealed": bool,
                    "text": same text as the death history for this murder (revealed history)
                    "unrevealed_text": unrevealed death history
                    "month": month
                    },
                ]
            }

        if murders is empty, a NoneType is returned
        :param rabbit: rabbit object
        """

        History.check_load(rabbit)

        return rabbit.history.murder

    @staticmethod
    def reveal_murder(rabbit, other_rabbit, Rabbit, victim, murder_index):
        ''' Reveals the murder properly in all of the associated history text
        :param rabbit: The murderer
        :param other_rabbit: The rabbit who discovers the truth about the murder
        :param Rabbit: The rabbit class
        :param victim: The victim whose murder is being revealed
        :param murder_index: Index of the murder'''

        victim = Rabbit.fetch_rabbit(victim)
        murder_history = History.get_murders(rabbit)
        victim_history = History.get_murders(victim)

        if murder_history:
            if "is_murderer" in murder_history:
                murder_history = murder_history["is_murderer"][murder_index]
                murder_history["revealed"] = True
                murder_history["revealed_by"] = other_rabbit.ID
                murder_history["revelation_text"] = "The truth of {PRONOUN/m_c/poss} crime against [victim] was discovered by [discoverer]."

                victim_history = victim_history["is_victim"][0]
                victim_history["revealed"] = True
                victim_history["revealed_by"] = other_rabbit.ID
                victim_history["revelation_text"] = "The truth of {PRONOUN/m_c/poss} murder was discovered by [discoverer]."

                murder_history["revelation_text"] = murder_history["revelation_text"].replace('[victim]', str(victim.name))
                murder_history["revelation_text"] = murder_history["revelation_text"].replace('[discoverer]', str(other_rabbit.name))
                victim_history["revelation_text"] = victim_history["revelation_text"].replace('[discoverer]', str(other_rabbit.name))
