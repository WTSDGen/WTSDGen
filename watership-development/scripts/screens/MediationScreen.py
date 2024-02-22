import pygame.transform
import pygame_gui.elements
from random import choice

from .Screens import Screens

from scripts.utility import get_text_box_theme, scale, shorten_text_to_fit
from scripts.rabbit.rabbits import Rabbit
from scripts.game_structure import image_cache
from scripts.game_structure.image_button import UIImageButton, UISpriteButton, UIRelationStatusBar
from scripts.game_structure.game_essentials import game, MANAGER


class MediationScreen(Screens):
    def __init__(self, name=None):
        super().__init__(name)
        self.back_button = None
        self.selected_chief = None
        self.selected_rabbit_1 = None
        self.selected_rabbit_2 = None
        self.chief_elements = {}
        self.chief = []
        self.rabbit_buttons = []
        self.page = 1
        self.selected_rabbit_elements = {}
        self.allow_romantic = True

    def handle_event(self, event):

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.change_screen('profile screen')
            elif event.ui_element == self.last_med:
                self.selected_chief -= 1
                self.update_chief_info()
            elif event.ui_element == self.next_med:
                self.selected_chief += 1
                self.update_chief_info()
            elif event.ui_element == self.next_page:
                self.page += 1
                self.update_page()
            elif event.ui_element == self.previous_page:
                self.page -= 1
                self.update_page()
            elif event.ui_element == self.romantic_checkbox:
                if self.allow_romantic:
                    self.allow_romantic = False
                else:
                    self.allow_romantic = True
                self.update_buttons()
            elif event.ui_element == self.deselect_1:
                self.selected_rabbit_1 = None
                self.update_selected_rabbits()
            elif event.ui_element == self.deselect_2:
                self.selected_rabbit_2 = None
                self.update_selected_rabbits()
            elif event.ui_element == self.mediate_button:
                game.mediated.append([self.selected_rabbit_1.ID, self.selected_rabbit_2.ID])
                game.patrolled.append(self.chief[self.selected_chief].ID)
                output = Rabbit.mediate_relationship(
                    self.chief[self.selected_chief], self.selected_rabbit_1, self.selected_rabbit_2,
                    self.allow_romantic)
                self.results.set_text(output)
                self.update_selected_rabbits()
                self.update_chief_info()
            elif event.ui_element == self.sabotoge_button:
                game.mediated.append(f"{self.selected_rabbit_1.ID}, {self.selected_rabbit_2.ID}")
                game.patrolled.append(self.chief[self.selected_chief].ID)
                output = Rabbit.mediate_relationship(
                    self.chief[self.selected_chief], self.selected_rabbit_1, self.selected_rabbit_2,
                    self.allow_romantic,
                    sabotage=True)
                self.results.set_text(output)
                self.update_selected_rabbits()
                self.update_chief_info()
            elif event.ui_element == self.random1:
                self.selected_rabbit_1 = self.random_rabbit()
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.selected_rabbit_2 = self.random_rabbit()
                self.update_selected_rabbits()
            elif event.ui_element == self.random2:
                self.selected_rabbit_2 = self.random_rabbit()
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.selected_rabbit_1 = self.random_rabbit()
                self.update_selected_rabbits()
            elif event.ui_element in self.rabbit_buttons:
                if event.ui_element.return_rabbit_object() not in [self.selected_rabbit_1, self.selected_rabbit_2]:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT or not self.selected_rabbit_1:
                        self.selected_rabbit_1 = event.ui_element.return_rabbit_object()
                    else:
                        self.selected_rabbit_2 = event.ui_element.return_rabbit_object()
                    self.update_selected_rabbits()

    def screen_switches(self):
        # Gather the chiefs:
        self.chief = []
        for rabbit in Rabbit.all_rabbits_list:
            if rabbit.status in ["chief rabbit"] and not (rabbit.dead or rabbit.outside):
                self.chief.append(rabbit)

        self.page = 1

        if self.chief:
            if Rabbit.fetch_rabbit(game.switches["rabbit"]) in self.chief:
                self.selected_chief = self.chief.index(Rabbit.fetch_rabbit(game.switches["rabbit"]))
            else:
                self.selected_chief = 0
        else:
            self.selected_chief = None

        self.back_button = UIImageButton(scale(pygame.Rect((50, 50), (210, 60))), "", object_id="#back_button")

        self.selected_frame_1 = pygame_gui.elements.UIImage(scale(pygame.Rect((100, 160), (400, 700))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/chief_selected_frame.png"),
                                                                (400, 700))
                                                            )
        self.selected_frame_1.disable()
        self.selected_frame_2 = pygame_gui.elements.UIImage(scale(pygame.Rect((1100, 160), (400, 700))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/chief_selected_frame.png"),
                                                                (400, 700))
                                                            )
        self.selected_frame_2.disable()

        self.rabbit_bg = pygame_gui.elements.UIImage(scale(pygame.Rect
                                                        ((100, 940), (1400, 300))),
                                                  pygame.transform.scale(
                                                      pygame.image.load(
                                                          "resources/images/mediation_selection_bg.png").convert_alpha(),
                                                      (1400, 300))
                                                  )
        self.rabbit_bg.disable()

        # Will be overwritten
        self.romantic_checkbox = None
        self.romantic_checkbox_text = pygame_gui.elements.UILabel(scale(pygame.Rect((737, 650), (200, 40))),
                                                                  "Allow romantic",
                                                                  object_id=get_text_box_theme(
                                                                      "#text_box_22_horizleft"),
                                                                  manager=MANAGER)

        self.mediate_button = UIImageButton(scale(pygame.Rect((560, 700), (210, 60))), "",
                                            object_id="#mediate_button",
                                            manager=MANAGER)
        self.sabotoge_button = UIImageButton(scale(pygame.Rect((800, 700), (218, 60))), "",
                                             object_id="#sabotage_button",
                                             manager=MANAGER)

        self.next_med = UIImageButton(scale(pygame.Rect((952, 540), (68, 68))), "", object_id="#arrow_right_button")
        self.last_med = UIImageButton(scale(pygame.Rect((560, 540), (68, 68))), "", object_id="#arrow_left_button")

        self.next_page = UIImageButton(scale(pygame.Rect((866, 1224), (68, 68))), "", object_id="#relation_list_next")
        self.previous_page = UIImageButton(scale(pygame.Rect((666, 1224), (68, 68))), "",
                                           object_id="#relation_list_previous")

        self.deselect_1 = UIImageButton(scale(pygame.Rect((136, 868), (254, 60))), "",
                                        object_id="#remove_rabbit_button")
        self.deselect_2 = UIImageButton(scale(pygame.Rect((1210, 868), (254, 60))), "",
                                        object_id="#remove_rabbit_button")

        self.results = pygame_gui.elements.UITextBox("",
                                                     scale(pygame.Rect((560, 770), (458, 200))),
                                                     object_id=get_text_box_theme(
                                                         "#text_box_22_horizcenter_spacing_95"),
                                                     manager=MANAGER)

        self.error = pygame_gui.elements.UITextBox("",
                                                   scale(pygame.Rect((560, 75), (458, 115))),
                                                   object_id=get_text_box_theme("#text_box_22_horizcenter_spacing_95"),
                                                   manager=MANAGER)

        self.random1 = UIImageButton(scale(pygame.Rect((396, 864), (68, 68))), "", object_id="#random_dice_button")
        self.random2 = UIImageButton(scale(pygame.Rect((1136, 864), (68, 68))), "", object_id="#random_dice_button")

        self.update_buttons()
        self.update_chief_info()

    def random_rabbit(self):
        if self.selected_rabbit_list():
            random_list = [i for i in self.all_rabbits_list if i.ID not in self.selected_rabbit_list()]
        else:
            random_list = self.all_rabbits_list
        return choice(random_list)

    def update_chief_info(self):
        for ele in self.chief_elements:
            self.chief_elements[ele].kill()
        self.chief_elements = {}

        if self.selected_chief is not None:  # It can be zero, so we must test for not None here.
            x_value = 630
            chief = self.chief[self.selected_chief]

            # Clear chief as selected rabbit
            if chief == self.selected_rabbit_1:
                self.selected_rabbit_1 = None
                self.update_selected_rabbits()
            if chief == self.selected_rabbit_2:
                self.selected_rabbit_2 = None
                self.update_selected_rabbits()

            self.chief_elements["chief_image"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((x_value, 180), (300, 300))),
                pygame.transform.scale(
                    chief.sprite, (300, 300)))

            name = str(chief.name)
            short_name = shorten_text_to_fit(name, 240, 22)
            self.chief_elements["name"] = pygame_gui.elements.UILabel(
                scale(pygame.Rect((x_value - 10, 480), (320, -1))),
                short_name,
                object_id=get_text_box_theme())

            text = chief.personality.trait + "\n" + chief.experience_level

            if chief.not_working():
                text += "\nThis rabbit isn't able to work"
                self.mediate_button.disable()
                self.sabotoge_button.disable()
            else:
                text += "\nThis rabbit can work"
                self.mediate_button.enable()
                self.sabotoge_button.enable()

            self.chief_elements["details"] = pygame_gui.elements.UITextBox(text,
                                                                              scale(pygame.Rect((x_value, 520),
                                                                                                (310, 120))),
                                                                              object_id=get_text_box_theme(
                                                                                  "#text_box_22_horizcenter_spacing_95"),
                                                                              manager=MANAGER)

            chief_number = len(self.chief)
            if self.selected_chief < chief_number - 1:
                self.next_med.enable()
            else:
                self.next_med.disable()

            if self.selected_chief > 0:
                self.last_med.enable()
            else:
                self.last_med.disable()

        else:
            self.last_med.disable()
            self.next_med.disable()

        self.update_buttons()
        self.update_list_rabbits()

    def update_list_rabbits(self):
        self.all_rabbits_list = [i for i in Rabbit.all_rabbits_list if
                              (i.ID != self.chief[self.selected_chief].ID) and not (i.dead or i.outside)]
        self.all_rabbits = self.chunks(self.all_rabbits_list, 24)

        self.update_page()

    def update_page(self):
        for rabbit in self.rabbit_buttons:
            rabbit.kill()
        self.rabbit_buttons = []

        if self.page > len(self.all_rabbits):
            self.page = len(self.all_rabbits)
        elif self.page < 1:
            self.page = 1

        if self.page >= len(self.all_rabbits):
            self.next_page.disable()
        else:
            self.next_page.enable()

        if self.page <= 1:
            self.previous_page.disable()
        else:
            self.previous_page.enable()

        x = 130
        y = 970
        for rabbit in self.all_rabbits[self.page - 1]:
            if game.warren.warren_settings["show fav"] and rabbit.favourite:
                _temp = pygame.transform.scale(
                            pygame.image.load(
                                f"resources/images/fav_marker.png").convert_alpha(),
                            (100, 100))
                    
                self.rabbit_buttons.append(
                    pygame_gui.elements.UIImage(
                        scale(pygame.Rect((x, y), (100, 100))),
                        _temp))
                self.rabbit_buttons[-1].disable()
            
            self.rabbit_buttons.append(
                UISpriteButton(scale(pygame.Rect((x, y), (100, 100))), rabbit.sprite, rabbit_object=rabbit)
            )
            x += 110
            if x > 1400:
                y += 110
                x = 130

    def update_selected_rabbits(self):
        for ele in self.selected_rabbit_elements:
            self.selected_rabbit_elements[ele].kill()
        self.selected_rabbit_elements = {}

        self.draw_info_block(self.selected_rabbit_1, (100, 160))
        self.draw_info_block(self.selected_rabbit_2, (1100, 160))

        self.update_buttons()

    def draw_info_block(self, rabbit, starting_pos: tuple):
        if not rabbit:
            return

        other_rabbit = [Rabbit.fetch_rabbit(i) for i in self.selected_rabbit_list() if i != rabbit.ID]
        if other_rabbit:
            other_rabbit = other_rabbit[0]
        else:
            other_rabbit = None

        tag = str(starting_pos)

        x = starting_pos[0]
        y = starting_pos[1]

        self.selected_rabbit_elements["rabbit_image" + tag] = pygame_gui.elements.UIImage(
            scale(pygame.Rect((x + 100, y + 14), (200, 200))),
            pygame.transform.scale(
                rabbit.sprite, (200, 200)))

        name = str(rabbit.name)
        short_name = shorten_text_to_fit(name, 250, 30)
        self.selected_rabbit_elements["name" + tag] = pygame_gui.elements.UILabel(
            scale(pygame.Rect((x, y + 200), (400, 60))),
            short_name,
            object_id="#text_box_30_horizcenter")

        # Gender
        if rabbit.genderalign == 'doe':
            gender_icon = image_cache.load_image("resources/images/doe_big.png").convert_alpha()
        elif rabbit.genderalign == 'buck':
            gender_icon = image_cache.load_image("resources/images/buck_big.png").convert_alpha()
        elif rabbit.genderalign == 'trans doe':
            gender_icon = image_cache.load_image("resources/images/transfem_big.png").convert_alpha()
        elif rabbit.genderalign == 'trans buck':
            gender_icon = image_cache.load_image("resources/images/transmasc_big.png").convert_alpha()
        else:
            # Everyone else gets the nonbinary icon
            gender_icon = image_cache.load_image("resources/images/nonbi_big.png").convert_alpha()

        self.selected_rabbit_elements["gender" + tag] = pygame_gui.elements.UIImage(
            scale(pygame.Rect((x + 320, y + 24), (50, 50))),
            pygame.transform.scale(gender_icon,
                                   (50, 50)))

        related = False
        # MATE
        if other_rabbit and len(rabbit.mate) > 0 and other_rabbit.ID in rabbit.mate:
            self.selected_rabbit_elements['mate_icon' + tag] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((x + 28, y + 28),
                                  (44, 40))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/heart_big.png").convert_alpha(),
                    (44, 40)))
        elif other_rabbit:
            # FAMILY DOT
            # Only show family dot on cousins if first cousin mates are disabled.
            if game.warren.warren_settings['first cousin mates']:
                check_cousins = False
            else:
                check_cousins = other_rabbit.is_cousin(rabbit)

            if other_rabbit.is_uncle_aunt(rabbit) or rabbit.is_uncle_aunt(other_rabbit) \
                    or other_rabbit.is_grandparent(rabbit) or \
                    rabbit.is_grandparent(other_rabbit) or \
                    other_rabbit.is_parent(rabbit) or \
                    rabbit.is_parent(other_rabbit) or \
                    other_rabbit.is_sibling(rabbit) or check_cousins:
                related = True
                self.selected_rabbit_elements['relation_icon' + tag] = pygame_gui.elements.UIImage(
                    scale(pygame.Rect((x + 28,
                                       y + 28),
                                      (36, 36))),
                    pygame.transform.scale(
                        image_cache.load_image(
                            "resources/images/dot_big.png").convert_alpha(),
                        (36, 36)))

        col1 = str(rabbit.months)
        if rabbit.months == 1:
            col1 += " month"
        else:
            col1 += " months"
        if len(rabbit.personality.trait) > 15:
            _t = rabbit.personality.trait[:13] + ".."
        else:
            _t = rabbit.personality.trait
        col1 += "\n" + _t
        self.selected_rabbit_elements["col1" + tag] = pygame_gui.elements.UITextBox(col1,
                                                                                 scale(pygame.Rect((x + 42, y + 252),
                                                                                                   (180, -1))),
                                                                                 object_id="#text_box_22_horizleft_spacing_95",
                                                                                 manager=MANAGER)

        mates = False
        if len(rabbit.mate) > 0:
            col2 = "has a mate"
            if other_rabbit:
                if other_rabbit.ID in rabbit.mate:
                    mates = True
                    col2 = f"{other_rabbit.name}'s mate"
        else:
            col2 = "mate: none"

        # Relation info:
        if related and other_rabbit and not mates:
            col2 += "\n"
            if other_rabbit.is_uncle_aunt(rabbit):
                if rabbit.genderalign in ['doe', 'trans doe']:
                    col2 += "niece"
                elif rabbit.genderalign in ['buck', 'trans buck']:
                    col2 += "nephew"
                else:
                    col2 += "sibling's child"
            elif rabbit.is_uncle_aunt(other_rabbit):
                if rabbit.genderalign in ['doe', 'trans doe']:
                    col2 += "aunt"
                elif rabbit.genderalign in ['buck', 'trans buck']:
                    col2 += "uncle"
                else:
                    col2 += "related: parent's sibling"
            elif rabbit.is_grandparent(other_rabbit):
                col2 += "grandparent"
            elif other_rabbit.is_grandparent(rabbit):
                col2 += "grandchild"
            elif rabbit.is_parent(other_rabbit):
                col2 += "parent"
            elif other_rabbit.is_parent(rabbit):
                col2 += "child"
            elif rabbit.is_sibling(other_rabbit) or other_rabbit.is_sibling(rabbit):
                col2 += "sibling"
            elif not game.warren.warren_settings["first cousin mates"] and other_rabbit.is_cousin(rabbit):
                col2 += "cousin"

        self.selected_rabbit_elements["col2" + tag] = pygame_gui.elements.UITextBox(col2,
                                                                                 scale(pygame.Rect((x + 220, y + 252),
                                                                                                   (161, -1))),
                                                                                 object_id="#text_box_22_horizleft_spacing_95",
                                                                                 manager=MANAGER)

        # ------------------------------------------------------------------------------------------------------------ #
        # RELATION BARS

        if other_rabbit:
            name = str(rabbit.name)
            short_name = shorten_text_to_fit(name, 136, 22)


            self.selected_rabbit_elements[f"relation_heading{tag}"] = pygame_gui.elements.UILabel(
                scale(pygame.Rect((x + 40, y + 320),
                                  (320, -1))),
                f"~~{short_name}'s feelings~~",
                object_id="#text_box_22_horizcenter")

            if other_rabbit.ID in rabbit.relationships:
                the_relationship = rabbit.relationships[other_rabbit.ID]
            else:
                the_relationship = rabbit.create_one_relationship(other_rabbit)

            barbar = 42
            bar_count = 0
            y_start = 354
            x_start = 50

            # ROMANTIC LOVE
            # CHECK AGE DIFFERENCE
            same_age = the_relationship.rabbit_to.age == rabbit.age
            adult_ages = ['young adult', 'adult', 'senior adult', 'senior']
            both_adult = the_relationship.rabbit_to.age in adult_ages and rabbit.age in adult_ages
            check_age = both_adult or same_age

            # If they are not both adults, or the same age, OR they are related, don't display any romantic affection,
            # even if they somehow have some. They should not be able to get any, but it never hurts to check.
            if not check_age or related:
                display_romantic = 0
                # Print, just for bug checking. Again, they should not be able to get love towards their relative.
                if the_relationship.romantic_love and related:
                    print(str(rabbit.name) + " has " + str(the_relationship.romantic_love) + " romantic love "
                                                                                          "towards their relative, " + str(
                        the_relationship.rabbit_to.name))
            else:
                display_romantic = the_relationship.romantic_love

            if display_romantic > 49:
                text = "romantic love:"
            else:
                text = "romantic like:"

            self.selected_rabbit_elements[f'romantic_text{tag}'] = pygame_gui.elements.UITextBox(text, scale(pygame.Rect(
                (x + x_start, y + y_start + (barbar * bar_count) - 10),
                (300, 60))),
                                                                                              object_id="#text_box_22_horizleft")
            self.selected_rabbit_elements[f'romantic_bar{tag}'] = UIRelationStatusBar(scale(pygame.Rect((x + x_start,
                                                                                                      y + y_start + 30 + (
                                                                                                              barbar * bar_count)),
                                                                                                     (300, 18))),
                                                                                   display_romantic,
                                                                                   positive_trait=True,
                                                                                   dark_mode=game.settings['dark mode']
                                                                                   )
            bar_count += 1

            # PLANTONIC
            if the_relationship.platonic_like > 49:
                text = "platonic love:"
            else:
                text = "platonic like:"
            self.selected_rabbit_elements[f'plantonic_text{tag}'] = pygame_gui.elements.UITextBox(text, scale(pygame.Rect(
                (x + x_start, y + y_start + (barbar * bar_count) - 10),
                (300, 60))),
                                                                                               object_id="#text_box_22_horizleft")
            self.selected_rabbit_elements[f'platonic_bar{tag}'] = UIRelationStatusBar(scale(pygame.Rect((x + x_start,
                                                                                                      y + y_start + 30 + (
                                                                                                              barbar * bar_count)),
                                                                                                     (300, 18))),
                                                                                   the_relationship.platonic_like,
                                                                                   positive_trait=True,
                                                                                   dark_mode=game.settings['dark mode'])

            bar_count += 1

            # DISLIKE
            if the_relationship.dislike > 49:
                text = "hate:"
            else:
                text = "dislike:"
            self.selected_rabbit_elements[f'dislike_text{tag}'] = pygame_gui.elements.UITextBox(text, scale(pygame.Rect(
                (x + x_start, y + y_start + (barbar * bar_count) - 10),
                (300, 60))),
                                                                                             object_id="#text_box_22_horizleft")
            self.selected_rabbit_elements[f'dislike_bar{tag}'] = UIRelationStatusBar(scale(pygame.Rect((x + x_start,
                                                                                                     y + y_start + 30 + (
                                                                                                             barbar * bar_count)),
                                                                                                    (300, 18))),
                                                                                  the_relationship.dislike,
                                                                                  positive_trait=False,
                                                                                  dark_mode=game.settings['dark mode'])

            bar_count += 1

            # ADMIRE
            if the_relationship.admiration > 49:
                text = "admiration:"
            else:
                text = "respect:"
            self.selected_rabbit_elements[f'admiration_text{tag}'] = pygame_gui.elements.UITextBox(text, scale(pygame.Rect(
                (x + x_start, y + y_start + (barbar * bar_count) - 10),
                (300, 60))),
                                                                                                object_id="#text_box_22_horizleft")
            self.selected_rabbit_elements[f'admiration_bar{tag}'] = UIRelationStatusBar(scale(pygame.Rect((x + x_start,
                                                                                                        y + y_start + 30 + (
                                                                                                                barbar * bar_count)),
                                                                                                       (300, 18))),
                                                                                     the_relationship.admiration,
                                                                                     positive_trait=True,
                                                                                     dark_mode=game.settings[
                                                                                         'dark mode'])

            bar_count += 1

            # COMFORTABLE
            if the_relationship.comfortable > 49:
                text = "security:"
            else:
                text = "comfortable:"
            self.selected_rabbit_elements[f'comfortable_text{tag}'] = pygame_gui.elements.UITextBox(text,
                                                                                                 scale(pygame.Rect(
                                                                                                     (x + x_start,
                                                                                                      y + y_start + (
                                                                                                              barbar * bar_count) - 10),
                                                                                                     (300, 60))),
                                                                                                 object_id="#text_box_22_horizleft")
            self.selected_rabbit_elements[f'comfortable_bar{tag}'] = UIRelationStatusBar(scale(pygame.Rect((x + x_start,
                                                                                                         y + y_start + 30 + (
                                                                                                                 barbar * bar_count)),
                                                                                                        (300, 18))),
                                                                                      the_relationship.comfortable,
                                                                                      positive_trait=True,
                                                                                      dark_mode=game.settings[
                                                                                          'dark mode'])

            bar_count += 1

            # JEALOUS
            if the_relationship.jealousy > 49:
                text = "resentment:"
            else:
                text = "jealousy:"
            self.selected_rabbit_elements[f'jealous_text{tag}'] = pygame_gui.elements.UITextBox(text, scale(pygame.Rect(
                (x + x_start, y + y_start + (barbar * bar_count) - 10),
                (300, 60))),
                                                                                             object_id="#text_box_22_horizleft")
            self.selected_rabbit_elements[f'jealous_bar{tag}'] = UIRelationStatusBar(scale(pygame.Rect((x + x_start,
                                                                                                     y + y_start + 30 + (
                                                                                                             barbar * bar_count)),
                                                                                                    (300, 18))),
                                                                                  the_relationship.jealousy,
                                                                                  positive_trait=False,
                                                                                  dark_mode=game.settings['dark mode'])

            bar_count += 1

            # TRUST
            if the_relationship.trust > 49:
                text = "reliance:"
            else:
                text = "trust:"
            self.selected_rabbit_elements[f'trust_text{tag}'] = pygame_gui.elements.UITextBox(text, scale(pygame.Rect(
                (x + x_start, y + y_start + (barbar * bar_count) - 10),
                (300, 60))),
                                                                                           object_id="#text_box_22_horizleft")
            self.selected_rabbit_elements[f'trust_bar{tag}'] = UIRelationStatusBar(scale(pygame.Rect((x + x_start,
                                                                                                   y + y_start + 30 + (
                                                                                                           barbar * bar_count)),
                                                                                                  (300, 18))),
                                                                                the_relationship.trust,
                                                                                positive_trait=True,
                                                                                dark_mode=game.settings['dark mode'])

    def selected_rabbit_list(self):
        output = []
        if self.selected_rabbit_1:
            output.append(self.selected_rabbit_1.ID)
        if self.selected_rabbit_2:
            output.append(self.selected_rabbit_2.ID)

        return output

    def update_buttons(self):
        error_message = ""

        invalid_chief = False
        if self.selected_chief is not None:
            if self.chief[self.selected_chief].not_working():
                invalid_chief = True
                error_message += "This chief can't work this month. "
            elif self.chief[self.selected_chief].ID in game.patrolled:
                invalid_chief = True
                error_message += "This chief has already worked this month. "
        else:
            invalid_chief = True

        invalid_pair = False
        if self.selected_rabbit_1 and self.selected_rabbit_2:
            for x in game.mediated:
                if self.selected_rabbit_1.ID in x and self.selected_rabbit_2.ID in x:
                    invalid_pair = True
                    error_message += "This pair has already been mediated this month. "
                    break
        else:
            invalid_pair = True

        self.error.set_text(error_message)

        if invalid_chief or invalid_pair:
            self.mediate_button.disable()
            self.sabotoge_button.disable()
        else:
            self.mediate_button.enable()
            self.sabotoge_button.enable()

        if self.romantic_checkbox:
            self.romantic_checkbox.kill()

        if self.allow_romantic:
            self.romantic_checkbox = UIImageButton(scale(pygame.Rect((642, 635), (68, 68))), "",
                                                   object_id="#checked_checkbox",
                                                   tool_tip_text="Allow effects on romantic like, if possible. ",
                                                   manager=MANAGER)
        else:
            self.romantic_checkbox = UIImageButton(scale(pygame.Rect((642, 635), (68, 68))), "",
                                                   object_id="#unchecked_checkbox",
                                                   tool_tip_text="Allow effects on romantic like, if possible. ",
                                                   manager=MANAGER)

    def exit_screen(self):
        self.selected_rabbit_1 = None
        self.selected_rabbit_2 = None

        for ele in self.chief_elements:
            self.chief_elements[ele].kill()
        self.chief_elements = {}

        for rabbit in self.rabbit_buttons:
            rabbit.kill()
        self.rabbit_buttons = []

        for ele in self.selected_rabbit_elements:
            self.selected_rabbit_elements[ele].kill()
        self.selected_rabbit_elements = {}

        self.chief = []
        self.back_button.kill()
        del self.back_button
        self.selected_frame_1.kill()
        del self.selected_frame_1
        self.selected_frame_2.kill()
        del self.selected_frame_2
        self.rabbit_bg.kill()
        del self.rabbit_bg
        self.mediate_button.kill()
        del self.mediate_button
        self.sabotoge_button.kill()
        del self.sabotoge_button
        self.last_med.kill()
        del self.last_med
        self.next_med.kill()
        del self.next_med
        self.deselect_1.kill()
        del self.deselect_1
        self.deselect_2.kill()
        del self.deselect_2
        self.next_page.kill()
        del self.next_page
        self.previous_page.kill()
        del self.previous_page
        self.results.kill()
        del self.results
        self.random1.kill()
        del self.random1
        self.random2.kill()
        del self.random2
        if self.romantic_checkbox:
            self.romantic_checkbox.kill()
            del self.romantic_checkbox
        self.romantic_checkbox_text.kill()
        del self.romantic_checkbox_text
        self.error.kill()
        del self.error

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]
