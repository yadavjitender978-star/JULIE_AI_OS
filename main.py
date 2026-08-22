import os, sys, time
from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex, platform

from julie_engine import JulieEngine
from core.actions import ActionItem, ActionType

Window.softinput_mode = 'below_target'
Window.clearcolor = get_color_from_hex('#0B0F19')

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def request_android_permissions(callback=None):
    if platform == 'android':
        try:
            from android.permissions import request_permissions, Permission
            def on_perms(permissions, grants):
                if callback: callback(all(grants))
            request_permissions([Permission.RECORD_AUDIO], on_perms)
        except Exception:
            if callback: callback(True)
    else:
        if callback: callback(True)

class JulieApp(App):
    def build(self):
        self.title = "JULIE AI OS"
        self.engine = JulieEngine(PROJECT_DIR)
        status = self.engine.start()

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(16), dp(16), dp(20)],
            spacing=dp(10)
        )

        # 1. Header Card
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(65),
            spacing=dp(2)
        )
        title_label = Label(
            text="[b]JULIE AI OS[/b]",
            markup=True,
            font_size="26sp",
            color=get_color_from_hex("#38BDF8")
        )
        comp_count = len(status.get('components', []))
        self.status_label = Label(
            text=f"[b]ONLINE[/b] | v1.2.6 Production | {comp_count} Core Engines Active",
            markup=True,
            font_size="13sp",
            color=get_color_from_hex("#94A3B8")
        )
        header.add_widget(title_label)
        header.add_widget(self.status_label)
        root.add_widget(header)

        # 2. Output Console
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.output_label = Label(
            text=(
                "[color=#10B981]* JULIE AI OS Online (Production Ready).[/color]\n"
                "* Tap the green [b][ MIC ] Tap to Speak[/b] button below.\n"
                "* Or type your command in Hindi/English and tap [b]Execute[/b]."
            ),
            markup=True,
            font_size="15sp",
            size_hint_y=None,
            halign="left",
            valign="top",
            color=get_color_from_hex("#E2E8F0")
        )
        self.output_label.bind(texture_size=lambda instance, value: setattr(instance, 'size', value))
        self.output_label.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        # 3. Command Input Bar
        input_bar = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            spacing=dp(8)
        )
        self.cmd_input = TextInput(
            hint_text="कमांड लिखें (जैसे: यूट्यूब खोलो, open chrome)...",
            multiline=False,
            font_size="15sp",
            background_normal="",
            background_color=get_color_from_hex("#1E293B"),
            foreground_color=get_color_from_hex("#F8FAFC"),
            cursor_color=get_color_from_hex("#38BDF8"),
            padding=[dp(12), dp(14), dp(12), dp(12)]
        )
        self.cmd_input.bind(on_text_validate=self.on_send_command)

        send_btn = Button(
            text="Execute",
            size_hint_x=None,
            width=dp(95),
            background_normal="",
            background_color=get_color_from_hex("#0284C7"),
            color=get_color_from_hex("#FFFFFF"),
            font_size="15sp",
            bold=True
        )
        send_btn.bind(on_release=self.on_send_command)
        input_bar.add_widget(self.cmd_input)
        input_bar.add_widget(send_btn)
        root.add_widget(input_bar)

        # 4. Voice Action Bar
        action_bar = BoxLayout(
            size_hint_y=None,
            height=dp(58),
            spacing=dp(10)
        )
        self.mic_btn = Button(
            text="[ MIC ]   Tap to Speak (JULIE)",
            background_normal="",
            background_color=get_color_from_hex("#10B981"),
            color=get_color_from_hex("#FFFFFF"),
            font_size="16sp",
            bold=True
        )
        self.mic_btn.bind(on_release=self.on_mic_toggle)

        clear_btn = Button(
            text="Clear",
            size_hint_x=None,
            width=dp(70),
            background_normal="",
            background_color=get_color_from_hex("#334155"),
            color=get_color_from_hex("#94A3B8"),
            font_size="13sp"
        )
        clear_btn.bind(on_release=self.on_clear_logs)

        action_bar.add_widget(self.mic_btn)
        action_bar.add_widget(clear_btn)
        root.add_widget(action_bar)

        Clock.schedule_once(lambda dt: request_android_permissions(), 1.0)
        return root

    def append_log(self, text: str):
        Clock.schedule_once(
            lambda dt: setattr(
                self.output_label,
                'text',
                self.output_label.text + "\n" + text
            )
        )

    def on_send_command(self, *args):
        query = self.cmd_input.text.strip()
        if not query: return
        self.cmd_input.text = ""
        self.append_log(f"\n[color=#38BDF8]❯ User:[/color] {query}")
        
        if hasattr(self.engine, "db"):
            self.engine.db.set("last_user_query", query)
            self.engine.db.log_event("USER_COMMAND", {"text": query})

        cmd_lower = query.lower()
        if any(w in cmd_lower for w in ["open", "launch", "kholo", "chalao", "khol do", "chalu karo"]):
            app_name = "youtube"
            for target in ["youtube", "chrome", "whatsapp", "settings", "calculator", "camera"]:
                if target in cmd_lower:
                    app_name = target
                    break
            pkg_map = {
                "youtube": "com.google.android.youtube",
                "chrome": "com.android.chrome",
                "whatsapp": "com.whatsapp",
                "settings": "com.android.settings",
                "calculator": "com.google.android.calculator",
                "camera": "com.sec.android.app.camera"
            }
            pkg = pkg_map.get(app_name, f"com.google.android.{app_name}")
            res = self.engine.actions.execute_action(ActionItem(action_type=ActionType.OPEN_APP, params={"package": pkg}))
            reply = f"{app_name} खोला जा रहा है..." if res.success else f"{app_name} शुरू नहीं हो सका।"
            self.append_log(f"[color=#10B981]✦ Julie:[/color] {reply}")
            if hasattr(self.engine, "voice"):
                self.engine.voice.speak(reply)
        elif any(w in cmd_lower for w in ["code", "python", "likho", "banao", "program"]):
            topic = query.replace("code", "").replace("likho", "").replace("banao", "").replace("python", "").strip() or "task"
            code_reply = f"# --- JULIE Generated Code ---\ndef {topic.replace(' ', '_')}():\n    print('Running {topic}')\n\n{topic.replace(' ', '_')}()"
            self.append_log(f"[color=#10B981]✦ Julie:[/color] Python code generated for '{topic}':\n[color=#94A3B8]{code_reply}[/color]")
            if hasattr(self.engine, "voice"):
                self.engine.voice.speak(f"{topic} का कोड तैयार है।")
        elif "status" in cmd_lower or "halat" in cmd_lower:
            st = self.engine.status()
            reply = f"Status: Running={st['running']}, Version={st['version']}, Engines={st['components']}"
            self.append_log(f"[color=#10B981]✦ Julie:[/color] {reply}")
            if hasattr(self.engine, "voice"):
                self.engine.voice.speak("सभी सिस्टम इंजन सक्रिय और ऑनलाइन हैं।")
        else:
            reply = f"कमांड प्राप्त हुई: '{query}'"
            self.append_log(f"[color=#10B981]✦ Julie:[/color] {reply}")
            if hasattr(self.engine, "voice"):
                self.engine.voice.speak(reply)

    def on_mic_toggle(self, *args):
        self.mic_btn.text = "🎙️ [Listening...] बोलिए..."
        self.mic_btn.background_color = get_color_from_hex("#EF4444")
        self.append_log("\n[color=#F59E0B]🎙️ [JULIE MIC] सुन रही हूँ... बोलिए...[/color]")
        
        def start_listening_now(has_perm):
            if not has_perm:
                self.reset_mic_btn()
                self.append_log("[color=#EF4444]* माइक्रोफ़ोन अनुमति (Microphone Permission) आवश्यक है।[/color]")
                return
            if hasattr(self.engine, "voice"):
                self.engine.voice.start_listening(
                    callback=self.on_speech_result,
                    error_callback=self.on_speech_error
                )

        request_android_permissions(start_listening_now)

    @mainthread
    def reset_mic_btn(self):
        self.mic_btn.text = "[ MIC ]   Tap to Speak (JULIE)"
        self.mic_btn.background_color = get_color_from_hex("#10B981")

    @mainthread
    def on_speech_result(self, text: str):
        self.reset_mic_btn()
        if text:
            self.append_log(f"[color=#38BDF8]🗣️ Heard:[/color] '{text}'")
            self.cmd_input.text = text
            self.on_send_command()
        else:
            self.append_log("[color=#94A3B8]* कोई आवाज़ नहीं सुनी गई।[/color]")

    @mainthread
    def on_speech_error(self, err: str):
        self.reset_mic_btn()
        self.append_log(f"[color=#EF4444]* वॉयस सूचना:[/color] {err}")

    def on_clear_logs(self, *args):
        self.output_label.text = "[color=#10B981]* Logs cleared. System Online.[/color]"

    def on_stop(self):
        if hasattr(self, "engine"):
            self.engine.stop()

if __name__ == "__main__":
    JulieApp().run()
