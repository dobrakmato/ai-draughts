import tkinter
import random
import json
import math
from typing import List, Optional


class Player:
    def __init__(self, player_id: int, name: str, forward_y: int):
        self.id = player_id
        self.name = name
        self.forward_y = forward_y


class Players:
    NONE, WHITE, BLACK = Player(0, 'None', 0), Player(1, 'White', 1), Player(2, 'Black', -1)

    @staticmethod
    def from_id(player_id: int):
        if player_id == 0:
            return Players.NONE
        elif player_id == 1:
            return Players.WHITE
        elif player_id == 2:
            return Players.BLACK
        else:
            raise ValueError('Undefined player id')


class Skin:
    def __init__(self, ext='.png'):
        self.board_background = tkinter.PhotoImage(file=self.image_path(f'background{ext}'))

        self.valid_move = tkinter.PhotoImage(file=self.image_path(f'valid_move{ext}'))
        self.valid_jump = tkinter.PhotoImage(file=self.image_path(f'valid_jump{ext}'))

        self.black_pawn0 = tkinter.PhotoImage(file=self.image_path(f'black_pawn0{ext}'))
        self.black_pawn1 = tkinter.PhotoImage(file=self.image_path(f'black_pawn1{ext}'))
        self.black_draughts0 = tkinter.PhotoImage(file=self.image_path(f'black_draughts0{ext}'))
        self.black_draughts1 = tkinter.PhotoImage(file=self.image_path(f'black_draughts1{ext}'))

        self.white_pawn0 = tkinter.PhotoImage(file=self.image_path(f'white_pawn0{ext}'))
        self.white_pawn1 = tkinter.PhotoImage(file=self.image_path(f'white_pawn1{ext}'))
        self.white_draughts0 = tkinter.PhotoImage(file=self.image_path(f'white_draughts0{ext}'))
        self.white_draughts1 = tkinter.PhotoImage(file=self.image_path(f'white_draughts1{ext}'))

    @staticmethod
    def image_path(rel):
        return f'./images/{rel}'

    def get_image_for_pawn(self, player: Player, is_draughts: bool, animation_state: int):
        if player == Players.WHITE:
            if is_draughts:
                if animation_state == 0:
                    return self.white_draughts1
                else:
                    return self.white_draughts0
            else:
                if animation_state == 0:
                    return self.white_pawn1
                else:
                    return self.white_pawn0
        elif player == Players.BLACK:
            if is_draughts:
                if animation_state == 0:
                    return self.black_draughts1
                else:
                    return self.black_draughts0
            else:
                if animation_state == 0:
                    return self.black_pawn1
                else:
                    return self.black_pawn0
        else:
            raise ValueError('Can\'t get image for pawn with no player.')


class Graphics:
    def __init__(self, canvas: tkinter.Canvas):
        self.skin = Skin()
        self.canvas: tkinter.Canvas = canvas


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


class Move:
    def __init__(self, jumped_over, final_x: int, final_y: int):
        self.jumped_over = jumped_over
        self.final_x = final_x
        self.final_y = final_y

    def __str__(self):
        if self.is_jump():
            return f'Jump to {self.final_x};{self.final_y} while removing: {self.jumped_over}'
        else:
            return f'Move to {self.final_x};{self.final_y}'

    __repr__ = __str__

    def is_jump(self):
        return len(self.jumped_over) != 0


class PawnGUI:
    def __init__(self, pawn, g: Graphics):
        self.pawn = pawn
        self.graphics = g
        self.animation_state = 0
        self.animation_speed = 0
        self.image = g.canvas.create_image(self.pawn.x * 64, self.pawn.y * 64,
                                           image=g.skin.get_image_for_pawn(self.pawn.player, self.pawn.is_draughts(),
                                                                           self.animation_state))

        self.reset_image_position()
        self.initialize_animation()

    def initialize_animation(self):
        self.animation_speed = random.randint(1000, 3000)
        self.graphics.canvas.after(self.animation_speed, self.animation_proceed)

    def animation_proceed(self):
        self.animation_state = (self.animation_state + 1) % 2
        next_image = self.graphics.skin.get_image_for_pawn(self.pawn.player, self.pawn.is_draughts(),
                                                           self.animation_state)
        self.graphics.canvas.itemconfig(self.image, image=next_image)
        self.graphics.canvas.after(self.animation_speed, self.animation_proceed)

    def reset_image_position(self):
        self.set_image_position(self.pawn.x * 64 + 32, self.pawn.y * 64 + 32)

    def set_image_position(self, x, y):
        self.graphics.canvas.coords(self.image, x, y)

    def remove_image(self):
        self.graphics.canvas.delete(self.image)

    def bring_to_front(self):
        self.graphics.canvas.tag_raise(self.image)


