import json
import random
import os
import hashlib
import requests  
import urllib3
import threading
import time
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.animation import Animation

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
Window.clearcolor = (0.06, 0.09, 0.16, 1)

# === НАСТРОЙКИ БЕСКОНЕЧНОГО ОБЛАКА SUPABASE ===
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_HvLlvVVI8fz8rR6OSIDsqQ_mgXhml-K"
LOCAL_DB_FILE = "cyber_player_base.json"

# --- Функция красивого форматирования чисел (от k до VG) ---
def format_num(num):
    try:
        num = int(num)
        suffixes = [
            (10**63, "VG"), (10**60, "NnDc"), (10**57, "OcDc"), (10**54, "SpDC"),
            (10**51, "SxDC"), (10**48, "QnDC"), (10**45, "QDC"), (10**42, "TDC"),
            (10**39, "DDC"), (10**36, "UDC"), (10**33, "DC"), (10**30, "1Nn"),
            (10**27, "OC"), (10**24, "SP"), (10**21, "SX"), (10**18, "QN"),
            (10**15, "QD"), (10**12, "T"), (10**9, "B"), (10**6, "M"),
            (10**3, "k")
        ]
        for value, suffix in suffixes:
            if num >= value:
                return f"{num / value:.1f}{suffix}".replace(f".0{suffix}", suffix)
        return str(num)
    except:
        return str(num)

def load_local_db():
    if os.path.exists(LOCAL_DB_FILE):
        try:
            with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"users": {}}

def save_local_db(db):
    try:
        with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except:
        pass

# --- 1. ЭКРАН ВХОДА ---
class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=15)
        layout.add_widget(Label(text="CYBER LOGIN", font_size='32sp', bold=True, color=(0.22, 0.74, 0.97, 1)))
        self.nick_input = TextInput(multiline=False, hint_text="Никнейм...", height='50dp', size_hint_y=None)
        self.pass_input = TextInput(multiline=False, hint_text="Пароль...", password=True, height='50dp', size_hint_y=None)
        layout.add_widget(self.nick_input)
        layout.add_widget(self.pass_input)
        self.info_label = Label(text="Введите данные для входа", font_size='14sp', color=(1, 1, 1, 0.6))
        layout.add_widget(self.info_label)
        btn = Button(text="ВОЙТИ / РЕГИСТРАЦИЯ", size_hint_y=None, height='70dp', background_color=(0.14, 0.77, 0.37, 1), bold=True)
        btn.bind(on_press=self.try_login)
        layout.add_widget(btn)
        layout.add_widget(Label())
        self.add_widget(layout)

    def try_login(self, instance):
        nick = self.nick_input.text.strip()
        pw = self.pass_input.text.strip()
        if len(nick) < 2 or len(pw) < 2:
            self.info_label.text = "Слишком короткие данные!"
            return
        app = App.get_running_app()
        app.nickname = nick
        app.temp_pass = hashlib.sha256(pw.encode()).hexdigest()
        self.info_label.text = "Связь с сервером..."
        threading.Thread(target=app.cloud_login, daemon=True).start()

