import json
import random
import os
import threading
import urllib3
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

# ════════════════════════════════════════════════
#  ПУТЬ К ФАЙЛУ СОХРАНЕНИЯ — СТРОГО ОДИН РАЗ!
#  БАГ-ФИКС: раньше этот путь перезатирался строкой
#  "cyber_player_base.json" в блоке настроек Supabase.
# ════════════════════════════════════════════════
try:
    from kivy.utils import platform
    if platform == "android":
        # На андроиде используем user_data_dir — он доступен только после запуска App,
        # поэтому оставляем заглушку, а реальный путь выставляется в CyberClickerApp.build()
        _data_dir = None
    else:
        _data_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
except Exception:
    _data_dir = os.getcwd()

# Глобальная переменная. На Android будет перезаписана в build() через App.user_data_dir
LOCAL_DB_FILE = os.path.join(_data_dir, "cyber_player_base.json") if _data_dir else "cyber_player_base.json"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
Window.clearcolor = (0.06, 0.09, 0.16, 1)

# ════════════════════════════════════════════════
#  НАСТРОЙКИ SUPABASE
#  БАГ-ФИКС: убрана строка LOCAL_DB_FILE = "cyber_player_base.json",
#  которая раньше стояла здесь и убивала правильный путь выше.
# ════════════════════════════════════════════════
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR5cWt5Ym16aHJxa3Nkbmhqc2VjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk2ODUzMzEsImV4cCI6MjA5NTI2MTMzMX0.nNtSWZM4d21x698Cw2V2y9l8zAIq8xqRmliWeNuE5J0"

# Используем только UrlRequest вместо supabase-py
supabase_client = True  # Флаг что облако включено


# ════════════════════════════════════════════════
#  ФОРМАТИРОВАНИЕ ЧИСЕЛ
# ════════════════════════════════════════════════
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
    except Exception:
        return str(num)


# ════════════════════════════════════════════════
#  ЗАГРУЗКА / СОХРАНЕНИЕ ЛОКАЛЬНОЙ БД
#  БАГ-ФИКС: убраны локальные переопределения LOCAL_DB_FILE
#  внутри этих функций — теперь они используют глобальный путь.
# ════════════════════════════════════════════════
def load_local_db():
    if os.path.exists(LOCAL_DB_FILE):
        try:
            with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and "users" in data:
                    print("[ХАКЕР-БАЗА ЗАГРУЖЕНА]: Старые алмазы успешно подняты из файла!")
                    return data
        except Exception as e:
            print(f"[ОШИБКА ЧТЕНИЯ]: {e}")
    return {"users": {}}


def save_local_db(db):
    # БАГ-ФИКС: убран «щит от нулей» — он блокировал честное сохранение
    # при первом запуске игры (когда очков ещё действительно 0).
    # Защита не нужна, если click() и _save() правильно берут app.score.
    try:
        with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        print("[БАЗА СБЕРЕЖЕНА]: Алмазы намертво записаны на диск!")
    except Exception as e:
        print(f"[ОШИБКА ЗАПИСИ]: {e}")


# ════════════════════════════════════════════════
#  ЭКРАН ВХОДА
#  БАГ-ФИКС: убран App.get_running_app() из __init__ —
#  при создании экранов приложение ещё не запущено и вернёт None.
#  Теперь обращаемся к app только в момент нажатия кнопки.
# ════════════════════════════════════════════════
class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)

        layout.add_widget(Label(text="⚙️ КИБЕР-ВХОД ⚙️", font_size='28sp', bold=True, size_hint_y=0.15))

        self.input_nick = TextInput(text="", hint_text="Твой Хакер-Ник", multiline=False,
                                    size_hint_y=0.12, font_size='18sp')
        layout.add_widget(self.input_nick)

        self.input_pass = TextInput(text="", hint_text="Пароль", password=True, multiline=False,
                                    size_hint_y=0.12, font_size='18sp')
        layout.add_widget(self.input_pass)

        self.label_info = Label(text="Введите данные для входа в сеть",
                                color=(0.7, 0.7, 0.7, 1), size_hint_y=0.1)
        layout.add_widget(self.label_info)

        btn_login = Button(text="ПОДКЛЮЧИТЬСЯ", background_color=(0.23, 0.51, 0.96, 1),
                           font_size='22sp', bold=True, size_hint_y=0.18)
        btn_login.bind(on_press=self.start_login)
        layout.add_widget(btn_login)

        layout.add_widget(Label(size_hint_y=0.21))
        self.add_widget(layout)

    def start_login(self, instance):
        nick = self.input_nick.text.strip()
        password = self.input_pass.text.strip()

        if not nick or not password:
            self.label_info.text = "Заполни все поля, хакер!"
            return

        self.label_info.text = "Связь со спутником..."

        app = App.get_running_app()
        app.nickname = nick
        app.temp_pass = password
        threading.Thread(target=app.cloud_login, daemon=True).start()