class Pawn:
    def __init__(self, x: int, y: int, player: Player, g: Graphics):
        self.x = x
        self.y = y
        self.player = player
        self.graphics = g
        self.gui = PawnGUI(self, g)

    def __str__(self):
        return f'{self.player.name} Pawn at {self.x};{self.y}'

    __repr__ = __str__

    def is_draughts(self):
        return False

    def get_pawn_moves(self):
        return [(-1, self.player.forward_y), (1, self.player.forward_y)]

    def get_valid_moves_from(self, x, y, pawn_moves, board, allow_only_jumps, already_jumped_over, depth) -> List[Move]:
        valid_moves = []

        if depth > 12:
            return valid_moves

        for delta_x, delta_y in pawn_moves:
            target_position = (x + delta_x, y + delta_y)

            if not board.is_valid_position(*target_position):
                # The position was outside the playing board.
                continue

            if board.has_pawn_at(*target_position):
                # Existing pawn is blocking this move, we cloud jump over it if it isn't our pawn.
                # You can't jump over your own pawns. We will check if the existing pawn player is
                # different than this player.
                jumped_pawn = board.get_pawn_at(*target_position)

                if self.player != jumped_pawn.player:
                    # Nice! The pawn belongs to other player. We now only need valid (and free
                    # non-obstructed) position after we jump over the other player's pawn.
                    target_position = (target_position[0] + delta_x, target_position[1] + delta_y)

                    if not board.is_valid_position(*target_position):
                        # We can't jump this way because we would went out of board.
                        continue

                    if not board.has_pawn_at(*target_position):
                        # The spot is free. We can jump there.

                        # First try to find multi-jumps starting from end position of this jump.
                        valid_multi_jumps = self.get_valid_moves_from(target_position[0], target_position[1],
                                                                      pawn_moves, board, True,
                                                                      already_jumped_over + [jumped_pawn], depth + 1)

                        # We can perform single-jump only if there are no jumps following this jump.
                        if len(valid_multi_jumps) == 0:
                            valid_moves.append(Move(list(set(already_jumped_over + [jumped_pawn])), *target_position))

                        # Add all multi-jumps to list of valid jumps.
                        valid_moves.extend(valid_multi_jumps)

            else:
                # This is not a jump, so we should check if trivial moves are allowed.
                if not allow_only_jumps:
                    valid_moves.append(Move([], *target_position))

        return valid_moves

    def get_valid_moves(self, board) -> List[Move]:
        pawn_moves = self.get_pawn_moves()
        return self.get_valid_moves_from(self.x, self.y, pawn_moves, board, False, [], 0)

    def die(self):
        self.gui.remove_image()
        self.x = -1
        self.y = -1


class Draughts(Pawn):
    def __init__(self, from_pawn: Pawn):
        super().__init__(from_pawn.x, from_pawn.y, from_pawn.player, from_pawn.graphics)

    def __str__(self):
        return f'{self.player.name} Draughts at {self.x};{self.y}'

    __repr__ = __str__

    def get_pawn_moves(self):
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    def is_draughts(self):
        return True


class ScoreTracker:
    def __init__(self):
        self.score = {
            Players.BLACK: 0,
            Players.WHITE: 0
        }

    def reset(self):
        self.score = {
            Players.BLACK: 0,
            Players.WHITE: 0
        }

    def get_score(self, player: Player):
        return self.score[player]

    def increment_score(self, player: Player):
        self.score[player] = self.score[player] + 1


