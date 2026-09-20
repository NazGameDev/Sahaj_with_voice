"""
typing_modes.py — Pluggable typing modes for সহজ-Sahaj.

Adds two alternative typing modes to the main application:
  * InScript   — physical keyboard mapped to Assamese + on-screen keyboard.
  * Mouse      — click-to-insert Assamese letters panel.

Both windows follow the app's light / dark theme.
"""
import sys
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame,
    QApplication,
)
from PyQt6.QtCore import Qt, QPoint, QEvent, pyqtSignal, QObject


# ==================================================================
# Theme palette
# ==================================================================
THEME_COLORS = {
    "dark": {
        "window_bg":        "#2C2C2C",
        "window_border":    "#666666",
        "title_color":      "#EEEEEE",
        "key_bg":           "#3C3C3C",
        "key_fg":           "#E0E0E0",
        "key_border":       "#555555",
        "key_hover_bg":     "#505050",
        "key_hover_border": "#888888",
        "key_pressed_bg":   "#0D6EFD",
        "key_pressed_fg":   "#FFFFFF",
        "special_bg":       "#444444",
        "special_fg":       "#EEEEEE",
        "shift_bg":         "#5A6268",
        "enter_bg":         "#198754",
        "backspace_bg":     "#DC3545",
        "shift_active_bg":  "#FD7E14",
        "divider":          "#666666",
    },
    "light": {
        "window_bg":        "#F8F9FA",
        "window_border":    "#CED4DA",
        "title_color":      "#333333",
        "key_bg":           "#FFFFFF",
        "key_fg":           "#333333",
        "key_border":       "#CED4DA",
        "key_hover_bg":     "#E9ECEF",
        "key_hover_border": "#86B7FE",
        "key_pressed_bg":   "#0D6EFD",
        "key_pressed_fg":   "#FFFFFF",
        "special_bg":       "#E9ECEF",
        "special_fg":       "#333333",
        "shift_bg":         "#DEE2E6",
        "enter_bg":         "#198754",
        "backspace_bg":     "#DC3545",
        "shift_active_bg":  "#FD7E14",
        "divider":          "#CED4DA",
    },
}


def _colors(theme):
    return THEME_COLORS.get(theme, THEME_COLORS["dark"])


def _close_button_style(c=None):
    """Solid red circle with white ✕ — clearly visible on any theme."""
    return """
        QPushButton {
            background-color: #DC3545;
            color: #FFFFFF;
            border: none;
            border-radius: 11px;
            font-weight: bold;
            font-size: 13px;
            padding: 0px;
        }
        QPushButton:hover {
            background-color: #E4606D;
        }
        QPushButton:pressed {
            background-color: #BB2D3B;
        }
    """


# ==================================================================
# 1. InScript physical-key mapping
# ==================================================================
INSCRIPT_MAP = {
    "`": "॥",  "~": "~",
    "1": "১",  "!": "!",
    "2": "২",  "@": "@",
    "3": "৩",  "#": "্ৰ",
    "4": "৪",  "$": "ৰ্",
    "5": "৫",  "%": "জ্ঞ",
    "6": "৬",  "^": "ত্ৰ",
    "7": "৭",  "&": "ক্ষ",
    "8": "৮",  "*": "শ্ৰ",
    "9": "৯",  "(": "(",
    "0": "০",  ")": ")",
    "-": "-",  "_": "ঃ",
    "=": "ৃ",  "+": "ঋ",
    "q": "ৌ",  "Q": "ঔ",
    "w": "ৈ",  "W": "ঐ",
    "e": "া",  "E": "আ",
    "r": "ী",  "R": "ঈ",
    "t": "ূ",  "T": "ঊ",
    "y": "ব",  "Y": "ভ",
    "u": "হ",  "U": "ঙ",
    "i": "গ",  "I": "ঘ",
    "o": "দ",  "O": "ধ",
    "p": "জ",  "P": "ঝ",
    "[": "ড",  "{": "ঢ",
    "]": "়",  "}": "ঞ",
    "\\": "\\", "|": "|",
    "a": "ো",  "A": "ও",
    "s": "ে",  "S": "এ",
    "d": "্",  "D": "অ",
    "f": "ি",  "F": "ই",
    "g": "ু",  "G": "উ",
    "h": "প",  "H": "ফ",
    "j": "ৰ",  "J": "",
    "k": "ক",  "K": "খ",
    "l": "ত",  "L": "থ",
    ";": "চ",  ":": "ছ",
    "'": "ট",  "\"": "ঠ",
    "z": "",   "Z": "",
    "x": "ং",  "X": "ঁ",
    "c": "ম",  "C": "ণ",
    "v": "ন",  "V": "",
    "b": "ৱ",  "B": "",
    "n": "ল",  "N": "",
    "m": "স",  "M": "শ",
    ",": ",",  "<": "ষ",
    ".": ".",  ">": "।",
    "/": "য়",  "?": "য",
}


