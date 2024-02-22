import pygame
import pygame_gui
import ujson

from .Screens import Screens
from scripts.rabbit.rabbits import Rabbit
from scripts.events_module.freshkill_pile_events import Freshkill_Events
from scripts.game_structure.image_button import UISpriteButton, UIImageButton, UITextBoxTweaked
from scripts.utility import get_text_box_theme, scale, shorten_text_to_fit
from scripts.game_structure.game_essentials import game, screen_x, screen_y, MANAGER

with open('resources/warrensettings.json', 'r', encoding='utf-8') as f:
    settings_dict = ujson.load(f)

class FoodScreen(Screens):
    rabbit_buttons = {}
    conditions_hover = {}
    rabbit_names = []

    def __init__(self, name=None):
        super().__init__(name)
        self.help_button = None
        self.log_box = None
        self.log_title = None
        self.log_tab = None
        self.rabbits_tab = None
        self.tactic_tab = None
        self.nutrition_title = None
        self.satisfied_tab = None
        self.satisfied_rabbits = None
        self.hungry_tab = None
        self.hungry_rabbits = None
        self.info_messages = None
        self.rabbit_bg = None
        self.last_page = None
        self.next_page = None
        self.feed_button = None
        self.pile_base = None
        self.focus_rabbit = None
        self.focus_rabbit_object = None
        self.focus_info = None
        self.focus_name = None
        self.current_page = None
        self.back_button = None
        self.tactic_text = {}
        self.tactic_boxes = {}
        self.additional_text = {}
        self.checkboxes = {}

        self.tab_showing = self.hungry_tab
        self.tab_list = self.hungry_rabbits
        self.pile_size = "#freshkill_pile_average"

        self.open_tab = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.change_screen('burrow screen')
            elif event.ui_element == self.feed_button:
                game.warren.freshkill_pile.feed_rabbit(self.focus_rabbit_object, 1, 0)
                Freshkill_Events.handle_nutrient(self.focus_rabbit_object, game.warren.freshkill_pile.nutrition_info)
                self.update_rabbits_list()
                self.update_nutrition_rabbits()
                self.update_focus_rabbit()
                self.draw_pile()
            elif event.ui_element == self.next_page:
                self.current_page += 1
                self.update_nutrition_rabbits()
            elif event.ui_element == self.last_page:
                self.current_page -= 1
                self.update_nutrition_rabbits()
            elif event.ui_element == self.hungry_tab:
                self.tab_showing.enable()
                self.tab_list = self.hungry_rabbits
                self.tab_showing = self.hungry_tab
                self.hungry_tab.disable()
                self.update_nutrition_rabbits()
            elif event.ui_element == self.satisfied_tab:
                self.tab_showing.enable()
                self.tab_list = self.satisfied_rabbits
                self.tab_showing = self.satisfied_tab
                self.satisfied_tab.disable()
                self.update_nutrition_rabbits()
            elif event.ui_element in self.rabbit_buttons.values() and event.ui_element != self.focus_rabbit:
                self.focus_rabbit_object = event.ui_element.return_rabbit_object()
                self.update_focus_rabbit()
            elif event.ui_element == self.rabbits_tab:
                self.open_tab = "rabbits"
                self.rabbits_tab.disable()
                self.log_tab.enable()
                self.tactic_tab.enable()
                self.handle_tab_toggles()
            elif event.ui_element == self.log_tab:
                self.open_tab = "log"
                self.log_tab.disable()
                self.rabbits_tab.enable()
                self.tactic_tab.enable()
                self.handle_tab_toggles()
            elif event.ui_element == self.tactic_tab:
                self.open_tab = "tactic"
                self.log_tab.enable()
                self.rabbits_tab.enable()
                self.tactic_tab.disable()
                self.handle_tab_toggles()
            self.handle_checkbox_events(event)

    def update_rabbits_list(self):
        self.satisfied_rabbits = []
        self.hungry_rabbits = []
        nutrition_info = game.warren.freshkill_pile.nutrition_info
        low_nutrition_rabbits = [rabbit_id for rabbit_id, nutrient in nutrition_info.items() if nutrient.percentage < 100]
        for the_rabbit in Rabbit.all_rabbits_list:
            if not the_rabbit.dead and not the_rabbit.outside:
                if the_rabbit.ID in low_nutrition_rabbits:
                    self.hungry_rabbits.append(the_rabbit)
                else:
                    self.satisfied_rabbits.append(the_rabbit)
        if self.tab_showing == self.satisfied_tab:
            self.tab_list = self.satisfied_rabbits
        else:
            self.tab_list = self.hungry_rabbits

    def screen_switches(self):
        self.hide_menu_buttons()
        self.back_button = UIImageButton(scale(pygame.Rect((50, 50), (210, 60))), "", object_id="#back_button"
                                         , manager=MANAGER)
        self.feed_button = UIImageButton(scale(pygame.Rect((1250, 600), (160, 60))), "", object_id="#freshkill_feed"
                                      , manager=MANAGER)
        self.feed_button.hide()

        if game.warren.game_mode != 'classic':
            self.help_button = UIImageButton(scale(pygame.Rect(
                (1450, 50), (68, 68))),
                "",
                object_id="#help_button", manager=MANAGER,
                tool_tip_text="Your warren will harvest some amount of food over each timeskip, but successful harvesting patrols are the most "
                              "important source of food. You can see what was consumed and collected in the Log below! "
                              "Food can't be stored endlessly, after four months it will rot and will be thrown away. "
                              "Rabbits under 3 months with a parent taking care of them, don't need food. "
                              "<br><br>"
                              "Feeding the warren is very important, therefore rabbits will be fed before any changes to rank. "
                              "Hover your mouse over the pile to see the current amount and the needed amount of food of your warren! ",

            )
            self.last_page = UIImageButton(scale(pygame.Rect((660, 1272), (68, 68))), "", object_id="#arrow_left_button"
                                           , manager=MANAGER)
            self.next_page = UIImageButton(scale(pygame.Rect((952, 1272), (68, 68))), "",
                                           object_id="#arrow_right_button"
                                           , manager=MANAGER)

            self.nutrition_title = pygame_gui.elements.UITextBox(
                "Nutrition Overview",
                scale(pygame.Rect((281, 820), (400, 60))),
                object_id=get_text_box_theme("#text_box_40_horizcenter"), manager=MANAGER
            )
            self.log_title = pygame_gui.elements.UITextBox(
                "Freshkill Pile Log",
                scale(pygame.Rect((281, 820), (400, 60))),
                object_id=get_text_box_theme("#text_box_40_horizcenter"), manager=MANAGER
            )
            self.tactic_title = pygame_gui.elements.UITextBox(
                "Feeding Tactic",
                scale(pygame.Rect((281, 820), (400, 60))),
                object_id=get_text_box_theme("#text_box_40_horizcenter"), manager=MANAGER
            )
            self.log_title.hide()
            self.tactic_title.hide()
            self.rabbit_bg = pygame_gui.elements.UIImage(scale(pygame.Rect
                                                            ((280, 880), (1120, 400))),
                                                      pygame.image.load(
                                                          "resources/images/sick_hurt_bg.png").convert_alpha()
                                                      , manager=MANAGER)
            self.rabbit_bg.disable()
            log_text = game.freshkill_event_list.copy()
            self.log_box = pygame_gui.elements.UITextBox(
                f"{f'<br>-------------------------------<br>'.join(log_text)}<br>",
                scale(pygame.Rect
                      ((300, 900), (1080, 360))),
                object_id="#text_box_26_horizleft_verttop_pad_14_0_10", manager=MANAGER
            )
            self.log_box.hide()

            self.rabbits_tab = UIImageButton(scale(pygame.Rect
                                                ((218, 924), (70, 150))),
                                          "",
                                          object_id="#hurt_sick_rabbits_button", manager=MANAGER
                                          )
            self.rabbits_tab.disable()
            self.log_tab = UIImageButton(scale(pygame.Rect
                                               ((218, 1104), (70, 128))),
                                         "",
                                         object_id="#med_den_log_button", manager=MANAGER
                                         )
            self.tactic_tab = UIImageButton(scale(pygame.Rect
                                               ((1392, 924), (70, 140))),
                                         "",
                                         object_id="#tactic", manager=MANAGER
                                         )
            self.hungry_tab = UIImageButton(scale(pygame.Rect
                                                   ((980, 818), (160, 70))),
                                             "",
                                             object_id="#freshkill_hungry", manager=MANAGER)
            self.satisfied_tab = UIImageButton(scale(pygame.Rect
                                                 ((1174, 818), (190, 70))),
                                           "",
                                           object_id="#freshkill_satisfied", manager=MANAGER)
            self.tab_showing = self.hungry_tab

            self.update_rabbits_list()
            self.current_page = 1
            self.update_nutrition_rabbits()

        self.update_focus_rabbit()

        self.info_messages = UITextBoxTweaked(
            "",
            scale(pygame.Rect((216, 620), (1200, 160))),
            object_id=get_text_box_theme("#text_box_30_horizcenter_vertcenter"),
            line_spacing=1
        )


        information_display = []

        current_prey_amount = game.warren.freshkill_pile.total_amount
        needed_amount = game.warren.freshkill_pile.amount_food_needed()
        rabbit_need = game.prey_config["prey_requirement"]["rabbit"]
        rabbit_amount = int(current_prey_amount / rabbit_need) 
        general_text = f"Up to {rabbit_amount} rabbits can be fed with this amount of food."

        concern_text = "This should not appear."
        if current_prey_amount == 0:
            concern_text = "The harvest pile is empty, the warren desperately needs food!"
            self.pile_size = "#freshkill_pile_empty"
        elif 0 < current_prey_amount <= needed_amount / 2:
            concern_text = "The harvest pile can't even fed half of the warren. Harvesting patrols should be organized imitatively."
            self.pile_size = "#freshkill_pile_verylow"
        elif needed_amount / 2 < current_prey_amount <= needed_amount:
            concern_text = "Only half of the warren can be fed currently. Harvesting patrols should be organized."
            self.pile_size = "#freshkill_pile_low"
        elif needed_amount < current_prey_amount <= needed_amount * 1.5:
            concern_text = "Every mouth of the warren can be fed, but some more food would not harm."
            self.pile_size = "#freshkill_pile_average"
        elif needed_amount * 1.5 < current_prey_amount <= needed_amount * 2.5:
            concern_text = "The harvest pile is overflowing and the warren can feast!"
            self.pile_size = "#freshkill_pile_good"
        elif needed_amount * 2.5 < current_prey_amount:
            concern_text = "Frith has blessed the warren with plentiful food and the chief rabbit sends their thanks to the sun."
            self.pile_size = "#freshkill_pile_full"

        information_display.append(general_text)
        information_display.append(concern_text)
        self.info_messages.set_text("<br>".join(information_display))
        self.draw_pile()

    def handle_tab_toggles(self):
        if self.open_tab == "rabbits":
            self.tactic_title.hide()
            self.log_title.hide()
            self.log_box.hide()

            self.nutrition_title.show()
            self.last_page.show()
            self.next_page.show()
            self.hungry_tab.show()
            self.satisfied_tab.show()
            for rabbit in self.rabbit_buttons:
                self.rabbit_buttons[rabbit].show()
            for x in range(len(self.rabbit_names)):
                self.rabbit_names[x].show()
            for button in self.conditions_hover:
                self.conditions_hover[button].show()
            self.delete_checkboxes()
        elif self.open_tab == "log":
            self.tactic_title.hide()
            self.nutrition_title.hide()
            self.last_page.hide()
            self.next_page.hide()
            self.hungry_tab.hide()
            self.satisfied_tab.hide()
            for rabbit in self.rabbit_buttons:
                self.rabbit_buttons[rabbit].hide()
            for x in range(len(self.rabbit_names)):
                self.rabbit_names[x].hide()
            for button in self.conditions_hover:
                self.conditions_hover[button].hide()
            self.delete_checkboxes()
            self.log_title.show()
            self.log_box.show()
        elif self.open_tab == "tactic":
            self.nutrition_title.hide()
            self.log_title.hide()
            self.log_box.hide()
            self.last_page.hide()
            self.next_page.hide()
            self.hungry_tab.hide()
            self.satisfied_tab.hide()
            for rabbit in self.rabbit_buttons:
                self.rabbit_buttons[rabbit].hide()
            for x in range(len(self.rabbit_names)):
                self.rabbit_names[x].hide()
            for button in self.conditions_hover:
                self.conditions_hover[button].hide()

            self.tactic_title.show()
            self.create_checkboxes()

    def update_focus_rabbit(self):
        if not self.focus_rabbit_object:
            return
        if self.focus_rabbit:
            self.focus_rabbit.kill()
        if self.focus_info:
            self.focus_info.kill()
        if self.focus_name:
            self.focus_name.kill()

        # if the nutrition is full grey the feed button out
        self.feed_button.show()
        nutrition_info = game.warren.freshkill_pile.nutrition_info
        p = 100
        if self.focus_rabbit_object.ID in nutrition_info:
            p = int(nutrition_info[self.focus_rabbit_object.ID].percentage)
        if p >= 100:
            self.feed_button.disable()
        else:
            self.feed_button.enable()


        name = str(self.focus_rabbit_object.name)
        short_name = shorten_text_to_fit(name, 275, 30)
        self.focus_name = pygame_gui.elements.ui_label.UILabel(
            scale(pygame.Rect ((1100, 150), (450, 60))),
            short_name,
            object_id=get_text_box_theme("#text_box_30_horizcenter"), 
            manager=MANAGER
        )
        self.focus_info = UITextBoxTweaked(
            "",
            scale(pygame.Rect((1180, 190), (300, 240))),
            object_id=get_text_box_theme("#text_box_22_horizcenter"),
            line_spacing=1, manager=MANAGER
        )
        self.focus_rabbit = UISpriteButton(
            scale(pygame.Rect((1180, 290), (300, 300))),
            self.focus_rabbit_object.sprite,
            rabbit_object=self.focus_rabbit_object,
            manager=MANAGER
        )
        info_list = [self.focus_rabbit_object.skills.skill_string(short=True)]
        nutrition_info = game.warren.freshkill_pile.nutrition_info
        if self.focus_rabbit_object.ID in nutrition_info:
            info_list.append("nutrition: " + str(int(nutrition_info[self.focus_rabbit_object.ID].percentage)) + "%")
        work_status = "This rabbit can work"
        if self.focus_rabbit_object.not_working():
            work_status = "This rabbit isn't able to work"
        info_list.append(work_status)

        self.focus_info.set_text("<br>".join(info_list))

    def update_nutrition_rabbits(self):
        """
        set tab showing as either self.hungry_rabbits or self.satisfied_rabbits; whichever one you want to
        display and update
        """
        self.clear_rabbit_buttons()

        tab_list = self.tab_list

        if not tab_list:
            all_pages = []
        else:
            all_pages = self.chunks(tab_list, 10)

        if self.current_page > len(all_pages):
            if len(all_pages) == 0:
                self.current_page = 1
            else:
                self.current_page = len(all_pages)

        # Check for empty list (no rabbits)
        if all_pages:
            self.display_rabbits = all_pages[self.current_page - 1]
        else:
            self.display_rabbits = []

        # Update next and previous page buttons
        if len(all_pages) <= 1:
            self.next_page.disable()
            self.last_page.disable()
        else:
            if self.current_page >= len(all_pages):
                self.next_page.disable()
            else:
                self.next_page.enable()

            if self.current_page <= 1:
                self.last_page.disable()
            else:
                self.last_page.enable()

        pos_x = 350
        pos_y = 920
        i = 0
        for rabbit in self.display_rabbits:
            condition_list = []
            if rabbit.illnesses:
                if "starving" in rabbit.illnesses.keys():
                    condition_list.append("starving")
                elif "malnourished" in rabbit.illnesses.keys():
                    condition_list.append("malnourished")
            if self.tab_showing == self.hungry_tab:
                nutrition_info = game.warren.freshkill_pile.nutrition_info
                if rabbit.ID in nutrition_info:
                    p = int(nutrition_info[rabbit.ID].percentage)
                    condition_list.append(f" nutrition: {p}%")
            conditions = ",<br>".join(condition_list) if len(condition_list) > 0 else None

            self.rabbit_buttons["able_rabbit" + str(i)] = UISpriteButton(scale(pygame.Rect
                                                                         ((pos_x, pos_y), (100, 100))),
                                                                   rabbit.sprite,
                                                                   rabbit_object=rabbit,
                                                                   manager=MANAGER,
                                                                   tool_tip_text=conditions,
                                                                   starting_height=2)


            name = str(rabbit.name)
            short_name = shorten_text_to_fit(name, 185, 30)
            self.rabbit_names.append(pygame_gui.elements.UITextBox(short_name,
                                                                scale(
                                                                    pygame.Rect((pos_x - 60, pos_y + 100), (220, 60))),
                                                                object_id="#text_box_30_horizcenter", manager=MANAGER))

            pos_x += 200
            if pos_x >= 1340:
                pos_x = 350
                pos_y += 160
            i += 1

    def draw_pile(self):
        if self.pile_base:
            self.pile_base.kill()
        current_prey_amount = game.warren.freshkill_pile.total_amount
        needed_amount = round(game.warren.freshkill_pile.amount_food_needed(), 2)
        hover_display = f"<b>Current amount:</b> {current_prey_amount}<br><b>Needed amount:</b> {needed_amount}"
        self.pile_base = UIImageButton(scale(pygame.Rect
                                            ((500, 50), (600, 600))),
                                      "",
                                      object_id=self.pile_size,
                                      tool_tip_text=hover_display, manager=MANAGER
                                      )

    def exit_screen(self):
        self.info_messages.kill()
        self.feed_button.kill()
        self.pile_base.kill()
        self.focus_rabbit_object = None
        if self.focus_info:
            self.focus_info.kill()
        if self.focus_name:
            self.focus_name.kill()
        self.back_button.kill()
        if game.warren.game_mode != 'classic':
            self.help_button.kill()
            self.rabbit_bg.kill()
            self.last_page.kill()
            self.next_page.kill()
            self.hungry_tab.kill()
            self.satisfied_tab.kill()
            self.clear_rabbit_buttons()
            self.nutrition_title.kill()
            self.rabbits_tab.kill()
            self.log_tab.kill()
            self.log_title.kill()
            self.log_box.kill()
            self.tactic_tab.kill()
            self.tactic_title.kill()
            self.delete_checkboxes()
        if self.focus_rabbit:
            self.focus_rabbit.kill()

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]

    def clear_rabbit_buttons(self):
        for rabbit in self.rabbit_buttons:
            self.rabbit_buttons[rabbit].kill()
        for button in self.conditions_hover:
            self.conditions_hover[button].kill()
        for x in range(len(self.rabbit_names)):
            self.rabbit_names[x].kill()

        self.rabbit_names = []
        self.rabbit_buttons = {}

    def create_checkboxes(self):
        self.delete_checkboxes()

        self.tactic_text["container_general"] = pygame_gui.elements.UIScrollingContainer(
            scale(pygame.Rect((280, 900), (460, 350))), manager=MANAGER
        )

        n = 0
        x_val = 110
        for code, desc in settings_dict['freshkill_tactics'].items():
            if code == "ration prey":
                continue
            if len(desc) == 4 and isinstance(desc[3], list):
                x_val += 40
            
            self.tactic_text[code] = pygame_gui.elements.UITextBox(
                desc[0],
                scale(pygame.Rect((x_val, n * 70), (1000, 78))),
                container=self.tactic_text["container_general"],
                object_id=get_text_box_theme("#text_box_30_horizleft_pad_0_8"),
                manager=MANAGER)
            n += 1

        self.tactic_text["container_general"].set_scrollable_area_dimensions(
            (400 / 1600 * screen_x, (n * 60 + x_val + 40) / 1600 * screen_y)
        )

        self.additional_text["container_general"] = pygame_gui.elements.UIScrollingContainer(
            scale(pygame.Rect((720, 900), (655, 350))), manager=MANAGER
        )

        n = 0
        x_val = 110
        for code, desc in settings_dict['freshkill_tactics'].items():
            if code == "ration prey":
                # Handle nested
                if len(desc) == 4 and isinstance(desc[3], list):
                    x_val += 40

                self.additional_text[code] = pygame_gui.elements.UITextBox(
                    desc[0],
                    scale(pygame.Rect((x_val, n * 60), (1000, 78))),
                    container=self.additional_text["container_general"],
                    object_id=get_text_box_theme("#text_box_30_horizleft_pad_0_8"),
                    manager=MANAGER)
                n += 1

        x_val = 45
        self.additional_text["condition_increase"] = pygame_gui.elements.UITextBox(
            "<b>Status-order + needed amount:</b>",
            scale(pygame.Rect((x_val, n * 50 + 10), (1000, 78))),
            container=self.additional_text["container_general"],
            object_id=get_text_box_theme("#text_box_30_horizleft_pad_0_8"),
            manager=MANAGER
        )

        prey_requirement = game.prey_config["prey_requirement"]
        feeding_order = game.prey_config["feeding_order"]
        for status in feeding_order:
            amount = prey_requirement[status]
            self.additional_text["condition_increase"] = pygame_gui.elements.UITextBox(
                f"{n}. {status}: {amount} prey",
                scale(pygame.Rect((x_val, n * 45 + 55), (1000, 78))),
                container=self.additional_text["container_general"],
                object_id=get_text_box_theme("#text_box_30_horizleft_pad_0_8"),
                manager=MANAGER)
            n += 1

        self.additional_text["container_general"].set_scrollable_area_dimensions(
            (610 / 1600 * screen_x, (n * 60) / 1600 * screen_y)
        )


        self.refresh_checkboxes("general")

    def delete_checkboxes(self):
        for checkbox in self.tactic_boxes.values():
            checkbox.kill()
        self.tactic_boxes = {}
        for text in self.tactic_text.values():
            text.kill()
        self.tactic_text = {}
        for checkbox in self.checkboxes.values():
            checkbox.kill()
        self.checkboxes = {}
        for text in self.additional_text.values():
            text.kill()
        self.additional_text = {}

    def refresh_checkboxes(self, sub_menu):
        """
        TODO: DOCS
        """
        # Kill the checkboxes. No mercy here.
        for checkbox in self.tactic_boxes.values():
            checkbox.kill()
        self.tactic_boxes = {}

        n = 0
        for code, desc in settings_dict["freshkill_tactics"].items():
            if code == "ration prey":
                continue
            if game.warren.warren_settings[code]:
                box_type = "#checked_checkbox"
            else:
                box_type = "#unchecked_checkbox"
                
            # Handle nested
            disabled = False
            x_val = 20
            if len(desc) == 4 and isinstance(desc[3], list):
                x_val += 50
                disabled = game.warren.warren_settings.get(desc[3][0], not desc[3][1]) != desc[3][1]
                
            self.tactic_boxes[code] = UIImageButton(
                scale(pygame.Rect((x_val, n * 70), (68, 68))),
                "",
                object_id=box_type,
                container=self.tactic_text["container_" + sub_menu],
                tool_tip_text=desc[1])
            
            if disabled:
                self.tactic_boxes[code].disable()

            n += 1

        for checkbox in self.checkboxes.values():
            checkbox.kill()
        self.checkboxes = {}

        n = 0
        for code, desc in settings_dict["freshkill_tactics"].items():
            if code == "ration prey":
                if game.warren.warren_settings[code]:
                    box_type = "#checked_checkbox"
                else:
                    box_type = "#unchecked_checkbox"

                # Handle nested
                disabled = False
                x_val = 20
                if len(desc) == 4 and isinstance(desc[3], list):
                    x_val += 50
                    disabled = game.warren.warren_settings.get(desc[3][0], not desc[3][1]) != desc[3][1]

                self.checkboxes[code] = UIImageButton(
                    scale(pygame.Rect((x_val, n * 50), (68, 68))),
                    "",
                    object_id=box_type,
                    container=self.additional_text["container_" + sub_menu],
                    tool_tip_text=desc[1])

                if disabled:
                    self.checkboxes[code].disable()
                n += 1

    def handle_checkbox_events(self, event):
        """
        Switch on or off, only allow one checkbox to be selected.
        """
        active_key = None
        if event.ui_element in self.tactic_boxes.values():
            for key, value in self.tactic_boxes.items():
                if value == event.ui_element and value.object_ids[1] == "#unchecked_checkbox":
                    game.warren.switch_setting(key)
                    active_key = key
                    self.settings_changed = True
                    self.create_checkboxes()
                    break

            # un-switch all other keys
            for key, value in self.tactic_boxes.items():
                if active_key and key != active_key and value.object_ids[1] == "#checked_checkbox":
                    game.warren.switch_setting(key)
                    self.settings_changed = True
                    self.create_checkboxes()
                    break

        if event.ui_element in self.checkboxes.values():
            for key, value in self.checkboxes.items():
                if value == event.ui_element:
                    game.warren.switch_setting(key)
                    active_key = key
                    self.settings_changed = True
                    self.create_checkboxes()
                    break