# --- 2. ГЛАВНЫЙ ЭКРАН ---
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = App.get_running_app()
        self.main_layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        
        self.label_score = Label(text="0", font_size='60sp', bold=True, color=(0.98, 0.8, 0.08, 1))
        self.main_layout.add_widget(self.label_score)

        self.label_info = Label(text="", font_size='14sp', color=(0.22, 0.74, 0.97, 1), halign='center')
        self.main_layout.add_widget(self.label_info)

        self.btn_rebirth = Button(text="", size_hint_y=0.15, background_color=(0.57, 0.12, 0.96, 1), font_size='12sp', bold=True)
        self.btn_rebirth.bind(on_press=lambda x: self.game.do_rebirth())
        self.main_layout.add_widget(self.btn_rebirth)

        self.click_area = BoxLayout(orientation='vertical', size_hint_y=0.35)
        self.anim_label = Label(text="", font_size='24sp', bold=True, color=(0.14, 0.77, 0.37, 1), size_hint_y=0.2, opacity=0)
        self.click_area.add_widget(self.anim_label)
        
        self.btn_click = Button(text="ХАКНУТЬ", size_hint_y=0.8, background_color=(0.23, 0.51, 0.96, 1), font_size='36sp', bold=True)
        self.btn_click.bind(on_press=self.on_click_pressed)
        self.click_area.add_widget(self.btn_click)
        self.main_layout.add_widget(self.click_area)

        btns = BoxLayout(spacing=10, size_hint_y=0.15)
        btn_shop = Button(text="МАГАЗИН", background_color=(0.12, 0.16, 0.23, 1))
        btn_shop.bind(on_press=lambda x: setattr(self.manager, 'current', 'shop'))
        btn_top = Button(text="ТОП-10", background_color=(0.96, 0.62, 0.04, 1))
        btn_top.bind(on_press=lambda x: setattr(self.manager, 'current', 'leaderboard'))
        btns.add_widget(btn_shop)
        btns.add_widget(btn_top)
        self.main_layout.add_widget(btns)

        exit_btns = BoxLayout(spacing=10, size_hint_y=0.1)
        btn_out = Button(text="СМЕНИТЬ АККАУНТ", background_color=(0.7, 0.2, 0.2, 1))
        btn_out.bind(on_press=self.game.logout)
        exit_btns.add_widget(btn_out)
        
        btn_exit_app = Button(text="ВЫЙТИ ИЗ ИГРЫ", background_color=(0.4, 0.4, 0.4, 1))
        btn_exit_app.bind(on_press=self.game.exit_app)
        exit_btns.add_widget(btn_exit_app)
        self.main_layout.add_widget(exit_btns)

        self.add_widget(self.main_layout)
        Clock.schedule_interval(self.update_ui, 0.1)

    def on_click_pressed(self, instance):
        if self.game.current_brawler == "Школьник-Читер":
            current_click = "???"
        elif self.game.current_brawler == "ISKA25k":
            current_click = "Удача"
        else:
            current_click = format_num(int(self.game.income * (1 + self.game.rebirths * 0.5)))
            
        self.anim_label.text = f"+{current_click} 💎"
        self.anim_label.opacity = 1
        anim = Animation(opacity=0, duration=0.4)
        anim.start(self.anim_label)
        self.game.click()

    def update_ui(self, dt):
        next_cost = self.game.get_rebirth_cost()
        self.label_score.text = f"💎 {format_num(self.game.score)}"
        
        if self.game.current_brawler == "Школьник-Читер":
            click_text = "50% шанс: +150💎 / +0💎"
        elif self.game.current_brawler == "ISKA25k":
            click_text = "15% шанс: +200💎 / иначе +50💎"
        else:
            click_text = f"x{format_num(int(self.game.income * (1 + self.game.rebirths * 0.5)))} (Бонус: +{self.game.rebirths * 50}%)"
            
        self.label_info.text = f"Хакер: {self.game.nickname} | Перерождения: {self.game.rebirths}\nГерой: {self.game.current_brawler}\nКлик: {click_text} | Пассив: +{format_num(self.game.passive_income)}/сек"
        self.btn_rebirth.text = f"⚡ СДЕЛАТЬ ПЕРЕРОЖДЕНИЕ ⚡\nЦена: {format_num(next_cost)} 💎 | ...+50% к клику"
        
        if self.game.score >= next_cost:
            self.btn_rebirth.opacity = 1
            self.btn_rebirth.disabled = False
        else:
            self.btn_rebirth.opacity = 0
            self.btn_rebirth.disabled = True

