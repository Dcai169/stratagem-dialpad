import pygame
from pygame.locals import *
import numpy as np
from enum import Enum
import cairosvg
import io
from os import getcwd
from os.path import join as pathjoin
import json
from platform import system

CLEARALLINFO = USEREVENT + 1
CLEARSEQUENCE = USEREVENT + 2

class Direction(Enum):
    NONE = ""
    LEFT = "\u2B05"
    UP = "\u2B06"
    DOWN = "\u2B07"
    RIGHT = "\u2B95"


def round_base(x, base):
    return base * round(x/base)


def get_vector_direction(stroke_vector: np.ndarray) -> Direction:
    azimuth = round_base(np.rad2deg(np.arctan2(*stroke_vector)), 90)

    if np.linalg.norm(stroke_vector) < 100:
        return Direction.NONE

    if azimuth == 180 or azimuth == -180:
        return Direction.UP
    elif azimuth == 90:
        return Direction.RIGHT
    elif azimuth == 0:
        return Direction.DOWN
    elif azimuth == -90:
        return Direction.LEFT
    else:
        return Direction.NONE
    
def load_svg(filename):
    return pygame.image.load(io.BytesIO(cairosvg.svg2png(url=filename, dpi=120, scale=2)))


class Composer:
    def __init__(self) -> None:
        self.reset_sequence()

        with open("sequences.json") as f:
            self.stratagems = json.load(f)

    def reset_sequence(self) -> None:
        self.sequence = []

    def append_stroke(self, stroke: Direction) -> None:
        if stroke != Direction.NONE:
            self.sequence.append(stroke)

    def check_stratagems(self):
        possible_codes = [s for s in self.stratagems.keys() if self.get_current_sequence() in s[0:len(self.sequence)]]
        stratagem = None
        # print(possible_codes)

        if len(possible_codes) == 1 and self.get_current_sequence() in possible_codes:
            stratagem = self.stratagems[self.get_current_sequence()]
            self.reset_sequence()
        elif len(possible_codes) == 0:
            stratagem = {}
            self.reset_sequence()

        return stratagem

    def get_current_sequence(self) -> str:
        return "".join([i.value for i in self.sequence])


class App:
    def __init__(self):
        self.composer = Composer()
        self._running = True
        self.screen = None
        self.stratagem = None

        pygame.font.init()
        self.display_font = pygame.font.Font(pathjoin("assets", "fonts", "Monda-Regular.ttf.woff"), 60)
        self.inconsolata = pygame.font.Font(pathjoin("assets", "fonts", "Inconsolata", "static", "Inconsolata-Regular.ttf"), 72)
        

    def on_init(self):
        pygame.init()
    
        self.size = self.width, self.height = 800, 480

        display_mode = pygame.HWSURFACE | pygame.DOUBLEBUF

        if system() != "Windows":
            display_mode |= pygame.NOFRAME

        self.screen = pygame.display.set_mode(self.size, display_mode)
        # print(pygame.display.get_desktop_sizes())

        self._running = True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

        elif event.type == MOUSEBUTTONDOWN:
            self.stroke_start = np.array(pygame.mouse.get_pos())
            if self.stratagem is not None and self.stratagem != {}:
                self.screen.fill((0, 0, 0), self.sequence_rect)
                self.screen.fill((0, 0, 0), self.stratagem_name_rect)
                self.screen.fill((0, 0, 0), self.icon_rect)
            elif self.stratagem == {}:
                self.screen.fill((0, 0, 0), self.sequence_rect)

        elif event.type == MOUSEBUTTONUP:
            self.stroke_end = np.array(pygame.mouse.get_pos())

            stroke_dir = get_vector_direction(np.subtract(self.stroke_end, self.stroke_start))
            self.composer.append_stroke(stroke_dir)

            self.sequence = self.inconsolata.render(self.composer.get_current_sequence(), True, (255, 255, 255), (0, 0, 0))
            self.sequence_rect = self.sequence.get_rect()
            self.sequence_rect.center = (self.width // 2, self.height // 6)
            self.screen.blit(self.sequence, self.sequence_rect)

            self.stratagem = self.composer.check_stratagems()
            if self.stratagem is not None and self.stratagem != {}:
                self.stratagem_name = self.display_font.render(self.stratagem['name'], True, (255, 255, 255), (0, 0, 0))
                self.stratagem_name_rect = self.stratagem_name.get_rect()
                self.stratagem_name_rect.center = (self.width // 2, 2*self.height // 6)
                self.screen.blit(self.stratagem_name, self.stratagem_name_rect)

                filepath = pathjoin(getcwd(), 'assets', 'stratagem_icons', self.stratagem['icon'])
                self.icon = load_svg(filepath).convert(self.screen)
                self.icon_rect = self.icon.get_rect()
                self.icon_rect.center = (self.width // 2, 4*self.height // 6)
                self.screen.blit(self.icon, self.icon_rect)

                pygame.time.set_timer(CLEARALLINFO, 1600, loops=1)
            elif self.stratagem is not None and self.stratagem == {}:
                pygame.time.set_timer(CLEARSEQUENCE, 200, loops=1)

        elif event.type == CLEARALLINFO:
            self.screen.fill((0, 0, 0), self.sequence_rect)
            self.screen.fill((0, 0, 0), self.stratagem_name_rect)
            self.screen.fill((0, 0, 0), self.icon_rect)

            self.composer.reset_sequence()
        
        elif event.type == CLEARSEQUENCE:
            self.screen.fill((0, 0, 0), self.sequence_rect)

            self.composer.reset_sequence()

    def on_loop(self):
        pass

    def on_render(self):
        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False

        self.screen.fill((0, 0, 0))

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()


if __name__ == "__main__":
    theApp = App()
    pygame.display.set_caption('Stratagem Hero')
    theApp.on_execute()
