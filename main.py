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
        
        # --- ФИЧА: Горизонтальный ряд для алмаза и счёта ---
        # --- МОБИЛЬНЫЙ ЦЕНТР ДЛЯ АЛМАЗА И СЧЁТА ---
        score_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=5)
        
        # Левая распорка (сжимает к центру)
        score_layout.add_widget(Label(size_hint_x=0.3))
        
        from kivy.uix.image import Image
        # Твой компактный алмазик
        diamond_icon = Image(source='diamond.png', size_hint_x=0.15, allow_stretch=True)
        score_layout.add_widget(diamond_icon)
        
        # Текст счёта (убираем text_size, чтобы цифры не прыгали на новую строку!)
        self.label_score = Label(text="0", font_size='40sp', bold=True, color=(0.98, 0.8, 0.08, 1), size_hint_x=0.25, halign='left', valign='middle')
        score_layout.add_widget(self.label_score)
        
        # Правая распорка (сжимает к центру)
        score_layout.add_widget(Label(size_hint_x=0.3))
        
        self.main_layout.add_widget(score_layout)
        # ------------------------------------------


                # === ВОЗВРАЩАЕМ КРУТУЮ ШКАЛУ ИЗ ПАЛОЧЕК ===

        # ------------------------------------------

        # --------------------------------------------------

        self.label_info = Label(text="", font_size='14sp', color=(0.22, 0.74, 0.97, 1), halign='center')
        self.main_layout.add_widget(self.label_info)

        self.btn_rebirth = Button(text="", size_hint_y=0.15, background_color=(0.57, 0.12, 0.96, 1), font_size='12sp', bold=True)
        self.btn_rebirth.bind(on_press=lambda x: self.game.do_rebirth())
        self.main_layout.add_widget(self.btn_rebirth)

        self.click_area = BoxLayout(orientation='vertical', size_hint_y=0.35)
        self.anim_label = Label(text="", font_size='24sp', bold=True, color=(0.14, 0.77, 0.37, 1), size_hint_y=0.2, opacity=0)
        self.click_area.add_widget(self.anim_label)
        
        # У главной кнопки убран font_name, чтобы буквы на ПК не ломались
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
            
        # Убираем смайлик из вылетающего текста клика
        self.anim_label.text = f"+{current_click}"
        self.anim_label.opacity = 1
        anim = Animation(opacity=0, duration=0.4)
        anim.start(self.anim_label)
        self.game.click()

    def update_ui(self, dt):
        next_cost = self.game.get_rebirth_cost()
        # Теперь тут только число, без текстового значка алмаза
        self.label_score.text = f"{format_num(self.game.score)}"
        
        if self.game.current_brawler == "Школьник-Читер":
            click_text = "50% шанс: +150 / +0"
        elif self.game.current_brawler == "ISKA25k":
            click_text = "15% шанс: +10000 / иначе +5000"
        else:
            click_text = f"x{format_num(int(self.game.income * (1 + self.game.rebirths * 0.5)))} (Бонус: +{self.game.rebirths * 50}%)"
            
        # Из логов убраны смайлики батарейки, чтобы телефон не вис на старте
        # === ВОЗВРАЩАЕМ КРУТУЮ ШКАЛУ ИЗ ПАЛОЧЕК ===
        # Высчитываем количество закрашенных палочек (из 10 штук)
        bars = int((self.game.energy / self.game.max_energy) * 10)
        energy_bar = "[" + "|" * bars + " " * (10 - bars) + "]"
        
        self.label_info.text = f"Хакер: {self.game.nickname} | Перерождения: {self.game.rebirths}\nГерой: {self.game.current_brawler}\nКлик: {click_text} | Пассив: +{format_num(self.game.passive_income)}/сек\nЭНЕРГИЯ: {energy_bar} {int(self.game.energy)} / {self.game.max_energy}"
        # ==========================================

        self.btn_rebirth.text = f"⚡ СДЕЛАТЬ ПЕРЕРОЖДЕНИЕ ⚡\nЦена: {format_num(next_cost)} | ...+50% к клику"
        
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
            ("case_legendary", "ЛЕГЕНДАРНЫЙ КЕЙС\n(65% - 5k💎 | 25% - 7.5k💎 | 7% - Хакер | 3% - ISKA25k)", 0, False),
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
            btn.text = f"{name}\nЦена: {format_num(price)} "

