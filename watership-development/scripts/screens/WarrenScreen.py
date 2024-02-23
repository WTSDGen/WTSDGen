import pygame
import pygame_gui
import traceback
from copy import deepcopy
import random

from .Screens import Screens

from scripts.rabbit.rabbits import Rabbit
from scripts.game_structure.image_button import UISpriteButton, UIImageButton
from scripts.utility import scale
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y
from scripts.game_structure.windows import SaveError


class WarrenScreen(Screens):
    max_sprites_displayed = 400  # we don't want 100,000 sprites rendering at once. 400 is enough.
    rabbit_buttons = []

    def __init__(self, name=None):
        super().__init__(name)
        self.show_den_labels = None
        self.show_den_text = None
        self.label_toggle = None
        self.app_den_label = None
        self.clearing_label = None
        self.nursery_label = None
        self.elder_den_label = None
        self.med_den_label = None
        self.chief_rabbit_den_label = None
        self.rabbit_den_label = None
        self.layout = None

    def on_use(self):
        if game.warren.warren_settings['backgrounds']:
            if game.warren.current_season == 'Spring':
                screen.blit(self.spring_bg, (0, 0))
            elif game.warren.current_season == 'Summer':
                screen.blit(self.summer_bg, (0, 0))
            elif game.warren.current_season == 'Winter':
                screen.blit(self.winter_bg, (0, 0))
            elif game.warren.current_season == 'Autumn':
                screen.blit(self.autumn_bg, (0, 0))

    def handle_event(self, event):
        if game.switches['window_open']:
            pass
        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.save_button:
                try:
                    self.save_button_saving_state.show()
                    self.save_button.disable()
                    game.save_rabbits()
                    game.warren.save_warren()
                    game.warren.save_pregnancy(game.warren)
                    game.save_events()
                    game.save_settings()
                    game.switches['saved_warren'] = True
                    self.update_buttons_and_text()
                except RuntimeError:
                    SaveError(traceback.format_exc())
                    self.change_screen("start screen")
            if event.ui_element in self.rabbit_buttons:
                game.switches["rabbit"] = event.ui_element.return_rabbit_id()
                self.change_screen('profile screen')
            if event.ui_element == self.label_toggle:
                if game.warren.warren_settings['den labels']:
                    game.warren.warren_settings['den labels'] = False
                else:
                    game.warren.warren_settings['den labels'] = True
                self.update_buttons_and_text()
            if event.ui_element == self.med_den_label:
                self.change_screen('med den screen')
            else:
                self.menu_button_pressed(event)
            if event.ui_element == self.clearing_label:
                self.change_screen('food screen')
            else:
                self.menu_button_pressed(event)
        
        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if event.key == pygame.K_RIGHT:
                self.change_screen('inle screen')
            elif event.key == pygame.K_LEFT:
                self.change_screen('events screen')
            elif event.key == pygame.K_SPACE:
                self.save_button_saving_state.show()
                self.save_button.disable()
                game.save_rabbits()
                game.warren.save_warren()
                game.warren.save_pregnancy(game.warren)
                game.save_events()
                game.save_settings()
                game.switches['saved_warren'] = True
                self.update_buttons_and_text()


    def screen_switches(self):
        self.update_burrow_bg()
        game.switches['rabbit'] = None
        if game.warren.biome + game.warren.burrow_bg in game.warren.layouts:
            self.layout = game.warren.layouts[game.warren.biome + game.warren.burrow_bg]
        else:
            self.layout = game.warren.layouts["default"]

        self.choose_rabbit_positions()
        
        self.set_disabled_menu_buttons(["burrow_screen"])
        self.update_heading_text(f'{game.warren.name}')
        self.show_menu_buttons()

        # Creates and places the rabbit sprites.
        self.rabbit_buttons = []  # To contain all the buttons.

        # We have to convert the positions to something pygame_gui buttons will understand
        # This should be a temp solution. We should change the code that determines positions.
        i = 0
        for x in game.warren.warren_rabbits:
            if not Rabbit.all_rabbits[x].dead and Rabbit.all_rabbits[x].in_burrow and \
                    not (Rabbit.all_rabbits[x].exiled or Rabbit.all_rabbits[x].outside) and (Rabbit.all_rabbits[x].status != 'newborn' or game.config['fun']['all_rabbits_are_newborn'] or game.config['fun']['newborns_can_roam']):

                i += 1
                if i > self.max_sprites_displayed:
                    break

                try:
                    self.rabbit_buttons.append(
                        UISpriteButton(scale(pygame.Rect(tuple(Rabbit.all_rabbits[x].placement), (100, 100))),
                                       Rabbit.all_rabbits[x].sprite,
                                       rabbit_id=x,
                                       starting_height=i)
                    )
                except:
                    print(f"ERROR: placing {Rabbit.all_rabbits[x].name}\'s sprite on warren page")
                    
        # Den Labels
        # Redo the lorabbitions, so that it uses layout on the warren page
        self.rabbit_den_label = pygame_gui.elements.UIImage(
            scale(pygame.Rect(self.layout["rabbit den"], (242, 56))),
            pygame.transform.scale(
                image_cache.load_image('resources/images/rabbit_den.png'),
                (242, 56)))
        self.chief_rabbit_den_label = pygame_gui.elements.UIImage(
            scale(pygame.Rect(self.layout["chief rabbit den"], (224, 56))),
            pygame.transform.scale(
                image_cache.load_image('resources/images/chief_rabbit_den.png'),
                (224, 56)))
        self.med_den_label = UIImageButton(scale(pygame.Rect(
            self.layout["healing den"], (302, 56))),
            "",
            object_id="#med_den_button",
            starting_height=2
        )
        self.elder_den_label = pygame_gui.elements.UIImage(
            scale(pygame.Rect(self.layout["elder den"], (206, 56))),
            pygame.transform.scale(
                image_cache.load_image('resources/images/elder_den.png'),
                (206, 56)),
            )
        self.nursery_label = pygame_gui.elements.UIImage(scale(pygame.Rect(self.layout['nursery'], (160, 56))),
                                                         pygame.transform.scale(
                                                             image_cache.load_image('resources/images/nursery_den.png'),
                                                             (160, 56)))
        if game.warren.game_mode == 'classic':
            self.clearing_label = pygame_gui.elements.UIImage(
                scale(pygame.Rect(self.layout['clearing'], (162, 56))),
                pygame.transform.scale(
                    image_cache.load_image('resources/images/buttons/clearing.png'),
                    (162, 56)))
        else:
            self.clearing_label = UIImageButton(scale(pygame.Rect(
                self.layout['clearing'], (162, 56))),
                "",
                object_id="#clearing_button",
                starting_height=2
            )
        self.app_den_label = pygame_gui.elements.UIImage(
            scale(pygame.Rect(self.layout['rusasi den'], (294, 56))),
            pygame.transform.scale(
                image_cache.load_image('resources/images/app_den.png'),
                (294, 56)))

        # Draw the toggle and text
        self.show_den_labels = pygame_gui.elements.UIImage(scale(pygame.Rect((50, 1282), (334, 68))),
                                                           pygame.transform.scale(
                                                               image_cache.load_image(
                                                                   'resources/images/show_den_labels.png'),
                                                               (334, 68)))
        self.show_den_labels.disable()
        self.label_toggle = UIImageButton(scale(pygame.Rect((50, 1282), (64, 64))), "", object_id="#checked_checkbox")

        self.save_button = UIImageButton(scale(pygame.Rect(((686, 1286), (228, 60)))), "", object_id="#save_button")
        self.save_button.enable()
        self.save_button_saved_state = pygame_gui.elements.UIImage(
            scale(pygame.Rect((686, 1286), (228, 60))),
            pygame.transform.scale(
                image_cache.load_image('resources/images/save_warren_saved.png'),
                (228, 60)))
        self.save_button_saved_state.hide()
        self.save_button_saving_state = pygame_gui.elements.UIImage(
            scale(pygame.Rect((686, 1286), (228, 60))),
            pygame.transform.scale(
                image_cache.load_image('resources/images/save_warren_saving.png'),
                (228, 60)))
        self.save_button_saving_state.hide()

        self.update_buttons_and_text()

    def exit_screen(self):
        # removes the rabbit sprites.
        for button in self.rabbit_buttons:
            button.kill()
        self.rabbit_buttons = []

        # Kill all other elements, and destroy the reference so they aren't hanging around
        self.save_button.kill()
        del self.save_button
        self.save_button_saved_state.kill()
        del self.save_button_saved_state
        self.save_button_saving_state.kill()
        del self.save_button_saving_state
        self.rabbit_den_label.kill()
        del self.rabbit_den_label
        self.chief_rabbit_den_label.kill()
        del self.chief_rabbit_den_label
        self.med_den_label.kill()
        del self.med_den_label
        self.elder_den_label.kill()
        del self.elder_den_label
        self.nursery_label.kill()
        del self.nursery_label
        self.clearing_label.kill()
        del self.clearing_label
        self.app_den_label.kill()
        del self.app_den_label
        self.label_toggle.kill()
        del self.label_toggle
        self.show_den_labels.kill()
        del self.show_den_labels

        # reset save status
        game.switches['saved_warren'] = False

    def update_burrow_bg(self):
        light_dark = "light"
        if game.settings["dark mode"]:
            light_dark = "dark"

        burrow_bg_base_dir = 'resources/images/burrow_bg/'
        leaves = ["spring", "summer", "winter", "autumn"]
        burrow_nr = game.warren.burrow_bg

        if burrow_nr is None:
            burrow_nr = 'burrow1'
            game.warren.burrow_bg = burrow_nr

        available_biome = ['Forest', 'Mountainous', 'Plains', 'Beach']
        biome = game.warren.biome
        if biome not in available_biome:
            biome = available_biome[0]
            game.warren.biome = biome
        biome = biome.lower()

        all_backgrounds = []
        for leaf in leaves:
            platform_dir = f'{burrow_bg_base_dir}{biome}/{leaf}_{burrow_nr}_{light_dark}.png'
            all_backgrounds.append(platform_dir)

        self.spring_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[0]).convert(), (screen_x, screen_y))
        self.summer_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[1]).convert(), (screen_x, screen_y))
        self.winter_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[2]).convert(), (screen_x, screen_y))
        self.autumn_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[3]).convert(), (screen_x, screen_y))

    def choose_nonoverlapping_positions(self, first_choices, dens, weights=None):
        if not weights:
            weights = [1] * len(dens)

        dens = dens.copy()

        chosen_index = random.choices(range(0, len(dens)), weights=weights, k=1)[0]
        first_chosen_den = dens[chosen_index]
        while True:
            chosen_den = dens[chosen_index]
            if first_choices[chosen_den]:
                pos = random.choice(first_choices[chosen_den])
                first_choices[chosen_den].remove(pos)
                just_pos = pos[0].copy()
                if pos not in first_choices[chosen_den]:
                    # Then this is the second rabbit to be places here, given an offset

                    # Offset based on the "tag" in pos[1]. If "y" is in the tag,
                    # the rabbit will be offset down. If "x" is in the tag, the behavior depends on
                    # the presence of the "y" tag. If "y" is not present, always shift the rabbit left or right
                    # if it is present, shift the rabbit left or right 3/4 of the time.
                    if "x" in pos[1] and ("y" not in pos[1] or random.getrandbits(2)):
                        just_pos[0] += 15 * random.choice([-1, 1])
                    if "y" in pos[1]:
                        just_pos[1] += 15
                return tuple(just_pos)
            dens.pop(chosen_index)
            weights.pop(chosen_index)
            if not dens:
                break
            # Put finding the next index after the break condition, so it won't be done unless needed
            chosen_index = random.choices(range(0, len(dens)), weights=weights, k=1)[0]

        # If this code is reached, all position are filled.  Choose any position in the first den
        # checked, apply offsets.
        pos = random.choice(self.layout[first_chosen_den])
        just_pos = pos[0].copy()
        if "x" in pos[1] and random.getrandbits(1):
            just_pos[0] += 15 * random.choice([-1, 1])
        if "y" in pos[1]:
            just_pos[1] += 15
        return tuple(just_pos)

    def choose_rabbit_positions(self):
        """Determines the positions of rabbit on the warren screen."""
        # These are the first choices. As positions are chosen, they are removed from the options to indirabbite they are
        # taken.
        first_choices = deepcopy(self.layout)

        all_dens = ["nursery place", "chief rabbit place", "elder place", "healing place", "rusasi place",
                    "clearing place", "rabbit place"]

        # Allow two rabbit in the same position.
        for x in all_dens:
            first_choices[x].extend(first_choices[x])

        for x in game.warren.warren_rabbits:
            if Rabbit.all_rabbits[x].dead or Rabbit.all_rabbits[x].outside:
                continue

            # Newborns are not meant to be placed. They are hiding. 
            if Rabbit.all_rabbits[x].status == 'newborn' or game.config['fun']['all_rabbits_are_newborn']:
                if game.config['fun']['all_rabbits_are_newborn'] or game.config['fun']['newborns_can_roam']:
                    # Free them
                    Rabbit.all_rabbits[x].placement = self.choose_nonoverlapping_positions(first_choices, all_dens,
                                                                                     [1, 100, 1, 1, 1, 100, 50])
                else:
                    continue
 
            if Rabbit.all_rabbits[x].status in ['rusasi', 'trainee']:
                Rabbit.all_rabbits[x].placement = self.choose_nonoverlapping_positions(first_choices, all_dens,
                                                                                 [1, 50, 1, 1, 100, 100, 1])
            elif Rabbit.all_rabbits[x].status == 'captain':
                Rabbit.all_rabbits[x].placement = self.choose_nonoverlapping_positions(first_choices, all_dens,
                                                                                 [1, 50, 1, 1, 1, 50, 1])

            elif Rabbit.all_rabbits[x].status == 'elder':
                Rabbit.all_rabbits[x].placement = self.choose_nonoverlapping_positions(first_choices, all_dens,
                                                                                 [1, 1, 2000, 1, 1, 1, 1])
            elif Rabbit.all_rabbits[x].status == 'kitten':
                Rabbit.all_rabbits[x].placement = self.choose_nonoverlapping_positions(first_choices, all_dens,
                                                                                 [60, 8, 1, 1, 1, 1, 1])
            elif Rabbit.all_rabbits[x].status in [
                'healer rusasi', 'healer'
            ]:
                Rabbit.all_rabbits[x].placement = self.choose_nonoverlapping_positions(first_choices, all_dens,
                                                                                 [20, 20, 20, 400, 1, 1, 1])
            elif Rabbit.all_rabbits[x].status in ['rabbit', 'owsla']:
                Rabbit.all_rabbits[x].placement = self.choose_nonoverlapping_positions(first_choices, all_dens,
                                                                                 [1, 1, 1, 1, 1, 60, 60])
            elif Rabbit.all_rabbits[x].status == "chief rabbit":
                game.warren.chief_rabbit.placement = self.choose_nonoverlapping_positions(first_choices, all_dens,
                                                                                  [1, 200, 1, 1, 1, 1, 1])
                                                                                  

    def update_buttons_and_text(self):
        if game.switches['saved_warren']:
            self.save_button_saving_state.hide()
            self.save_button_saved_state.show()
            self.save_button.disable()
        else:
            self.save_button.enable()

        self.label_toggle.kill()
        if game.warren.warren_settings['den labels']:
            self.label_toggle = UIImageButton(scale(pygame.Rect((50, 1282), (68, 68))), "",
                                              object_id="#checked_checkbox")
            self.rabbit_den_label.show()
            self.clearing_label.show()
            self.nursery_label.show()
            self.app_den_label.show()
            self.chief_rabbit_den_label.show()
            self.med_den_label.show()
            self.elder_den_label.show()
        else:
            self.label_toggle = UIImageButton(scale(pygame.Rect((50, 1282), (68, 68))), "",
                                              object_id="#unchecked_checkbox")
            self.rabbit_den_label.hide()
            self.clearing_label.hide()
            self.nursery_label.hide()
            self.app_den_label.hide()
            self.chief_rabbit_den_label.hide()
            self.med_den_label.hide()
            self.elder_den_label.hide()
