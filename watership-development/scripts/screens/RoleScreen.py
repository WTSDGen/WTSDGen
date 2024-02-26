#!/usr/bin/env python3
import os
import pygame

from scripts.utility import scale

from .Screens import Screens

from scripts.utility import get_text_box_theme, shorten_text_to_fit
from scripts.rabbit.rabbits import Rabbit
from scripts.game_structure import image_cache
import pygame_gui
from scripts.game_structure.image_button import UIImageButton, UITextBoxTweaked
from scripts.game_structure.game_essentials import game, screen_x, screen_y, MANAGER


class RoleScreen(Screens):
    the_rabbit = None
    selected_rabbit_elements = {}
    buttons = {}
    next_rabbit = None
    previous_rabbit = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.change_screen("profile screen")
            elif event.ui_element == self.next_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.next_rabbit), Rabbit):
                    game.switches["rabbit"] = self.next_rabbit
                    self.update_selected_rabbit()
                else:
                    print("invalid next rabbit", self.next_rabbit)
            elif event.ui_element == self.previous_rabbit_button:
                if isinstance(Rabbit.fetch_rabbit(self.previous_rabbit), Rabbit):
                    game.switches["rabbit"] = self.previous_rabbit
                    self.update_selected_rabbit()
                else:
                    print("invalid previous rabbit", self.previous_rabbit)
            elif event.ui_element == self.promote_chief_rabbit:
                if self.the_rabbit == game.warren.captain:
                    game.warren.captain = None
                game.warren.new_chief_rabbit(self.the_rabbit)
                if game.sort_type == "rank":
                    Rabbit.sort_rabbits()
                self.update_selected_rabbit()
            elif event.ui_element == self.promote_captain:
                game.warren.captain = self.the_rabbit
                self.the_rabbit.status_change("captain", resort=True)
                self.update_selected_rabbit()
            elif event.ui_element == self.switch_rabbit:
                self.the_rabbit.status_change("rabbit", resort=True)
                self.update_selected_rabbit()
            elif event.ui_element == self.switch_med_rabbit:
                self.the_rabbit.status_change("healer", resort=True)
                self.update_selected_rabbit()
            elif event.ui_element == self.retire:
                self.the_rabbit.status_change("elder", resort=True)
                # Since you can't "unretire" a rabbit, apply the skill and trait change
                # here
                self.update_selected_rabbit()
            elif event.ui_element == self.switch_owsla:
                self.the_rabbit.status_change("owsla", resort=True)
                self.update_selected_rabbit()
            elif event.ui_element == self.switch_rabbit_app:
                self.the_rabbit.status_change("rusasi", resort=True)
                self.update_selected_rabbit()
            elif event.ui_element == self.switch_med_app:
                self.the_rabbit.status_change("healer rusasi", resort=True)
                self.update_selected_rabbit()
            elif event.ui_element == self.switch_owsla_app:
                self.the_rabbit.status_change("owsla rusasi", resort=True)
                self.update_selected_rabbit()
        
        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if event.key == pygame.K_ESCAPE:
                self.change_screen("profile screen")
            elif event.key == pygame.K_RIGHT:
                game.switches["rabbit"] = self.next_rabbit
                self.update_selected_rabbit()
            elif event.key == pygame.K_LEFT:
                game.switches["rabbit"] = self.previous_rabbit
                self.update_selected_rabbit()

    def screen_switches(self):

        self.next_rabbit_button = UIImageButton(scale(pygame.Rect((1244, 50), (306, 60))), "", object_id="#next_rabbit_button"
                                             , manager=MANAGER)
        self.previous_rabbit_button = UIImageButton(scale(pygame.Rect((50, 50), (306, 60))), "",
                                                 object_id="#previous_rabbit_button"
                                                 , manager=MANAGER)
        self.back_button = UIImageButton(scale(pygame.Rect((50, 120), (210, 60))), "", object_id="#back_button"
                                         , manager=MANAGER)

        # Create the buttons
        self.bar = pygame_gui.elements.UIImage(scale(pygame.Rect((96, 700), (1408, 20))),
                                               pygame.transform.scale(
                                                   image_cache.load_image("resources/images/bar.png"),
                                                   (1408 / 1600 * screen_x, 20 / 1400 * screen_y)
                                               ), manager=MANAGER)

        self.blurb_background = pygame_gui.elements.UIImage(scale(pygame.Rect
                                                                  ((100, 390), (1400, 300))),
                                                            pygame.transform.scale(
                                                                pygame.image.load(
                                                                    "resources/images/mediation_selection_bg.png").convert_alpha(),
                                                                (1400, 300))
                                                            )

        # LEADERSHIP
        self.promote_chief_rabbit = UIImageButton(scale(pygame.Rect((96, 720), (344, 72))), "",
                                            object_id="#promote_chief_rabbit_button",
                                            manager=MANAGER)
        self.promote_captain = UIImageButton(scale(pygame.Rect((96, 792), (344, 72))), "",
                                            object_id="#promote_captain_button",
                                            manager=MANAGER)

        # ADULT RABBIT ROLES
        self.switch_rabbit = UIImageButton(scale(pygame.Rect((451, 720), (344, 72))), "",
                                            object_id="#switch_rabbit_button",
                                            manager=MANAGER)
        self.retire = UIImageButton(scale(pygame.Rect((451, 792), (334, 72))), "",
                                    object_id="#retire_button",
                                    manager=MANAGER)
        self.switch_med_rabbit = UIImageButton(scale(pygame.Rect((805, 720), (344, 104))), "",
                                            object_id="#switch_med_rabbit_button",
                                            manager=MANAGER)
        self.switch_owsla = UIImageButton(scale(pygame.Rect((805, 824), (344, 72))), "",
                                             object_id="#switch_owsla_button",
                                             manager=MANAGER)

        # In-TRAINING ROLES:
        self.switch_rabbit_app = UIImageButton(scale(pygame.Rect((1159, 720), (344, 104))), "",
                                                object_id="#switch_rabbit_app_button",
                                                manager=MANAGER)
        self.switch_med_app = UIImageButton(scale(pygame.Rect((1159, 824), (344, 104))), "",
                                            object_id="#switch_med_app_button",
                                            manager=MANAGER)
        self.switch_owsla_app = UIImageButton(scale(pygame.Rect((1159, 928), (344, 104))), "",
                                                 object_id="#switch_owsla_app_button",
                                                 manager=MANAGER)

        self.update_selected_rabbit()

    def update_selected_rabbit(self):
        for ele in self.selected_rabbit_elements:
            self.selected_rabbit_elements[ele].kill()
        self.selected_rabbit_elements = {}

        self.the_rabbit = Rabbit.fetch_rabbit(game.switches['rabbit'])
        if not self.the_rabbit:
            return

        self.selected_rabbit_elements["rabbit_image"] = pygame_gui.elements.UIImage(
            scale(pygame.Rect((490, 80), (300, 300))),
            pygame.transform.scale(
                self.the_rabbit.sprite, (300, 300)),
            manager=MANAGER
        )

        name = str(self.the_rabbit.name)
        short_name = shorten_text_to_fit(name, 300, 26)
        self.selected_rabbit_elements["rabbit_name"] = pygame_gui.elements.UILabel(scale(pygame.Rect((775, 140), (350, -1))),
                                                                             short_name,
                                                                             object_id=get_text_box_theme())
        if self.the_rabbit.status == "healer rusasi":
            text = f"<b>healer's rusasi</b>\n{self.the_rabbit.personality.trait}\n"
        elif self.the_rabbit.status == "owsla rusasi":
            text = f"<b>owsla trainee</b>\n{self.the_rabbit.personality.trait}\n"
        else:
            text = f"<b>{self.the_rabbit.status}</b>\n{self.the_rabbit.personality.trait}\n"

        text += f"{self.the_rabbit.months} "

        if self.the_rabbit.months == 1:
            text += "month  |  "
        else:
            text += "months  |  "

        text += self.the_rabbit.genderalign + "\n"

        if self.the_rabbit.rusasirah:
            text += "rusasirah: "
            rusasirah = Rabbit.fetch_rabbit(self.the_rabbit.rusasirah)
            if rusasirah:
                text += str(rusasirah.name)

        if self.the_rabbit.rusasi:
            if len(self.the_rabbit.rusasi) > 1:
                text += "rusasi: "
            else:
                text += "rusasi: "

            text += ", ".join([str(Rabbit.fetch_rabbit(x).name) for x in
                               self.the_rabbit.rusasi if Rabbit.fetch_rabbit(x)])

        self.selected_rabbit_elements["rabbit_details"] = UITextBoxTweaked(text, scale(pygame.Rect((790, 200), (320, 188))),
                                                                     object_id=get_text_box_theme(
                                                                         "#text_box_22_horizcenter"),
                                                                     manager=MANAGER, line_spacing=0.95)

        self.selected_rabbit_elements["role_blurb"] = pygame_gui.elements.UITextBox(self.get_role_blurb(),
                                                                                 scale(pygame.Rect((340, 400),
                                                                                                   (1120, 270))),
                                                                                 object_id="#text_box_26_horizcenter_vertcenter_spacing_95",
                                                                                 manager=MANAGER)

        main_dir = "resources/images/"
        paths = {
            "chief rabbit": "chief_rabbit_icon.png",
            "captain": "captain_icon.png",
            "healer": "medic_icon.png",
            "healer rusasi": "medic_app_icon.png",
            "owsla": "owsla_icon.png",
            "owsla rusasi": "owsla_app_icon.png",
            "rabbit": "rabbit_icon.png",
            "rusasi": "rabbit_app_icon.png",
            "kit": "kit_icon.png",
            "newborn": "kit_icon.png",
            "elder": "elder_icon.png",
        }

        if self.the_rabbit.status in paths:
            icon_path = os.path.join(main_dir, paths[self.the_rabbit.status])
        else:
            icon_path = os.path.join(main_dir, "buttonrank.png")

        self.selected_rabbit_elements["role_icon"] = pygame_gui.elements.UIImage(
            scale(pygame.Rect((165, 462), (156, 156))),
            pygame.transform.scale(
                image_cache.load_image(icon_path),
                (156 / 1600 * screen_x, 156 / 1400 * screen_y)
            ))

        self.determine_previous_and_next_rabbit()
        self.update_disabled_buttons()

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

        if game.warren.chief_rabbit:
            chief_rabbitinvalid = game.warren.chief_rabbit.dead or game.warren.chief_rabbit.outside
        else:
            chief_rabbitinvalid = True

        if game.warren.captain:
            captain_invalid = game.warren.captain.dead or game.warren.captain.outside
        else:
            captain_invalid = True

        if self.the_rabbit.status == "rusasi":
            # LEADERSHIP
            self.promote_chief_rabbit.disable()
            self.promote_captain.disable()

            # ADULT RABBIT ROLES
            self.switch_rabbit.disable()
            self.switch_med_rabbit.disable()
            self.switch_owsla.disable()
            self.retire.disable()

            # In-TRAINING ROLES:
            self.switch_med_app.enable()
            self.switch_rabbit_app.disable()
            self.switch_owsla_app.enable()
        elif self.the_rabbit.status == "rabbit":
            # LEADERSHIP
            if chief_rabbitinvalid:
                self.promote_chief_rabbit.enable()
            else:
                self.promote_chief_rabbit.disable()

            if captain_invalid:
                self.promote_captain.enable()
            else:
                self.promote_captain.disable()

            # ADULT RABBIT ROLES
            self.switch_rabbit.disable()
            self.switch_med_rabbit.enable()
            self.switch_owsla.enable()
            self.retire.enable()

            # In-TRAINING ROLES:
            self.switch_med_app.disable()
            self.switch_rabbit_app.disable()
            self.switch_owsla_app.disable()
        elif self.the_rabbit.status == "captain":
            if chief_rabbitinvalid:
                self.promote_chief_rabbit.enable()
            else:
                self.promote_chief_rabbit.disable()

            self.promote_captain.disable()

            # ADULT RABBIT ROLES
            self.switch_rabbit.enable()
            self.switch_med_rabbit.disable()
            self.switch_owsla.disable()
            self.retire.enable()

            # In-TRAINING ROLES:
            self.switch_med_app.disable()
            self.switch_rabbit_app.disable()
            self.switch_owsla_app.disable()
        elif self.the_rabbit.status == "healer":
            self.promote_chief_rabbit.disable()
            self.promote_captain.disable()

            self.switch_rabbit.enable()
            self.switch_med_rabbit.disable()
            self.switch_owsla.enable()
            self.retire.enable()

            # In-TRAINING ROLES:
            self.switch_med_app.disable()
            self.switch_rabbit_app.disable()
            self.switch_owsla_app.disable()
        elif self.the_rabbit.status == "owsla":
            if chief_rabbitinvalid:
                self.promote_chief_rabbit.enable()
            else:
                self.promote_chief_rabbit.disable()

            if captain_invalid:
                self.promote_captain.enable()
            else:
                self.promote_captain.disable()

            self.switch_rabbit.enable()
            self.switch_med_rabbit.enable()
            self.switch_owsla.disable()
            self.retire.enable()

            # In-TRAINING ROLES:
            self.switch_med_app.disable()
            self.switch_rabbit_app.disable()
            self.switch_owsla_app.disable()
        elif self.the_rabbit.status == "elder":
            if chief_rabbitinvalid:
                self.promote_chief_rabbit.enable()
            else:
                self.promote_chief_rabbit.disable()

            if captain_invalid:
                self.promote_captain.enable()
            else:
                self.promote_captain.disable()

            # ADULT RABBIT ROLES
            self.switch_rabbit.enable()
            self.switch_med_rabbit.enable()
            self.switch_owsla.enable()
            self.retire.disable()

            # In-TRAINING ROLES:
            self.switch_med_app.disable()
            self.switch_rabbit_app.disable()
            self.switch_owsla_app.disable()
        elif self.the_rabbit.status == "healer rusasi":
            self.promote_chief_rabbit.disable()
            self.promote_captain.disable()

            # ADULT RABBIT ROLES
            self.switch_rabbit.disable()
            self.switch_med_rabbit.disable()
            self.switch_owsla.disable()
            self.retire.disable()

            # In-TRAINING ROLES:
            self.switch_med_app.disable()
            self.switch_rabbit_app.enable()
            self.switch_owsla_app.enable()
        elif self.the_rabbit.status == "owsla rusasi":
            self.promote_chief_rabbit.disable()
            self.promote_captain.disable()

            # ADULT RABBIT ROLES
            self.switch_rabbit.disable()
            self.switch_med_rabbit.disable()
            self.switch_owsla.disable()
            self.retire.disable()

            # In-TRAINING ROLES:
            self.switch_med_app.enable()
            self.switch_rabbit_app.enable()
            self.switch_owsla_app.disable()
        elif self.the_rabbit.status == "chief rabbit":
            self.promote_chief_rabbit.disable()
            self.promote_captain.disable()

            # ADULT RABBIT ROLES
            self.switch_rabbit.enable()
            self.switch_med_rabbit.disable()
            self.switch_owsla.disable()
            self.retire.enable()

            # In-TRAINING ROLES:
            self.switch_med_app.disable()
            self.switch_rabbit_app.disable()
            self.switch_owsla_app.disable()
        else:
            self.promote_chief_rabbit.disable()
            self.promote_captain.disable()

            # ADULT RABBIT ROLES
            self.switch_rabbit.disable()
            self.switch_med_rabbit.disable()
            self.switch_owsla.disable()
            self.retire.disable()

            # In-TRAINING ROLES:
            self.switch_med_app.disable()
            self.switch_rabbit_app.disable()
            self.switch_owsla_app.disable()

    def get_role_blurb(self):
        if self.the_rabbit.status == "rabbit":
            output = f"{self.the_rabbit.name} is a <b>rabbit</b>. Warriors are adult rabbits who feed and protect their " \
                     f"warren. They are trained to hunt and fight in addition to the ways of the rabbit code. " \
                     f"Warriors are essential to the survival of a warren, and usually make up the bulk of it's members. "
        elif self.the_rabbit.status == "chief rabbit":
            output = f"{self.the_rabbit.name} is the <b>chief rabbit</b> of {game.warren.name}warren. The guardianship of all " \
                     f"warren rabbits has been entrusted to them with blessings from Frithra. The chief rabbit is the highest " \
                     f"authority in the warren. The chief rabbit holds warren meetings, determines rabbit placement, and " \
                     f"directs the captain and the owsla. To help them protect the warren, " \
                     f"Frithra has given them nine blessings. They typically take the suffix \"ra\"."
        elif self.the_rabbit.status == "captain":
            output = f"{self.the_rabbit.name} is {game.warren.name}warren's <b>captain</b>. " \
                     f"The captain of the owsla is the second in command, " \
                     f"just below the chief_rabbit. They advise the chief rabbit and organize daily patrols, " \
                     f"alongside normal owsla duties. Typically, a captain is personally appointed by the current " \
                     f"chief_rabbit. As dictated by the law, all deputies must train at least one new recruit " \
                     f"before appointment.  " \
                     f"The captain succeeds the chief rabbit if they die or retire. "
        elif self.the_rabbit.status == "healer":
            output = f"{self.the_rabbit.name} is a <b>healer</b>. Healers are, as the name says, the healers of the warren. " \
                     f"They treat " \
                     f"injuries and illnesses with herbal remedies. Unlike the other rabbits, healers are not expected " \
                     f"to forage or fight for the warren. In addition to their healing duties, healers also have " \
                     f"a special connection to Frith. Every half-month, they travel to their warren's holy place " \
                     f"to commune with Frithra. "
        elif self.the_rabbit.status == "owsla":
            output = f"{self.the_rabbit.name} is a <b>owsla</b>. Owsla are a specialized group of rabbits " \
                     f"that usually " \
                     f"surround the chief_rabbit. Their exact purpose varies by warren, but many take a militaristic " \
                     f"role and serve as the warren's protectors and rule enforcers. Many chief rabbits also send the " \
                     f"owsla to steal food from ithé farms."
        elif self.the_rabbit.status == "elder":
            output = f"{self.the_rabbit.name} is an <b>elder</b>. They have spent many months serving their warren, " \
                     f"and have earned " \
                     f"many months of rest. Elders are essential to passing down the oral tradition of the warren. " \
                     f"Sometimes, rabbits may retire due to disability or injury. Whatever the " \
                     f"circumstance of their retirement, elders are held in high esteem in the warren, and always eat " \
                     f"before other rabbits. "
        elif self.the_rabbit.status == "rusasi":
            output = f"{self.the_rabbit.name} is a <b>rusasi</b>, in training to become the best rabbit they can be. " \
                     f"Kits can be made rusasi- meaning, literally, sibling- at six months of age, where they will learn how " \
                     f"to work for their warren. Typically, the training of an rusasi is entrusted " \
                     f"to an single rabbit - their rusasirah. To build character, rusasi are often assigned " \
                     f"the unpleasant and grunt tasks of warren life."
        elif self.the_rabbit.status == "healer rusasi":
            output = f"{self.the_rabbit.name} is a <b>healer's rusasi</b>, training to become a full healer. " \
                     f"Kits can be made healer rusasis at six months of age, where they will learn how to " \
                     f"heal their warrenmates and commune with Frith. healer rusasis are typically chosen " \
                     f"for their interest in healing and/or their connecting to Frith. "
        elif self.the_rabbit.status == "owsla rusasi":
            output = f"{self.the_rabbit.name} is a <b>owsla rusasi</b>, training to become a full owsla. " \
                     f"Their exact purpose varies by warren, but many take a militaristic " \
                     f"role and serve as the warren's protectors and rule enforcers. Many chief rabbits also send the " \
                     f"owsla to steal food from ithé farms. " \
                     f"Owsla trainees are often chosen for their quick thinking and bold personality. " 
        elif self.the_rabbit.status == "kit":
            output = f"{self.the_rabbit.name} is a <b>kit</b>. All rabbits below the age of six months are " \
                     f"considered kits. Kits " \
                     f"are prohibited from leaving burrow in order to protect them from the dangers of the wild. " \
                     f"Although they don't have any official duties in the warren, they are expected to learn the " \
                     f"legends and traditions of their warren. They are protected by every rabbit in the warren and always " \
                     f"eat first."
        elif self.the_rabbit.status == "newborn":
            output = f"{self.the_rabbit.name} is a <b>newborn kit</b>. All rabbits below the age of six months are " \
                     f"considered kits. Kits " \
                     f"are prohibited from leaving burrow in order to protect them from the dangers of the wild. " \
                     f"Although they don't have any official duties in the warren, they are expected to learn the " \
                     f"legends and traditions of their warren. They are protected by every rabbit in the warren and always " \
                     f"eat first."
        else:
            output = f"{self.the_rabbit.name} has an unknown rank. I guess they want to make their own way in life! "

        return output

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

    def exit_screen(self):
        self.back_button.kill()
        del self.back_button
        self.next_rabbit_button.kill()
        del self.next_rabbit_button
        self.previous_rabbit_button.kill()
        del self.previous_rabbit_button
        self.bar.kill()
        del self.bar
        self.promote_chief_rabbit.kill()
        del self.promote_chief_rabbit
        self.promote_captain.kill()
        del self.promote_captain
        self.switch_rabbit.kill()
        del self.switch_rabbit
        self.switch_med_rabbit.kill()
        del self.switch_med_rabbit
        self.switch_owsla.kill()
        del self.switch_owsla
        self.retire.kill()
        del self.retire
        self.switch_med_app.kill()
        del self.switch_med_app
        self.switch_rabbit_app.kill()
        del self.switch_rabbit_app
        self.switch_owsla_app.kill()
        del self.switch_owsla_app
        self.blurb_background.kill()
        del self.blurb_background

        for ele in self.selected_rabbit_elements:
            self.selected_rabbit_elements[ele].kill()
        self.selected_rabbit_elements = {}