# --- 4. МИРОВОЙ ТОП-10 ---
class LeaderboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = App.get_running_app()
        
        # Главный контейнер на весь экран
        root = BoxLayout(orientation='vertical', padding=30, spacing=20)
        
        # Простой, чёткий заголовок
        root.add_widget(Label(text="🏆 МИРОВОЙ ТОП-10 🏆", size_hint_y=0.15, font_size='24sp', bold=True))
        
        # ТОТ САМЫЙ МОНОЛИТНЫЙ БЛОК. Больше никаких BoxLayout и ScrollView внутри!
        # Текст будет выводиться единым полотном, Kivy его никак не сожмёт в ноль.
        self.top_text_label = Label(
            text="ЗАГРУЗКА МИРОВОГО ТОПА...", 
            font_size='18sp', 
            size_hint_y=0.7, 
            halign='center', 
            valign='middle'
        )

        self.top_text_label.text_size = (800, None)
        root.add_widget(self.top_text_label)
        
        # Кнопка возврата назад
        btn = Button(text="НАЗАД В ИГРУ", size_hint_y=0.15, background_color=(0.12, 0.16, 0.23, 1), bold=True)
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        root.add_widget(btn)
        
        self.add_widget(root)

    def on_enter(self):
        # Принудительно сохраняем прогресс перед показом топа
        self.game.force_cloud_save()
        self.top_text_label.text = "ЗАГРУЗКА МИРОВОГО ТОПА..."
        threading.Thread(target=self.load_top, daemon=True).start()

    def load_top(self):
        from kivy.network.urlrequest import UrlRequest
        base_url = "https://" + "dyqkybmzhrqksdnhjsec" + ".supabase.co"
        url = base_url + "/rest/v1/saves?select=id,full_db"
        headers = {
            "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Range": "0-9"
        }
        UrlRequest(url, on_success=self.on_top_success, on_failure=self.on_top_error, on_error=self.on_top_error, req_headers=headers)

    def on_top_success(self, req, result):
        Clock.schedule_once(lambda dt: self.update_top_ui(result), 0)

    def on_top_error(self, req, result):
        Clock.schedule_once(lambda dt: self.update_top_ui([]), 0)

    def update_top_ui(self, all_rows):
        import json
        mock_data = []

        if isinstance(all_rows, dict):
            all_rows = [all_rows]

        if isinstance(all_rows, list) and all_rows:
            for row in all_rows:
                if not isinstance(row, dict): continue
                user_name = row.get("id")
                full_db = row.get("full_db", {})

                # Десериализуем строку из Supabase в словарь Python
                if isinstance(full_db, str) and full_db.strip():
                    try: 
                        full_db = json.loads(full_db)
                    except: 
                        full_db = {}

                if user_name:
                    score_val = 0
                    if isinstance(full_db, dict) and full_db:
                        s_data = full_db.get("save_data", {})
                        if isinstance(s_data, dict):
                            score_val = s_data.get("score", 0)
                        else:
                            score_val = full_db.get("score", 0)

                    # Копируем строго то число, которое лежит в базе данных сервера!
                    mock_data.append({"name": str(user_name), "score": int(score_val)})

        # Если в базе реально шаром покати, пишем честный текст без фейковых начислений
        if not mock_data:
            self.top_text_label.text = "В таблице лидеров пока пусто...\n\nНакликай 10 алмазов!"
            return

        # Сортируем топ строго по честным рекордам из облака
        mock_data = sorted(mock_data, key=lambda x: x['score'], reverse=True)[:10]

        lines = []
        for i, user in enumerate(mock_data, 1):
            lines.append(f"{i}. {user['name']}  ---  {format_num(user['score'])} 💎")

        self.top_text_label.text = "\n".join(lines)

