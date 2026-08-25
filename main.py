# ==============================================================================
# JULIE AI OS — PRODUCTION STABLE CORE v6.6
# Android 15 / API 35
#
# FIXES:
# 1. MessageBubble texture_size tuple bug fixed
# 2. Android 15 safe-area handled without risky JNI system-bar calls
# 3. Explicit root background prevents bottom visual patch
# 4. MessageBubble width behaviour fixed
# 5. SpeechRecognizer lifecycle protected
# 6. Multiline input preserved
# 7. No experimental Android system-bar JNI
# ==============================================================================

import os
import re
from datetime import datetime, timedelta

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.graphics import (
    Color,
    RoundedRectangle,
    Line,
    Ellipse,
)
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex


# ==============================================================================
# GLOBAL WINDOW SETUP
# ==============================================================================

WINDOW_BG = "#05080F"

Window.clearcolor = get_color_from_hex(WINDOW_BG)

try:
    Window.softinput_mode = "below_target"
except Exception:
    pass


# ==============================================================================
# ANDROID DETECTION
# ==============================================================================

IS_ANDROID = False

try:
    from android.permissions import (
        Permission,
        check_permission,
        request_permissions,
    )

    from android.runnable import run_on_ui_thread

    from jnius import (
        PythonJavaClass,
        autoclass,
        java_method,
    )

    IS_ANDROID = True

except Exception:

    def run_on_ui_thread(function):
        return function


# Android 15 / API 35 Navigation Bar Fix
def configure_android_navigation_bar():
    if not IS_ANDROID:
        return
    try:
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        window = activity.getWindow()

        Color = autoclass("android.graphics.Color")
        window.setNavigationBarColor(Color.TRANSPARENT)

        # Disable Android 15 3-button navigation contrast scrim
        window.setNavigationBarContrastEnforced(False)

        # Keep divider transparent
        try:
            window.setNavigationBarDividerColor(Color.TRANSPARENT)
        except Exception:
            pass
    except Exception as exc:
        print("Navigation bar configuration:", exc)


# ==============================================================================
# 1. SMART PHONETIC CLEANER
# ==============================================================================

def smart_clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.strip().lower()

    corrections = {
        r"\bcal\b": "kal",
        r"\bcall\b(?!\s+(me|him|her|them|\d+))": "kal",
        r"\bkall\b": "kal",
        r"\bcolo\b": "kholo",
        r"\bkolo\b": "kholo",
        r"\bchalo\b": "chalao",
        r"\byutub\b": "youtube",
        r"\butube\b": "youtube",
        r"\bwhats app\b": "whatsapp",
        r"\bwatsapp\b": "whatsapp",
        r"\bcrome\b": "chrome",
    }

    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text)

    return text


# ==============================================================================
# 2. ANDROID SPEECH LISTENER
# ==============================================================================

if IS_ANDROID:

    class JulieSpeechListener(PythonJavaClass):

        __javainterfaces__ = [
            "android/speech/RecognitionListener"
        ]

        __javacontext__ = "app"

        def __init__(self, app):
            super().__init__()
            self.app = app

        @java_method("(Landroid/os/Bundle;)V")
        def onReadyForSpeech(self, params):
            self.app.on_speech_ready()

        @java_method("()V")
        def onBeginningOfSpeech(self):
            pass

        @java_method("(F)V")
        def onRmsChanged(self, rms):
            pass

        @java_method("([B)V")
        def onBufferReceived(self, buffer):
            pass

        @java_method("()V")
        def onEndOfSpeech(self):
            pass

        @java_method("(I)V")
        def onError(self, code):
            self.app.on_speech_error(int(code))

        @java_method("(Landroid/os/Bundle;)V")
        def onResults(self, results):

            try:
                SpeechRecognizer = autoclass(
                    "android.speech.SpeechRecognizer"
                )

                matches = results.getStringArrayList(
                    SpeechRecognizer.RESULTS_RECOGNITION
                )

                text = ""

                if matches is not None:
                    try:
                        if matches.size() > 0:
                            text = str(matches.get(0))
                    except Exception:
                        text = ""

                self.app.on_speech_success(text)

            except Exception:
                self.app.reset_mic()

        @java_method("(Landroid/os/Bundle;)V")
        def onPartialResults(self, partialResults):
            pass

        @java_method("(ILandroid/os/Bundle;)V")
        def onEvent(self, eventType, params):
            pass