# ════════════════════════════════════════════════
#  ГЛАВНЫЙ ЭКРАН
#  БАГ-ФИКС: методы on_enter, click, _save перенесены СЮДА
#  (раньше они висели в классе App и никогда не срабатывали как методы экрана).
# ════════════════════════════════════════════════
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.main_layout = BoxLayout(orientation='vertical', padding=30, spacing=15)

        score_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=5)
        score_layout.add_widget(Label(size_hint_x=0.3))

        from kivy.uix.image import Image
        diamond_icon = Image(source='diamond.png', size_hint_x=0.15, allow_stretch=True)
        score_layout.add_widget(diamond_icon)

        self.label_score = Label(text="0", font_size='40sp', bold=True,
                                 color=(0.98, 0.8, 0.08, 1), size_hint_x=0.25,
                                 halign='left', valign='middle')
        score_layout.add_widget(self.label_score)
        score_layout.add_widget(Label(size_hint_x=0.3))
        self.main_layout.add_widget(score_layout)

        self.label_info = Label(text="", font_size='14sp',
                                color=(0.22, 0.74, 0.97, 1), halign='center')
        self.main_layout.add_widget(self.label_info)

        self.btn_rebirth = Button(text="", size_hint_y=0.15,
                                  background_color=(0.57, 0.12, 0.96, 1),
                                  font_size='12sp', bold=True)
        self.btn_rebirth.bind(on_press=lambda x: App.get_running_app().do_rebirth())
        self.main_layout.add_widget(self.btn_rebirth)

        self.click_area = BoxLayout(orientation='vertical', size_hint_y=0.35)
        self.anim_label = Label(text="", font_size='24sp', bold=True,
                                color=(0.14, 0.77, 0.37, 1), size_hint_y=0.2, opacity=0)
        self.click_area.add_widget(self.anim_label)

        self.btn_click = Button(text="ХАКНУТЬ", size_hint_y=0.8,
                                background_color=(0.23, 0.51, 0.96, 1),
                                font_size='36sp', bold=True)
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
        btn_out.bind(on_press=lambda x: App.get_running_app().logout())
        exit_btns.add_widget(btn_out)

        btn_exit_app = Button(text="ВЫЙТИ ИЗ ИГРЫ", background_color=(0.4, 0.4, 0.4, 1))
        btn_exit_app.bind(on_press=lambda x: App.get_running_app().exit_app())
        exit_btns.add_widget(btn_exit_app)
        self.main_layout.add_widget(exit_btns)

        self.add_widget(self.main_layout)
        Clock.schedule_interval(self.update_ui, 0.1)

    # ── БАГ-ФИКС: on_enter теперь в MainScreen, а не в App ──────────────────
    def on_enter(self):
        """Вызывается каждый раз при переходе на этот экран — синхронизируем лейбл."""
        app = App.get_running_app()
        self.label_score.text = format_num(app.score)

    def on_click_pressed(self, instance):
        app = App.get_running_app()
        if app.current_brawler == "Школьник-Читер":
            current_click = "???"
        elif app.current_brawler == "ISKA25k":
            current_click = "Удача"
        else:
            current_click = format_num(int(app.income * (1 + app.rebirths * 0.5)))

        self.anim_label.text = f"+{current_click}"
        self.anim_label.opacity = 1
        anim = Animation(opacity=0, duration=0.4)
        anim.start(self.anim_label)
        app.click()

    def update_ui(self, dt):
        app = App.get_running_app()
        next_cost = app.get_rebirth_cost()
        self.label_score.text = format_num(app.score)

        if app.current_brawler == "Школьник-Читер":
            click_text = "50% шанс: +150 / +0"
        elif app.current_brawler == "ISKA25k":
            click_text = "15% шанс: +10000 / иначе +5000"
        else:
            click_text = (f"x{format_num(int(app.income * (1 + app.rebirths * 0.5)))} "
                          f"(Бонус: +{app.rebirths * 50}%)")

        bars = int((app.energy / app.max_energy) * 10)
        energy_bar = "[" + "|" * bars + " " * (10 - bars) + "]"

        self.label_info.text = (
            f"Хакер: {app.nickname} | Перерождения: {app.rebirths}\n"
            f"Герой: {app.current_brawler}\n"
            f"Клик: {click_text} | Пассив: +{format_num(app.passive_income)}/сек\n"
            f"ЭНЕРГИЯ: {energy_bar} {int(app.energy)} / {app.max_energy}"
        )

        self.btn_rebirth.text = f"⚡ СДЕЛАТЬ ПЕРЕРОЖДЕНИЕ ⚡\nЦена: {format_num(next_cost)} | ...+50% к клику"
        can_rebirth = app.score >= next_cost
        self.btn_rebirth.opacity = 1 if can_rebirth else 0
        self.btn_rebirth.disabled = not can_rebirth


