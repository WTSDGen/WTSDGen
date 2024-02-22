#!/usr/bin/env python3

import os
from random import choice

import pygame

from ..rabbit.history import History
from ..housekeeping.datadir import get_save_dir
from ..game_structure.windows import ChangeRabbitName, SpecifyRabbitGender, KillRabbit, ChangeRabbitToggles

import ujson

from scripts.utility import event_text_adjust, scale, ACC_DISPLAY, process_text, chunks

from .Screens import Screens

from scripts.utility import get_text_box_theme, scale_dimentions, shorten_text_to_fit
from scripts.rabbit.rabbits import Rabbit, BACKSTORIES
from scripts.rabbit.pelts import Pelt
from scripts.game_structure import image_cache
import pygame_gui
from re import sub
from scripts.game_structure.image_button import UIImageButton, UITextBoxTweaked
from scripts.game_structure.game_essentials import game, MANAGER
from scripts.warren_resources.freshkill import FRESHKILL_ACTIVE


# ---------------------------------------------------------------------------- #
#             change how accessory info displays on rabbit profiles               #
# ---------------------------------------------------------------------------- #
def accessory_display_name(rabbit):
    accessory = rabbit.pelt.accessory

    if accessory is None:
        return ''
    acc_display = accessory.lower()

    if accessory in Pelt.collars:
        collar_colors = {'crimson': 'red', 'blue': 'blue', 'yellow': 'yellow', 'cyan': 'cyan',
                         'red': 'orange', 'lime': 'lime', 'green': 'green', 'rainbow': 'rainbow',
                         'black': 'black', 'spikes': 'spiky', 'white': 'white', 'pink': 'pink',
                         'purple': 'purple', 'multi': 'multi', 'indigo': 'indigo'}
        collar_color = next((color for color in collar_colors if acc_display.startswith(color)), None)

        if collar_color:
            if acc_display.endswith('bow') and not collar_color == 'rainbow':
                acc_display = collar_colors[collar_color] + ' bow'
            elif acc_display.endswith('bell'):
                acc_display = collar_colors[collar_color] + ' bell collar'
            else:
                acc_display = collar_colors[collar_color] + ' collar'

    elif accessory in Pelt.wild_accessories:
        if acc_display == 'blue feathers':
            acc_display = 'crow feathers'
        elif acc_display == 'red feathers':
            acc_display = 'cardinal feathers'

    return acc_display


# ---------------------------------------------------------------------------- #
#               assigns backstory blurbs to the backstory                      #
# ---------------------------------------------------------------------------- #
def bs_blurb_text(rabbit):
    backstory = rabbit.backstory
    backstory_text = BACKSTORIES["backstories"][backstory]
    
    if rabbit.status in ['pet', 'hlessi', 'rogue', 'defector']:
            return f"This rabbit is a {rabbit.status} and currently resides outside of the warrens."
    
    return backstory_text

# ---------------------------------------------------------------------------- #
#             change how backstory info displays on rabbit profiles               #
# ---------------------------------------------------------------------------- #
def backstory_text(rabbit):
    backstory = rabbit.backstory
    if backstory is None:
        return ''
    bs_category = None
    
    for category in BACKSTORIES["backstory_categories"]:
        if backstory in category:
            bs_category = category
            break
    bs_display = BACKSTORIES["backstory_display"][bs_category]

    return bs_display

