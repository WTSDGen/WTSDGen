import pygame
import pygame_gui
from math import ceil
from scripts.game_structure.image_button import UISpriteButton, UIImageButton
from .Screens import Screens

from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.rabbit.rabbits import Rabbit
from ..utility import get_text_box_theme, scale, shorten_text_to_fit


class OutsideWarrenScreen(Screens):

    list_page = 1  # Holds the current page
    display_rabbits = []  # Holds the rabbit sprite objects
    rabbit_names = []  # Holds the rabbit name text-box objects
    
    previous_search_text = ""

    def load_images(self):
        self.search_bar_image = pygame.transform.scale(pygame.image.load(
            "resources/images/search_bar.png").convert_alpha(), (456 / 1600 * screen_x, 68 / 1400 * screen_y))

    def __init__(self, name=None):
        super().__init__(name)
        self.filter_age = None
        self.filter_id = None
        self.filter_rank = None
        self.filter_exp = None
        self.filter_by_open = None
        self.filter_by_closed = None
        self.page_number = None
        self.previous_page_button = None
        self.next_page_button = None
        self.outside_warren_button = None
        self.your_warren_button = None
        self.to_dead_button = None
        self.filter_container = None
        self.living_rabbits = None
        self.all_pages = None
        self.current_listed_rabbits = None
        self.load_images()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.your_warren_button:
                self.change_screen("list screen")
            if event.ui_element == self.to_dead_button:
                self.change_screen("inle screen")
            elif event.ui_element in self.display_rabbits:
                game.switches["rabbit"] = event.ui_element.return_rabbit_id()
                self.change_screen('profile screen')
            elif event.ui_element == self.next_page_button:
                self.list_page += 1
                self.update_page()
            elif event.ui_element == self.previous_page_button:
                self.list_page -= 1
                self.update_page()
            elif event.ui_element == self.filter_by_closed:
                self.filter_by_closed.hide()
                self.filter_by_open.show()
                self.filter_rank.show()
                self.filter_id.show()
                self.filter_age.show()
                self.filter_exp.show()
            elif event.ui_element == self.filter_by_open:
                self.filter_by_open.hide()
                self.filter_by_closed.show()
                self.filter_options_visible = False
                self.filter_id.hide()
                self.filter_rank.hide()
                self.filter_age.hide()
                self.filter_exp.hide()
            elif event.ui_element == self.filter_age:
                self.filter_id.hide()
                self.filter_age.hide()
                self.filter_rank.hide()
                self.filter_exp.hide()
                self.filter_by_open.hide()
                self.filter_by_closed.show()
                game.sort_type = "reverse_age"
                Rabbit.sort_rabbits()
                self.get_living_rabbits()
                self.update_search_rabbits(self.search_bar.get_text())
            elif event.ui_element == self.filter_rank:
                self.filter_id.hide()
                self.filter_age.hide()
                self.filter_rank.hide()
                self.filter_exp.hide()
                self.filter_by_open.hide()
                self.filter_by_closed.show()
                game.sort_type = "rank"
                Rabbit.sort_rabbits()
                self.get_living_rabbits()
                self.update_search_rabbits(self.search_bar.get_text())
            elif event.ui_element == self.filter_id:
                self.filter_id.hide()
                self.filter_age.hide()
                self.filter_rank.hide()
                self.filter_exp.hide()
                self.filter_by_open.hide()
                self.filter_by_closed.show()
                game.sort_type = "id"
                Rabbit.sort_rabbits()
                self.get_living_rabbits()
                self.update_search_rabbits(self.search_bar.get_text())
            elif event.ui_element == self.filter_exp:
                self.filter_id.hide()
                self.filter_age.hide()
                self.filter_rank.hide()
                self.filter_exp.hide()
                self.filter_by_open.hide()
                self.filter_by_closed.show()
                game.sort_type = "exp"
                Rabbit.sort_rabbits()
                self.get_living_rabbits()
                self.update_search_rabbits(self.search_bar.get_text())
            elif event.ui_element in self.display_rabbits:
                game.switches["rabbit"] = event.ui_element.return_rabbit_id()
                self.change_screen('profile screen')
            else:
                self.menu_button_pressed(event)
        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if self.search_bar.is_focused:
                return
            if event.key == pygame.K_LEFT:
                self.change_screen("warren screen")
            elif event.key == pygame.K_RIGHT:
                self.change_screen('patrol screen')

    def get_living_rabbits(self):
        self.living_rabbits = []
        for the_rabbit in Rabbit.all_rabbits_list:
            if not the_rabbit.dead and the_rabbit.outside:
                self.living_rabbits.append(the_rabbit)

    def screen_switches(self):
        
        # Determine the living, non-exiled rabbits.
        self.get_living_rabbits()

        self.search_bar = pygame_gui.elements.UITextEntryLine(scale(pygame.Rect((845, 278), (294, 55))),
                                                              object_id="#search_entry_box", manager=MANAGER)

        self.your_warren_button = UIImageButton(scale(pygame.Rect((230, 270), (68, 68))), "", object_id="#your_warren_button")
        self.outside_warren_button = UIImageButton(scale(pygame.Rect((298, 270), (68, 68))), "",
                                                 object_id="#outside_warren_button", manager=MANAGER)
        self.outside_warren_button.disable()
        self.to_dead_button = UIImageButton(scale(pygame.Rect((560, 270), (134, 68))), "",
                                                 object_id="#to_dead_button", manager=MANAGER,
                                                tool_tip_text='view rabbits in the afterlife')
        self.next_page_button = UIImageButton(scale(pygame.Rect((912, 1190), (68, 68))), "", object_id="#arrow_right_button")
        self.previous_page_button = UIImageButton(scale(pygame.Rect((620, 1190), (68, 68))), "",
                                                  object_id="#arrow_left_button", manager=MANAGER)
        self.page_number = pygame_gui.elements.UITextBox("", scale(pygame.Rect((680, 1190), (220, 60))),
                                                         object_id=get_text_box_theme("#text_box_30_horizcenter"),
                                                         manager=MANAGER)  # Text will be filled in later

        self.set_disabled_menu_buttons(["rabbitlist_screen"])
        self.update_heading_text('Outside The warren')
        self.show_menu_buttons()
        self.update_search_rabbits("")  # This will list all the rabbits, and create the button objects.

        x_pos = 1152
        y_pos = 270
        self.filter_by_closed = UIImageButton(
            scale(pygame.Rect((x_pos, y_pos), (196, 68))),
            "",
            object_id="#filter_by_closed_button",
            tool_tip_text="By default, rabbits are sorted by rank.", manager=MANAGER
        )
        self.filter_by_open = UIImageButton(
            scale(pygame.Rect((x_pos, y_pos), (196, 68))),
            "",
            object_id="#filter_by_open_button", manager=MANAGER
        )
        self.filter_by_open.hide()
        y_pos += 68

        self.filter_rank = UIImageButton(
            scale(pygame.Rect((x_pos - 2, y_pos), (204, 58))),
            "",
            object_id="#filter_rank_button",
            starting_height=2, manager=MANAGER
        )
        self.filter_rank.hide()
        y_pos += 58
        self.filter_age = UIImageButton(
            scale(pygame.Rect((x_pos - 2, y_pos), (204, 58))),
            "",
            object_id="#filter_age_button",
            starting_height=2, manager=MANAGER
        )
        self.filter_age.hide()
        y_pos += 58
        self.filter_id = UIImageButton(
            scale(pygame.Rect((x_pos - 2, y_pos), (204, 58))),
            "",
            object_id="#filter_ID_button",
            starting_height=2, manager=MANAGER
        )
        self.filter_id.hide()
        y_pos += 58
        self.filter_exp = UIImageButton(
            scale(pygame.Rect((x_pos - 2, y_pos), (204, 58))),
            "",
            object_id="#filter_exp_button",
            starting_height=2, manager=MANAGER
        )
        self.filter_exp.hide()

    def exit_screen(self):
        self.hide_menu_buttons()
        self.your_warren_button.kill()
        self.outside_warren_button.kill()
        self.to_dead_button.kill()
        self.next_page_button.kill()
        self.previous_page_button.kill()
        self.page_number.kill()
        self.search_bar.kill()
        self.filter_by_closed.kill()
        self.filter_by_open.kill()
        self.filter_rank.kill()
        self.filter_age.kill()
        self.filter_id.kill()
        self.filter_exp.kill()

        # Remove currently displayed rabbits and rabbit names.
        for rabbit in self.display_rabbits:
            rabbit.kill()
        self.display_rabbits = []

        for name in self.rabbit_names:
            name.kill()
        self.rabbit_names = []

    def update_search_rabbits(self, search_text):
        """Run this function when the search text changes, or when the screen is switched to."""
        self.current_listed_rabbits = []
        search_text = search_text.strip()
        if search_text != '':
            for rabbit in self.living_rabbits:
                if search_text.lower() in str(rabbit.name).lower():
                    self.current_listed_rabbits.append(rabbit)
        else:
            self.current_listed_rabbits = self.living_rabbits.copy()

        self.all_pages = int(ceil(len(self.current_listed_rabbits) /
                                  20.0)) if len(self.current_listed_rabbits) > 20 else 1

        self.update_page()

    def update_page(self):
        """Run this function when page changes."""
        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.list_page > self.all_pages:
            self.list_page = self.all_pages

        # Handle which next buttons are clickable.
        if self.all_pages <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.list_page >= self.all_pages:
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.list_page == 1 and self.all_pages > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()

        self.page_number.set_text(str(self.list_page) + "/" + str(self.all_pages))

        # Remove the images for currently listed rabbits
        for rabbit in self.display_rabbits:
            rabbit.kill()
        self.display_rabbits = []

        for name in self.rabbit_names:
            name.kill()
        self.rabbit_names = []

        # Generate object for the current rabbits
        pos_x = 0
        pos_y = 0
        if self.current_listed_rabbits:
            for rabbit in self.chunks(self.current_listed_rabbits, 20)[self.list_page - 1]:
                #update_sprite(rabbit)
                
                if rabbit.favourite:
                    
                    _temp = pygame.transform.scale(
                            pygame.image.load(
                                f"resources/images/fav_marker.png").convert_alpha(),
                            (100, 100))
                    
                    _temp.set_alpha(150)
                    
                    self.display_rabbits.append(
                        pygame_gui.elements.UIImage(
                            scale(pygame.Rect((260 + pos_x, 360 + pos_y), (100, 100))),
                            _temp))
                    self.display_rabbits[-1].disable()
                
                self.display_rabbits.append(
                    UISpriteButton(scale(pygame.Rect
                                   ((260 + pos_x, 360 + pos_y), (100, 100))),
                                   rabbit.sprite,
                                   rabbit.ID,
                                   starting_height=1, manager=MANAGER))

                name = str(rabbit.name)
                short_name = shorten_text_to_fit(name, 220, 30)

                self.rabbit_names.append(pygame_gui.elements.ui_label.UILabel(scale(pygame.Rect((160 + pos_x, 460 + pos_y), (300, 60))), short_name, object_id=get_text_box_theme("#text_box_30_horizcenter"), manager=MANAGER))
                pos_x += 240
                if pos_x >= 1200:
                    pos_x = 0
                    pos_y += 200

    def on_use(self):

        # Only update the postions if the search text changes
        if self.search_bar.get_text() != self.previous_search_text:
            self.update_search_rabbits(self.search_bar.get_text())
        self.previous_search_text = self.search_bar.get_text()

        screen.blit(self.search_bar_image, (696/1600 * screen_x, 270/1400 * screen_y))

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]