# ════════════════════════════════════════════════
#  МАГАЗИН
# ════════════════════════════════════════════════
class ShopScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=20, spacing=10)
        root.add_widget(Label(text="КИБЕР-МАРКЕТ", font_size='26sp', bold=True, size_hint_y=0.1))
        scroll = ScrollView()
        self.items = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.items.bind(minimum_height=self.items.setter('height'))
        self.shop_buttons = []

        self.shop_data = [
            ("case_normal",    "ОБЫЧНЫЙ КЕЙС\n(35% - 150💎 | 65% - 0💎)",                          0,  False),
            ("case_epic",      "ЭПИЧЕСКИЙ КЕЙС\n(35% - 400💎 | 20% - Герой Школьник | 45% - 0💎)", 0,  False),
            ("case_legendary", "ЛЕГЕНДАРНЫЙ КЕЙС\n(65% - 5k💎 | 25% - 7.5k💎 | 7% - Хакер | 3% - ISKA25k)", 0, False),
            ("farm",           "МАЙНИНГ ФЕРМА (+5/сек)",                                            0,  False),
            ("double",         "УДВОИТЕЛЬ КЛИКА (x2)",                                              0,  False),
            ("hero_sl",        "ГЕРОЙ: Школьник-Читер",                                             1,  True),
            ("hero_hacker",    "ГЕРОЙ: Хакер",                                                      10, True),
            ("hero_iska",      "ГЕРОЙ: ISKA25k",                                                    50, True),
        ]

        for key, name, pwr, is_hero in self.shop_data:
            btn = Button(text="", size_hint_y=None, height='90dp', halign='center')
            btn.bind(on_press=lambda x, k=key, n=name, p=pwr, ih=is_hero:
                     App.get_running_app().buy(k, n, p, ih))
            self.items.add_widget(btn)
            self.shop_buttons.append((key, btn, name))

        scroll.add_widget(self.items)
        root.add_widget(scroll)

        btn_back = Button(text="НАЗАД", size_hint_y=0.1)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        root.add_widget(btn_back)
        self.add_widget(root)
        # update_buttons вызывается только в on_enter, не при создании экрана

    def on_enter(self):
        self.update_buttons()

    def update_buttons(self):
        app = App.get_running_app()
        for key, btn, name in self.shop_buttons:
            price = app.get_price(key)
            btn.text = f"{name}\nЦена: {format_num(price)} "


