try:
    import pygame
    import pygame.gfxdraw
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from model.board import BoardState
from model.rules import legal_moves, is_checkmate, is_draw, is_in_check, find_king

SQ         = 80
BOARD_SIZE = SQ * 8
SIDEBAR    = 280
WIDTH      = BOARD_SIZE + SIDEBAR
HEIGHT     = BOARD_SIZE + 60

C_BG          = (15,  15,  20)
C_LIGHT       = (235, 215, 185)
C_DARK        = (165, 115,  75)
C_SIDEBAR_BG  = (22,  22,  30)
C_SIDEBAR_ACC = (80,  60, 140)
C_WHITE_PIECE = (245, 240, 225)
C_BLACK_PIECE = (30,   25,  20)
C_TEXT        = (210, 205, 195)
C_SUBTEXT     = (130, 120, 110)
C_BTN         = (55,  50,  80)
C_BTN_HOV     = (90,  80, 130)

PIECE_UNICODE = {
     6:'♔', -6:'♚',
     5:'♕', -5:'♛',
     4:'♖', -4:'♜',
     3:'♗', -3:'♝',
     2:'♘', -2:'♞',
     1:'♙', -1:'♟',
}

def draw_rounded_rect(surface, color, rect, radius=10):
    x, y, w, h = rect
    r = min(radius, w//2, h//2)
    pygame.draw.rect(surface, color, (x+r, y, w-2*r, h))
    pygame.draw.rect(surface, color, (x, y+r, w, h-2*r))
    for cx, cy in [(x+r, y+r), (x+w-r, y+r), (x+r, y+h-r), (x+w-r, y+h-r)]:
        pygame.draw.circle(surface, color, (cx, cy), r)

def alpha_rect(surface, color_rgba, rect):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    s.fill(color_rgba)
    surface.blit(s, (rect[0], rect[1]))

class ChessGUI:
    def __init__(self):
        if not PYGAME_AVAILABLE:
            raise RuntimeError("pip install pygame")
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("ChessMind")
        self._load_fonts()
        self._render_pieces()

        self.selected    = None
        self.last_move   = None
        self.move_log    = []
        self.message     = ""
        self.ai_thinking = False
        self.flip_board  = False
        self.hovered_btn = None

        self.buttons = {
            'new':   pygame.Rect(BOARD_SIZE+20, 160, SIDEBAR-40, 44),
            'flip':  pygame.Rect(BOARD_SIZE+20, 215, SIDEBAR-40, 44),
            'watch': pygame.Rect(BOARD_SIZE+20, 270, SIDEBAR-40, 44),
        }
        self.clock = pygame.time.Clock()

    def _load_fonts(self):
        candidates = ["segoeuisymbol", "symbola", "dejavusans", None]
        self.font_piece = None
        for name in candidates:
            try:
                f = pygame.font.SysFont(name, 58) if name else pygame.font.Font(None, 58)
                test = f.render("♔", True, (255,255,255))
                if test.get_width() > 8:
                    self.font_piece = f
                    break
            except:
                pass
        if not self.font_piece:
            self.font_piece = pygame.font.Font(None, 58)

        self.font_title  = pygame.font.SysFont("georgia", 26, bold=True)
        self.font_label  = pygame.font.SysFont("georgia", 14)
        self.font_coord  = pygame.font.SysFont("consolas", 12)
        self.font_log    = pygame.font.SysFont("consolas", 13)
        self.font_btn    = pygame.font.SysFont("georgia", 13, bold=True)
        self.font_msg    = pygame.font.SysFont("georgia", 17, bold=True)
        self.font_sub    = pygame.font.SysFont("georgia", 13)

    def _render_pieces(self):
        self.piece_surfs = {}
        for code, sym in PIECE_UNICODE.items():
            color = C_WHITE_PIECE if code > 0 else C_BLACK_PIECE
            self.piece_surfs[code] = self.font_piece.render(sym, True, color)

    def sq_to_screen(self, row, col):
        if self.flip_board:
            return (7-col)*SQ, row*SQ
        return col*SQ, (7-row)*SQ

    def screen_to_sq(self, px, py):
        c, r = px//SQ, 7-(py//SQ)
        if self.flip_board:
            c, r = 7-c, 7-r
        if 0 <= r < 8 and 0 <= c < 8:
            return r, c
        return None

    def draw(self, state, moves=None):
        self.screen.fill(C_BG)
        self._draw_board(state, moves)
        self._draw_pieces(state)
        self._draw_coords()
        self._draw_sidebar(state)
        self._draw_bar()
        pygame.display.flip()
        self.clock.tick(60)

    def _draw_board(self, state, moves):
        for row in range(8):
            for col in range(8):
                x, y = self.sq_to_screen(row, col)
                color = C_LIGHT if (row+col)%2==0 else C_DARK
                pygame.draw.rect(self.screen, color, (x, y, SQ, SQ))

        # Dernier coup
        if self.last_move:
            for r, c in [self.last_move[0], self.last_move[1]]:
                x, y = self.sq_to_screen(r, c)
                alpha_rect(self.screen, (100,180,255,90), (x, y, SQ, SQ))

        # Roi en échec
        if is_in_check(state, state.current_player):
            kr, kc = find_king(state.board, state.current_player)
            x, y = self.sq_to_screen(kr, kc)
            alpha_rect(self.screen, (220,50,50,160), (x, y, SQ, SQ))

        # Sélection
        if self.selected:
            x, y = self.sq_to_screen(*self.selected)
            alpha_rect(self.screen, (255,220,60,140), (x, y, SQ, SQ))

        # Coups légaux
        if moves and self.selected:
            for m in moves:
                if m[0] == self.selected:
                    tr, tc = m[1]
                    x, y = self.sq_to_screen(tr, tc)
                    s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
                    if state.board[tr][tc] != 0:
                        pygame.draw.circle(s, (100,200,100,110), (SQ//2,SQ//2), SQ//2-3, 6)
                    else:
                        pygame.draw.circle(s, (100,200,100,120), (SQ//2,SQ//2), 13)
                    self.screen.blit(s, (x, y))

        pygame.draw.rect(self.screen, (50,45,60), (0,0,BOARD_SIZE,BOARD_SIZE), 2)

    def _draw_pieces(self, state):
        for row in range(8):
            for col in range(8):
                p = state.board[row][col]
                if p == 0: continue
                surf = self.piece_surfs.get(p)
                if not surf: continue
                x, y = self.sq_to_screen(row, col)
                pw, ph = surf.get_size()
                ox, oy = (SQ-pw)//2, (SQ-ph)//2

                # Contour pour les pièces noires
                if p < 0:
                    outline = self.font_piece.render(PIECE_UNICODE[p], True, (190,180,165))
                    for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
                        self.screen.blit(outline, (x+ox+dx, y+oy+dy))

                self.screen.blit(surf, (x+ox, y+oy))

    def _draw_coords(self):
        cols = 'abcdefgh'
        for i in range(8):
            ci = i if not self.flip_board else 7-i
            ri = 7-i if not self.flip_board else i
            color = C_DARK if i%2==0 else C_LIGHT
            lc = self.font_coord.render(cols[ci], True, color)
            self.screen.blit(lc, (i*SQ+SQ-14, BOARD_SIZE-15))
            color = C_DARK if (7-i)%2==0 else C_LIGHT
            lr = self.font_coord.render(str(ri+1), True, color)
            self.screen.blit(lr, (3, i*SQ+3))

    def _draw_sidebar(self, state):
        pygame.draw.rect(self.screen, C_SIDEBAR_BG, (BOARD_SIZE, 0, SIDEBAR, HEIGHT))
        pygame.draw.line(self.screen, (50,45,70), (BOARD_SIZE,0), (BOARD_SIZE,HEIGHT), 2)

        # Titre
        t = self.font_title.render("ChessMind", True, (210,185,255))
        self.screen.blit(t, (BOARD_SIZE+20, 18))
        s = self.font_sub.render("Moteur IA — Self-play", True, C_SUBTEXT)
        self.screen.blit(s, (BOARD_SIZE+22, 48))
        pygame.draw.line(self.screen, C_SIDEBAR_ACC, (BOARD_SIZE+20,68),(WIDTH-20,68),1)

        # Joueur courant
        dot = C_WHITE_PIECE if state.current_player==1 else (70,70,70)
        pygame.draw.circle(self.screen, dot, (BOARD_SIZE+30, 93), 7)
        pygame.draw.circle(self.screen, C_SUBTEXT, (BOARD_SIZE+30, 93), 7, 1)
        pl = "Blancs" if state.current_player==1 else "Noirs"
        self.screen.blit(self.font_label.render(f"Tour des {pl}", True, C_TEXT), (BOARD_SIZE+45, 85))
        self.screen.blit(self.font_label.render(f"Coup n° {state.fullmove_number}", True, C_SUBTEXT), (BOARD_SIZE+45, 102))
        pygame.draw.line(self.screen, (40,38,55),(BOARD_SIZE+20,120),(WIDTH-20,120),1)

        # Boutons
        labels = {'new':'Nouvelle partie','flip':'Retourner le plateau','watch':'IA vs IA'}
        for key, rect in self.buttons.items():
            color = C_BTN_HOV if self.hovered_btn==key else C_BTN
            draw_rounded_rect(self.screen, color, (rect.x,rect.y,rect.w,rect.h), 8)
            lbl = self.font_btn.render(labels[key], True, C_TEXT)
            self.screen.blit(lbl, (rect.x+(rect.w-lbl.get_width())//2, rect.y+(rect.h-lbl.get_height())//2))

        # Séparateur historique
        pygame.draw.line(self.screen,(40,38,55),(BOARD_SIZE+20,330),(WIDTH-20,330),1)
        self.screen.blit(self.font_sub.render("Historique des coups",True,C_SUBTEXT),(BOARD_SIZE+20,338))

        y = 358
        for entry in self.move_log[-15:]:
            self.screen.blit(self.font_log.render(entry, True, C_SUBTEXT), (BOARD_SIZE+20, y))
            y += 17

        # IA réfléchit
        if self.ai_thinking:
            t2 = pygame.time.get_ticks()/400
            a = int(140 + 115*math.sin(t2))
            think = self.font_sub.render("IA réfléchit...", True, (a, a//2, 255))
            self.screen.blit(think, (BOARD_SIZE+20, HEIGHT-55))

    def _draw_bar(self):
        pygame.draw.rect(self.screen,(18,16,24),(0,BOARD_SIZE,BOARD_SIZE,60))
        pygame.draw.line(self.screen,(40,38,55),(0,BOARD_SIZE),(BOARD_SIZE,BOARD_SIZE),1)
        if self.message:
            msg = self.font_msg.render(self.message, True, (220,200,100))
            self.screen.blit(msg, (20, BOARD_SIZE+18))

    def add_to_log(self, move, player):
        cols = 'abcdefgh'
        (fr,fc),(tr,tc),promo = move
        n = f"{cols[fc]}{fr+1}{cols[tc]}{tr+1}"
        if promo: n += {5:'=Q',4:'=R',3:'=B',2:'=N'}.get(promo,'=Q')
        dot = "●" if player==1 else "○"
        num = len(self.move_log)//2+1
        if player==1:
            self.move_log.append(f"{num:2d}. {dot} {n}")
        elif self.move_log:
            self.move_log[-1] += f"  {dot} {n}"

    def handle_hover(self, pos):
        self.hovered_btn = None
        for k, r in self.buttons.items():
            if r.collidepoint(pos):
                self.hovered_btn = k

    def get_sq(self, pos):
        px, py = pos
        if px >= BOARD_SIZE or py >= BOARD_SIZE: return None
        return self.screen_to_sq(px, py)

    def get_btn(self, pos):
        for k, r in self.buttons.items():
            if r.collidepoint(pos): return k
        return None

    def close(self):
        pygame.quit()


def run_gui(net=None):
    import threading, time
    from controller.self_play import NeuralAgent
    from controller.trainer import load_model
    from model.neural_net import ChessNet

    if net is None:
        net = ChessNet()
        load_model(net)

    ai = NeuralAgent(net, temperature=0.3)
    gui = ChessGUI()
    state = BoardState()
    mode = 'play'
    game_over = False
    ai_pending = None
    watch_timer = 0
    moves = legal_moves(state)

    gui.message = "Jouez les Blancs — cliquez pour déplacer"
    gui.draw(state, moves)

    def think(s, ms):
        nonlocal ai_pending
        gui.ai_thinking = True
        time.sleep(0.2)
        ai_pending = ai.select_move(s, ms)
        gui.ai_thinking = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEMOTION:
                gui.handle_hover(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                btn = gui.get_btn(event.pos)

                if btn == 'new':
                    state = BoardState(); gui.selected=None; gui.last_move=None
                    gui.move_log=[]; game_over=False; mode='play'
                    moves=legal_moves(state); gui.message="Nouvelle partie — Jouez les Blancs"
                    ai_pending=None

                elif btn == 'flip':
                    gui.flip_board = not gui.flip_board

                elif btn == 'watch':
                    state=BoardState(); gui.selected=None; gui.last_move=None
                    gui.move_log=[]; game_over=False; mode='watch'
                    moves=legal_moves(state); gui.message="IA vs IA"
                    watch_timer=pygame.time.get_ticks(); ai_pending=None

                elif not game_over and mode=='play' and state.current_player==1:
                    sq = gui.get_sq(event.pos)
                    if sq:
                        r, c = sq
                        if gui.selected is None:
                            if state.board[r][c] > 0:
                                gui.selected = sq
                        else:
                            move = next((m for m in moves if m[0]==gui.selected and m[1]==sq), None)
                            if move:
                                gui.add_to_log(move, 1)
                                state.apply_move(move); gui.last_move=move; gui.selected=None
                                moves=legal_moves(state)
                                if is_checkmate(state):
                                    gui.message="Échec et mat ! Blancs gagnent !"; game_over=True
                                elif is_draw(state):
                                    gui.message="Nulle !"; game_over=True
                                else:
                                    gui.message="IA réfléchit..."
                                    threading.Thread(target=think,args=(state.copy(),moves),daemon=True).start()
                            else:
                                gui.selected = sq if state.board[r][c]>0 else None

        # IA joue (mode play)
        if not game_over and mode=='play' and state.current_player==-1 and ai_pending:
            m = ai_pending; ai_pending=None
            gui.add_to_log(m, -1)
            state.apply_move(m); gui.last_move=m
            moves=legal_moves(state)
            if is_checkmate(state):
                gui.message="Échec et mat ! Noirs gagnent !"; game_over=True
            elif is_draw(state):
                gui.message="Nulle !"; game_over=True
            else:
                gui.message="Jouez les Blancs"

        # IA vs IA
        if not game_over and mode=='watch':
            now=pygame.time.get_ticks()
            if now-watch_timer > 600 and moves:
                watch_timer=now
                m=ai.select_move(state,moves)
                gui.add_to_log(m,state.current_player)
                state.apply_move(m); gui.last_move=m
                moves=legal_moves(state)
                if is_checkmate(state):
                    w="Blancs" if state.current_player==-1 else "Noirs"
                    gui.message=f"Échec et mat ! {w} gagnent !"; game_over=True
                elif is_draw(state):
                    gui.message="Nulle !"; game_over=True

        gui.draw(state, moves if not game_over else [])

    gui.close()


if __name__ == "__main__":
    run_gui()