# --- 3. МАГАЗИН ---
class ShopScreen(Screen):
    def on_enter(self):
        self.update_buttons()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = App.get_running_app()
        root = BoxLayout(orientation='vertical', padding=20, spacing=10)
        root.add_widget(Label(text="КИБЕР-МАРКЕТ", font_size='26sp', bold=True, size_hint_y=0.1))
        scroll = ScrollView()
        self.items = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.items.bind(minimum_height=self.items.setter('height'))
        self.shop_buttons = []
        
        self.shop_data = [
            ("case_normal", "ОБЫЧНЫЙ КЕЙС\n(35% - 150💎 | 65% - 0💎)", 0, False),
            ("case_epic", "ЭПИЧЕСКИЙ КЕЙС\n(35% - 400💎 | 20% - Герой Школьник | 45% - 0💎)", 0, False),
            ("case_legendary", "ЛЕГЕНДАРНЫЙ КЕЙС\n(65% - 5k💎 | 25% - 7.5k💎 | 7% - Хакер | 3% - ISKA)", 0, False),
            ("farm", "МАЙНИНГ ФЕРМА (+5/сек)", 0, False),
            ("double", "УДВОИТЕЛЬ КЛИКА (x2)", 0, False),
            ("hero_sl", "ГЕРОЙ: Школьник-Читер", 1, True),
            ("hero_hacker", "ГЕРОЙ: Хакер", 10, True),
            ("hero_iska", "ГЕРОЙ: ISKA25k", 50, True)
        ]
        for key, name, pwr, is_hero in self.shop_data:
            btn = Button(text="", size_hint_y=None, height='90dp', halign='center')
            btn.bind(on_press=lambda x, k=key, n=name, p=pwr, ih=is_hero: self.game.buy(k, n, p, ih))
            self.items.add_widget(btn)
            self.shop_buttons.append((key, btn, name))
        scroll.add_widget(self.items)
        root.add_widget(scroll)
        btn_back = Button(text="НАЗАД", size_hint_y=0.1)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        root.add_widget(btn_back)
        self.add_widget(root)
        self.update_buttons()

    def update_buttons(self):
        for key, btn, name in self.shop_buttons:
            price = self.game.get_price(key)
            btn.text = f"{name}\nЦена: {format_num(price)} 💎"

# --- 4. МИРОВОЙ ТОП-10 ---
class LeaderboardScreen(Screen):
    def on_enter(self):
        self.layout.clear_widgets()
        self.layout.add_widget(Label(text="ЗАГРУЗКА МИРОВОГО ТОПА...", size_hint_y=None, height='50dp'))
        threading.Thread(target=self.load_top, daemon=True).start()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = App.get_running_app()
        root = BoxLayout(orientation='vertical', padding=20)
        root.add_widget(Label(text="🏆 МИРОВОЙ ТОП-10", size_hint_y=0.1, font_size='22sp'))
        self.layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        scroll = ScrollView()
        scroll.add_widget(self.layout)
        root.add_widget(scroll)
        btn = Button(text="НАЗАД", size_hint_y=0.1)
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        root.add_widget(btn)
        self.add_widget(root)

    def load_top(self):
        full_db = self.game.get_cloud_db()
        # Возвращаемся в главный поток, чтобы обновить UI Kivy
        Clock.schedule_once(lambda dt: self.update_top_ui(full_db), 0)

    def update_top_ui(self, full_db):
        self.layout.clear_widgets()
        users_dict = full_db.get("users", {})
        mock_data = []
        for user, saved in users_dict.items():
            if user != "__system_check__" and isinstance(saved, dict):
                score_val = saved.get("save_data", {}).get("score", 0)
                mock_data.append({"name": user, "score": score_val})
        
        mock_data = sorted(mock_data, key=lambda x: x['score'], reverse=True)[:10]
        if not mock_data:
            self.layout.add_widget(Label(text="Топ пуст", size_hint_y=None, height='40dp'))
            return

        for i, user in enumerate(mock_data, 1):
            self.layout.add_widget(Label(
                text=f"{i}. {user['name']} — {format_num(user['score'])} 💎",
                size_hint_y=None, height='40dp', font_size='16sp'
            ))

