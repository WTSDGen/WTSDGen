import pygame
from random import choice, randrange
import pygame_gui

from .Screens import Screens

from scripts.utility import get_text_box_theme, scale
from scripts.warren import Warren
from scripts.rabbit.rabbits import create_example_rabbits, Rabbit
from scripts.rabbit.names import names
from re import sub
from scripts.game_structure import image_cache
from scripts.game_structure.image_button import UIImageButton, UISpriteButton
from scripts.game_structure.game_essentials import game, MANAGER
from scripts.patrol.patrol import Patrol


class MakeWarrenScreen(Screens):
    # UI images
    warren_name_frame_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/clan_name_frame.png').convert_alpha(), (432, 100))
    name_warren_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/name_warren_light.png').convert_alpha(), (1600, 1400))
    chief_rabbitimg = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/chief_rabbit_light.png').convert_alpha(), (1600, 1400))
    captain_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/captain_light.png').convert_alpha(), (1600, 1400))
    medic_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/med_light.png').convert_alpha(), (1600, 1400))
    warren_img = pygame.transform.scale(pygame.image.load(
        'resources/images/pick_clan_screen/warren_light.png').convert_alpha(), (1600, 1400))
    bg_preview_border = pygame.transform.scale(
        pygame.image.load("resources/images/bg_preview_border.png").convert_alpha(), (466, 416))

    classic_mode_text = "This mode is Watership at it's most basic. " \
                        "The player will not be expected to manage the minutia of warren life. <br><br>" \
                        "Perfect for a relaxing game session or for focusing on storytelling. <br><br>" \
                        "With this mode you are the eye in the sky, watching the warren as their story unfolds. "

    expanded_mode_text = "A more hands-on experience. " \
                         "This mode has everything in Classic Mode as well as more management-focused features.<br><br>" \
                         "New features include:<br>" \
                         "- Illnesses, Injuries, and Permanent Conditions<br>" \
                         "- Herb gathering and treatment<br>" \
                         "- Ability to choose patrol type<br><br>" \
                         "With this mode you'll be making the important warren-life decisions."

    cruel_mode_text = "This mode has all the features of Expanded mode, but is significantly more difficult. If " \
                      "you'd like a challenge with a bit of brutality, then this mode is for you.<br><br>" \
                      "You heard the warnings... a Cruel Season is coming. Will you survive?" \
                      "<br> <br>" \
                      "-COMING SOON-"

    # This section holds all the information needed
    game_mode = 'classic'  # To save the users selection before conformation.
    warren_name = ""  # To store the Warren name before conformation
    chief_rabbit = None  # To store the Warren chief rabbit before conformation
    captain = None
    med_rabbit = None
    members = []
    elected_burrow = None

    # Holds biome we have selected
    biome_selected = None
    selected_burrow_tab = 1
    selected_season = None
    # Camp number selected
    burrow_num = "1"
    # Holds the rabbit we have currently selected.
    selected_rabbit = None
    # Hold which sub-screen we are on
    sub_screen = 'game mode'
    # Holds which ranks we are currently selecting.
    choosing_rank = None
    # To hold the images for the sections. Makes it easier to kill them
    elements = {}
    tabs = {}

    def __init__(self, name=None):
        super().__init__(name)
        self.rolls_left = game.config["warren_creation"]["rerolls"]
        self.menu_warning = None

    def screen_switches(self):
        # Reset variables
        self.game_mode = 'classic'
        self.warren_name = ""
        self.selected_burrow_tab = 1
        self.biome_selected = None
        self.selected_season = "Spring"
        self.choosing_rank = None
        self.chief_rabbit = None  # To store the Warren chief rabbit before conformation
        self.captain = None
        self.med_rabbit = None
        self.members = []

        # Buttons that appear on every screen.
        self.menu_warning = pygame_gui.elements.UITextBox(
            'Note: going back to main menu resets the generated rabbits.',
            scale(pygame.Rect((50, 50), (1200, -1))),
            object_id=get_text_box_theme("#text_box_22_horizleft"), manager=MANAGER
        )
        self.main_menu = UIImageButton(scale(pygame.Rect((50, 100), (306, 60))), "", object_id="#main_menu_button"
                                       , manager=MANAGER)
        create_example_rabbits()
        # self.worldseed = randrange(10000)
        self.open_game_mode()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.main_menu:
                self.change_screen('start screen')
            if self.sub_screen == "game mode":
                self.handle_game_mode_event(event)
            elif self.sub_screen == 'name warren':
                self.handle_name_warren_event(event)
            elif self.sub_screen == 'choose chief rabbit':
                self.handle_choose_chief_rabbit_event(event)
            elif self.sub_screen == 'choose captain':
                self.handle_choose_captain_event(event)
            elif self.sub_screen == 'choose med rabbit':
                self.handle_choose_med_event(event)
            elif self.sub_screen == 'choose members':
                self.handle_choose_members_event(event)
            elif self.sub_screen == 'choose burrow':
                self.handle_choose_background_event(event)
            elif self.sub_screen == 'saved screen':
                self.handle_saved_warren_event(event)
        
        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if self.sub_screen == 'game mode':
                self.handle_game_mode_key(event)
            elif self.sub_screen == 'name warren':
                self.handle_name_warren_key(event)
            elif self.sub_screen == 'choose burrow':
                self.handle_choose_background_key(event)
            elif self.sub_screen == 'saved screen' and (event.key == pygame.K_RETURN or event.key == pygame.K_RIGHT):
                self.change_screen('start screen')

    def handle_game_mode_event(self, event):
        """Handle events for the game mode screen"""
        # Game mode selection buttons
        if event.ui_element == self.elements['classic_mode_button']:
            self.game_mode = 'classic'
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['expanded_mode_button']:
            self.game_mode = 'expanded'
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['cruel_mode_button']:
            self.game_mode = 'cruel'
            self.refresh_text_and_buttons()
        # When the next_step button is pressed, go to the Warren naming page.
        elif event.ui_element == self.elements['next_step']:
            game.settings['game_mode'] = self.game_mode
            self.open_name_warren()
    
    def handle_game_mode_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.change_screen('start screen')
        elif event.key == pygame.K_DOWN:
            if self.game_mode == 'classic':
                self.game_mode = 'expanded'
            elif self.game_mode == 'expanded':
                self.game_mode = 'cruel'
            self.refresh_text_and_buttons()
        elif event.key == pygame.K_UP:
            if self.game_mode == 'cruel':
                self.game_mode = 'expanded'
            elif self.game_mode == 'expanded':
                self.game_mode = 'classic'
            self.refresh_text_and_buttons()

        elif event.key == pygame.K_RIGHT or event.key == pygame.K_RETURN:
            if self.elements['next_step'].is_enabled:
                game.settings['game_mode'] = self.game_mode
                self.open_name_warren()

    def handle_name_warren_event(self, event):
        if event.ui_element == self.elements["random"]:
            self.elements["name_entry"].set_text(choice(names.names_dict["normal_prefixes"]))
        elif event.ui_element == self.elements["reset_name"]:
            self.elements["name_entry"].set_text("")
        elif event.ui_element == self.elements['next_step']:
            new_name = sub(r'[^A-Za-z0-9 ]+', "", self.elements["name_entry"].get_text()).strip()
            if not new_name:
                self.elements["error"].set_text("Your warren's name cannot be empty")
                self.elements["error"].show()
                return
            if new_name.casefold() in [warren.casefold() for warren in game.switches['warren_list']]:
                self.elements["error"].set_text("A warren with that name already exists.")
                self.elements["error"].show()
                return
            self.warren_name = new_name
            self.open_choose_chief_rabbit()
        elif event.ui_element == self.elements['previous_step']:
            self.warren_name = ""
            self.open_game_mode()
    
    def handle_name_warren_key(self, event):
        if event.key == pygame.K_ESCAPE:
            self.change_screen('start screen')
        elif event.key == pygame.K_LEFT:
            if not self.elements['name_entry'].is_focused:
                self.warren_name = ""
                self.open_game_mode()
        elif event.key == pygame.K_RIGHT:
            if not self.elements['name_entry'].is_focused:
                new_name = sub(r'[^A-Za-z0-9 ]+', "", self.elements["name_entry"].get_text()).strip()
                if not new_name:
                    self.elements["error"].set_text("Your warren's name cannot be empty")
                    self.elements["error"].show()
                    return
                if new_name.casefold() in [warren.casefold() for warren in game.switches['warren_list']]:
                    self.elements["error"].set_text("A warren with that name already exists.")
                    self.elements["error"].show()
                    return
                self.warren_name = new_name
                self.open_choose_chief_rabbit()
        elif event.key == pygame.K_RETURN:
            new_name = sub(r'[^A-Za-z0-9 ]+', "", self.elements["name_entry"].get_text()).strip()
            if not new_name:
                self.elements["error"].set_text("Your warren's name cannot be empty")
                self.elements["error"].show()
                return
            if new_name.casefold() in [warren.casefold() for warren in game.switches['warren_list']]:
                self.elements["error"].set_text("A warren with that name already exists.")
                self.elements["error"].show()
                return
            self.warren_name = new_name
            self.open_choose_chief_rabbit()

    def handle_choose_chief_rabbit_event(self, event):
        if event.ui_element in [self.elements['roll1'], self.elements['roll2'], self.elements['roll3'],
                                self.elements["dice"]]:
            self.elements['select_rabbit'].hide()
            create_example_rabbits()  # create new rabbits
            self.selected_rabbit = None  # Your selected rabbit now no longer exists. Sad. They go away.
            if self.elements['error_message']:
                self.elements['error_message'].hide()
            self.refresh_rabbit_images_and_info()  # Refresh all the images.
            self.rolls_left -= 1
            if game.config["warren_creation"]["rerolls"] == 3:
                event.ui_element.disable()
            else:
                self.elements["reroll_count"].set_text(str(self.rolls_left))
                if self.rolls_left == 0:
                    event.ui_element.disable()

        elif event.ui_element in [self.elements["rabbit" + str(u)] for u in range(0, 12)]:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                clicked_rabbit = event.ui_element.return_rabbit_object()
                if clicked_rabbit.age not in ["newborn", "kit", "adolescent"]:
                    self.chief_rabbit = clicked_rabbit
                    self.selected_rabbit = None
                    self.open_choose_captain()
            else:
                self.selected_rabbit = event.ui_element.return_rabbit_object()
                self.refresh_rabbit_images_and_info(self.selected_rabbit)
                self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['select_rabbit']:
            self.chief_rabbit = self.selected_rabbit
            self.selected_rabbit = None
            self.open_choose_captain()
        elif event.ui_element == self.elements['previous_step']:
            self.warren_name = ""
            self.open_name_warren()

    def handle_choose_captain_event(self, event):
        if event.ui_element == self.elements['previous_step']:
            self.chief_rabbit = None
            self.selected_rabbit = None
            self.open_choose_chief_rabbit()
        elif event.ui_element in [self.elements["rabbit" + str(u)] for u in range(0, 12)]:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                clicked_rabbit = event.ui_element.return_rabbit_object()
                if clicked_rabbit.age not in ["newborn", "kit", "adolescent"]:
                    self.captain = clicked_rabbit
                    self.selected_rabbit = None
                    self.open_choose_med_rabbit()
            elif event.ui_element.return_rabbit_object() != self.chief_rabbit:
                self.selected_rabbit = event.ui_element.return_rabbit_object()
                self.refresh_rabbit_images_and_info(self.selected_rabbit)
                self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['select_rabbit']:
            self.captain = self.selected_rabbit
            self.selected_rabbit = None
            self.open_choose_med_rabbit()

    def handle_choose_med_event(self, event):
        if event.ui_element == self.elements['previous_step']:
            self.captain = None
            self.selected_rabbit = None
            self.open_choose_captain()
        elif event.ui_element in [self.elements["rabbit" + str(u)] for u in range(0, 12)]:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                clicked_rabbit = event.ui_element.return_rabbit_object()
                if clicked_rabbit.age not in ["newborn", "kit", "adolescent"]:
                    self.med_rabbit = clicked_rabbit
                    self.selected_rabbit = None
                    self.open_choose_members()
            elif event.ui_element.return_rabbit_object():
                self.selected_rabbit = event.ui_element.return_rabbit_object()
                self.refresh_rabbit_images_and_info(self.selected_rabbit)
                self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['select_rabbit']:
            self.med_rabbit = self.selected_rabbit
            self.selected_rabbit = None
            self.open_choose_members()

    def handle_choose_members_event(self, event):
        if event.ui_element == self.elements['previous_step']:
            if not self.members:
                self.med_rabbit = None
                self.selected_rabbit = None
                self.open_choose_med_rabbit()
            else:
                self.members.pop()  # Delete the last rabbit added
                self.selected_rabbit = None
                self.refresh_rabbit_images_and_info()
                self.refresh_text_and_buttons()
        elif event.ui_element in [self.elements["rabbit" + str(u)] for u in range(0, 12)]:
            if event.ui_element.return_rabbit_object():
                if pygame.key.get_mods() & pygame.KMOD_SHIFT and len(self.members) < 7:
                    clicked_rabbit = event.ui_element.return_rabbit_object()
                    self.members.append(clicked_rabbit)
                    self.selected_rabbit = None
                    self.refresh_rabbit_images_and_info(None)
                    self.refresh_text_and_buttons()
                else:
                    self.selected_rabbit = event.ui_element.return_rabbit_object()
                    self.refresh_rabbit_images_and_info(self.selected_rabbit)
                    self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['select_rabbit']:
            self.members.append(self.selected_rabbit)
            self.selected_rabbit = None
            self.refresh_rabbit_images_and_info(None)
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['next_step']:
            self.selected_rabbit = None
            self.open_choose_background()

    def handle_choose_background_event(self, event):
        if event.ui_element == self.elements['previous_step']:
            self.open_choose_members()
        elif event.ui_element == self.elements['forest_biome']:
            self.biome_selected = "Forest"
            self.selected_burrow_tab = 1
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['mountain_biome']:
            self.biome_selected = "Mountainous"
            self.selected_burrow_tab = 1
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['plains_biome']:
            self.biome_selected = "Plains"
            self.selected_burrow_tab = 1
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['beach_biome']:
            self.biome_selected = "Beach"
            self.selected_burrow_tab = 1
            self.refresh_text_and_buttons()
        elif event.ui_element == self.tabs["tab1"]:
            self.selected_burrow_tab = 1
            self.refresh_selected_burrow()
        elif event.ui_element == self.tabs["tab2"]:
            self.selected_burrow_tab = 2
            self.refresh_selected_burrow()
        elif event.ui_element == self.tabs["tab3"]:
            self.selected_burrow_tab = 3
            self.refresh_selected_burrow()
        elif event.ui_element == self.tabs["tab4"]:
            self.selected_burrow_tab = 4
            self.refresh_selected_burrow()
        elif event.ui_element == self.tabs["newleaf_tab"]:
            self.selected_season = "Spring"
            self.refresh_text_and_buttons()
        elif event.ui_element == self.tabs["greenleaf_tab"]:
            self.selected_season = "Summer"
            self.refresh_text_and_buttons()
        elif event.ui_element == self.tabs["leaffall_tab"]:
            self.selected_season = "Autumn"
            self.refresh_text_and_buttons()
        elif event.ui_element == self.tabs["leafbare_tab"]:
            self.selected_season = "Winter"
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements["random_background"]:
            # Select a random biome and background
            old_biome = self.biome_selected
            possible_biomes = ['Forest', 'Mountainous', 'Plains', 'Beach']
            # ensuring that the new random burrow will not be the same one
            if old_biome is not None:
                possible_biomes.remove(old_biome)
            self.biome_selected = choice(possible_biomes)
            if self.biome_selected == 'Forest':
                self.selected_burrow_tab = randrange (1, 5)
            else:
                self.selected_burrow_tab = randrange(1, 4)
            self.refresh_selected_burrow()
            self.refresh_text_and_buttons()
        elif event.ui_element == self.elements['done_button']:
            self.save_warren()
            self.open_warren_saved_screen()
    
    def handle_choose_background_key(self, event):
        if event.key == pygame.K_RIGHT:
            if self.biome_selected is None:
                self.biome_selected = "Forest"
            elif self.biome_selected == "Forest":
                self.biome_selected = "Mountainous"
            elif self.biome_selected == "Mountainous":
                self.biome_selected = "Plains"
            elif self.biome_selected == "Plains":
                self.biome_selected = "Beach"
            self.selected_burrow_tab = 1
            self.refresh_text_and_buttons()
        elif event.key == pygame.K_LEFT:
            if self.biome_selected is None:
                self.biome_selected = "Beach"
            elif self.biome_selected == "Beach":
                self.biome_selected = "Plains"
            elif self.biome_selected == "Plains":
                self.biome_selected = "Mountainous"
            elif self.biome_selected == "Mountainous":
                self.biome_selected = "Forest"
            self.selected_burrow_tab = 1
            self.refresh_text_and_buttons()
        elif event.key == pygame.K_UP and self.biome_selected is not None:
            if self.selected_burrow_tab > 1:
                self.selected_burrow_tab -= 1
                self.refresh_selected_burrow()
        elif event.key == pygame.K_DOWN and self.biome_selected is not None:
            if self.selected_burrow_tab < 4:
                self.selected_burrow_tab += 1
                self.refresh_selected_burrow()
        elif event.key == pygame.K_RETURN:
            self.save_warren()
            self.open_warren_saved_screen()

    def handle_saved_warren_event(self, event):
        if event.ui_element == self.elements["continue"]:
            self.change_screen('burrow screen')

    def exit_screen(self):
        self.main_menu.kill()
        self.menu_warning.kill()
        self.clear_all_page()
        self.rolls_left = game.config["warren_creation"]["rerolls"]
        return super().exit_screen()

    def on_use(self):

        # Don't allow someone to enter no name for their warren
        if self.sub_screen == 'name warren':
            if self.elements["name_entry"].get_text() == "":
                self.elements['next_step'].disable()
            elif self.elements["name_entry"].get_text().startswith(" "):
                self.elements["error"].set_text("Warren names cannot start with a space.")
                self.elements["error"].show()
                self.elements['next_step'].disable()
            elif self.elements["name_entry"].get_text().casefold() in [warren.casefold() for warren in
                                                                       game.switches['warren_list']]:
                self.elements["error"].set_text("A warren with that name already exists.")
                self.elements["error"].show()
                self.elements['next_step'].disable()
                return
            else:
                self.elements["error"].hide()
                self.elements['next_step'].enable()

    def clear_all_page(self):
        """Clears the entire page, including layout images"""
        for image in self.elements:
            self.elements[image].kill()
        for tab in self.tabs:
            self.tabs[tab].kill()
        self.elements = {}

    def refresh_text_and_buttons(self):
        """Refreshes the button states and text boxes"""
        if self.sub_screen == "game mode":
            # Set the mode explanation text
            if self.game_mode == 'classic':
                display_text = self.classic_mode_text
                display_name = "Classic Mode"
            elif self.game_mode == 'expanded':
                display_text = self.expanded_mode_text
                display_name = "Expanded Mode"
            elif self.game_mode == 'cruel':
                display_text = self.cruel_mode_text
                display_name = "Cruel Season"
            else:
                display_text = ""
                display_name = "ERROR"
            self.elements['mode_details'].set_text(display_text)
            self.elements['mode_name'].set_text(display_name)

            # Update the enabled buttons for the game selection to disable the
            # buttons for the mode currently selected. Mostly for aesthetics, and it
            # make it very clear which mode is selected. 
            if self.game_mode == 'classic':
                self.elements['classic_mode_button'].disable()
                self.elements['expanded_mode_button'].enable()
                self.elements['cruel_mode_button'].enable()
            elif self.game_mode == 'expanded':
                self.elements['classic_mode_button'].enable()
                self.elements['expanded_mode_button'].disable()
                self.elements['cruel_mode_button'].enable()
            elif self.game_mode == 'cruel':
                self.elements['classic_mode_button'].enable()
                self.elements['expanded_mode_button'].enable()
                self.elements['cruel_mode_button'].disable()
            else:
                self.elements['classic_mode_button'].enable()
                self.elements['expanded_mode_button'].enable()
                self.elements['cruel_mode_button'].enable()

            # Don't let the player go forwards with cruel mode, it's not done yet.
            if self.game_mode == 'cruel':
                self.elements['next_step'].disable()
            else:
                self.elements['next_step'].enable()
        # Show the error message if you try to choose a child for chief rabbit, captain, or med rabbit.
        elif self.sub_screen in ['choose chief rabbit', 'choose captain', 'choose med rabbit']:
            if self.selected_rabbit.age in ["newborn", "kit", "adolescent"]:
                self.elements['select_rabbit'].hide()
                self.elements['error_message'].show()
            else:
                self.elements['select_rabbit'].show()
                self.elements['error_message'].hide()
        # Refresh the choose-members background to match number of rabbit's chosen.
        elif self.sub_screen == 'choose members':
            if len(self.members) == 0:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load("resources/images/pick_clan_screen/warren_none_light.png").convert_alpha(),
                        (1600, 1400)))
                self.elements['next_step'].disable()
            elif len(self.members) == 1:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load("resources/images/pick_clan_screen/warren_one_light.png").convert_alpha(),
                        (1600, 1400)))
                self.elements['next_step'].disable()
            elif len(self.members) == 2:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load("resources/images/pick_clan_screen/warren_two_light.png").convert_alpha(),
                        (1600, 1400)))
                self.elements['next_step'].disable()
            elif len(self.members) == 3:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load("resources/images/pick_clan_screen/warren_three_light.png").convert_alpha(),
                        (1600, 1400)))
                self.elements['next_step'].disable()
            elif 4 <= len(self.members) <= 6:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load("resources/images/pick_clan_screen/warren_four_light.png").convert_alpha(),
                        (1600, 1400)))
                self.elements['next_step'].enable()
                # In order for the "previous step" to work properly, we must enable this button, just in case it
                # was disabled in the next step.
                self.elements["select_rabbit"].enable()
            elif len(self.members) == 7:
                self.elements["background"].set_image(
                    pygame.transform.scale(
                        pygame.image.load("resources/images/pick_clan_screen/warren_full_light.png").convert_alpha(),
                        (1600, 1400)))
                self.elements["select_rabbit"].disable()
                self.elements['next_step'].enable()

            # Hide the recruit rabbit button if no rabbit is selected.
            if self.selected_rabbit is not None:
                self.elements['select_rabbit'].show()
            else:
                self.elements['select_rabbit'].hide()

        elif self.sub_screen == 'choose burrow':
            # Enable/disable biome buttons
            if self.biome_selected == 'Forest':
                self.elements['forest_biome'].disable()
                self.elements['mountain_biome'].enable()
                self.elements['plains_biome'].enable()
                self.elements['beach_biome'].enable()
            elif self.biome_selected == "Mountainous":
                self.elements['forest_biome'].enable()
                self.elements['mountain_biome'].disable()
                self.elements['plains_biome'].enable()
                self.elements['beach_biome'].enable()
            elif self.biome_selected == "Plains":
                self.elements['forest_biome'].enable()
                self.elements['mountain_biome'].enable()
                self.elements['plains_biome'].disable()
                self.elements['beach_biome'].enable()
            elif self.biome_selected == "Beach":
                self.elements['forest_biome'].enable()
                self.elements['mountain_biome'].enable()
                self.elements['plains_biome'].enable()
                self.elements['beach_biome'].disable()

            if self.selected_season == 'Spring':
                self.tabs['newleaf_tab'].disable()
                self.tabs['greenleaf_tab'].enable()
                self.tabs['leaffall_tab'].enable()
                self.tabs['leafbare_tab'].enable()
            elif self.selected_season == 'Summer':
                self.tabs['newleaf_tab'].enable()
                self.tabs['greenleaf_tab'].disable()
                self.tabs['leaffall_tab'].enable()
                self.tabs['leafbare_tab'].enable()
            elif self.selected_season == 'Autumn':
                self.tabs['newleaf_tab'].enable()
                self.tabs['greenleaf_tab'].enable()
                self.tabs['leaffall_tab'].disable()
                self.tabs['leafbare_tab'].enable()
            elif self.selected_season == 'Winter':
                self.tabs['newleaf_tab'].enable()
                self.tabs['greenleaf_tab'].enable()
                self.tabs['leaffall_tab'].enable()
                self.tabs['leafbare_tab'].disable()

            if self.biome_selected is not None and self.selected_burrow_tab is not None:
                self.elements['done_button'].enable()

            # Deal with tab and shown burrow image:
            self.refresh_selected_burrow()

    def refresh_selected_burrow(self):
        """Updates selected burrow image and tabs"""
        self.tabs["tab1"].kill()
        self.tabs["tab2"].kill()
        self.tabs["tab3"].kill()
        self.tabs["tab4"].kill()

        if self.biome_selected == 'Forest':
            self.tabs["tab1"] = UIImageButton(scale(pygame.Rect((190, 360), (308, 60))), "", object_id="#classic_tab"
                                              , manager=MANAGER)
            self.tabs["tab2"] = UIImageButton(scale(pygame.Rect((216, 430), (308, 60))), "", object_id="#gully_tab"
                                              , manager=MANAGER)
            self.tabs["tab3"] = UIImageButton(scale(pygame.Rect((190, 500), (308, 60))), "", object_id="#grotto_tab"
                                              , manager=MANAGER)
            self.tabs["tab4"] = UIImageButton(scale(pygame.Rect((170, 570), (308, 60))), "", object_id="#lakeside_tab"
                                              , manager=MANAGER)
        elif self.biome_selected == 'Mountainous':
            self.tabs["tab1"] = UIImageButton(scale(pygame.Rect((222, 360), (308, 60))), "", object_id="#cliff_tab"
                                              , manager=MANAGER)
            self.tabs["tab2"] = UIImageButton(scale(pygame.Rect((180, 430), (308, 60))), "", object_id="#cave_tab"
                                              , manager=MANAGER)
            self.tabs["tab3"] = UIImageButton(scale(pygame.Rect((85, 500), (358, 60))), "", object_id="#crystal_tab"
                                              , manager=MANAGER)
        elif self.biome_selected == 'Plains':
            self.tabs["tab1"] = UIImageButton(scale(pygame.Rect((128, 360), (308, 60))), "", object_id="#grasslands_tab"
                                              , manager=MANAGER, )
            self.tabs["tab2"] = UIImageButton(scale(pygame.Rect((178, 430), (308, 60))), "", object_id="#tunnel_tab"
                                              , manager=MANAGER)
            self.tabs["tab3"] = UIImageButton(scale(pygame.Rect((128, 500), (308, 60))), "", object_id="#wasteland_tab"
                                              , manager=MANAGER)
        elif self.biome_selected == 'Beach':
            self.tabs["tab1"] = UIImageButton(scale(pygame.Rect((152, 360), (308, 60))), "", object_id="#tidepool_tab"
                                              , manager=MANAGER)
            self.tabs["tab2"] = UIImageButton(scale(pygame.Rect((130, 430), (308, 60))), "", object_id="#tidal_cave_tab"
                                              , manager=MANAGER)
            self.tabs["tab3"] = UIImageButton(scale(pygame.Rect((140, 500), (308, 60))), "", object_id="#shipwreck_tab"
                                              , manager=MANAGER)

        if self.selected_burrow_tab == 1:
            self.tabs["tab1"].disable()
            self.tabs["tab2"].enable()
            self.tabs["tab3"].enable()
            self.tabs["tab4"].enable()
        elif self.selected_burrow_tab == 2:
            self.tabs["tab1"].enable()
            self.tabs["tab2"].disable()
            self.tabs["tab3"].enable()
            self.tabs["tab4"].enable()
        elif self.selected_burrow_tab == 3:
            self.tabs["tab1"].enable()
            self.tabs["tab2"].enable()
            self.tabs["tab3"].disable()
            self.tabs["tab4"].enable()
        elif self.selected_burrow_tab == 4:
            self.tabs["tab1"].enable()
            self.tabs["tab2"].enable()
            self.tabs["tab3"].enable()
            self.tabs["tab4"].disable()
        else:
            self.tabs["tab1"].enable()
            self.tabs["tab2"].enable()
            self.tabs["tab3"].enable()
            self.tabs["tab4"].enable()

        # I have to do this for proper layering.
        if "burrow_art" in self.elements:
            self.elements["burrow_art"].kill()
        if self.biome_selected:
            self.elements["burrow_art"] = pygame_gui.elements.UIImage(scale(pygame.Rect((350, 340), (900, 800))),
                                                                    pygame.transform.scale(
                                                                        pygame.image.load(
                                                                            self.get_burrow_art_path(
                                                                                self.selected_burrow_tab)).convert_alpha(),
                                                                        (900, 800)), manager=MANAGER)
            self.elements['art_frame'].kill()
            self.elements['art_frame'] = pygame_gui.elements.UIImage(scale(pygame.Rect(((334, 324), (932, 832)))),
                                                                     pygame.transform.scale(
                                                                         pygame.image.load(
                                                                             "resources/images/bg_preview_border.png").convert_alpha(),
                                                                         (932, 832)), manager=MANAGER)

    def refresh_selected_rabbit_info(self, selected=None):
        # SELECTED RABBIT INFO
        if selected is not None:

            if self.sub_screen == 'choose chief rabbit':
                self.elements['rabbit_name'].set_text(str(selected.name) +
                                                   ' --> ' +
                                                   selected.name.prefix +
                                                   'rah')
            else:
                self.elements['rabbit_name'].set_text(str(selected.name))
            self.elements['rabbit_name'].show()
            self.elements['rabbit_info'].set_text(selected.gender + "\n" +
                                               str(selected.age + "\n" +
                                                   str(selected.personality.trait) + "\n" +
                                                   str(selected.skills.skill_string())))
            self.elements['rabbit_info'].show()
        else:
            self.elements['next_step'].disable()
            self.elements['rabbit_info'].hide()
            self.elements['rabbit_name'].hide()

    def refresh_rabbit_images_and_info(self, selected=None):
        """Update the image of the rabbit selected in the middle. Info and image.
        Also updates the lorabbition of selected rabbits. """

        column_poss = [100, 200]

        # updates selected rabbit info
        self.refresh_selected_rabbit_info(selected)

        # RABBIT IMAGES
        for u in range(6):
            if "rabbit" + str(u) in self.elements:
                self.elements["rabbit" + str(u)].kill()
            if game.choose_rabbits[u] == selected:
                self.elements["rabbit" + str(u)] = self.elements["rabbit" + str(u)] = UISpriteButton(
                    scale(pygame.Rect((540, 400), (300, 300))),
                    pygame.transform.scale(game.choose_rabbits[u].sprite, (300, 300)),
                    rabbit_object=game.choose_rabbits[u])
            elif game.choose_rabbits[u] in [self.chief_rabbit, self.captain, self.med_rabbit] + self.members:
                self.elements["rabbit" + str(u)] = UISpriteButton(scale(pygame.Rect((1300, 250 + 100 * u), (100, 100))),
                                                               game.choose_rabbits[u].sprite,
                                                               rabbit_object=game.choose_rabbits[u], manager=MANAGER)
                self.elements["rabbit" + str(u)].disable()
            else:
                self.elements["rabbit" + str(u)] = UISpriteButton(
                    scale(pygame.Rect((column_poss[0], 260 + 100 * u), (100, 100))),
                    game.choose_rabbits[u].sprite,
                    tool_tip_text=self._get_rabbit_tooltip_string(game.choose_rabbits[u]),
                    rabbit_object=game.choose_rabbits[u], manager=MANAGER)
        for u in range(6, 12):
            if "rabbit" + str(u) in self.elements:
                self.elements["rabbit" + str(u)].kill()
            if game.choose_rabbits[u] == selected:
                self.elements["rabbit" + str(u)] = self.elements["rabbit" + str(u)] = UISpriteButton(
                    scale(pygame.Rect((540, 400), (300, 300))),
                    pygame.transform.scale(game.choose_rabbits[u].sprite, (300, 300)),
                    rabbit_object=game.choose_rabbits[u], manager=MANAGER)
            elif game.choose_rabbits[u] in [self.chief_rabbit, self.captain, self.med_rabbit] + self.members:
                self.elements["rabbit" + str(u)] = UISpriteButton(
                    scale(pygame.Rect((1400, 260 + 100 * (u - 6)), (100, 100))),
                    game.choose_rabbits[u].sprite,
                    rabbit_object=game.choose_rabbits[u], manager=MANAGER)
                self.elements["rabbit" + str(u)].disable()
            else:
                self.elements["rabbit" + str(u)] = UISpriteButton(
                    scale(pygame.Rect((column_poss[1], 260 + 100 * (u - 6)), (100, 100))),
                    game.choose_rabbits[u].sprite,
                    tool_tip_text=self._get_rabbit_tooltip_string(game.choose_rabbits[u]),
                    rabbit_object=game.choose_rabbits[u], manager=MANAGER)

    def _get_rabbit_tooltip_string(self, rabbit: Rabbit):
        """Get tooltip for rabbit. Tooltip displays name, sex, age group, and trait."""

        return f"<b>{rabbit.name}</b><br>{rabbit.gender}<br>{rabbit.age}<br>{rabbit.personality.trait}"

    def open_game_mode(self):
        # Clear previous screen
        self.clear_all_page()
        self.sub_screen = 'game mode'

        text_box = image_cache.load_image(
            'resources/images/game_mode_text_box.png').convert_alpha()

        self.elements['game_mode_background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((650, 260), (798, 922))),
                                                                            pygame.transform.scale(text_box, (798, 922))
                                                                            , manager=MANAGER)
        self.elements['permi_warning'] = pygame_gui.elements.UITextBox(
            "Your warren's game mode is permanent and cannot be changed after warren creation.",
            scale(pygame.Rect((200, 1162), (1200, 80))),
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER
        )

        # Create all the elements.
        self.elements['classic_mode_button'] = UIImageButton(scale(pygame.Rect((218, 480), (264, 60))), "",
                                                             object_id="#classic_mode_button",
                                                             manager=MANAGER)
        self.elements['expanded_mode_button'] = UIImageButton(scale(pygame.Rect((188, 640), (324, 68))), "",
                                                              object_id="#expanded_mode_button",
                                                              manager=MANAGER)
        self.elements['cruel_mode_button'] = UIImageButton(scale(pygame.Rect((200, 800), (300, 60))), "",
                                                           object_id="#cruel_mode_button",
                                                           manager=MANAGER)
        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 1240), (294, 60))), "",
                                                       object_id="#previous_step_button",
                                                       manager=MANAGER)
        self.elements['previous_step'].disable()
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 1240), (294, 60))), "",
                                                   object_id="#next_step_button",
                                                   manager=MANAGER)
        self.elements['mode_details'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((650, 320), (810, 922))),
                                                                      object_id="#text_box_30_horizleft_pad_40_40",
                                                                      manager=MANAGER)
        self.elements['mode_name'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((850, 270), (400, 55))),
                                                                   object_id="#text_box_30_horizcenter_light",
                                                                   manager=MANAGER)

        self.refresh_text_and_buttons()

    def open_name_warren(self):
        """Opens the name Warren screen"""
        self.clear_all_page()
        self.sub_screen = 'name warren'

        # Create all the elements.
        self.elements["background"] = pygame_gui.elements.UIImage(scale(pygame.Rect((0, 0), (1600, 1400))),
                                                                  pygame.transform.scale(MakeWarrenScreen.name_warren_img,
                                                                                         (1600, 1400))
                                                                  , manager=MANAGER)
        self.elements['background'].disable()
        self.elements["random"] = UIImageButton(scale(pygame.Rect((448, 1190), (68, 68))), "",
                                                object_id="#random_dice_button"
                                                , manager=MANAGER)

        self.elements["error"] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((506, 1310), (596, -1))),
                                                               manager=MANAGER,
                                                               object_id="#default_dark", visible=False)

        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 1270), (294, 60))), "",
                                                       object_id="#previous_step_button", manager=MANAGER)
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 1270), (294, 60))), "",
                                                   object_id="#next_step_button", manager=MANAGER)
        self.elements['next_step'].disable()
        self.elements["name_entry"] = pygame_gui.elements.UITextEntryLine(scale(pygame.Rect((530, 1195), (280, 58)))
                                                                          , manager=MANAGER)
        self.elements["name_entry"].set_allowed_characters(
            list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_- "))
        self.elements["name_entry"].set_text_length_limit(11)
        self.elements["warren"] = pygame_gui.elements.UITextBox("-Warren",
                                                              scale(pygame.Rect((750, 1200), (200, 50))),
                                                              object_id="#text_box_30_horizcenter_light",
                                                              manager=MANAGER)
        self.elements["reset_name"] = UIImageButton(scale(pygame.Rect((910, 1190), (268, 60))), "",
                                                    object_id="#reset_name_button", manager=MANAGER)

    def warren_name_header(self):
        self.elements["name_backdrop"] = pygame_gui.elements.UIImage(scale(pygame.Rect((584, 200), (432, 100))),
                                                                     MakeWarrenScreen.warren_name_frame_img, manager=MANAGER)
        self.elements["warren_name"] = pygame_gui.elements.UITextBox(self.warren_name,
                                                                   scale(pygame.Rect((585, 212), (432, 100))),
                                                                   object_id="#text_box_30_horizcenter_light",
                                                                   manager=MANAGER)

    def open_choose_chief_rabbit(self):
        """Set up the screen for the choose chief rabbit phase. """
        self.clear_all_page()
        self.sub_screen = 'choose chief rabbit'

        self.elements['background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((0, 828), (1600, 572))),
                                                                  MakeWarrenScreen.chief_rabbitimg, manager=MANAGER)

        self.elements['background'].disable()
        self.warren_name_header()

        # Roll_buttons
        x_pos = 310
        y_pos = 470
        self.elements['roll1'] = UIImageButton(scale(pygame.Rect((x_pos, y_pos), (68, 68))), "",
                                               object_id="#random_dice_button", manager=MANAGER)
        y_pos += 80
        self.elements['roll2'] = UIImageButton(scale(pygame.Rect((x_pos, y_pos), (68, 68))), "",
                                               object_id="#random_dice_button", manager=MANAGER)
        y_pos += 80
        self.elements['roll3'] = UIImageButton(scale(pygame.Rect((x_pos, y_pos), (68, 68))), "",
                                               object_id="#random_dice_button", manager=MANAGER)

        _tmp = 160
        if self.rolls_left == -1:
            _tmp += 5
        self.elements['dice'] = UIImageButton(scale(pygame.Rect((_tmp, 870), (68, 68))), "",
                                              object_id="#random_dice_button", manager=MANAGER)
        del _tmp
        self.elements['reroll_count'] = pygame_gui.elements.UILabel(scale(pygame.Rect((200, 880), (100, 50))),
                                                                    str(self.rolls_left),
                                                                    object_id=get_text_box_theme(""),
                                                                    manager=MANAGER)

        if game.config["warren_creation"]["rerolls"] == 3:
            if self.rolls_left <= 2:
                self.elements['roll1'].disable()
            if self.rolls_left <= 1:
                self.elements['roll2'].disable()
            if self.rolls_left == 0:
                self.elements['roll3'].disable()
            self.elements['dice'].hide()
            self.elements['reroll_count'].hide()
        else:
            if self.rolls_left == 0:
                self.elements['dice'].disable()
            elif self.rolls_left == -1:
                self.elements['reroll_count'].hide()
            self.elements['roll1'].hide()
            self.elements['roll2'].hide()
            self.elements['roll3'].hide()

        # info for chosen rabbits:
        self.elements['rabbit_info'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((880, 500), (230, 250))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_22_horizleft_spacing_95"),
                                                                  manager=MANAGER)
        self.elements['rabbit_name'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((300, 350), (1000, 110))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_30_horizcenter"),
                                                                  manager=MANAGER)

        self.elements['select_rabbit'] = UIImageButton(scale(pygame.Rect((468, 696), (664, 104))), "",
                                                    object_id="#appoint_chief_button", 
                                                    starting_height=2,
                                                    visible=False, manager=MANAGER)
        # Error message, to appear if you can't choose that rabbit.
        self.elements['error_message'] = pygame_gui.elements.UITextBox(
            "Too young to become chief rabbit",
            scale(pygame.Rect((300, 706), (1000, 110))),
            object_id=get_text_box_theme("#text_box_30_horizcenter_red"),
            visible=False,
            manager=MANAGER)

        # Next and previous buttons
        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 800), (294, 60))), "",
                                                       object_id="#previous_step_button", manager=MANAGER)
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 800), (294, 60))), "",
                                                   object_id="#next_step_button", manager=MANAGER)
        self.elements['next_step'].disable()

        # draw rabbits to choose from
        self.refresh_rabbit_images_and_info()

    def open_choose_captain(self):
        """Open sub-page to select captain."""
        self.clear_all_page()
        self.sub_screen = 'choose captain'

        self.elements['background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((0, 828), (1600, 572))),
                                                                  MakeWarrenScreen.captain_img, manager=MANAGER)
        self.elements['background'].disable()
        self.warren_name_header()

        # info for chosen rabbits:
        self.elements['rabbit_info'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((880, 520), (230, 250))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_22_horizleft_spacing_95"),
                                                                  manager=MANAGER)
        self.elements['rabbit_name'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((300, 350), (1000, 110))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_30_horizcenter"),
                                                                  manager=MANAGER)

        self.elements['select_rabbit'] = UIImageButton(scale(pygame.Rect((418, 696), (768, 104))), "",
                                                    object_id="#support_chief_rabbit_button", 
                                                    starting_height=2,
                                                    visible=False, manager=MANAGER)
        # Error message, to appear if you can't choose that rabbit.
        self.elements['error_message'] = pygame_gui.elements.UITextBox(
            "Too young to become captain",
            scale(pygame.Rect((300, 706), (1000, 110))),
            object_id=get_text_box_theme("#text_box_30_horizcenter_red"),
            visible=False,
            manager=MANAGER)

        # Next and previous buttons
        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 800), (294, 60))), "",
                                                       object_id="#previous_step_button", manager=MANAGER)
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 800), (294, 60))), "",
                                                   object_id="#next_step_button", manager=MANAGER)
        self.elements['next_step'].disable()

        # draw rabbits to choose from
        self.refresh_rabbit_images_and_info()

    def open_choose_med_rabbit(self):
        self.clear_all_page()
        self.sub_screen = 'choose med rabbit'

        self.elements['background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((0, 828), (1600, 572))),
                                                                  MakeWarrenScreen.medic_img, manager=MANAGER)
        self.elements['background'].disable()
        self.warren_name_header()

        # info for chosen rabbits:
        self.elements['rabbit_info'] = pygame_gui.elements.UITextBox("",
                                                                  scale(pygame.Rect((880, 520), (230, 250))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_22_horizleft_spacing_95"),
                                                                  manager=MANAGER)
        self.elements['rabbit_name'] = pygame_gui.elements.UITextBox("",
                                                                  scale(pygame.Rect((300, 350), (1000, 110))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_30_horizcenter"),
                                                                  manager=MANAGER)

        self.elements['select_rabbit'] = UIImageButton(scale(pygame.Rect((520, 684), (612, 116))),
                                                    "",
                                                    object_id="#aid_warren_button",
                                                    starting_height=2,
                                                    visible=False,
                                                    manager=MANAGER)
        # Error message, to appear if you can't choose that rabbit.
        self.elements['error_message'] = pygame_gui.elements.UITextBox(
            "Too young to become a healer",
            scale(pygame.Rect((300, 706), (1000, 110))),
            object_id=get_text_box_theme("#text_box_30_horizcenter_red"),
            visible=False,
            manager=MANAGER)

        # Next and previous buttons
        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 800), (294, 60))), "",
                                                       object_id="#previous_step_button", manager=MANAGER)
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 800), (294, 60))), "",
                                                   object_id="#next_step_button", manager=MANAGER)
        self.elements['next_step'].disable()

        # draw rabbits to choose from
        self.refresh_rabbit_images_and_info()

    def open_choose_members(self):
        self.clear_all_page()
        self.sub_screen = 'choose members'

        self.elements['background'] = pygame_gui.elements.UIImage(scale(pygame.Rect((0, 828), (1600, 572))),
                                                                  pygame.transform.scale(
                                                                      pygame.image.load(
                                                                          "resources/images/pick_clan_screen/warren_none_light.png").convert_alpha(),
                                                                      (1600, 1400)), manager=MANAGER)
        self.elements['background'].disable()
        self.warren_name_header()

        # info for chosen rabbits:
        self.elements['rabbit_info'] = pygame_gui.elements.UITextBox("",
                                                                  scale(pygame.Rect((880, 520), (230, 250))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_22_horizleft_spacing_95"),
                                                                  manager=MANAGER)
        self.elements['rabbit_name'] = pygame_gui.elements.UITextBox("", scale(pygame.Rect((300, 350), (1000, 110))),
                                                                  visible=False,
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_30_horizcenter"),
                                                                  manager=MANAGER)

        self.elements['select_rabbit'] = UIImageButton(scale(pygame.Rect((706, 720), (190, 60))),
                                                    "",
                                                    object_id="#recruit_button",
                                                    starting_height=2,
                                                    visible=False,
                                                    manager=MANAGER)

        # Next and previous buttons
        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 800), (294, 60))), "",
                                                       object_id="#previous_step_button", manager=MANAGER)
        self.elements['next_step'] = UIImageButton(scale(pygame.Rect((800, 800), (294, 60))), "",
                                                   object_id="#next_step_button", manager=MANAGER)
        self.elements['next_step'].disable()

        # draw rabbits to choose from
        self.refresh_rabbit_images_and_info()

        # This is doing the same thing again, but it's needed to make the "last step button work"
        self.refresh_rabbit_images_and_info()
        self.refresh_text_and_buttons()

    def open_choose_background(self):
        # clear screen
        self.clear_all_page()
        self.sub_screen = 'choose burrow'

        self.elements['previous_step'] = UIImageButton(scale(pygame.Rect((506, 1290), (294, 60))), "",
                                                       object_id="#previous_step_button", manager=MANAGER)
        self.elements["done_button"] = UIImageButton(scale(pygame.Rect((800, 1290), (294, 60))), "",
                                                     object_id="#done_arrow_button", manager=MANAGER)
        self.elements['done_button'].disable()

        # Biome buttons
        self.elements['forest_biome'] = UIImageButton(scale(pygame.Rect((392, 200), (200, 92))), "",
                                                      object_id="#forest_biome_button", manager=MANAGER)
        self.elements['mountain_biome'] = UIImageButton(scale(pygame.Rect((608, 200), (212, 92))), "",
                                                        object_id="#mountain_biome_button", manager=MANAGER)
        self.elements['plains_biome'] = UIImageButton(scale(pygame.Rect((848, 200), (176, 92))), "",
                                                      object_id="#plains_biome_button", manager=MANAGER)
        self.elements['beach_biome'] = UIImageButton(scale(pygame.Rect((1040, 200), (164, 92))), "",
                                                     object_id="#beach_biome_button", manager=MANAGER)

        # Camp Art Choosing Tabs, Dummy buttons, will be overridden.
        self.tabs["tab1"] = UIImageButton(scale(pygame.Rect((0, 0), (0, 0))), "",
                                          visible=False, manager=MANAGER)
        self.tabs["tab2"] = UIImageButton(scale(pygame.Rect((0, 0), (0, 0))), "",
                                          visible=False, manager=MANAGER)
        self.tabs["tab3"] = UIImageButton(scale(pygame.Rect((0, 0), (0, 0))), "",
                                          visible=False, manager=MANAGER)
        self.tabs["tab4"] = UIImageButton(scale(pygame.Rect((0, 0), (0, 0))), "",
                                          visible=False, manager=MANAGER)

        y_pos = 550
        self.tabs["newleaf_tab"] = UIImageButton(scale(pygame.Rect((1250, y_pos), (78, 68))), "",
                                                 object_id="#newleaf_toggle_button",
                                                 manager=MANAGER,
                                                 tool_tip_text='Switch starting season to Spring.'
                                                 )
        y_pos += 100
        self.tabs["greenleaf_tab"] = UIImageButton(scale(pygame.Rect((1250, y_pos), (78, 68))), "",
                                                   object_id="#greenleaf_toggle_button",
                                                   manager=MANAGER,
                                                   tool_tip_text='Switch starting season to Summer.'
                                                   )
        y_pos += 100
        self.tabs["leaffall_tab"] = UIImageButton(scale(pygame.Rect((1250, y_pos), (78, 68))), "",
                                                  object_id="#leaffall_toggle_button",
                                                  manager=MANAGER,
                                                  tool_tip_text='Switch starting season to Autumn.'
                                                  )
        y_pos += 100
        self.tabs["leafbare_tab"] = UIImageButton(scale(pygame.Rect((1250, y_pos), (78, 68))), "",
                                                  object_id="#leafbare_toggle_button",
                                                  manager=MANAGER,
                                                  tool_tip_text='Switch starting season to Winter.'
                                                  )
        # Random background
        self.elements["random_background"] = UIImageButton(scale(pygame.Rect((510, 1190), (580, 60))), "",
                                                           object_id="#random_background_button", manager=MANAGER)

        # art frame
        self.elements['art_frame'] = pygame_gui.elements.UIImage(scale(pygame.Rect(((334, 324), (932, 832)))),
                                                                 pygame.transform.scale(
                                                                     pygame.image.load(
                                                                         "resources/images/bg_preview_border.png").convert_alpha(),
                                                                     (932, 832)), manager=MANAGER)

        # burrow art self.elements["burrow_art"] = pygame_gui.elements.UIImage(scale(pygame.Rect((175,170),(450, 400))),
        # pygame.image.load(self.get_burrow_art_path(1)).convert_alpha(), visible=False)

    def open_warren_saved_screen(self):
        self.clear_all_page()
        self.sub_screen = 'saved screen'

        self.elements["chief_rabbit_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((700, 240), (200, 200))),
                                                                    pygame.transform.scale(
                                                                        game.warren.chief_rabbit.sprite,
                                                                        (200, 200)), manager=MANAGER)
        self.elements["continue"] = UIImageButton(scale(pygame.Rect((692, 500), (204, 60))), "",
                                                  object_id="#continue_button_small")
        self.elements["save_confirm"] = pygame_gui.elements.UITextBox('Your Warren has been created and saved!',
                                                                      scale(pygame.Rect((200, 140), (1200, 60))),
                                                                      object_id=get_text_box_theme(
                                                                          "#text_box_30_horizcenter"),
                                                                      manager=MANAGER)

    def save_warren(self):
        
        game.mediated.clear()
        game.patrolled.clear()
        game.rabbit_to_fade.clear()
        Rabbit.outside_rabbits.clear()
        Patrol.used_patrols.clear()
        convert_burrow = {1: 'burrow1', 2: 'burrow2', 3: 'burrow3', 4: 'burrow4'}
        game.warren = Warren(self.warren_name,
                         self.chief_rabbit,
                         self.captain,
                         self.med_rabbit,
                         self.biome_selected,
                         convert_burrow[self.selected_burrow_tab],
                         self.game_mode, self.members,
                         starting_season=self.selected_season)
        game.warren.create_warren()
        #game.warren.inle_rabbits.clear()
        game.cur_events_list.clear()
        game.herb_events_list.clear()
        Rabbit.grief_strings.clear()
        Rabbit.sort_rabbits()

    def get_burrow_art_path(self, burrownum):
        leaf = self.selected_season.replace("-", "")

        burrow_bg_base_dir = "resources/images/burrow_bg/"
        start_leave = leaf.casefold()
        light_dark = "light"
        if game.settings["dark mode"]:
            light_dark = "dark"

        biome = self.biome_selected.lower()

        if burrownum:
            return f'{burrow_bg_base_dir}/{biome}/{start_leave}_burrow{burrownum}_{light_dark}.png'
        else:
            return None
