import pygame.transform
import pygame_gui.elements
from random import choice


from .Screens import Screens

from scripts.utility import get_text_box_theme, scale, scale_dimentions, shorten_text_to_fit
from scripts.rabbit.rabbits import Rabbit
from scripts.game_structure import image_cache
from scripts.game_structure.image_button import UIImageButton, UISpriteButton, UIRelationStatusBar
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.game_structure.windows import RelationshipLog
from scripts.game_structure.propagating_thread import PropagatingThread


class RelationshipScreen(Screens):
    checkboxes = {}  # To hold the checkboxes.
    focus_rabbit_elements = {}
    relation_list_elements = {}
    sprite_buttons = {}
    inspect_rabbit_elements = {}
    previous_search_text = ""

    current_page = 1

    inspect_rabbit = None

    search_bar = pygame.transform.scale(
        image_cache.load_image("resources/images/relationship_search.png").convert_alpha(),
        (456 / 1600 * screen_x, 78 / 1400 * screen_y)
    )
    details_frame = pygame.transform.scale(
        image_cache.load_image("resources/images/relationship_details_frame.png").convert_alpha(),
        (508 / 1600 * screen_x,
         688 / 1400 * screen_y)
    )
    toggle_frame = pygame.transform.scale(
        image_cache.load_image("resources/images/relationship_toggle_frame.png").convert_alpha(),
        (502 / 1600 * screen_x, 240 / 1400 * screen_y)
    )
    list_frame = pygame.transform.scale(
        image_cache.load_image("resources/images/relationship_list_frame.png").convert_alpha(),
        (1004 / 1600 * screen_x, 1000 / 1400 * screen_y)
    )

    def __init__(self, name=None):
        super().__init__(name)
        self.all_relations = None
        self.the_rabbit = None
        self.previous_rabbit = None
        self.next_rabbit = None
        self.view_profile_button = None
        self.switch_focus_button = None
        self.page_number = None
        self.next_page_button = None
        self.previous_page_button = None
        self.show_empty_text = None
        self.show_dead_text = None
        self.back_button = None
        self.next_rabbit_button = None
        self.previous_rabbit_button = None
        self.log_icon = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.sprite_buttons.values():
                self.inspect_rabbit = event.ui_element.return_rabbit_object()
                self.update_inspected_relation()
            elif event.ui_element == self.back_button:
                self.change_screen("profile screen")
            elif event.ui_element == self.switch_focus_button:
                game.switches["rabbit"] = self.inspect_rabbit.ID
                self.update_focus_rabbit()
            elif event.ui_element == self.view_profile_button:
                game.switches["rabbit"] = self.inspect_rabbit.ID
                self.change_screen('profile screen')
            elif event.ui_element == self.next_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.next_rabbit), Rabbit):
                    game.switches["rabbit"] = self.next_rabbit
                    self.update_focus_rabbit()
                else:
                    print("invalid next rabbit", self.next_rabbit)
            elif event.ui_element == self.previous_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.previous_rabbit), Rabbit):
                    game.switches["rabbit"] = self.previous_rabbit
                    self.update_focus_rabbit()
                else:
                    print("invalid previous rabbit", self.previous_rabbit)
            elif event.ui_element == self.previous_page_button:
                self.current_page -= 1
                self.update_rabbit_page()
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                self.update_rabbit_page()
            elif event.ui_element == self.log_icon:
                if self.inspect_rabbit.ID not in self.the_rabbit.relationships:
                    return
                RelationshipLog(
                    self.the_rabbit.relationships[self.inspect_rabbit.ID],
                    [self.view_profile_button, self.switch_focus_button,\
                        self.next_rabbit_button,self.previous_rabbit_button,self.next_page_button],
                    [self.back_button, self.log_icon, self.checkboxes["show_dead"], self.checkboxes["show_empty"],\
                     self.show_dead_text, self.show_empty_text]
                )
            elif event.ui_element == self.checkboxes["show_dead"]:
                game.warren.warren_settings['show dead relation'] = not game.warren.warren_settings['show dead relation']
                self.update_checkboxes()
                self.apply_rabbit_filter()
                self.update_rabbit_page()
            elif event.ui_element == self.checkboxes["show_empty"]:
                game.warren.warren_settings['show empty relation'] = not game.warren.warren_settings['show empty relation'] 
                self.update_checkboxes()
                self.apply_rabbit_filter()
                self.update_rabbit_page()

    def screen_switches(self):

        self.previous_rabbit_button = UIImageButton(scale(pygame.Rect((50, 50), (306, 60))), "",
                                                 object_id="#previous_rabbit_button")
        self.next_rabbit_button = UIImageButton(scale(pygame.Rect((1244, 50), (306, 60))), "",
                                             object_id="#next_rabbit_button")
        self.back_button = UIImageButton(scale(pygame.Rect((50, 1290), (210, 60))), "", object_id="#back_button")

        self.search_bar = pygame_gui.elements.UITextEntryLine(scale(pygame.Rect((1220, 194), (290, 46))),
                                                              object_id="#search_entry_box")

        self.show_dead_text = pygame_gui.elements.UITextBox("Show Dead", scale(pygame.Rect((220, 1010), (200, 60))),
                                                            object_id="#text_box_30_horizleft")
        self.show_empty_text = pygame_gui.elements.UITextBox("Show Empty", scale(pygame.Rect((220, 1100), (200, 60))),
                                                             object_id="#text_box_30_horizleft")

        # Draw the checkboxes
        self.update_checkboxes()

        self.previous_page_button = UIImageButton(scale(pygame.Rect((880, 1232), (68, 68))), "",
                                                  object_id="#relation_list_previous")
        self.next_page_button = UIImageButton(scale(pygame.Rect((1160, 1232), (68, 68))), "",
                                              object_id="#relation_list_next")

        self.page_number = pygame_gui.elements.UITextBox("", scale(pygame.Rect((890, 1234), (300, 68))),
                                                         object_id=get_text_box_theme("#text_box_30_horizcenter"))

        self.switch_focus_button = UIImageButton(scale(pygame.Rect((170, 780), (272, 60))), "",
                                                 object_id="#switch_focus_button")
        self.switch_focus_button.disable()
        self.view_profile_button = UIImageButton(scale(pygame.Rect((170, 840), (272, 60))), "",
                                                 object_id="#view_profile_button")
        self.view_profile_button.disable()

        self.log_icon = UIImageButton(scale(pygame.Rect((445, 808), (68, 68))), "",
                                                 object_id="#log_icon")
        self.log_icon.disable()

        # Updates all info for the currently focused rabbit.
        self.update_focus_rabbit()

    def exit_screen(self):
        for ele in self.checkboxes:
            self.checkboxes[ele].kill()
        self.checkboxes = {}

        for ele in self.focus_rabbit_elements:
            self.focus_rabbit_elements[ele].kill()
        self.focus_rabbit_elements = {}

        for ele in self.relation_list_elements:
            self.relation_list_elements[ele].kill()
        self.relation_list_elements = {}

        for ele in self.sprite_buttons:
            self.sprite_buttons[ele].kill()
        self.sprite_buttons = {}

        for ele in self.inspect_rabbit_elements:
            self.inspect_rabbit_elements[ele].kill()
        self.inspect_rabbit_elements = {}

        self.previous_rabbit_button.kill()
        del self.previous_rabbit_button
        self.next_rabbit_button.kill()
        del self.next_rabbit_button
        self.back_button.kill()
        del self.back_button
        self.search_bar.kill()
        del self.search_bar
        self.show_dead_text.kill()
        del self.show_dead_text
        self.show_empty_text.kill()
        del self.show_empty_text
        self.previous_page_button.kill()
        del self.previous_page_button
        self.next_page_button.kill()
        del self.next_page_button
        self.page_number.kill()
        del self.page_number
        self.switch_focus_button.kill()
        del self.switch_focus_button
        self.view_profile_button.kill()
        del self.view_profile_button
        self.log_icon.kill()
        del self.log_icon

    def get_previous_next_rabbit(self):
        """Determines where the previous the next buttons should lead, and enables/diables them"""
        """'Determines where the next and previous buttons point too."""

        is_instructor = False
        if self.the_rabbit.dead and game.warren.instructor.ID == self.the_rabbit.ID:
            is_instructor = True

        previous_rabbit = 0
        next_rabbit = 0
        if self.the_rabbit.dead and not is_instructor and not self.the_rabbit.df:
            previous_rabbit = game.warren.instructor.ID

        if is_instructor:
            next_rabbit = 1

        for check_rabbit in Rabbit.all_rabbits_list:
            if check_rabbit.ID == self.the_rabbit.ID:
                next_rabbit = 1
            else:
                if next_rabbit == 0 and check_rabbit.ID != self.the_rabbit.ID and check_rabbit.dead == self.the_rabbit.dead and \
                        check_rabbit.ID != game.warren.instructor.ID and check_rabbit.outside == self.the_rabbit.outside and \
                        check_rabbit.df == self.the_rabbit.df and not check_rabbit.faded:
                    previous_rabbit = check_rabbit.ID

                elif next_rabbit == 1 and check_rabbit.ID != self.the_rabbit.ID and check_rabbit.dead == self.the_rabbit.dead and \
                        check_rabbit.ID != game.warren.instructor.ID and check_rabbit.outside == self.the_rabbit.outside and \
                        check_rabbit.df == self.the_rabbit.df and not check_rabbit.faded:
                    next_rabbit = check_rabbit.ID

                elif int(next_rabbit) > 1:
                    break

        if next_rabbit == 1:
            next_rabbit = 0

        self.next_rabbit = next_rabbit
        self.previous_rabbit = previous_rabbit

        if self.next_rabbit == 0:
            self.next_rabbit_button.disable()
        else:
            self.next_rabbit_button.enable()

        if self.previous_rabbit == 0:
            self.previous_rabbit_button.disable()
        else:
            self.previous_rabbit_button.enable()

    def update_checkboxes(self):
        # Remove all checkboxes
        for ele in self.checkboxes:
            self.checkboxes[ele].kill()
        self.checkboxes = {}

        if game.warren.warren_settings['show dead relation']:
            checkbox_type = "#checked_checkbox"
        else:
            checkbox_type = "#unchecked_checkbox"

        self.checkboxes["show_dead"] = UIImageButton(scale(pygame.Rect((156, 1010), (68, 68))), "",
                                                     object_id=checkbox_type)

        if game.warren.warren_settings['show empty relation']:
            checkbox_type = "#checked_checkbox"
        else:
            checkbox_type = "#unchecked_checkbox"

        self.checkboxes["show_empty"] = UIImageButton(scale(pygame.Rect((156, 1100), (68, 68))), "",
                                                      object_id=checkbox_type)

    def update_focus_rabbit(self):
        for ele in self.focus_rabbit_elements:
            self.focus_rabbit_elements[ele].kill()
        self.focus_rabbit_elements = {}

        self.the_rabbit = Rabbit.all_rabbits.get(game.switches['rabbit'],
                                        game.warren.instructor
                                        )

        self.current_page = 1
        self.inspect_rabbit = None

        # Keep a list of all the relations
        if game.config["sorting"]["sort_by_rel_total"]:
            self.all_relations = sorted(self.the_rabbit.relationships.values(),
                                        key=lambda x: sum(map(abs, [x.romantic_love, x.platonic_like, x.dislike, x.admiration, x.comfortable, x.jealousy, x.trust])),
                                        reverse=True)
        else:
            self.all_relations = list(self.the_rabbit.relationships.values()).copy()

        self.focus_rabbit_elements["header"] = pygame_gui.elements.UITextBox(str(self.the_rabbit.name) + " Relationships",
                                                                          scale(pygame.Rect((150, 150), (800, 100))),
                                                                          object_id=get_text_box_theme(
                                                                              "#text_box_34_horizleft"))
        self.focus_rabbit_elements["details"] = pygame_gui.elements.UITextBox(self.the_rabbit.genderalign + " - " + \
                                                                           str(self.the_rabbit.months) + " months - " + \
                                                                           self.the_rabbit.personality.trait,
                                                                           scale(pygame.Rect((160, 210), (800, 60))),
                                                                           object_id=get_text_box_theme(
                                                                               "#text_box_22_horizleft"))
        self.focus_rabbit_elements["image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((50, 150), (100, 100))),
                                                                       self.the_rabbit.sprite)

        self.get_previous_next_rabbit()
        self.apply_rabbit_filter(self.search_bar.get_text())
        self.update_inspected_relation()
        self.update_rabbit_page()

    def update_inspected_relation(self):
        for ele in self.inspect_rabbit_elements:
            self.inspect_rabbit_elements[ele].kill()
        self.inspect_rabbit_elements = {}

        if self.inspect_rabbit is not None:
            # NAME LENGTH
            chosen_name = str(self.inspect_rabbit.name)
            if 19 <= len(chosen_name):
                if self.inspect_rabbit.dead:
                    chosen_short_name = str(self.inspect_rabbit.name)[0:11]
                    chosen_name = chosen_short_name + '...'
                    chosen_name += " (dead)"
                else:
                    chosen_short_name = str(self.inspect_rabbit.name)[0:16]
                    chosen_name = chosen_short_name + '...'

            self.inspect_rabbit_elements["name"] = pygame_gui.elements.ui_label.UILabel(
                scale(pygame.Rect((150, 590), (300, 80))),
                chosen_name,
                object_id="#text_box_34_horizcenter")

            # Rabbit Image
            self.inspect_rabbit_elements["image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((150, 290), (300, 300))),
                                                                             pygame.transform.scale(
                                                                                 self.inspect_rabbit.sprite,
                                                                                 (300, 300)))

            related = False
            # Mate Heart
            # TODO: UI UPDATE IS NEEDED
            if len(self.the_rabbit.mate) > 0 and self.inspect_rabbit.ID in self.the_rabbit.mate:
                self.inspect_rabbit_elements["mate"] = pygame_gui.elements.UIImage(scale(pygame.Rect((90, 300), (44, 40))),
                                                                                pygame.transform.scale(
                                                                                    image_cache.load_image(
                                                                                        "resources/images/heart_big.png").convert_alpha(),
                                                                                    (44, 40)))
            else:
                # Family Dot
                related = self.the_rabbit.is_related(self.inspect_rabbit, game.warren.warren_settings["first cousin mates"])
                if related:
                    self.inspect_rabbit_elements['family'] = pygame_gui.elements.UIImage(
                        scale(pygame.Rect((90, 300), (36, 36))),
                        pygame.transform.scale(
                            image_cache.load_image(
                                "resources/images/dot_big.png").convert_alpha(),
                            (36, 36)))

            # Gender
            if self.inspect_rabbit.genderalign == 'doe':
                gender_icon = image_cache.load_image("resources/images/doe_big.png").convert_alpha()
            elif self.inspect_rabbit.genderalign == 'buck':
                gender_icon = image_cache.load_image("resources/images/buck_big.png").convert_alpha()
            elif self.inspect_rabbit.genderalign == 'trans doe':
                gender_icon = image_cache.load_image("resources/images/transfem_big.png").convert_alpha()
            elif self.inspect_rabbit.genderalign == 'trans buck':
                gender_icon = image_cache.load_image("resources/images/transmasc_big.png").convert_alpha()
            else:
                # Everyone else gets the nonbinary icon
                gender_icon = image_cache.load_image("resources/images/nonbi_big.png").convert_alpha()

            self.inspect_rabbit_elements["gender"] = pygame_gui.elements.UIImage(scale(pygame.Rect((470, 290), (68, 68))),
                                                                              pygame.transform.scale(gender_icon,
                                                                                                     (68, 68)))

            # Column One Details:
            col1 = ""
            # Gender-Align
            col1 += self.inspect_rabbit.genderalign + "\n"

            # Age
            col1 += f"{self.inspect_rabbit.months} months\n"

            # Trait
            col1 += f"{self.inspect_rabbit.personality.trait}\n"

            self.inspect_rabbit_elements["col1"] = pygame_gui.elements.UITextBox(col1,
                                                                              scale(pygame.Rect((120, 650), (180, 180))),
                                                                              object_id="#text_box_22_horizleft_spacing_95",
                                                                              manager=MANAGER)

            # Column Two Details:
            col2 = ""

            # Mate
            if len(self.inspect_rabbit.mate) > 0 and self.the_rabbit.ID not in self.inspect_rabbit.mate:
                col2 += "has a mate\n"
            elif len(self.the_rabbit.mate) > 0 and self.inspect_rabbit.ID in self.the_rabbit.mate:
                col2 += f"{self.the_rabbit.name}'s mate\n"
            else:
                col2 += "mate: none\n"

            # Relation info:
            if related:
                if self.the_rabbit.is_uncle_aunt(self.inspect_rabbit):
                    if self.inspect_rabbit.genderalign in ['doe', 'trans doe']:
                        col2 += "related: niece"
                    elif self.inspect_rabbit.genderalign in ['buck', 'trans buck']:
                        col2 += "related: nephew"
                    else:
                        col2 += "related: sibling's child\n"
                elif self.inspect_rabbit.is_uncle_aunt(self.the_rabbit):
                    if self.inspect_rabbit.genderalign in ['doe', 'trans doe']:
                        col2 += "related: aunt"
                    elif self.inspect_rabbit.genderalign in ['buck', 'trans buck']:
                        col2 += "related: uncle"
                    else:
                        col2 += "related: parent's sibling"
                elif self.inspect_rabbit.is_grandparent(self.the_rabbit):
                    col2 += "related: grandparent"
                elif self.the_rabbit.is_grandparent(self.inspect_rabbit):
                    col2 += "related: grandchild"
                elif self.inspect_rabbit.is_parent(self.the_rabbit):
                    col2 += "related: parent"
                elif self.the_rabbit.is_parent(self.inspect_rabbit):
                    col2 += "related: child"
                elif self.inspect_rabbit.is_sibling(self.the_rabbit) or self.the_rabbit.is_sibling(self.inspect_rabbit):
                    if self.inspect_rabbit.is_littermate(self.the_rabbit) or self.the_rabbit.is_littermate(self.inspect_rabbit):
                        col2 += "related: sibling (littermate)"
                    else:
                        col2 += "related: sibling"
                elif not game.warren.warren_settings["first cousin mates"] and self.inspect_rabbit.is_cousin(self.the_rabbit):
                    col2 += "related: cousin"

            self.inspect_rabbit_elements["col2"] = pygame_gui.elements.UITextBox(col2,
                                                                              scale(pygame.Rect((300, 650), (180, 180))),
                                                                              object_id="#text_box_22_horizleft_spacing_95",
                                                                              manager=MANAGER)

            if self.inspect_rabbit.dead:
                self.view_profile_button.enable()
                self.switch_focus_button.disable()
                self.log_icon.enable()
            else:
                self.view_profile_button.enable()
                self.switch_focus_button.enable()
                self.log_icon.enable()
        else:
            self.view_profile_button.disable()
            self.switch_focus_button.disable()
            self.log_icon.disable()

    def apply_rabbit_filter(self, search_text=""):
        # Filter for dead or empty rabbits
        self.filtered_rabbits = self.all_relations.copy()
        if not game.warren.warren_settings["show dead relation"]:
            self.filtered_rabbits = list(
                filter(lambda rel: not rel.rabbit_to.dead, self.filtered_rabbits))

        if not game.warren.warren_settings["show empty relation"]:
            self.filtered_rabbits = list(
                filter(
                    lambda rel: (rel.romantic_love + rel.platonic_like + rel.
                                 dislike + rel.admiration + rel.comfortable +
                                 rel.jealousy + rel.trust) > 0, self.filtered_rabbits))

        # Filter for search
        search_rabbits = []
        if search_text.strip() != "":
            for rabbit in self.filtered_rabbits:
                if search_text.lower() in str(rabbit.rabbit_to.name).lower():
                    search_rabbits.append(rabbit)
            self.filtered_rabbits = search_rabbits

    def update_rabbit_page(self):
        for ele in self.relation_list_elements:
            self.relation_list_elements[ele].kill()
        self.relation_list_elements = {}

        for ele in self.sprite_buttons:
            self.sprite_buttons[ele].kill()
        self.sprite_buttons = {}

        all_pages = self.chunks(self.filtered_rabbits, 8)

        if self.current_page > len(all_pages):
            self.current_page = len(all_pages)

        if self.current_page == 0:
            self.current_page = 1

        if all_pages:
            display_rel = all_pages[self.current_page - 1]
        else:
            display_rel = []

        pos_x = 580
        pos_y = 300
        i = 0
        for rel in display_rel:
            self.generate_relation_block((pos_x, pos_y), rel, i)

            i += 1
            pos_x += 244
            if pos_x > 1400:
                pos_y += 484
                pos_x = 580

        self.page_number.set_text(f"{self.current_page} / {len(all_pages)}")

        # Enable and disable page buttons.
        if len(all_pages) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(all_pages):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(all_pages) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()

    def generate_relation_block(self, pos, the_relationship, i):
        # Generates a relation_block starting at postion, from the relationship object "the_relation"
        # "position" should refer to the top left corner of the *main* relation box, not including the name.
        pos_x = pos[0]
        pos_y = pos[1]

        self.sprite_buttons["image" + str(i)] = UISpriteButton(scale(pygame.Rect((pos_x + 44, pos_y), (100, 100))),
                                                               the_relationship.rabbit_to.sprite,
                                                               rabbit_object=the_relationship.rabbit_to)

        # CHECK NAME LENGTH - SHORTEN IF NECESSARY
        name = str(the_relationship.rabbit_to.name)  # get name
        short_name = shorten_text_to_fit(name, 210, 26)
        self.relation_list_elements["name" + str(i)] = pygame_gui.elements.UITextBox(short_name,
                                                                                     scale(pygame.Rect(
                                                                                         (pos_x - 10, pos_y - 50),
                                                                                         (220, 60))),
                                                                                     object_id="#text_box_26_horizcenter")

        # Gender alignment
        if the_relationship.rabbit_to.genderalign == 'doe':
            gender_icon = image_cache.load_image("resources/images/doe_big.png").convert_alpha()
        elif the_relationship.rabbit_to.genderalign == 'buck':
            gender_icon = image_cache.load_image("resources/images/buck_big.png").convert_alpha()
        elif the_relationship.rabbit_to.genderalign == 'trans doe':
            gender_icon = image_cache.load_image("resources/images/transfem_big.png").convert_alpha()
        elif the_relationship.rabbit_to.genderalign == 'trans buck':
            gender_icon = image_cache.load_image("resources/images/transmasc_big.png").convert_alpha()
        else:
            # Everyone else gets the nonbinary icon
            gender_icon = image_cache.load_image("resources/images/nonbi_big.png").convert_alpha()

        self.relation_list_elements["gender" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((pos_x + 160,
                                                                                                        pos_y + 10),
                                                                                                       (36, 36))),
                                                                                     pygame.transform.scale(gender_icon,
                                                                                                            (36, 36)))

        related = False
        # MATE
        if len(self.the_rabbit.mate) > 0 and the_relationship.rabbit_to.ID in self.the_rabbit.mate:

            self.relation_list_elements['mate_icon' + str(i)] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((pos_x + 10, pos_y + 10),
                                  (22, 20))),
                image_cache.load_image(
                    "resources/images/heart_big.png").convert_alpha())
        else:
            # FAMILY DOT
            # Only show family dot on cousins if first cousin mates are disabled.
            if game.warren.warren_settings['first cousin mates']:
                check_cousins = False
            else:
                check_cousins = the_relationship.rabbit_to.is_cousin(self.the_rabbit)

            if the_relationship.rabbit_to.is_uncle_aunt(self.the_rabbit) or self.the_rabbit.is_uncle_aunt(
                    the_relationship.rabbit_to) \
                    or the_relationship.rabbit_to.is_grandparent(self.the_rabbit) or \
                    self.the_rabbit.is_grandparent(the_relationship.rabbit_to) or \
                    the_relationship.rabbit_to.is_parent(self.the_rabbit) or \
                    self.the_rabbit.is_parent(the_relationship.rabbit_to) or \
                    the_relationship.rabbit_to.is_sibling(self.the_rabbit) or check_cousins:
                related = True
                self.relation_list_elements['relation_icon' + str(i)] = pygame_gui.elements.UIImage(
                    scale(pygame.Rect((pos_x + 10,
                                       pos_y + 10),
                                      (18, 18))),
                    image_cache.load_image(
                        "resources/images/dot_big.png").convert_alpha())

        # ------------------------------------------------------------------------------------------------------------ #
        # RELATION BARS

        barbar = 44
        bar_count = 0

        # ROMANTIC LOVE
        # CHECK AGE DIFFERENCE
        same_age = the_relationship.rabbit_to.age == self.the_rabbit.age
        adult_ages = ['young adult', 'adult', 'senior adult', 'senior']
        both_adult = the_relationship.rabbit_to.age in adult_ages and self.the_rabbit.age in adult_ages
        check_age = both_adult or same_age

        # If they are not both adults, or the same age, OR they are related, don't display any romantic affection,
        # even if they somehow have some. They should not be able to get any, but it never hurts to check.
        if not check_age or related:
            display_romantic = 0
            # Print, just for bug checking. Again, they should not be able to get love towards their relative.
            if the_relationship.romantic_love and related:
                print(
                    f"WARNING: {self.the_rabbit.name} has {the_relationship.romantic_love} romantic love towards their relative, {the_relationship.rabbit_to.name}")
        else:
            display_romantic = the_relationship.romantic_love

        if display_romantic > 49:
            text = "romantic love:"
        else:
            text = "romantic like:"

        self.relation_list_elements[f'romantic_text{i}'] = pygame_gui.elements.UITextBox(text,
                                                                                         scale(pygame.Rect(
                                                                                             (pos_x + 6, pos_y + 87 + (
                                                                                                     barbar * bar_count)),
                                                                                             (170, 60))),
                                                                                         object_id="#text_box_22_horizleft")
        self.relation_list_elements[f'romantic_bar{i}'] = UIRelationStatusBar(scale(pygame.Rect((pos_x + 6,
                                                                                                 pos_y + 130 + (
                                                                                                         barbar * bar_count)),
                                                                                                (188, 20))),
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
        self.relation_list_elements[f'plantonic_text{i}'] = pygame_gui.elements.UITextBox(text,
                                                                                          scale(pygame.Rect((pos_x + 6,
                                                                                                             pos_y + 87 + (
                                                                                                                     barbar * bar_count)),
                                                                                                            (160, 60))),
                                                                                          object_id="#text_box_22_horizleft")
        self.relation_list_elements[f'platonic_bar{i}'] = UIRelationStatusBar(scale(pygame.Rect((pos_x + 6,
                                                                                                 pos_y + 130 + (
                                                                                                         barbar * bar_count)),
                                                                                                (188, 20))),
                                                                              the_relationship.platonic_like,
                                                                              positive_trait=True,
                                                                              dark_mode=game.settings['dark mode'])

        bar_count += 1

        # DISLIKE
        if the_relationship.dislike > 49:
            text = "hate:"
        else:
            text = "dislike:"
        self.relation_list_elements[f'dislike_text{i}'] = pygame_gui.elements.UITextBox(text,
                                                                                        scale(pygame.Rect((pos_x + 6,
                                                                                                           pos_y + 87 + (
                                                                                                                   barbar * bar_count)),
                                                                                                          (160, 60))),
                                                                                        object_id="#text_box_22_horizleft")
        self.relation_list_elements[f'dislike_bar{i}'] = UIRelationStatusBar(scale(pygame.Rect((pos_x + 6,
                                                                                                pos_y + 130 + (
                                                                                                        barbar * bar_count)),
                                                                                               (188, 20))),
                                                                             the_relationship.dislike,
                                                                             positive_trait=False,
                                                                             dark_mode=game.settings['dark mode'])

        bar_count += 1

        # ADMIRE
        if the_relationship.admiration > 49:
            text = "admiration:"
        else:
            text = "respect:"
        self.relation_list_elements[f'admiration_text{i}'] = pygame_gui.elements.UITextBox(text,
                                                                                           scale(pygame.Rect((pos_x + 6,
                                                                                                              pos_y + 87 + (
                                                                                                                      barbar * bar_count)),
                                                                                                             (
                                                                                                                 160,
                                                                                                                 60))),
                                                                                           object_id="#text_box_22_horizleft")
        self.relation_list_elements[f'admiration_bar{i}'] = UIRelationStatusBar(scale(pygame.Rect((pos_x + 6,
                                                                                                   pos_y + 130 + (
                                                                                                           barbar * bar_count)),
                                                                                                  (188, 20))),
                                                                                the_relationship.admiration,
                                                                                positive_trait=True,
                                                                                dark_mode=game.settings['dark mode'])

        bar_count += 1

        # COMFORTABLE
        if the_relationship.comfortable > 49:
            text = "security:"
        else:
            text = "comfort:"
        self.relation_list_elements[f'comfortable_text{i}'] = pygame_gui.elements.UITextBox(text,
                                                                                            scale(
                                                                                                pygame.Rect((pos_x + 6,
                                                                                                             pos_y + 87 + (
                                                                                                                     barbar * bar_count)),
                                                                                                            (160, 60))),
                                                                                            object_id="#text_box_22_horizleft")
        self.relation_list_elements[f'comfortable_bar{i}'] = UIRelationStatusBar(scale(pygame.Rect((pos_x + 6,
                                                                                                    pos_y + 130 + (
                                                                                                            barbar * bar_count)),
                                                                                                   (188, 20))),
                                                                                 the_relationship.comfortable,
                                                                                 positive_trait=True,
                                                                                 dark_mode=game.settings['dark mode'])

        bar_count += 1

        # JEALOUS
        if the_relationship.jealousy > 49:
            text = "resentment:"
        else:
            text = "jealousy:"
        self.relation_list_elements[f'jealous_text{i}'] = pygame_gui.elements.UITextBox(text,
                                                                                        scale(pygame.Rect((pos_x + 6,
                                                                                                           pos_y + 87 + (
                                                                                                                   barbar * bar_count)),
                                                                                                          (160, 60))),
                                                                                        object_id="#text_box_22_horizleft")
        self.relation_list_elements[f'jealous_bar{i}'] = UIRelationStatusBar(scale(pygame.Rect((pos_x + 6,
                                                                                                pos_y + 130 + (
                                                                                                        barbar * bar_count)),
                                                                                               (188, 20))),
                                                                             the_relationship.jealousy,
                                                                             positive_trait=False,
                                                                             dark_mode=game.settings['dark mode'])

        bar_count += 1

        # TRUST
        if the_relationship.trust > 49:
            text = "reliance:"
        else:
            text = "trust:"
        self.relation_list_elements[f'trust_text{i}'] = pygame_gui.elements.UITextBox(text,
                                                                                      scale(pygame.Rect((pos_x + 6,
                                                                                                         pos_y + 87 + (
                                                                                                                 barbar * bar_count)),
                                                                                                        (160, 60))),
                                                                                      object_id="#text_box_22_horizleft")
        self.relation_list_elements[f'trust_bar{i}'] = UIRelationStatusBar(scale(pygame.Rect((pos_x + 6,
                                                                                              pos_y + 130 + (
                                                                                                      barbar * bar_count)),
                                                                                             (188, 20))),
                                                                           the_relationship.trust,
                                                                           positive_trait=True,
                                                                           dark_mode=game.settings['dark mode'])

    def on_use(self):

        # LOAD UI IMAGES
        screen.blit(RelationshipScreen.search_bar, (1070 / 1600 * screen_x, 180 / 1400 * screen_y))
        screen.blit(RelationshipScreen.details_frame, (50 / 1600 * screen_x, 260 / 1400 * screen_y))
        screen.blit(RelationshipScreen.toggle_frame, (90 / 1600 * screen_x, 958 / 1400 * screen_y))
        screen.blit(RelationshipScreen.list_frame, (546 / 1600 * screen_x, 244 / 1400 * screen_y))

        # Only update the postions if the search text changes
        if self.search_bar.get_text() != self.previous_search_text:
            self.apply_rabbit_filter(self.search_bar.get_text())
            self.update_rabbit_page()
        self.previous_search_text = self.search_bar.get_text()

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]