# ==================================================================
# 2. InScript keyboard layout
# ==================================================================
KEYBOARD_ROWS = [
    [
        ("`",  "॥", "~",  1, None),
        ("1",  "১", "!",  1, None),
        ("2",  "২", "@",  1, None),
        ("3",  "৩", "্ৰ", 1, None),
        ("4",  "৪", "ৰ্", 1, None),
        ("5",  "৫", "জ্ঞ", 1, None),
        ("6",  "৬", "ত্ৰ", 1, None),
        ("7",  "৭", "ক্ষ", 1, None),
        ("8",  "৮", "শ্ৰ", 1, None),
        ("9",  "৯", "(",  1, None),
        ("0",  "০", ")",  1, None),
        ("-",  "-", "ঃ",  1, None),
        ("=",  "ৃ", "ঋ",  1, None),
        ("⌫", "⌫", "⌫",  2, "backspace"),
    ],
    [
        ("⇥",  "⇥", "⇥",  1.5, "tab"),
        ("q",  "ৌ", "ঔ",  1, None),
        ("w",  "ৈ", "ঐ",  1, None),
        ("e",  "া", "আ",  1, None),
        ("r",  "ী", "ঈ",  1, None),
        ("t",  "ূ", "ঊ",  1, None),
        ("y",  "ব", "ভ",  1, None),
        ("u",  "হ", "ঙ",  1, None),
        ("i",  "গ", "ঘ",  1, None),
        ("o",  "দ", "ধ",  1, None),
        ("p",  "জ", "ঝ",  1, None),
        ("[",  "ড", "ঢ",  1, None),
        ("]",  "়", "ঞ",  1, None),
        ("\\", "\\", "|", 1.5, None),
    ],
    [
        ("⇪",  "⇪", "⇪",  1.75, "caps"),
        ("a",  "ো", "ও",  1, None),
        ("s",  "ে", "এ",  1, None),
        ("d",  "্", "অ",  1, None),
        ("f",  "ি", "ই",  1, None),
        ("g",  "ু", "উ",  1, None),
        ("h",  "প", "ফ",  1, None),
        ("j",  "ৰ", "",   1, None),
        ("k",  "ক", "খ",  1, None),
        ("l",  "ত", "থ",  1, None),
        (";",  "চ", "ছ",  1, None),
        ("'",  "ট", "ঠ",  1, None),
        ("⏎",  "⏎", "⏎",  2.25, "enter"),
    ],
    [
        ("⇧",  "⇧", "⇧",  2.5, "shift"),
        ("z",  "",  "",   1, None),
        ("x",  "ং", "ঁ",  1, None),
        ("c",  "ম", "ণ",  1, None),
        ("v",  "ন", "",   1, None),
        ("b",  "ৱ", "",   1, None),
        ("n",  "ল", "",   1, None),
        ("m",  "স", "শ",  1, None),
        (",",  ",", "ষ",  1, None),
        (".",  ".", "।",  1, None),
        ("/",  "য়", "য",  1, None),
        ("⇧",  "⇧", "⇧",  2.5, "shift"),
    ],
    [
        ("Ctrl", "Ctrl", "Ctrl", 1.5, "ctrl"),
        ("Alt",  "Alt",  "Alt",  1.5, "alt"),
        ("",     " ",    " ",   9.0, "space"),
        ("Alt",  "Alt",  "Alt",  1.5, "alt"),
        ("Ctrl", "Ctrl", "Ctrl", 1.5, "ctrl"),
    ],
]

UNIT_W = 55
UNIT_H = 58
SPACING = 5