# ════════════════════════════════════════════════
#  ТОП-10
# ════════════════════════════════════════════════
class LeaderboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=30, spacing=20)
        root.add_widget(Label(text="🏆 МИРОВОЙ ТОП-10 🏆", size_hint_y=0.15,
                              font_size='24sp', bold=True))

        self.top_text_label = Label(
            text="ЗАГРУЗКА МИРОВОГО ТОПА...",
            font_size='18sp', size_hint_y=0.7,
            halign='center', valign='middle'
        )
        self.top_text_label.text_size = (800, None)
        root.add_widget(self.top_text_label)

        btn = Button(text="НАЗАД В ИГРУ", size_hint_y=0.15,
                     background_color=(0.12, 0.16, 0.23, 1), bold=True)
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main'))
        root.add_widget(btn)
        self.add_widget(root)

    def on_enter(self):
        self.load_top()

    def load_top(self):
        from kivy.network.urlrequest import UrlRequest
        base_url = "https://dyqkybmzhrqksdnhjsec.supabase.co"
        url = base_url + "/rest/v1/saves?select=id,full_db"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Range": "0-9"
        }
        UrlRequest(url, on_success=self.on_top_success,
                   on_failure=self.on_top_error, on_error=self.on_top_error,
                   req_headers=headers)

    def on_top_success(self, req, result):
        Clock.schedule_once(lambda dt: self.update_top_ui(result), 0)

    def on_top_error(self, req, result):
        Clock.schedule_once(lambda dt: self.update_top_ui([]), 0)

    def update_top_ui(self, all_rows):
        mock_data = []
        if isinstance(all_rows, dict):
            all_rows = [all_rows]
        if isinstance(all_rows, list) and all_rows:
            for row in all_rows:
                if not isinstance(row, dict):
                    continue
                user_name = row.get("id")
                full_db = row.get("full_db", {})
                if isinstance(full_db, str) and full_db.strip():
                    try:
                        full_db = json.loads(full_db)
                    except Exception:
                        full_db = {}
                if user_name:
                    score_val = 0
                    if isinstance(full_db, dict) and full_db:
                        s_data = full_db.get("save_data", {})
                        score_val = s_data.get("score", 0) if isinstance(s_data, dict) else full_db.get("score", 0)
                    mock_data.append({"name": str(user_name), "score": int(score_val)})

        if not mock_data:
            self.top_text_label.text = "В таблице лидеров пока пусто...\n\nНакликай 10 алмазов!"
            return

        mock_data = sorted(mock_data, key=lambda x: x['score'], reverse=True)[:10]
        lines = [f"{i}. {u['name']}  ---  {format_num(u['score'])} 💎"
                 for i, u in enumerate(mock_data, 1)]
        self.top_text_label.text = "\n".join(lines)


