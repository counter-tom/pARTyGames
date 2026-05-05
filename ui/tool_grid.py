import pygame
from core.color import Color


class ToolGridButton:
    def __init__(self, rect, tool, action, image_path=None, selected_image_path=None, label=""):
        self.rect = pygame.Rect(rect)
        self.tool = tool
        self.action = action
        self.label = label

        self.image = None
        self.selected_image = None

        if image_path:
            try:
                img = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(img, (48, 48))
            except Exception as e:
                print(f"Error loading image: {e}")

        if selected_image_path:
            try:
                img = pygame.image.load(selected_image_path).convert_alpha()
                self.selected_image = pygame.transform.scale(img, (48, 48))
            except Exception as e:
                print(f"Error loading selected image: {e}")

    def check_hover(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.check_hover():
                self.action()
                return True
        return False

    def draw(self, screen, font, selected=False):
        if selected:
            bg = (120, 160, 255)
        elif self.check_hover():
            bg = (90, 90, 120)
        else:
            bg = (60, 60, 90)

        pygame.draw.rect(screen, bg, self.rect, 0, 8)
        pygame.draw.rect(screen, (200, 200, 255), self.rect, 2, 8)

        if selected and self.selected_image:
            img = self.selected_image
        else:
            img = self.image

        if img:
            x = self.rect.centerx - img.get_width() // 2
            y = self.rect.centery - img.get_height() // 2
            screen.blit(img, (x, y))
        else:
            text = font.render(self.label, True, (255, 255, 255))
            screen.blit(
                text,
                (
                    self.rect.centerx - text.get_width() // 2,
                    self.rect.centery - text.get_height() // 2,
                ),
            )


class ToolGrid:
    def __init__(self, screen, x, y, font, columns=3, button_size=64, gap=8):
        self.screen = screen
        self.x = x
        self.y = y
        self.font = font
        self.columns = columns
        self.button_size = button_size
        self.gap = gap
        self.buttons = []
        self.is_hovering_ui = False

    def add_tool(self, tool, action, image_path=None, selected_image_path=None, label=""):
        index = len(self.buttons)
        col = index % self.columns
        row = index // self.columns

        rect = pygame.Rect(
            self.x + col * (self.button_size + self.gap),
            self.y + row * (self.button_size + self.gap),
            self.button_size,
            self.button_size
        )

        self.buttons.append(
            ToolGridButton(
                rect,
                tool,
                action,
                image_path=image_path,
                selected_image_path=selected_image_path,
                label=label
            )
        )

    def update(self):
        self.is_hovering_ui = any(button.check_hover() for button in self.buttons)

    def handle_events(self, event):
        for button in self.buttons:
            if button.handle_event(event):
                return True
        return False

    def draw(self, current_tool):
        for button in self.buttons:
            button.draw(
                self.screen,
                self.font,
                selected=(button.tool == current_tool)
            )