# ==============================================================================
# 3. MIC BUTTON
# ==============================================================================

class MicButton(Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)

        self.size_hint = (None, None)
        self.size = (dp(44), dp(44))

        with self.canvas.before:

            self.bg_color = Color(
                rgba=get_color_from_hex("#131D31")
            )

            self.circle = Ellipse(
                pos=self.pos,
                size=self.size
            )

        with self.canvas.after:

            self.icon_color = Color(
                rgba=get_color_from_hex("#38BDF8")
            )

            self.mic_body = RoundedRectangle(
                pos=(0, 0),
                size=(dp(10), dp(16)),
                radius=[dp(5)]
            )

            self.mic_arc = Line(
                width=dp(1.8)
            )

            self.mic_stem = Line(
                width=dp(1.8)
            )

            self.mic_base = Line(
                width=dp(1.8)
            )

        self.bind(
            pos=self.redraw,
            size=self.redraw
        )

        self.redraw()

    def redraw(self, *args):

        x = self.x
        y = self.y

        self.circle.pos = self.pos
        self.circle.size = self.size

        self.mic_body.pos = (
            x + dp(17),
            y + dp(14)
        )

        self.mic_arc.points = [
            x + dp(13),
            y + dp(18),

            x + dp(13),
            y + dp(11),

            x + dp(31),
            y + dp(11),

            x + dp(31),
            y + dp(18)
        ]

        self.mic_stem.points = [
            x + dp(22),
            y + dp(11),

            x + dp(22),
            y + dp(7)
        ]

        self.mic_base.points = [
            x + dp(17),
            y + dp(7),

            x + dp(27),
            y + dp(7)
        ]

    def set_active(self, active):

        if active:

            self.icon_color.rgba = get_color_from_hex(
                "#FFFFFF"
            )

            self.bg_color.rgba = get_color_from_hex(
                "#EF4444"
            )

        else:

            self.icon_color.rgba = get_color_from_hex(
                "#38BDF8"
            )

            self.bg_color.rgba = get_color_from_hex(
                "#131D31"
            )


# ==============================================================================
# 4. SEND BUTTON
# ==============================================================================

class SendButton(Button):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)

        self.size_hint = (None, None)
        self.size = (dp(44), dp(44))

        with self.canvas.before:

            self.bg_color = Color(
                rgba=get_color_from_hex("#2563EB")
            )

            self.circle = Ellipse(
                pos=self.pos,
                size=self.size
            )

        with self.canvas.after:

            self.icon_color = Color(
                rgba=get_color_from_hex("#FFFFFF")
            )

            self.arrow = Line(
                width=dp(2.2),
                joint="round"
            )

        self.bind(
            pos=self.redraw,
            size=self.redraw
        )

        self.redraw()

    def redraw(self, *args):

        x = self.x
        y = self.y

        self.circle.pos = self.pos
        self.circle.size = self.size

        self.arrow.points = [

            x + dp(14),
            y + dp(13),

            x + dp(31),
            y + dp(22),

            x + dp(14),
            y + dp(31),

            x + dp(18),
            y + dp(22),

            x + dp(14),
            y + dp(13)
        ]


# ==============================================================================
# 5. MESSAGE BUBBLE
# ==============================================================================

