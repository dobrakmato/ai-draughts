import tkinter
import random
import json
import math


class Graphics:
    def __init__(self, w, h):
        self.width = w
        self.height = h

        Log.info('Creating graphics (and canvas) instance of size ' + str(w) + 'x' + str(h))
        self.canvas = tkinter.Canvas(width=self.width, height=self.height)
        # self.canvas.configure(background='#002259')
        self.canvas.pack()

    def middle(self):
        return self.width / 2, self.height / 2


class Skin:
    def __init__(self, name):
        self.name = name
        Log.info('Loading skin ' + name)
        json_dic = JsonUtils.load_json(self.path('skin.json'))

        self.board_dark_color = json_dic['board']['colors']['dark']
        self.board_light_color = json_dic['board']['colors']['light']

        self.bl = tkinter.PhotoImage(file=self.path('bl.png'))
        self.bp = tkinter.PhotoImage(file=self.path('bp.png'))
        self.cl = tkinter.PhotoImage(file=self.path('cl.png'))
        self.cp = tkinter.PhotoImage(file=self.path('cp.png'))
        self.bd = tkinter.PhotoImage(file=self.path('bd.png'))
        self.cd = tkinter.PhotoImage(file=self.path('cd.png'))

    def path(self, rel):
        return f'skins/{self.name}/{rel}'

    def get_image(self, typ, animation_state, is_draught):
        if is_draught:
            if typ == 1:
                return self.bd
            else:
                return self.cd
        else:
            if typ == 1:
                if animation_state == 0:
                    return self.bl
                else:
                    return self.bp
            elif typ == 2:
                if animation_state == 0:
                    return self.cl
                else:
                    return self.cp
            else:
                raise RuntimeError('This should not be called with other values as 1, 2')


class Pawn:
    def __init__(self, g: Graphics, skin: Skin, x, y, typ):
        self.g = g
        self.skin = skin

        self.x = x
        self.y = y
        self.player = typ
        self.dead = False
        self.is_draught = False
        self.animation_speed = random.randint(500, 5000)
        self.animation_state = 0

        min_x = x * (g.width / 8)
        min_y = y * (g.height / 8)
        max_x = (x + 1) * (g.width / 8)
        max_y = (y + 1) * (g.height / 8)

        self.image = g.canvas.create_image((min_x + max_x) / 2, (min_y + max_y) / 2,
                                           image=skin.get_image(self.player, self.animation_state, self.is_draught))

        g.canvas.after(self.animation_speed, self.animate)

    def __str__(self):
        return f'P{self.player} pawn at {self.x}, {self.y}'

    __repr__ = __str__

    def die(self):
        self.dead = True
        self.g.canvas.delete(self.image)

    def pos_from_xy(self):
        min_x = self.x * (self.g.width / 8)
        min_y = self.y * (self.g.height / 8)
        max_x = (self.x + 1) * (self.g.width / 8)
        max_y = (self.y + 1) * (self.g.height / 8)

        return (min_x + max_x) / 2, (min_y + max_y) / 2

    def reset_to_xy(self):
        self.g.canvas.coords(self.image, self.pos_from_xy())

    def animate(self):
        self.animation_state = (self.animation_state + 1) % 2
        self.g.canvas.itemconfigure(self.image,
                                    image=self.skin.get_image(self.player, self.animation_state, self.is_draught))
        self.g.canvas.after(self.animation_speed, self.animate)


