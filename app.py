import pygame
import sys
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from models.player import HumanPlayer, RandomAI, HunterAI
from models.board import Board
from models.constants import SHIPS, GRID_SIZE, EMPTY, SHIP, HIT, MISS, SUNK

# ─────────────────────────────────────────────
#  Constants & Configuration
# ─────────────────────────────────────────────
CELL_SIZE = 40
MARGIN = 50
BOARD_WIDTH = GRID_SIZE * CELL_SIZE
WINDOW_WIDTH = (BOARD_WIDTH * 2) + (MARGIN * 3)
WINDOW_HEIGHT = BOARD_WIDTH + (MARGIN * 2) + 150

BG_COLOR = (18, 18, 24)       # Deeper dark
TEXT_COLOR = (240, 240, 245)
GRID_COLOR = (45, 45, 60)
GHOST_VALID = (80, 220, 120, 120)    # Soft green
GHOST_INVALID = (240, 80, 80, 120)   # Soft red

COLOR_MAP = {
    EMPTY: (25, 30, 45),     # Ocean dark blue
    SHIP: (60, 180, 140),    # Teal ship
    HIT: (230, 70, 70),      # Bright red hit
    MISS: (100, 110, 130),   # Slate gray miss
    SUNK: (150, 30, 30)      # Dark red sunk
}

# ─────────────────────────────────────────────
#  UI Helpers
# ─────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = (55, 60, 80)
        self.hover_color = (80, 90, 120)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, TEXT_COLOR, self.rect, 2, border_radius=8)
        
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