# --- 5. ЛОГИКА ПРИЛОЖЕНИЯ И ОБЛАКА ---
class CyberClickerApp(App):
    def build(self):
        self.last_click_time = 0
        self.title = "Cyber Clicker"
        self.nickname = "GUEST"
        self.temp_pass = ""
        self.score = 0
        self.income = 1
        self.passive_income = 0
        self.rebirths = 0
        self.current_brawler = "Новичок"
        self.click_count = 0
        self.owned_brawlers = ["Новичок"]
        self.prices = {
            "case_normal": 100, "case_epic": 1000, "case_legendary": 10000,
            "farm": 150, "double": 200, "hero_sl": 5000, "hero_hacker": 15000, "hero_iska": 25000
        }
        self.sm = ScreenManager()
        self.sm.add_widget(RegistrationScreen(name='auth'))
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(ShopScreen(name='shop'))
        self.sm.add_widget(LeaderboardScreen(name='leaderboard'))
        Clock.schedule_interval(self.add_passive, 1.0)
        Clock.schedule_interval(self.save_to_cloud_tick, 30.0)
        return self.sm

    def get_cloud_db(self):
        url = f"https://dyqkybmzhrqksdnhjsec.supabase.co/rest/v1/saves?id=eq.1&select=full_db"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        try:
            res = requests.get(url, headers=headers, timeout=4)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("full_db", {"users": {}})
        except: pass
        return {"users": {}}


    def update_cloud_db(self, full_db):
        url = f"https://dyqkybmzhrqksdnhjsec.supabase.co/rest/v1/saves"
        headers = {
            "apikey": SUPABASE_KEY, 
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json", 
            "Prefer": "resolution=merge-duplicates"
        }
        payload = {"id": 1, "full_db": full_db}
        threading.Thread(target=lambda: requests.post(url, headers=headers, json=payload, timeout=4), daemon=True).start()



    def cloud_login(self):
        if SUPABASE_KEY == "ВСТАВЬ_СЮДА_СВОЙ_ДЛИННЫЙ_ANON_PUBLIC_КЛЮЧ":
            Clock.schedule_once(lambda dt: self.set_auth_info("Укажите SUPABASE_KEY!"), 0)
            return

        full_db = self.get_cloud_db()
        if "users" not in full_db:
            full_db["users"] = {}
        db = full_db["users"]
        
        if self.nickname in db:
            saved_pass = db[self.nickname].get("password")
            if saved_pass == self.temp_pass:
                user_data = db[self.nickname].get("save_data", {})
                self.score = user_data.get("score", 0)
                self.income = user_data.get("income", 1)
                self.passive_income = user_data.get("passive", 0)
                self.rebirths = user_data.get("rebirths", 0)
                self.current_brawler = user_data.get("brawler", "Новичок")
                self.owned_brawlers = user_data.get("owned_brawlers", ["Новичок"])
                self.prices.update(user_data.get("prices", {}))
                Clock.schedule_once(lambda dt: self.enter_game(), 0)
            else:
                Clock.schedule_once(lambda dt: self.set_auth_info("Неверный пароль!"), 0)
        else:
            db[self.nickname] = {
                "password": self.temp_pass,
                "save_data": {
                    "score": self.score, "income": self.income, "passive": self.passive_income,
                    "rebirths": self.rebirths, "brawler": self.current_brawler, "prices": self.prices,
                    "owned_brawlers": self.owned_brawlers
                }
            }
            self.update_cloud_db(full_db)
            save_local_db(full_db)
            Clock.schedule_once(lambda dt: self.enter_game(), 0)

    def set_auth_info(self, text):
        self.sm.get_screen('auth').info_label.text = text

    def enter_game(self):
        self.sm.current = 'main'

    def add_passive(self, dt):
        if self.sm.current != 'auth':
            self.score += self.passive_income
            self.local_save_only()

    def local_save_only(self):
        if self.nickname != "GUEST" and self.sm.current != 'auth':
            local_db = load_local_db()
            if "users" not in local_db: local_db["users"] = {}
            local_db["users"][self.nickname] = {
                "password": self.temp_pass,
                "save_data": {
                    "score": self.score, "income": self.income, "passive": self.passive_income,
                    "rebirths": self.rebirths, "brawler": self.current_brawler, "prices": self.prices,
                    "owned_brawlers": self.owned_brawlers
                }
            }
            save_local_db(local_db)

    def save_to_cloud_tick(self, dt):
        if self.nickname != "GUEST" and self.sm.current != 'auth':
            full_db = load_local_db()
            if "users" not in full_db: full_db["users"] = {}
            full_db["users"][self.nickname] = {
                "password": self.temp_pass,
                "save_data": {
                    "score": self.score, "income": self.income, "passive": self.passive_income,
                    "rebirths": self.rebirths, "brawler": self.current_brawler, "prices": self.prices,
                    "owned_brawlers": self.owned_brawlers
                }
            }
            self.update_cloud_db(full_db)

    def force_cloud_save(self):
        self.save_to_cloud_tick(0)

    def get_rebirth_cost(self):
        # Если перерождений 0, то цена для 1-го перерождения
        if self.rebirths == 0:
            return 1000000  # Твоя цена для 1-го перерождения (например, 5k)
        # Если перерождение уже 1, то цена для 2-го
        elif self.rebirths == 1:
            return 5000000  # Твоя цена для 2-го перерождения (например, 25k)
        # Если перерождений 2, то цена для 3-го
        elif self.rebirths == 2:
            return 25000000  # Твоя цена для 3-го перерождения (например, 100k)
        # Для всех остальных (4-го, 5-го и далее) цена будет расти автоматически
        else:
            return (self.rebirths + 1) * 50000000


    def do_rebirth(self):
        cost = self.get_rebirth_cost()
        if self.score >= cost:
            self.score = 0
            self.income = 1
            self.passive_income = 0
            self.current_brawler = "Новичок"
            self.owned_brawlers = ["Новичок"]
            self.rebirths += 1
            
            # ФИЧА №1: Полный сброс цен в магазине до начальных при перерождении
            self.prices = {
                "case_normal": 100, "case_epic": 1000, "case_legendary": 10000,
                "farm": 150, "double": 200, "hero_sl": 5000, "hero_hacker": 15000, "hero_iska": 25000       
            }
            
            self.local_save_only()
            self.force_cloud_save()

    def buy(self, key, name, power, is_hero):
        # ФИЧА №2: Блокировка покупки персонажей по перерождениям
        if key == "hero_hacker" and self.rebirths < 2:
            self.show_popup("БЛОКИРОВКА!", "Для покупки Хакера нужно минимум 2 перерождения!")
            return
        if key == "hero_iska" and self.rebirths < 3:
            self.show_popup("БЛОКИРОВКА!", "Для покупки ISKA25k нужно минимум 3 перерождения!")
            return

        price = self.get_price(key)
        if self.score >= price:
            self.score -= price
            
            if is_hero:
                brawler_name = name.replace("ГЕРОЙ: ", "")
                self.current_brawler = brawler_name
                if brawler_name not in self.owned_brawlers: 
                    self.owned_brawlers.append(brawler_name)
                self.income += power
            elif key == "farm":
                self.passive_income += 5
                self.prices[key] = int(price * 1.5)
            elif key == "double":
                self.income *= 2
                self.prices[key] = int(price * 2)
            elif key == "case_normal":
                if random.random() < 0.35:
                    self.score += 150
                    self.show_popup("ОБЫЧНЫЙ КЕЙС", "Вы выиграли 150 💎!")
                else: self.show_popup("ОБЫЧНЫЙ КЕЙС", "Пусто...")
            elif key == "case_epic":
                rand = random.random()
                if rand < 0.35:
                    self.score += 400
                    self.show_popup("ЭПИЧЕСКИЙ КЕЙС", "Вы выиграли 400 💎!")
                elif rand < 0.55:
                    if "Школьник-Читер" in self.owned_brawlers:
                        self.score += 5000
                        self.show_popup("ДУБЛИКАТ!", "Школьник-Читер уже есть! Возвращено 5k 💎")
                    else:
                        self.owned_brawlers.append("Школьник-Читер")
                        self.current_brawler = "Школьник-Читер"
                        self.income += 1
                        self.show_popup("НОВЫЙ БОЕЦ!", "Вы выбили бойца: Школьник-Читер!")
                else: self.show_popup("ЭПИЧЕСКИЙ КЕЙС", "Пусто...")
            elif key == "case_legendary":
                rand = random.random()
                if rand < 0.65:
                    self.score += 5000
                    self.show_popup("ЛЕГЕНДАРНЫЙ КЕЙС", "Вы выиграли 5,000 💎!")
                elif rand < 0.90:
                    self.score += 7500
                    self.show_popup("ЛЕГЕНДАРНЫЙ КЕЙС", "Вы выиграли 7,500 💎!")
                elif rand < 0.97:
                    if "Хакер" in self.owned_brawlers:
                        self.score += 15000
                        self.show_popup("ДУБЛИКАТ!", "Хакер уже есть! Возвращено 15k 💎")
                    else:
                        self.owned_brawlers.append("Хакер")
                        self.current_brawler = "Хакер"
                        self.income += 10
                        self.show_popup("МИФИЧЕСКИЙ ХАКЕР!", "Вы выбили бойца: Хакер!")
                else:
                    if "ISKA25k" in self.owned_brawlers:
                        self.score += 25000
                        self.show_popup("ДУБЛИКАТ!", "ISKA25k уже есть! Возвращено 25k 💎")
                    else:
                        self.owned_brawlers.append("ISKA25k")
                        self.current_brawler = "ISKA25k"
                        self.income += 50
                        self.show_popup("ЛЕГЕНДА!", "Вы выбили самого крутого бойца: ISKA25k!")
            
            self.local_save_only()
            self.force_cloud_save()
            if self.sm.has_screen('shop'): self.sm.get_screen('shop').update_buttons()

    def click(self):
        current_time = time.time()
        # Проверяем интервал: если прошло меньше 0.1 секунды — это автокликер!
        if current_time - self.last_click_time < 0.10:
            # Меняем текст на главной кнопке через ScreenManager
            if self.sm.has_screen('main'):
                self.sm.get_screen('main').btn_click.text = "ЗАЩИТА! 🤖"
                # Возвращаем нормальный текст кнопки через 0.5 секунд
                Clock.schedule_once(lambda dt: setattr(self.sm.get_screen('main').btn_click, 'text', "ХАКНУТЬ"), 0.5)
            return # Выходим из функции, алмазы НЕ начисляются!
            
        # Если проверка пройдена, запоминаем время текущего успешного клика
        self.last_click_time = current_time

        # --- Твоя обычная логика начисления алмазов ---
        if self.current_brawler == "Школьник-Читер":
            gained = 150 if random.random() < 0.40 else 0
            self.score += gained
        elif self.current_brawler == "ISKA25k":
            gained = 200 if random.random() < 0.15 else 50
            self.score += gained
        else:
            self.score += int(self.income * (1 + self.rebirths * 0.5))
        
        self.local_save_only()
        self.click_count += 1
        if self.click_count >= 10:
            self.click_count = 0
            self.save_to_cloud_tick(0)


    def get_price(self, key):
        return self.prices.get(key, 0)

    def show_popup(self, title, text):
        box = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Создаем текст с включенным автоматическим переносом строк
        lbl = Label(
            text=text, 
            halign='center',      # Выравнивание текста строго по центру
            valign='middle',      # Выравнивание по вертикали
            font_size='16sp'      # Оптимальный размер шрифта для мобилок
        )
        # Этот хак заставляет Kivy переносить текст по ширине окна Popup
        lbl.bind(size=lambda s, w: setattr(lbl, 'text_size', (w[0] - 20, None)))
        
        box.add_widget(lbl)
        
        # Увеличиваем Popup, чтобы длинный текст точно поместился (размер 0.85 на 0.45)
        popup = Popup(title=title, content=box, size_hint=(0.85, 0.45))
        
        btn = Button(text="ОК", size_hint_y=0.3, background_color=(0.23, 0.51, 0.96, 1), bold=True)
        btn.bind(on_press=popup.dismiss)
        box.add_widget(btn)
        
        popup.open()

    def logout(self, *args):
        self.nickname = "GUEST"
        self.sm.current = 'auth'

    def exit_app(self, instance):
        App.get_running_app().stop()

if __name__ == '__main__':
    CyberClickerApp().run()
