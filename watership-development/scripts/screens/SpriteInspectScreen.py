#!/usr/bin/env python3
# -*- coding: ascii -*-
import pygame

from ..game_structure.windows import SaveAsImage

from scripts.utility import scale
from .Screens import Screens
from scripts.utility import get_text_box_theme, scale_dimentions, generate_sprite, shorten_text_to_fit
from scripts.rabbit.rabbits import Rabbit
import pygame_gui
from scripts.game_structure.image_button import UIImageButton, UITextBoxTweaked
from scripts.game_structure.game_essentials import game, MANAGER


class SpriteInspectScreen(Screens):
    rabbit_life_stages = ["newborn", "kit", "adolescent", "adult", "senior"]
    
    def __init__(self, name=None):
        self.back_button = None
        self.previous_rabbit_button = None
        self.previous_rabbit = None
        self.next_rabbit_button = None
        self.next_rabbit = None
        self.the_rabbit = None
        self.rabbit_image = None
        self.rabbit_elements = {}
        self.checkboxes = {}
        self.platform_shown_text = None
        self.scars_shown = None
        self.acc_shown_text = None
        self.override_dead_lineart_text = None
        self.override_not_working_text = None
        self.save_image_button = None
        
        #Image Settings: 
        self.platform_shown = None
        self.displayed_lifestage = None
        self.scars_shown = True
        self.override_dead_lineart = False
        self.acc_shown = True
        self.override_not_working = False
        
        super().__init__(name)
    
    def handle_event(self, event):
        # Don't handle the events if a window is open.     
        if game.switches['window_open']:
            return
        
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.change_screen("profile screen")
            elif event.ui_element == self.next_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.next_rabbit), Rabbit):
                    game.switches["rabbit"] = self.next_rabbit
                    self.rabbit_setup()
                else:
                    print("invalid next rabbit", self.next_rabbit)
            elif event.ui_element == self.previous_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.previous_rabbit), Rabbit):
                    game.switches["rabbit"] = self.previous_rabbit
                    self.rabbit_setup()
                else:
                    print("invalid previous rabbit", self.previous_rabbit)
            elif event.ui_element == self.next_life_stage:
                self.displayed_life_stage = min(self.displayed_life_stage + 1, 
                                                len(self.valid_life_stages) - 1)
                self.update_disabled_buttons()
                self.make_rabbit_image()
            elif event.ui_element == self.save_image_button:
                SaveAsImage(self.generate_image_to_save(), str(self.the_rabbit.name))
            elif event.ui_element == self.previous_life_stage:
                self.displayed_life_stage = max(self.displayed_life_stage - 1, 
                                                0)
                self.update_disabled_buttons()
                self.make_rabbit_image()
            elif event.ui_element == self.checkboxes["platform_shown"]:
                if self.platform_shown:
                    self.platform_shown = False
                else:
                    self.platform_shown = True
                
                self.set_background_visablity()
                self.update_checkboxes()
            elif event.ui_element == self.checkboxes["scars_shown"]:
                if self.scars_shown:
                    self.scars_shown = False
                else:
                    self.scars_shown = True
                
                self.make_rabbit_image()
                self.update_checkboxes()
            elif event.ui_element == self.checkboxes["acc_shown"]:
                if self.acc_shown:
                    self.acc_shown = False
                else:
                    self.acc_shown = True
                
                self.make_rabbit_image()
                self.update_checkboxes()
            elif event.ui_element == self.checkboxes["override_dead_lineart"]:
                if self.override_dead_lineart:
                    self.override_dead_lineart = False
                else:
                    self.override_dead_lineart = True
                
                self.make_rabbit_image()
                self.update_checkboxes()
            elif event.ui_element == self.checkboxes["override_not_working"]:
                if self.override_not_working:
                    self.override_not_working = False
                else:
                    self.override_not_working = True
                
                self.make_rabbit_image()
                self.update_checkboxes()
            elif event.ui_element == self.rabbit_elements["favourite_button"]:
                self.the_rabbit.favourite = False
                self.rabbit_elements["favourite_button"].hide()
                self.rabbit_elements["not_favourite_button"].show()
            elif event.ui_element == self.rabbit_elements["not_favourite_button"]:
                self.the_rabbit.favourite = True
                self.rabbit_elements["favourite_button"].show()
                self.rabbit_elements["not_favourite_button"].hide()
    
        return super().handle_event(event)
    
    def screen_switches(self):        
        self.next_rabbit_button = UIImageButton(scale(pygame.Rect((1244, 50), (306, 60))), "", object_id="#next_rabbit_button"
                                             , manager=MANAGER)
        self.previous_rabbit_button = UIImageButton(scale(pygame.Rect((50, 50), (306, 60))), "",
                                                 object_id="#previous_rabbit_button"
                                                 , manager=MANAGER)
        self.back_button = UIImageButton(scale(pygame.Rect((50, 120), (210, 60))), "", object_id="#back_button"
                                         , manager=MANAGER)
        
        self.previous_life_stage = UIImageButton(scale(pygame.Rect((150, 550), (76, 100))), "", object_id="#arrow_right_fancy",
                                                 starting_height=2)
        
        self.next_life_stage = UIImageButton(scale(pygame.Rect((1374, 550), (76, 100))), "", object_id="#arrow_left_fancy",
                                             starting_height=2)
        
        self.save_image_button = UIImageButton(scale(pygame.Rect((50, 190),(270, 60))), "", object_id="#save_image_button")
        
        # Toggle Text:
        self.platform_shown_text = pygame_gui.elements.UITextBox("Show Platform", scale(pygame.Rect((310, 1160), (290, 100))),
                                                                 object_id=get_text_box_theme(
                                                                              "#text_box_34_horizcenter"), 
                                                                 starting_height=2)
        self.scars_shown_text = pygame_gui.elements.UITextBox("Show Scar(s)", scale(pygame.Rect((710, 1160), (290, 100))),
                                                              object_id=get_text_box_theme(
                                                                              "#text_box_34_horizcenter"), 
                                                                 starting_height=2)
        self.acc_shown_text = pygame_gui.elements.UITextBox("Show Accessory", scale(pygame.Rect((1100, 1160), (290, 100))),
                                                            object_id=get_text_box_theme(
                                                                              "#text_box_34_horizcenter"), 
                                                            starting_height=2)
        self.override_dead_lineart_text = pygame_gui.elements.UITextBox("Show as Living", scale(pygame.Rect((510, 1260), (290, 100))),
                                                                        object_id=get_text_box_theme(
                                                                              "#text_box_34_horizcenter"), 
                                                                        starting_height=2)
        self.override_not_working_text = pygame_gui.elements.UITextBox("Show as Healthy", scale(pygame.Rect((910, 1260), (290, 100))),
                                                                 object_id=get_text_box_theme(
                                                                              "#text_box_34_horizcenter"), 
                                                                 starting_height=2)
        
        
        if game.warren.warren_settings['backgrounds']:
            self.platform_shown = True
        else:
            self.platform_shown = False
        
        self.rabbit_setup()
        return super().screen_switches()

    def rabbit_setup(self): 
        """Sets up all the elements related to the rabbit """
        for ele in self.rabbit_elements:
            self.rabbit_elements[ele].kill()
        self.rabbit_elements = {}
        
        self.the_rabbit = Rabbit.fetch_rabbit(game.switches['rabbit'])
        
        self.rabbit_elements["platform"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((240, 200), (1120, 980))),
                pygame.transform.scale(self.get_platform(), scale_dimentions((1120, 701))), 
                manager=MANAGER)
        self.set_background_visablity()
        
        # Gather list of current and previous life states
        # "young adult", "adult", and "senior adult" all look the same: collapse to adult
        # This is not the best way to do it, so if we make them have difference appearances, this will
        # need to be changed/removed. 
        if self.the_rabbit.age in ["young adult", "adult", "senior adult"]:
            current_life_stage = "adult"
        else:
            current_life_stage = self.the_rabbit.age
        
        self.valid_life_stages = []
        for life_stage in SpriteInspectScreen.rabbit_life_stages:
            self.valid_life_stages.append(life_stage)
            if life_stage == current_life_stage:
                break
        
        #Store the index of the currently displayed life stage. 
        self.displayed_life_stage = len(self.valid_life_stages) - 1
        
        #Reset all the toggles
        self.lifestage = None
        self.scars_shown = True
        self.override_dead_lineart = False
        self.acc_shown = True
        self.override_not_working = False
        
        # Make the rabbit image
        self.make_rabbit_image()
        
        rabbit_name = str(self.the_rabbit.name)  # name
        if self.the_rabbit.dead:
            rabbit_name += " (dead)"  # A dead rabbit will have the (dead) sign next to their name
        short_name = shorten_text_to_fit(rabbit_name, 390, 40)
        
        self.rabbit_elements["rabbit_name"] = pygame_gui.elements.UITextBox(short_name,
                                                                          scale(pygame.Rect((50, 120), (-1, 80))),
                                                                          object_id=get_text_box_theme(
                                                                              "#text_box_40_horizcenter"), manager=MANAGER)
        name_text_size = self.rabbit_elements["rabbit_name"].get_relative_rect()

        self.rabbit_elements["rabbit_name"].kill()

        self.rabbit_elements["rabbit_name"] = pygame_gui.elements.UITextBox(short_name,
                                                                      scale(pygame.Rect(
                                                                        (800 - name_text_size.width, 120),
                                                                        (name_text_size.width * 2, 80))),
                                                                       object_id=get_text_box_theme(
                                                                        "#text_box_40_horizcenter"), manager=MANAGER)
        
        # Fullscreen
        if game.settings['fullscreen']:
            x_pos = 745 - name_text_size.width//2
        else:
            x_pos = 740 - name_text_size.width
        self.rabbit_elements["favourite_button"] = UIImageButton(scale(pygame.Rect
                                                                ((x_pos, 127), (56, 56))),
                                                              "",
                                                              object_id="#fav_rabbit",
                                                              manager=MANAGER,
                                                              tool_tip_text='Remove favorite status',
                                                              starting_height=2)

        self.rabbit_elements["not_favourite_button"] = UIImageButton(scale(pygame.Rect
                                                                    ((x_pos, 127),
                                                                        (56, 56))),
                                                                 "",
                                                                 object_id="#not_fav_rabbit",
                                                                 manager=MANAGER,
                                                                 tool_tip_text='Mark as favorite',
                                                                 starting_height=2)  
        if self.the_rabbit.favourite:
            self.rabbit_elements["favourite_button"].show()
            self.rabbit_elements["not_favourite_button"].hide()
        else:
            self.rabbit_elements["favourite_button"].hide()
            self.rabbit_elements["not_favourite_button"].show()
        
        
        # Write the checkboxes. The text is set up in switch_screens.  
        self.update_checkboxes()
        
        
        self.determine_previous_and_next_rabbit()
        self.update_disabled_buttons()
    
    def update_checkboxes(self):
        for ele in self.checkboxes:
            self.checkboxes[ele].kill()
        self.checkboxes = {}
        
        # "Show Platform"
        self.make_one_checkbox((200, 1150), "platform_shown", self.platform_shown)
        
        # "Show Scars"
        self.make_one_checkbox((600, 1150), "scars_shown", self.scars_shown, self.the_rabbit.pelt.scars)
        
        # "Show accessories"
        self.make_one_checkbox((1000, 1150), "acc_shown", self.acc_shown, self.the_rabbit.pelt.accessory)
        
        # "Show as living"
        self.make_one_checkbox((400, 1250), "override_dead_lineart", self.override_dead_lineart, self.the_rabbit.dead,
                               disabled_object_id="#checked_checkbox")
        
        # "Show as healthy"
        self.make_one_checkbox((800, 1250), "override_not_working", self.override_not_working, self.the_rabbit.not_working(),
                               disabled_object_id="#checked_checkbox")
        
    def make_one_checkbox(self, lorabbition:tuple, name:str, stored_bool: bool, rabbit_value_to_allow=True,
                          disabled_object_id = "#unchecked_checkbox"):
        """Makes a single checkbox. So I don't have to copy and paste this 5 times. 
            if rabbit_value_to_allow evaluates to False, then the unchecked checkbox is always used the the checkbox 
            is disabled"""
        
        if not rabbit_value_to_allow:
            self.checkboxes[name] = UIImageButton(scale(pygame.Rect(lorabbition, (102, 102))), "" ,
                                                            object_id = disabled_object_id,
                                                            starting_height=2)
            self.checkboxes[name].disable()
        elif stored_bool:
            self.checkboxes[name] = UIImageButton(scale(pygame.Rect(lorabbition, (102, 102))), "" ,
                                                            object_id = "#checked_checkbox",
                                                            starting_height=2)
        else:
            self.checkboxes[name] = UIImageButton(scale(pygame.Rect(lorabbition, (102, 102))), "" ,
                                                            object_id = "#unchecked_checkbox",
                                                            starting_height=2)
    
    def make_rabbit_image(self):
        """Makes the rabbit image """
        if "rabbit_image" in self.rabbit_elements:
            self.rabbit_elements["rabbit_image"].kill()
        
        self.rabbit_image = generate_sprite(self.the_rabbit, life_state=self.valid_life_stages[self.displayed_life_stage], 
                                         scars_hidden=not self.scars_shown,
                                         acc_hidden=not self.acc_shown, always_living=self.override_dead_lineart, 
                                         no_not_working=self.override_not_working)
        
        self.rabbit_elements["rabbit_image"] = pygame_gui.elements.UIImage(
            scale(pygame.Rect((450, 200),(700, 700))),
            pygame.transform.scale(self.rabbit_image, scale_dimentions((700, 700)))
        )
      
    def determine_previous_and_next_rabbit(self):
        """'Determines where the next and previous buttons point too."""

        is_instructor = False
        if self.the_rabbit.dead and game.warren.instructor.ID == self.the_rabbit.ID:
            is_instructor = True

        previous_rabbit = 0
        next_rabbit = 0
        if self.the_rabbit.dead and not is_instructor and self.the_rabbit.df == game.warren.instructor.df and \
                not (self.the_rabbit.outside or self.the_rabbit.exiled):
            previous_rabbit = game.warren.instructor.ID

        if is_instructor:
            next_rabbit = 1

        for check_rabbit in Rabbit.all_rabbits_list:
            if check_rabbit.ID == self.the_rabbit.ID:
                next_rabbit = 1
            else:
                if next_rabbit == 0 and check_rabbit.ID != self.the_rabbit.ID and check_rabbit.dead == self.the_rabbit.dead \
                        and check_rabbit.ID != game.warren.instructor.ID and check_rabbit.outside == self.the_rabbit.outside and \
                        check_rabbit.df == self.the_rabbit.df and not check_rabbit.faded:
                    previous_rabbit = check_rabbit.ID

                elif next_rabbit == 1 and check_rabbit != self.the_rabbit.ID and check_rabbit.dead == self.the_rabbit.dead \
                        and check_rabbit.ID != game.warren.instructor.ID and check_rabbit.outside == self.the_rabbit.outside and \
                        check_rabbit.df == self.the_rabbit.df and not check_rabbit.faded:
                    next_rabbit = check_rabbit.ID

                elif int(next_rabbit) > 1:
                    break

        if next_rabbit == 1:
            next_rabbit = 0

        self.next_rabbit = next_rabbit
        self.previous_rabbit = previous_rabbit
    
    def set_background_visablity(self):
        if "platform" not in self.rabbit_elements:
            return
        
        if self.platform_shown:
            self.rabbit_elements["platform"].show()
            self.rabbit_elements["platform"].disable()
        else:
            self.rabbit_elements["platform"].hide()
    
    def exit_screen(self):
        self.back_button.kill()
        self.back_button = None
        self.previous_rabbit_button.kill()
        self.previous_rabbit_button = None
        self.next_rabbit_button.kill()
        self.next_rabbit_button = None
        self.previous_life_stage.kill()
        self.previous_life_stage = None
        self.next_life_stage.kill()
        self.next_life_stage = None
        self.save_image_button.kill()
        self.save_image_button = None
        self.platform_shown_text.kill()
        self.platform_shown_text = None
        self.scars_shown_text.kill()
        self.scars_shown = None
        self.acc_shown_text.kill()
        self.acc_shown_text = None
        self.override_dead_lineart_text.kill()
        self.override_dead_lineart_text = None
        self.override_not_working_text.kill()
        self.override_not_working_text = None
        
        for ele in self.rabbit_elements:
            self.rabbit_elements[ele].kill()
        self.rabbit_elements = {}
        for ele in self.checkboxes:
            self.checkboxes[ele].kill()
        self.checkboxes = {}
        return super().exit_screen()
    
    def update_disabled_buttons(self):
        # Previous and next rabbit button
        if self.next_rabbit == 0:
            self.next_rabbit_button.disable()
        else:
            self.next_rabbit_button.enable()

        if self.previous_rabbit == 0:
            self.previous_rabbit_button.disable()
        else:
            self.previous_rabbit_button.enable()
            
        if self.displayed_life_stage >= len(self.valid_life_stages) - 1:
            self.next_life_stage.disable()
        else:
            self.next_life_stage.enable()
            
        if self.displayed_life_stage <= 0:
            self.previous_life_stage.disable()
        else:
            self.previous_life_stage.enable()
        
        
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
        
        offset = 0
        if light_dark == "light":
            offset = 80
        
        if the_rabbit.df:
            biome_platforms = platformsheet.subsurface(pygame.Rect(0, order.index('SC/DF') * 70, 640, 70))
            return biome_platforms.subsurface(pygame.Rect(0 + offset, 0, 80, 70))
        elif the_rabbit.dead or game.warren.instructor.ID == the_rabbit.ID:
            biome_platforms = platformsheet.subsurface(pygame.Rect(0, order.index('SC/DF') * 70, 640, 70))
            return biome_platforms.subsurface(pygame.Rect(160 + offset, 0, 80, 70))
        else:
            biome_platforms = platformsheet.subsurface(pygame.Rect(0, order.index(biome) * 70, 640, 70)).convert_alpha()
            season_x = {
                "greenleaf": 0 + offset,
                "leafbare": 160 + offset,
                "leaffall": 320 + offset,
                "newleaf": 480 + offset
            }
            
            
            return biome_platforms.subsurface(pygame.Rect(
                season_x.get(game.warren.current_season.lower(), season_x["greenleaf"]), 0, 80, 70))
            
    def generate_image_to_save(self):
        """Generates the image to save, with platform if needed. """
        if self.platform_shown:
            full_image = self.get_platform()
            full_image.blit(self.rabbit_image, (15, 0))
            return full_image
        else:
            return self.rabbit_image
