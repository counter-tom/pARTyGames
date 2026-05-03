import pygame

class FillCommand:
    def __init__(self, canvas, start_pos, fill_color, firebase=None):  #  Add firebase=None
        self.canvas = canvas
        self.start_pos = start_pos
        self.fill_color = fill_color
        self.firebase = firebase  #  Store it
        self.old_strokes = []
        self.old_surface = None

    def do(self):
        self.old_strokes = list(self.canvas.strokes)
        self.old_surface = self.canvas.surface.copy()
        self.flood_fill(self.canvas.surface, self.start_pos, self.fill_color)
        self.canvas.makeDirty()

        #  Use self.firebase instead of self.canvas.firebase
        if self.firebase is not None:
            self.firebase.push_fill(
                self.start_pos[0],
                self.start_pos[1],
                self.fill_color
            )

    def undo(self):
        self.canvas.strokes = list(self.old_strokes)
        self.canvas.surface = self.old_surface.copy()
        self.canvas.makeDirty()

    def flood_fill(self, surface, start_pos, fill_color):
        if surface.get_at(start_pos) == fill_color:
            return
        width, height = surface.get_size()
        pixels = pygame.PixelArray(surface)
        x, y = start_pos
        
        if x < 0 or x >= width or y < 0 or y >= height:
            del pixels
            return

        target_color = pixels[x,y]
        if target_color == fill_color:
            del pixels
            return

        stack = [(x, y)]

        while stack:
            px, py = stack.pop()
           
            x_left_bound = px
            while x_left_bound > 0 and pixels[x_left_bound - 1, py] == target_color:
                x_left_bound -= 1
           
            x_right_bound = px
            while x_right_bound < width - 1 and pixels[x_right_bound + 1, py] == target_color:
                x_right_bound += 1
            
            pixels[x_left_bound: x_right_bound + 1, py] = fill_color

            for dy in [-1, 1]:
                ny = py + dy
                if 0 <= ny < height:
                    x_scan = x_left_bound
                    while x_scan <= x_right_bound:
                        # Look for a pixel that matches target_color
                        if pixels[x_scan, ny] == target_color:
                            stack.append((x_scan, ny))
                            
                
                            while x_scan <= x_right_bound and pixels[x_scan, ny] == target_color:
                                x_scan += 1
                        else:
                            x_scan += 1

    
        del pixels 