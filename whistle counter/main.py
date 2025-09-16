from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

import winsound  # for alarm sound on Windows

from desktop_audio import DesktopAudioListener


class WhistleApp(App):
    def build(self):
        # Audio listener
        self.listener = DesktopAudioListener()

        # Counter & target
        self.counter = 0
        self.target_count = 5  # default

        # Layout
        self.layout = BoxLayout(orientation="vertical", padding=20, spacing=20)

        # Whistle counter label
        self.label = Label(text="Whistle Counter: 0", font_size=28)
        self.layout.add_widget(self.label)

        # Volume label
        self.volume_label = Label(text="Volume: 0", font_size=20)
        self.layout.add_widget(self.volume_label)

        # Volume progress bar
        self.volume_bar = ProgressBar(max=100)
        self.layout.add_widget(self.volume_bar)

        # Target count input
        self.target_input = TextInput(
            text=str(self.target_count),
            hint_text="Enter target whistle count",
            multiline=False,
            font_size=20,
            size_hint=(1, 0.2),
        )
        self.layout.add_widget(self.target_input)

        # Start button
        self.start_btn = Button(text="Start Listening", size_hint=(1, 0.2))
        self.start_btn.bind(on_press=self.start_listening)
        self.layout.add_widget(self.start_btn)

        # Stop button
        self.stop_btn = Button(text="Stop Listening", size_hint=(1, 0.2))
        self.stop_btn.bind(on_press=self.stop_listening)
        self.layout.add_widget(self.stop_btn)

        return self.layout

    def start_listening(self, instance):
        self.counter = 0
        self.label.text = "Whistle Counter: 0"

        # Read target from input
        try:
            self.target_count = int(self.target_input.text.strip())
        except ValueError:
            self.target_count = 5  # fallback default
            self.target_input.text = "5"

        self.listener.start(self.on_whistle, self.on_volume)

    def stop_listening(self, instance):
        self.listener.stop()

    def on_whistle(self):
        """Called when a whistle is detected"""
        self.counter += 1
        Clock.schedule_once(lambda dt: self.update_counter())

        # Trigger alarm when target is reached
        if self.counter >= self.target_count:
            self.trigger_alarm()

    def on_volume(self, rms):
        """Update volume meter"""
        level = min(100, int(rms * 5000))
        Clock.schedule_once(lambda dt: setattr(self.volume_bar, "value", level))
        Clock.schedule_once(
            lambda dt: setattr(self.volume_label, "text", f"Volume: {level}")
        )

    def update_counter(self):
        self.label.text = f"Whistle Counter: {self.counter}"

    def trigger_alarm(self):
        """Play alarm sound + show popup"""
        winsound.Beep(1000, 1000)  # frequency 1000Hz, duration 1 sec

        popup = Popup(
            title="Whistle Alarm 🚨",
            content=Label(text=f"{self.target_count} whistles reached!"),
            size_hint=(0.6, 0.4),
        )
        popup.open()


if __name__ == "__main__":
    WhistleApp().run()