# ==================================================================
# 3. Mouse Typing data
# ==================================================================
MOUSE_TYPING_LEFT = [
    [("ক", "ক"), ("খ", "খ"), ("গ", "গ"), ("ঘ", "ঘ"), ("ঙ", "ঙ"),
     None, ("ৰ্", "ৰ্")],
    [("চ", "চ"), ("ছ", "ছ"), ("জ", "জ"), ("ঝ", "ঝ"), ("ঞ", "ঞ"),
     None, ("ৎ", "ৎ")],
    [("ট", "ট"), ("ঠ", "ঠ"), ("ড", "ড"), ("ঢ", "ঢ"), ("ণ", "ণ")],
    [("ত", "ত"), ("থ", "থ"), ("দ", "দ"), ("ধ", "ধ"), ("ন", "ন")],
    [("প", "প"), ("ফ", "ফ"), ("ব", "ব"), ("ভ", "ভ"), ("ম", "ম")],
    [("য", "য"), ("ৰ", "ৰ"), ("ল", "ল"), ("ৱ", "ৱ"), ("শ", "শ"),
     ("ষ", "ষ"), ("স", "স"), ("হ", "হ")],
    [("ক্ষ", "ক্ষ"), ("ড়", "ড়"), ("ঢ়", "ঢ়"), ("য়", "য়")],
]

MOUSE_TYPING_RIGHT = [
    [("অ", "অ"), ("আ", "আ"), ("ই", "ই"), ("ঈ", "ঈ"), ("উ", "উ"), ("ঊ", "ঊ")],
    [("◌া", "া"), ("◌ি", "ি"), ("◌ী", "ী"), ("◌ু", "ু"), ("◌ূ", "ূ")],
    [("ঋ", "ঋ"), ("ৠ", "ৠ"), ("ঌ", "ঌ"), ("ৡ", "ৡ"),
     ("এ", "এ"), ("ঐ", "ঐ"), ("ও", "ও"), ("ঔ", "ঔ")],
    [("◌ৃ", "ৃ"), ("◌ৄ", "ৄ"), ("◌ৢ", "ৢ"), ("◌ৣ", "ৣ"),
     ("◌ে", "ে"), ("◌ৈ", "ৈ"), ("◌ো", "ো"), ("◌ৌ", "ৌ")],
    [("◌ঁ", "ঁ"), ("◌ঃ", "ঃ"), ("◌ং", "ং"), ("◌্", "্")],
]