class Board:
    def __init__(self, g: Graphics, skin: Skin, friendly_fire: bool):
        self.g = g
        Log.info('Creating board')

        # game state
        self.friendly_fire = friendly_fire
        self.board = JsonUtils.load_json('start_game.json')['pawns']
        self.current_player = JsonUtils.load_json('start_game.json')['first_player']
        self.pawns = [[None for x in range(8)] for y in range(8)]
        self.currently_dragging: Pawn = None

        Log.info('Friendly fire is ' + ('enabled' if self.friendly_fire else 'disabled'))

        a, b = skin.board_dark_color, skin.board_light_color
        for x in range(8):
            for y in range(8):
                x0 = x * (g.width / 8)
                y0 = y * (g.height / 8)
                x1 = (x + 1) * (g.width / 8)
                y1 = (y + 1) * (g.height / 8)

                g.canvas.create_rectangle(x0, y0, x1, y1, fill=a)

                a, b = b, a
            a, b = b, a

        for x in range(8):
            for y in range(8):
                if self.board[y][x] != 0:
                    self.pawns[x][y] = Pawn(self.g, skin, x, y, abs(self.board[y][x]))

                    # make draughts
                    if self.board[y][x] < 0:
                        self.pawns[x][y].is_draught = True

        g.canvas.bind('<Button-1>', self.start_drag)
        g.canvas.bind('<B1-Motion>', self.do_drag)
        g.canvas.bind('<ButtonRelease-1>', self.end_drag)

    def start_drag(self, e):
        # pick pawn
        pawn = self.get_pawn_at(e.x, e.y)

        if pawn is None:
            Log.debug('No pawn was selected')
            return

        if self.current_player != pawn.player:
            Log.err('Player ' + str(self.current_player) + ' tried to play with pawn that does not belong to him.')
            return

        self.currently_dragging = pawn
        self.g.canvas.tag_raise(self.currently_dragging.image)

    def do_drag(self, e):
        # move pawn
        if self.currently_dragging is not None:
            lx, ly = self.g.canvas.coords(self.currently_dragging.image)
            self.g.canvas.move(self.currently_dragging.image, e.x - lx, e.y - ly)

    def end_drag(self, e):
        try:
            if self.currently_dragging is not None:
                ix = e.x // (self.g.width // 8)
                iy = e.y // (self.g.height // 8)

                lix = self.currently_dragging.x
                liy = self.currently_dragging.y

                dix = ix - lix
                diy = iy - liy

                # can't move outside the board
                if ix < 0 or iy < 0 or ix > 7 or iy > 7:
                    return Log.err('Wrong move. Cant place outside window.')

                # if not draught, can move only forward
                if not self.currently_dragging.is_draught and (
                            (self.current_player == 1 and diy < 1) or (self.current_player == 2 and diy > -1)):
                    return Log.err('Wrong move. Pawn can move only forward.')

                # can only move diagonally
                if abs(dix) != abs(diy):
                    return Log.err('Wrong move. Pawn/Draught must move diagonally.')

                pawn_at_position = self.get_pawn_at(e.x, e.y)

                # cant place pawn at pawn, or can?
                if pawn_at_position is not None:
                    return Log.err('Wrong move. Cant place pawn on pawn.')

                # validate jumps (moves with length > 1)
                if abs(dix) > 1:
                    jumped_over = []

                    x, y = lix, liy
                    last = 'self'
                    for i in range(lix, ix, int(math.copysign(1, dix))):

                        # skip first pawn (the one that is jumping)
                        if self.pawns[x][y] == self.currently_dragging:
                            x += int(math.copysign(1, dix))
                            if self.currently_dragging.is_draught:
                                y += int(math.copysign(1, diy))
                            else:
                                y += 1 if self.current_player == 1 else -1
                            continue

                        if self.pawns[x][y] is None:
                            if i == ix - int(math.copysign(1, dix)) and not self.currently_dragging.is_draught:
                                return Log.err('Invalid jump. Jump can\'t end with gap.')

                            if last == 'pawn':
                                last = 'gap'
                            else:
                                if not self.currently_dragging.is_draught:
                                    return Log.err('Invalid jump. Too long gap between pawn and attacker.')
                        else:
                            if last == 'self':
                                jumped_over.append(self.pawns[x][y])
                            elif last == 'gap':
                                jumped_over.append(self.pawns[x][y])
                            else:
                                if not self.currently_dragging.is_draught:
                                    return Log.err('Invalid jump. Missing gap between pawns.')
                            last = 'pawn'

                        x += int(math.copysign(1, dix))
                        if self.currently_dragging.is_draught:
                            y += int(math.copysign(1, diy))
                        else:
                            y += 1 if self.current_player == 1 else -1

                    Log.debug('jumped over: ' + str(jumped_over))

                    # validate no gap between jumped and me

                    # validate friendly fire
                    if not self.friendly_fire and any(p.player == self.current_player for p in jumped_over):
                        return Log.err('Invalid jump. Friendly fire disabled.')

                    for p in jumped_over:
                        if p.player != self.current_player:
                            p.die()
                            self.pawns[p.x][p.y] = None

                # promote to draught
                if (self.current_player == 2 and iy == 0) or (self.current_player == 1 and iy == 7):
                    self.currently_dragging.is_draught = True

                # place pawn to pos
                self.pawns[self.currently_dragging.x][self.currently_dragging.y] = None
                self.pawns[ix][iy] = self.currently_dragging
                self.currently_dragging.x = ix
                self.currently_dragging.y = iy

                # switch player
                if self.current_player == 1:
                    self.current_player = 2
                else:
                    self.current_player = 1
        finally:
            if self.currently_dragging is not None:
                self.currently_dragging.reset_to_xy()
            self.currently_dragging = None

    def get_pawn_at(self, x, y) -> Pawn:
        ix = x // (self.g.width // 8)
        iy = y // (self.g.height // 8)
        return self.pawns[ix][iy]


class JsonUtils:
    @staticmethod
    def load_json(file):
        with open(file) as f:
            return json.loads(f.read())


class Log:
    @staticmethod
    def debug(msg):
        Log.log('debug', msg)

    @staticmethod
    def info(msg):
        Log.log('info', msg)

    @staticmethod
    def err(msg):
        Log.log('error', msg)

    @staticmethod
    def warn(msg):
        Log.log('warn', msg)

    @staticmethod
    def log(level, msg):
        print('[' + level + '] ' + msg)


class Program:
    def __init__(self):
        Log.info('Loading settings...')
        self.settings = JsonUtils.load_json('settings.json')
        self.g = Graphics(self.settings['width'], self.settings['height'])
        self.skin = Skin(self.settings['skin'])
        self.board = Board(self.g, self.skin, self.settings['friendly_fire'])
        tkinter.mainloop()


Program()
