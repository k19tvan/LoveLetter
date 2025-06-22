import os
import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.image import AsyncImage
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

INTRO_BACKGROUND = "assets/chill.webp"  
RULES_BACKGROUND = "assets/rule.jpg"  
EMPTY_CARD_IMAGE = "assets/cards/empty_card.png"

from logic4 import (
    Player, Deck, GameRound, Card,
    CARD_PROTOTYPES, CARDS_DATA_RAW,
    CARD_FOLDER, CARD_BACK_IMAGE, ELIMINATED_IMAGE
)

Window.size = (1000, 800)
Window.clearcolor = (0.1, 0.1, 0.2, 1)


class StyledLabel(Label):
    """Standard styled label for consistent UI appearance"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = kwargs.get('color', (0.9, 0.9, 1, 1))
        self.bold = kwargs.get('bold', True)
        self.outline_width = kwargs.get('outline_width', 1)
        self.outline_color = kwargs.get('outline_color', (0, 0, 0, 1))


class ImageButton(ButtonBehavior, Image):
    """Image with button behavior and card info display on right-click"""
    def __init__(self, **kwargs):
        self.card_info_callback = kwargs.pop('card_info_callback', None)
        self.card_data = kwargs.pop('card_data', None)
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = True
        
    def on_press(self):
        self.opacity = 0.8
        
    def on_release(self):
        self.opacity = 1.0
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and touch.button == 'right' and self.card_info_callback and self.card_data:
            self.card_info_callback(self.card_data)
            return True
        return super(ImageButton, self).on_touch_down(touch)


class CardDisplay(BoxLayout):
    """Card display widget with rounded corners and styling"""
    def __init__(self, card_source="", name="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 5
        self.size_hint_y = None
        self.height = 180
        
        # Add background with rounded corners
        with self.canvas.before:
            Color(0.2, 0.2, 0.3, 0.7)
            self.bg = RoundedRectangle(radius=[10,])
            
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Card image with border
        self.card_image = Image(source=card_source, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.card_image)
        
        # Name label
        self.name_label = StyledLabel(text=name, size_hint_y=0.2, font_size='12sp')
        self.add_widget(self.name_label)
        
    def _update_rect(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size


class IntroScreen(Screen):
    """Introduction screen with fullscreen background"""
    def __init__(self, **kwargs):
        super(IntroScreen, self).__init__(**kwargs)
        layout = FloatLayout()
        
        # Hình nền tràn màn hình
        bg_image = Image(
            source=INTRO_BACKGROUND,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        layout.add_widget(bg_image)
        
        # Tạo container để chứa nút (để thêm hiệu ứng viền)
        button_container = RelativeLayout(
            size_hint=(0.4, 0.12),
            pos_hint={'center_x': 0.5, 'center_y': 0.2}
        )
        
        # Thêm nút bắt đầu trò chơi (trước khi thêm viền để tránh overlay)
        start_button = Button(
            text="BẮT ĐẦU CHƠI",
            font_size=32,
            bold=True,
            background_color=(0.8, 0.1, 0.1, 0.85),  # Màu đỏ sẫm như túi Love Letter
            color=(1, 0.9, 0.5, 1),  # Màu vàng giống chữ trên túi
            size_hint=(0.95, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # Thêm hiệu ứng khi nhấn
        def on_press(instance):
            instance.background_color = (0.9, 0.2, 0.2, 0.9)
            instance.font_size = 34
            
        def on_release(instance):
            instance.background_color = (0.8, 0.1, 0.1, 0.85)
            instance.font_size = 32
            self.go_to_rules(instance)
            
        start_button.bind(on_press=on_press)
        start_button.bind(on_release=on_release)
        
        # Thêm nút vào container
        button_container.add_widget(start_button)
        
        # Thêm đường viền cho container nút sau khi đã thêm nút vào
        with button_container.canvas.before:
            Color(0.9, 0.8, 0.3, 0.7)  # Màu vàng cho viền
            self.border_rect = RoundedRectangle(radius=[10])
            
        # Gọi update_rect ngay sau khi tạo để đặt vị trí ban đầu cho viền
        def update_rect(*args):
            self.border_rect.pos = button_container.pos
            self.border_rect.size = button_container.size
            
        button_container.bind(pos=update_rect, size=update_rect)
        # Cập nhật ngay lần đầu thay vì đợi sự kiện
        Clock.schedule_once(lambda dt: update_rect(), 0)
        
        layout.add_widget(button_container)
        self.add_widget(layout)
                
    def go_to_rules(self, instance):
        self.manager.current = 'rules'

class RulesScreen(Screen):
    """Rules screen with fullscreen background"""
    game_instance = None  # Will be set by app
    
    def __init__(self, **kwargs):
        super(RulesScreen, self).__init__(**kwargs)
        layout = FloatLayout()
        
        # Hình nền tràn màn hình
        bg_image = Image(
            source=RULES_BACKGROUND,
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # Thêm hint text để người dùng biết có thể nhấn vào màn hình
        hint_label = Label(
            text="Nhấn vào màn hình để bắt đầu chơi",
            font_size=24,
            bold=True,
            color=(1, 0.9, 0.5, 1),
            size_hint=(0.8, 0.1),
            pos_hint={'center_x': 0.5, 'bottom': 0.05}
        )
        
        layout.add_widget(bg_image)
        layout.add_widget(hint_label)
        
        # Gắn sự kiện nhấn vào bất kỳ đâu trên màn hình
        layout.bind(on_touch_down=self.on_layout_click)
        
        self.add_widget(layout)
        
    def on_layout_click(self, instance, touch):
        """Handle click anywhere on the rules screen"""
        if self.collide_point(*touch.pos):
            self.start_game(None)
            return True
        return super(RulesScreen, self).on_touch_down(touch)
        
    def start_game(self, instance):
        """Start the game when user clicks anywhere on the rules screen"""
        self.manager.current = 'game'
        # Initialize the game when entering the game screen
        if hasattr(self, 'game_instance') and self.game_instance:
            Clock.schedule_once(lambda dt: self.game_instance.initialize_game_setup(), 0.1)

class LoveLetterGame(BoxLayout):  
    """Main game widget containing all game logic and UI"""
    def __init__(self, **kwargs):
        # Initialize essential properties first
        self.game_log = ["Welcome to Love Letter Kivy!"]
        self.num_players_session = 0
        self.players_session_list = []
        self.human_player_id = 0
        self.current_round_manager = None
        self.tokens_to_win_session = 0
        self.game_over_session_flag = True
        self.active_popup = None
        self.waiting_for_input = False
        self.opponent_widgets_map = {}
        self.animated_widget_details = {}
        
        super().__init__(**kwargs)
        
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        
        # Background
        with self.canvas.before:
            Color(0.15, 0.15, 0.25, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Use Clock to handle setup instead of on_kv_post
        Clock.schedule_once(self._delayed_setup, 1)
        
    def _update_rect(self, instance, value):
        """Update rectangle position and size - unified method for all UI elements"""
        if hasattr(instance, 'bg'):
            instance.bg.pos = instance.pos
            instance.bg.size = instance.size
        
        # Handle RoundedRectangle in canvas.before
        if hasattr(instance, 'canvas') and hasattr(instance.canvas, 'before'):
            for instruction in instance.canvas.before.children:
                if isinstance(instruction, RoundedRectangle) or isinstance(instruction, Rectangle):
                    instruction.pos = instance.pos
                    instruction.size = instance.size
        
    def _delayed_setup(self, dt):
        """Initialization called after widget has been added to the window"""
        self._load_card_prototypes_and_images()
        self.setup_ui_placeholders()
        
    def initialize_game_setup(self):
        """Called when the user presses Start Game from the Rules screen"""
        self.prompt_player_count()
        
    def cleanup_leftover_rectangles(self):
        """Remove all extra Rectangle objects from widget canvases"""
        # Clear animations
        self._clear_animations_and_proceed(None)
        
        # Check widgets recursively
        widgets_to_check = [self] + self.children[:] 
        if hasattr(self, 'opponents_grid'):
            widgets_to_check.append(self.opponents_grid)
            widgets_to_check.extend(self.opponents_grid.children[:])
        
        for widget in widgets_to_check:
            if hasattr(widget, 'canvas') and hasattr(widget.canvas, 'before') and hasattr(widget.canvas.before, 'children'):
                instructions_to_remove = [
                    instruction for instruction in widget.canvas.before.children 
                    if (isinstance(instruction, Rectangle) or isinstance(instruction, RoundedRectangle)) 
                    and not hasattr(widget, '_update_rect')
                ]
                for instruction in instructions_to_remove:
                    widget.canvas.before.remove(instruction)
                        
    def display_card_info_popup(self, card_data):
        """Display detailed information about a card in a popup"""
        self.dismiss_active_popup()  # Close any existing popup
        
        # Card colors based on value
        card_colors = {
            0: (0.5, 0.5, 0.5),  # Gray
            1: (0.2, 0.4, 1.0),  # Blue
            2: (0.7, 0.7, 1.0),  # Light blue
            3: (0.6, 0.3, 0.7),  # Purple
            4: (0.3, 0.7, 0.3),  # Green
            5: (0.9, 0.7, 0.2),  # Gold
            6: (0.9, 0.5, 0.3),  # Orange
            7: (0.7, 0.3, 0.7),  # Violet
            8: (1.0, 0.3, 0.3),  # Red
            9: (0.9, 0.9, 1.0),  # White
        }
        
        card_value = card_data.value if hasattr(card_data, 'value') else 0
        card_color = card_colors.get(card_value, (0.5, 0.5, 0.5))
        
        # Create popup layout
        popup_layout = BoxLayout(orientation='vertical', spacing=0, padding=0)
        
        # Header with card name
        header = BoxLayout(orientation='vertical', size_hint_y=0.15, padding=[15, 5])
        with header.canvas.before:
            Color(*card_color, 0.9)
            header_bg = RoundedRectangle(radius=[5, 5, 0, 0])
        header.bind(pos=lambda inst, val: self._update_rect(header, val), 
                  size=lambda inst, val: self._update_rect(header, val))
        
        # Card name with Vietnamese name
        name_row = BoxLayout(orientation='horizontal')
        
        name_box = BoxLayout(orientation='vertical', size_hint_x=0.7)
        card_name_label = StyledLabel(
            text=f"{card_data.name}",
            font_size=24,
            bold=True,
            color=(1, 1, 1, 1),
            outline_width=2,
            outline_color=(0, 0, 0, 0.5),
            halign='left'
        )
        name_box.add_widget(card_name_label)
        
        if hasattr(card_data, 'vietnamese_name'):
            viet_name_label = StyledLabel(
                text=f"({card_data.vietnamese_name})",
                font_size=16,
                italic=True,
                color=(1, 1, 1, 0.9),
                halign='left'
            )
            name_box.add_widget(viet_name_label)
        
        # Value display
        value_box = BoxLayout(orientation='vertical', size_hint_x=0.3)
        value_label = StyledLabel(
            text=f"Value: {card_data.value}",
            font_size=20,
            bold=True,
            color=(1, 1, 1, 1),
            outline_width=1,
            outline_color=(0, 0, 0, 0.5)
        )
        value_box.add_widget(value_label)
        
        name_row.add_widget(name_box)
        name_row.add_widget(value_box)
        header.add_widget(name_row)
        
        popup_layout.add_widget(header)
        
        # Main content in horizontal layout
        content = BoxLayout(orientation='horizontal', padding=15, spacing=10)
        
        # Card image
        image_frame = BoxLayout(orientation='vertical', size_hint_x=0.4, padding=5)
        with image_frame.canvas.before:
            Color(0.15, 0.15, 0.2, 0.8)
            image_bg = RoundedRectangle(radius=[5])
        image_frame.bind(pos=lambda inst, val: self._update_rect(image_frame, val), 
                       size=lambda inst, val: self._update_rect(image_frame, val))
        
        card_image = Image(
            source=card_data.image_path,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        image_frame.add_widget(card_image)
        content.add_widget(image_frame)
        
        # Card effect description
        effect_panel = BoxLayout(orientation='vertical', 
                            size_hint_x=0.6,
                            spacing=10)
        
        effect_title = StyledLabel(
            text="Effect:",
            font_size=22,
            bold=True,
            color=(0.9, 0.8, 0.3, 1),
            size_hint_y=None,
            height=40,
            halign='center'
        )
        effect_title.bind(size=effect_title.setter('text_size'))
        effect_panel.add_widget(effect_title)
        
        effect_box = BoxLayout(size_hint_y=1, padding=10)
        with effect_box.canvas.before:
            Color(0.15, 0.15, 0.2, 0.6)
            RoundedRectangle(pos=effect_box.pos, size=effect_box.size, radius=[5])
        effect_box.bind(pos=lambda inst, val: self._update_rect(effect_box, val), 
                      size=lambda inst, val: self._update_rect(effect_box, val))
        
        effect_scroll = ScrollView(do_scroll_x=False)
        
        effect_text = StyledLabel(
            text=card_data.description,
            font_size=20,
            size_hint_y=None,
            halign='center',
            valign='middle',
            color=(0.95, 0.95, 1, 1),
            padding=(15, 15),
            markup=True
        )
        
        effect_text.bind(width=lambda *x: effect_text.setter('text_size')(effect_text, (effect_text.width, None)))
        effect_text.bind(texture_size=effect_text.setter('size'))
        effect_scroll.add_widget(effect_text)
        effect_box.add_widget(effect_scroll)
        effect_panel.add_widget(effect_box)
        
        content.add_widget(effect_panel)
        popup_layout.add_widget(content)
        
        # Close button
        footer = BoxLayout(orientation='horizontal', size_hint_y=0.1, padding=[15, 10])
        footer.add_widget(Widget(size_hint_x=0.35))
        
        close_btn = Button(
            text="Close",
            size_hint=(0.3, 0.8),
            background_color=(*card_color, 1.0),
            font_size=18,
            bold=True,
            pos_hint={'center_y': 0.5}
        )
        close_btn.bind(on_press=lambda x: self.dismiss_active_popup())
        footer.add_widget(close_btn)
        
        footer.add_widget(Widget(size_hint_x=0.35))
        popup_layout.add_widget(footer)
        
        # Create popup
        self.active_popup = Popup(
            title="Card Information",
            content=popup_layout,
            size_hint=(0.85, 0.8),
            title_color=(0.9, 0.9, 0.7, 1),
            title_size='20sp',
            title_align='center',
            separator_color=card_color,
            auto_dismiss=True
        )
        
        self.active_popup.open()

    def _load_card_prototypes_and_images(self):
        """Load card prototypes and images from the data files"""
        global CARD_PROTOTYPES
        CARD_PROTOTYPES.clear()

        missing_card_back = not os.path.exists(CARD_BACK_IMAGE)
        if missing_card_back:
            self.log_message(f"CRITICAL ERROR: Card back image not found at {CARD_BACK_IMAGE}", permanent=True)

        for eng_name, data in CARDS_DATA_RAW.items():
            viet_name = data['vietnamese_name']
            path_jpg = os.path.join(CARD_FOLDER, f"{viet_name}.jpg")
            path_png = os.path.join(CARD_FOLDER, f"{viet_name}.png")
            actual_path = next((p for p in [path_jpg, path_png] if os.path.exists(p)), None)

            if not actual_path:
                self.log_message(f"Warning: Image for '{eng_name}' ({viet_name}) not found. Using card back.",
                                 permanent=True)
                actual_path = CARD_BACK_IMAGE if not missing_card_back else ""

            CARD_PROTOTYPES[eng_name] = Card(
                name=eng_name,
                value=data['value'],
                description=data['description'],
                image_path=actual_path,
                vietnamese_name=viet_name,
                count_classic=data['count_classic'],
                count_large=data['count_large']
            )
        self.log_message(f"Card prototypes loaded: {len(CARD_PROTOTYPES)} card types", permanent=True)

    def setup_ui_placeholders(self):
        """Create initial welcome screen while waiting to start the game"""
        self.clear_widgets()
        
        welcome_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Game title
        title_label = StyledLabel(
            text="Love Letter Board Game", 
            font_size=32,
            color=(0.9, 0.7, 0.8, 1),
            size_hint_y=0.3
        )
        welcome_layout.add_widget(title_label)
        
        # Card back image
        image_box = BoxLayout(size_hint_y=0.4)
        if os.path.exists(CARD_BACK_IMAGE):
            welcome_image = Image(source=CARD_BACK_IMAGE, size_hint_max_x=0.7)
            welcome_image.pos_hint = {'center_x': 0.5}
            image_box.add_widget(welcome_image)
        welcome_layout.add_widget(image_box)
        
        # Waiting message
        waiting_label = StyledLabel(
            text="Đang chờ bắt đầu trò chơi...", 
            font_size=24, 
            size_hint_y=0.3
        )
        welcome_layout.add_widget(waiting_label)
        
        self.add_widget(welcome_layout)

    def prompt_player_count(self):
        """Show popup to select number of players"""
        self.game_log = ["Welcome to Love Letter Kivy!", "Please select number of players (2-8)."]
        if hasattr(self, 'message_label'): 
            self.log_message("", permanent=False)

        popup_layout = BoxLayout(orientation='vertical', spacing="15dp", padding="20dp")
        
        title_label = StyledLabel(
            text="Select Number of Players (2-8):", 
            font_size=22,
            size_hint_y=None, 
            height="50dp"
        )
        popup_layout.add_widget(title_label)
        
        options_layout = GridLayout(cols=4, spacing="10dp", size_hint_y=None)
        options_layout.bind(minimum_height=options_layout.setter('height'))
        
        for i in range(2, 5):
            btn = Button(
                text=str(i), 
                size_hint_y=None, 
                height="60dp",
                background_color=(0.3, 0.4, 0.8, 1),
                font_size=20,
                bold=True
            )
            btn.player_count = i
            btn.bind(on_press=self.initialize_game_with_player_count)
            options_layout.add_widget(btn)
            
        popup_layout.add_widget(options_layout)
        
        self.active_popup = Popup(
            title="Love Letter - Player Count", 
            content=popup_layout,
            size_hint=(0.6, 0.4), 
            auto_dismiss=False,
            title_color=(1, 0.9, 0.8, 1),
            title_size='20sp',
            title_align='center',
            background="atlas://data/images/defaulttheme/button_pressed"
        )
        self.active_popup.open()

    def initialize_game_with_player_count(self, instance):
        """Initialize a new game with the selected player count"""
        if self.active_popup:
            self.active_popup.dismiss()
            self.active_popup = None
            
        self.num_players_session = instance.player_count
        self.log_message(f"Number of players set to: {self.num_players_session}")

        # Set tokens needed to win based on player count
        if self.num_players_session == 2:
            self.tokens_to_win_session = 7
        elif self.num_players_session == 3:
            self.tokens_to_win_session = 5
        elif self.num_players_session == 4:
            self.tokens_to_win_session = 4
        else:
            self.tokens_to_win_session = 3
        self.log_message(f"Tokens needed to win: {self.tokens_to_win_session}")

        # Create player list with human player as ID 0
        self.players_session_list = [Player(id_num=0, name="Player 1 (You)")]
        self.human_player_id = self.players_session_list[0].id
        for i in range(1, self.num_players_session):
            self.players_session_list.append(Player(id_num=i, name=f"CPU {i}", is_cpu=True))

        self.setup_main_ui()
        self.start_new_game_session()

    def setup_main_ui(self):
        """Create the main game UI with all components"""
        self.clear_widgets()
        
        # Top section with scores and game log
        top_section = BoxLayout(size_hint_y=0.17, orientation='vertical', spacing=5)
        
        # Info bar with scores and turn indicator
        info_bar = BoxLayout(size_hint_y=None, height=40, padding=[10, 5])
        with info_bar.canvas.before:
            Color(0.25, 0.35, 0.55, 0.85)
            info_bar_bg = RoundedRectangle(radius=[10,])
        info_bar.bind(pos=lambda inst, val: self._update_rect(info_bar, val),
                    size=lambda inst, val: self._update_rect(info_bar, val))
            
        self.score_label = StyledLabel(
            text="Scores:", 
            size_hint_x=0.7, 
            halign='left', 
            valign='middle', 
            font_size=16,
            bold=True,
            color=(0.95, 0.9, 0.7, 1)
        )
        self.score_label.bind(size=self.score_label.setter('text_size'))
        
        self.turn_label = StyledLabel(
            text="Game Over", 
            size_hint_x=0.3, 
            halign='right', 
            valign='middle', 
            color=(1, 0.85, 0.3, 1),
            font_size=17,
            bold=True
        )
        
        self.turn_label.bind(size=self.turn_label.setter('text_size'))
        
        info_bar.add_widget(self.score_label)
        info_bar.add_widget(self.turn_label)
        top_section.add_widget(info_bar)
        
        # Game log with scrollview
        log_container = BoxLayout(size_hint_y=1, padding=[10, 5])
        with log_container.canvas.before:
            Color(0.08, 0.08, 0.15, 0.8)
            log_container_bg = RoundedRectangle(radius=[10,])
        log_container.bind(pos=lambda inst, val: self._update_rect(log_container, val),
                         size=lambda inst, val: self._update_rect(log_container, val))
        
        log_scroll_view = ScrollView(size_hint_y=1)
        self.message_label = Label(
            text="\n".join(self.game_log), 
            size_hint_y=None, 
            halign='left', 
            valign='top',
            color=(0.95, 0.95, 0.98, 1),
            font_size=14,
            padding=(15, 10),
            font_name='Roboto'
        )
        self.message_label.bind(texture_size=self.message_label.setter('size'))
        log_scroll_view.add_widget(self.message_label)
        log_container.add_widget(log_scroll_view)
        top_section.add_widget(log_container)
        self.add_widget(top_section)

        # Main game area
        game_area = BoxLayout(orientation='vertical', spacing=15, size_hint_y=0.7)
        
        # Opponents area with title
        opponents_header = BoxLayout(size_hint_y=None, height=35, padding=[10, 0])
        with opponents_header.canvas.before:
            Color(0.2, 0.2, 0.35, 0.8)
            opponents_header_bg = RoundedRectangle(pos=opponents_header.pos, size=opponents_header.size, radius=[10, 10, 0, 0])
        opponents_header.bind(pos=lambda inst, val: self._update_rect(opponents_header, val),
                            size=lambda inst, val: self._update_rect(opponents_header, val))

        opponents_header.add_widget(Widget(size_hint_x=0.08))
        opponents_header.add_widget(StyledLabel(
            text="Opponents", 
            size_hint_x=0.92,
            size_hint_y=None, 
            height=35, 
            font_size=18,
            bold=True,
            color=(0.95, 0.8, 0.4, 1)
        ))
        game_area.add_widget(opponents_header)
        
        # Opponents display grid
        opponents_container = BoxLayout(size_hint_y=0.4, padding=[5, 0, 5, 10])
        with opponents_container.canvas.before:
            Color(0.12, 0.12, 0.22, 0.8)
            self.opponents_bg = RoundedRectangle(radius=[0, 0, 10, 10])
        opponents_container.bind(pos=lambda inst, val: self._update_rect(opponents_container, val),
                               size=lambda inst, val: self._update_rect(opponents_container, val))

        self.opponents_area_scrollview = ScrollView(size_hint=(1, 1))
        self.opponents_grid = GridLayout(
            cols=max(1, min(4, self.num_players_session - 1) if self.num_players_session > 1 else 1),
            size_hint_x=None if self.num_players_session - 1 > 3 else 1, 
            size_hint_y=None,
            spacing=15,
            padding=[10, 10]
        )
        
        self.opponents_grid.bind(minimum_width=self.opponents_grid.setter('width'))
        self.opponents_grid.bind(minimum_height=self.opponents_grid.setter('height'))
        self.opponents_area_scrollview.add_widget(self.opponents_grid)
        opponents_container.add_widget(self.opponents_area_scrollview)
        game_area.add_widget(opponents_container)
        
        # Player hand area
        self.human_player_display_wrapper = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=10)
        
        player_header = BoxLayout(size_hint_y=None, height=35, padding=[10, 0])
        with player_header.canvas.before:
            Color(0.15, 0.3, 0.25, 0.8)
            player_header_bg = RoundedRectangle(radius=[10, 10, 0, 0])
        player_header.bind(pos=lambda inst, val: self._update_rect(player_header, val),
                         size=lambda inst, val: self._update_rect(player_header, val))

        player_header.add_widget(Widget(size_hint_x=0.08))
        player_header.add_widget(StyledLabel(
            text="Your Hand (Click to Play)", 
            size_hint_x=0.92,
            size_hint_y=None, 
            height=35, 
            font_size=18,
            bold=True,
            color=(0.4, 0.9, 0.7, 1)
        ))
        self.human_player_display_wrapper.add_widget(player_header)
        
        player_hand_container = BoxLayout(size_hint_y=0.7)
        with player_hand_container.canvas.before:
            Color(0.08, 0.2, 0.15, 0.8)
            player_hand_bg = RoundedRectangle(radius=[0, 0, 10, 10])
        player_hand_container.bind(pos=lambda inst, val: self._update_rect(player_hand_container, val),
                                 size=lambda inst, val: self._update_rect(player_hand_container, val))

        self.player_hand_area = BoxLayout(orientation='horizontal', spacing=20, padding=[20, 15])
        player_hand_container.add_widget(self.player_hand_area)
        self.human_player_display_wrapper.add_widget(player_hand_container)
        
        game_area.add_widget(self.human_player_display_wrapper)
        
        # Center game area with deck, played card, and game info
        center_game_area = BoxLayout(size_hint_y=0.2, spacing=10, padding=[10, 5])

        # Left area: Deck
        left_area = BoxLayout(orientation='vertical', size_hint_x=0.25)
        left_area.add_widget(StyledLabel(
            text="Deck", 
            size_hint_y=0.2,
            font_size=16,
            color=(0.9, 0.9, 0.7, 1)
        ))

        # Deck display with 3D effect
        deck_display = RelativeLayout(size_hint_y=0.6)
        for i in range(2):
            offset = 1.0 * (i + 1)
            shadow_card = Image(
                source=CARD_BACK_IMAGE,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(0.8, 0.8),
                pos_hint={'center_x': 0.5 - 0.02 * offset, 'center_y': 0.5 - 0.02 * offset},
                opacity=0.5 - 0.15*i
            )
            deck_display.add_widget(shadow_card)

        self.deck_image = Image(
            source=CARD_BACK_IMAGE, 
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.8, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        deck_display.add_widget(self.deck_image)
        left_area.add_widget(deck_display)

        # Cards remaining count
        self.deck_count_label = StyledLabel(
            text="0 cards", 
            size_hint_y=0.2,
            font_size=14,
            color=(0.9, 0.9, 0.7, 1)
        )
        left_area.add_widget(self.deck_count_label)

        # Center area: Last played card
        center_area = BoxLayout(orientation='vertical', size_hint_x=0.5)
        self.last_played_title = StyledLabel(
            text="Lá bài vừa đánh", 
            size_hint_y=0.2,
            font_size=16,
            bold=True,
            color=(0.9, 0.8, 0.3, 1)
        )
        center_area.add_widget(self.last_played_title)

        # Last played card container
        played_card_frame = BoxLayout(size_hint_y=0.8, padding=[10, 5])
        with played_card_frame.canvas.before:
            Color(0.1, 0.15, 0.2, 0.5)
            played_card_bg = RoundedRectangle(radius=[10,])
        played_card_frame.bind(pos=lambda inst, val: self._update_rect(played_card_frame, val),
                             size=lambda inst, val: self._update_rect(played_card_frame, val))

        self.last_played_card_container = RelativeLayout(size_hint=(1, 1))
        self.last_played_card_image = Image(
            source=EMPTY_CARD_IMAGE,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(0.9, 0.9),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0.3
        )
        self.last_played_card_container.add_widget(self.last_played_card_image)
        played_card_frame.add_widget(self.last_played_card_container)
        center_area.add_widget(played_card_frame)

        # Right area: Game information
        right_area = BoxLayout(orientation='vertical', size_hint_x=0.25)
        right_area.add_widget(StyledLabel(
            text="Thông tin", 
            size_hint_y=0.2,
            font_size=16,
            color=(0.9, 0.9, 0.7, 1)
        ))

        # Game info display
        game_info_frame = BoxLayout(orientation='vertical', size_hint_y=0.8)
        with game_info_frame.canvas.before:
            Color(0.1, 0.15, 0.2, 0.5)
            game_info_bg = RoundedRectangle(radius=[10,])
        game_info_frame.bind(pos=lambda inst, val: self._update_rect(game_info_frame, val),
                           size=lambda inst, val: self._update_rect(game_info_frame, val))

        self.round_info_label = StyledLabel(
            text="Vòng đấu đang diễn ra", 
            font_size=12,
            color=(0.9, 0.9, 1, 1),
            halign='center'
        )
        self.round_info_label.bind(size=self.round_info_label.setter('text_size'))
        game_info_frame.add_widget(self.round_info_label)

        self.players_remaining_label = StyledLabel(
            text="Người chơi: 0/0", 
            font_size=12,
            color=(0.9, 0.9, 1, 1),
            halign='center'
        )
        self.players_remaining_label.bind(size=self.players_remaining_label.setter('text_size'))
        game_info_frame.add_widget(self.players_remaining_label)
        right_area.add_widget(game_info_frame)

        # Add areas to center game area
        center_game_area.add_widget(left_area)
        center_game_area.add_widget(center_area)
        center_game_area.add_widget(right_area)

        game_area.add_widget(center_game_area)
        self.add_widget(game_area)

        # Bottom action button
        button_container = BoxLayout(size_hint_y=None, height=60, padding=[100, 0])
        self.action_button = Button(
            text="Start New Game Session", 
            size_hint=(1, 0.9),
            pos_hint={'center_y': 0.5},
            background_color=(0.4, 0.6, 0.9, 1),
            font_size=19,
            bold=True,
            border=(0, 0, 0, 5)
        )
        self.action_button.bind(on_press=self.on_press_action_button)
        button_container.add_widget(self.action_button)
        self.add_widget(button_container)
                
        self.update_ui_full()
        
    def log_message(self, msg, permanent=True):
        """Add message to game log and update display"""
        if permanent:
            self.game_log.append(msg)
            if len(self.game_log) > 100: 
                self.game_log = self.game_log[-100:]
                
        if hasattr(self, 'message_label'):
            self.message_label.text = "\n".join(self.game_log)
            if self.message_label.parent and isinstance(self.message_label.parent, ScrollView):
                self.message_label.parent.scroll_y = 0

    def update_ui_full(self):
        """Update all UI elements to match current game state"""
        if not hasattr(self, 'score_label'): 
            return
            
        self.cleanup_leftover_rectangles()

        # Update scores
        score_texts = []
        for p in self.players_session_list:
            token_display = "★" * p.tokens + "☆" * (self.tokens_to_win_session - p.tokens)
            score_texts.append(f"{p.name}: {token_display}")
        self.score_label.text = " | ".join(score_texts)

        # Update turn info
        current_player_name_round = "N/A"
        is_round_active_for_ui = False
        
        if self.current_round_manager and self.current_round_manager.round_active:
            is_round_active_for_ui = True
            current_player_name_round = self.players_session_list[self.current_round_manager.current_player_idx].name

        # Set button text and turn label based on game state
        if self.game_over_session_flag:
            self.turn_label.text = "Game Over!"
            self.action_button.text = "Start New Game Session"
            self.action_button.background_color = (0.4, 0.6, 0.9, 1)
        elif not is_round_active_for_ui:
            self.turn_label.text = "Round Over"
            self.action_button.text = "Start Next Round"
            self.action_button.background_color = (0.5, 0.7, 0.3, 1)
        else:
            self.turn_label.text = f"Turn: {current_player_name_round}"
            self.action_button.text = "Forfeit Round (DEBUG)"
            self.action_button.background_color = (0.8, 0.3, 0.3, 1)

        # Update deck display
        if self.current_round_manager and self.current_round_manager.deck:
            # Update deck info
            self.deck_count_label.text = f"{self.current_round_manager.deck.count()}"
            self.deck_image.source = CARD_BACK_IMAGE if not self.current_round_manager.deck.is_empty() else EMPTY_CARD_IMAGE
            self.deck_image.opacity = 1.0 if not self.current_round_manager.deck.is_empty() else 0.3
            
            # Update game info
            active_players = sum(1 for p in self.players_session_list if not p.is_eliminated)
            total_players = len(self.players_session_list)
            self.players_remaining_label.text = f"Người chơi: {active_players}/{total_players}"
            
            # Update round info
            if self.current_round_manager.round_active:
                current_player = self.players_session_list[self.current_round_manager.current_player_idx].name
                self.round_info_label.text = f"Lượt của: {current_player}"
            else:
                self.round_info_label.text = "Vòng đấu kết thúc"
        else:
            self.deck_count_label.text = "0"
            self.deck_image.source = EMPTY_CARD_IMAGE
            self.deck_image.opacity = 0.3
            self.round_info_label.text = "Không có vòng đấu"
            self.players_remaining_label.text = "Người chơi: 0/0"
            
        # Find last played card to display
        last_played_card = None
        last_played_by = None

        # Prioritize human player's cards
        human_player = self.players_session_list[self.human_player_id]
        if human_player.discard_pile and len(human_player.discard_pile) > 0:
            last_played_card = human_player.discard_pile[-1]
            last_played_by = human_player
        else:
            # If human hasn't played, find most recent opponent card
            for player in self.players_session_list:
                if player.id != self.human_player_id and player.discard_pile and len(player.discard_pile) > 0:
                    last_played_card = player.discard_pile[-1]
                    last_played_by = player
                    break

        # Update last played card display
        self.last_played_card_container.clear_widgets()
        if last_played_card:
            card_button = ImageButton(
                source=last_played_card.image_path,
                card_info_callback=self.display_card_info_popup,
                card_data=last_played_card,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(0.95, 0.95),
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            self.last_played_card_container.add_widget(card_button)
            
            player_name = last_played_by.name if last_played_by else "Unknown"
            self.last_played_title.text = f"Bài của: {player_name}"
        else:
            empty_card = Image(
                source=EMPTY_CARD_IMAGE,
                allow_stretch=True,
                keep_ratio=True,
                size_hint=(0.95, 0.95),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                opacity=0.3
            )
            self.last_played_card_container.add_widget(empty_card)
            self.last_played_title.text = "Chưa có bài đánh ra"

        # Update opponent displays
        self.update_opponents_display()
            
        # Update human player hand display
        self.update_player_hand()

        self.log_message("", permanent=False)

    def update_opponents_display(self):
        """Update opponents area with current player states"""
        self.opponents_grid.clear_widgets()
        self.opponent_widgets_map.clear()
        
        if self.num_players_session <= 1:
            return
            
        # Set columns based on player count
        max_cols = 4
        self.opponents_grid.cols = min(max_cols, max(1, self.num_players_session - 1))
        self.opponents_grid.size_hint_x = None if self.num_players_session - 1 > max_cols else 1

        for p_opponent in self.players_session_list:
            if p_opponent.id == self.human_player_id:
                continue

            # Create opponent container
            opponent_container = BoxLayout(
                orientation='vertical', 
                size_hint_y=None, 
                height=210, 
                width=160, 
                padding=[8, 8, 8, 8]
            )
            
            # Add background with status color
            with opponent_container.canvas.before:
                # Border
                Color(0.3, 0.3, 0.4, 0.9)
                RoundedRectangle(
                    pos=(opponent_container.pos[0]-2, opponent_container.pos[1]-2), 
                    size=(opponent_container.size[0]+4, opponent_container.size[1]+4), 
                    radius=[15,]
                )
                # Background based on status
                if p_opponent.is_eliminated:
                    Color(0.5, 0.1, 0.1, 0.7)  # Red for eliminated
                elif p_opponent.is_protected:
                    Color(0.2, 0.5, 0.2, 0.7)  # Green for protected
                else:
                    Color(0.15, 0.15, 0.25, 0.7)  # Default
                RoundedRectangle(radius=[15,])
            
            opponent_container.bind(pos=self._update_rect, size=self._update_rect)
            
            # Name display with tokens
            name_box = BoxLayout(size_hint_y=0.15)
            # Name box background
            with name_box.canvas.before:
                if p_opponent.is_eliminated:
                    Color(0.4, 0.08, 0.08, 0.9)
                elif p_opponent.is_protected:
                    Color(0.15, 0.4, 0.15, 0.9)
                else:
                    Color(0.1, 0.1, 0.2, 0.9)
                RoundedRectangle(radius=[10, 10, 0, 0])
            name_box.bind(pos=self._update_rect, size=self._update_rect)

            # Player name and status
            token_text = f"{p_opponent.name}"
            status_text = " [E]" if p_opponent.is_eliminated else " [P]" if p_opponent.is_protected else ""

            name_label = StyledLabel(
                text=token_text + status_text, 
                font_size='13sp',
                bold=True,
                color=(1, 1, 0.85, 1) if not p_opponent.is_eliminated else (1, 0.7, 0.7, 1)
            )
            name_box.add_widget(name_label)
            opponent_container.add_widget(name_box)
            
            # Card display
            card_img_src = CARD_BACK_IMAGE
            if p_opponent.is_eliminated:
                card_img_src = ELIMINATED_IMAGE
            elif not p_opponent.hand:
                card_img_src = "transparent"
            
            card_box = BoxLayout(size_hint_y=0.55)
            if card_img_src == "transparent":
                card_image = Widget()
            elif card_img_src == CARD_BACK_IMAGE or card_img_src == ELIMINATED_IMAGE:
                card_image = Image(source=card_img_src, allow_stretch=True, keep_ratio=True)
            else:
                if p_opponent.hand:
                    card_obj = p_opponent.hand[0]
                    card_image = ImageButton(
                        source=card_img_src,
                        card_info_callback=self.display_card_info_popup,
                        card_data=card_obj
                    )
                else:
                    card_image = Widget()
                    
            card_box.add_widget(card_image)
            opponent_container.add_widget(card_box)
            
            # Discard pile
            discard_box = BoxLayout(orientation='vertical', size_hint_y=0.3)
            discard_box.add_widget(StyledLabel(text="Discard", font_size='10sp', size_hint_y=0.3))
            
            if p_opponent.discard_pile:
                discard_card = p_opponent.discard_pile[-1]
                discard_image = ImageButton(
                    source=discard_card.image_path, 
                    allow_stretch=True, 
                    keep_ratio=True, 
                    size_hint_y=0.7,
                    card_info_callback=self.display_card_info_popup,
                    card_data=discard_card
                )
            else:
                discard_image = Image(
                    source=EMPTY_CARD_IMAGE, 
                    allow_stretch=True, 
                    keep_ratio=True, 
                    size_hint_y=0.7,
                    opacity=0.3
                )
            discard_box.add_widget(discard_image)
            opponent_container.add_widget(discard_box)
            
            self.opponents_grid.add_widget(opponent_container)
            self.opponent_widgets_map[p_opponent.id] = opponent_container

    def update_player_hand(self):
        """Update display of human player's hand"""
        human_player = self.players_session_list[self.human_player_id]
        self.player_hand_area.clear_widgets()
        
        if human_player.is_eliminated:
            self.player_hand_area.add_widget(Image(source=ELIMINATED_IMAGE, allow_stretch=True))
            self.player_hand_area.add_widget(StyledLabel(text="Eliminated!", color=(1, 0.5, 0.5, 1), font_size=24))
            return
            
        if not human_player.hand:
            return
            
        is_player_turn_active = (
            self.current_round_manager and
            self.current_round_manager.round_active and
            self.current_round_manager.current_player_idx == self.human_player_id and
            not self.waiting_for_input
        )

        for card_obj in human_player.hand:
            # Create card container
            card_container = BoxLayout(
                orientation='vertical',
                size_hint=(1 / len(human_player.hand) if len(human_player.hand) > 0 else 1, 1),
                padding=[10, 10, 10, 5]
            )

            if is_player_turn_active:
                with card_container.canvas.before:
                    Color(0.2, 0.4, 0.3, 0.4)
                    RoundedRectangle(
                        pos=(card_container.pos[0]+4, card_container.pos[1]-4), 
                        size=card_container.size,
                        radius=[8,]
                    )
                    
            card_frame = BoxLayout(padding=[2, 2, 2, 2])
            with card_frame.canvas.before:
                # Border color based on playability
                if is_player_turn_active:
                    Color(0.9, 0.8, 0.3, 0.8)  # Gold for playable
                else:
                    Color(0.4, 0.4, 0.5, 0.4)  # Gray for inactive
                RoundedRectangle(radius=[5,])
            card_frame.bind(pos=lambda inst, val: self._update_rect(inst, val), 
                        size=lambda inst, val: self._update_rect(inst, val))
                            
            # Card button
            card_button = ImageButton(
                source=card_obj.image_path,
                card_info_callback=self.display_card_info_popup,
                card_data=card_obj,
                size_hint=(0.95, 0.95),
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )
            
            card_button.card_name = card_obj.name
            card_button.bind(on_press=self.on_player_card_selected)
            card_button.disabled = not is_player_turn_active
            card_button.opacity = 1.0 if is_player_turn_active else 0.7
            
            card_frame.add_widget(card_button)
            card_container.add_widget(card_frame)
                            
            # Card info display
            card_info = BoxLayout(size_hint_y=None, height=25, padding=[0, 5, 0, 0])
            with card_info.canvas.before:
                Color(0.15, 0.15, 0.2, 0.8)
                RoundedRectangle(radius=[0, 0, 5, 5])
            card_info.bind(pos=self._update_rect, size=self._update_rect)
            
            info_label = StyledLabel(
                text=f"{card_obj.name} ({card_obj.value})", 
                font_size='13sp',
                color=(1, 0.92, 0.7, 1),
                bold=True
            )
            card_info.add_widget(info_label)
            card_container.add_widget(card_info)
            
            self.player_hand_area.add_widget(card_container)

    def _get_player_widget_by_id(self, player_id):
        """Get player widget by ID"""
        if player_id == self.human_player_id:
            return self.human_player_display_wrapper
        return self.opponent_widgets_map.get(player_id)

    def _update_anim_rect_pos_size(self, instance, value):
        """Update animation rectangle position and size"""
        if hasattr(instance, 'canvas_anim_bg_rect'):
            instance.canvas_anim_bg_rect.pos = instance.pos
            instance.canvas_anim_bg_rect.size = instance.size
            
    # Continue fixing the rest of the methods...
    def on_press_action_button(self, instance):
        """Handle the main action button press"""
        if self.game_over_session_flag:
            self.prompt_player_count()
        elif self.current_round_manager and not self.current_round_manager.round_active:
            self.start_new_round()
        else:
            if self.current_round_manager and self.current_round_manager.round_active and \
                    self.current_round_manager.current_player_idx == self.human_player_id:
                self.log_message(f"{self.players_session_list[self.human_player_id].name} forfeits the round.")
                self.log_message("DEBUG: Forfeit currently complex to reimplement cleanly. Ignored.")
            else:
                self.log_message("Cannot forfeit now.")

    def ui_animate_effect(self, effect_details, duration=1.0, on_complete_callback=None):
        """Animate game effects"""
        self.dismiss_active_popup()
        processed_animation = False
        anim_type = effect_details.get('type')
        
        if anim_type == 'highlight_player':
            player_ids = effect_details.get('player_ids', [])
            color_type = effect_details.get('color_type', 'target')
            actor_id = effect_details.get('actor_id')

            if self.game_over_session_flag and color_type in ['elimination', 'actor_action']:
                if on_complete_callback:
                    on_complete_callback()
                return
        
            if color_type == 'target':
                highlight_color_rgba = (0.5, 0.8, 1, 0.6)
            elif color_type == 'elimination':
                highlight_color_rgba = (1, 0.2, 0.2, 0.7)
            elif color_type == 'protection':
                highlight_color_rgba = (0.2, 1, 0.2, 0.7)
            elif color_type == 'actor_action':
                highlight_color_rgba = (1, 0.8, 0.2, 0.6)
            else:
                highlight_color_rgba = (0.7, 0.7, 0.7, 0.5)

            widgets_to_animate_this_call = []
            if actor_id is not None and effect_details.get('highlight_actor', False):
                actor_widget = self._get_player_widget_by_id(actor_id)
                if actor_widget:
                    widgets_to_animate_this_call.append({'widget': actor_widget, 'color': (1, 0.8, 0.2, 0.5)})

            for p_id in player_ids:
                widget = self._get_player_widget_by_id(p_id)
                if widget:
                    widgets_to_animate_this_call.append({'widget': widget, 'color': highlight_color_rgba})

            for item in widgets_to_animate_this_call:
                widget_to_animate = item['widget']
                color_rgba = item['color']
                processed_animation = True
                
                if widget_to_animate not in self.animated_widget_details:
                    with widget_to_animate.canvas.before:
                        widget_to_animate.canvas_anim_bg_color = Color(*color_rgba)
                        widget_to_animate.canvas_anim_bg_rect = Rectangle(
                            size=widget_to_animate.size,
                            pos=widget_to_animate.pos
                        )
                    widget_to_animate.bind(
                        pos=self._update_anim_rect_pos_size,
                        size=self._update_anim_rect_pos_size
                    )
                    self.animated_widget_details[widget_to_animate] = {
                        'widget': widget_to_animate,
                        'instruction_color': widget_to_animate.canvas_anim_bg_color,
                        'instruction_rect': widget_to_animate.canvas_anim_bg_rect,
                        'original_bound_pos_size': True
                    }
                else:
                    widget_to_animate.canvas_anim_bg_color.rgba = color_rgba
                    widget_to_animate.canvas_anim_bg_rect.size = widget_to_animate.size
                    widget_to_animate.canvas_anim_bg_rect.pos = widget_to_animate.pos

        if processed_animation:
            Clock.schedule_once(lambda dt: self._clear_animations_and_proceed(on_complete_callback), duration)
        elif on_complete_callback:
            on_complete_callback()

    def _clear_animations_and_proceed(self, on_complete_callback):
        """Clear animations and proceed with callback"""
        for widget, details in list(self.animated_widget_details.items()):
            w = details['widget']
            if hasattr(w, 'canvas_anim_bg_color'):
                w.canvas_anim_bg_color.rgba = (0, 0, 0, 0)
        self.animated_widget_details.clear()
        if on_complete_callback:
            on_complete_callback()

    def on_press_action_button(self, instance):
        """Handle the main action button press"""
        if self.game_over_session_flag:
            self.prompt_player_count()
        elif self.current_round_manager and not self.current_round_manager.round_active:
            self.start_new_round()
        else:
            if self.current_round_manager and self.current_round_manager.round_active and \
                    self.current_round_manager.current_player_idx == self.human_player_id:
                self.log_message(f"{self.players_session_list[self.human_player_id].name} forfeits the round.")
                self.log_message("DEBUG: Forfeit currently complex to reimplement cleanly. Ignored.")
            else:
                self.log_message("Cannot forfeit now.")

    def start_new_game_session(self):
        """Start a new game session"""
        self.log_message(f"--- Starting New Game Session with {self.num_players_session} players ---")
        for p in self.players_session_list:
            p.tokens = 0
        self.game_over_session_flag = False
        self.start_new_round()

    def start_new_round(self):
        """Start a new round of play"""
        self.log_message("--- UI: Preparing New Round ---")
        if self.game_over_session_flag:
            self.log_message("Game is over. Cannot start new round until new game session.")
            self.update_ui_full()
            return
            
        game_deck = Deck(self.num_players_session, self.log_message)
        game_deck.burn_one_card(self.num_players_session)
        min_cards_needed = self.num_players_session
        
        if game_deck.count() < min_cards_needed:
            self.log_message(
                f"Error: Not enough cards in deck ({game_deck.count()}) for {self.num_players_session} players. Needs {min_cards_needed}."
            )
            self.game_over_session_flag = True
            self.update_ui_full()
            return

        ui_callbacks = {
            'update_ui_full_callback': self.update_ui_full,
            'set_waiting_flag_callback': self.set_waiting_for_input_flag,
            'get_active_popup_callback': lambda: self.active_popup,
            'dismiss_active_popup_callback': self.dismiss_active_popup,
            'request_target_selection_callback': self.ui_display_target_selection_popup,
            'request_guard_value_popup_callback': self.ui_display_guard_value_popup,
            'request_bishop_value_popup_callback': self.ui_display_bishop_value_popup,
            'request_bishop_redraw_choice_popup_callback': self.ui_display_bishop_redraw_choice_popup,
            'request_cardinal_first_target_popup_callback': self.ui_display_cardinal_first_target_popup,
            'request_cardinal_second_target_popup_callback': self.ui_display_cardinal_second_target_popup,
            'request_cardinal_look_choice_popup_callback': self.ui_display_cardinal_look_choice_popup,
            'award_round_tokens_callback': self.award_round_tokens_and_check_game_over,
            'check_game_over_token_callback': self.check_game_over_on_token_gain,
            'game_over_callback': self.handle_game_over_from_round,
            'animate_effect_callback': self.ui_animate_effect,
        }

        self.current_round_manager = GameRound(
            self.players_session_list,
            game_deck,
            self.human_player_id,
            self.log_message,
            ui_callbacks
        )
        self.current_round_manager.start_round()

    def on_player_card_selected(self, instance):
        """Handle when a player selects a card to play"""
        if not self.current_round_manager or not self.current_round_manager.round_active or \
                self.players_session_list[self.human_player_id].is_cpu or \
                self.current_round_manager.current_player_idx != self.human_player_id or \
                self.waiting_for_input:
            return
            
        card_name_to_play = instance.card_name
        self.current_round_manager.human_plays_card(card_name_to_play)

    def set_waiting_for_input_flag(self, is_waiting):
        """Set waiting for input flag and update UI"""
        self.waiting_for_input = is_waiting
        self.update_ui_full()

    def dismiss_active_popup(self):
        """Dismiss the active popup if any"""
        if self.active_popup:
            self.active_popup.dismiss()
            self.active_popup = None

    def _create_popup_layout_with_scroll(self, title_text):
        """Create a popup layout with a scrollview"""
        popup_layout = BoxLayout(orientation='vertical', spacing="10dp", padding="10dp")
        popup_layout.add_widget(StyledLabel(
            text=title_text,
            font_size=18,
            color=(1, 0.9, 0.7, 1)
        ))
        
        scroll_content = GridLayout(cols=1, spacing="5dp", size_hint_y=None)
        scroll_content.bind(minimum_height=scroll_content.setter('height'))
        
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(scroll_content)
        popup_layout.add_widget(scroll_view)
        
        return popup_layout, scroll_content

    def ui_display_target_selection_popup(self, acting_player_obj, card_played_obj, valid_targets_list,
                                        continuation_callback_in_gameround):
        """Display popup for selecting a target for card effects"""
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        
        popup_layout = BoxLayout(orientation='vertical', spacing="15dp", padding="20dp")
        
        # Add card image and info
        header_box = BoxLayout(size_hint_y=0.3, spacing=10)
        card_image = Image(
            source=card_played_obj.image_path, 
            size_hint_x=0.3, 
            allow_stretch=True, 
            keep_ratio=True
        )
        header_box.add_widget(card_image)
        
        info_box = BoxLayout(orientation='vertical', size_hint_x=0.7)
        info_box.add_widget(StyledLabel(
            text=f"{card_played_obj.name} (Value: {card_played_obj.value})", 
            font_size=18,
            color=(1, 0.9, 0.7, 1)
        ))
        info_box.add_widget(StyledLabel(
            text=card_played_obj.description, 
            font_size=14,
            color=(0.9, 0.9, 1, 1)
        ))
        header_box.add_widget(info_box)
        popup_layout.add_widget(header_box)
        
        # Title
        popup_layout.add_widget(StyledLabel(
            text=f"Choose target for {acting_player_obj.name}:",
            font_size=16,
            color=(1, 1, 0.8, 1),
            size_hint_y=None,
            height=30
        ))
        
        # Target selection
        scroll_view = ScrollView(size_hint=(1, 0.6))
        target_grid = GridLayout(cols=1, spacing="8dp", size_hint_y=None)
        target_grid.bind(minimum_height=target_grid.setter('height'))
        
        for target in valid_targets_list:
            btn_text = f"{target.name}"
            if target == acting_player_obj:
                btn_text += " (Yourself)"
            
            btn = Button(
                text=btn_text, 
                size_hint_y=None, 
                height="50dp",
                background_color=(0.3, 0.5, 0.8, 1) if target != acting_player_obj else (0.5, 0.5, 0.3, 1),
                font_size=16
            )
            btn.target_player_id = target.id
            btn.bind(on_press=lambda instance, ap=acting_player_obj, tid=target.id:
                (self.dismiss_active_popup(), continuation_callback_in_gameround(ap, tid)))
            target_grid.add_widget(btn)
        
        scroll_view.add_widget(target_grid)
        popup_layout.add_widget(scroll_view)
        
        self.active_popup = Popup(
            title=f"{card_played_obj.name} Target Selection", 
            content=popup_layout,
            size_hint=(0.8, 0.8), 
            auto_dismiss=False,
            title_color=(1, 0.9, 0.7, 1),
            title_size='20sp',
            title_align='center',
            background="atlas://data/images/defaulttheme/button_pressed"
        )
        self.active_popup.open()

    def ui_display_guard_value_popup(self, acting_player_obj, target_player_obj, possible_values_list,
                                continuation_callback_in_gameround):
        """Display popup for Guard card value guessing"""
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        
        popup_layout = BoxLayout(orientation='vertical', spacing="15dp", padding="20dp")
        
        popup_layout.add_widget(StyledLabel(
            text=f"Guard: Guess {target_player_obj.name}'s card value (not 1):",
            font_size=18,
            color=(1, 0.9, 0.7, 1),
            size_hint_y=None,
            height=50
        ))
        
        options_grid = GridLayout(cols=4, spacing="10dp")
        
        for val in possible_values_list:
            btn = Button(
                text=str(val),
                size_hint_y=None,
                height="50dp",
                background_color=(0.3, 0.5, 0.8, 1),
                font_size=20,
                bold=True
            )
            btn.bind(on_press=lambda inst, ap=acting_player_obj, tp=target_player_obj:
                (self.dismiss_active_popup(), continuation_callback_in_gameround(ap, tp, int(inst.text))))
            options_grid.add_widget(btn)
        
        popup_layout.add_widget(options_grid)
        
        self.active_popup = Popup(
            title="Guard Value Selection",
            content=popup_layout,
            size_hint=(0.7, 0.5),
            auto_dismiss=False,
            title_color=(1, 0.9, 0.7, 1),
            title_size='20sp',
            title_align='center'
        )
        self.active_popup.open()

    def ui_display_bishop_value_popup(self, acting_player_obj, target_player_obj, possible_values_list,
                                    continuation_callback_in_gameround):
        """Display popup for Bishop card value guessing"""
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        
        popup_layout, options_layout = self._create_popup_layout_with_scroll(
            f"Bishop: Guess {target_player_obj.name}'s card value (not Guard):"
        )
        options_layout.cols = 4
        
        for val in possible_values_list:
            btn = Button(text=str(val), size_hint_y=None, height="40dp")
            btn.bind(on_press=lambda inst_val, ap=acting_player_obj, tp=target_player_obj, v=val:
                (self.dismiss_active_popup(), continuation_callback_in_gameround(ap, tp, v)))
            options_layout.add_widget(btn)
            
        self.active_popup = Popup(
            title="Bishop Guess Value", 
            content=popup_layout,
            size_hint=(0.8, 0.6), 
            auto_dismiss=False
        )
        self.active_popup.open()

    def ui_display_bishop_redraw_choice_popup(self, acting_player_obj, target_player_obj, was_correct_guess,
                                        continuation_callback_in_gameround):
        """Display popup for Bishop redraw choice"""
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        guess_text = "correctly" if was_correct_guess else "incorrectly"
        
        popup_layout.add_widget(StyledLabel(
            text=f"{acting_player_obj.name} played Bishop. Your card ({target_player_obj.hand[0].name}) was guessed {guess_text}.\n"
                f"Discard and draw new card?"
        ))
        
        btn_yes = Button(text="Yes, Discard & Draw", size_hint_y=None, height="40dp")
        btn_yes.bind(on_press=lambda x, tp=target_player_obj, choice=True:
                (self.dismiss_active_popup(), continuation_callback_in_gameround(tp, choice)))
        popup_layout.add_widget(btn_yes)
        
        btn_no = Button(text="No, Keep Card", size_hint_y=None, height="40dp")
        btn_no.bind(on_press=lambda x, tp=target_player_obj, choice=False:
                (self.dismiss_active_popup(), continuation_callback_in_gameround(tp, choice)))
        popup_layout.add_widget(btn_no)
        
        self.active_popup = Popup(
            title=f"Bishop: {target_player_obj.name}'s Choice", 
            content=popup_layout,
            size_hint=(0.7, 0.5), 
            auto_dismiss=False
        )
        self.active_popup.open()

    def ui_display_cardinal_first_target_popup(self, acting_player_obj, card_played_obj, valid_targets_list,
                                            continuation_callback):
        """Display popup for selecting the first target for Cardinal swap"""
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        
        popup_layout, scroll_content = self._create_popup_layout_with_scroll(
            f"{card_played_obj.name}: Choose 1st player for swap:"
        )
        
        for target in valid_targets_list:
            btn = Button(text=target.name, size_hint_y=None, height="40dp")
            btn.bind(on_press=lambda inst, ap=acting_player_obj, t_id=target.id:
                (self.dismiss_active_popup(), continuation_callback(ap, t_id)))
            scroll_content.add_widget(btn)
            
        self.active_popup = Popup(
            title="Cardinal Swap (1/2)", 
            content=popup_layout, 
            size_hint=(0.8, 0.7),
            auto_dismiss=False
        )
        self.active_popup.open()

    def ui_display_cardinal_second_target_popup(self, acting_player_obj, p1_swap_obj, valid_targets_for_p2_list,
                                            continuation_callback):
        """Display popup for selecting the second target for Cardinal swap"""
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        
        popup_layout, scroll_content = self._create_popup_layout_with_scroll(
            f"Cardinal: Choose 2nd player to swap with {p1_swap_obj.name}:"
        )
        
        for target in valid_targets_for_p2_list:
            btn = Button(text=target.name, size_hint_y=None, height="40dp")
            btn.bind(on_press=lambda inst, ap=acting_player_obj, p1s=p1_swap_obj, t2_id=target.id:
                (self.dismiss_active_popup(), continuation_callback(ap, p1s, t2_id)))
            scroll_content.add_widget(btn)
            
        self.active_popup = Popup(
            title="Cardinal Swap (2/2)", 
            content=popup_layout, 
            size_hint=(0.8, 0.7),
            auto_dismiss=False
        )
        self.active_popup.open()

    def ui_display_cardinal_look_choice_popup(self, acting_player_obj, p1_swapped_obj, p2_swapped_obj,
                                        continuation_callback):
        """Display popup for choosing which player's cards to look at after Cardinal swap"""
        self.dismiss_active_popup()
        self.set_waiting_for_input_flag(True)
        
        popup_layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        popup_layout.add_widget(StyledLabel(text="Cardinal: Look at whose new hand?"))

        btn1 = Button(text=f"Look at {p1_swapped_obj.name}'s card", size_hint_y=None, height="40dp")
        btn1.bind(on_press=lambda inst, ap=acting_player_obj, look_id=p1_swapped_obj.id:
                (self.dismiss_active_popup(), continuation_callback(ap, look_id)))
        popup_layout.add_widget(btn1)
        
        btn2 = Button(text=f"Look at {p2_swapped_obj.name}'s card", size_hint_y=None, height="40dp")
        btn2.bind(on_press=lambda inst, ap=acting_player_obj, look_id=p2_swapped_obj.id:
                (self.dismiss_active_popup(), continuation_callback(ap, look_id)))
        popup_layout.add_widget(btn2)
        
        self.active_popup = Popup(
            title="Cardinal Look Choice", 
            content=popup_layout, 
            size_hint=(0.7, 0.5),
            auto_dismiss=False
        )
        self.active_popup.open()

    def display_victory_screen(self, winner):
        """Display victory screen with animations"""
        self.dismiss_active_popup()
        
        victory_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
        
        with victory_layout.canvas.before:
            Color(0.2, 0.2, 0.3, 0.9)  # Dark background
            RoundedRectangle(pos=victory_layout.pos, size=victory_layout.size, radius=[15,])
        victory_layout.bind(pos=self._update_rect, size=self._update_rect)
        
        # Title with winner name
        title_label = StyledLabel(
            text=f"{winner.name} CHIẾN THẮNG!",
            font_size=40, 
            bold=True,
            color=(1, 0.9, 0.3, 1),
            size_hint_y=0.3
        )
        victory_layout.add_widget(title_label)
        
        # Winner image
        image_box = BoxLayout(size_hint_y=0.3)
        winner_image = Image(
            source=CARD_BACK_IMAGE,
            size_hint=(0.5, 0.8),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        image_box.add_widget(winner_image)
        victory_layout.add_widget(image_box)
        
        # Victory info
        info_text = f"Đã giành được {winner.tokens} token tình yêu\nvà chinh phục trái tim của Công chúa!"
        info_label = StyledLabel(
            text=info_text,
            font_size=22,
            color=(0.9, 0.9, 1, 1),
            size_hint_y=0.2,
            halign='center'
        )
        info_label.bind(size=info_label.setter('text_size'))
        victory_layout.add_widget(info_label)
        
        # Play again button
        button_box = BoxLayout(size_hint_y=0.2, padding=[40, 20])
        new_game_button = Button(
            text="Chơi Lại", 
            size_hint=(0.7, 0.6),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            background_color=(0.4, 0.6, 0.9, 1),
            font_size=24,
            bold=True
        )
        new_game_button.bind(on_press=lambda x: (self.dismiss_active_popup(), self.prompt_player_count()))
        button_box.add_widget(new_game_button)
        victory_layout.add_widget(button_box)
        
        # Show the victory popup
        self.active_popup = Popup(
            title="Kết Thúc Trò Chơi",
            content=victory_layout,
            size_hint=(0.8, 0.7),
            title_align='center',
            title_size='24sp',
            title_color=(1, 0.8, 0.4, 1),
            auto_dismiss=False,
            background='atlas://data/images/defaulttheme/button_pressed'
        )
        self.active_popup.open()
            
    def award_round_tokens_and_check_game_over(self, list_of_winner_players):
        """Award tokens to round winners and check for game over"""
        game_ended_this_round = False
        final_winner_of_game = None

        for winner_of_round in list_of_winner_players:
            if winner_of_round is None:
                continue

            self.log_message(f"{winner_of_round.name} gains a token of affection for winning the round!")
            winner_of_round.tokens += 1
            
            if self.check_game_over_on_token_gain(winner_of_round):
                game_ended_this_round = True
                final_winner_of_game = winner_of_round

            # Check for Jester effects (special card)
            if hasattr(self.current_round_manager, '_is_card_in_current_deck') and \
            self.current_round_manager._is_card_in_current_deck('Jester'):
                for p_observer in self.players_session_list:
                    if p_observer.id != winner_of_round.id and hasattr(p_observer, 'jester_on_player_id') and \
                    p_observer.jester_on_player_id == winner_of_round.id:
                        self.log_message(f"{p_observer.name} also gains token (Jester on {winner_of_round.name})!")
                        p_observer.tokens += 1
                        if not game_ended_this_round and self.check_game_over_on_token_gain(p_observer):
                            game_ended_this_round = True
                            final_winner_of_game = p_observer

        if game_ended_this_round and final_winner_of_game:
            self.handle_game_over_from_round(final_winner_of_game)

        self.update_ui_full()

    def check_game_over_on_token_gain(self, player_who_gained_token):
        """Check if game is over when a player gains a token"""
        if self.game_over_session_flag:
            return True
        if player_who_gained_token.tokens >= self.tokens_to_win_session:
            return True
        return False

    def handle_game_over_from_round(self, winner_of_game):
        """Handle the game over state"""
        if self.game_over_session_flag:
            return
            
        self.log_message(f"--- GAME OVER! {winner_of_game.name} wins the game with {winner_of_game.tokens} tokens! ---")
        self.game_over_session_flag = True
        
        if self.current_round_manager:
            self.current_round_manager.round_active = False
            
        self.update_ui_full()
        
        # Display the victory screen
        self.display_victory_screen(winner_of_game)


class LoveLetterApp(App):
    def build(self):
        """Build the main application"""
        os.makedirs(CARD_FOLDER, exist_ok=True)
        self.title = 'Love Letter Board Game'
        
        # Create a screen manager for multiple screens
        sm = ScreenManager(transition=FadeTransition(duration=0.5))
        
        # Create game instance first so it can be referenced
        self.game = LoveLetterGame()
        
        # Add intro screen
        sm.add_widget(IntroScreen(name='intro'))
        
        # Add rules screen with access to game instance
        rules_screen = RulesScreen(name='rules')
        rules_screen.game_instance = self.game  # Give rules screen access to game instance
        sm.add_widget(rules_screen)
        
        # Add main game screen
        game_screen = Screen(name='game')
        game_screen.add_widget(self.game)
        sm.add_widget(game_screen)
        
        # Start with intro screen
        return sm


if __name__ == '__main__':
    # Create necessary directories and default assets if they don't exist
    os.makedirs(CARD_FOLDER, exist_ok=True)
    
    # Create default card back image if it doesn't exist
    if not os.path.exists(CARD_BACK_IMAGE):
        try:
            from PIL import Image as PILImage, ImageDraw
            img = PILImage.new('RGB', (200, 300), color=(25, 40, 100))
            d = ImageDraw.Draw(img)
            d.text((10, 10), "CARD BACK", fill=(255, 255, 0))
            img.save(CARD_BACK_IMAGE)
            print(f"INFO: Created dummy {CARD_BACK_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create dummy card back: {e}")

    # Create eliminated player indicator if it doesn't exist
    if not os.path.exists(ELIMINATED_IMAGE):
        try:
            from PIL import Image as PILImage, ImageDraw
            img = PILImage.new('RGB', (100, 150), color=(100, 20, 20))
            d = ImageDraw.Draw(img)
            d.text((10, 10), "ELIMINATED", fill=(255, 255, 255))
            img.save(ELIMINATED_IMAGE)
            print(f"INFO: Created dummy {ELIMINATED_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create dummy ELIMINATED_IMAGE: {e}")
            
    # Create empty card placeholder if it doesn't exist
    if not os.path.exists(EMPTY_CARD_IMAGE):
        try:
            from PIL import Image as PILImage
            img = PILImage.new('RGBA', (200, 300), color=(0, 0, 0, 0))
            img.save(EMPTY_CARD_IMAGE)
            print(f"INFO: Created empty card image at {EMPTY_CARD_IMAGE}")
        except Exception as e:
            print(f"WARNING: Could not create empty card image: {e}")

    # Create dummy card images if they don't exist
    for card_name_key, card_detail_raw in CARDS_DATA_RAW.items():
        v_name = card_detail_raw['vietnamese_name']
        expected_path_png = os.path.join(CARD_FOLDER, f"{v_name}.png")
        expected_path_jpg = os.path.join(CARD_FOLDER, f"{v_name}.jpg")
        
        if not os.path.exists(expected_path_png) and not os.path.exists(expected_path_jpg):
            try:
                from PIL import Image as PILImage, ImageDraw
                img = PILImage.new('RGB', (200, 300),
                            color=(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
                d = ImageDraw.Draw(img)
                d.text((10, 10), card_name_key, fill=(255, 255, 255))
                d.text((10, 50), f"V:{card_detail_raw['value']}", fill=(255, 255, 255))
                d.text((10, 90), f"({v_name})", fill=(255, 255, 255))
                img.save(expected_path_png)
                print(f"INFO: Created dummy {expected_path_png} for {card_name_key}")
            except Exception as e:
                print(f"WARNING: Could not create dummy image for {card_name_key}: {e}")

    # Launch the application
    LoveLetterApp().run()