# --- 5. ЛОГИКА ПРИЛОЖЕНИЯ И ОБЛАКА ---
class CyberClickerApp(App):
    def build(self):
        self.energy = 100
        self.max_energy = 100
        self.energy_level = 1
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
            "farm": 150, "double": 200, "hero_sl": 25000, "hero_hacker": 50000, "hero_iska": 100000
        }
        self.sm = ScreenManager()
        self.sm.add_widget(RegistrationScreen(name='auth'))
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(ShopScreen(name='shop'))
        self.sm.add_widget(LeaderboardScreen(name='leaderboard'))
        Clock.schedule_interval(self.add_passive, 1.0)
        Clock.schedule_interval(self.save_to_cloud_tick, 30.0)
        return self.sm

        # Автоматический вход при запуске
        import os
        if os.path.exists("autoreg.txt"):
            try:
                with open("autoreg.txt", "r") as f:
                    saved_nick, saved_pass = f.read().split(":")
                self.nickname = saved_nick
                self.temp_pass = saved_pass
                # Запускаем фоновую авторизацию в Supabase
                threading.Thread(target=self.cloud_login, daemon=True).start()
            except: pass



    def set_auth_info(self, text):
        self.sm.get_screen('auth').info_label.text = text

    def enter_game(self):
        self.sm.current = 'main'

    def add_passive(self, dt):
        if self.energy < self.max_energy:
            self.energy += 1
        if self.energy > self.max_energy:
            self.energy = self.max_energy
        if self.sm.current != 'auth':
            self.score += self.passive_income
            self.local_save_only()

    def local_save_only(self):
        # Локальный бэкап на устройстве
        try:
            import json
            current_user_data = {
                "password": self.temp_pass,
                "save_data": {
                    "score": self.score, "income": self.income, "passive": self.passive_income,
                    "rebirths": self.rebirths, "brawler": self.current_brawler, "prices": self.prices,
                    "owned_brawlers": self.owned_brawlers
                }
            }
            with open("local_save.json", "w", encoding="utf-8") as f:
                json.dump(current_user_data, f, ensure_ascii=False, indent=4)
        except: pass

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

    def get_cloud_db(self):
        # Мобильный запрос через UrlRequest (телефон его не заблокирует)
        from kivy.network.urlrequest import UrlRequest
        base_url = "https://" + "dyqkybmzhrqksdnhjsec" + ".supabase.co"
        url = base_url + f"/rest/v1/saves?id=eq.{str(self.nickname)}&select=full_db"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        
        # Запрос улетает в фоне, а ответ обработает функция on_db_success
        UrlRequest(url, on_success=self.on_db_success, on_failure=self.on_db_error, on_error=self.on_db_error, req_headers=headers)

    def on_db_success(self, req, result):
        import json
        full_db = {}
        if isinstance(result, list) and len(result) > 0:
            full_db = result[0].get("full_db", {})
            if isinstance(full_db, str) and full_db.strip():
                try: full_db = json.loads(full_db)
                except: pass
        self.process_mobile_login(full_db)

    def on_db_error(self, req, result):
        self.process_mobile_login({})

    def cloud_login(self):
        if SUPABASE_KEY == "ВСТАВЬ_СЮДА_СВОЙ_ДЛИННЫЙ_ANON_PUBLIC_КЛЮЧ":
            Clock.schedule_once(lambda dt: self.set_auth_info("Укажите SUPABASE_KEY!"), 0)
            return
        # На телефоне сначала просто пинаем get_cloud_db, логика продолжится в process_mobile_login
        self.get_cloud_db()

    def process_mobile_login(self, user_cloud_data):
        import json
        if user_cloud_data:
            saved_pass = user_cloud_data.get("password")
            save_data = user_cloud_data.get("save_data", {})
            if not saved_pass and "password" in user_cloud_data:
                saved_pass = user_cloud_data["password"]

            if saved_pass == self.temp_pass or not saved_pass:
                if isinstance(save_data, dict):
                    self.score = int(save_data.get("score", 0))
                    self.income = int(save_data.get("income", 1))
                    self.passive_income = int(save_data.get("passive", 0))
                    self.rebirths = int(save_data.get("rebirths", 0))
                    self.current_brawler = str(save_data.get("brawler", "Новичок"))
                    self.owned_brawlers = save_data.get("owned_brawlers", ["Новичок"])
                    if "prices" in save_data:
                        self.prices.update(save_data.get("prices", {}))
                
                if self.sm.has_screen('main'):
                    self.sm.get_screen('main').label_score.text = f"{self.score}"
                try:
                    with open("autoreg.txt", "w") as f:
                        f.write(f"{self.nickname}:{self.temp_pass}")
                except: pass
                Clock.schedule_once(lambda dt: self.enter_game(), 0)
                return
            else:
                Clock.schedule_once(lambda dt: self.set_auth_info("Неверный пароль!"), 0)
                return

        new_user_profile = {
            "password": str(self.temp_pass),
            "save_data": {
                "score": int(self.score), "income": int(self.income), "passive": int(self.passive_income),
                "rebirths": int(self.rebirths), "brawler": str(self.current_brawler), "prices": self.prices,
                "owned_brawlers": self.owned_brawlers
            }
        }
        self.update_cloud_db(new_user_profile)
        try:
            with open("autoreg.txt", "w") as f:
                f.write(f"{self.nickname}:{self.temp_pass}")
        except: pass
        Clock.schedule_once(lambda dt: self.enter_game(), 0)

    def update_cloud_db(self, full_db):
        from kivy.network.urlrequest import UrlRequest
        import json
        base_url = "https://" + "dyqkybmzhrqksdnhjsec" + ".supabase.co"
        url = base_url + "/rest/v1/saves"
        headers = {
            "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"
        }
        payload = json.dumps({"id": str(self.nickname), "full_db": full_db})
        # Безопасная мобильная POST-отправка в фоне
        UrlRequest(url, req_body=payload, req_headers=headers, method='POST')


    def force_cloud_save(self):
        # Жестко собираем структуру прямо перед отправкой
        import json
        user_data = {
            "password": str(self.temp_pass),
            "save_data": {
                "score": int(self.score),
                "income": int(self.income),
                "passive": int(self.passive_income),
                "rebirths": int(self.rebirths),
                "brawler": str(self.current_brawler),
                "prices": self.prices,
                "owned_brawlers": self.owned_brawlers
            }
        }
        # Пуляем напрямую в update
        self.update_cloud_db(user_data)

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

    def cloud_login(self):
        if SUPABASE_KEY == "ВСТАВЬ_СЮДА_СВОЙ_ДЛИННЫЙ_ANON_PUBLIC_КЛЮЧ":
            Clock.schedule_once(lambda dt: self.set_auth_info("Укажите SUPABASE_KEY!"), 0)
            return

        # Скачиваем и парсим чистый словарь full_db
        user_cloud_data = self.get_cloud_db()
        
        if user_cloud_data:
            saved_pass = user_cloud_data.get("password")
            save_data = user_cloud_data.get("save_data", {})
            
            if not saved_pass and "password" in user_cloud_data:
                saved_pass = user_cloud_data["password"]

            if saved_pass == self.temp_pass or not saved_pass:
                # НАМЕРТВО ЗАЛИВАЕМ АЛМАЗЫ В ОПЕРАТИВНУЮ ПАМЯТЬ
                if isinstance(save_data, dict):
                    self.score = int(save_data.get("score", 0))
                    self.income = int(save_data.get("income", 1))
                    self.passive_income = int(save_data.get("passive", 0))
                    self.rebirths = int(save_data.get("rebirths", 0))
                    self.current_brawler = str(save_data.get("brawler", "Новичок"))
                    self.owned_brawlers = save_data.get("owned_brawlers", ["Новичок"])
                    if "prices" in save_data:
                        self.prices.update(save_data.get("prices", {}))
                
                # ЖЁСТКИЙ ХАК: Впечатываем баланс в текст главного экрана ДО перехода, чтобы Kivy не обнулился!
                if self.sm.has_screen('main'):
                    self.sm.get_screen('main').label_score.text = f"{self.score}"
                
                # Безопасно пишем файл автовхода
                try:
                    with open("autoreg.txt", "w") as f:
                        f.write(f"{self.nickname}:{self.temp_pass}")
                except: pass
                    
                Clock.schedule_once(lambda dt: self.enter_game(), 0)
                return
            else:
                Clock.schedule_once(lambda dt: self.set_auth_info("Неверный пароль!"), 0)
                return

        # Если игрока нет на сервере — создаем ему чистую структуру jsonb
        new_user_profile = {
            "password": str(self.temp_pass),
            "save_data": {
                "score": int(self.score), "income": int(self.income), "passive": int(self.passive_income),
                "rebirths": int(self.rebirths), "brawler": str(self.current_brawler), "prices": self.prices,
                "owned_brawlers": self.owned_brawlers
            }
        }
        self.update_cloud_db(new_user_profile)
        
        try:
            with open("autoreg.txt", "w") as f:
                f.write(f"{self.nickname}:{self.temp_pass}")
        except: pass
            
        Clock.schedule_once(lambda dt: self.enter_game(), 0)
        
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
                        self.show_popup("ДУБЛИКАТ!", "Школьник-Читер уже есть! Возвращено 25k 💎")
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
                        self.show_popup("ДУБЛИКАТ!", "Хакер уже есть! Возвращено 50k 💎")
                    else:
                        self.owned_brawlers.append("Хакер")
                        self.current_brawler = "Хакер"
                        self.income += 10
                        self.show_popup("МИФИЧЕСКИЙ ХАКЕР!", "Вы выбили бойца: Хакер!")
                else:
                    if "ISKA25k" in self.owned_brawlers:
                        self.score += 25000
                        self.show_popup("ДУБЛИКАТ!", "ISKA25k уже есть! Возвращено 100k 💎")
                    else:
                        self.owned_brawlers.append("ISKA25k")
                        self.current_brawler = "ISKA25k"
                        self.income += 50
                        self.show_popup("ЛЕГЕНДА!", "Вы выбили самого крутого бойца: ISKA25k!")
            
            self.local_save_only()
            self.force_cloud_save()
            if self.sm.has_screen('shop'): self.sm.get_screen('shop').update_buttons()

    def click(self):
        # (Тут твоя проверка энергии)
        if self.energy < 1:
            if self.sm.has_screen('main'):
                self.sm.get_screen('main').btn_click.text = "НЕТ ЭНЕРГИИ!"
                Clock.schedule_once(lambda dt: setattr(self.sm.get_screen('main').btn_click, 'text', "ХАКНУТЬ"), 0.5)
            return

        self.energy -= 1

        # ИСПРАВЛЕННАЯ ЛОГИКА КЛИКА С УЧЕТОМ ПЕРЕРОЖДЕНИЙ ДЛЯ ВСЕХ ГЕРОЕВ
        bonus_multiplier = 1 + (self.rebirths * 0.5) # Твои +50% за каждое перерождение

        if self.current_brawler == "Школьник-Читер":
            gained = int(150 * bonus_multiplier) if random.random() < 0.40 else 0
            self.score += gained
        elif self.current_brawler == "ISKA25k":
            gained = int(10000 * bonus_multiplier) if random.random() < 0.15 else int(5000 * bonus_multiplier)
            self.score += gained
        else:
            # Обычный клик теперь ЖЕЛЕЗНО умножается на бонус перерождений!
            self.score += int(self.income * bonus_multiplier)
        
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