class MessageBubble(BoxLayout):

    def __init__(self, sender, text, **kwargs):

        super().__init__(**kwargs)

        self.orientation = "vertical"

        self.size_hint_y = None

        # IMPORTANT:
        # Prevent parent BoxLayout from stretching bubble horizontally.
        self.size_hint_x = None

        self.padding = [
            dp(16),
            dp(12),
            dp(16),
            dp(12)
        ]

        self.spacing = dp(6)

        width = min(
            Window.width *
            (0.82 if sender == "USER" else 0.92),
            dp(360)
        )

        self.width = width

        if sender == "USER":

            bg = "#1B3A60"
            accent = "#93C5FD"
            title = "YOU"

            self.pos_hint = {
                "right": 1
            }

        elif sender == "SYSTEM":

            bg = "#0F1A2C"
            accent = "#38BDF8"
            title = "SYSTEM KERNEL"

            self.pos_hint = {
                "x": 0
            }

        else:

            bg = "#122033"
            accent = "#10B981"
            title = "JULIE AI OS"

            self.pos_hint = {
                "x": 0
            }

        timestamp = datetime.now().strftime("%H:%M")

        # ----------------------------------------------------------------------
        # Bubble Background
        # ----------------------------------------------------------------------

        with self.canvas.before:

            Color(
                rgba=get_color_from_hex(bg)
            )

            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(18)]
            )

            Color(
                rgba=get_color_from_hex(
                    "#2C5282"
                    if sender == "USER"
                    else "#1E3A5F"
                )
            )

            self.border = Line(
                rounded_rectangle=[
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(18)
                ],
                width=dp(1)
            )

        self.bind(
            pos=self.update_canvas,
            size=self.update_canvas
        )

        # ----------------------------------------------------------------------
        # Header
        # ----------------------------------------------------------------------

        header = Label(
            text=f"[b]{title}[/b]  {timestamp}",
            markup=True,
            color=get_color_from_hex(accent),
            font_size="11sp",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(18)
        )

        header.text_size = (
            width - dp(32),
            None
        )

        # ----------------------------------------------------------------------
        # Message Body
        # ----------------------------------------------------------------------

        body = Label(
            text=text,
            color=get_color_from_hex("#F1F5F9"),
            font_size="15sp",
            halign="left",
            valign="top",
            size_hint_y=None
        )

        body.text_size = (
            width - dp(32),
            None
        )

        body.bind(
            texture_size=self.update_height
        )

        self.body = body

        self.add_widget(header)
        self.add_widget(body)

        # Initial safe height
        self.height = dp(60)

    def update_canvas(self, *args):

        self.rect.pos = self.pos
        self.rect.size = self.size

        self.border.rounded_rectangle = [
            self.x,
            self.y,
            self.width,
            self.height,
            dp(18)
        ]

    def update_height(self, instance, texture_size):
        height = float(texture_size[1])
        instance.height = height
        self.height = dp(48) + height

    def build(self):

        self.title = "JULIE AI OS"

        self.speech_recognizer = None
        self.listener_ref = None
        self.is_listening = False

        # ----------------------------------------------------------------------
        # ROOT CONTAINER
        #
        # IMPORTANT:
        # No Android JNI system-bar calls here.
        # dp(48) is a conservative bottom safe-area reservation.
        # ----------------------------------------------------------------------

        root = BoxLayout(
            orientation="vertical",
            padding=[
                dp(10),
                dp(8),
                dp(10),
                dp(48)
            ],
            spacing=dp(6)
        )

        # ----------------------------------------------------------------------
        # Explicit dark background
        #
        # Prevents any transparent/white bottom patch.
        # ----------------------------------------------------------------------

        with root.canvas.before:

            self.root_bg_color = Color(
                rgba=get_color_from_hex(WINDOW_BG)
            )

            self.root_bg = RoundedRectangle(
                pos=root.pos,
                size=root.size
            )

        root.bind(
            pos=self.update_root_background,
            size=self.update_root_background
        )

        # ======================================================================
        # HEADER
        # ======================================================================

        header = BoxLayout(
            size_hint_y=None,
            height=dp(42)
        )

        title_box = BoxLayout(
            orientation="vertical"
        )

        title = Label(
            text="[b]JULIE AI OS[/b]",
            markup=True,
            font_size="19sp",
            color=get_color_from_hex("#38BDF8"),
            halign="left",
            valign="middle"
        )

        title.bind(
            width=lambda instance, value:
            setattr(
                instance,
                "text_size",
                (value, None)
            )
        )

        subtitle = Label(
            text="PRO QUANTUM SYSTEM v6.6",
            font_size="8.5sp",
            color=get_color_from_hex("#64748B"),
            halign="left",
            valign="middle"
        )

        subtitle.bind(
            width=lambda instance, value:
            setattr(
                instance,
                "text_size",
                (value, None)
            )
        )

        title_box.add_widget(title)
        title_box.add_widget(subtitle)

        status = Label(
            text="[b]● SECURE[/b]",
            markup=True,
            font_size="10sp",
            color=get_color_from_hex("#10B981"),
            halign="right",
            valign="middle"
        )

        status.bind(
            width=lambda instance, value:
            setattr(
                instance,
                "text_size",
                (value, None)
            )
        )

        header.add_widget(title_box)
        header.add_widget(status)

        root.add_widget(header)

        # ======================================================================
        # CHAT
        # ======================================================================

        self.scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3),
            size_hint=(1, 1)
        )

        self.chat = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=[
                dp(2),
                dp(4),
                dp(2),
                dp(8)
            ]
        )

        self.chat.bind(
            minimum_height=self.chat.setter("height")
        )

        self.scroll.add_widget(self.chat)

        root.add_widget(self.scroll)

        # ======================================================================
        # BOTTOM STACK
        # ======================================================================

        self.bottom_stack = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(56),
            spacing=dp(4)
        )

        # ======================================================================
        # SECONDARY INPUT
        # ======================================================================

        self.second_box_wrapper = BoxLayout(
            size_hint_y=None,
            height=0,
            padding=[
                dp(4),
                0,
                dp(4),
                0
            ]
        )

        self.secondary_input = TextInput(
            hint_text="Add Tag / Quick Command Modifier...",
            hint_text_color=get_color_from_hex("#475569"),
            multiline=False,
            font_size="12.5sp",
            background_normal="",
            background_active="",
            background_color=(
                0.08,
                0.12,
                0.20,
                1
            ),
            foreground_color=get_color_from_hex("#38BDF8"),
            cursor_color=get_color_from_hex("#38BDF8"),
            padding=[
                dp(10),
                dp(6),
                dp(10),
                dp(6)
            ]
        )

        self.second_box_wrapper.add_widget(
            self.secondary_input
        )

        self.bottom_stack.add_widget(
            self.second_box_wrapper
        )

        # ======================================================================
        # MAIN INPUT
        # ======================================================================

        input_box = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            padding=[
                dp(10),
                dp(6),
                dp(6),
                dp(6)
            ],
            spacing=dp(6)
        )

        with input_box.canvas.before:

            Color(
                rgba=get_color_from_hex("#0D1626")
            )

            self.input_bg = RoundedRectangle(
                pos=input_box.pos,
                size=input_box.size,
                radius=[dp(26)]
            )

            Color(
                rgba=get_color_from_hex("#1E293B")
            )

            self.input_border = Line(
                rounded_rectangle=[
                    input_box.x,
                    input_box.y,
                    input_box.width,
                    input_box.height,
                    dp(26)
                ],
                width=1
            )

        input_box.bind(
            pos=self.update_input_bg,
            size=self.update_input_bg
        )

        # ======================================================================
        # MAIN TEXT INPUT
        # ======================================================================

        self.cmd_input = TextInput(
            hint_text="Ask or command JULIE...",
            hint_text_color=get_color_from_hex("#64748B"),
            multiline=True,
            font_size="14sp",
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=get_color_from_hex("#F8FAFC"),
            cursor_color=get_color_from_hex("#38BDF8"),
            padding=[
                dp(6),
                dp(10),
                dp(4),
                dp(8)
            ]
        )

        self.cmd_input.bind(
            text=self.on_main_text_changed
        )

        input_box.add_widget(
            self.cmd_input
        )

        # ======================================================================
        # MIC
        # ======================================================================

        self.mic = MicButton()

        self.mic.bind(
            on_release=self.on_mic
        )

        input_box.add_widget(
            self.mic
        )

        # ======================================================================
        # SEND
        # ======================================================================

        send = SendButton()

        send.bind(
            on_release=self.on_send_button
        )

        input_box.add_widget(
            send
        )

        self.bottom_stack.add_widget(
            input_box
        )

        root.add_widget(
            self.bottom_stack
        )

        Clock.schedule_once(
            self.startup,
            0.2
        )

        return root

    # ==========================================================================
    # ROOT BACKGROUND
    # ==========================================================================

    def update_root_background(self, instance, *args):

        self.root_bg.pos = instance.pos
        self.root_bg.size = instance.size

    # ==========================================================================
    # INPUT BACKGROUND
    # ==========================================================================

    def update_input_bg(self, instance, *args):

        self.input_bg.pos = instance.pos
        self.input_bg.size = instance.size

        self.input_border.rounded_rectangle = [
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            dp(26)
        ]

    # ==========================================================================
    # STARTUP
    # ==========================================================================

    def startup(self, dt):

        self.add_message(
            "SYSTEM",
            "JULIE AI OS Pro Kernel v6.6 Active."
        )

        self.add_message(
            "JULIE",
            "Hello! Type multi-line messages and use the send button."
        )

        if IS_ANDROID:

            try:

                if not check_permission(
                    Permission.RECORD_AUDIO
                ):

                    request_permissions(
                        [Permission.RECORD_AUDIO]
                    )

            except Exception:
                pass

    # ==========================================================================
    # DYNAMIC SECOND INPUT
    # ==========================================================================

    def on_main_text_changed(self, instance, value):

        if len(value.strip()) > 0:

            self.second_box_wrapper.height = dp(38)
            self.bottom_stack.height = dp(96)

        else:

            self.second_box_wrapper.height = 0
            self.bottom_stack.height = dp(56)

    # ==========================================================================
    # ADD MESSAGE
    # ==========================================================================

    def add_message(self, sender, text):

        bubble = MessageBubble(
            sender,
            text
        )

        self.chat.add_widget(
            bubble
        )

        Clock.schedule_once(
            lambda dt:
            setattr(
                self.scroll,
                "scroll_y",
                0
            ),
            0.08
        )

    # ==========================================================================
    # SEND BUTTON
    # ==========================================================================

    def on_send_button(self, *args):

        query = self.cmd_input.text.strip()
        modifier = self.secondary_input.text.strip()

        if not query and not modifier:
            return

        if modifier:

            full_query = (
                f"{query} [{modifier}]"
            )

        else:

            full_query = query

        self.cmd_input.text = ""
        self.secondary_input.text = ""

        self.execute(
            full_query
        )

    # ==========================================================================
    # MICROPHONE
    # ==========================================================================

    def on_mic(self, *args):

        if self.is_listening:

            self.stop_listening_safely()

            return

        self.is_listening = True

        self.mic.set_active(True)

        if not IS_ANDROID:

            Clock.schedule_once(
                lambda dt:
                self.on_speech_success(
                    "kal youtube kholo"
                ),
                1.5
            )

            return

        self.start_android_speech()

    # ==========================================================================
    # ANDROID SPEECH START
    # ==========================================================================

    def start_android_speech(self):

        @run_on_ui_thread
        def start():

            try:

                PythonActivity = autoclass(
                    "org.kivy.android.PythonActivity"
                )

                SpeechRecognizer = autoclass(
                    "android.speech.SpeechRecognizer"
                )

                RecognizerIntent = autoclass(
                    "android.speech.RecognizerIntent"
                )

                Intent = autoclass(
                    "android.content.Intent"
                )

                activity = PythonActivity.mActivity

                if activity is None:

                    self.reset_mic()

                    return

                if not SpeechRecognizer.isRecognitionAvailable(
                    activity
                ):

                    self.reset_mic()

                    return

                if self.speech_recognizer is None:

                    self.speech_recognizer = (
                        SpeechRecognizer.createSpeechRecognizer(
                            activity
                        )
                    )

                    self.listener_ref = (
                        JulieSpeechListener(self)
                    )

                    self.speech_recognizer.setRecognitionListener(
                        self.listener_ref
                    )

                else:

                    try:
                        self.speech_recognizer.cancel()
                    except Exception:
                        pass

                intent = Intent(
                    RecognizerIntent.ACTION_RECOGNIZE_SPEECH
                )

                intent.putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                    RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
                )

                intent.putExtra(
                    RecognizerIntent.EXTRA_CALLING_PACKAGE,
                    activity.getPackageName()
                )

                intent.putExtra(
                    RecognizerIntent.EXTRA_LANGUAGE,
                    "hi-IN"
                )

                intent.putExtra(
                    RecognizerIntent.EXTRA_MAX_RESULTS,
                    1
                )

                self.speech_recognizer.startListening(
                    intent
                )

            except Exception:

                self.reset_mic()

        start()

    # ==========================================================================
    # STOP SPEECH
    # ==========================================================================

    def stop_listening_safely(self):

        if IS_ANDROID and self.speech_recognizer:

            try:

                @run_on_ui_thread
                def cancel_rec():

                    try:

                        self.speech_recognizer.stopListening()

                    except Exception:

                        try:
                            self.speech_recognizer.cancel()
                        except Exception:
                            pass

                cancel_rec()

            except Exception:
                pass

        self.reset_mic()

    # ==========================================================================
    # SPEECH CALLBACKS
    # ==========================================================================

    @mainthread
    def on_speech_ready(self):
        pass

    @mainthread
    def on_speech_success(self, raw_text):

        self.reset_mic()

        if not raw_text:
            return

        query = smart_clean_text(
            raw_text
        )

        self.execute(
            query
        )

    @mainthread
    def on_speech_error(self, code):

        self.reset_mic()

        if code == 11:

            if self.speech_recognizer:

                try:
                    self.speech_recognizer.destroy()
                except Exception:
                    pass

            self.speech_recognizer = None
            self.listener_ref = None

    @mainthread
    def reset_mic(self):

        self.is_listening = False

        if hasattr(self, "mic"):

            self.mic.set_active(False)

    # ==========================================================================
    # COMMAND ENGINE
    # ==========================================================================

    def execute(self, query):

        self.add_message(
            "USER",
            query
        )

        q = query.lower()

        # ======================================================================
        # APP LAUNCHER
        # ======================================================================

        if any(
            word in q
            for word in [
                "kholo",
                "open",
                "chalao",
                "launch",
                "khol do"
            ]
        ):

            app_name = "YouTube"
            package = "com.google.android.youtube"

            if "whatsapp" in q:

                app_name = "WhatsApp"
                package = "com.whatsapp"

            elif "chrome" in q:

                app_name = "Chrome"
                package = "com.android.chrome"

            elif "settings" in q:

                app_name = "Settings"
                package = "com.android.settings"

            elif "camera" in q:

                app_name = "Camera"
                package = "com.sec.android.app.camera"

            elif "calculator" in q:

                app_name = "Calculator"
                package = "com.google.android.calculator"

            if IS_ANDROID:

                try:

                    os.system(
                        "monkey "
                        f"-p {package} "
                        "-c android.intent.category.LAUNCHER "
                        "1 > /dev/null 2>&1"
                    )

                except Exception:
                    pass

            self.add_message(
                "JULIE",
                f"Opening {app_name} on your device..."
            )

        # ======================================================================
        # DATE / TIME
        # ======================================================================

        elif any(
            word in q
            for word in [
                "kal",
                "parson",
                "parso",
                "aaj",
                "date",
                "tarikh"
            ]
        ):

            now = datetime.now()

            if "parson" in q or "parso" in q:

                target = now + timedelta(days=2)

                reply = (
                    "Parson ki date "
                    f"{target.strftime('%d %B %Y')} "
                    f"({target.strftime('%A')}) hogi."
                )

            elif "kal" in q:

                target = now + timedelta(days=1)

                reply = (
                    "Kal ki date "
                    f"{target.strftime('%d %B %Y')} "
                    f"({target.strftime('%A')}) hogi."
                )

            else:

                reply = (
                    "Aaj ki date "
                    f"{now.strftime('%d %B %Y')} "
                    f"({now.strftime('%A')}) hai."
                )

            self.add_message(
                "JULIE",
                reply
            )

        # ======================================================================
        # STATUS
        # ======================================================================

        elif (
            "status" in q
            or "kaise ho" in q
        ):

            self.add_message(
                "JULIE",
                "All local JULIE AI OS interface systems are functioning normally."
            )

        # ======================================================================
        # DEFAULT
        # ======================================================================

        else:

            self.add_message(
                "JULIE",
                f"Command received: '{query}'"
            )


# ==============================================================================
# APPLICATION START
# ==============================================================================

if __name__ == "__main__":

    JulieOSApp().run()