class MoveTransaction:
    moves = 0

    def __init__(self, pawn: Pawn, board):
        self.board = board
        self.pawn = pawn
        self.currently_dragging = pawn
        self.valid_moves = pawn.get_valid_moves(board)
        if self.board.valid_moves_gui is not None:
            self.board.valid_moves_gui.show_moves(self.valid_moves)
        self.pawn.gui.bring_to_front()

    def find_valid_move(self, x, y):
        for move in self.valid_moves:
            if move.final_y == y and move.final_x == x:
                return move
        return None

    def dragging(self, e):
        self.pawn.gui.set_image_position(e.x, e.y)

    def rollback(self):
        if self.board.valid_moves_gui is not None:
            self.board.valid_moves_gui.remove_all_moves()

        self.pawn.gui.reset_image_position()

    def commit(self, played_move: Move):
        # Hide valid moves if enabled.
        if self.board.valid_moves_gui is not None:
            self.board.valid_moves_gui.remove_all_moves()

        # Increment global move counter.
        MoveTransaction.moves += 1

        # Move pawn on board.
        self.board.set_pawn_at(played_move.final_x, played_move.final_y, self.pawn)
        self.board.set_pawn_at(self.pawn.x, self.pawn.y, None)

        # Update internal pawn data.
        self.pawn.x = played_move.final_x
        self.pawn.y = played_move.final_y

        # Update pawn's graphics.
        self.pawn.gui.reset_image_position()

        # Remove all jumped pawns.
        for jumped in played_move.jumped_over:
            self.board.set_pawn_at(jumped.x, jumped.y, None)
            self.board.score_tracker.increment_score(self.pawn.player)
            jumped.die()

        # Promote pawn to draughts.
        if self.board.should_become_draught(self.pawn.x, self.pawn.y):
            self.board.set_pawn_at(self.pawn.x, self.pawn.y, Draughts(self.pawn))
            self.pawn.die()
            self.pawn = None

        # Proceed to next player.
        self.board.current_player = Players.BLACK if self.board.current_player == Players.WHITE else Players.WHITE


class ValidMovesGUI:
    def __init__(self, g: Graphics):
        self.graphics = g
        self.created_objects = []

    def show_moves(self, valid_moves: List[Move]):
        for move in valid_moves:
            image = self.graphics.skin.valid_jump if move.is_jump() else self.graphics.skin.valid_move
            obj = self.graphics.canvas.create_image(move.final_x * 64 + 32, move.final_y * 64 + 32, image=image)
            self.created_objects.append(obj)

    def remove_all_moves(self):
        for obj in self.created_objects:
            self.graphics.canvas.delete(obj)


class BoardGUI:
    def __init__(self, board, g: Graphics):
        self.board = board
        self.graphics = g
        self.background = g.canvas.create_image(256, 256, image=g.skin.board_background)


class InfoboardGUI:
    def __init__(self, board, g: Graphics):
        self.board = board
        self.graphics = g
        self.logo = g.canvas.create_text(512 + 16, 16, text='Dáma', font=('Arial', 32), anchor=tkinter.NW)
        self.current_player = g.canvas.create_text(512 + 16, 100, text='', font=('Arial', 16), anchor=tkinter.NW)
        self.black_score = g.canvas.create_text(512 + 16, 100 + 32 * 2, text='', font=('Arial', 16), anchor=tkinter.NW)
        self.white_score = g.canvas.create_text(512 + 16, 100 + 32 * 3, text='', font=('Arial', 16), anchor=tkinter.NW)
        self.moves = g.canvas.create_text(512 + 16, 100 + 32 * 4, text='', font=('Arial', 16), anchor=tkinter.NW)
        self.black_ai_note = g.canvas.create_text(512 + 16, 100 + 32 * 6, text='',
                                                  font=('Arial', 10), anchor=tkinter.NW)

        self.update()

    def update(self):
        self.graphics.canvas.itemconfig(self.current_player,
                                        text=f'Current player: {self.board.current_player.name}')
        self.graphics.canvas.itemconfig(self.black_score,
                                        text=f'Black: {self.board.score_tracker.get_score(Players.BLACK)}')
        self.graphics.canvas.itemconfig(self.white_score,
                                        text=f'White: {self.board.score_tracker.get_score(Players.WHITE)}')
        self.graphics.canvas.itemconfig(self.moves,
                                        text=f'Moves: {MoveTransaction.moves}')

        if self.board.ai is not None:
            self.graphics.canvas.itemconfig(self.black_ai_note,
                                            text=f'BlackAI is enabled for player Black.')