# ─────────────────────────────────────────────
#  Main Application State Machine
# ─────────────────────────────────────────────
class BattleshipGUI:
    """
    Main Application State Machine and Rendering Engine for Battleship.
    Handles the Pygame event loop, user interactions, and transitions 
    between MENU, PLACEMENT, PLAYING, and STATS states.
    It also coordinates the head-less fast-forward simulation engine.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Battleship - AI Simulation Engine")
        self.clock = pygame.time.Clock()
        
        self.font_large = pygame.font.SysFont("segoeui", 36, bold=True)
        self.font = pygame.font.SysFont("segoeui", 20, bold=True)
        self.font_small = pygame.font.SysFont("segoeui", 16)

        self.state = "MENU"
        
        # Menu variables
        self.mode = "PvAI"     
        self.ai1_type = "Hunter" 
        self.ai2_type = "Random" 
        self.player1_name = "Player 1"
        self.player2_name = "AI 2"
        self.num_matches = "100" # Default n matches
        self.active_input = None  

        # Game variables
        self.p1 = None
        self.p2 = None
        self.turn = 0
        self.game_over = False
        self.status_msg = ""
        self.ai_delay_timer = 0
        
        # Simulation stats
        self.stats = {}
        self.match_data = []

        # Placement variables
        self.ships_to_place = []
        self.is_horizontal = True

        self.setup_menu_buttons()

    def setup_menu_buttons(self):
        cx = WINDOW_WIDTH // 2
        self.btn_mode = Button(cx - 100, 100, 200, 40, f"Mode: {self.mode}", self.font)
        
        # Left column (Player 1)
        self.btn_ai1 = Button(cx - 220, 170, 200, 40, f"P1 AI: {self.ai1_type}", self.font)
        self.p1_rect = pygame.Rect(cx - 220, 240, 200, 40)
        
        # Right column (Player 2)
        self.btn_ai2 = Button(cx + 20, 170, 200, 40, f"P2 AI: {self.ai2_type}", self.font)
        self.p2_rect = pygame.Rect(cx + 20, 240, 200, 40)
        
        # Center bottom (N matches & Start)
        self.n_rect = pygame.Rect(cx - 100, 330, 200, 40)
        self.btn_start = Button(cx - 100, 410, 200, 50, "START", self.font_large)
        self.btn_menu = Button(cx - 100, 400, 200, 50, "BACK TO MENU", self.font)
        self.btn_graphs = Button(cx - 100, 470, 200, 50, "SHOW GRAPHS", self.font)

    # ─── MENU STATE ──────────────────────────────────────
    def handle_menu_events(self, event):
        if self.btn_mode.is_clicked(event):
            self.mode = "AIvAI" if self.mode == "PvAI" else "PvAI"
            self.btn_mode.text = f"Mode: {self.mode}"
        
        if self.mode == "AIvAI" and self.btn_ai1.is_clicked(event):
            self.ai1_type = "Random" if self.ai1_type == "Hunter" else "Hunter"
            self.btn_ai1.text = f"P1 AI: {self.ai1_type}"

        if self.btn_ai2.is_clicked(event):
            self.ai2_type = "Random" if self.ai2_type == "Hunter" else "Hunter"
            self.btn_ai2.text = f"P2 AI: {self.ai2_type}"

        if self.btn_start.is_clicked(event):
            self.start_game_setup()

        # Handle text box selection
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.p1_rect.collidepoint(event.pos): self.active_input = "P1"
            elif self.p2_rect.collidepoint(event.pos): self.active_input = "P2"
            elif self.mode == "AIvAI" and self.n_rect.collidepoint(event.pos): self.active_input = "N"
            else: self.active_input = None

        # Handle typing
        if event.type == pygame.KEYDOWN and self.active_input:
            if event.key == pygame.K_BACKSPACE:
                if self.active_input == "P1": self.player1_name = self.player1_name[:-1]
                elif self.active_input == "P2": self.player2_name = self.player2_name[:-1]
                elif self.active_input == "N": self.num_matches = self.num_matches[:-1]
            elif event.unicode.isprintable():
                if self.active_input == "P1" and len(self.player1_name) < 12:
                    self.player1_name += event.unicode
                elif self.active_input == "P2" and len(self.player2_name) < 12:
                    self.player2_name += event.unicode
                elif self.active_input == "N" and event.unicode.isdigit() and len(self.num_matches) < 5:
                    self.num_matches += event.unicode # Only allow digits for matches

    def draw_menu(self):
        title = self.font_large.render("BATTLESHIP SETUP", True, (120, 220, 255))
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH//2, 50)))

        self.btn_mode.draw(self.screen)
        self.btn_ai2.draw(self.screen)
        
        if self.mode == "AIvAI":
            self.btn_ai1.draw(self.screen)
        
        self._draw_input_box(self.p1_rect, self.player1_name, "Player 1 Name:", self.active_input == "P1")
        self._draw_input_box(self.p2_rect, self.player2_name, "Player 2 Name:", self.active_input == "P2")
        
        if self.mode == "AIvAI":
            self._draw_input_box(self.n_rect, self.num_matches, "Number of Matches (n):", self.active_input == "N")

        self.btn_start.draw(self.screen)

    def _draw_input_box(self, rect, text, label, is_active):
        color = (120, 220, 255) if is_active else (150, 150, 160)
        pygame.draw.rect(self.screen, (30, 35, 50), rect, border_radius=5)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=5)
        txt_surf = self.font.render(text + ("|" if is_active else ""), True, TEXT_COLOR)
        self.screen.blit(txt_surf, (rect.x + 10, rect.y + 8))
        lbl_surf = self.font_small.render(label, True, TEXT_COLOR)
        self.screen.blit(lbl_surf, (rect.x, rect.y - 22))

    # ─── SETUP & PLACEMENT STATE ─────────────────────────
    def start_game_setup(self):
        n = int(self.num_matches) if self.num_matches else 1
        
        if self.mode == "AIvAI" and n > 1:
            self.state = "SIMULATING"
            self.run_simulation(n)
            return

        # Create P1
        if self.mode == "PvAI":
            self.p1 = HumanPlayer(self.player1_name)
            self.ships_to_place = SHIPS.copy()
            self.state = "PLACEMENT"
        else:
            AI1 = HunterAI if self.ai1_type == "Hunter" else RandomAI
            self.p1 = AI1(self.player1_name)
            self.p1.board.place_all_random()
            self.state = "PLAYING"

        # Create P2
        AI2 = HunterAI if self.ai2_type == "Hunter" else RandomAI
        self.p2 = AI2(self.player2_name)
        self.p2.board.place_all_random()

        self.turn = 0
        self.game_over = False
        self.status_msg = "Game Started!"

    def handle_placement_events(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.is_horizontal = not self.is_horizontal

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            board_x, board_y = MARGIN, MARGIN + 50
            
            if board_x <= mouse_x < board_x + BOARD_WIDTH and board_y <= mouse_y < board_y + BOARD_WIDTH:
                col = (mouse_x - board_x) // CELL_SIZE
                row = (mouse_y - board_y) // CELL_SIZE
                
                name, length = self.ships_to_place[0]
                if self.p1.board.can_place(col, row, length, self.is_horizontal):
                    self.p1.board.place_ship(name, col, row, length, self.is_horizontal)
                    self.ships_to_place.pop(0)
                    
                    if not self.ships_to_place:
                        self.state = "PLAYING"
                        self.status_msg = f"{self.p1.name}'s turn!"

    def draw_placement(self):
        self.draw_grid(self.p1.board, MARGIN, MARGIN + 50, "PLACE YOUR FLEET", hide_ships=False)
        msg1 = self.font.render("Press 'R' to rotate ship.", True, (255, 215, 0))
        self.screen.blit(msg1, (MARGIN, WINDOW_HEIGHT - 80))

        if self.ships_to_place:
            name, length = self.ships_to_place[0]
            msg2 = self.font.render(f"Placing: {name} (Length: {length})", True, TEXT_COLOR)
            self.screen.blit(msg2, (MARGIN, WINDOW_HEIGHT - 50))

            mouse_x, mouse_y = pygame.mouse.get_pos()
            board_x, board_y = MARGIN, MARGIN + 50
            if board_x <= mouse_x < board_x + BOARD_WIDTH and board_y <= mouse_y < board_y + BOARD_WIDTH:
                col = (mouse_x - board_x) // CELL_SIZE
                row = (mouse_y - board_y) // CELL_SIZE
                valid = self.p1.board.can_place(col, row, length, self.is_horizontal)
                color = GHOST_VALID if valid else GHOST_INVALID
                ghost_surface = pygame.Surface((CELL_SIZE * (length if self.is_horizontal else 1), 
                                                CELL_SIZE * (1 if self.is_horizontal else length)), pygame.SRCALPHA)
                ghost_surface.fill(color)
                self.screen.blit(ghost_surface, (board_x + col * CELL_SIZE, board_y + row * CELL_SIZE))

    # ─── PLAYING STATE ───────────────────────────────────
    def handle_playing_events(self, event):
        if self.game_over and event.type == pygame.MOUSEBUTTONDOWN:
            self.state = "MENU" 
            return

        current_player = self.p1 if self.turn % 2 == 0 else self.p2
        defender = self.p2 if self.turn % 2 == 0 else self.p1

        if isinstance(current_player, HumanPlayer) and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            board_x, board_y = MARGIN, MARGIN + 50
            
            if board_x <= mouse_x < board_x + BOARD_WIDTH and board_y <= mouse_y < board_y + BOARD_WIDTH:
                col = (mouse_x - board_x) // CELL_SIZE
                row = (mouse_y - board_y) // CELL_SIZE

                if (col, row) not in current_player.tracking_grid.shots_received:
                    current_player.tracking_grid.shots_received.add((col, row))
                    result = defender.board.receive_shot(col, row)
                    current_player.record_shot_result(col, row, result)
                    self.process_shot_result(current_player, defender, result)

    def update_playing(self):
        if self.game_over: return
        current_player = self.p1 if self.turn % 2 == 0 else self.p2
        defender = self.p2 if self.turn % 2 == 0 else self.p1

        if not isinstance(current_player, HumanPlayer):
            self.ai_delay_timer += self.clock.get_time()
            if self.ai_delay_timer > 600: 
                col, row = current_player.choose_shot()
                result = defender.board.receive_shot(col, row)
                current_player.record_shot_result(col, row, result)
                self.process_shot_result(current_player, defender, result)
                self.ai_delay_timer = 0

    def process_shot_result(self, attacker, defender, result):
        if result == "hit": self.status_msg = f"{attacker.name} landed a HIT!"
        elif result.startswith("sunk"): self.status_msg = f"{attacker.name} SUNK the {result.split(':')[1]}!"
        else: self.status_msg = f"{attacker.name} missed."

        if defender.board.all_sunk():
            self.status_msg = f"GAME OVER! {attacker.name} WINS! (Click to return)"
            self.game_over = True
        else:
            self.turn += 1

    def draw_playing(self):
        left_x, right_x = MARGIN, MARGIN * 2 + BOARD_WIDTH
        y_offset = MARGIN + 50

        if self.mode == "PvAI":
            self.draw_grid(self.p1.tracking_grid, left_x, y_offset, "ENEMY WATERS", hide_ships=True)
            self.draw_grid(self.p1.board, right_x, y_offset, f"{self.p1.name.upper()}'S FLEET", hide_ships=False)
        else:
            self.draw_grid(self.p1.board, left_x, y_offset, f"{self.p1.name} (P1)", hide_ships=False)
            self.draw_grid(self.p2.board, right_x, y_offset, f"{self.p2.name} (P2)", hide_ships=False)

        msg_surf = self.font_large.render(self.status_msg, True, (255, 215, 0))
        self.screen.blit(msg_surf, msg_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 60)))

    # ─── CORE DRAWING METHOD ─────────────────────────────
    def draw_grid(self, board, x_offset, y_offset, title, hide_ships):
        title_surface = self.font.render(title, True, TEXT_COLOR)
        self.screen.blit(title_surface, (x_offset, y_offset - 30))

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cell_state = board.grid[row][col]
                if hide_ships and cell_state == SHIP: cell_state = EMPTY

                rect = pygame.Rect(x_offset + (col * CELL_SIZE), y_offset + (row * CELL_SIZE), CELL_SIZE - 2, CELL_SIZE - 2)
                pygame.draw.rect(self.screen, COLOR_MAP.get(cell_state, COLOR_MAP[EMPTY]), rect, border_radius=4)
                
                if cell_state in (HIT, SUNK):
                    pygame.draw.line(self.screen, (255,255,255), (rect.left+5, rect.top+5), (rect.right-5, rect.bottom-5), 3)
                    pygame.draw.line(self.screen, (255,255,255), (rect.left+5, rect.bottom-5), (rect.right-5, rect.top+5), 3)
                elif cell_state == MISS:
                    pygame.draw.circle(self.screen, (150,150,150), rect.center, 6)

    # ─── SIMULATION & STATS ──────────────────────────────
    def run_simulation(self, n):
        """
        Runs a headless simulation of 'n' matches between two AI players.
        This bypasses the Pygame rendering loop entirely for maximum performance,
        collecting highly granular data on hit rates, turns, and decision times.
        """
        self.stats = {"total": n, self.player1_name: 0, self.player2_name: 0}
        self.match_data = []
        
        AI1 = HunterAI if self.ai1_type == "Hunter" else RandomAI
        AI2 = HunterAI if self.ai2_type == "Hunter" else RandomAI

        for i in range(n):
            p1 = AI1(self.player1_name)
            p2 = AI2(self.player2_name)
            p1.board.place_all_random()
            p2.board.place_all_random()
            
            turn = 0
            while True:
                attacker = p1 if turn % 2 == 0 else p2
                defender = p2 if turn % 2 == 0 else p1
                
                col, row = attacker.choose_shot()
                result = defender.board.receive_shot(col, row)
                attacker.record_shot_result(col, row, result)
                
                if defender.board.all_sunk():
                    self.stats[attacker.name] += 1
                    
                    # Record detailed match stats
                    match_stats = {
                        "winner": attacker.name,
                        "turns": turn // 2,
                        "p1_shots": p1.shots_fired,
                        "p1_hits": p1.hits_landed,
                        "p1_explor": p1.exploration_shots,
                        "p1_exploit": p1.exploitation_shots,
                        "p1_time": p1.decision_time_total,
                        "p2_shots": p2.shots_fired,
                        "p2_hits": p2.hits_landed,
                        "p2_explor": p2.exploration_shots,
                        "p2_exploit": p2.exploitation_shots,
                        "p2_time": p2.decision_time_total,
                        "p1_ships_left": sum(1 for s in p1.board.ships if not s['sunk']),
                        "p2_ships_left": sum(1 for s in p2.board.ships if not s['sunk'])
                    }
                    self.match_data.append(match_stats)
                    break
                turn += 1
                
        self.state = "STATS"

    def show_matplotlib_graphs(self):
        """
        Processes the simulation match_data using Numpy and displays four
        distinct Seaborn plots (Pie Chart, Histogram, Boxplot, and Stacked Bar)
        in a separate Matplotlib window.
        """
        if not self.match_data: return
        
        sns.set_theme(style="darkgrid")
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Battleship Simulation Statistics', fontsize=16)

        winners = [m["winner"] for m in self.match_data]
        p1_wins = winners.count(self.player1_name)
        p2_wins = winners.count(self.player2_name)
        
        # 1. Win Rate Pie Chart
        axs[0, 0].pie([p1_wins, p2_wins], labels=[f"{self.player1_name} ({self.ai1_type})", f"{self.player2_name} ({self.ai2_type})"], 
                      autopct='%1.1f%%', colors=['#4CAF50', '#F44336'], startangle=90)
        axs[0, 0].set_title('Win Rate')

        # 2. Average Turns to Victory Distribution
        turns = [m["turns"] for m in self.match_data]
        sns.histplot(turns, kde=True, ax=axs[0, 1], color='#2196F3')
        axs[0, 1].set_title('Turns to Victory Distribution')
        axs[0, 1].set_xlabel('Turns')
        axs[0, 1].set_ylabel('Frequency')

        # 3. Average Hit Accuracy Bar Chart
        p1_acc = np.mean([m["p1_hits"] / max(1, m["p1_shots"]) for m in self.match_data]) * 100
        p2_acc = np.mean([m["p2_hits"] / max(1, m["p2_shots"]) for m in self.match_data]) * 100
        
        axs[1, 0].bar([self.player1_name, self.player2_name], [p1_acc, p2_acc], color=['#4CAF50', '#F44336'])
        axs[1, 0].set_title('Average Hit Accuracy (%)')
        axs[1, 0].set_ylabel('Accuracy (%)')
        axs[1, 0].set_ylim(0, max(100, max(p1_acc, p2_acc) + 10))

        # 4. Average Shots Profile (Searching vs Hunting)
        p1_explor_avg = np.mean([m["p1_explor"] for m in self.match_data])
        p1_exploit_avg = np.mean([m["p1_exploit"] for m in self.match_data])
        p2_explor_avg = np.mean([m["p2_explor"] for m in self.match_data])
        p2_exploit_avg = np.mean([m["p2_exploit"] for m in self.match_data])
        
        labels = [self.player1_name, self.player2_name]
        explor_means = [p1_explor_avg, p2_explor_avg]
        exploit_means = [p1_exploit_avg, p2_exploit_avg]
        
        axs[1, 1].bar(labels, explor_means, label='Random Searching (Explore)', color='#2196F3')
        axs[1, 1].bar(labels, exploit_means, bottom=explor_means, label='Targeted Hunting (Exploit)', color='#FF9800')
        axs[1, 1].set_title('Average Shots Profile per Game')
        axs[1, 1].set_ylabel('Number of Shots')
        axs[1, 1].legend()

        plt.tight_layout()
        plt.show()

    def draw_stats(self):
        title = self.font_large.render("SIMULATION STATISTICS", True, (120, 220, 255))
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH//2, 80)))
        
        n_text = self.font.render(f"Total Matches Simulated: {self.stats['total']}", True, TEXT_COLOR)
        
        p1_wins = self.stats[self.player1_name]
        p2_wins = self.stats[self.player2_name]
        p1_pct = (p1_wins / self.stats['total']) * 100
        p2_pct = (p2_wins / self.stats['total']) * 100

        p1_text = self.font_large.render(f"{self.player1_name} ({self.ai1_type}): {p1_wins} Wins ({p1_pct:.1f}%)", True, (80, 220, 120))
        p2_text = self.font_large.render(f"{self.player2_name} ({self.ai2_type}): {p2_wins} Wins ({p2_pct:.1f}%)", True, (240, 80, 80))
        
        avg_turns = np.mean([m["turns"] for m in self.match_data]) if self.match_data else 0
        turns_text = self.font.render(f"Average Turns per Game: {avg_turns:.1f}", True, (200, 200, 200))
        
        self.screen.blit(n_text, n_text.get_rect(center=(WINDOW_WIDTH//2, 150)))
        self.screen.blit(turns_text, turns_text.get_rect(center=(WINDOW_WIDTH//2, 190)))
        self.screen.blit(p1_text, p1_text.get_rect(center=(WINDOW_WIDTH//2, 260)))
        self.screen.blit(p2_text, p2_text.get_rect(center=(WINDOW_WIDTH//2, 330)))
        
        self.btn_graphs.draw(self.screen)
        self.btn_menu.draw(self.screen)

    # ─── MAIN LOOP ───────────────────────────────────────
    def run(self):
        while True:
            self.screen.fill(BG_COLOR)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == "MENU": self.handle_menu_events(event)
                elif self.state == "PLACEMENT": self.handle_placement_events(event)
                elif self.state == "PLAYING": self.handle_playing_events(event)
                elif self.state == "STATS":
                    if self.btn_menu.is_clicked(event):
                        self.state = "MENU"
                    elif self.btn_graphs.is_clicked(event):
                        self.show_matplotlib_graphs()

            if self.state == "MENU": self.draw_menu()
            elif self.state == "PLACEMENT": self.draw_placement()
            elif self.state == "PLAYING":
                self.update_playing()
                self.draw_playing()
            elif self.state == "STATS": self.draw_stats()

            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    app = BattleshipGUI()
    app.run()

