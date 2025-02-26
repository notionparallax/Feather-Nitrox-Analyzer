import random
import time
import math
import board
import digitalio
import displayio
import terminalio
import storage
from adafruit_display_text import label
from adafruit_debouncer import Debouncer

display = board.DISPLAY

# Define button pins
button1_pin = digitalio.DigitalInOut(board.BUTTON)
button1_pin.direction = digitalio.Direction.INPUT
button1_pin.pull = digitalio.Pull.UP
button1 = Debouncer(button1_pin)


button2_pin = digitalio.DigitalInOut(board.D1)
button2_pin.direction = digitalio.Direction.INPUT
button2_pin.pull = digitalio.Pull.DOWN
button2 = Debouncer(button2_pin)

button3_pin = digitalio.DigitalInOut(board.D2)
button3_pin.direction = digitalio.Direction.INPUT
button3_pin.pull = digitalio.Pull.DOWN
button3 = Debouncer(button3_pin)

# Define states
SLEEP = 0
ANALYSE = 1
CALIBRATE = 2
HISTORY = 3

state = SLEEP
last_state = None

o2_pc = 101  # impossible number to start with


def draw_screen(
    display=display,
    texts=["Please Hammer,", "Don't hurt em!", "Stop! Hammertime!"],
    buttons=["A", "B", "C"],
    border=20,
    fontscale=2,
    background_colour=0x00FF00,  # Bright Green
    foreground_colour=0xAA0088,  # Purple
    text_colour=0xFFFF00,
):
    # Make the display context
    splash = displayio.Group()
    display.root_group = splash
    parts = []

    color_bitmap = displayio.Bitmap(display.width, display.height, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = foreground_colour

    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    parts.append(bg_sprite)

    # Draw a label
    for i, text in enumerate(texts):
        text_area = label.Label(terminalio.FONT, text=text, color=text_colour)
        text_width = text_area.bounding_box[2] * fontscale
        text_group = displayio.Group(
            scale=fontscale,
            x=display.width // 2 - text_width // 2,
            y=(display.height // (len(texts) + 1)) * (i + 1),
        )
        text_group.append(text_area)  # Subgroup for text scaling
        parts.append(text_group)

    # Button labels
    button_positions = [8, display.height // 2 + 4, display.height - 10]
    for i, text in enumerate(buttons):
        text_area = label.Label(terminalio.FONT, text=text, color=text_colour)
        text_width = text_area.bounding_box[2] * fontscale
        text_group = displayio.Group(
            scale=int(fontscale * 0.8),
            x=2,
            y=button_positions[i],
        )
        text_group.append(text_area)  # Subgroup for text scaling
        parts.append(text_group)

    for p in parts:
        splash.append(p)


def draw_sleep_screen():
    draw_screen(
        texts=["SLEEPING", "zzzzzzzzzz"],
        buttons=["wake", ".", "."],
    )


def calculate_mod(o2_percentage, pp_o2_max=1.6, give_int=True):
    """Calculates the maximum operating depth of a gas mixture,
    given the fraction of O2 and maximum partial pressure of O2."""
    oxygen_fraction = o2_percentage / 100
    mod = 10 * ((pp_o2_max / oxygen_fraction) - 1)
    if give_int:
        return math.ceil(mod)
    return mod


def draw_analyse_screen():
    global o2_pc
    # random O2, with decimal section
    o2_pc = random.randrange(19, 75) + random.random()

    draw_screen(
        texts=[
            f"O2: {o2_pc:.1f}%",
            f"MOD 1.4: {calculate_mod(o2_pc, pp_o2_max=1.4)}m",
            f"MOD 1.6: {calculate_mod(o2_pc, pp_o2_max=1.6)}m",
            f"Battery: {3+random.random():.1f}V",
            f"Sensor: {random.random()*5:.2f}V",
            "FAKE!!!!",
        ],
        buttons=[
            "Calibrate",
            "History",
            "Sleep",
        ],
    )


def draw_calibrate_screen():
    draw_screen(
        texts=["CALIBRATING", "Please wait"],
    )
    time.sleep(2)


def draw_history_screen():
    draw_screen(
        texts=[
            "O2%  Time      MOD",
            "21%  10:00:25  56m",
            "20%  09:45:01  54m",
            "19%  09:30:45  53m",
        ],
        buttons=[
            "up",
            "bk",
            "dn",
        ],
    )


class StateMachine:
    def __init__(self):
        self.state = SLEEP

    def on_event(self, event):
        if self.state == SLEEP:
            if event == "button1_pressed":
                self.state = ANALYSE
        elif self.state == ANALYSE:
            if event == "button1_pressed":
                self.state = CALIBRATE
                print("Changing state to CALIBRATE")
            elif event == "button2_pressed":
                self.state = HISTORY
                print("Changing state to HISTORY")
            elif event == "button3_pressed":
                self.state = SLEEP
                print("Changing state to SLEEP")
        elif self.state == HISTORY:
            if event == "button1_pressed":
                self.scroll_up()
            elif event == "button2_pressed":
                self.state = ANALYSE
                print("Changing state to ANALYSE")
            elif event == "button3_pressed":
                self.scroll_down()
        elif self.state == CALIBRATE:
            if (
                event == "button1_pressed"
                or event == "button2_pressed"
                or event == "button3_pressed"
            ):
                self.state = ANALYSE
                print("Changing state to ANALYSE")

    def scroll_up(self):
        print("Scrolling up in history")

    def scroll_down(self):
        print("Scrolling down in history")


state_machine = StateMachine()


def handle_buttons():
    button1.update()
    button2.update()
    button3.update()

    if button1.fell:
        print("Button 1 pressed")
        state_machine.on_event("button1_pressed")
    if button2.fell:
        print("Button 2 pressed")
        state_machine.on_event("button2_pressed")
    if button3.fell:
        print("Button 3 pressed")
        state_machine.on_event("button3_pressed")


while True:
    handle_buttons()
    if state_machine.state != last_state:
        print(f"State changed to {state_machine.state}")
        if state_machine.state == SLEEP:
            draw_sleep_screen()
        elif state_machine.state == ANALYSE:
            draw_analyse_screen()
        elif state_machine.state == CALIBRATE:
            draw_calibrate_screen()
        elif state_machine.state == HISTORY:
            draw_history_screen()
        last_state = state_machine.state
    time.sleep(0.1)
