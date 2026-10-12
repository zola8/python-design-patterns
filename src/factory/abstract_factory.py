# 1. The Product (The Button)
# First, define what a button is.

class Button:
    def __init__(self, color, text_color):
        self.color = color
        self.text_color = text_color

    def render(self):
        return f"[Button: BG={self.color}, Text={self.text_color}]"


# 2. The Abstract Factory (The Blueprint)
# This defines what the factory must be able to do. It doesn't create anything yet; it just sets the rules.

from abc import ABC
from abc import abstractmethod


class ThemeFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button:
        pass


# 3. The Concrete Factories (The Makers)
# These are the actual factories that make the specific styles.

# Factory for Light Mode
class LightThemeFactory(ThemeFactory):
    def create_button(self) -> Button:
        return Button(color="White", text_color="Black")


# Factory for Dark Mode
class DarkThemeFactory(ThemeFactory):
    def create_button(self) -> Button:
        return Button(color="Black", text_color="White")


def show_ui(factory: ThemeFactory):
    btn = factory.create_button()
    print(btn.render())


if __name__ == '__main__':
    light_factory = LightThemeFactory()
    show_ui(light_factory)

    dark_factory = DarkThemeFactory()
    show_ui(dark_factory)
