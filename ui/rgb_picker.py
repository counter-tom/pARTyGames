import pygame
from core.color import Color


class RGBPicker:
    def __init__(self, screen, x, y, font):
        self.screen = screen
        self.x = x
        self.y = y
        self.font = font

        self.bar_width = 40
        self.bar_height = 150
        self.bar_spacing = 20

        self.button_width = 40
        self.button_height = 20

        self.preview_width = 160
        self.preview_height = 50

        self.red_value = 0
        self.green_value = 0
        self.blue_value = 0

        self.active_channel = None

        # Bars
        self.red_bar_rect = pygame.Rect(self.x, self.y, self.bar_width, self.bar_height)
        self.green_bar_rect = pygame.Rect(
            self.x + self.bar_width + self.bar_spacing,
            self.y,
            self.bar_width,
            self.bar_height
        )
        self.blue_bar_rect = pygame.Rect(
            self.x + 2 * (self.bar_width + self.bar_spacing),
            self.y,
            self.bar_width,
            self.bar_height
        )

        # Buttons
        plus_y = self.y + self.bar_height + 10
        reset_y = plus_y + self.button_height + 8

        self.red_plus_rect = pygame.Rect(self.x, plus_y, self.button_width, self.button_height)
        self.green_plus_rect = pygame.Rect(
            self.x + self.bar_width + self.bar_spacing,
            plus_y,
            self.button_width,
            self.button_height
        )
        self.blue_plus_rect = pygame.Rect(
            self.x + 2 * (self.bar_width + self.bar_spacing),
            plus_y,
            self.button_width,
            self.button_height
        )

        self.red_reset_rect = pygame.Rect(self.x, reset_y, self.button_width, self.button_height)
        self.green_reset_rect = pygame.Rect(
            self.x + self.bar_width + self.bar_spacing,
            reset_y,
            self.button_width,
            self.button_height
        )
        self.blue_reset_rect = pygame.Rect(
            self.x + 2 * (self.bar_width + self.bar_spacing),
            reset_y,
            self.button_width,
            self.button_height
        )

        # Preview box
        self.preview_y = reset_y + self.button_height + 20
        self.preview_rect = pygame.Rect(self.x, self.preview_y, self.preview_width, self.preview_height)

    def get_color(self):
        return (self.red_value, self.green_value, self.blue_value)

    def is_hovering(self):
        mouse_pos = pygame.mouse.get_pos()
        return (
            self.red_bar_rect.collidepoint(mouse_pos)
            or self.green_bar_rect.collidepoint(mouse_pos)
            or self.blue_bar_rect.collidepoint(mouse_pos)
            or self.red_plus_rect.collidepoint(mouse_pos)
            or self.green_plus_rect.collidepoint(mouse_pos)
            or self.blue_plus_rect.collidepoint(mouse_pos)
            or self.red_reset_rect.collidepoint(mouse_pos)
            or self.green_reset_rect.collidepoint(mouse_pos)
            or self.blue_reset_rect.collidepoint(mouse_pos)
            or self.preview_rect.collidepoint(mouse_pos)
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # +1 buttons
            if self.red_plus_rect.collidepoint(mouse_pos):
                self.red_value = min(255, self.red_value + 1)
            elif self.green_plus_rect.collidepoint(mouse_pos):
                self.green_value = min(255, self.green_value + 1)
            elif self.blue_plus_rect.collidepoint(mouse_pos):
                self.blue_value = min(255, self.blue_value + 1)

            # Reset buttons
            elif self.red_reset_rect.collidepoint(mouse_pos):
                self.red_value = 0
            elif self.green_reset_rect.collidepoint(mouse_pos):
                self.green_value = 0
            elif self.blue_reset_rect.collidepoint(mouse_pos):
                self.blue_value = 0

            # Bars
            elif self.red_bar_rect.collidepoint(mouse_pos):
                self.active_channel = "red"
                self.set_value_from_mouse("red", mouse_pos[1])
            elif self.green_bar_rect.collidepoint(mouse_pos):
                self.active_channel = "green"
                self.set_value_from_mouse("green", mouse_pos[1])
            elif self.blue_bar_rect.collidepoint(mouse_pos):
                self.active_channel = "blue"
                self.set_value_from_mouse("blue", mouse_pos[1])

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.active_channel = None

        elif event.type == pygame.MOUSEMOTION and self.active_channel is not None:
            if pygame.mouse.get_pressed()[0]:
                self.set_value_from_mouse(self.active_channel, event.pos[1])

    def set_value_from_mouse(self, channel, mouse_y):
        top = self.y
        bottom = self.y + self.bar_height

        clamped_y = max(top, min(bottom, mouse_y))
        percent = 1 - ((clamped_y - top) / self.bar_height)
        value = int(percent * 255)

        if channel == "red":
            self.red_value = value
        elif channel == "green":
            self.green_value = value
        elif channel == "blue":
            self.blue_value = value

    # 🔥 Adaptive glow (white for black text, black for white text)
    def draw_text_with_glow(self, text, x, y, text_color):
        glow_color = (255, 255, 255) if text_color == (0, 0, 0) else (0, 0, 0)

        glow = self.font.render(text, True, glow_color)

        # outline
        self.screen.blit(glow, (x + 1, y + 1))
        self.screen.blit(glow, (x - 1, y + 1))
        self.screen.blit(glow, (x + 1, y - 1))
        self.screen.blit(glow, (x - 1, y - 1))

        # optional thicker glow (uncomment if you want stronger effect)
        # self.screen.blit(glow, (x + 2, y))
        # self.screen.blit(glow, (x - 2, y))
        # self.screen.blit(glow, (x, y + 2))
        # self.screen.blit(glow, (x, y - 2))

        text_surf = self.font.render(text, True, text_color)
        self.screen.blit(text_surf, (x, y))

    def draw_bar(self, rect, fill_color, value, label):
        pygame.draw.rect(self.screen, (70, 70, 90), rect)
        pygame.draw.rect(self.screen, Color.BLACK.value, rect, 2)

        fill_height = int((value / 255) * rect.height)
        fill_rect = pygame.Rect(
            rect.x,
            rect.y + rect.height - fill_height,
            rect.width,
            fill_height
        )

        if fill_height > 0:
            pygame.draw.rect(self.screen, fill_color, fill_rect)

        # Label above
        label_surf = self.font.render(label, True, Color.BLACK.value)
        self.screen.blit(
            label_surf,
            (rect.x + rect.width // 2 - label_surf.get_width() // 2, rect.y - 22)
        )

        # Value inside bar
        value_text = str(value)

        text_color = (0, 0, 0) if value > 128 else (255, 255, 255)

        if fill_height > 20:
            value_y = fill_rect.y + fill_rect.height // 2 - self.font.get_height() // 2
        else:
            value_y = rect.y + 5

        value_x = rect.x + rect.width // 2 - self.font.size(value_text)[0] // 2

        self.draw_text_with_glow(value_text, value_x, value_y, text_color)

    def draw_button(self, rect, color_value, label):
        pygame.draw.rect(self.screen, color_value, rect)
        pygame.draw.rect(self.screen, Color.BLACK.value, rect, 2)

        label_surf = self.font.render(label, True, Color.BLACK.value)
        self.screen.blit(
            label_surf,
            (
                rect.x + rect.width // 2 - label_surf.get_width() // 2,
                rect.y + rect.height // 2 - label_surf.get_height() // 2
            )
        )

    def draw(self):
        self.draw_bar(self.red_bar_rect, (255, 0, 0), self.red_value, "R")
        self.draw_bar(self.green_bar_rect, (0, 255, 0), self.green_value, "G")
        self.draw_bar(self.blue_bar_rect, (0, 0, 255), self.blue_value, "B")

        self.draw_button(self.red_plus_rect, (255, 160, 160), "+")
        self.draw_button(self.green_plus_rect, (160, 255, 160), "+")
        self.draw_button(self.blue_plus_rect, (160, 160, 255), "+")

        self.draw_button(self.red_reset_rect, (255, 210, 210), "0")
        self.draw_button(self.green_reset_rect, (210, 255, 210), "0")
        self.draw_button(self.blue_reset_rect, (210, 210, 255), "0")

        preview_color = (self.red_value, self.green_value, self.blue_value)
        pygame.draw.rect(self.screen, preview_color, self.preview_rect)
        pygame.draw.rect(self.screen, Color.BLACK.value, self.preview_rect, 2)

        preview_label = self.font.render("Preview", True, Color.BLACK.value)
        self.screen.blit(preview_label, (self.preview_rect.x + 5, self.preview_rect.y + 5))