class BlackAI:
    def __init__(self, board, g: Graphics, me=Players.BLACK):
        self.me = me
        self.board = board
        self.graphics = g

    def try_to_play(self):
        if self.board.current_player == self.me:
            self.play()

    def play(self):
        pawns = self.get_all_pawns()
        random.shuffle(pawns)

        moves = []

        for pawn in pawns:
            for move in pawn.get_valid_moves(self.board):
                score = 1

                if move.is_jump():
                    score += len(move.jumped_over) * 10

                moves.append((score, pawn, move))

        # sort moves.
        moves = sorted(moves, key=lambda tup: tup[0], reverse=True)
        print('[AI] Moves:', moves)

        if len(moves) == 0:
            return

        # play the best move.
        score, pawn, move = moves[0]

        # simulate thinking so players are not frustrated
        def helper():
            print('[AI] Best move:', move)
            self.play_move(pawn, move)

        self.graphics.canvas.after(score * random.randint(10, 90), helper)

    def play_move(self, pawn, move):
        self.board.move_transaction = MoveTransaction(pawn, self.board)
        self.board.move_transaction.commit(move)
        self.board.move_transaction = None

        self.board.infoboard_gui.update()
        self.board.check_for_win()
        self.board.next_round()

    def get_all_pawns(self) -> List[Pawn]:
        pawns = []
        for x in range(8):
            for y in range(8):
                if self.board.has_pawn_at(x, y) and self.board.get_pawn_at(x, y).player == self.me:
                    pawns.append(self.board.get_pawn_at(x, y))
        return pawns