# ---------------------------------------------------------------------------- #
#                               Profile Screen                                 #
# ---------------------------------------------------------------------------- #
class ProfileScreen(Screens):
    # UI Images
    backstory_tab = image_cache.load_image("resources/images/backstory_bg.png").convert_alpha()
    conditions_tab = image_cache.load_image("resources/images/conditions_tab_backdrop.png").convert_alpha()
    condition_details_box = image_cache.load_image("resources/images/condition_details_box.png").convert_alpha()

    # Keep track of current tabs open. Can be used to keep tabs open when pages are switched, and
    # helps with exiting the screen
    open_tab = None

    def __init__(self, name=None):
        super().__init__(name)
        self.show_months = None
        self.no_months = None
        self.help_button = None
        self.open_sub_tab = None
        self.editing_notes = False
        self.user_notes = None
        self.save_text = None
        self.not_fav_tab = None
        self.fav_tab = None
        self.edit_text = None
        self.sub_tab_4 = None
        self.sub_tab_3 = None
        self.sub_tab_2 = None
        self.sub_tab_1 = None
        self.backstory_background = None
        self.history_text_box = None
        self.conditions_tab_button = None
        self.condition_container = None
        self.left_conditions_arrow = None
        self.right_conditions_arrow = None
        self.conditions_background = None
        self.previous_rabbit = None
        self.next_rabbit = None
        self.rabbit_image = None
        self.background = None
        self.rabbit_info_column2 = None
        self.rabbit_info_column1 = None
        self.rabbit_thought = None
        self.rabbit_name = None
        self.placeholder_tab_4 = None
        self.placeholder_tab_3 = None
        self.placeholder_tab_2 = None
        self.backstory_tab_button = None
        self.dangerous_tab_button = None
        self.personal_tab_button = None
        self.roles_tab_button = None
        self.relations_tab_button = None
        self.back_button = None
        self.previous_rabbit_button = None
        self.next_rabbit_button = None
        self.the_rabbit = None
        self.checkboxes = {}
        self.profile_elements = {}

    def handle_event(self, event):

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:

            if game.switches['window_open']:
                pass
            elif event.ui_element == self.back_button:
                self.close_current_tab()
                self.change_screen(game.last_screen_forProfile)
            elif event.ui_element == self.previous_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.previous_rabbit), Rabbit):
                    self.clear_profile()
                    game.switches['rabbit'] = self.previous_rabbit
                    self.build_profile()
                    self.update_disabled_buttons_and_text()
                else:
                    print("invalid previous rabbit", self.previous_rabbit)
            elif event.ui_element == self.next_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.next_rabbit), Rabbit):
                    self.clear_profile()
                    game.switches['rabbit'] = self.next_rabbit
                    self.build_profile()
                    self.update_disabled_buttons_and_text()
                else:
                    print("invalid next rabbit", self.previous_rabbit)
            elif event.ui_element == self.inspect_button:
                self.close_current_tab()
                self.change_screen("sprite inspect screen")
            elif event.ui_element == self.relations_tab_button:
                self.toggle_relations_tab()
            elif event.ui_element == self.roles_tab_button:
                self.toggle_roles_tab()
            elif event.ui_element == self.personal_tab_button:
                self.toggle_personal_tab()
            elif event.ui_element == self.dangerous_tab_button:
                self.toggle_dangerous_tab()
            elif event.ui_element == self.backstory_tab_button:
                if self.open_sub_tab is None:
                    if game.switches['favorite_sub_tab'] is None:
                        self.open_sub_tab = 'life events'
                    else:
                        self.open_sub_tab = game.switches['favorite_sub_tab']

                self.toggle_history_tab()
            elif event.ui_element == self.conditions_tab_button:
                self.toggle_conditions_tab()
            elif "chief_rabbit_ceremony" in self.profile_elements and \
                    event.ui_element == self.profile_elements["chief_rabbit_ceremony"]:
                self.change_screen('ceremony screen')
            elif event.ui_element == self.profile_elements["med_den"]:
                self.change_screen('med den screen')
            elif "mediation" in self.profile_elements and event.ui_element == self.profile_elements["mediation"]:
                self.change_screen('mediation screen')
            elif event.ui_element == self.profile_elements["favourite_button"]:
                self.the_rabbit.favourite = False
                self.profile_elements["favourite_button"].hide()
                self.profile_elements["not_favourite_button"].show()
            elif event.ui_element == self.profile_elements["not_favourite_button"]:
                self.the_rabbit.favourite = True
                self.profile_elements["favourite_button"].show()
                self.profile_elements["not_favourite_button"].hide()
            else:
                self.handle_tab_events(event)

            if game.switches['window_open']:
                pass

        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if game.switches['window_open']:
                pass

            elif event.key == pygame.K_LEFT:
                self.clear_profile()
                game.switches['rabbit'] = self.previous_rabbit
                self.build_profile()
                self.update_disabled_buttons_and_text()
            elif event.key == pygame.K_RIGHT:
                self.clear_profile()
                game.switches['rabbit'] = self.next_rabbit
                self.build_profile()
                self.update_disabled_buttons_and_text()
            
            elif event.key == pygame.K_ESCAPE:
                self.close_current_tab()
                self.change_screen(game.last_screen_forProfile)

    def handle_tab_events(self, event):
        # Relations Tab
        if self.open_tab == 'relations':
            if event.ui_element == self.family_tree_button:
                self.change_screen('see kittens screen')
            elif event.ui_element == self.see_relationships_button:
                self.change_screen('relationship screen')
            elif event.ui_element == self.choose_mate_button:
                self.change_screen('choose mate screen')
            elif event.ui_element == self.change_adoptive_parent_button:
                self.change_screen('choose adoptive parent screen')

        # Roles Tab
        elif self.open_tab == 'roles':
            if event.ui_element == self.manage_roles:
                self.change_screen('role screen')
            elif event.ui_element == self.change_rusasirah_button:
                self.change_screen('choose rusasirah screen')
        # Personal Tab
        elif self.open_tab == 'personal':
            if event.ui_element == self.change_name_button:
                ChangeRabbitName(self.the_rabbit)
            elif event.ui_element == self.specify_gender_button:
                SpecifyRabbitGender(self.the_rabbit)
                '''if self.the_rabbit.genderalign in ["doe", "trans doe"]:
                    self.the_rabbit.pronouns = [self.the_rabbit.default_pronouns[1].copy()]
                elif self.the_rabbit.genderalign in ["buck", "trans buck"]:
                    self.the_rabbit.pronouns = [self.the_rabbit.default_pronouns[2].copy()]
                else: self.the_rabbit.pronouns = [self.the_rabbit.default_pronouns[0].copy()]'''
            #when button is pressed...
            elif event.ui_element == self.cis_trans_button:
                #if the rabbit is anything besides m/f/transm/transf then turn them back to cis
                if self.the_rabbit.genderalign not in ["doe", "trans doe", "buck", "trans buck"]:
                    self.the_rabbit.genderalign = self.the_rabbit.gender
                elif self.the_rabbit.gender == "buck" and self.the_rabbit.genderalign == 'doe':
                    self.the_rabbit.genderalign = self.the_rabbit.gender
                elif self.the_rabbit.gender == "doe" and self.the_rabbit.genderalign == 'buck':
                    self.the_rabbit.genderalign = self.the_rabbit.gender
                #if the rabbit is cis (gender & gender align are the same) then set them to trans
                #cis bucks -> trans doe first
                elif self.the_rabbit.gender == "buck" and self.the_rabbit.genderalign == 'buck':
                    self.the_rabbit.genderalign = 'trans doe'
                #cis does -> trans buck
                elif self.the_rabbit.gender == "doe" and self.the_rabbit.genderalign == 'doe':
                    self.the_rabbit.genderalign = 'trans buck'
                #if the rabbit is trans then set them to nonbinary
                elif self.the_rabbit.genderalign in ["trans doe", "trans buck"]:
                    self.the_rabbit.genderalign = 'nonbinary'
                '''#pronoun handler
                if self.the_rabbit.genderalign in ["doe", "trans doe"]:
                    self.the_rabbit.pronouns = [self.the_rabbit.default_pronouns[1].copy()]
                elif self.the_rabbit.genderalign in ["buck", "trans buck"]:
                    self.the_rabbit.pronouns = [self.the_rabbit.default_pronouns[2].copy()]
                elif self.the_rabbit.genderalign in ["nonbinary"]:
                    self.the_rabbit.pronouns = [self.the_rabbit.default_pronouns[0].copy()]
                elif self.the_rabbit.genderalign not in ["doe", "trans doe", "buck", "trans buck"]:
                    self.the_rabbit.pronouns = [self.the_rabbit.default_pronouns[0].copy()]'''
                self.clear_profile()
                self.build_profile()
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.rabbit_toggles_button:
                ChangeRabbitToggles(self.the_rabbit)
        # Dangerous Tab
        elif self.open_tab == 'dangerous':
            if event.ui_element == self.kill_rabbit_button:
                KillRabbit(self.the_rabbit)
            elif event.ui_element == self.exile_rabbit_button:
                if not self.the_rabbit.dead and not self.the_rabbit.exiled:
                    Rabbit.exile(self.the_rabbit)
                    self.clear_profile()
                    self.build_profile()
                    self.update_disabled_buttons_and_text()
                if self.the_rabbit.dead:
                    if self.the_rabbit.df is True:
                        self.the_rabbit.outside, self.the_rabbit.exiled = False, False
                        self.the_rabbit.df = False
                        game.warren.add_to_inle(self.the_rabbit)
                        self.the_rabbit.thought = "Is relieved to once again graze in Inlé"
                    else:
                        self.the_rabbit.outside, self.the_rabbit.exiled = False, False
                        self.the_rabbit.df = True
                        game.warren.add_to_darkforest(self.the_rabbit)
                        self.the_rabbit.thought = "Is distraught after being cast out from the light of Frith"

                self.clear_profile()
                self.build_profile()
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.destroy_accessory_button:
                self.the_rabbit.pelt.accessory = None
                self.clear_profile()
                self.build_profile()
                self.update_disabled_buttons_and_text()
        # History Tab
        elif self.open_tab == 'history':
            if event.ui_element == self.sub_tab_1:
                if self.open_sub_tab == 'user notes':
                    self.notes_entry.kill()
                    self.display_notes.kill()
                    if self.edit_text:
                        self.edit_text.kill()
                    if self.save_text:
                        self.save_text.kill()
                    self.help_button.kill()
                self.open_sub_tab = 'life events'
                self.toggle_history_sub_tab()
            elif event.ui_element == self.sub_tab_2:
                if self.open_sub_tab == 'life events':
                    self.history_text_box.kill()
                self.open_sub_tab = 'user notes'
                self.toggle_history_sub_tab()
            elif event.ui_element == self.fav_tab:
                game.switches['favorite_sub_tab'] = None
                self.fav_tab.hide()
                self.not_fav_tab.show()
            elif event.ui_element == self.not_fav_tab:
                game.switches['favorite_sub_tab'] = self.open_sub_tab
                self.fav_tab.show()
                self.not_fav_tab.hide()
            elif event.ui_element == self.save_text:
                self.user_notes = sub(r"[^A-Za-z0-9<->/.()*'&#!?,| ]+", "", self.notes_entry.get_text())
                self.save_user_notes()
                self.editing_notes = False
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.edit_text:
                self.editing_notes = True
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.no_months:
                game.switches["show_history_months"] = True
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.show_months:
                game.switches["show_history_months"] = False
                self.update_disabled_buttons_and_text()

        # Conditions Tab
        elif self.open_tab == 'conditions':
            if event.ui_element == self.right_conditions_arrow:
                self.conditions_page += 1
                self.display_conditions_page()
            if event.ui_element == self.left_conditions_arrow:
                self.conditions_page -= 1
                self.display_conditions_page()

    def screen_switches(self):
        self.the_rabbit = Rabbit.all_rabbits.get(game.switches['rabbit'])

        # Set up the menu buttons, which appear on all rabbit profile images.
        self.next_rabbit_button = UIImageButton(scale(pygame.Rect((1244, 50), (306, 60))), "", object_id="#next_rabbit_button"
                                             , manager=MANAGER)
        self.previous_rabbit_button = UIImageButton(scale(pygame.Rect((50, 50), (306, 60))), "",
                                                 object_id="#previous_rabbit_button"
                                                 , manager=MANAGER)
        self.back_button = UIImageButton(scale(pygame.Rect((50, 120), (210, 60))), "", object_id="#back_button"
                                         , manager=MANAGER)
        self.inspect_button = UIImageButton(scale(pygame.Rect((1482, 120),(68,68))), "", 
                                            object_id="#magnify_button",
                                            manager=MANAGER)
        self.relations_tab_button = UIImageButton(scale(pygame.Rect((96, 840), (352, 60))), "",
                                                  object_id="#relations_tab_button", manager=MANAGER)
        self.roles_tab_button = UIImageButton(scale(pygame.Rect((448, 840), (352, 60))), "",
                                              object_id="#roles_tab_button"
                                              , manager=MANAGER)
        self.personal_tab_button = UIImageButton(scale(pygame.Rect((800, 840), (352, 60))), "",
                                                 object_id="#personal_tab_button", manager=MANAGER)
        self.dangerous_tab_button = UIImageButton(scale(pygame.Rect((1152, 840), (352, 60))), "",
                                                  object_id="#dangerous_tab_button", manager=MANAGER)

        self.backstory_tab_button = UIImageButton(scale(pygame.Rect((96, 1244), (352, 60))), "",
                                                  object_id="#backstory_tab_button", manager=MANAGER)

        self.conditions_tab_button = UIImageButton(
            scale(pygame.Rect((448, 1244), (352, 60))),
            "",
            object_id="#conditions_tab_button", manager=MANAGER
        )

        self.placeholder_tab_3 = UIImageButton(scale(pygame.Rect((800, 1244), (352, 60))), "",
                                               object_id="#rabbit_tab_3_blank_button", starting_height=1, manager=MANAGER)
        self.placeholder_tab_3.disable()

        self.placeholder_tab_4 = UIImageButton(scale(pygame.Rect((1152, 1244), (352, 60))), "",
                                               object_id="#rabbit_tab_4_blank_button", manager=MANAGER)
        self.placeholder_tab_4.disable()

        self.build_profile()

        self.hide_menu_buttons()  # Menu buttons don't appear on the profile screen
        if game.last_screen_forProfile == 'med den screen':
            self.toggle_conditions_tab()

    def clear_profile(self):
        """Clears all profile objects. """
        for ele in self.profile_elements:
            self.profile_elements[ele].kill()
        self.profile_elements = {}

        if self.user_notes:
            self.user_notes = 'Click the check mark to enter notes about your rabbit!'

        for box in self.checkboxes:
            self.checkboxes[box].kill()
        self.checkboxes = {}

    def exit_screen(self):
        self.clear_profile()
        self.back_button.kill()
        self.next_rabbit_button.kill()
        self.previous_rabbit_button.kill()
        self.relations_tab_button.kill()
        self.roles_tab_button.kill()
        self.personal_tab_button.kill()
        self.dangerous_tab_button.kill()
        self.backstory_tab_button.kill()
        self.conditions_tab_button.kill()
        self.placeholder_tab_3.kill()
        self.placeholder_tab_4.kill()
        self.inspect_button.kill()
        self.close_current_tab()

    def build_profile(self):
        """Rebuild builds the rabbit profile. Run when you switch rabbits
            or for changes in the profile."""
        self.the_rabbit = Rabbit.all_rabbits.get(game.switches["rabbit"])

        # use these attributes to create differing profiles for Inle rabbits etc.
        is_sc_instructor = False
        is_df_instructor = False
        if self.the_rabbit is None:
            return
        if self.the_rabbit.dead and game.warren.instructor.ID == self.the_rabbit.ID and self.the_rabbit.df is False:
            is_sc_instructor = True
        elif self.the_rabbit.dead and game.warren.instructor.ID == self.the_rabbit.ID and self.the_rabbit.df is True:
            is_df_instructor = True

        # Info in string
        rabbit_name = str(self.the_rabbit.name)
        rabbit_name = shorten_text_to_fit(rabbit_name, 425, 40)
        if self.the_rabbit.dead:
            rabbit_name += " (dead)"  # A dead rabbit will have the (dead) sign next to their name
        if is_sc_instructor:
            self.the_rabbit.thought = "Hello. I am here to guide the dead rabbits of " + game.warren.name + " into Inlé."
        if is_df_instructor:
            self.the_rabbit.thought = "I am here to drag the dead rabbits of " + game.warren.name + " into the lightless lands."


        self.profile_elements["rabbit_name"] = pygame_gui.elements.UITextBox(rabbit_name,
                                                                          scale(pygame.Rect((50, 280), (-1, 80))),
                                                                          object_id=get_text_box_theme(
                                                                              "#text_box_40_horizcenter"),
                                                                          manager=MANAGER)
        name_text_size = self.profile_elements["rabbit_name"].get_relative_rect()

        self.profile_elements["rabbit_name"].kill()

        self.profile_elements["rabbit_name"] = pygame_gui.elements.UITextBox(rabbit_name,
                                                                          scale(pygame.Rect(
                                                                              (800 - name_text_size.width, 280),
                                                                              (name_text_size.width * 2, 80))),
                                                                          object_id=get_text_box_theme(
                                                                              "#text_box_40_horizcenter"),
                                                                          manager=MANAGER)

        # Write rabbit thought
        self.profile_elements["rabbit_thought"] = pygame_gui.elements.UITextBox(self.the_rabbit.thought,
                                                                             scale(pygame.Rect((200, 340), (1200, 80))),
                                                                             wrap_to_height=True,
                                                                             object_id=get_text_box_theme(
                                                                                 "#text_box_30_horizcenter_spacing_95")
                                                                             , manager=MANAGER)

        self.profile_elements["rabbit_info_column1"] = UITextBoxTweaked(self.generate_column1(self.the_rabbit),
                                                                     scale(pygame.Rect((600, 460), (360, 380))),
                                                                     object_id=get_text_box_theme(
                                                                         "#text_box_22_horizleft"),
                                                                     line_spacing=0.95, manager=MANAGER)
        self.profile_elements["rabbit_info_column2"] = UITextBoxTweaked(self.generate_column2(self.the_rabbit),
                                                                     scale(pygame.Rect((980, 460), (500, 360))),
                                                                     object_id=get_text_box_theme(
                                                                         "#text_box_22_horizleft"),
                                                                     line_spacing=0.95, manager=MANAGER)

        # Set the rabbit backgrounds.
        if game.warren.warren_settings['backgrounds']:
            self.profile_elements["background"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((110, 400), (480, 420))),
                pygame.transform.scale(self.get_platform(), scale_dimentions((480, 420))), 
                manager=MANAGER)
            self.profile_elements["background"].disable()

        # Create rabbit image object
        self.profile_elements["rabbit_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((200, 400), (300, 300))),

                                                                         pygame.transform.scale(
                                                                             self.the_rabbit.sprite,
                                                                             (300, 300)), manager=MANAGER)
        self.profile_elements["rabbit_image"].disable()

        # if rabbit is a med or med app, show button for their den
        self.profile_elements["med_den"] = UIImageButton(scale(pygame.Rect
                                                               ((200, 760), (302, 56))),
                                                         "",
                                                         object_id="#med_den_button",
                                                         manager=MANAGER,
                                                         starting_height=2)
        if not (self.the_rabbit.dead or self.the_rabbit.outside) and (
                self.the_rabbit.status in ['healer' 'healer rusasi'] or
                self.the_rabbit.is_ill() or
                self.the_rabbit.is_injured()):
            self.profile_elements["med_den"].show()
        else:
            self.profile_elements["med_den"].hide()

        # Fullscreen
        if game.settings['fullscreen']:
            x_pos = 745 - name_text_size.width//2
        else:
            x_pos = 740 - name_text_size.width

        self.profile_elements["favourite_button"] = UIImageButton(scale(pygame.Rect
                                                                        ((x_pos, 287), (56, 56))),
                                                                  "",
                                                                  object_id="#fav_rabbit",
                                                                  manager=MANAGER,
                                                                  tool_tip_text='Remove favorite status',
                                                                  starting_height=2)

        self.profile_elements["not_favourite_button"] = UIImageButton(scale(pygame.Rect
                                                                            ((x_pos, 287),
                                                                             (56, 56))),
                                                                      "",
                                                                      object_id="#not_fav_rabbit",
                                                                      manager=MANAGER,
                                                                      tool_tip_text='Mark as favorite',
                                                                      starting_height=2)

        if self.the_rabbit.favourite:
            self.profile_elements["favourite_button"].show()
            self.profile_elements["not_favourite_button"].hide()
        else:
            self.profile_elements["favourite_button"].hide()
            self.profile_elements["not_favourite_button"].show()

        # Determine where the next and previous rabbit buttons lead
        self.determine_previous_and_next_rabbit()

        # Disable and enable next and previous rabbit buttons as needed.
        if self.next_rabbit == 0:
            self.next_rabbit_button.disable()
        else:
            self.next_rabbit_button.enable()

        if self.previous_rabbit == 0:
            self.previous_rabbit_button.disable()
        else:
            self.previous_rabbit_button.enable()

        if self.open_tab == "history" and self.open_sub_tab == 'user notes':
            self.load_user_notes()

        if self.the_rabbit.status == 'chief rabbit' and not self.the_rabbit.dead:
            self.profile_elements["mediation"] = UIImageButton(scale(pygame.Rect(
                (766, 220), (68, 68))),
                "",
                object_id="#mediation_button", manager=MANAGER
            )
            if self.the_rabbit.dead or self.the_rabbit.outside:
                self.profile_elements["mediation"].disable()

    def determine_previous_and_next_rabbit(self):
        """'Determines where the next and previous buttons point too."""

        is_instructor = False
        if self.the_rabbit.dead and game.warren.instructor.ID == self.the_rabbit.ID:
            is_instructor = True

        previous_rabbit = 0
        next_rabbit = 0
        current_rabbit_found = 0
        if self.the_rabbit.dead and not is_instructor and self.the_rabbit.df == game.warren.instructor.df and \
                not (self.the_rabbit.outside or self.the_rabbit.exiled):
            previous_rabbit = game.warren.instructor.ID

        if is_instructor:
            current_rabbit_found = 1

        for check_rabbit in Rabbit.all_rabbits_list:
            if check_rabbit.ID == self.the_rabbit.ID:
                current_rabbit_found = 1
            else:
                if current_rabbit_found == 0 and check_rabbit.ID != self.the_rabbit.ID and check_rabbit.dead == self.the_rabbit.dead \
                        and check_rabbit.ID != game.warren.instructor.ID and check_rabbit.outside == self.the_rabbit.outside and \
                        check_rabbit.df == self.the_rabbit.df and not check_rabbit.faded:
                    previous_rabbit = check_rabbit.ID

                elif current_rabbit_found == 1 and check_rabbit != self.the_rabbit.ID and check_rabbit.dead == self.the_rabbit.dead \
                        and check_rabbit.ID != game.warren.instructor.ID and check_rabbit.outside == self.the_rabbit.outside and \
                        check_rabbit.df == self.the_rabbit.df and not check_rabbit.faded:
                    next_rabbit = check_rabbit.ID
                    break

                elif int(next_rabbit) > 1:
                    break

        if next_rabbit == 1:
            next_rabbit = 0

        self.next_rabbit = next_rabbit
        self.previous_rabbit = previous_rabbit

    def generate_column1(self, the_rabbit):
        """Generate the left column information"""
        output = ""
        # SEX/GENDER
        if the_rabbit.genderalign is None or the_rabbit.genderalign == the_rabbit.gender:
            output += str(the_rabbit.gender)
        else:
            output += str(the_rabbit.genderalign)
        # NEWLINE ----------
        output += "\n"

        # AGE
        if the_rabbit.age == 'kitten':
            output += 'young'
        elif the_rabbit.age == 'senior':
            output += 'senior'
        else:
            output += the_rabbit.age
        # NEWLINE ----------
        output += "\n"

        # EYE COLOR
        output += 'eyes: ' + str(the_rabbit.describe_eyes())
        # NEWLINE ----------
        output += "\n"

        # PELT TYPE
        output += 'pelt: ' + the_rabbit.pelt.name.lower()
        # NEWLINE ----------
        output += "\n"

        # PELT LENGTH
        output += 'fur length: ' + the_rabbit.pelt.length
        # NEWLINE ----------

        # ACCESSORY
        if the_rabbit.pelt.accessory:
            output += "\n"
            output += 'accessory: ' + str(ACC_DISPLAY[the_rabbit.pelt.accessory]["default"])
            # NEWLINE ----------

        # PARENTS
        all_parents = [Rabbit.fetch_rabbit(i) for i in the_rabbit.get_parents()]
        if all_parents: 
            output += "\n"
            if len(all_parents) == 1:
                output += "parent: " + str(all_parents[0].name)
            elif len(all_parents) > 2:
                output += "parents: " + ", ".join([str(i.name) for i in all_parents[:2]]) + f", and {len(all_parents) - 2} "
                if len(all_parents) - 2 == 1:
                    output += "other"
                else:
                    output += "others"
            else:
                output += "parents: " + ", ".join([str(i.name) for i in all_parents])

        
        # MOONS
        output += "\n"
        if the_rabbit.dead:
            output += str(the_rabbit.months)
            if the_rabbit.months == 1:
                output += ' month (in life)\n'
            elif the_rabbit.months != 1:
                output += ' months (in life)\n'

            output += str(the_rabbit.dead_for)
            if the_rabbit.dead_for == 1:
                output += ' month (in death)'
            elif the_rabbit.dead_for != 1:
                output += ' months (in death)'
        else:
            output += str(the_rabbit.months)
            if the_rabbit.months == 1:
                output += ' month'
            elif the_rabbit.months != 1:
                output += ' months'

        # MATE
        if len(the_rabbit.mate) > 0:
            output += "\n"
            
            
            mate_names = []
            # Grab the names of only the first two, since that's all we will display
            for _m in the_rabbit.mate[:2]:
                mate_ob = Rabbit.fetch_rabbit(_m)
                if not isinstance(mate_ob, Rabbit):
                    continue
                if mate_ob.dead != self.the_rabbit.dead:
                    if the_rabbit.dead:
                        former_indirabbite = "(living)"
                    else:
                        former_indirabbite = "(dead)"
                    
                    mate_names.append(f"{str(mate_ob.name)} {former_indirabbite}")
                elif mate_ob.outside != self.the_rabbit.outside:
                    mate_names.append(f"{str(mate_ob.name)} (away)")
                else:
                    mate_names.append(f"{str(mate_ob.name)}")
                    
            if len(the_rabbit.mate) == 1:
                output += "mate: " 
            else:
                output += "mates: "
            
            output += ", ".join(mate_names)
            
            if len(the_rabbit.mate) > 2:
                output += f", and {len(the_rabbit.mate) - 2}"
                if len(the_rabbit.mate) - 2 > 1:
                    output += " others"
                else:
                    output += " other"

        if not the_rabbit.dead:
            # NEWLINE ----------
            output += "\n"

        return output

    def generate_column2(self, the_rabbit):
        """Generate the right column information"""
        output = ""

        # STATUS
        if the_rabbit.outside and not the_rabbit.exiled and the_rabbit.status not in ['pet', 'hlessi', 'rogue',
                                                                             'defector']:
            output += "<font color='#FF0000'>lost</font>"
        elif the_rabbit.exiled:
            output += "<font color='#FF0000'>exiled</font>"
        elif the_rabbit.status == "healer rusasi":
            output += "healer's apprentice"
        elif the_rabbit.status == "owsla rusasi":
            output += "owsla trainee"
        else:
            output += the_rabbit.status

            # NEWLINE ----------
        output += "\n"

        # MENTOR
        # Only shows up if the rabbit has a rusasirah.
        if the_rabbit.rusasirah:
            rusasirah_ob = Rabbit.fetch_rabbit(the_rabbit.rusasirah)
            if rusasirah_ob:
                output += "rusasirah: " + str(rusasirah_ob.name) + "\n"

        # CURRENT APPRENTICES
        # Optional - only shows up if the rabbit has an rusasi currently
        if the_rabbit.rusasi:
            app_count = len(the_rabbit.rusasi)
            if app_count == 1 and Rabbit.fetch_rabbit(the_rabbit.rusasi[0]):
                output += 'favored rusasi: ' + str(Rabbit.fetch_rabbit(the_rabbit.rusasi[0]).name)
            elif app_count > 1:
                output += 'favored rusasi: ' + ", ".join([str(Rabbit.fetch_rabbit(i).name) for i in the_rabbit.rusasi if Rabbit.fetch_rabbit(i)])

            # NEWLINE ----------
            output += "\n"

        # FORMER APPRENTICES
        # Optional - Only shows up if the rabbit has previous rusasi(s)
        if the_rabbit.former_rusasis:
            
            rusasi = [Rabbit.fetch_rabbit(i) for i in the_rabbit.former_rusasis if isinstance(Rabbit.fetch_rabbit(i), Rabbit)]
            
            if len(rusasi) > 2:
                output += 'grown rusasi: ' + ", ".join([str(i.name) for i in rusasi[:2]]) + \
                    ", and " + str(len(rusasi) - 2) 
                if len(rusasi) - 2 > 1:
                    output += " others"
                else:
                    output += " other"
            else:
                if len(rusasi) > 1:
                    output += 'grown rusasi: '
                else:
                    output += 'grown rusasi: '
                output += ", ".join(str(i.name) for i in rusasi)

            # NEWLINE ----------
            output += "\n"

        # CHARACTER TRAIT
        output += the_rabbit.personality.trait
        # NEWLINE ----------
        output += "\n"

        # RABBIT SKILLS
        output += the_rabbit.skills.skill_string()
        # NEWLINE ----------
        output += "\n"

        # EXPERIENCE
        output += 'experience: ' + str(the_rabbit.experience_level)

        if game.warren.warren_settings['showxp']:
            output += ' (' + str(the_rabbit.experience) + ')'
        # NEWLINE ----------
        output += "\n"

        # BACKSTORY
        bs_text = 'this should not appear'
        if the_rabbit.status in ['pet', 'hlessi', 'rogue', 'defector']:
            bs_text = the_rabbit.status
        else:
            if the_rabbit.backstory:
                #print(the_rabbit.backstory)
                for category in BACKSTORIES["backstory_categories"]:
                    if the_rabbit.backstory in BACKSTORIES["backstory_categories"][category]:
                        bs_text = BACKSTORIES["backstory_display"][category]
                        break
            else:
                bs_text = 'warrenborn'
        output += f"backstory: {bs_text}"
        # NEWLINE ----------
        output += "\n"

        # NUTRITION INFO (if the game is in the correct mode)
        if game.warren.game_mode in ["expanded", "cruel season"] and the_rabbit.is_alive() and FRESHKILL_ACTIVE:
            nutr = None
            if the_rabbit.ID in game.warren.freshkill_pile.nutrition_info:
                nutr = game.warren.freshkill_pile.nutrition_info[the_rabbit.ID]
            if nutr:
                output += f"nutrition status: {round(nutr.percentage, 1)}%\n"
            else:
                output += f"nutrition status: 100%\n"

        if the_rabbit.is_disabled():
            for condition in the_rabbit.permanent_condition:
                if the_rabbit.permanent_condition[condition]['born_with'] is True and \
                        the_rabbit.permanent_condition[condition]["months_until"] != -2:
                    continue
                output += 'has a permanent condition'

                # NEWLINE ----------
                output += "\n"
                break

        if the_rabbit.is_injured():
            if "recovering from birth" in the_rabbit.injuries:
                output += 'recovering from birth!'
            elif "pregnant" in the_rabbit.injuries:
                output += 'pregnant!'
            else:
                output += "injured!"
        elif the_rabbit.is_ill():
            if "grief stricken" in the_rabbit.illnesses:
                output += 'grieving!'
            elif "fleas" in the_rabbit.illnesses:
                output += 'flea-ridden!'
            else:
                output += 'sick!'

        return output

    def toggle_history_tab(self, sub_tab_switch=False):
        """Opens the history tab
        param sub_tab_switch should be set to True if switching between sub tabs within the History tab
        """
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open at a time
        self.close_current_tab()

        if previous_open_tab == 'history' and sub_tab_switch is False:
            '''If the current open tab is history and we aren't switching between sub tabs,
             just close the tab and do nothing else. '''
            pass
        else:
            self.open_tab = 'history'
            self.backstory_background = pygame_gui.elements.UIImage(scale(pygame.Rect((178, 930), (1240, 314))),
                                                                    self.backstory_tab)
            self.backstory_background.disable()
            self.sub_tab_1 = UIImageButton(scale(pygame.Rect((1418, 950), (84, 60))), "", object_id="#sub_tab_1_button"
                                           , manager=MANAGER)
            self.sub_tab_1.disable()
            self.sub_tab_2 = UIImageButton(scale(pygame.Rect((1418, 1024), (84, 60))), "", object_id="#sub_tab_2_button"
                                           , manager=MANAGER)
            self.sub_tab_2.disable()
            self.sub_tab_3 = UIImageButton(scale(pygame.Rect((1418, 1098), (84, 60))), "", object_id="#sub_tab_3_button"
                                           , manager=MANAGER)
            self.sub_tab_3.disable()
            self.sub_tab_4 = UIImageButton(scale(pygame.Rect((1418, 1172), (84, 60))), "", object_id="#sub_tab_4_button"
                                           , manager=MANAGER)
            self.sub_tab_4.disable()
            self.fav_tab = UIImageButton(
                scale(pygame.Rect((105, 960), (56, 56))),
                "",
                object_id="#fav_star",
                tool_tip_text='un-favorite this sub tab',
                manager=MANAGER
            )
            self.not_fav_tab = UIImageButton(
                scale(pygame.Rect((105, 960), (56, 56))),
                "",
                object_id="#not_fav_star",
                tool_tip_text='favorite this sub tab - it will be the default sub tab displayed when History is viewed',
                manager=MANAGER
            )

            if self.open_sub_tab != 'life events':
                self.toggle_history_sub_tab()
            else:
                # This will be overwritten in update_disabled_buttons_and_text()
                self.history_text_box = pygame_gui.elements.UITextBox("", scale(pygame.Rect((80, 480), (615, 142)))
                                                                      , manager=MANAGER)
                self.no_months = UIImageButton(scale(pygame.Rect(
                    (104, 1028), (68, 68))),
                    "",
                    object_id="#unchecked_checkbox",
                    tool_tip_text='Show the month that certain history events occurred on', manager=MANAGER
                )
                self.show_months = UIImageButton(scale(pygame.Rect(
                    (104, 1028), (68, 68))),
                    "",
                    object_id="#checked_checkbox",
                    tool_tip_text='Stop showing the month that certain history events occurred on', manager=MANAGER
                )

                self.update_disabled_buttons_and_text()

    def toggle_user_notes_tab(self):
        """Opens the User Notes portion of the History Tab"""
        self.load_user_notes()
        if self.user_notes is None:
            self.user_notes = 'Click the check mark to enter notes about your rabbit!'

        self.notes_entry = pygame_gui.elements.UITextEntryBox(
            scale(pygame.Rect((200, 946), (1200, 298))),
            initial_text=self.user_notes,
            object_id='#text_box_26_horizleft_pad_10_14',
            manager=MANAGER
        )

        self.display_notes = UITextBoxTweaked(self.user_notes,
                                              scale(pygame.Rect((200, 946), (120, 298))),
                                              object_id="#text_box_26_horizleft_pad_10_14",
                                              line_spacing=1, manager=MANAGER)

        self.update_disabled_buttons_and_text()

    def save_user_notes(self):
        """Saves user-entered notes. """
        warrenname = game.warren.name

        notes = self.user_notes

        notes_directory = get_save_dir() + '/' + warrenname + '/notes'
        notes_file_path = notes_directory + '/' + self.the_rabbit.ID + '_notes.json'

        if not os.path.exists(notes_directory):
            os.makedirs(notes_directory)

        if notes is None or notes == 'Click the check mark to enter notes about your rabbit!':
            return

        new_notes = {str(self.the_rabbit.ID): notes}

        game.safe_save(notes_file_path, new_notes)

    def load_user_notes(self):
        """Loads user-entered notes. """
        warrenname = game.warren.name

        notes_directory = get_save_dir() + '/' + warrenname + '/notes'
        notes_file_path = notes_directory + '/' + self.the_rabbit.ID + '_notes.json'

        if not os.path.exists(notes_file_path):
            return

        try:
            with open(notes_file_path, 'r') as read_file:
                rel_data = ujson.loads(read_file.read())
                self.user_notes = 'Click the check mark to enter notes about your rabbit!'
                if str(self.the_rabbit.ID) in rel_data:
                    self.user_notes = rel_data.get(str(self.the_rabbit.ID))
        except Exception as e:
            print(f"ERROR: there was an error reading the Notes file of rabbit #{self.the_rabbit.ID}.\n", e)

    def toggle_history_sub_tab(self):
        """To toggle the history-sub-tab"""

        if self.open_sub_tab == 'life events':
            self.toggle_history_tab(sub_tab_switch=True)

        elif self.open_sub_tab == 'user notes':
            self.toggle_user_notes_tab()

    def get_all_history_text(self):
        """Generates a string with all important history information."""
        output = ""
        if self.open_sub_tab == 'life events':
            # start our history with the backstory, since all rabbits get one
            if self.the_rabbit.status not in ["rogue", "pet", "hlessi", "defector"]:
                life_history = [str(self.get_backstory_text())]
            else:
                life_history = []

            # now get rusasihip history and add that if any exists
            app_history = self.get_rusasihip_text()
            if app_history:
                life_history.append(app_history)
                
            #Get rusasirahhip text if it exists
            rusasirah_history = self.get_rusasirahhip_text()
            if rusasirah_history:
                life_history.append(rusasirah_history)

            # now go get the scar history and add that if any exists
            body_history = []
            scar_history = self.get_scar_text()
            if scar_history:
                body_history.append(scar_history)
            death_history = self.get_death_text()
            if death_history:
                body_history.append(death_history)
            # join scar and death into one paragraph
            if body_history:
                life_history.append(" ".join(body_history))

            murder = self.get_murder_text()
            if murder:
                life_history.append(murder)

            # join together history list with line breaks
            output = '\n\n'.join(life_history)
        return output

    def get_backstory_text(self):
        """
        returns the backstory blurb
        """
        rabbit_dict = {
            "m_c": (str(self.the_rabbit.name), choice(self.the_rabbit.pronouns))
        }
        bs_blurb = None
        if self.the_rabbit.backstory:
            bs_blurb = BACKSTORIES["backstories"][self.the_rabbit.backstory]
        if self.the_rabbit.status in ['pet', 'hlessi', 'rogue', 'defector']:
            bs_blurb = f"This rabbit is a {self.the_rabbit.status} and currently resides outside of the warrens."

        if bs_blurb is not None:
            adjust_text = str(bs_blurb).replace('This rabbit', str(self.the_rabbit.name))
            text = adjust_text
        else:
            text = str(self.the_rabbit.name) + " was born into the warren where {PRONOUN/m_c/subject} currently reside."

        beginning = History.get_beginning(self.the_rabbit)
        if beginning:
            if beginning['warren_born']:
                text += " {PRONOUN/m_c/subject/CAP} {VERB/m_c/were/was} born on month " + str(
                    beginning['month']) + " during " + str(beginning['birth_season']) + "."
            else:
                text += " {PRONOUN/m_c/subject/CAP} joined the warren on month " + str(
                    beginning['month']) + " at the age of " + str(beginning['age']) + " months."

        text = process_text(text, rabbit_dict)
        return text

    def get_scar_text(self):
        """
        returns the adjusted scar text
        """
        scar_text = []
        scar_history = History.get_death_or_scars(self.the_rabbit, scar=True)
        if game.switches['show_history_months']:
            months = True
        else:
            months = False

        if scar_history:
            i = 0
            for scar in scar_history:
                # base adjustment to get the rabbit's name and months if needed
                new_text = (event_text_adjust(Rabbit,
                                              scar["text"],
                                              self.the_rabbit,
                                              Rabbit.fetch_rabbit(scar["involved"])))
                if months:
                    new_text += f" (Month {scar['month']})"

                # checking to see if we can throw out a duplirabbite
                if new_text in scar_text:
                    i += 1
                    continue

                # the first event keeps the rabbit's name, consecutive events get to switch it up a bit
                if i != 0:
                    sentence_beginners = [
                        "This rabbit",
                        "Then {PRONOUN/m_c/subject} {VERB/m_c/were/was}",
                        "{PRONOUN/m_c/subject/CAP} {VERB/m_c/were/was} also",
                        "Also, {PRONOUN/m_c/subject} {VERB/m_c/were/was}",
                        "As well as",
                        "{PRONOUN/m_c/subject/CAP} {VERB/m_c/were/was} then"
                    ]
                    chosen = choice(sentence_beginners)
                    if chosen == 'This rabbit':
                        new_text = new_text.replace(str(self.the_rabbit.name), chosen, 1)
                    else:
                        new_text = new_text.replace(f"{self.the_rabbit.name} was", f"{chosen}", 1)
                rabbit_dict = {
                    "m_c": (str(self.the_rabbit.name), choice(self.the_rabbit.pronouns))
                }
                new_text = process_text(new_text, rabbit_dict)
                scar_text.append(new_text)
                i += 1

            scar_history = ' '.join(scar_text)

        return scar_history

    def get_rusasihip_text(self):
        """
        returns adjusted rusasihip history text (rusasirah influence and app ceremony)
        """
        if self.the_rabbit.status in ['pet', 'hlessi', 'rogue', 'defector']:
            return ""

        rusasirah_influence = History.get_rusasirah_influence(self.the_rabbit)
        influence_history = ""
        
        #First, just list the rusasirah:
        if self.the_rabbit.status in ['kitten', 'newborn']:
                influence_history = 'This rabbit has not begun training.'
        elif self.the_rabbit.status in ['rusasi', 'healer rusasi', 'owsla rusasi']:
            influence_history = 'This rabbit has not finished training.'
        else:
            valid_formor_rusasirah = [Rabbit.fetch_rabbit(i) for i in self.the_rabbit.former_rusasisrah if 
                                    isinstance(Rabbit.fetch_rabbit(i), Rabbit)]
            if valid_formor_rusasirah:
                influence_history += "{PRONOUN/m_c/subject/CAP} {VERB/m_c/were/was} rusasirahed by "
                if len(valid_formor_rusasirah) > 1:
                    influence_history += ", ".join([str(i.name) for i in valid_formor_rusasirah[:-1]]) + " and " + \
                        str(valid_formor_rusasirah[-1].name) + ". "
                else:
                    influence_history += str(valid_formor_rusasirah[0].name) + ". "
            else:
                influence_history += "This rabbit either did not have a rusasirah, or {PRONOUN/m_c/poss} rusasirah is unknown. "
            
            # Second, do the facet/personality effect
            trait_influence = []
            if "trait" in rusasirah_influence and isinstance(rusasirah_influence["trait"], dict):
                for rusasirah in rusasirah_influence["trait"]:
                    #If the strings are not set (empty list), continue. 
                    if not rusasirah_influence["trait"][rusasirah].get("strings"):
                        continue
                    
                    ment_obj = Rabbit.fetch_rabbit(rusasirah)
                    #Continue of the rusasirah is invalid too.
                    if not isinstance(ment_obj, Rabbit):
                        continue
                    
                    if len(rusasirah_influence["trait"][rusasirah].get("strings")) > 1:
                        string_snippet = ", ".join(rusasirah_influence["trait"][rusasirah].get("strings")[:-1]) + \
                            " and " + rusasirah_influence["trait"][rusasirah].get("strings")[-1]
                    else:
                        string_snippet = rusasirah_influence["trait"][rusasirah].get("strings")[0]
                        
                    
                    trait_influence.append(str(ment_obj.name) +  \
                                        " influenced {PRONOUN/m_c/object} to be more likely to " + string_snippet + ". ")
                    
                    

            influence_history += " ".join(trait_influence)
            
            
            skill_influence = []
            if "skill" in rusasirah_influence and isinstance(rusasirah_influence["skill"], dict):
                for rusasirah in rusasirah_influence["skill"]:
                    #If the strings are not set (empty list), continue. 
                    if not rusasirah_influence["skill"][rusasirah].get("strings"):
                        continue
                    
                    ment_obj = Rabbit.fetch_rabbit(rusasirah)
                    #Continue of the rusasirah is invalid too.
                    if not isinstance(ment_obj, Rabbit):
                        continue
                    
                    if len(rusasirah_influence["skill"][rusasirah].get("strings")) > 1:
                        string_snippet = ", ".join(rusasirah_influence["skill"][rusasirah].get("strings")[:-1]) + \
                            " and " + rusasirah_influence["skill"][rusasirah].get("strings")[-1]
                    else:
                        string_snippet = rusasirah_influence["skill"][rusasirah].get("strings")[0]
                        
                    
                    skill_influence.append(str(ment_obj.name) +  \
                                        " helped {PRONOUN/m_c/object} become better at " + string_snippet + ". ")
                    
                    

            influence_history += " ".join(skill_influence)

        app_ceremony = History.get_app_ceremony(self.the_rabbit)

        graduation_history = ""
        if app_ceremony:
            graduation_history = "When {PRONOUN/m_c/subject} graduated, {PRONOUN/m_c/subject} {VERB/m_c/were/was} honored for {PRONOUN/m_c/poss} " +  app_ceremony['honor'] + "."

            grad_age = app_ceremony["graduation_age"]
            if int(grad_age) < 11:
                graduation_history += " {PRONOUN/m_c/poss/CAP} training went so well that {PRONOUN/m_c/subject} graduated early at " + str(
                    grad_age) + " months old."
            elif int(grad_age) > 13:
                graduation_history += " {PRONOUN/m_c/subject/CAP} graduated late at " + str(grad_age) + " months old."
            else:
                graduation_history += " {PRONOUN/m_c/subject/CAP} graduated at " + str(grad_age) + " months old."

            if game.switches['show_history_months']:
                graduation_history += f" (Month {app_ceremony['month']})"
        rabbit_dict = {
            "m_c": (str(self.the_rabbit.name), choice(self.the_rabbit.pronouns))
        }
        rusasihip_history = influence_history + " " + graduation_history
        rusasihip_history = process_text(rusasihip_history, rabbit_dict)
        return rusasihip_history


    def get_rusasirahhip_text(self):
        """
        
        returns full list of previously rusasirahed rusasi. 
        
        """
        
        text = ""
        # Doing this is two steps 
        all_real_rusasi = [Rabbit.fetch_rabbit(i) for i in self.the_rabbit.former_rusasis if isinstance(Rabbit.fetch_rabbit(i), Rabbit)]
        if all_real_rusasi:
            text = "{PRONOUN/m_c/subject/CAP} taught "
            if len(all_real_rusasi) > 2:
                text += ', '.join([str(i.name) for i in all_real_rusasi[:-1]]) + ", and " + str(all_real_rusasi[-1].name) + "."
            elif len(all_real_rusasi) == 2:
                text += str(all_real_rusasi[0].name) + " and " + str(all_real_rusasi[1].name) + "."
            elif len(all_real_rusasi) == 1:
                text += str(all_real_rusasi[0].name) + "."
            
            rabbit_dict = {
            "m_c": (str(self.the_rabbit.name), choice(self.the_rabbit.pronouns))
            }   
            
            text = process_text(text, rabbit_dict)
        
        return text
        

    def get_text_for_murder_event(self, event, death):
        ''' returns the adjusted murder history text for the victim '''
        if event["text"] == death["text"] and event["month"] == death["month"]:
            if event["revealed"] is True: 
                final_text = event_text_adjust(Rabbit, event["text"], self.the_rabbit, Rabbit.fetch_rabbit(death["involved"]))
                if event.get("revelation_text"):
                    final_text = final_text + event["revelation_text"]
                return final_text
            else:
                return event_text_adjust(Rabbit, event["unrevealed_text"], self.the_rabbit, Rabbit.fetch_rabbit(death["involved"]))
        return None


    def get_death_text(self):
        """
        returns adjusted death history text
        """
        text = None
        death_history = self.the_rabbit.history.get_death_or_scars(self.the_rabbit, death=True)
        murder_history = self.the_rabbit.history.get_murders(self.the_rabbit)
        if game.switches['show_history_months']:
            months = True
        else:
            months = False

        if death_history:
            all_deaths = []
            death_number = len(death_history)
            for index, death in enumerate(death_history):
                found_murder = False  # Add this line to track if a matching murder event is found
                if "is_victim" in murder_history:
                    for event in murder_history["is_victim"]:
                        text = self.get_text_for_murder_event(event, death)
                        if text is not None:
                            found_murder = True  # Update the flag if a matching murder event is found
                            break

                if found_murder and text is not None and not event["revealed"]:
                    text = event_text_adjust(Rabbit, event["unrevealed_text"], self.the_rabbit, Rabbit.fetch_rabbit(death["involved"]))
                elif not found_murder:
                    text = event_text_adjust(Rabbit, death["text"], self.the_rabbit, Rabbit.fetch_rabbit(death["involved"]))


                if self.the_rabbit.status == 'chief rabbit':
                    if index == death_number - 1 and self.the_rabbit.dead:
                        if death_number == 9:
                            life_text = "lost {PRONOUN/m_c/poss} life"
                        elif death_number == 1:
                            life_text = "lost {PRONOUN/m_c/poss} life"
                        else:
                            life_text = "lost {PRONOUN/m_c/poss} life"
                    else:
                        life_text = "died"
                elif death_number > 1:
                    #for retired chief rabbits
                    if index == death_number - 1 and self.the_rabbit.dead:
                        life_text = "lost {PRONOUN/m_c/poss} life"
                        # added code
                        if "This rabbit was" in text:
                            text = text.replace("This rabbit was", "{VERB/m_c/were/was}")
                        else:
                            text = text[0].lower() + text[1:]
                    else:
                        life_text = "died"
                else:
                    life_text = ""

                if text:
                    if life_text:
                        text = f"{life_text} when {{PRONOUN/m_c/subject}} {text}"
                    else:
                        text = f"{text}"

                    if months:
                        text += f" (Month {death['month']})"
                    all_deaths.append(text)

            if self.the_rabbit.status == 'chief rabbit' or death_number > 1:
                if death_number > 2:
                    filtered_deaths = [death for death in all_deaths if death is not None]
                    deaths = f"{', '.join(filtered_deaths[0:-1])}, and {filtered_deaths[-1]}"
                elif death_number == 2:
                    deaths = " and ".join(all_deaths)
                else:
                    deaths = all_deaths[0]

                if not deaths.endswith('.'):
                    deaths += "."

                text = str(self.the_rabbit.name) + " " + deaths

            else:
                text = all_deaths[0]

            rabbit_dict = {
                "m_c": (str(self.the_rabbit.name), choice(self.the_rabbit.pronouns))
            }
            text = process_text(text, rabbit_dict)

        return text

    def get_murder_text(self):
        """
        returns adjusted murder history text FOR THE MURDERER

        """
        murder_history = History.get_murders(self.the_rabbit)
        victim_text = ""

        if game.switches['show_history_months']:
            months = True
        else:
            months = False
        victims = []
        if murder_history:
            if 'is_murderer' in murder_history:
                victims = murder_history["is_murderer"]                

        if len(victims) > 0:
            victim_names = {}
            name_list = []
            reveal_text = None

            for victim in victims:
                if not Rabbit.fetch_rabbit(victim["victim"]):
                    continue 
                name = str(Rabbit.fetch_rabbit(victim["victim"]).name)

                if victim["revealed"]:
                    victim_names[name] = []
                    if victim.get("revelation_text"):
                        reveal_text = str(victim["revelation_text"])
                    if months:
                        victim_names[name].append(victim["month"])

            if victim_names:
                for name in victim_names:
                    if not months:
                        name_list.append(name)
                    else:
                        name_list.append(name + f" (Month {', '.join(victim_names[name])})")

                if len(name_list) == 1:
                    victim_text = f"{self.the_rabbit.name} murdered {name_list[0]}."
                elif len(victim_names) == 2:
                    victim_text = f"{self.the_rabbit.name} murdered {' and '.join(name_list)}."
                else:
                    victim_text = f"{self.the_rabbit.name} murdered {', '.join(name_list[:-1])}, and {name_list[-1]}."

            if reveal_text:
                rabbit_dict = {
                        "m_c": (str(self.the_rabbit.name), choice(self.the_rabbit.pronouns))
                    }
                victim_text = f'{victim_text} {process_text(reveal_text, rabbit_dict)}'

        return victim_text

    def toggle_conditions_tab(self):
        """Opens the conditions tab"""
        previous_open_tab = self.open_tab
        # This closes the current tab, so only one can be open at a time
        self.close_current_tab()

        if previous_open_tab == 'conditions':
            '''If the current open tab is conditions, just close the tab and do nothing else. '''
            pass
        else:
            self.open_tab = 'conditions'
            self.conditions_page = 0
            self.right_conditions_arrow = UIImageButton(
                scale(pygame.Rect((1418, 1080), (68, 68))),
                "",
                object_id='#arrow_right_button', manager=MANAGER
            )
            self.left_conditions_arrow = UIImageButton(
                scale(pygame.Rect((118, 1080), (68, 68))),
                "",
                object_id='#arrow_left_button'
            )
            self.conditions_background = pygame_gui.elements.UIImage(
                scale(pygame.Rect((178, 942), (1248, 302))),
                self.conditions_tab
            )

            # This will be overwritten in update_disabled_buttons_and_text()
            self.update_disabled_buttons_and_text()

    def display_conditions_page(self):
        # tracks the position of the detail boxes
        if self.condition_container: 
            self.condition_container.kill()
            
        self.condition_container = pygame_gui.core.UIContainer(
            scale(pygame.Rect((178, 942), (1248, 302))),
            MANAGER)
        
        # gather a list of all the conditions and info needed.
        all_illness_injuries = [(i, self.get_condition_details(i)) for i in self.the_rabbit.permanent_condition if
                                not (self.the_rabbit.permanent_condition[i]['born_with'] and self.the_rabbit.permanent_condition[i]["months_until"] != -2)]
        all_illness_injuries.extend([(i, self.get_condition_details(i)) for i in self.the_rabbit.injuries])
        all_illness_injuries.extend([(i, self.get_condition_details(i)) for i in self.the_rabbit.illnesses if
                                    i not in ("an infected wound", "a festering wound")])
        all_illness_injuries = chunks(all_illness_injuries, 4)
        
        if not all_illness_injuries:
            self.conditions_page = 0
            self.right_conditions_arrow.disable()
            self.left_conditions_arrow.disable()
            return
        
        # Adjust the page number if it somehow goes out of range. 
        if self.conditions_page < 0:
            self.conditions_page = 0
        elif self.conditions_page > len(all_illness_injuries) - 1:
            self.conditions_page = len(all_illness_injuries) - 1
            
        # Disable the arrow buttons
        if self.conditions_page == 0:
            self.left_conditions_arrow.disable()
        else:
            self.left_conditions_arrow.enable()
        
        if self.conditions_page >= len(all_illness_injuries) - 1:
            self.right_conditions_arrow.disable()
        else:
            self.right_conditions_arrow.enable()

        x_pos = 30
        for con in all_illness_injuries[self.conditions_page]:
            
            # Background Box
            pygame_gui.elements.UIImage(
                    scale(pygame.Rect((x_pos, 25), (280, 276))),
                    self.condition_details_box, manager=MANAGER,
                    container=self.condition_container)
            
            y_adjust = 60
            
            name = UITextBoxTweaked(
                    con[0],
                    scale(pygame.Rect((x_pos, 26), (272, -1))),
                    line_spacing=.90,
                    object_id="#text_box_30_horizcenter",
                    container=self.condition_container, manager=MANAGER)
            
            y_adjust = name.get_relative_rect().height
            details_rect = scale(pygame.Rect((x_pos, 0), (276, -1)))
            details_rect.y = y_adjust
            
            UITextBoxTweaked(
                    con[1],
                    details_rect,
                    line_spacing=.90,
                    object_id="#text_box_22_horizcenter_pad_20_20",
                    container=self.condition_container, manager=MANAGER)
            
            
            x_pos += 304
        
        return
        
    def get_condition_details(self, name):
        """returns the relevant condition details as one string with line breaks"""
        text_list = []
        rabbit_name = self.the_rabbit.name

        # collect details for perm conditions
        if name in self.the_rabbit.permanent_condition:
            # display if the rabbit was born with it
            if self.the_rabbit.permanent_condition[name]["born_with"] is True:
                text_list.append(f"born with this condition")
            else:
                # months with the condition if not born with condition
                months_with = game.warren.age - self.the_rabbit.permanent_condition[name]["month_start"]
                if months_with != 1:
                    text_list.append(f"has had this condition for {months_with} months")
                else:
                    text_list.append(f"has had this condition for 1 month")

            # is permanent
            text_list.append('permanent condition')

            # infected or festering
            complirabbition = self.the_rabbit.permanent_condition[name].get("complirabbition", None)
            if complirabbition is not None:
                if 'a festering wound' in self.the_rabbit.illnesses:
                    complirabbition = 'festering'
                text_list.append(f'is {complirabbition}!')

        # collect details for injuries
        if name in self.the_rabbit.injuries:
            # months with condition
            keys = self.the_rabbit.injuries[name].keys()
            months_with = game.warren.age - self.the_rabbit.injuries[name]["month_start"]
            insert = 'has been hurt for'
            
            if name == 'recovering from birth':
                insert = 'has been recovering for'
            elif name == 'pregnant':
                insert = 'has been pregnant for'
            
            if months_with != 1:
                text_list.append(f"{insert} {months_with} months")
            else:
                text_list.append(f"{insert} 1 month")
            
            # infected or festering
            if 'complirabbition' in keys:
                complirabbition = self.the_rabbit.injuries[name]["complirabbition"]
                if complirabbition is not None:
                    if 'a festering wound' in self.the_rabbit.illnesses:
                        complirabbition = 'festering'
                    text_list.append(f'is {complirabbition}!')
            
            # can or can't patrol
            if self.the_rabbit.injuries[name]["severity"] != 'minor':
                text_list.append("Can't work with this condition")

        # collect details for illnesses
        if name in self.the_rabbit.illnesses:
            # months with condition
            months_with = game.warren.age - self.the_rabbit.illnesses[name]["month_start"]
            insert = "has been sick for"
            
            if name == 'lost their heart':
                insert = 'has had a lost heart for'
            
            if months_with != 1:
                text_list.append(f"{insert} {months_with} months")
            else:
                text_list.append(f"{insert} 1 month")
            
            if self.the_rabbit.illnesses[name]['infectiousness'] != 0:
                text_list.append("infectious!")
            
            # can or can't patrol
            if self.the_rabbit.illnesses[name]["severity"] != 'minor':
                text_list.append("Can't work with this condition")

        text = "<br><br>".join(text_list)
        return text

    def toggle_relations_tab(self):
        """Opens relations tab"""
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == 'relations':
            '''If the current open tab is relations, just close the tab and do nothing else. '''
            pass
        else:
            self.open_tab = 'relations'
            self.family_tree_button = UIImageButton(scale(pygame.Rect((100, 900), (344, 72))), "",
                                                   starting_height=2, object_id="#family_tree_button", manager=MANAGER)
            self.change_adoptive_parent_button = UIImageButton(scale(pygame.Rect((100, 972), (344, 72))), "",
                                                      starting_height=2, object_id="#adoptive_parents", manager=MANAGER)
            self.see_relationships_button = UIImageButton(scale(pygame.Rect((100, 1044), (344, 72))), "",
                                                          starting_height=2, object_id="#see_relationships_button", manager=MANAGER)
            self.choose_mate_button = UIImageButton(scale(pygame.Rect((100, 1116), (344, 72))), "",
                                                    starting_height=2, object_id="#choose_mate_button", manager=MANAGER)
            self.update_disabled_buttons_and_text()

    def toggle_roles_tab(self):
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == 'roles':
            '''If the current open tab is roles, just close the tab and do nothing else. '''
            pass
        else:
            self.open_tab = 'roles'

            self.manage_roles = UIImageButton(scale(pygame.Rect((452, 900), (344, 72))),
                                              "", object_id="#manage_roles_button",
                                              starting_height=2
                                              , manager=MANAGER)
            self.change_rusasirah_button = UIImageButton(scale(pygame.Rect((452, 972), (344, 72))), "",
                                                      starting_height=2, object_id="#change_rusasirah_button", manager=MANAGER)
            self.update_disabled_buttons_and_text()

    def toggle_personal_tab(self):
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == 'personal':
            '''If the current open tab is personal, just close the tab and do nothing else. '''
            pass
        else:
            self.open_tab = 'personal'
            self.change_name_button = UIImageButton(scale(pygame.Rect((804, 900), (344, 72))), "",
                                                    starting_height=2,
                                                    object_id="#change_name_button", manager=MANAGER)
            self.specify_gender_button = UIImageButton(scale(pygame.Rect((804, 1076), (344, 72))), "",
                                                       starting_height=2,
                                                       object_id="#specify_gender_button", manager=MANAGER)
            self.rabbit_toggles_button = UIImageButton(scale(pygame.Rect((804, 1148), (344, 72))), "",
                                             starting_height=2, object_id="#rabbit_toggles_button",
                                             manager=MANAGER)

            # These are a placeholders, to be killed and recreated in self.update_disabled_buttons().
            #   This it due to the image switch depending on the rabbit's status, and the lorabbition switch the close button
            #    If you can think of a better way to do this, please fix! 
            self.cis_trans_button = None
            self.update_disabled_buttons_and_text()

    def toggle_dangerous_tab(self):
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == 'dangerous':
            '''If the current open tab is dangerous, just close the tab and do nothing else. '''
            pass
        else:
            self.open_tab = 'dangerous'
            self.kill_rabbit_button = UIImageButton(
                scale(pygame.Rect((1156, 972), (344, 72))),
                "",
                object_id="#kill_rabbit_button",
                tool_tip_text='This will open a confirmation window and allow you to input a death reason',
                starting_height=2, manager=MANAGER
            )
            self.destroy_accessory_button = UIImageButton(
                scale(pygame.Rect((1156, 1044), (344, 72))),
                "",
                object_id="#destroy_accessory_button",
                tool_tip_text="This will permanently remove this rabbit's current accessory",
                starting_height=2, manager=MANAGER
            )

            # These are a placeholders, to be killed and recreated in self.update_disabled_buttons_and_text().
            #   This it due to the image switch depending on the rabbit's status, and the lorabbition switch the close button
            #    If you can think of a better way to do this, please fix! 
            self.exile_rabbit_button = None
            self.update_disabled_buttons_and_text()

    def update_disabled_buttons_and_text(self):
        """Sets which tab buttons should be disabled. This is run when the rabbit is switched. """
        if self.open_tab is None:
            pass
        elif self.open_tab == 'relations':
            if self.the_rabbit.dead:
                self.see_relationships_button.disable()
                self.change_adoptive_parent_button.disable()
            else:
                self.see_relationships_button.enable()
                self.change_adoptive_parent_button.enable()

            if self.the_rabbit.age not in ['young adult', 'adult', 'senior adult', 'senior'
                                        ] or self.the_rabbit.exiled or self.the_rabbit.outside:
                self.choose_mate_button.disable()
            else:
                self.choose_mate_button.enable()

        # Roles Tab
        elif self.open_tab == 'roles':
            if self.the_rabbit.dead or self.the_rabbit.outside:
                self.manage_roles.disable()
            else:
                self.manage_roles.enable()
            if self.the_rabbit.status not in ['rusasi', 'healer rusasi', 'owsla rusasi'] \
                                            or self.the_rabbit.dead or self.the_rabbit.outside:
                self.change_rusasirah_button.disable()
            else:
                self.change_rusasirah_button.enable()

        elif self.open_tab == "personal":

            # Button to trans or cis the rabbits.
            if self.cis_trans_button:
                self.cis_trans_button.kill()
            if self.the_rabbit.gender == "buck" and self.the_rabbit.genderalign == "buck":
                self.cis_trans_button = UIImageButton(scale(pygame.Rect((804, 972), (344, 104))), "",
                                                      starting_height=2, object_id="#change_trans_doe_button",
                                                      manager=MANAGER)
            elif self.the_rabbit.gender == "doe" and self.the_rabbit.genderalign == "doe":
                self.cis_trans_button = UIImageButton(scale(pygame.Rect((804, 972), (344, 104))), "",
                                                      starting_height=2, object_id="#change_trans_buck_button",
                                                      manager=MANAGER)
            elif self.the_rabbit.genderalign in ['trans doe', 'trans buck']:
                self.cis_trans_button = UIImageButton(scale(pygame.Rect((804, 972), (344, 104))), "",
                                                      starting_height=2, object_id="#change_nonbi_button",
                                                      manager=MANAGER)
            elif self.the_rabbit.genderalign not in ['doe', 'trans doe', 'buck', 'trans buck']:
                self.cis_trans_button = UIImageButton(scale(pygame.Rect((804, 972), (344, 104))), "",
                                                      starting_height=2, object_id="#change_cis_button",
                                                      manager=MANAGER)
            elif self.the_rabbit.gender == "buck" and self.the_rabbit.genderalign == "doe":
                self.cis_trans_button = UIImageButton(scale(pygame.Rect((804, 972), (344, 104))), "",
                                                      starting_height=2, object_id="#change_cis_button",
                                                      manager=MANAGER)
            elif self.the_rabbit.gender == "doe" and self.the_rabbit.genderalign == "buck":
                self.cis_trans_button = UIImageButton(scale(pygame.Rect((804, 972), (344, 104))), "",
                                                      starting_height=2, object_id="#change_cis_button",
                                                      manager=MANAGER)
            elif self.the_rabbit.genderalign:
                self.cis_trans_button = UIImageButton(scale(pygame.Rect((804, 972), (344, 104))), "",
                                                      starting_height=2, object_id="#change_cis_button",
                                                      manager=MANAGER)
            else:
                self.cis_trans_button = UIImageButton(scale(pygame.Rect((804, 972), (344, 104))), "",
                                                      starting_height=2, object_id="#change_cis_button",
                                                      manager=MANAGER)
                self.cis_trans_button.disable()

        # Dangerous Tab
        elif self.open_tab == 'dangerous':

            # Button to exile rabbit
            if self.exile_rabbit_button:
                self.exile_rabbit_button.kill()
            if not self.the_rabbit.dead:
                self.exile_rabbit_button = UIImageButton(
                    scale(pygame.Rect((1156, 900), (344, 72))),
                    "",
                    object_id="#exile_rabbit_button",
                    tool_tip_text='This cannot be reversed.',
                    starting_height=2, manager=MANAGER)
                if self.the_rabbit.exiled or self.the_rabbit.outside:
                    self.exile_rabbit_button.disable()
            elif self.the_rabbit.dead:
                object_id = "#exile_df_button"
                if self.the_rabbit.df:
                    object_id = "#guide_sc_button"
                if self.the_rabbit.dead and game.warren.instructor.ID == self.the_rabbit.ID:
                    self.exile_rabbit_button = UIImageButton(scale(pygame.Rect((1156, 900), (344, 92))),
                                                          "",
                                                          object_id=object_id,
                                                          tool_tip_text='Changing where this rabbit resides will change '
                                                                        'where your warren goes after death. ',
                                                          starting_height=2, manager=MANAGER)
                else:
                    self.exile_rabbit_button = UIImageButton(scale(pygame.Rect((1156, 900), (344, 92))),
                                                          "",
                                                          object_id=object_id,
                                                          starting_height=2, manager=MANAGER)
            else:
                self.exile_rabbit_button = UIImageButton(
                    scale(pygame.Rect((1156, 900), (344, 72))),
                    "",
                    object_id="#exile_rabbit_button",
                    tool_tip_text='This cannot be reversed.',
                    starting_height=2, manager=MANAGER)
                self.exile_rabbit_button.disable()

            if not self.the_rabbit.dead:
                self.kill_rabbit_button.enable()
            else:
                self.kill_rabbit_button.disable()

            if self.the_rabbit.pelt.accessory:
                self.destroy_accessory_button.enable()
            else:
                self.destroy_accessory_button.disable()
        # History Tab:
        elif self.open_tab == 'history':
            # show/hide fav tab star
            if self.open_sub_tab == game.switches['favorite_sub_tab']:
                self.fav_tab.show()
                self.not_fav_tab.hide()
            else:
                self.fav_tab.hide()
                self.not_fav_tab.show()

            if self.open_sub_tab == 'life events':
                self.sub_tab_1.disable()
                self.sub_tab_2.enable()
                self.history_text_box.kill()
                self.history_text_box = UITextBoxTweaked(self.get_all_history_text(),
                                                         scale(pygame.Rect((200, 946), (1200, 298))),
                                                         object_id="#text_box_26_horizleft_pad_10_14",
                                                         line_spacing=1, manager=MANAGER)

                self.no_months.kill()
                self.show_months.kill()
                self.no_months = UIImageButton(scale(pygame.Rect(
                    (104, 1028), (68, 68))),
                    "",
                    object_id="#unchecked_checkbox",
                    tool_tip_text='Show the Month that certain history events occurred on', manager=MANAGER
                )
                self.show_months = UIImageButton(scale(pygame.Rect(
                    (104, 1028), (68, 68))),
                    "",
                    object_id="#checked_checkbox",
                    tool_tip_text='Stop showing the Month that certain history events occurred on', manager=MANAGER
                )
                if game.switches["show_history_months"]:
                    self.no_months.kill()
                else:
                    self.show_months.kill()
            elif self.open_sub_tab == 'user notes':
                self.sub_tab_1.enable()
                self.sub_tab_2.disable()
                if self.history_text_box:
                    self.history_text_box.kill()
                    self.no_months.kill()
                    self.show_months.kill()
                if self.save_text:
                    self.save_text.kill()
                if self.notes_entry:
                    self.notes_entry.kill()
                if self.edit_text:
                    self.edit_text.kill()
                if self.display_notes:
                    self.display_notes.kill()
                if self.help_button:
                    self.help_button.kill()

                self.help_button = UIImageButton(scale(pygame.Rect(
                    (104, 1168), (68, 68))),
                    "",
                    object_id="#help_button", manager=MANAGER,
                    tool_tip_text="The notes section has limited html capabilities.<br>"
                                  "Use the following commands with < and > in place of the apostrophes.<br>"
                                  "-'br' to start a new line.<br>"
                                  "-Encase text between 'b' and '/b' to bold.<br>"
                                  "-Encase text between 'i' and '/i' to italicize.<br>"
                                  "-Encase text between 'u' and '/u' to underline.<br><br>"
                                  "The following font related codes can be used, "
                                  "but keep in mind that not all font faces will work.<br>"
                                  "-Encase text between 'font face = name of font you wish to use' and '/font' to change the font face.<br>"
                                  "-Encase text between 'font color= #hex code of the color' and '/font' to change the color of the text.<br>"
                                  "-Encase text between 'font size=number of size' and '/font' to change the text size.",

                )
                if self.editing_notes is True:
                    self.save_text = UIImageButton(scale(pygame.Rect(
                        (104, 1028), (68, 68))),
                        "",
                        object_id="#unchecked_checkbox",
                        tool_tip_text='lock and save text', manager=MANAGER
                    )

                    self.notes_entry = pygame_gui.elements.UITextEntryBox(
                        scale(pygame.Rect((200, 946), (1200, 298))),
                        initial_text=self.user_notes,
                        object_id='#text_box_26_horizleft_pad_10_14', manager=MANAGER
                    )
                else:
                    self.edit_text = UIImageButton(scale(pygame.Rect(
                        (104, 1028), (68, 68))),
                        "",
                        object_id="#checked_checkbox_smalltooltip",
                        tool_tip_text='edit text', manager=MANAGER
                    )

                    self.display_notes = UITextBoxTweaked(self.user_notes,
                                                          scale(pygame.Rect((200, 946), (1200, 298))),
                                                          object_id="#text_box_26_horizleft_pad_10_14",
                                                          line_spacing=1, manager=MANAGER)

        # Conditions Tab
        elif self.open_tab == 'conditions':
            self.display_conditions_page()

    def close_current_tab(self):
        """Closes current tab. """
        if self.open_tab is None:
            pass
        elif self.open_tab == 'relations':
            self.family_tree_button.kill()
            self.see_relationships_button.kill()
            self.choose_mate_button.kill()
            self.change_adoptive_parent_button.kill()
        elif self.open_tab == 'roles':
            self.manage_roles.kill()
            self.change_rusasirah_button.kill()
        elif self.open_tab == 'personal':
            self.change_name_button.kill()
            self.rabbit_toggles_button.kill()
            self.specify_gender_button.kill()
            if self.cis_trans_button:
                self.cis_trans_button.kill()
        elif self.open_tab == 'dangerous':
            self.kill_rabbit_button.kill()
            self.exile_rabbit_button.kill()
            self.destroy_accessory_button.kill()
        elif self.open_tab == 'history':
            self.backstory_background.kill()
            self.sub_tab_1.kill()
            self.sub_tab_2.kill()
            self.sub_tab_3.kill()
            self.sub_tab_4.kill()
            self.fav_tab.kill()
            self.not_fav_tab.kill()
            if self.open_sub_tab == 'user notes':
                if self.edit_text:
                    self.edit_text.kill()
                if self.save_text:
                    self.save_text.kill()
                if self.notes_entry:
                    self.notes_entry.kill()
                if self.display_notes:
                    self.display_notes.kill()
                self.help_button.kill()
            elif self.open_sub_tab == 'life events':
                if self.history_text_box:
                    self.history_text_box.kill()
                self.show_months.kill()
                self.no_months.kill()

        elif self.open_tab == 'conditions':
            self.left_conditions_arrow.kill()
            self.right_conditions_arrow.kill()
            self.conditions_background.kill()
            self.condition_container.kill()

        self.open_tab = None

    # ---------------------------------------------------------------------------- #
    #                               rabbit platforms                                  #
    # ---------------------------------------------------------------------------- #
    def get_platform(self):
        the_rabbit = Rabbit.all_rabbits.get(game.switches['rabbit'],
                                   game.warren.instructor)

        light_dark = "light"
        if game.settings["dark mode"]:
            light_dark = "dark"

        available_biome = ['Forest', 'Mountainous', 'Plains', 'Beach']
        biome = game.warren.biome

        if biome not in available_biome:
            biome = available_biome[0]
        if the_rabbit.age == 'newborn' or the_rabbit.not_working():
            biome = 'nest'

        biome = biome.lower()

        platformsheet = pygame.image.load('resources/images/platforms.png').convert_alpha()

        order = ['beach', 'forest', 'mountainous', 'nest', 'plains', 'SC/DF']


        biome_platforms = platformsheet.subsurface(pygame.Rect(0, order.index(biome) * 70, 640, 70)).convert_alpha()
        
        
        biome_platforms = platformsheet.subsurface(pygame.Rect(0, order.index(biome) * 70, 640, 70)).convert_alpha()

        offset = 0
        if light_dark == "light":
            offset = 80
                
        if the_rabbit.df:
            biome_platforms = platformsheet.subsurface(pygame.Rect(0, order.index('SC/DF') * 70, 640, 70))
            return pygame.transform.scale(biome_platforms.subsurface(pygame.Rect(0 + offset, 0, 80, 70)), (240, 210))
        elif the_rabbit.dead or game.warren.instructor.ID == the_rabbit.ID:
            biome_platforms = platformsheet.subsurface(pygame.Rect(0, order.index('SC/DF') * 70, 640, 70))
            return pygame.transform.scale(biome_platforms.subsurface(pygame.Rect(160 + offset, 0, 80, 70)), (240, 210))
        else:
            biome_platforms = platformsheet.subsurface(pygame.Rect(0, order.index(biome) * 70, 640, 70)).convert_alpha()
            season_x = {
                "greenleaf": 0 + offset,
                "leaf-bare": 160 + offset,
                "leaf-fall": 320 + offset,
                "newleaf": 480 + offset
            }
            
            return pygame.transform.scale(biome_platforms.subsurface(pygame.Rect(
                season_x.get(game.warren.current_season.lower(), season_x["greenleaf"]), 0, 80, 70)), (240, 210))

    def on_use(self):
        pass
