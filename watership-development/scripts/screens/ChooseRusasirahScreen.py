import pygame.transform
import pygame_gui.elements

from .Screens import Screens

from scripts.utility import get_text_box_theme, scale
from scripts.rabbit.rabbits import Rabbit
from scripts.game_structure import image_cache
from scripts.game_structure.image_button import UIImageButton, UISpriteButton
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER


class ChooseRusasirahScreen(Screens):
    selected_rusasirah = None
    current_page = 1
    list_frame = pygame.transform.scale(image_cache.load_image("resources/images/choosing_frame.png").convert_alpha(),
                                        (1300 / 1600 * screen_x, 452 / 1400 * screen_y))
    rusasi_details = {}
    selected_details = {}
    rabbit_list_buttons = {}

    def __init__(self, name=None):
        super().__init__(name)
        self.list_page = None
        self.next_rabbit = None
        self.previous_rabbit = None
        self.next_page_button = None
        self.previous_page_button = None
        self.current_rusasirah_warning = None
        self.no_rusasirah_warning = None
        self.confirm_rusasirah = None
        self.remove_rusasirah = None
        self.back_button = None
        self.next_rabbit_button = None
        self.previous_rabbit_button = None
        self.rusasirah_icon = None
        self.app_frame = None
        self.rusasirah_frame = None
        self.current_rusasirah_text = None
        self.info = None
        self.heading = None
        self.rusasirah = None
        self.the_rabbit = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.rabbit_list_buttons.values():
                self.selected_rusasirah = event.ui_element.return_rabbit_object()
                self.update_selected_rabbit()
                self.update_buttons()
            elif event.ui_element == self.confirm_rusasirah:
                self.change_rusasirah(self.selected_rusasirah)
                self.update_buttons()
                self.update_selected_rabbit()
            elif event.ui_element == self.remove_rusasirah:
                self.change_rusasirah(self.selected_rusasirah)
                self.update_buttons()
                self.update_selected_rabbit()
            elif event.ui_element == self.back_button:
                self.change_screen('profile screen')
            elif event.ui_element == self.next_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.next_rabbit), Rabbit):
                    game.switches['rabbit'] = self.next_rabbit
                    self.update_rusasi()
                    self.update_rabbit_list()
                    self.update_selected_rabbit()
                    self.update_buttons()
                else:
                    print("invalid next rabbit", self.next_rabbit)
            elif event.ui_element == self.previous_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.previous_rabbit), Rabbit):
                    game.switches['rabbit'] = self.previous_rabbit
                    self.update_rusasi()
                    self.update_rabbit_list()
                    self.update_selected_rabbit()
                    self.update_buttons()
                else:
                    print("invalid previous rabbit", self.previous_rabbit)
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                self.update_rabbit_list()
            elif event.ui_element == self.previous_page_button:
                self.current_page -= 1
                self.update_rabbit_list()

    def screen_switches(self):
        self.the_rabbit = Rabbit.all_rabbits[game.switches['rabbit']]
        self.rusasirah = Rabbit.fetch_rabbit(self.the_rabbit.rusasirah)

        self.heading = pygame_gui.elements.UITextBox("Choose a new rusasirah for " + str(self.the_rabbit.name),
                                                     scale(pygame.Rect((300, 50), (1000, 80))),
                                                     object_id=get_text_box_theme("#text_box_34_horizcenter"),
                                                     manager=MANAGER)
        self.info = pygame_gui.elements.UITextBox("If an rusasi is 6 months old and their rusasirah is changed, they "
                                                  "will not be listed as a former rusasi on their old rusasirah's "
                                                  "profile. Rusasis without a rusasirah will have one automatically "
                                                  "assigned next month. An rusasi's rusasirah can have an influence on "
                                                  "their trait and skill later in life.\nChoose your rusasirah wisely",
                                                  scale(pygame.Rect((360, 105), (880, 185))),
                                                  object_id=get_text_box_theme("#text_box_22_horizcenter_spacing_95"),
                                                  manager=MANAGER)
        if self.rusasirah is not None:
            self.current_rusasirah_text = pygame_gui.elements.UITextBox(f"{self.the_rabbit.name}'s current rusasirah is "
                                                                     f"{self.rusasirah.name}",
                                                                     scale(pygame.Rect((460, 260), (680, 60))),
                                                                     object_id=get_text_box_theme(
                                                                         "#text_box_22_horizcenter")
                                                                     , manager=MANAGER)
        else:
            self.current_rusasirah_text = pygame_gui.elements.UITextBox(f"{self.the_rabbit.name} does not have a rusasirah",
                                                                     scale(pygame.Rect((460, 260), (680, 60))),
                                                                     object_id=get_text_box_theme(
                                                                         "#text_box_22_horizcenter")
                                                                     , manager=MANAGER)

        # Layout Images:
        self.rusasirah_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((80, 226), (562, 394))),
                                                        pygame.transform.scale(
                                                            image_cache.load_image(
                                                                "resources/images/choosing_rabbit1_frame_ment.png").convert_alpha(),
                                                            (562, 394)), manager=MANAGER)
        self.app_frame = pygame_gui.elements.UIImage(scale(pygame.Rect((960, 226), (562, 394))),
                                                     pygame.transform.scale(
                                                         image_cache.load_image(
                                                             "resources/images/choosing_rabbit2_frame_ment.png").convert_alpha(),
                                                         (562, 394)), manager=MANAGER)

        self.rusasirah_icon = pygame_gui.elements.UIImage(scale(pygame.Rect((630, 320), (343, 228))),
                                                       pygame.transform.scale(
                                                           image_cache.load_image(
                                                               "resources/images/rusasirah.png").convert_alpha(),
                                                           (343, 228)), manager=MANAGER)

        self.previous_rabbit_button = UIImageButton(scale(pygame.Rect((50, 50), (306, 60))), "",
                                                 object_id="#previous_rabbit_button")
        self.next_rabbit_button = UIImageButton(scale(pygame.Rect((1244, 50), (306, 60))), "",
                                             object_id="#next_rabbit_button")
        self.back_button = UIImageButton(scale(pygame.Rect((50, 1290), (210, 60))), "", object_id="#back_button")
        self.confirm_rusasirah = UIImageButton(scale(pygame.Rect((652, 620), (296, 60))), "",
                                            object_id="#confirm_rusasirah_button")
        self.remove_rusasirah = UIImageButton(scale(pygame.Rect((652, 620), (296, 60))), "",
                                            object_id="#remove_rusasirah_button")
        self.current_rusasirah_warning = pygame_gui.elements.UITextBox(
            "Current rusasirah selected",
            scale(pygame.Rect((600, 670), (400, 60))),
            object_id=get_text_box_theme("#text_box_22_horizcenter_red"),
            manager=MANAGER)
        self.no_rusasirah_warning = pygame_gui.elements.UITextBox("<font color=#FF0000>No rusasirah selected</font>"
                                                                    , scale(pygame.Rect((600, 670), (400, 60))),
                                                                    object_id=get_text_box_theme(
                                                                        "#text_box_22_horizcenter"),
                                                                    manager=MANAGER)
        self.previous_page_button = UIImageButton(scale(pygame.Rect((630, 1160), (68, 68))), "",
                                                  object_id="#relation_list_previous", manager=MANAGER)
        self.next_page_button = UIImageButton(scale(pygame.Rect((902, 1160), (68, 68))), "",
                                              object_id="#relation_list_next", manager=MANAGER)

        self.update_rusasi()  # Draws the current rusasi
        self.update_selected_rabbit()  # Updates the image and details of selected rabbit
        self.update_rabbit_list()
        self.update_buttons()

    def exit_screen(self):
        for ele in self.rabbit_list_buttons:
            self.rabbit_list_buttons[ele].kill()
        self.rabbit_list_buttons = {}

        for ele in self.rusasi_details:
            self.rusasi_details[ele].kill()
        self.rusasi_details = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        self.heading.kill()
        del self.heading
        self.info.kill()
        del self.info
        self.current_rusasirah_text.kill()
        del self.current_rusasirah_text
        self.rusasirah_frame.kill()
        del self.rusasirah_frame
        self.rusasirah_icon.kill()
        del self.rusasirah_icon
        self.previous_rabbit_button.kill()
        del self.previous_rabbit_button
        self.next_rabbit_button.kill()
        del self.next_rabbit_button
        self.back_button.kill()
        del self.back_button
        self.confirm_rusasirah.kill()
        del self.confirm_rusasirah
        self.remove_rusasirah.kill()
        del self.remove_rusasirah
        self.current_rusasirah_warning.kill()
        del self.current_rusasirah_warning
        self.no_rusasirah_warning.kill()
        del self.no_rusasirah_warning
        self.previous_page_button.kill()
        del self.previous_page_button
        self.next_page_button.kill()
        del self.next_page_button
        self.app_frame.kill()
        del self.app_frame

    def update_rusasi(self):
        """ Updates the rusasi focused on. """
        for ele in self.rusasi_details:
            self.rusasi_details[ele].kill()
        self.rusasi_details = {}

        self.the_rabbit = Rabbit.all_rabbits[game.switches['rabbit']]
        self.current_page = 1
        self.selected_rusasirah = Rabbit.fetch_rabbit(self.the_rabbit.rusasirah)
        self.rusasirah = Rabbit.fetch_rabbit(self.the_rabbit.rusasirah)

        self.heading.set_text(f"Choose a new rusasirah for {self.the_rabbit.name}")
        if self.the_rabbit.rusasirah:
            self.current_rusasirah_text.set_text(
                f"{self.the_rabbit.name}'s current rusasirah is {self.rusasirah.name}")
        else:
            self.current_rusasirah_text.set_text(
                f"{self.the_rabbit.name} does not have a rusasirah")
        self.rusasi_details["rusasi_image"] = pygame_gui.elements.UIImage(
            scale(pygame.Rect((1200, 300), (300, 300))),
            pygame.transform.scale(
                self.the_rabbit.sprite,
                (300, 300)),
            manager=MANAGER)

        info = self.the_rabbit.status + "\n" + self.the_rabbit.genderalign + \
               "\n" + self.the_rabbit.personality.trait + "\n" + self.the_rabbit.skills.skill_string(short=True)
        self.rusasi_details["rusasi_info"] = pygame_gui.elements.UITextBox(
            info,
            scale(pygame.Rect((980, 325), (210, 250))),
            object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
            manager=MANAGER)

        name = str(self.the_rabbit.name)  # get name
        if 11 <= len(name):  # check name length
            short_name = str(name)[0:9]
            name = short_name + '...'
        self.rusasi_details["rusasi_name"] = pygame_gui.elements.ui_label.UILabel(
            scale(pygame.Rect((1240, 230), (220, 60))),
            name,
            object_id="#text_box_34_horizcenter", manager=MANAGER)

        self.find_next_previous_rabbits()  # Determine where the next and previous rabbit buttons lead

        if self.next_rabbit == 0:
            self.next_rabbit_button.disable()
        else:
            self.next_rabbit_button.enable()

        if self.previous_rabbit == 0:
            self.previous_rabbit_button.disable()
        else:
            self.previous_rabbit_button.enable()

    def find_next_previous_rabbits(self):
        """Determines where the previous and next buttons lead"""
        is_instructor = False
        if self.the_rabbit.dead and game.warren.instructor.ID == self.the_rabbit.ID:
            is_instructor = True

        self.previous_rabbit = 0
        self.next_rabbit = 0
        if self.the_rabbit.dead and not is_instructor and not self.the_rabbit.df:
            self.previous_rabbit = game.warren.instructor.ID

        if is_instructor:
            self.next_rabbit = 1

        for check_rabbit in Rabbit.all_rabbits_list:
            if check_rabbit.ID == self.the_rabbit.ID:
                self.next_rabbit = 1

            if self.next_rabbit == 0 and check_rabbit.ID != self.the_rabbit.ID and check_rabbit.dead == self.the_rabbit.dead and \
                    check_rabbit.ID != game.warren.instructor.ID and not check_rabbit.exiled and check_rabbit.status in \
                    ["rusasi", "healer rusasi", "owsla rusasi"] \
                    and check_rabbit.df == self.the_rabbit.df:
                self.previous_rabbit = check_rabbit.ID

            elif self.next_rabbit == 1 and check_rabbit.ID != self.the_rabbit.ID and check_rabbit.dead == self.the_rabbit.dead and \
                    check_rabbit.ID != game.warren.instructor.ID and not check_rabbit.exiled and check_rabbit.status in \
                    ["rusasi", "healer rusasi", "owsla rusasi"] \
                    and check_rabbit.df == self.the_rabbit.df:
                self.next_rabbit = check_rabbit.ID

            elif int(self.next_rabbit) > 1:
                break

        if self.next_rabbit == 1:
            self.next_rabbit = 0

    def change_rusasirah(self, new_rusasirah=None):
        old_rusasirah = Rabbit.fetch_rabbit(self.the_rabbit.rusasirah)
        if new_rusasirah == old_rusasirah:
        #if "changing rusasirah" to the same rabbit, remove them as rusasirah instead
            if self.the_rabbit.months > 6 and self.the_rabbit.ID not in old_rusasirah.former_rusasi:
                old_rusasirah.former_rusasis.append(self.the_rabbit.ID)
            self.the_rabbit.rusasirah = None
            old_rusasirah.rusasi.remove(self.the_rabbit.ID)
            self.rusasirah = None
        elif new_rusasirah and old_rusasirah is not None:
            old_rusasirah.rusasi.remove(self.the_rabbit.ID)
            if self.the_rabbit.months > 6 and self.the_rabbit.ID not in old_rusasirah.former_rusasi:
                old_rusasirah.former_rusasis.append(self.the_rabbit.ID)

            self.the_rabbit.patrol_with_rusasirah = 0
            self.the_rabbit.rusasirah = new_rusasirah.ID
            new_rusasirah.rusasi.append(self.the_rabbit.ID)
            self.rusasirah = new_rusasirah

            # They are a current rusasi, not a former one now!
            if self.the_rabbit.ID in new_rusasirah.former_rusasi:
                new_rusasirah.former_rusasis.remove(self.the_rabbit.ID)

        elif new_rusasirah:
            self.the_rabbit.rusasirah = new_rusasirah.ID
            new_rusasirah.rusasi.append(self.the_rabbit.ID)
            self.rusasirah = new_rusasirah
            if self.the_rabbit.ID not in new_rusasirah.former_rusasi:
                self.the_rabbit.patrol_with_rusasirah = 0

            # They are a current rusasi, not a former one now!
            if self.the_rabbit.ID in new_rusasirah.former_rusasis:
                new_rusasirah.former_rusasis.remove(self.the_rabbit.ID)

        if self.rusasirah is not None:
            self.current_rusasirah_text.set_text(
                f"{self.the_rabbit.name}'s current rusasirah is {self.rusasirah.name}")
        else:
            self.current_rusasirah_text.set_text(f"{self.the_rabbit.name} does not have a rusasirah")

    def update_selected_rabbit(self):
        """Updates the image and information on the currently selected rusasirah"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_rusasirah:

            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((100, 300), (300, 300))),
                pygame.transform.scale(
                    self.selected_rusasirah.sprite,
                    (300, 300)), manager=MANAGER)

            info = self.selected_rusasirah.status + "\n" + \
                   self.selected_rusasirah.genderalign + "\n" + self.selected_rusasirah.personality.trait + "\n" + \
                   self.selected_rusasirah.skills.skill_string(short=True)
            if len(self.selected_rusasirah.former_rusasis) >= 1:
                info += f"\n{len(self.selected_rusasirah.former_rusasis)} former rusasi(s)"
            if len(self.selected_rusasirah.rusasi) >= 1:
                info += f"\n{len(self.selected_rusasirah.rusasi)} current rusasi(s)"
            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(info,
                                                                                   scale(pygame.Rect((420, 325),
                                                                                                     (210, 250))),
                                                                                   object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                                                                                   manager=MANAGER)

            name = str(self.selected_rusasirah.name)  # get name
            if 11 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + '...'
            self.selected_details["rusasirah_name"] = pygame_gui.elements.ui_label.UILabel(
                scale(pygame.Rect((130, 230), (220, 60))),
                name,
                object_id="#text_box_34_horizcenter", manager=MANAGER)

    def update_rabbit_list(self):
        """Updates the rabbit sprite buttons. """
        valid_rusasirah = self.chunks(self.get_valid_rusasirah(), 30)

        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.current_page > len(valid_rusasirah):
            self.list_page = len(valid_rusasirah)

        # Handle which next buttons are clickable.
        if len(valid_rusasirah) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(valid_rusasirah):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(valid_rusasirah) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()
        display_rabbits = []
        if valid_rusasirah:
            display_rabbits = valid_rusasirah[self.current_page - 1]

        # Kill all the currently displayed rabbits.
        for ele in self.rabbit_list_buttons:
            self.rabbit_list_buttons[ele].kill()
        self.rabbit_list_buttons = {}

        pos_x = 0
        pos_y = 40
        i = 0
        for rabbit in display_rabbits:
            self.rabbit_list_buttons["rabbit" + str(i)] = UISpriteButton(
                scale(pygame.Rect((200 + pos_x, 730 + pos_y), (100, 100))),
                rabbit.sprite, rabbit_object=rabbit, manager=MANAGER)
            pos_x += 120
            if pos_x >= 1100:
                pos_x = 0
                pos_y += 120
            i += 1

    def update_buttons(self):
        """Updates the status of buttons. """
        # Disable to enable the choose rusasirah button
        if not self.selected_rusasirah:
            self.remove_rusasirah.hide()
            self.remove_rusasirah.disable()
            self.confirm_rusasirah.show()
            self.confirm_rusasirah.disable()
            self.current_rusasirah_warning.hide()
            self.no_rusasirah_warning.show()
        elif self.selected_rusasirah.ID == self.the_rabbit.rusasirah:
            self.confirm_rusasirah.hide()
            self.remove_rusasirah.show()
            self.remove_rusasirah.enable()
            self.current_rusasirah_warning.show()
            self.no_rusasirah_warning.hide()
        else:
            self.remove_rusasirah.hide()
            self.remove_rusasirah.disable()
            self.confirm_rusasirah.show()
            self.confirm_rusasirah.enable()
            self.current_rusasirah_warning.hide()
            self.no_rusasirah_warning.hide()

    def get_valid_rusasirah(self):
        valid_rusasirah = []

        if self.the_rabbit.status == "rusasi":
            for rabbit in Rabbit.all_rabbits_list:
                if not rabbit.dead and not rabbit.outside and rabbit.status in [
                    'rabbit', 'captain'
                ]:
                    valid_rusasirah.append(rabbit)
        elif self.the_rabbit.status == "healer rusasi":
            for rabbit in Rabbit.all_rabbits_list:
                if not rabbit.dead and not rabbit.outside and rabbit.status == 'healer':
                    valid_rusasirah.append(rabbit)
        elif self.the_rabbit.status == 'owsla rusasi':
            for rabbit in Rabbit.all_rabbits_list:
                if not rabbit.dead and not rabbit.outside and rabbit.status == 'owsla':
                    valid_rusasirah.append(rabbit)

        return valid_rusasirah

    def on_use(self):
        # Due to a bug in pygame, any image with buttons over it must be blited
        screen.blit(self.list_frame, (150 / 1600 * screen_x, 720 / 1400 * screen_y))

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]
