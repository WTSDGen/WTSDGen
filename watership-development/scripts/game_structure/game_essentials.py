import pygame
import pygame_gui

from scripts.housekeeping.datadir import get_save_dir, get_temp_dir

import ujson
import os
from shutil import move as shutil_move
from ast import literal_eval
from scripts.event_class import Single_Event

pygame.init()


# G A M E
class Game():
    max_name_length = 10
    # max_events_displayed = 10
    # event_scroll_ct = 0
    # max_allegiance_displayed = 17
    # allegiance_scroll_ct = 0
    # max_relation_events_displayed = 10
    # relation_scroll_ct = 0

    mediated = []  # Keep track of which couples have been mediated this month.
    just_died = []  # keeps track of which rabbits died this month via die()

    cur_events_list = []
    ceremony_events_list = []
    birth_death_events_list = []
    relation_events_list = []
    health_events_list = []
    other_warrens_events_list = []
    misc_events_list = []
    herb_events_list = []
    freshkill_event_list = []

    allegiance_list = []
    language = {}
    game_mode = ''
    language_list = ['english', 'spanish', 'german']
    game_mode_list = ['classic', 'expanded', 'cruel season']

    rabbit_to_fade = []
    sub_tab_list = ['life events', 'user notes']

    # Keeping track of various last screen for various purposes
    last_screen_forupdate = 'start screen'
    last_screen_forProfile = 'list screen'

    # down = pygame.image.load("resources/images/buttons/arrow_down.png").convert_alpha()
    # up = pygame.image.load("resources/images/buttons/arrow_up.png").convert_alpha()

    # Sort-type
    sort_type = "rank"

    choose_rabbits = {}
    '''rabbit_buttons = {
        'rabbit0': None,
        'rabbit1': None,
        'rabbit2': None,
        'rabbit3': None,
        'rabbit4': None,
        'rabbit5': None,
        'rabbit6': None,
        'rabbit7': None,
        'rabbit8': None,
        'rabbit9': None,
        'rabbit10': None,
        'rabbit11': None
    }'''
    patrol_rabbits = {}
    patrolled = []

    # store changing parts of the game that the user can toggle with buttons
    switches = {
        'rabbit': None,
        'warren_name': '',
        'chief rabbit': None,
        'captain': None,
        'healer': None,
        'members': [],
        're_roll': False,
        'roll_count': 0,
        'event': None,
        'cur_screen': 'start screen',
        'naming_text': '',
        'timeskip': False,
        'mate': None,
        'choosing_mate': False,
        'rusasirah': None,
        'setting': None,
        'save_settings': False,
        'list_page': 1,
        'last_screen': 'start screen',
        'events_left': 0,
        'save_warren': False,
        'saved_warren': False,
        'new_chief_rabbit': False,
        'rusasi_switch': False,
        'captain_switch': False,
        'warren_list': '',
        'switch_warren': False,
        'read_warrens': False,
        'kill_rabbit': False,
        'current_patrol': [],
        'patrol_remove': False,
        'rabbit_remove': False,
        'fill_patrol': False,
        'patrol_done': False,
        'error_message': '',
        'traceback': '',
        'rusasi': None,
        'change_name': '',
        'change_suffix': '',
        'name_rabbit': None,
        'biome': None,
        'burrow_bg': None,
        'language': 'english',
        'options_tab': None,
        'profile_tab_group': None,
        'sub_tab_group': None,
        'gender_align': None,
        'show_details': False,
        'chosen_rabbit': None,
        'game_mode': '',
        'set_game_mode': False,
        'broke_up': False,
        'show_info': False,
        'patrol_chosen': 'general',
        'favorite_sub_tab': None,
        'root_rabbit': None,
        'window_open': False,
        'skip_conditions': [],
        'show_history_months': False,
        'fps': 30
    }
    all_screens = {}
    cur_events = {}
    map_info = {}

    # SETTINGS
    settings = {}
    settings['mns open'] = False
    setting_lists = {}

    debug_settings = {
        "showcoords": False,
        "showbounds": False,
        "visualdebugmode": False,
        "showfps": False
    }

    # Init Settings
    with open("resources/gamesettings.json", 'r') as read_file:
        _settings = ujson.loads(read_file.read())

    for setting, values in _settings['__other'].items():
        settings[setting] = values[0]
        setting_lists[setting] = values

    _ = []
    _.append(_settings['general'])

    for rabbit in _:  # Add all the settings to the settings dictionary
        for setting_name, inf in rabbit.items():
            settings[setting_name] = inf[2]
            setting_lists[setting_name] = [inf[2], not inf[2]]
    del _settings
    del _
    #End init settings

    settings_changed = False

    # CLAN
    warren = None
    rabbit_class = None
    config = {}
    prey_config = {}

    rpc = None

    is_close_menu_open = False

    def __init__(self, current_screen='start screen'):
        self.current_screen = current_screen
        self.clicked = False
        self.keyspressed = []
        self.switch_screens = False

        with open(f"resources/game_config.json", 'r') as read_file:
            self.config = ujson.loads(read_file.read())

        with open(f"resources/prey_config.json", 'r') as read_file:
            self.prey_config = ujson.loads(read_file.read())

        if self.config['fun']['april_fools']:
            self.config['fun']['newborns_can_roam'] = True
            self.config['fun']['newborns_can_patrol'] = True

    def update_game(self):
        if self.current_screen != self.switches['cur_screen']:
            self.current_screen = self.switches['cur_screen']
            self.switch_screens = True
        self.clicked = False
        self.keyspressed = []

    @staticmethod
    def safe_save(path: str, write_data, check_integrity=False, max_attempts: int = 15):
        """ If write_data is not a string, assumes you want this
            in json format. If check_integrity is true, it will read back the file
            to check that the correct data has been written to the file. 
            If not, it will simply write the data to the file with no other
            checks. """

        # If write_data is not a string,
        if type(write_data) is not str:
            _data = ujson.dumps(write_data, indent=4)
        else:
            _data = write_data

        dir_name, file_name = os.path.split(path)

        if check_integrity:
            if not file_name:
                raise RuntimeError(
                    f"Safe_Save: No file name was found in {path}")

            temp_file_path = get_temp_dir() + "/" + file_name + ".tmp"
            i = 0
            while True:
                # Attempt to write to temp file
                with open(temp_file_path, "w") as write_file:
                    write_file.write(_data)
                    write_file.flush()
                    os.fsync(write_file.fileno())

                # Read the entire file back in
                with open(temp_file_path, 'r') as read_file:
                    _read_data = read_file.read()

                if _data != _read_data:
                    i += 1
                    if i > max_attempts:
                        print(
                            f"Safe_Save ERROR: {file_name} was unable to properly save {i} times. Saving Failed.")
                        raise RuntimeError(
                            f"Safe_Save: {file_name} was unable to properly save {i} times!")
                    print(
                        f"Safe_Save: {file_name} was incorrectly saved. Trying again.")
                    continue

                # This section is reached is the file was not nullied. Move the file and return True

                shutil_move(temp_file_path, path)
                return
        else:
            os.makedirs(dir_name, exist_ok=True)
            with open(path, 'w') as write_file:
                write_file.write(_data)
                write_file.flush()
                os.fsync(write_file.fileno())

    def read_warrens(self):
        '''with open(get_save_dir() + '/warrenlist.txt', 'r') as read_file:
            warren_list = read_file.read()
            if_warrens = len(warren_list)
        if if_warrens > 0:
            warren_list = warren_list.split('\n')
            warren_list = [i.strip() for i in warren_list if i]  # Remove empty and whitespace
            return warren_list
        else:
            return None'''
        # All of the above is old code
        # Now, we want warrenlist.txt to contain ONLY the name of the Warren that is currently loaded
        # We will get the list of warrens from the saves folder
        # each Warren has its own folder, and the name of the folder is the name of the warren
        # so we can just get a list of all the folders in the saves folder

        # First, we need to make sure the saves folder exists
        if not os.path.exists(get_save_dir()):
            os.makedirs(get_save_dir())
            print('Created saves folder')
            return None

        # Now we can get a list of all the folders in the saves folder
        warren_list = [f.name for f in os.scandir(get_save_dir()) if f.is_dir()]

        # the Warren specified in saves/warrenlist.txt should be first in the list
        # so we can load it automatically

        if os.path.exists(get_save_dir() + '/warrenlist.txt'):
            with open(get_save_dir() + '/warrenlist.txt', 'r') as f:
                loaded_warren = f.read().strip().splitlines()
                if loaded_warren:
                    loaded_warren = loaded_warren[0]
                else:
                    loaded_warren = None
            os.remove(get_save_dir() + '/warrenlist.txt')
            if loaded_warren:
                self.safe_save(get_save_dir() +
                               '/currentwarren.txt', loaded_warren)
        elif os.path.exists(get_save_dir() + '/currentwarren.txt'):
            with open(get_save_dir() + '/currentwarren.txt', 'r') as f:
                loaded_warren = f.read().strip()
        else:
            loaded_warren = None

        if loaded_warren and loaded_warren in warren_list:
            warren_list.remove(loaded_warren)
            warren_list.insert(0, loaded_warren)

        # Now we can return the list of warrens
        if not warren_list:
            print('No warrens found')
            return None
        # print('Warrens found:', warren_list)
        return warren_list

    def save_warrenlist(self, loaded_warren=None):
        '''warrens = []
        if loaded_warren:
            warrens.append(f"{loaded_warren}\n")

        for warren_name in self.switches['warren_list']:
            if warren_name and warren_name != loaded_warren:
                warrens.append(f"{warren_name}\n")

        if warrens:
            with open(get_save_dir() + '/warrenlist.txt', 'w') as f:
                f.writelines(warrens)'''
        if loaded_warren:
            if os.path.exists(get_save_dir() + '/warrenlist.txt'):
                # we don't need warrenlist.txt anymore
                os.remove(get_save_dir() + '/warrenlist.txt')
            game.safe_save(f"{get_save_dir()}/currentwarren.txt", loaded_warren)
        else:
            if os.path.exists(get_save_dir() + '/currentwarren.txt'):
                os.remove(get_save_dir() + '/currentwarren.txt')

    def save_settings(self):
        """ Save user settings for later use """
        if os.path.exists(get_save_dir() + "/settings.txt"):
            os.remove(get_save_dir() + "/settings.txt")
        
        self.settings_changed = False
        game.safe_save(get_save_dir() + '/settings.json', self.settings)

    def load_settings(self):
        """ Load settings that user has saved from previous use """
        
        try:
            with open(get_save_dir() + '/settings.json', 'r') as read_file:
                settings_data = ujson.loads(read_file.read())
        except FileNotFoundError:
            return

        for key, value in settings_data.items():
            if key in self.settings:
                self.settings[key] = value

        self.switches['language'] = self.settings['language']
        if self.settings['language'] != 'english':
            self.switch_language()

    def switch_language(self):
        # add translation information here
        if os.path.exists('languages/' + game.settings['language'] + '.txt'):
            with open('languages/' + game.settings['language'] + '.txt',
                      'r') as read_file:
                raw_language = read_file.read()
            game.language = literal_eval(raw_language)

    def switch_setting(self, setting_name):
        """ Call this function to change a setting given in the parameter by one to the right on it's list """
        self.settings_changed = True

        # Give the index that the list is currently at
        list_index = self.setting_lists[setting_name].index(
            self.settings[setting_name])

        if list_index == len(
                self.setting_lists[setting_name]
        ) - 1:  # The option is at the list's end, go back to 0
            self.settings[setting_name] = self.setting_lists[setting_name][0]
        else:
            # Else move on to the next item on the list
            self.settings[setting_name] = self.setting_lists[setting_name][
                list_index + 1]

    def save_rabbits(self):
        """Save the rabbit data."""

        warrenname = ''
        ''' if game.switches['warren_name'] != '':
            warrenname = game.switches['warren_name']
        elif len(game.switches['warren_name']) > 0:
            warrenname = game.switches['warren_list'][0]'''
        if game.warren is not None:
            warrenname = game.warren.name
        directory = get_save_dir() + '/' + warrenname
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Delete all existing relationship files
        if not os.path.exists(directory + '/relationships'):
            os.makedirs(directory + '/relationships')
        for f in os.listdir(directory + '/relationships'):
            os.remove(os.path.join(directory + '/relationships', f))

        self.save_faded_rabbits(warrenname)  # Fades rabbit and saves them, if needed

        warren_rabbits = []
        for inter_rabbit in self.rabbit_class.all_rabbits.values():
            rabbit_data = inter_rabbit.get_save_dict()
            warren_rabbits.append(rabbit_data)

            # Don't save conditions for classic condition. This
            # should allow closing and reloading to clear conditions on
            # classic, just in case a condition is accidently applied.
            if game.game_mode != "classic":
                inter_rabbit.save_condition()

            if inter_rabbit.history:
                inter_rabbit.save_history(directory + '/history')
                # after saving, dump the history info
                inter_rabbit.history = None
            if not inter_rabbit.dead:
                inter_rabbit.save_relationship_of_rabbit(
                    directory + '/relationships')

        self.safe_save(
            f"{get_save_dir()}/{warrenname}/warren_rabbits.json", warren_rabbits)

    def save_faded_rabbits(self, warrenname):
        """Deals with fades rabbits, if needed, adding them as faded """
        if game.rabbit_to_fade:
            directory = get_save_dir() + '/' + warrenname + "/faded_rabbits"
            if not os.path.exists(directory):
                os.makedirs(directory)

        copy_of_info = ""
        for rabbit in game.rabbit_to_fade:

            inter_rabbit = self.rabbit_class.all_rabbits[rabbit]

            # Add ID to list of faded rabbits.
            self.warren.faded_ids.append(rabbit)

            # If they have a mate, break it up
            if inter_rabbit.mate:
                for mate_id in inter_rabbit.mate:
                    if mate_id in self.rabbit_class.all_rabbits:
                        self.rabbit_class.all_rabbits[mate_id].unset_mate(inter_rabbit)

            # If they have parents, add them to their parents "faded offspring" list:
            for x in inter_rabbit.get_parents():
                if x in self.rabbit_class.all_rabbits:
                    self.rabbit_class.all_rabbits[x].faded_offspring.append(rabbit)
                else:
                    parent_faded = self.add_faded_offspring_to_faded_rabbit(
                        x, rabbit)
                    if not parent_faded:
                        print(f"WARNING: Can't find parent {x} of {rabbit.name}")

            # Get a copy of info
            if game.warren.warren_settings["save_faded_copy"]:
                copy_of_info += ujson.dumps(inter_rabbit.get_save_dict(), indent=4) + \
                    "\n--------------------------------------------------------------------------\n"

            # SAVE TO IT'S OWN LITTLE FILE. This is a trimmed-down version for relation keeping only.
            rabbit_data = inter_rabbit.get_save_dict(faded=True)

            self.safe_save(
                f"{get_save_dir()}/{warrenname}/faded_rabbits/{rabbit}.json", rabbit_data)

            # Remove the rabbit from the active rabbits lists
            self.warren.remove_rabbit(rabbit)

        game.rabbit_to_fade = []

        # Save the copies, flush the file.
        if game.warren.warren_settings["save_faded_copy"]:
            with open(get_save_dir() + '/' + warrenname + '/faded_rabbits_info_copy.txt', 'a') as write_file:

                if not os.path.exists(get_save_dir() + '/' + warrenname + '/faded_rabbits_info_copy.txt'):
                    # Create the file if it doesn't exist
                    with open(get_save_dir() + '/' + warrenname + '/faded_rabbits_info_copy.txt', 'w') as create_file:
                        pass

                with open(get_save_dir() + '/' + warrenname + '/faded_rabbits_info_copy.txt', 'a') as write_file:
                    write_file.write(copy_of_info)

                    write_file.flush()
                    os.fsync(write_file.fileno())

    def save_events(self):
        """
        Save current events list to events.json
        """
        events_list = []
        for event in game.cur_events_list:
            events_list.append(event.to_dict())
        game.safe_save(
            f"{get_save_dir()}/{game.warren.name}/events.json", events_list)

    def add_faded_offspring_to_faded_rabbit(self, parent, offspring):
        """In order to siblings to work correctly, and not to lose relation info on fading, we have to keep track of
        both active and faded rabbit's faded offpsring. This will add a faded offspring to a faded parents file. """
        try:
            with open(get_save_dir() + '/' + self.warren.name + '/faded_rabbits/' + parent + ".json", 'r') as read_file:
                rabbit_info = ujson.loads(read_file.read())
        except:
            print("ERROR: loading faded rabbit")
            return False

        rabbit_info["faded_offspring"].append(offspring)

        self.safe_save(
            f"{get_save_dir()}/{self.warren.name}/faded_rabbits/{parent}.json", rabbit_info)

        return True

    def load_events(self):
        """
        Load events from events.json and place into game.cur_events_list.
        """

        warrenname = self.warren.name
        events_path = f'{get_save_dir()}/{warrenname}/events.json'
        events_list = []
        try:
            with open(events_path, 'r') as f:
                events_list = ujson.loads(f.read())
            for event_dict in events_list:
                event_obj = Single_Event.from_dict(event_dict)
                if event_obj:
                    game.cur_events_list.append(event_obj)
        except FileNotFoundError:
            pass

    def get_config_value(self, *args):
        """Fetches a value from the self.config dictionary. Pass each key as a 
        seperate arugment, in the same order you would access the dictionary. 
        This function will apply war modifers if the warren is currently at war. """

        war_effected = {
            ("death_related", "chief_rabbit_death_chance"): ("death_related", "war_death_modifier_chief_rabbit"),
            ("death_related", "classic_death_chance"): ("death_related", "war_death_modifier"),
            ("death_related", "expanded_death_chance"): ("death_related", "war_death_modifier"),
            ("death_related", "cruel season_death_chance"): ("death_related", "war_death_modifier"),
            ("condition_related", "classic_injury_chance"): ("condition_related", "war_injury_modifier"),
            ("condition_related", "expanded_injury_chance"): ("condition_related", "war_injury_modifier"),
            ("condition_related", "cruel season_injury_chance"): ("condition_related", "war_injury_modifier")
        }

        # Get Value
        config_value = self.config
        for key in args:
            config_value = config_value[key]

        # Apply war if needed
        if self.warren and self.warren.war.get("at_war", False) and args in war_effected:
            # Grabs the modifer
            mod = self.config
            for key in war_effected[args]:
                mod = mod[key]

            config_value -= mod

        return config_value


