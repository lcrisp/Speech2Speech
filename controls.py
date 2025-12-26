from pynput import keyboard
from load_conf import EXIT_KEY, INJECT_KEY, THEN_KEY

KEYMAP = {"esc": keyboard.Key.esc, "enter": keyboard.Key.enter, "space": keyboard.Key.space, "tab": keyboard.Key.tab}

def _parse_key(name: str):
    name = (name or "").lower().strip()
    if name in KEYMAP:
        return KEYMAP[name]
    if len(name) == 1:
        return keyboard.KeyCode.from_char(name)
    return keyboard.Key.esc

class Controls:
    def __init__(self):
        self.exit_pressed = False
        self.inject_pressed = False
        self.then_pressed = False
        self._exit_key = _parse_key(EXIT_KEY)
        self._inject_key = _parse_key(INJECT_KEY)
        self._then_key = _parse_key(THEN_KEY)
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.daemon = True
        self.listener.start()

    def _on_press(self, key):
        if key == self._exit_key:
            self.exit_pressed = True
        if key == self._inject_key:
            self.inject_pressed = True
        if key == self._then_key:
            self.then_pressed = True

    def check_exit(self) -> bool:
        return self.exit_pressed
