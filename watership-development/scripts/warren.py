# pylint: disable=line-too-long
"""

TODO: Docs


"""

# pylint: enable=line-too-long

import random
from random import choice, randint
import os

import pygame

from scripts.rabbit.history import History
from scripts.events_module.generate_events import OngoingEvent
from scripts.housekeeping.datadir import get_save_dir

import ujson
import statistics

from scripts.game_structure.game_essentials import game
from scripts.housekeeping.version import get_version_info, SAVE_VERSION_NUMBER
from scripts.utility import update_sprite, get_current_season, quit  # pylint: disable=redefined-builtin
from scripts.rabbit.rabbits import Rabbit, rabbit_class
from scripts.rabbit.names import names
from scripts.rabbit.pelts import Pelt
from scripts.warren_resources.freshkill import Freshkill_Pile, Nutrition
from scripts.rabbit.sprites import sprites
from sys import exit  # pylint: disable=redefined-builtin


class Warren():
    """

    TODO: Docs

    """
    BIOME_TYPES = ["Forest", "Plains", "Mountainous", "Beach"]

    RABBIT_TYPES = [
        "newborn",
        "kitten",
        "rusasi",
        "rabbit",
        "healer",
        "captain",
        "chief rabbit",
        "elder",
        "owsla",
        "general",
    ]


    warren_rabbits = []
    inle_rabbits = []
    darkforest_rabbits = []
    unknown_rabbits = []
    seasons = [
        'Spring',
        'Spring',
        'Spring',
        'Summer',
        'Summer',
        'Summer',
        'Autumn',
        'Autumn',
        'Autumn',
        'Winter',
        'Winter',
        'Winter',
    ]

    with open("resources/placements.json", 'r') as read_file:
        layouts = ujson.loads(read_file.read())
    
    age = 0
    current_season = 'Spring'
    all_warrens = []

    def __init__(self,
                 name="",
                 chief_rabbit=None,
                 captain=None,
                 healer=None,
                 biome='Forest',
                 burrow_bg=None,
                 game_mode='classic',
                 starting_members=[],
                 starting_season='Spring'):
        self.history = History()
        if name == "":
            return
        
        self.name = name
        self.chief_rabbit = chief_rabbit
        if self.chief_rabbit:
            self.chief_rabbit.status_change('chief rabbit')
            self.warren_rabbits.append(self.chief_rabbit.ID)

        self.chief_rabbit_predecessors = 0
        self.captain = captain
        if captain is not None:
            self.captain.status_change('captain')
            self.warren_rabbits.append(self.captain.ID)
        self.captain_predecessors = 0
        self.healer = healer
        self.healer_list = []
        self.healer_predecessors = 0
        if healer is not None:
            self.warren_rabbits.append(self.healer.ID)
            self.healer_list.append(self.healer.ID)
            if healer.status != 'healer':
                Rabbit.all_rabbits[healer.ID].status_change('healer')
        self.healer_number = len(
            self.healer_list
        )  # Must do this after the healer is added to the list.
        self.herbs = {}
        self.age = 0
        self.current_season = 'Spring'
        self.starting_season = starting_season
        self.instructor = None
        # This is the first rabbit in inle, to "guide" the other dead rabbits there.
        self.biome = biome
        self.burrow_bg = burrow_bg
        self.game_mode = game_mode
        self.pregnancy_data = {}
        self.inheritance = {}
        
        # Init Settings
        self.warren_settings = {}
        self.setting_lists = {}
        with open("resources/warrensettings.json", 'r') as read_file:
            _settings = ujson.loads(read_file.read())

        for setting, values in _settings['__other'].items():
            self.warren_settings[setting] = values[0]
            self.setting_lists[setting] = values

        all_settings = []
        all_settings.append(_settings['general'])
        all_settings.append(_settings['role'])
        all_settings.append(_settings['relation'])
        all_settings.append(_settings['freshkill_tactics'])

        for setting in all_settings:  # Add all the settings to the settings dictionary
            for setting_name, inf in setting.items():
                self.warren_settings[setting_name] = inf[2]
                self.setting_lists[setting_name] = [inf[2], not inf[2]]
        
        
        #Reputation is for hlessis/pets/outsiders in general that wish to join the warren. 
        #it's a range from 1-100, with 30-70 being neutral, 71-100 being "welcoming",
        #and 1-29 being "hostile". if you're hostile to outsiders, they will VERY RARELY show up.
        self._reputation = 80
        
        self.starting_members = starting_members
        if game_mode in ['expanded', 'cruel season']:
            self.freshkill_pile = Freshkill_Pile()
        else:
            self.freshkill_pile = None
        self.primary_disaster = None
        self.secondary_disaster = None
        self.war = {
            "at_war": False,
            "enemy": None, 
            "duration": 0,
        }

        self.faded_ids = [
        ]  # Stores ID's of faded rabbits, to ensure these IDs aren't reused.

    def create_warren(self):
        """
        This function is only called once a new warren is
        created in the 'warren created' screen, not every time
        the program starts
        """
        self.instructor = Rabbit(prefix="Black Rabbit of Inle", status="captain", months=149)
        self.instructor.pelt = Pelt(name="SingleColour", length="short", colour="BLACK", eye_color="GREY", adult_sprite="7")
        self.instructor.dead = True
        self.instructor.dead_for = randint(20, 200)
        self.add_rabbit(self.instructor)
        self.add_to_inle(self.instructor)
        self.all_warrens = []

        key_copy = tuple(Rabbit.all_rabbits.keys())
        for i in key_copy:  # Going through all currently existing rabbits
            # rabbit_class is a Rabbit-object
            not_found = True
            for x in self.starting_members:
                if Rabbit.all_rabbits[i] == x:
                    self.add_rabbit(Rabbit.all_rabbits[i])
                    not_found = False
            if Rabbit.all_rabbits[i] != self.chief_rabbit and Rabbit.all_rabbits[i] != \
                    self.healer and Rabbit.all_rabbits[i] != \
                    self.captain and Rabbit.all_rabbits[i] != \
                    self.instructor \
                    and not_found:
                Rabbit.all_rabbits[i].example = True
                self.remove_rabbit(Rabbit.all_rabbits[i].ID)

        # give thoughts,actions and relationships to rabbits
        for rabbit_id in Rabbit.all_rabbits:
            Rabbit.all_rabbits.get(rabbit_id).init_all_relationships()
            Rabbit.all_rabbits.get(rabbit_id).backstory = 'warren_founder'
            if Rabbit.all_rabbits.get(rabbit_id).status == 'rusasi':
                Rabbit.all_rabbits.get(rabbit_id).status_change('rusasi')
            Rabbit.all_rabbits.get(rabbit_id).thoughts()

        game.save_rabbits()
        number_other_warrens = randint(3, 5)
        for _ in range(number_other_warrens):
            self.all_warrens.append(OtherWarren())
        self.save_warren()
        game.save_warrenlist(self.name)
        game.switches['warren_list'] = game.read_warrens()
        # if map_available:
        #    save_map(game.map_info, game.warren.name)

        # CHECK IF CAMP BG IS SET -fail-safe in case it gets set to None-
        if game.switches['burrow_bg'] is None:
            random_burrow_options = ['burrow1', 'burrow2']
            random_burrow = choice(random_burrow_options)
            game.switches['burrow_bg'] = random_burrow

        # if no game mode chosen, set to Classic
        if game.switches['game_mode'] is None:
            game.switches['game_mode'] = 'classic'
            self.game_mode = 'classic'
        #if game.switches['game_mode'] == 'cruel_season':
        #    game.settings['disasters'] = True

        # set the starting season
        season_index = self.seasons.index(self.starting_season)
        self.current_season = self.seasons[season_index]

    def add_rabbit(self, rabbit):  # rabbit is a 'Rabbit' object
        """ Adds rabbit into the list of warren rabbits"""
        if rabbit.ID in Rabbit.all_rabbits and rabbit.ID not in self.warren_rabbits:
            self.warren_rabbits.append(rabbit.ID)

    def add_to_inle(self, rabbit):  # Same as add_rabbit
        """
        Places the dead rabbit into Inle.
        It should not be removed from the list of rabbits in the warren
        """
        if rabbit.ID in Rabbit.all_rabbits and rabbit.dead and rabbit.ID not in self.inle_rabbits and rabbit.df is False:
            # The dead-value must be set to True before the rabbit can go to inle
            self.inle_rabbits.append(rabbit.ID)
            if rabbit.ID in self.darkforest_rabbits:
                self.darkforest_rabbits.remove(rabbit.ID)
            if rabbit.ID in self.unknown_rabbits:
                self.unknown_rabbits.remove(rabbit.ID)
            if rabbit.ID in self.healer_list:
                self.healer_list.remove(rabbit.ID)
                self.healer_predecessors += 1

    def add_to_darkforest(self, rabbit):  # Same as add_rabbit
        """
        Places the dead rabbit into the lightless.
        It should not be removed from the list of rabbits in the warren
        """
        if rabbit.ID in Rabbit.all_rabbits and rabbit.dead and rabbit.df:
            self.darkforest_rabbits.append(rabbit.ID)
            if rabbit.ID in self.inle_rabbits:
                self.inle_rabbits.remove(rabbit.ID)
            if rabbit.ID in self.unknown_rabbits:
                self.unknown_rabbits.remove(rabbit.ID)
            if rabbit.ID in self.healer_list:
                self.healer_list.remove(rabbit.ID)
                self.healer_predecessors += 1
            # update_sprite(Rabbit.all_rabbits[str(rabbit)])
            # The dead-value must be set to True before the rabbit can go to inle

    def add_to_unknown(self, rabbit):
        """
        Places dead rabbit into the unknown residence.
        It should not be removed from the list of rabbits in the warren
        :param rabbit: rabbit object
        """
        if rabbit.ID in Rabbit.all_rabbits and rabbit.dead and rabbit.outside:
            self.unknown_rabbits.append(rabbit.ID)
            if rabbit.ID in self.inle_rabbits:
                self.inle_rabbits.remove(rabbit.ID)
            if rabbit.ID in self.darkforest_rabbits:
                self.darkforest_rabbits.remove(rabbit.ID)
            if rabbit.ID in self.healer_list:
                self.healer_list.remove(rabbit.ID)
                self.healer_predecessors += 1

    def add_to_warren(self, rabbit):
        """
        TODO: DOCS
        """
        if rabbit.ID in Rabbit.all_rabbits and not rabbit.outside and rabbit.ID in Rabbit.outside_rabbits:
            # The outside-value must be set to True before the rabbit can go to cotc
            Rabbit.outside_rabbits.pop(rabbit.ID)
            rabbit.warren = str(game.warren.name)

    def add_to_outside(self, rabbit):  # same as add_rabbit
        """
        Places the gone rabbit into cotc.
        It should not be removed from the list of rabbits in the warren
        """
        if rabbit.ID in Rabbit.all_rabbits and rabbit.outside and rabbit.ID not in Rabbit.outside_rabbits:
            # The outside-value must be set to True before the rabbit can go to cotc
            Rabbit.outside_rabbits.update({rabbit.ID: rabbit})

    def remove_rabbit(self, ID):  # ID is rabbit.ID
        """
        This function is for completely removing the rabbit from the game,
        it's not meant for a rabbit that's simply dead
        """

        if Rabbit.all_rabbits[ID] in Rabbit.all_rabbits_list:
            Rabbit.all_rabbits_list.remove(Rabbit.all_rabbits[ID])

        if ID in Rabbit.all_rabbits:
            Rabbit.all_rabbits.pop(ID)
        
        if ID in self.warren_rabbits:
            self.warren_rabbits.remove(ID)
        if ID in self.inle_rabbits:
            self.inle_rabbits.remove(ID)
        if ID in self.unknown_rabbits:
            self.unknown_rabbits.remove(ID)
        if ID in self.darkforest_rabbits:
            self.darkforest_rabbits.remove(ID)

    def __repr__(self):
        if self.name is not None:
            _ = f'{self.name}: led by {self.chief_rabbit.name}' \
                f'with {self.healer.name} as healer'
            return _

        else:
            return 'No Warren'

    def new_chief_rabbit(self, chief_rabbit):
        """
        TODO: DOCS
        """
        if chief_rabbit:
            self.history.add_lead_ceremony(chief_rabbit)
            self.chief_rabbit = chief_rabbit
            Rabbit.all_rabbits[chief_rabbit.ID].status_change('chief_rabbit')
            self.chief_rabbit_predecessors += 1

        game.switches['new_chief_rabbit'] = None

    def new_captain(self, captain):
        """
        TODO: DOCS
        """
        if captain:
            self.captain = captain
            Rabbit.all_rabbits[captain.ID].status_change('captain')
            self.captain_predecessors += 1

    def new_healer(self, healer):
        """
        TODO: DOCS
        """
        if healer:
            if healer.status != 'healer':
                Rabbit.all_rabbits[healer.ID].status_change('healer')
            if healer.ID not in self.healer_list:
                self.healer_list.append(healer.ID)
            healer = self.healer_list[0]
            self.healer = Rabbit.all_rabbits[healer]
            self.healer_number = len(self.healer_list)

    def remove_healer(self, healer):
        """
        Removes a med rabbit. Use when retiring, or switching to rabbit
        """
        if healer:
            if healer.ID in game.warren.healer_list:
                game.warren.healer_list.remove(healer.ID)
                game.warren.healer_number = len(game.warren.healer_list)
            if self.healer:
                if healer.ID == self.healer.ID:
                    if game.warren.healer_list:
                        game.warren.healer = Rabbit.fetch_rabbit(
                            game.warren.healer_list[0])
                        game.warren.healer_number = len(game.warren.healer_list)
                    else:
                        game.warren.healer = None

    @staticmethod
    def switch_warrens(warren):
        """
        TODO: DOCS
        """
        game.save_warrenlist(warren)
        quit(savesettings=False, clearevents=True)

    def save_warren(self):
        """
        TODO: DOCS
        """

        warren_data = {
            "warrenname": self.name,
            "warrenage": self.age,
            "biome": self.biome,
            "burrow_bg": self.burrow_bg,
            "gamemode": self.game_mode,
            "instructor": self.instructor.ID,
            "reputation": self.reputation,
            "mediated": game.mediated,
            "starting_season": self.starting_season,
            "temperament": self.temperament,
            "version_name": SAVE_VERSION_NUMBER,
            "version_commit": get_version_info().version_number,
            "source_build": get_version_info().is_source_build
        }

        # LEADER DATA
        if self.chief_rabbit:
            warren_data["chief_rabbit"] = self.chief_rabbit.ID

        else:
            warren_data["chief_rabbit"] = None

        warren_data["chief_rabbit_predecessors"] = self.chief_rabbit_predecessors

        # DEPUTY DATA
        if self.captain:
            warren_data["captain"] = self.captain.ID
        else:
            warren_data["captain"] = None

        warren_data["captain_predecessors"] = self.captain_predecessors

        # MED RABBIT DATA
        if self.healer:
            warren_data["healer"] = self.healer.ID
        else:
            warren_data["healer"] = None
        warren_data["healer_number"] = self.healer_number
        warren_data["healer_predecessors"] = self.healer_predecessors

        # LIST OF CLAN RABBITS
        warren_data['warren_rabbits'] = ",".join([str(i) for i in self.warren_rabbits])

        warren_data["faded_rabbits"] = ",".join([str(i) for i in self.faded_ids])

        # Patrolled rabbits
        warren_data["patrolled_rabbits"] = [str(i) for i in game.patrolled]

        # OTHER CLANS
        # Warren Names
        warren_data["other_warrens_names"] = ",".join(
            [str(i.name) for i in self.all_warrens])
        warren_data["other_warrens_relations"] = ",".join(
            [str(i.relations) for i in self.all_warrens])
        warren_data["other_warren_temperament"] = ",".join(
            [str(i.temperament) for i in self.all_warrens])
        warren_data["war"] = self.war

        self.save_herbs(game.warren)
        self.save_disaster(game.warren)
        self.save_pregnancy(game.warren)

        self.save_warren_settings()
        if game.warren.game_mode in ['expanded', 'cruel season']:
            self.save_freshkill_pile(game.warren)

        game.safe_save(f"{get_save_dir()}/{self.name}warren.json", warren_data)

        if os.path.exists(get_save_dir() + f'/{self.name}warren.txt'):
            os.remove(get_save_dir() + f'/{self.name}warren.txt')

    def switch_setting(self, setting_name):
        """ Call this function to change a setting given in the parameter by one to the right on it's list """
        self.settings_changed = True

        # Give the index that the list is currently at
        list_index = self.setting_lists[setting_name].index(
            self.warren_settings[setting_name])

        if list_index == len(
                self.setting_lists[setting_name]
        ) - 1:  # The option is at the list's end, go back to 0
            self.warren_settings[setting_name] = self.setting_lists[setting_name][0]
        else:
            # Else move on to the next item on the list
            self.warren_settings[setting_name] = self.setting_lists[setting_name][
                list_index + 1]

    def save_warren_settings(self):
        game.safe_save(get_save_dir() + f'/{self.name}/warren_settings.json', self.warren_settings)

    def load_warren(self):
        """
        TODO: DOCS
        """

        version_info = None
        if os.path.exists(get_save_dir() + '/' + game.switches['warren_list'][0] +
                          'warren.json'):
            version_info = self.load_warren_json()
        elif os.path.exists(get_save_dir() + '/' + game.switches['warren_list'][0] +
                            'warren.txt'):
            self.load_warren_txt()
        else:
            game.switches[
                'error_message'] = "There was an error loading the warren.json"

        game.warren.load_warren_settings()

        return version_info

    def load_warren_txt(self):
        """
        TODO: DOCS
        """
        other_warrens = []
        if game.switches['warren_list'] == '':
            number_other_warrens = randint(3, 5)
            for _ in range(number_other_warrens):
                self.all_warrens.append(OtherWarren())
            return
        if game.switches['warren_list'][0].strip() == '':
            number_other_warrens = randint(3, 5)
            for _ in range(number_other_warrens):
                self.all_warrens.append(OtherWarren())
            return
        game.switches[
            'error_message'] = "There was an error loading the warren.txt"
        with open(get_save_dir() + '/' + game.switches['warren_list'][0] + 'warren.txt',
                  'r',
                  encoding='utf-8') as read_file:  # pylint: disable=redefined-outer-name
            warren_data = read_file.read()
        warren_data = warren_data.replace('\t', ',')
        sections = warren_data.split('\n')
        if len(sections) == 7:
            general = sections[0].split(',')
            chief_rabbitinfo = sections[1].split(',')
            captain_info = sections[2].split(',')
            healer_info = sections[3].split(',')
            instructor_info = sections[4]
            members = sections[5].split(',')
            other_warrens = sections[6].split(',')
        elif len(sections) == 6:
            general = sections[0].split(',')
            chief_rabbitinfo = sections[1].split(',')
            captain_info = sections[2].split(',')
            healer_info = sections[3].split(',')
            instructor_info = sections[4]
            members = sections[5].split(',')
            other_warrens = []
        else:
            general = sections[0].split(',')
            chief_rabbitinfo = sections[1].split(',')
            captain_info = 0, 0
            healer_info = sections[2].split(',')
            instructor_info = sections[3]
            members = sections[4].split(',')
            other_warrens = []
        if len(general) == 9:
            if general[3] == 'None':
                general[3] = 'burrow1'
            elif general[4] == 'None':
                general[4] = 0
            elif general[7] == 'None':
                general[7] = 'classic'
            elif general[8] == 'None':
                general[8] = 50
            game.warren = Warren(general[0],
                             Rabbit.all_rabbits[chief_rabbitinfo[0]],
                             Rabbit.all_rabbits.get(captain_info[0], None),
                             Rabbit.all_rabbits.get(healer_info[0], None),
                             biome=general[2],
                             burrow_bg=general[3],
                             game_mode=general[7])
            game.warren.reputation = general[8]
        elif len(general) == 8:
            if general[3] == 'None':
                general[3] = 'burrow1'
            elif general[4] == 'None':
                general[4] = 0
            elif general[7] == 'None':
                general[7] = 'classic'
            game.warren = Warren(
                general[0],
                Rabbit.all_rabbits[chief_rabbitinfo[0]],
                Rabbit.all_rabbits.get(captain_info[0], None),
                Rabbit.all_rabbits.get(healer_info[0], None),
                biome=general[2],
                burrow_bg=general[3],
                game_mode=general[7],
            )
        elif len(general) == 7:
            if general[4] == 'None':
                general[4] = 0
            elif general[3] == 'None':
                general[3] = 'burrow1'
            game.warren = Warren(
                general[0],
                Rabbit.all_rabbits[chief_rabbitinfo[0]],
                Rabbit.all_rabbits.get(captain_info[0], None),
                Rabbit.all_rabbits.get(healer_info[0], None),
                biome=general[2],
                burrow_bg=general[3],
            )
        elif len(general) == 3:
            game.warren = Warren(general[0], Rabbit.all_rabbits[chief_rabbitinfo[0]],
                             Rabbit.all_rabbits.get(captain_info[0], None),
                             Rabbit.all_rabbits.get(healer_info[0], None),
                             general[2])
        else:
            game.warren = Warren(general[0], Rabbit.all_rabbits[chief_rabbitinfo[0]],
                             Rabbit.all_rabbits.get(captain_info[0], None),
                             Rabbit.all_rabbits.get(healer_info[0], None))
        game.warren.age = int(general[1])
        if not game.config['lock_season']:
            game.warren.current_season = game.warren.seasons[game.warren.age % 12]
        else:
            game.warren.current_season = game.warren.starting_season
        game.warren.chief_rabbit_predecessors = int(
            int(chief_rabbitinfo[2]))

        if len(captain_info) > 1:
            game.warren.captain_predecessors = int(captain_info[1])
        if len(healer_info) > 1:
            game.warren.healer_predecessors = int(healer_info[1])
        if len(healer_info) > 2:
            game.warren.healer_number = int(healer_info[2])
        if len(sections) > 4:
            if instructor_info in Rabbit.all_rabbits:
                game.warren.instructor = Rabbit.all_rabbits[instructor_info]
                game.warren.add_rabbit(game.warren.instructor)
        else:
            game.warren.instructor = Rabbit(
                status=choice(["rabbit", "rabbit", "elder"]))
            # update_sprite(game.warren.instructor)
            game.warren.instructor.dead = True
            game.warren.add_rabbit(game.warren.instructor)
        if other_warrens != [""]:
            for other_warren in other_warrens:
                other_warren_info = other_warren.split(';')
                self.all_warrens.append(
                    OtherWarren(other_warren_info[0], int(other_warren_info[1]),
                              other_warren_info[2]))

        else:
            number_other_warrens = randint(3, 5)
            for _ in range(number_other_warrens):
                self.all_warrens.append(OtherWarren())

        for rabbit in members:
            if rabbit in Rabbit.all_rabbits:
                game.warren.add_rabbit(Rabbit.all_rabbits[rabbit])
                game.warren.add_to_inle(Rabbit.all_rabbits[rabbit])
            else:
                print('WARNING: Rabbit not found:', rabbit)
        self.load_pregnancy(game.warren)
        game.switches['error_message'] = ''

    def load_warren_json(self):
        """
        TODO: DOCS
        """
        other_warrens = []
        if game.switches['warren_list'] == '':
            number_other_warrens = randint(3, 5)
            for _ in range(number_other_warrens):
                self.all_warrens.append(OtherWarren())
            return
        if game.switches['warren_list'][0].strip() == '':
            number_other_warrens = randint(3, 5)
            for _ in range(number_other_warrens):
                self.all_warrens.append(OtherWarren())
            return

        game.switches[
            'error_message'] = "There was an error loading the warren.json"
        with open(get_save_dir() + '/' + game.switches['warren_list'][0] + 'warren.json',
                  'r',
                  encoding='utf-8') as read_file:  # pylint: disable=redefined-outer-name
            warren_data = ujson.loads(read_file.read())

        if warren_data["chief_rabbit"]:
            chief_rabbit = Rabbit.all_rabbits[warren_data["chief_rabbit"]]

        else:
            chief_rabbit = None


        if warren_data["captain"]:
            captain = Rabbit.all_rabbits[warren_data["captain"]]
        else:
            captain = None

        if warren_data["healer"]:
            healer = Rabbit.all_rabbits[warren_data["healer"]]
        else:
            healer = None

        game.warren = Warren(warren_data["warrenname"],
                         chief_rabbit,
                         captain,
                         healer,
                         biome=warren_data["biome"],
                         burrow_bg=warren_data["burrow_bg"],
                         game_mode=warren_data["gamemode"])

        game.warren.reputation = int(warren_data["reputation"])

        game.warren.age = warren_data["warrenage"]
        game.warren.starting_season = warren_data[
            "starting_season"] if "starting_season" in warren_data else 'Spring'
        get_current_season()


        game.warren.chief_rabbit_predecessors = warren_data["chief_rabbit_predecessors"]

        game.warren.captain_predecessors = warren_data["captain_predecessors"]
        game.warren.healer_predecessors = warren_data["healer_predecessors"]
        game.warren.healer_number = warren_data["healer_number"]

        # Instructor Info
        if warren_data["instructor"] in Rabbit.all_rabbits:
            game.warren.instructor = Rabbit.all_rabbits[warren_data["instructor"]]
            game.warren.add_rabbit(game.warren.instructor)
        else:
            game.warren.instructor = Rabbit(
                status=choice(["rabbit", "rabbit", "elder"]))
            # update_sprite(game.warren.instructor)
            game.warren.instructor.dead = True
            game.warren.add_rabbit(game.warren.instructor)

        for name, relation, temper in zip(
                warren_data["other_warrens_names"].split(","),
                warren_data["other_warrens_relations"].split(","),
                warren_data["other_warren_temperament"].split(",")):
            game.warren.all_warrens.append(OtherWarren(name, int(relation), temper))

        for rabbit in warren_data["warren_rabbits"].split(","):
            if rabbit in Rabbit.all_rabbits:
                game.warren.add_rabbit(Rabbit.all_rabbits[rabbit])
                game.warren.add_to_inle(Rabbit.all_rabbits[rabbit])
                game.warren.add_to_darkforest(Rabbit.all_rabbits[rabbit])
                game.warren.add_to_unknown(Rabbit.all_rabbits[rabbit])
            else:
                print('WARNING: Rabbit not found:', rabbit)
        if "war" in warren_data:
            game.warren.war = warren_data["war"]

        if "faded_rabbits" in warren_data:
            if warren_data["faded_rabbits"].strip():  # Check for empty string
                for rabbit in warren_data["faded_rabbits"].split(","):
                    game.warren.faded_ids.append(rabbit)

        # Patrolled rabbits
        if "patrolled_rabbits" in warren_data:
            game.patrolled = warren_data["patrolled_rabbits"]

        # Mediated flag
        if "mediated" in warren_data:
            if not isinstance(warren_data["mediated"], list):
                game.mediated = []
            else:
                game.mediated = warren_data["mediated"]

        self.load_pregnancy(game.warren)
        self.load_herbs(game.warren)
        self.load_disaster(game.warren)
        if game.warren.game_mode != "classic":
            self.load_freshkill_pile(game.warren)
        game.switches['error_message'] = ''

        # Return Version Info. 
        return {
            "version_name": warren_data.get("version_name"),
            "version_commit": warren_data.get("version_commit"),
            "source_build": warren_data.get("source_build")
        }

    def load_warren_settings(self):
        if os.path.exists(get_save_dir() + f'/{game.switches["warren_list"][0]}/warren_settings.json'):
            with open(get_save_dir() + f'/{game.switches["warren_list"][0]}/warren_settings.json', 'r',
                      encoding='utf-8') as write_file:
                _load_settings = ujson.loads(write_file.read())
                
        for key, value in _load_settings.items():
            if key in self.warren_settings:
                self.warren_settings[key] = value

    def load_herbs(self, warren):
        """
        TODO: DOCS
        """
        if not game.warren.name:
            return
        file_path = get_save_dir() + f"/{game.warren.name}/herbs.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as read_file:  # pylint: disable=redefined-outer-name
                warren.herbs = ujson.loads(read_file.read())

        else:
            # generate a random set of herbs since the Warren didn't have any saved
            herbs = {}
            random_herbs = random.choices(HERBS, k=random.randrange(3, 8))
            for herb in random_herbs:
                herbs.update({herb: random.randint(1, 3)})
            with open(file_path, 'w', encoding='utf-8') as rel_file:
                json_string = ujson.dumps(herbs, indent=4)
                rel_file.write(json_string)
            warren.herbs = herbs

    def save_herbs(self, warren):
        """
        TODO: DOCS
        """
        if not game.warren.name:
            return

        game.safe_save(f"{get_save_dir()}/{game.warren.name}/herbs.json", warren.herbs)

    def load_pregnancy(self, warren):
        """
        Load the information about what rabbit is pregnant and in what 'state' they are in the pregnancy.
        """
        if not game.warren.name:
            return
        file_path = get_save_dir() + f"/{game.warren.name}/pregnancy.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as read_file:  # pylint: disable=redefined-outer-name
                warren.pregnancy_data = ujson.load(read_file)
        else:
            warren.pregnancy_data = {}

    def save_pregnancy(self, warren):
        """
        Save the information about what rabbit is pregnant and in what 'state' they are in the pregnancy.
        """
        if not game.warren.name:
            return

        game.safe_save(f"{get_save_dir()}/{game.warren.name}/pregnancy.json", warren.pregnancy_data)

    def load_disaster(self, warren):
        """
        TODO: DOCS
        """
        if not game.warren.name:
            return

        file_path = get_save_dir() + f"/{game.warren.name}/disasters/primary.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as read_file:  # pylint: disable=redefined-outer-name
                    disaster = ujson.load(read_file)
                    if disaster:
                        warren.primary_disaster = OngoingEvent(
                            event=disaster["event"],
                            tags=disaster["tags"],
                            duration=disaster["duration"],
                            current_duration=disaster["current_duration"]
                            if "current_duration" else disaster["duration"],  # pylint: disable=using-constant-test
                            trigger_events=disaster["trigger_events"],
                            progress_events=disaster["progress_events"],
                            conclusion_events=disaster["conclusion_events"],
                            secondary_disasters=disaster[
                                "secondary_disasters"],
                            collateral_damage=disaster["collateral_damage"])
                    else:
                        warren.primary_disaster = {}
            else:
                os.makedirs(get_save_dir() + f"/{game.warren.name}/disasters")
                warren.primary_disaster = None
                with open(file_path, 'w', encoding='utf-8') as rel_file:
                    json_string = ujson.dumps(warren.primary_disaster, indent=4)
                    rel_file.write(json_string)
        except:
            warren.primary_disaster = None

        file_path = get_save_dir() + f"/{game.warren.name}/disasters/secondary.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as read_file:
                    disaster = ujson.load(read_file)
                    if disaster:
                        warren.secondary_disaster = OngoingEvent(
                            event=disaster["event"],
                            tags=disaster["tags"],
                            duration=disaster["duration"],
                            current_duration=disaster["current_duration"]
                            if "current_duration" else disaster["duration"],  # pylint: disable=using-constant-test
                            progress_events=disaster["progress_events"],
                            conclusion_events=disaster["conclusion_events"],
                            collateral_damage=disaster["collateral_damage"])
                    else:
                        warren.secondary_disaster = {}
            else:
                os.makedirs(get_save_dir() + f"/{game.warren.name}/disasters")
                warren.secondary_disaster = None
                with open(file_path, 'w', encoding='utf-8') as rel_file:
                    json_string = ujson.dumps(warren.secondary_disaster,
                                              indent=4)
                    rel_file.write(json_string)

        except:
            warren.secondary_disaster = None

    def save_disaster(self, warren=game.warren):
        """
        TODO: DOCS
        """
        if not warren.name:
            return
        file_path = get_save_dir() + f"/{warren.name}/disasters/primary.json"
        if not os.path.isdir(f'{get_save_dir()}/{warren.name}/disasters'):
            os.mkdir(f'{get_save_dir()}/{warren.name}/disasters')
        if warren.primary_disaster:
            disaster = {
                "event": warren.primary_disaster.event,
                "tags": warren.primary_disaster.tags,
                "duration": warren.primary_disaster.duration,
                "current_duration": warren.primary_disaster.current_duration,
                "trigger_events": warren.primary_disaster.trigger_events,
                "progress_events": warren.primary_disaster.progress_events,
                "conclusion_events": warren.primary_disaster.conclusion_events,
                "secondary_disasters":
                    warren.primary_disaster.secondary_disasters,
                "collateral_damage": warren.primary_disaster.collateral_damage
            }
        else:
            disaster = {}

        game.safe_save(f"{get_save_dir()}/{warren.name}/disasters/primary.json", disaster)

        if warren.secondary_disaster:
            disaster = {
                "event": warren.secondary_disaster.event,
                "tags": warren.secondary_disaster.tags,
                "duration": warren.secondary_disaster.duration,
                "current_duration": warren.secondary_disaster.current_duration,
                "trigger_events": warren.secondary_disaster.trigger_events,
                "progress_events": warren.secondary_disaster.progress_events,
                "conclusion_events": warren.secondary_disaster.conclusion_events,
                "secondary_disasters":
                    warren.secondary_disaster.secondary_disasters,
                "collateral_damage": warren.secondary_disaster.collateral_damage
            }
        else:
            disaster = {}

        game.safe_save(f"{get_save_dir()}/{warren.name}/disasters/secondary.json", disaster)

    def load_freshkill_pile(self, warren):
        """
        TODO: DOCS
        """
        if not game.warren.name or warren.game_mode == 'classic':
            return

        file_path = get_save_dir() + f"/{game.warren.name}/freshkill_pile.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as read_file:  # pylint: disable=redefined-outer-name
                    pile = ujson.load(read_file)
                    warren.freshkill_pile = Freshkill_Pile(pile)

                file_path = get_save_dir() + f"/{game.warren.name}/nutrition_info.json"
                if os.path.exists(file_path) and warren.freshkill_pile:
                    with open(file_path, 'r', encoding='utf-8') as read_file:
                        nutritions = ujson.load(read_file)
                        for k, nutr in nutritions.items():
                            nutrition = Nutrition()
                            nutrition.max_score = nutr['max_score']
                            nutrition.current_score = nutr['current_score']
                            warren.freshkill_pile.nutrition_info[k] = nutrition
                        if len(nutritions) <= 0:
                            for rabbit in Rabbit.all_rabbits_list:
                                warren.freshkill_pile.add_rabbit_to_nutrition(rabbit)
            else:
                warren.freshkill_pile = Freshkill_Pile()
        except:
            warren.freshkill_pile = Freshkill_Pile()

    def save_freshkill_pile(self, warren):
        """
        TODO: DOCS
        """
        if warren.game_mode == "classic" or not warren.freshkill_pile:
            return

        game.safe_save(f"{get_save_dir()}/{game.warren.name}/freshkill_pile.json", warren.freshkill_pile.pile)

        data = {}
        for k, nutr in warren.freshkill_pile.nutrition_info.items():
            data[k] = {
                "max_score": nutr.max_score,
                "current_score": nutr.current_score,
                "percentage": nutr.percentage,
            }

        game.safe_save(f"{get_save_dir()}/{game.warren.name}/nutrition_info.json", data)

    ## Properties

    @property
    def reputation(self):
        return self._reputation

    @reputation.setter
    def reputation(self, a: int):
        self._reputation = int(a)
        if self._reputation > 100:
            self._reputation = 100
        elif self._reputation < 0:
            self._reputation = 0
            
    @property
    def temperament(self):
        """Temperment is determined whenever it's accessed. This makes sure it's always accurate to the 
            current rabbits in the Warren. However, determining Warren temperment is slow! 
            Warren temperment should be used as sparcely as possible, since
            it's pretty resource-intensive to determine it. """
        
        all_rabbits = [i for i in Rabbit.all_rabbits_list if 
                    i.status not in ["chief rabbit ", "captain"] and
                    not i.dead and 
                    not i.outside]
        chief_rabbit = Rabbit.fetch_rabbit(self.chief_rabbit) if isinstance(Rabbit.fetch_rabbit(self.chief_rabbit), Rabbit) else None 
        captain = Rabbit.fetch_rabbit(self.captain) if isinstance(Rabbit.fetch_rabbit(self.captain), Rabbit) else None
        
        weight = 0.3

        if (chief_rabbit or captain) and all_rabbits:
            warren_sociability = round(weight * statistics.mean([i.personality.sociability for i in [chief_rabbit, captain] if i]) + \
                (1-weight) *  statistics.median([i.personality.sociability for i in all_rabbits]))
            warren_aggression = round(weight * statistics.mean([i.personality.aggression for i in [chief_rabbit, captain] if i]) + \
                (1-weight) *  statistics.median([i.personality.aggression for i in all_rabbits]))
        elif (chief_rabbit or captain):
            warren_sociability = round(statistics.mean([i.personality.sociability for i in [chief_rabbit, captain] if i]))
            warren_aggression = round(statistics.mean([i.personality.aggression for i in [chief_rabbit, captain] if i]))
        elif all_rabbits:
            warren_sociability = round(statistics.median([i.personality.sociability for i in all_rabbits]))
            warren_aggression = round(statistics.median([i.personality.aggression for i in all_rabbits]))
        else:
            return "stoic"
        
        # temperment = ['high_agress', 'med_agress', 'low agress' ]
        if 12 <= warren_sociability:
            _temperament = ['gracious', 'mellow', 'logical']
        elif 5 <= warren_sociability:
            _temperament = ['amiable', 'stoic', 'wary']
        else:
            _temperament = ['cunning', 'proud', 'bloodthirsty']
            
        if 12 <= warren_aggression:
            _temperament = _temperament[2]
        elif 5 <= warren_aggression:
            _temperament = _temperament[1] 
        else:
            _temperament = _temperament[0] 
        
        return _temperament
    
    @temperament.setter
    def temperament(self, val):
        #print("Warren temperment set by member personality --> you can not set it externally.", val)
        return
            