game = Game()

if not os.path.exists(get_save_dir() + '/settings.txt'):
    os.makedirs(get_save_dir(), exist_ok=True)
    with open(get_save_dir() + '/settings.txt', 'w') as write_file:
        write_file.write('')
game.load_settings()

pygame.display.set_caption('Watership')

if game.settings['fullscreen']:
    screen_x, screen_y = 1600, 1400
    screen = pygame.display.set_mode(
        (screen_x, screen_y), pygame.FULLSCREEN | pygame.SCALED)
else:
    screen_x, screen_y = 800, 700
    screen = pygame.display.set_mode((screen_x, screen_y))


def load_manager(res: tuple):
    # initialize pygame_gui manager, and load themes
    manager = pygame_gui.ui_manager.UIManager(
        res, 'resources/theme/defaults.json', enable_live_theme_updates=False)
    manager.add_font_paths(
        font_name='notosans',
        regular_path='resources/fonts/NotoSans-Medium.ttf',
        bold_path='resources/fonts/NotoSans-ExtraBold.ttf',
        italic_path='resources/fonts/NotoSans-MediumItalic.ttf',
        bold_italic_path='resources/fonts/NotoSans-ExtraBoldItalic.ttf'
    )
    

    if res[0] > 800:
        manager.get_theme().load_theme('resources/theme/defaults.json')
        manager.get_theme().load_theme('resources/theme/buttons.json')
        manager.get_theme().load_theme('resources/theme/text_boxes.json')
        manager.get_theme().load_theme('resources/theme/text_boxes_dark.json')
        manager.get_theme().load_theme('resources/theme/vertical_scroll_bar.json')
        manager.get_theme().load_theme('resources/theme/window_base.json')
        manager.get_theme().load_theme('resources/theme/tool_tips.json')

        manager.preload_fonts([
            {'name': 'notosans', 'point_size': 30, 'style': 'italic'},
            {'name': 'notosans', 'point_size': 26, 'style': 'italic'},
            {'name': 'notosans', 'point_size': 30, 'style': 'bold'},
            {'name': 'notosans', 'point_size': 26, 'style': 'bold'},
            {'name': 'notosans', 'point_size': 22, 'style': 'bold'},
        ])

    else:
        manager.get_theme().load_theme('resources/theme/defaults_small.json')
        manager.get_theme().load_theme('resources/theme/buttons_small.json')
        manager.get_theme().load_theme('resources/theme/text_boxes_small.json')
        manager.get_theme().load_theme('resources/theme/text_boxes_dark_small.json')
        manager.get_theme().load_theme('resources/theme/vertical_scroll_bar.json')
        manager.get_theme().load_theme('resources/theme/window_base_small.json')
        manager.get_theme().load_theme('resources/theme/tool_tips_small.json')

        manager.preload_fonts([
            {'name': 'notosans', 'point_size': 11, 'style': 'bold'},
            {'name': 'notosans', 'point_size': 13, 'style': 'bold'},
            {'name': 'notosans', 'point_size': 15, 'style': 'bold'},
            {'name': 'notosans', 'point_size': 13, 'style': 'italic'},
            {'name': 'notosans', 'point_size': 15, 'style': 'italic'}
        ])
        
    manager.get_theme().load_theme('resources/theme/windows.json')
    manager.get_theme().load_theme('resources/theme/image_buttons.json')

    return manager


MANAGER = load_manager((screen_x, screen_y))