# ==================================================================
# 4. InScript keyboard window
# ==================================================================
class InScriptKeyboardWindow(QDialog):
    key_clicked = pyqtSignal(str)
    special_key = pyqtSignal(str)

    def __init__(self, parent=None, theme="dark"):
        super().__init__(parent)
        self.setWindowTitle("InScript Assamese Keyboard")
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.theme = theme
        self._drag_position = QPoint()
        self._shift_state = False
        self._software_shift = False
        self._key_buttons = []
        self.title_label = None
        self.close_btn = None

        self._build_ui()
        self._apply_stylesheet()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    # ---------------------------------------------------------
    def set_theme(self, theme):
        self.theme = theme
        self._apply_stylesheet()
        self._refresh_all_buttons()

    def _apply_stylesheet(self):
        c = _colors(self.theme)
        self.setStyleSheet(f"""
            InScriptKeyboardWindow {{
                background-color: {c['window_bg']};
                border: 2px solid {c['window_border']};
                border-radius: 10px;
            }}
        """)
        if self.title_label:
            self.title_label.setStyleSheet(
                f"color: {c['title_color']}; font-weight: bold; "
                f"padding: 4px; font-size: 13px;"
            )
        if self.close_btn:
            self.close_btn.setStyleSheet(_close_button_style(c))

    # ---------------------------------------------------------
    def eventFilter(self, obj, event):
        etype = event.type()
        if etype in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            if event.key() == Qt.Key.Key_Shift:
                is_pressed = (etype == QEvent.Type.KeyPress)
                if is_pressed != self._shift_state:
                    self._shift_state = is_pressed
                    self._refresh_all_buttons()
        return super().eventFilter(obj, event)

    # ---------------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        title_bar = QHBoxLayout()
        self.title_label = QLabel("⌨️  InScript Assamese — drag to move")
        title_bar.addWidget(self.title_label)
        title_bar.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.clicked.connect(self.hide)
        title_bar.addWidget(self.close_btn)
        main_layout.addLayout(title_bar)

        for row in KEYBOARD_ROWS:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(SPACING)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addStretch()
            for key_def in row:
                btn = self._make_key_button(key_def)
                row_layout.addWidget(btn)
            row_layout.addStretch()
            main_layout.addLayout(row_layout)

        self.adjustSize()

    # ---------------------------------------------------------
    def _make_key_button(self, key_def):
        label, normal, shifted, width_units, action = key_def
        btn = QPushButton()
        btn.setFixedSize(int(UNIT_W * width_units), UNIT_H)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn._key_def = key_def
        self._key_buttons.append(btn)

        if action == "shift":
            btn.clicked.connect(self._toggle_software_shift)
        elif action == "space":
            btn.clicked.connect(lambda: self.special_key.emit("space"))
        elif action == "backspace":
            btn.clicked.connect(lambda: self.special_key.emit("backspace"))
        elif action == "enter":
            btn.clicked.connect(lambda: self.special_key.emit("enter"))
        elif action in ("tab", "caps", "ctrl", "win", "alt", "menu"):
            pass
        else:
            btn.clicked.connect(lambda checked, b=btn: self._emit_char(b))

        self._refresh_button(btn)
        return btn

    # ---------------------------------------------------------
    def _char_key_style(self):
        c = _colors(self.theme)
        return f"""
            QPushButton {{
                background-color: {c['key_bg']};
                color: {c['key_fg']};
                border: 1px solid {c['key_border']};
                border-radius: 5px;
                font-size: 20px;
                font-family: "Nirmala UI", "Segoe UI", sans-serif;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: {c['key_hover_bg']};
                border-color: {c['key_hover_border']};
            }}
            QPushButton:pressed {{
                background-color: {c['key_pressed_bg']};
                color: {c['key_pressed_fg']};
            }}
        """

    def _special_key_style(self, action):
        c = _colors(self.theme)
        bg = c["special_bg"]
        fg = c["special_fg"]
        if action == "shift":
            bg = c["shift_bg"]
        elif action == "enter":
            bg = c["enter_bg"]
            fg = "#FFFFFF"
        elif action == "backspace":
            bg = c["backspace_bg"]
            fg = "#FFFFFF"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {c['key_border']};
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c['key_hover_bg']};
            }}
            QPushButton:pressed {{
                background-color: {c['key_pressed_bg']};
                color: {c['key_pressed_fg']};
            }}
        """

    def _shift_active_style(self):
        c = _colors(self.theme)
        return f"""
            QPushButton {{
                background-color: {c['shift_active_bg']};
                color: white;
                border: 1px solid {c['key_border']};
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }}
        """

    # ---------------------------------------------------------
    def _emit_char(self, btn):
        label, normal, shifted, _, action = btn._key_def
        if action is not None:
            return
        char = shifted if self._is_shift_active() else normal
        if not char:
            return
        self.key_clicked.emit(char)
        if self._software_shift:
            self._software_shift = False
            self._refresh_all_buttons()

    def _toggle_software_shift(self):
        self._software_shift = not self._software_shift
        self._refresh_all_buttons()

    def _is_shift_active(self):
        return self._shift_state or self._software_shift

    # ---------------------------------------------------------
    def _refresh_all_buttons(self):
        for btn in self._key_buttons:
            self._refresh_button(btn)

    def _refresh_button(self, btn):
        label, normal, shifted, _, action = btn._key_def

        if action in ("shift", "caps", "tab", "enter", "backspace", "space",
                      "ctrl", "win", "alt", "menu"):
            if action == "space":
                btn.setText("Space")
            else:
                btn.setText(label)
            if action == "shift":
                if self._is_shift_active():
                    btn.setStyleSheet(self._shift_active_style())
                else:
                    btn.setStyleSheet(self._special_key_style("shift"))
            else:
                btn.setStyleSheet(self._special_key_style(action))
            return

        char = shifted if self._is_shift_active() else normal
        if char:
            btn.setText(f"{char}\n{label}")
        else:
            btn.setText("")
        btn.setToolTip(
            f"Key: {label}\nNormal: {normal or '(blank)'}\n"
            f"Shifted: {shifted or '(blank)'}"
        )
        btn.setStyleSheet(self._char_key_style())

    # ---------------------------------------------------------
    def closeEvent(self, event):
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()


# ==================================================================
# 5. Mouse Typing window
# ==================================================================
class MouseTypingWindow(QDialog):
    key_clicked = pyqtSignal(str)

    KEY_SIZE = 52
    KEY_SPACING = 5

    def __init__(self, parent=None, theme="dark"):
        super().__init__(parent)
        self.setWindowTitle("Mouse Typing — Assamese Alphabet")
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.theme = theme
        self._drag_position = QPoint()
        self.title_label = None
        self.close_btn = None
        self.divider = None
        self._build_ui()
        self._apply_stylesheet()

    # ---------------------------------------------------------
    def set_theme(self, theme):
        self.theme = theme
        self._apply_stylesheet()
        # Refresh every key button
        for btn in self.findChildren(QPushButton):
            if btn is self.close_btn:
                continue
            btn.setStyleSheet(self._key_style())

    def _apply_stylesheet(self):
        c = _colors(self.theme)
        self.setStyleSheet(f"""
            MouseTypingWindow {{
                background-color: {c['window_bg']};
                border: 2px solid {c['window_border']};
                border-radius: 10px;
            }}
        """)
        if self.title_label:
            self.title_label.setStyleSheet(
                f"color: {c['title_color']}; font-weight: bold; "
                f"padding: 4px; font-size: 13px;"
            )
        if self.close_btn:
            self.close_btn.setStyleSheet(_close_button_style(c))
        if self.divider:
            self.divider.setStyleSheet(
                f"color: {c['divider']}; background-color: {c['divider']};"
            )

    # ---------------------------------------------------------
    def _key_style(self):
        c = _colors(self.theme)
        return f"""
            QPushButton {{
                background-color: {c['key_bg']};
                color: {c['key_fg']};
                border: 1px solid {c['key_border']};
                border-radius: 6px;
                font-size: 16px;
                font-family: "Nirmala UI", "Segoe UI", sans-serif;
            }}
            QPushButton:hover {{
                background-color: {c['key_hover_bg']};
                border-color: {c['key_hover_border']};
            }}
            QPushButton:pressed {{
                background-color: {c['key_pressed_bg']};
                color: {c['key_pressed_fg']};
            }}
        """

    # ---------------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        title_bar = QHBoxLayout()
        self.title_label = QLabel("🖱️  Mouse Typing — click any letter")
        title_bar.addWidget(self.title_label)
        title_bar.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.clicked.connect(self.hide)
        title_bar.addWidget(self.close_btn)
        main_layout.addLayout(title_bar)

        content = QHBoxLayout()
        content.setSpacing(16)

        # Left: consonants
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(6)
        left_layout.setContentsMargins(0, 0, 0, 0)
        for row in MOUSE_TYPING_LEFT:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(self.KEY_SPACING)
            for entry in row:
                if entry is None:
                    spacer = QWidget()
                    spacer.setFixedSize(self.KEY_SIZE, self.KEY_SIZE)
                    row_layout.addWidget(spacer)
                else:
                    display, value = entry
                    row_layout.addWidget(self._make_button(display, value))
            row_layout.addStretch()
            left_layout.addLayout(row_layout)
        left_layout.addStretch()
        content.addWidget(left_widget)

        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.Shape.VLine)
        self.divider.setFrameShadow(QFrame.Shadow.Plain)
        self.divider.setFixedWidth(2)
        content.addWidget(self.divider)

        # Right: vowels
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(6)
        right_layout.setContentsMargins(0, 0, 0, 0)
        for row in MOUSE_TYPING_RIGHT:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(self.KEY_SPACING)
            for display, value in row:
                row_layout.addWidget(self._make_button(display, value))
            row_layout.addStretch()
            right_layout.addLayout(row_layout)
        right_layout.addStretch()
        content.addWidget(right_widget)

        main_layout.addLayout(content)
        self.adjustSize()

    # ---------------------------------------------------------
    def _make_button(self, display, value):
        btn = QPushButton(display)
        btn.setFixedSize(self.KEY_SIZE, self.KEY_SIZE)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setToolTip(f"Insert: {value}")
        btn.setStyleSheet(self._key_style())
        btn.clicked.connect(lambda checked, v=value: self.key_clicked.emit(v))
        return btn

    # ---------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()


# ==================================================================
# 6. Manager — the only thing main.py talks to
# ==================================================================
class TypingModeManager(QObject):
    """
    Hooks InScript / Mouse-Typing windows onto an existing text editor.
    """
    def __init__(self, main_window, text_editor, theme="dark"):
        super().__init__(main_window)
        self.main_window = main_window
        self.text_editor = text_editor
        self.theme = theme

        self.inscript_window = None
        self.mouse_window = None
        self.current_mode = "none"

        self.text_editor.installEventFilter(self)

    # ----- public -----
    def set_mode(self, mode):
        if mode == self.current_mode:
            return
        self.current_mode = mode

        self._hide_inscript()
        self._hide_mouse()

        if mode == "inscript":
            self._show_inscript()
        elif mode == "mouse":
            self._show_mouse()

    def set_theme(self, theme):
        """Called from main.toggle_theme() so live windows follow the theme."""
        self.theme = theme
        if self.inscript_window is not None:
            self.inscript_window.set_theme(theme)
        if self.mouse_window is not None:
            self.mouse_window.set_theme(theme)

    def shutdown(self):
        self._hide_inscript()
        self._hide_mouse()
        try:
            self.text_editor.removeEventFilter(self)
        except Exception:
            pass

    # ----- internals -----
    def _show_inscript(self):
        if self.inscript_window is None:
            self.inscript_window = InScriptKeyboardWindow(
                self.main_window, theme=self.theme
            )
            self.inscript_window.key_clicked.connect(self._insert_text)
            self.inscript_window.special_key.connect(self._handle_special)
        self._position_window(self.inscript_window)
        self.inscript_window.show()
        self.inscript_window.raise_()
        self.text_editor.setFocus()

    def _hide_inscript(self):
        if self.inscript_window is not None:
            self.inscript_window.hide()

    def _show_mouse(self):
        if self.mouse_window is None:
            self.mouse_window = MouseTypingWindow(
                self.main_window, theme=self.theme
            )
            self.mouse_window.key_clicked.connect(self._insert_text)
        self._position_window(self.mouse_window)
        self.mouse_window.show()
        self.mouse_window.raise_()
        self.text_editor.setFocus()

    def _hide_mouse(self):
        if self.mouse_window is not None:
            self.mouse_window.hide()

    def _position_window(self, win):
        try:
            geo = self.main_window.geometry()
            w = win.sizeHint().width()
            h = win.sizeHint().height()
            x = geo.x() + (geo.width() - w) // 2
            y = geo.y() + geo.height() - h - 80
            win.move(max(0, x), max(0, y))
        except Exception:
            pass

    def _insert_text(self, text):
        if not text:
            return
        self.text_editor.insertPlainText(text)
        self.text_editor.setFocus()

    def _handle_special(self, key):
        if key == "space":
            self.text_editor.insertPlainText(" ")
        elif key == "backspace":
            cursor = self.text_editor.textCursor()
            cursor.deletePreviousChar()
        elif key == "enter":
            self.text_editor.insertPlainText("\n")
        self.text_editor.setFocus()

    # ----- key hook -----
    def eventFilter(self, obj, event):
        if obj is self.text_editor and event.type() == QEvent.Type.KeyPress:
            if self.current_mode == "inscript":
                return self._handle_inscript_keypress(event)
        return super().eventFilter(obj, event)

    def _handle_inscript_keypress(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.text_editor.insertPlainText(" ")
            return True

        if event.key() in (
            Qt.Key.Key_Backspace, Qt.Key.Key_Delete,
            Qt.Key.Key_Left, Qt.Key.Key_Right,
            Qt.Key.Key_Up, Qt.Key.Key_Down,
            Qt.Key.Key_Home, Qt.Key.Key_End,
            Qt.Key.Key_Return, Qt.Key.Key_Enter,
            Qt.Key.Key_Tab,
        ):
            return False

        key = event.text()
        if key and key in INSCRIPT_MAP:
            char = INSCRIPT_MAP[key]
            if char:
                self.text_editor.insertPlainText(char)
            return True

        return True