class OtherWarren():
    """
    TODO: DOCS
    """

    def __init__(self, name='', relations=0, temperament=''):
        temperament_list = [
            'cunning', 'wary', 'logical', 'proud', 'stoic', 'mellow',
            'bloodthirsty', 'amiable', 'gracious'
        ]
        self.name = name or choice(names.names_dict["normal_prefixes"])
        self.relations = relations or randint(8, 12)
        self.temperament = temperament or choice(temperament_list)
        if self.temperament not in temperament_list:
            self.temperament = choice(temperament_list)

    def __repr__(self):
        return f"{self.name}Warren"


class Inle():
    """
    TODO: DOCS
    """
    forgotten_stages = {
        0: [0, 100],
        10: [101, 200],
        30: [201, 300],
        60: [301, 400],
        90: [401, 500],
        100: [501, 502]
    }  # Tells how faded the rabbit will be in Inle by months spent
    dead_rabbits = {}

    def __init__(self):
        """
        TODO: DOCS
        """
        self.instructor = None

    def fade(self, rabbit):
        """
        TODO: DOCS
        """
        white = pygame.Surface((sprites.size, sprites.size))
        fade_level = 0
        if rabbit.dead:
            for f in self.forgotten_stages:  # pylint: disable=consider-using-dict-items
                if rabbit.dead_for in range(self.forgotten_stages[f][0],
                                         self.forgotten_stages[f][1]):
                    fade_level = f
        white.fill((255, 255, 255, fade_level))
        return white


warren_class = Warren()
warren_class.remove_rabbit(rabbit_class.ID)

HERBS = None
with open("resources/dicts/herbs.json", 'r', encoding='utf-8') as read_file:
    HERBS = ujson.loads(read_file.read())
