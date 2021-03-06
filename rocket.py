# rocket.py

import wadze    # Web Assembly Decoder
module = wadze.parse_module(open('html/program.wasm', 'rb').read())

# Build imported functions
import math

# These functions are imported by Wasm.  Must be implemented in the host
# environment (Python).   These are listed in the required order.

def imp_Math_atan(x):
    return float64(math.atan(x))

def imp_clear_screen():
    print('clear_screen')

def imp_cos(x):
    return float64(math.cos(x))

def imp_draw_bullet(x, y):
    print('draw_bullet', x, y)

def imp_draw_enemy(x, y):
    print('draw_enemy', x, y)

def imp_draw_particle(x, y, z):
    print('draw_particle', x, y, z)

def imp_draw_player(x, y, z):
    print('draw_player', x, y, z)

def imp_draw_score(s):
    print('draw_score', s)

def imp_sin(x):
    return float64(math.sin(x))

import pygame

pygame.init()

size = width, height = (800, 600)
screen = pygame.display.set_mode(size)
font = pygame.font.SysFont("helvetica", 36)

def imp_clear_screen():
    screen.fill((0,0,0))

def imp_draw_bullet(x, y):
    pygame.draw.circle(screen, (0,0, 255), (int(x), int(y)), 2)

def imp_draw_enemy(x, y):
    pygame.draw.circle(screen, (255,255,0), (int(x), int(y)), 15, 15)

def imp_draw_particle(x, y, z):
    pygame.draw.circle(screen, (255,0,255), (int(x),int(y)), abs(int(z)))

def imp_draw_player(x, y, z):
    pygame.draw.circle(screen, (255,0,0), (int(x), int(y)), 10, 2)

def imp_draw_score(s):
    # print('draw_score', s)
    text = font.render(f'Score: {int(s)}', True, (200,200, 0))
    screen.blit(text, (5, 5))


import machine

# Declare as imported functions for our "machine"
imported_functions = [ 
    machine.ImportFunction(1, 1, imp_Math_atan),
    machine.ImportFunction(0, 0, imp_clear_screen),
    machine.ImportFunction(1, 1, imp_cos),
    machine.ImportFunction(2, 0, imp_draw_bullet),
    machine.ImportFunction(2, 0, imp_draw_enemy),
    machine.ImportFunction(3, 0, imp_draw_particle),
    machine.ImportFunction(3, 0, imp_draw_player),
    machine.ImportFunction(1, 0, imp_draw_score),
    machine.ImportFunction(1, 1, imp_sin),
]

# Declare "defined" functions
defined_functions = [ ]

for typeidx, code in zip(module['func'], module['code']):
    functype = module['type'][typeidx]  # Signature
    func = machine.Function(nparams = len(functype.params),
                            returns = bool(functype.returns),
                            code = wadze.parse_code(code).instructions)
    defined_functions.append(func)

functions = imported_functions + defined_functions

# Declare "exported" functions
exports = { exp.name: functions[exp.ref] for exp in module['export']
            if isinstance(exp, wadze.ExportFunction) }

m = machine.Machine(functions, 100*65536)    # Hack on memory

# Initialize memory
for data in module['data']:
    m.execute(data.offset, None)
    offset = m.pop()
    m.memory[offset:offset+len(data.values)] = data.values

from machine import float64, int32

# Call something
width = float64(800.0)
height = float64(600.0)

m.call(exports['resize'], width, height)    # Prayer

# Game loop
import time

last = time.time()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            raise SystemExit()
        elif event.type == pygame.KEYUP:
            print(event.key)
            if event.key == 32:
                m.call(exports['toggle_shoot'], int32(0))
            elif event.key == 1073741903:
                m.call(exports['toggle_turn_right'], int32(0))
            elif event.key == 1073741904:
                m.call(exports['toggle_turn_left'], int32(0))
            elif event.key == 1073741906:
                m.call(exports['toggle_boost'], int32(0))

        elif event.type == pygame.KEYDOWN:
            if event.key == 32:
                m.call(exports['toggle_shoot'], int32(1))
            elif event.key == 1073741903:
                m.call(exports['toggle_turn_right'], int32(1))
            elif event.key == 1073741904:
                m.call(exports['toggle_turn_left'], int32(1))
            elif event.key == 1073741906:
                m.call(exports['toggle_boost'], int32(1))

    now = time.time()
    dt = now - last
    last = now
    m.call(exports['update'], float64(dt))
    m.call(exports['draw'])
    pygame.display.flip()