import board
import digitalio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode


def setup():
    keyboard = Keyboard(usb_hid.devices)

    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT

    button = digitalio.DigitalInOut(board.GP22)
    button.switch_to_input(pull=digitalio.Pull.DOWN)

    led.value = True

    return (keyboard, led, button)


def press_and_release(kbd, keycode):
    kbd.press(keycode)
    time.sleep(0.02)
    kbd.release(keycode)
    time.sleep(0.02)


def loop(keyboard, led, button):
    state = False

    while True:
        if button.value:
            if not state:
                state = True
                print("Push!")
                keyboard.press(Keycode.ALT)
                press_and_release(keyboard, Keycode.PRINT_SCREEN)
                press_and_release(keyboard, Keycode.R)
                press_and_release(keyboard, Keycode.E)
                press_and_release(keyboard, Keycode.I)
                press_and_release(keyboard, Keycode.S)
                press_and_release(keyboard, Keycode.U)
                press_and_release(keyboard, Keycode.B)
                keyboard.release(Keycode.ALT)
                time.sleep(0.02)
                keyboard.press(Keycode.CONTROL, Keycode.ALT, Keycode.DELETE)
            led.value = False
            time.sleep(0.02)
            led.value = True
            time.sleep(0.02)
        if state and not button.value:
            state = False
            print("Release!")
            keyboard.release_all()


def main():
    while True:
        keyboard, led, button = setup()

        try:
            loop(keyboard, led, button)
        except BaseException as exc:
            # Clean up as best as we can ...
            led.deinit()
            button.deinit()
            try:
                keyboard.release_all()
            except:
                pass

            # Report the error, not that I know how to use the debug circuit on the pico, but whatever
            print(type(exc).__name__, exc)

            # Very important, without this, we'll brick circuitpython...!
            if not isinstance(exc, Exception):
                # This is something serious, like KeyboardInterrupt or SystemExit,
                # And we ought not intercept it... we can brick Thonny/CircuitPython otherwise...!
                raise


if __name__ == '__main__':
    main()