class Board:
    def __init__(self, graphics, ai_enabled, white_ai_enabled, show_valid_moves):
        self.score_tracker = ScoreTracker()
        self.move_transaction: MoveTransaction = None
        self.pawns = [[None for x in range(8)] for y in range(8)]
        self.current_player = Players.WHITE
        self.graphics = graphics
        self.valid_moves_gui = ValidMovesGUI(self.graphics) if show_valid_moves else None
        self.gui = BoardGUI(self, self.graphics)
        self.ai = BlackAI(self, self.graphics) if ai_enabled else None
        self.ai2 = BlackAI(self, self.graphics, Players.WHITE) if white_ai_enabled else None
        self.infoboard_gui = InfoboardGUI(self, self.graphics)
        self.bind_events()

    def __str__(self):
        s = ''
        for y in range(8):
            for x in range(8):
                p = self.pawns[x][y]
                if p is None:
                    s += '_'
                elif p.player == Players.WHITE:
                    s += 'w'
                elif p.player == Players.BLACK:
                    s += 'b'
                else:
                    s += '?'
            s += '\n'
        return s

    __repr__ = __str__

    def has_pawn_at(self, x, y) -> bool:
        return self.pawns[x][y] is not None

    def get_pawn_at(self, x, y) -> Optional[Pawn]:
        return self.pawns[x][y]

    def set_pawn_at(self, x, y, pawn: Optional[Pawn]):
        self.pawns[x][y] = pawn

    def bind_events(self):
        self.graphics.canvas.bind('<Button-1>', self.start_drag)
        self.graphics.canvas.bind('<B1-Motion>', self.do_drag)
        self.graphics.canvas.bind('<ButtonRelease-1>', self.finish_drag)

    def start_drag(self, e):
        x, y = e.x // 64, e.y // 64

        if not self.is_valid_position(x, y):
            return Log.err(f'{x};{y} is not valid board position')

        if not self.has_pawn_at(x, y):
            return Log.err(f'no pawn at {x};{y}')

        if self.get_pawn_at(x, y).player != self.current_player:
            return Log.err(f'pawn at position {x};{y} is not current player\'s')

        # Position is valid and contains correct player's pawn. Start new move transaction.
        self.move_transaction = MoveTransaction(self.get_pawn_at(x, y), self)

    def do_drag(self, e):
        if self.move_transaction is not None:
            self.move_transaction.dragging(e)

    def finish_drag(self, e):
        x, y = e.x // 64, e.y // 64

        if self.valid_moves_gui is not None:
            self.valid_moves_gui.remove_all_moves()

        # Proceed only if there is ongoing transaction.
        if self.move_transaction is None:
            return

        # Ensure that end position is valid, otherwise rollback the transaction.
        if not self.is_valid_position(x, y):
            Log.err(f'{x};{y} is not valid board position')
            return self.move_transaction.rollback()

        # Check if played move is in valid moves list.
        played_valid_move = self.move_transaction.find_valid_move(x, y)

        if played_valid_move is not None:
            Log.info(f'Valid move played. From {self.move_transaction.pawn.x};{self.move_transaction.pawn.y} to {x};{y}'
                     + ' Committed transaction.')
            self.move_transaction.commit(played_valid_move)
        else:
            self.move_transaction.rollback()

        self.move_transaction = None
        print(str(self))
        self.infoboard_gui.update()

        if not self.check_for_win():
            self.check_for_draw()

        self.save_savegame('save.json')
        self.next_round()

    def next_round(self):
        if self.ai is not None:
            self.ai.try_to_play()
        if self.ai2 is not None:
            self.ai2.try_to_play()

    def load_savegame(self, file_name):
        with open(file_name) as f:
            # load savegame to dict
            doc = json.load(f)

            # apply loaded state
            self.score_tracker.reset()
            self.current_player = Players.from_id(doc['next_player'])
            for y in range(8):
                for x in range(8):
                    if doc['pawns'][y][x] != 0:
                        self.pawns[x][y] = Pawn(x, y, Players.from_id(doc['pawns'][y][x]), self.graphics)
            print(f'Game loaded from {file_name}!')

    def save_savegame(self, file_name):
        with open(file_name, 'w') as f:
            doc = {'next_player': self.current_player.id, 'pawns': []}
            for y in range(8):
                row = []
                for x in range(8):
                    e: Pawn = self.pawns[x][y]
                    if e is None:
                        row.append(0)
                    else:
                        if isinstance(e, Draughts):
                            row.append(-e.player.id)
                        else:
                            row.append(e.player.id)
                doc['pawns'].append(row)
            json.dump(doc, f)
            print(f'Board saved to {file_name}!')

    def check_for_win(self):
        black_pawns = 0
        white_pawns = 0

        for x in range(8):
            for y in range(8):
                pawn = self.get_pawn_at(x, y)

                if pawn is not None:
                    if pawn.player == Players.WHITE:
                        white_pawns += 1
                    elif pawn.player == Players.BLACK:
                        black_pawns += 1

        if white_pawns == 0:
            self.show_win_screen(Players.BLACK)
            return True
        if black_pawns == 0:
            self.show_win_screen(Players.WHITE)
            return True

    def check_for_draw(self):
        possible_moves = 0

        for x in range(8):
            for y in range(8):
                pawn = self.get_pawn_at(x, y)

                if pawn is not None and pawn.player == self.current_player:
                    possible_moves += len(pawn.get_valid_moves(self))

        Log.debug(f'Player {self.current_player.name} has {possible_moves} possible moves.')
        if possible_moves == 0:
            self.show_draw()

    def show_win_screen(self, winner: Player):
        self.graphics.canvas.create_rectangle(0, 0, 800, 800, fill='#744e30')
        self.graphics.canvas.create_text(384, 256,
                                         text=f'Winner: {winner.name}\nScore: {self.score_tracker.get_score(winner)}',
                                         font=('Arial', 32))

    def show_draw(self):
        self.graphics.canvas.create_rectangle(0, 0, 800, 800, fill='#744e30')
        self.graphics.canvas.create_text(384, 256,
                                         text=f'Draw! Player {self.current_player.name} has no moves left!\n' +
                                              f'White score: {self.score_tracker.get_score(Players.WHITE)}\n' +
                                              f'Black score: {self.score_tracker.get_score(Players.BLACK)}',
                                         font=('Arial', 32))

    @staticmethod
    def should_become_draught(x, y):
        return y == 0 or y == 7

    @staticmethod
    def is_valid_position(x, y):
        return 8 > x >= 0 and 8 > y >= 0


class Program:
    def __init__(self):
        # ------------- SETTINGS START ----------------
        black_ai_enabled = True
        white_ai_enabled = False
        show_valid_moves = True
        # -------------- SETTINGS END -----------------

        c = tkinter.Canvas(width=768, height=511)
        c.configure(background='#744e30')
        c.pack()
        custom_graphics = Graphics(c)

        b = Board(custom_graphics, black_ai_enabled, white_ai_enabled, show_valid_moves)
        b.load_savegame('default_savegame.json')
        b.save_savegame('save.json')
        print(b)

        tkinter.mainloop()


Program()