# ════════════════════════════════════════════════
#  ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
# ════════════════════════════════════════════════
class CyberClickerApp(App):
    def build(self):
        global LOCAL_DB_FILE

        # БАГ-ФИКС: на Android user_data_dir доступен только здесь, внутри build()
        try:
            from kivy.utils import platform
            if platform == "android":
                LOCAL_DB_FILE = os.path.join(self.user_data_dir, "cyber_player_base.json")
        except Exception:
            pass

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
            "farm": 150, "double": 200,
            "hero_sl": 25000, "hero_hacker": 50000, "hero_iska": 100000,
        }

        self.sm = ScreenManager()
        self.sm.add_widget(RegistrationScreen(name='auth'))
        self.sm.add_widget(MainScreen(name='main'))
        self.sm.add_widget(ShopScreen(name='shop'))
        self.sm.add_widget(LeaderboardScreen(name='leaderboard'))

        Clock.schedule_interval(self.add_passive, 1.0)
        Clock.schedule_interval(self.save_to_cloud_tick, 5.0)

        # Загружаем базу ПОСЛЕ того как LOCAL_DB_FILE уже правильный
        self.db = load_local_db()

        return self.sm

    # ── Вспомогалки UI ──────────────────────────────────────────────────────
    def set_auth_info(self, text):
        try:
            if self.sm.has_screen('auth'):
                self.sm.get_screen('auth').label_info.text = str(text)
        except Exception:
            pass

    def enter_game(self):
        if self.sm.has_screen('main'):
            self.sm.current = 'main'
            # on_enter у MainScreen сам обновит лейбл — дополнительно дублируем на всякий случай
            self.sm.get_screen('main').label_score.text = format_num(self.score)

    # ── Клик ────────────────────────────────────────────────────────────────
    # БАГ-ФИКС: click() теперь ТОЛЬКО в App (один экземпляр, без дублирования).
    # Он берёт и пишет строго self.score (app.score) — никаких self на экране.
    def click(self):
        if self.energy < 1:
            if self.sm.has_screen('main'):
                btn = self.sm.get_screen('main').btn_click
                btn.text = "НЕТ ЭНЕРГИИ!"
                Clock.schedule_once(lambda dt: setattr(btn, 'text', "ХАКНУТЬ"), 0.5)
            return

        self.energy -= 1
        bonus = 1 + (self.rebirths * 0.5)

        if self.current_brawler == "Школьник-Читер":
            self.score += int(150 * bonus) if random.random() < 0.40 else 0
        elif self.current_brawler == "ISKA25k":
            self.score += int(10000 * bonus) if random.random() < 0.15 else int(5000 * bonus)
        else:
            self.score += int(self.income * bonus)

        self._save_local()

    # ── Сохранение ──────────────────────────────────────────────────────────
    # БАГ-ФИКС: один метод сохранения, использует глобальный LOCAL_DB_FILE.
    def _save_local(self):
        print(f"[СОХРАНЕНИЕ] ник={self.nickname}, очки={self.score}")
        if "users" not in self.db:
            self.db["users"] = {}
        if self.nickname not in self.db["users"]:
            self.db["users"][self.nickname] = {}

        self.db["users"][self.nickname].update({
            "diamonds": int(self.score),
            "score":    int(self.score),
            "income":   int(self.income),
            "passive":  int(self.passive_income),
            "rebirths": int(self.rebirths),
            "brawler":  str(self.current_brawler),
            "owned_brawlers": self.owned_brawlers,
        })
        print(f"[В ФАЙЛ] {self.db}")
        save_local_db(self.db)
    
    # local_save_only оставляем как псевдоним для совместимости со старыми вызовами
    def local_save_only(self):
        self._save_local()

    # ── Пассивный доход ─────────────────────────────────────────────────────
    def add_passive(self, dt):
        if self.energy < self.max_energy:
            self.energy = min(self.energy + 1, self.max_energy)
        # Сохраняем ТОЛЬКО если игрок уже вошёл в игру!
        if self.sm.current == 'main':
            self.score += self.passive_income
            if self.score > 0:
                self._save_local()
            
    # ── Облако ──────────────────────────────────────────────────────────────
    def save_to_cloud_tick(self, dt):
        if self.sm.current != 'main':
            return
        from kivy.network.urlrequest import UrlRequest
        url = "https://dyqkybmzhrqksdnhjsec.supabase.co/rest/v1/saves?id=eq." + str(self.nickname)
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        body = json.dumps({
            "username": str(self.nickname),
            "diamonds": int(self.score),
            "income":   int(self.income),
            "rebirths": int(self.rebirths),
            "full_db": {
                "password": str(self.temp_pass),
                "save_data": {
                    "diamonds": int(self.score),
                    "score":    int(self.score),
                    "income":   int(self.income),
                    "passive":  int(self.passive_income),
                    "rebirths": int(self.rebirths),
                    "brawler":  str(self.current_brawler),
                    "owned_brawlers": self.owned_brawlers,
                }
            }
        })
        def on_ok(req, res):
            print(f"[ОБЛАКО]: {self.nickname} — {self.score} алмазов сохранено ☁️")
        def on_err(req, res):
            # Запись не существует — создаём
            post_url = "https://dyqkybmzhrqksdnhjsec.supabase.co/rest/v1/saves"
            post_headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            post_body = json.dumps({
                "id":       str(self.nickname),
                "username": str(self.nickname),
                "diamonds": int(self.score),
                "income":   int(self.income),
                "rebirths": int(self.rebirths),
                "full_db": {
                    "password": str(self.temp_pass),
                    "save_data": {
                        "diamonds": int(self.score),
                        "score":    int(self.score),
                        "income":   int(self.income),
                        "passive":  int(self.passive_income),
                        "rebirths": int(self.rebirths),
                        "brawler":  str(self.current_brawler),
                        "owned_brawlers": self.owned_brawlers,
                    }
                }
            })
            UrlRequest(post_url, req_body=post_body, req_headers=post_headers, method='POST')
        UrlRequest(url, req_body=body, req_headers=headers, method='PATCH',
                   on_success=on_ok, on_failure=on_err, on_error=on_err)
    def get_cloud_db(self):
        from kivy.network.urlrequest import UrlRequest
        url = "https://dyqkybmzhrqksdnhjsec.supabase.co" + \
              f"/rest/v1/saves?id=eq.{self.nickname}&select=full_db"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        UrlRequest(url, on_success=self.on_db_success,
                   on_failure=self.on_db_error, on_error=self.on_db_error,
                   req_headers=headers)

    def on_db_success(self, req, result):
        full_db = {}
        if isinstance(result, list) and result:
            full_db = result[0].get("full_db", {})
            if isinstance(full_db, str) and full_db.strip():
                try:
                    full_db = json.loads(full_db)
                except Exception:
                    pass
        if not full_db:
            # Облако вернуло пустоту — читаем локальный файл
            print("[ОБЛАКО ПУСТОЕ]: Читаем локальный файл...")
            self.load_from_local_and_enter()
            return
        self.process_mobile_login(full_db)

    def on_db_error(self, req, result):
        # Облако недоступно — читаем локальный файл напрямую
        print("[ОБЛАКО НЕДОСТУПНО]: Читаем локальный файл...")
        self.load_from_local_and_enter()

    # БАГ-ФИКС: cloud_login объявлен ОДИН РАЗ (раньше был дважды — второй перекрывал первый).
    def cloud_login(self):
        self.get_cloud_db()

    def load_from_local_and_enter(self):
        """Загружает данные из локального файла и входит в игру."""
        import os, json
        if os.path.exists(LOCAL_DB_FILE):
            try:
                with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                if (local_data and "users" in local_data
                        and self.nickname in local_data["users"]):
                    u = local_data["users"][self.nickname]
                    self.score          = int(u.get("diamonds", u.get("score", 0)))
                    self.income         = int(u.get("income", 1))
                    self.passive_income = int(u.get("passive", 0))
                    self.rebirths       = int(u.get("rebirths", 0))
                    self.current_brawler = str(u.get("brawler", "Новичок"))
                    self.owned_brawlers = u.get("owned_brawlers", ["Новичок"])
                    self.db = local_data
                    print(f"[ЛОКАЛ ЗАГРУЖЕН]: {self.nickname} — {self.score} алмазов")
                    Clock.schedule_once(lambda dt: self.enter_game(), 0)
                    return
            except Exception as e:
                print(f"[ОШИБКА ЛОКАЛА]: {e}")
        print("[ПЕРВЫЙ ЗАПУСК]: Создаём новый профиль")
        Clock.schedule_once(lambda dt: self.enter_game(), 0)

    def _load_best_score(self, cloud_score):
        """Берёт максимум из облака и локального файла — защита от затирания нулями."""
        import os, json
        local_score = 0
        if os.path.exists(LOCAL_DB_FILE):
            try:
                with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                if "users" in local_data and self.nickname in local_data["users"]:
                    u = local_data["users"][self.nickname]
                    local_score = int(u.get("diamonds", u.get("score", 0)))
            except Exception:
                pass
        best = max(cloud_score, local_score)
        print(f"[ВЫБОР ЛУЧШЕГО]: облако={cloud_score}, локал={local_score}, берём={best}")
        return best

    def process_mobile_login(self, user_cloud_data):
        # ── 1. Нет облака → читаем локальный файл ───────────────────────────
        if not user_cloud_data:
            if os.path.exists(LOCAL_DB_FILE):
                try:
                    with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                        local_data = json.load(f)
                    if (local_data and "users" in local_data
                            and self.nickname in local_data["users"]):
                        u = local_data["users"][self.nickname]
                        self.score          = int(u.get("diamonds", u.get("score", 0)))
                        self.income         = int(u.get("income", 1))
                        self.passive_income = int(u.get("passive", 0))
                        self.rebirths       = int(u.get("rebirths", 0))
                        self.current_brawler = str(u.get("brawler", "Новичок"))
                        self.owned_brawlers = u.get("owned_brawlers", ["Новичок"])
                        self.db = local_data
                        print(f"[ЗАГРУЗКА]: {self.nickname} — {self.score} алмазов")
                        Clock.schedule_once(lambda dt: self.enter_game(), 0)
                        return
                except Exception as e:
                    print(f"[ОШИБКА ЧТЕНИЯ ЛОКАЛА]: {e}")

        # ── 2. Облако ответило — проверяем пароль ───────────────────────────
        if user_cloud_data:
            saved_pass = user_cloud_data.get("password")
            save_data  = user_cloud_data.get("save_data", {})

            if saved_pass == self.temp_pass or not saved_pass:
                if isinstance(save_data, dict):
                    cloud_score = int(save_data.get("diamonds", save_data.get("score", 0)))
                    self.score  = self._load_best_score(cloud_score)
                    self.income         = int(save_data.get("income", 1))
                    self.passive_income = int(save_data.get("passive", 0))
                    self.rebirths       = int(save_data.get("rebirths", 0))
                    self.current_brawler = str(save_data.get("brawler", "Новичок"))
                    self.owned_brawlers = save_data.get("owned_brawlers", ["Новичок"])
                    if "prices" in save_data:
                        self.prices.update(save_data["prices"])
                Clock.schedule_once(lambda dt: self.enter_game(), 0)
                return
            else:
                Clock.schedule_once(lambda dt: self.set_auth_info("Неверный пароль!"), 0)
                return

        # ── 3. Профиль уже есть в локальной базе — не затираем нулями ───────
        if os.path.exists(LOCAL_DB_FILE):
            try:
                with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                    check_data = json.load(f)
                if ("users" in check_data and self.nickname in check_data["users"]):
                    u = check_data["users"][self.nickname]
                    self.score = int(u.get("diamonds", u.get("score", 0)))
                    print(f"[ЗАГРУЗКА]: ник={self.nickname}, алмазы={self.score}, файл={LOCAL_DB_FILE}")
                    self.db    = check_data
                    print("[ЗАЩИТА]: Профиль найден в локальной базе — нули не пишем!")
                    Clock.schedule_once(lambda dt: self.enter_game(), 0)
                    return
            except Exception:
                pass

        # ── 4. Первый запуск — создаём новый профиль ────────────────────────
        new_profile = {
            "password": str(self.temp_pass),
            "save_data": {
                "diamonds": 0, "score": 0, "income": 1, "passive": 0,
                "rebirths": 0, "brawler": "Новичок", "owned_brawlers": ["Новичок"],
            }
        }
        self.update_cloud_db(new_profile)
        Clock.schedule_once(lambda dt: self.enter_game(), 0)

    def update_cloud_db(self, full_db):
        def run():
            try:
                supabase_client.table("saves").upsert({
                    "id":       str(self.nickname),
                    "username": str(self.nickname),
                    "diamonds": int(self.score),
                    "income":   int(self.income),
                    "rebirths": int(self.rebirths),
                    "full_db":  full_db
                }).execute()
                print(f"[ОБЛАКО upsert]: OK")
            except Exception as e:
                print(f"[ОБЛАКО upsert СБОЙ]: {e}")
        if supabase_client:
            threading.Thread(target=run, daemon=True).start()
    def force_cloud_save(self):
        self.update_cloud_db({
            "password": str(self.temp_pass),
            "save_data": {
                "diamonds": int(self.score), "score": int(self.score),
                "income": int(self.income),  "passive": int(self.passive_income),
                "rebirths": int(self.rebirths), "brawler": str(self.current_brawler),
                "prices": self.prices, "owned_brawlers": self.owned_brawlers,
            }
        })

    # ── Перерождение ────────────────────────────────────────────────────────
    def get_rebirth_cost(self):
        if   self.rebirths == 0: return 1_000_000
        elif self.rebirths == 1: return 5_000_000
        elif self.rebirths == 2: return 25_000_000
        else:                    return (self.rebirths + 1) * 50_000_000

    def do_rebirth(self):
        cost = self.get_rebirth_cost()
        if self.score < cost:
            return
        self.score   -= cost
        self.rebirths += 1
        self.income   = 1
        self.passive_income = 0
        self.prices = {
            "case_normal": 100, "case_epic": 1000, "case_legendary": 10000,
            "farm": 150, "double": 200,
            "hero_sl": 25000, "hero_hacker": 50000, "hero_iska": 100000,
        }
        self._save_local()
        self.show_popup("ПЕРЕРОЖДЕНИЕ!", f"Ты переродился! Перерождений: {self.rebirths}\n+50% к каждому клику навсегда!")

    # ── Магазин ─────────────────────────────────────────────────────────────
    def get_price(self, key):
        return self.prices.get(key, 0)

    def buy(self, key, name, power, is_hero):
        if key == "hero_hacker" and self.rebirths < 2:
            self.show_popup("БЛОКИРОВКА!", "Для покупки Хакера нужно минимум 2 перерождения!")
            return
        if key == "hero_iska" and self.rebirths < 3:
            self.show_popup("БЛОКИРОВКА!", "Для покупки ISKA25k нужно минимум 3 перерождения!")
            return

        price = self.get_price(key)
        if self.score < price:
            return

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
            else:
                self.show_popup("ОБЫЧНЫЙ КЕЙС", "Пусто...")
        elif key == "case_epic":
            r = random.random()
            if r < 0.35:
                self.score += 400
                self.show_popup("ЭПИЧЕСКИЙ КЕЙС", "Вы выиграли 400 💎!")
            elif r < 0.55:
                if "Школьник-Читер" in self.owned_brawlers:
                    self.score += 5000
                    self.show_popup("ДУБЛИКАТ!", "Школьник-Читер уже есть! Возвращено 25k 💎")
                else:
                    self.owned_brawlers.append("Школьник-Читер")
                    self.current_brawler = "Школьник-Читер"
                    self.income += 1
                    self.show_popup("НОВЫЙ БОЕЦ!", "Вы выбили бойца: Школьник-Читер!")
            else:
                self.show_popup("ЭПИЧЕСКИЙ КЕЙС", "Пусто...")
        elif key == "case_legendary":
            r = random.random()
            if r < 0.65:
                self.score += 5000
                self.show_popup("ЛЕГЕНДАРНЫЙ КЕЙС", "Вы выиграли 5,000 💎!")
            elif r < 0.90:
                self.score += 7500
                self.show_popup("ЛЕГЕНДАРНЫЙ КЕЙС", "Вы выиграли 7,500 💎!")
            elif r < 0.97:
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

        self._save_local()
        self.force_cloud_save()
        if self.sm.has_screen('shop'):
            self.sm.get_screen('shop').update_buttons()

    # ── Попап ────────────────────────────────────────────────────────────────
    def show_popup(self, title, text):
        box = BoxLayout(orientation='vertical', padding=20, spacing=10)
        lbl = Label(text=text, halign='center', valign='middle', font_size='16sp')
        lbl.bind(size=lambda s, w: setattr(lbl, 'text_size', (w[0] - 20, None)))
        box.add_widget(lbl)
        popup = Popup(title=title, content=box, size_hint=(0.85, 0.45))
        btn = Button(text="ОК", size_hint_y=0.3,
                     background_color=(0.23, 0.51, 0.96, 1), bold=True)
        btn.bind(on_press=popup.dismiss)
        box.add_widget(btn)
        popup.open()

    # ── Выход ────────────────────────────────────────────────────────────────
    def logout(self, *args):
        self.nickname = "GUEST"
        self.sm.current = 'auth'

    def exit_app(self, *args):
        self.stop()


if __name__ == '__main__':
    CyberClickerApp().run()
