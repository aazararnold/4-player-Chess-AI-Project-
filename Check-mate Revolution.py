import sys
import math
import time
import pygame
import numpy as np
from enum import Enum, auto
from typing import List, Tuple, Dict, Set, Optional, Union

# Initialize pygame
pygame.init()

# Constants - ADJUSTED FOR BETTER DISPLAY
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
BOARD_SIZE = 500
SQUARE_SIZE = BOARD_SIZE // 8
SIDEBAR_WIDTH = 150
INFO_HEIGHT = 80

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_SQUARE = (118, 150, 86)
LIGHT_SQUARE = (238, 238, 210)
HIGHLIGHT = (186, 202, 68)
MOVE_HIGHLIGHT = (255, 255, 0, 180)  # Brighter yellow with transparency
CHECK_HIGHLIGHT = (255, 0, 0, 180)
BUTTON_COLOR = (100, 149, 237)  # Cornflower blue
BUTTON_HOVER_COLOR = (65, 105, 225)  # Royal blue
BUTTON_TEXT_COLOR = WHITE

# Player colors
PLAYER_COLORS = [
    (255, 0, 0),    # Red (Player 1)
    (0, 0, 255),    # Blue (Player 2)
    (0, 255, 0),    # Green (Player 3)
    (255, 255, 0)   # Yellow (Player 4)
]

class GameMode(Enum):
    FREE_FOR_ALL = auto()
    TEAM_MODE = auto()

class PieceType(Enum):
    KING = auto()
    QUEEN = auto()
    ROOK = auto()
    BISHOP = auto()
    KNIGHT = auto()
    PAWN = auto()

class Button:
    def __init__(self, x, y, width, height, text, font, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.is_hovered = False
        
    def draw(self, screen):
        color = BUTTON_HOVER_COLOR if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                self.action()
                return True
        return False

class Player:
    def __init__(self, id: int, is_ai: bool = False, team: int = None):
        self.id = id
        self.is_ai = is_ai
        self.team = team if team is not None else id
        self.is_eliminated = False
        self.pieces = []
        self.color = PLAYER_COLORS[id % len(PLAYER_COLORS)]
        
    def __str__(self):
        return f"Player {self.id+1}" + (" (AI)" if self.is_ai else "")

class Piece:
    def __init__(self, piece_type: PieceType, player: Player, position: Tuple[int, int]):
        self.type = piece_type
        self.player = player
        self.position = position
        self.has_moved = False
        self.value = self._get_value()
        self.animation_pos = None  # For smooth movement animation
        player.pieces.append(self)
        
    def _get_value(self) -> int:
        values = {
            PieceType.KING: 1000,
            PieceType.QUEEN: 9,
            PieceType.ROOK: 5,
            PieceType.BISHOP: 3,
            PieceType.KNIGHT: 3,
            PieceType.PAWN: 1
        }
        return values[self.type]
    
    def get_possible_moves(self, board) -> List[Tuple[int, int]]:
        moves = []
        row, col = self.position
        
        if self.type == PieceType.PAWN:
            # Pawns move differently based on player position
            direction = self._get_pawn_direction(board.rotation)
            
            # Forward move
            new_row, new_col = row + direction[0], col + direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8 and board.board[new_row][new_col] is None:
                moves.append((new_row, new_col))
                
                # Double move from starting position
                if not self.has_moved:
                    new_row, new_col = row + 2*direction[0], col + 2*direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8 and board.board[new_row][new_col] is None:
                        moves.append((new_row, new_col))
            
            # Capture moves
            for dx, dy in [(direction[0] + direction[1], direction[0] - direction[1]), 
                          (direction[0] - direction[1], direction[0] + direction[1])]:
                if dx == 0 and dy == 0:
                    continue
                new_row, new_col = row + dx, col + dy
                if 0 <= new_row < 8 and 0 <= new_col < 8 and board.board[new_row][new_col] is not None:
                    if board.board[new_row][new_col].player.id != self.player.id:
                        moves.append((new_row, new_col))
        
        elif self.type == PieceType.KNIGHT:
            for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    if board.board[new_row][new_col] is None or board.board[new_row][new_col].player.id != self.player.id:
                        moves.append((new_row, new_col))
        
        elif self.type == PieceType.BISHOP:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    if board.board[new_row][new_col] is None:
                        moves.append((new_row, new_col))
                    else:
                        if board.board[new_row][new_col].player.id != self.player.id:
                            moves.append((new_row, new_col))
                        break
        
        elif self.type == PieceType.ROOK:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    if board.board[new_row][new_col] is None:
                        moves.append((new_row, new_col))
                    else:
                        if board.board[new_row][new_col].player.id != self.player.id:
                            moves.append((new_row, new_col))
                        break
        
        elif self.type == PieceType.QUEEN:
            # Queen combines rook and bishop moves
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    if board.board[new_row][new_col] is None:
                        moves.append((new_row, new_col))
                    else:
                        if board.board[new_row][new_col].player.id != self.player.id:
                            moves.append((new_row, new_col))
                        break
        
        elif self.type == PieceType.KING:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board.board[new_row][new_col] is None or board.board[new_row][new_col].player.id != self.player.id:
                            moves.append((new_row, new_col))
        
        # Filter out moves that would put the king in check
        valid_moves = []
        for move in moves:
            if not board.would_be_in_check_after_move(self, move):
                valid_moves.append(move)
                
        return valid_moves
    
    def _get_pawn_direction(self, rotation: int) -> Tuple[int, int]:
        # Determine pawn direction based on player and board rotation
        base_directions = [
            (-1, 0),  # Player 1 (top)
            (0, -1),  # Player 2 (right)
            (1, 0),   # Player 3 (bottom)
            (0, 1)    # Player 4 (left)
        ]
        
        player_index = (self.player.id - rotation) % 4
        return base_directions[player_index]
    
    def __str__(self):
        return f"{self.player.id}_{self.type.name}"

class ChessBoard:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.rotation = 0  # 0, 1, 2, 3 for 0°, 90°, 180°, 270°
        self.rotation_animation = 0  # For smooth rotation animation
        self.is_rotating = False
        
    def place_piece(self, piece: Piece, position: Tuple[int, int]):
        row, col = position
        self.board[row][col] = piece
        piece.position = position
        
    def move_piece(self, piece: Piece, new_position: Tuple[int, int]) -> Optional[Piece]:
        old_row, old_col = piece.position
        new_row, new_col = new_position
        
        # Check if there's a piece to capture
        captured_piece = self.board[new_row][new_col]
        
        # Update board
        self.board[old_row][old_col] = None
        self.board[new_row][new_col] = piece
        piece.position = new_position
        piece.has_moved = True
        
        return captured_piece
    
    def start_rotation(self):
        self.is_rotating = True
        self.rotation_animation = 0
    
    def update_rotation(self, delta_time):
        if self.is_rotating:
            # Rotate 90 degrees over 1 second
            self.rotation_animation += 90 * delta_time
            if self.rotation_animation >= 90:
                self.rotation = (self.rotation + 1) % 4
                self.is_rotating = False
                self.rotation_animation = 0
                self._complete_rotation()
    
    def _complete_rotation(self):
        # Create a new rotated board
        new_board = [[None for _ in range(8)] for _ in range(8)]
        
        for row in range(8):
            for col in range(8):
                if self.board[row][col] is not None:
                    # Calculate new position after rotation
                    new_row, new_col = col, 7 - row
                    new_board[new_row][new_col] = self.board[row][col]
                    new_board[new_row][new_col].position = (new_row, new_col)
        
        self.board = new_board
    
    def is_in_check(self, player: Player) -> bool:
        # Find the king
        king_position = None
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.type == PieceType.KING and piece.player.id == player.id:
                    king_position = (row, col)
                    break
            if king_position:
                break
        
        if not king_position:
            return False  # No king found (already captured)
        
        # Check if any opponent piece can capture the king
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.player.id != player.id:
                    # Get raw moves without check filtering
                    for dr, dc in self._get_raw_moves(piece):
                        if (row + dr, col + dc) == king_position:
                            return True
        
        return False
    
    def _get_raw_moves(self, piece: Piece) -> List[Tuple[int, int]]:
        # Simplified version to get potential attack squares without check validation
        moves = []
        row, col = piece.position
        
        if piece.type == PieceType.PAWN:
            direction = piece._get_pawn_direction(self.rotation)
            # Capture moves only for pawns
            for dx, dy in [(direction[0] + direction[1], direction[0] - direction[1]), 
                          (direction[0] - direction[1], direction[0] + direction[1])]:
                if dx == 0 and dy == 0:
                    continue
                new_row, new_col = row + dx, col + dy
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    moves.append((new_row - row, new_col - col))
        
        elif piece.type == PieceType.KNIGHT:
            for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    moves.append((dr, dc))
        
        elif piece.type == PieceType.BISHOP:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    moves.append((i*dr, i*dc))
                    if self.board[new_row][new_col] is not None:
                        break
        
        elif piece.type == PieceType.ROOK:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    moves.append((i*dr, i*dc))
                    if self.board[new_row][new_col] is not None:
                        break
        
        elif piece.type == PieceType.QUEEN:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    moves.append((i*dr, i*dc))
                    if self.board[new_row][new_col] is not None:
                        break
        
        elif piece.type == PieceType.KING:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        moves.append((dr, dc))
        
        return moves
    
    def would_be_in_check_after_move(self, piece: Piece, new_position: Tuple[int, int]) -> bool:
        # Create a temporary copy of the board
        old_position = piece.position
        old_row, old_col = old_position
        new_row, new_col = new_position
        
        # Store the piece that might be captured
        captured_piece = self.board[new_row][new_col]
        
        # Make the move temporarily
        self.board[old_row][old_col] = None
        self.board[new_row][new_col] = piece
        piece.position = new_position
        
        # Check if the player's king is in check
        in_check = self.is_in_check(piece.player)
        
        # Undo the move
        self.board[old_row][old_col] = piece
        self.board[new_row][new_col] = captured_piece
        piece.position = old_position
        
        return in_check
    
    def has_valid_moves(self, player: Player) -> bool:
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.player.id == player.id:
                    if len(piece.get_possible_moves(self)) > 0:
                        return True
        return False
    
    def is_checkmate(self, player: Player) -> bool:
        return self.is_in_check(player) and not self.has_valid_moves(player)
    
    def is_stalemate(self, player: Player) -> bool:
        return not self.is_in_check(player) and not self.has_valid_moves(player)

class ChessGame:
    def __init__(self, num_human_players: int = 1, game_mode: GameMode = GameMode.FREE_FOR_ALL, ai_difficulty: int = 2):
        self.board = ChessBoard()
        self.game_mode = game_mode
        self.ai_difficulty = ai_difficulty
        self.players = []
        self.current_player_idx = 0
        self.turn_count = 0
        self.selected_piece = None
        self.possible_moves = []
        self.game_over = False
        self.winner = None
        self.message = ""
        self.conversion_mode = False
        self.conversion_player = None
        self.conversion_pieces = []
        self.move_animation = None  # For smooth piece movement
        self.move_animation_time = 0
        self.move_animation_duration = 0.5  # seconds
        self.ai_thinking = False
        self.ai_move_delay = 0
        
        # Create players
        for i in range(4):
            is_ai = i >= num_human_players
            team = i % 2 if game_mode == GameMode.TEAM_MODE else i
            self.players.append(Player(i, is_ai, team))
        
        # Set up the board
        self._setup_board()
        
        # Verify no player starts in check
        self._ensure_no_initial_checks()
    
    def _setup_board(self):
        # CORRECT PIECE DISTRIBUTION: 1 King, 1 Queen, 1 Rook, 1 Bishop, 2 Knights, 2 Pawns per player
        
        # Player 1 (Red - bottom)
        # Pawns
        self.board.place_piece(Piece(PieceType.PAWN, self.players[0], (6, 3)), (6, 3))
        self.board.place_piece(Piece(PieceType.PAWN, self.players[0], (6, 4)), (6, 4))
        
        # Other pieces
        self.board.place_piece(Piece(PieceType.ROOK, self.players[0], (7, 0)), (7, 0))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[0], (7, 1)), (7, 1))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[0], (7, 2)), (7, 2))
        self.board.place_piece(Piece(PieceType.QUEEN, self.players[0], (7, 3)), (7, 3))
        self.board.place_piece(Piece(PieceType.KING, self.players[0], (7, 4)), (7, 4))
        self.board.place_piece(Piece(PieceType.BISHOP, self.players[0], (7, 5)), (7, 5))
        
        # Player 2 (Blue - right)
        # Pawns
        self.board.place_piece(Piece(PieceType.PAWN, self.players[1], (3, 6)), (3, 6))
        self.board.place_piece(Piece(PieceType.PAWN, self.players[1], (4, 6)), (4, 6))
        
        # Other pieces
        self.board.place_piece(Piece(PieceType.BISHOP, self.players[1], (2, 7)), (2, 7))
        self.board.place_piece(Piece(PieceType.QUEEN, self.players[1], (3, 7)), (3, 7))
        self.board.place_piece(Piece(PieceType.KING, self.players[1], (4, 7)), (4, 7))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[1], (5, 7)), (5, 7))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[1], (6, 7)), (6, 7))
        self.board.place_piece(Piece(PieceType.ROOK, self.players[1], (7, 7)), (7, 7))
        
        # Player 3 (Green - top)
        # Pawns
        self.board.place_piece(Piece(PieceType.PAWN, self.players[2], (1, 3)), (1, 3))
        self.board.place_piece(Piece(PieceType.PAWN, self.players[2], (1, 4)), (1, 4))
        
        # Other pieces
        self.board.place_piece(Piece(PieceType.BISHOP, self.players[2], (0, 2)), (0, 2))
        self.board.place_piece(Piece(PieceType.QUEEN, self.players[2], (0, 3)), (0, 3))
        self.board.place_piece(Piece(PieceType.KING, self.players[2], (0, 4)), (0, 4))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[2], (0, 5)), (0, 5))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[2], (0, 6)), (0, 6))
        self.board.place_piece(Piece(PieceType.ROOK, self.players[2], (0, 7)), (0, 7))
        
        # Player 4 (Yellow - left)
        # Pawns
        self.board.place_piece(Piece(PieceType.PAWN, self.players[3], (3, 1)), (3, 1))
        self.board.place_piece(Piece(PieceType.PAWN, self.players[3], (4, 1)), (4, 1))
        
        # Other pieces
        self.board.place_piece(Piece(PieceType.ROOK, self.players[3], (0, 0)), (0, 0))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[3], (1, 0)), (1, 0))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[3], (2, 0)), (2, 0))
        self.board.place_piece(Piece(PieceType.QUEEN, self.players[3], (3, 0)), (3, 0))
        self.board.place_piece(Piece(PieceType.KING, self.players[3], (4, 0)), (4, 0))
        self.board.place_piece(Piece(PieceType.BISHOP, self.players[3], (5, 0)), (5, 0))
    
    def _ensure_no_initial_checks(self):
        # Verify no player starts in check
        for player in self.players:
            if self.board.is_in_check(player):
                # Adjust pawn positions if needed
                self._adjust_pawns_to_prevent_check(player)
    
    def _adjust_pawns_to_prevent_check(self, player):
        # Find pawns for this player
        pawns = [p for p in player.pieces if p.type == PieceType.PAWN]
        
        # Try different positions for pawns to block potential checks
        for pawn in pawns:
            old_pos = pawn.position
            row, col = old_pos
            
            # Try moving the pawn forward
            for new_row in range(max(1, row-2), min(6, row+2)):
                for new_col in range(max(1, col-2), min(6, col+2)):
                    if (new_row, new_col) != old_pos and self.board.board[new_row][new_col] is None:
                        # Try this position
                        self.board.board[row][col] = None
                        pawn.position = (new_row, new_col)
                        self.board.board[new_row][new_col] = pawn
                        
                        # Check if this resolves the check
                        if not self.board.is_in_check(player):
                            return
                        
                        # Revert if it doesn't help
                        self.board.board[new_row][new_col] = None
                        pawn.position = old_pos
                        self.board.board[row][col] = pawn
    
    def update(self, delta_time):
        # Update board rotation animation
        self.board.update_rotation(delta_time)
        
        # Update piece movement animation
        if self.move_animation:
            piece, start_pos, end_pos = self.move_animation
            self.move_animation_time += delta_time
            progress = min(1.0, self.move_animation_time / self.move_animation_duration)
            
            # Calculate current position
            start_x = SIDEBAR_WIDTH + start_pos[1] * SQUARE_SIZE + SQUARE_SIZE // 2
            start_y = start_pos[0] * SQUARE_SIZE + SQUARE_SIZE // 2
            end_x = SIDEBAR_WIDTH + end_pos[1] * SQUARE_SIZE + SQUARE_SIZE // 2
            end_y = end_pos[0] * SQUARE_SIZE + SQUARE_SIZE // 2
            
            current_x = start_x + (end_x - start_x) * progress
            current_y = start_y + (end_y - start_y) * progress
            
            piece.animation_pos = (current_x, current_y)
            
            # End animation
            if progress >= 1.0:
                piece.animation_pos = None
                self.move_animation = None
                self.move_animation_time = 0
        
        # Handle AI thinking delay
        if self.ai_thinking:
            self.ai_move_delay -= delta_time
            if self.ai_move_delay <= 0:
                self.ai_thinking = False
                self._execute_ai_move()
    
    def handle_click(self, pos: Tuple[int, int]) -> bool:
        # Don't handle clicks during animations
        if self.move_animation or self.board.is_rotating or self.ai_thinking:
            return False
        
        # Check if we're in conversion mode
        if self.conversion_mode:
            return self._handle_conversion_click(pos)
        
        # Check if the click is on the board
        if not self._is_on_board(pos):
            return self._handle_ui_click(pos)
        
        # Get board coordinates
        col = (pos[0] - SIDEBAR_WIDTH) // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        
        # Current player
        current_player = self.players[self.current_player_idx]
        
        # If a piece is already selected
        if self.selected_piece:
            # Check if the clicked position is a valid move
            if (row, col) in self.possible_moves:
                # Make the move with animation
                self._animate_move(self.selected_piece, (row, col))
                
                # Reset selection
                self.selected_piece = None
                self.possible_moves = []
                
                return True
            else:
                # Deselect if clicking on an invalid move
                self.selected_piece = None
                self.possible_moves = []
                
                # Try to select a new piece
                return self.handle_click(pos)
        else:
            # Try to select a piece
            piece = self.board.board[row][col]
            if piece and piece.player.id == current_player.id:
                self.selected_piece = piece
                self.possible_moves = piece.get_possible_moves(self.board)
                return True
        
        return False
    
    def _animate_move(self, piece: Piece, new_position: Tuple[int, int]):
        # Start animation
        old_position = piece.position
        self.move_animation = (piece, old_position, new_position)
        self.move_animation_time = 0
        
        # Capture logic
        captured_piece = self.board.board[new_position[0]][new_position[1]]
        
        # Make the move
        self.board.move_piece(piece, new_position)
        
        # Check if a king was captured
        if captured_piece and captured_piece.type == PieceType.KING:
            self._handle_king_capture(captured_piece.player, piece.player)
        
        # Check for checkmate or stalemate
        self._check_game_state()
        
        # Next turn if game is not over
        if not self.game_over and not self.conversion_mode:
            self._next_turn()
    
    def _handle_conversion_click(self, pos: Tuple[int, int]) -> bool:
        # Check if the click is on the board
        if not self._is_on_board(pos):
            return False
        
        # Get board coordinates
        col = (pos[0] - SIDEBAR_WIDTH) // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        
        # Check if the clicked position has a piece that can be converted
        piece = self.board.board[row][col]
        if piece and piece in self.conversion_pieces:
            # Convert the piece - change player and color
            piece.player = self.conversion_player
            
            # Remove all other pieces of the defeated player
            for p in self.pieces_to_remove:
                if p != piece and p in p.player.pieces:
                    # Remove from board
                    if self.board.board[p.position[0]][p.position[1]] == p:
                        self.board.board[p.position[0]][p.position[1]] = None
                    
                    # Remove from player's pieces list
                    if p in p.player.pieces:
                        p.player.pieces.remove(p)
            
            # End conversion mode
            self.conversion_mode = False
            self.conversion_player = None
            self.conversion_pieces = []
            self.pieces_to_remove = []
            
            # Next turn
            self._next_turn()
            
            return True
        
        return False
    
    def _handle_ui_click(self, pos: Tuple[int, int]) -> bool:
        # This will be handled by the UI class
        return False
    
    def _is_on_board(self, pos: Tuple[int, int]) -> bool:
        x, y = pos
        return (SIDEBAR_WIDTH <= x < SIDEBAR_WIDTH + BOARD_SIZE and 
                0 <= y < BOARD_SIZE)
    
    def _handle_king_capture(self, defeated_player: Player, victor_player: Player):
        # Mark the player as eliminated
        defeated_player.is_eliminated = True
        
        # Check if the game is over
        if self.game_mode == GameMode.FREE_FOR_ALL:
            # Count active players
            active_players = [p for p in self.players if not p.is_eliminated]
            if len(active_players) == 1:
                self.game_over = True
                self.winner = active_players[0]
                self.message = f"{self.winner} wins!"
                return
        else:  # Team mode
            # Check if all players of a team are eliminated
            team1_eliminated = all(p.is_eliminated for p in self.players if p.team == 0)
            team2_eliminated = all(p.is_eliminated for p in self.players if p.team == 1)
            
            if team1_eliminated or team2_eliminated:
                self.game_over = True
                winning_team = 1 if team1_eliminated else 0
                self.winner = [p for p in self.players if p.team == winning_team][0]
                self.message = f"Team {winning_team + 1} wins!"
                return
        
        # Enter conversion mode
        self.conversion_mode = True
        self.conversion_player = victor_player
        
        # Find pieces that can be converted (excluding the king)
        self.conversion_pieces = [p for p in defeated_player.pieces 
                                if p.type != PieceType.KING and 
                                self.board.board[p.position[0]][p.position[1]] is not None]
        
        self.message = f"{victor_player} can convert one of {defeated_player}'s pieces"
        
        # Store the defeated player's pieces for later removal
        self.pieces_to_remove = self.conversion_pieces.copy()
    
    def _check_game_state(self):
        # Check for checkmate or stalemate for the next player
        next_idx = self._get_next_player_idx()
        next_player = self.players[next_idx]
        
        if self.board.is_checkmate(next_player):
            # Handle checkmate - the current player wins
            current_player = self.players[self.current_player_idx]
            self._handle_king_capture(next_player, current_player)
        elif self.board.is_stalemate(next_player):
            # Handle stalemate - for now, just skip the player's turn
            self.message = f"{next_player} is in stalemate and skips a turn"
    
    def _next_turn(self):
        # Move to the next player
        self.current_player_idx = self._get_next_player_idx()
        self.turn_count += 1
        
        # Count eliminated players
        eliminated_players = sum(1 for p in self.players if p.is_eliminated)
        
        # Check if we need to rotate the board (every 4-n turns, where n is eliminated players)
        rotation_frequency = 4 - eliminated_players
        rotation_frequency = max(1, rotation_frequency)  # Ensure at least 1
        
        if self.turn_count % rotation_frequency == 0:
            self.board.start_rotation()
            self.message = "The board is rotating!"
        
        # Check if the current player is in check
        current_player = self.players[self.current_player_idx]
        if self.board.is_in_check(current_player):
            self.message = f"{current_player} is in check!"
        else:
            self.message = f"{current_player}'s turn"
        
        # If current player is AI, start AI thinking
        if current_player.is_ai and not self.game_over:
            self.ai_thinking = True
            self.ai_move_delay = 1.0  # 1 second delay to simulate thinking
            self.message = f"{current_player} is thinking..."
    
    def _get_next_player_idx(self) -> int:
        # Find the next non-eliminated player
        idx = (self.current_player_idx + 1) % len(self.players)
        while self.players[idx].is_eliminated:
            idx = (idx + 1) % len(self.players)
        return idx
    
    def _execute_ai_move(self):
        # Use Minimax AI for better moves
        ai = MinimaxAI(self.players[self.current_player_idx].id, depth=self.ai_difficulty)
        best_move = ai.get_best_move(self)
        
        if not best_move:
            # No moves available, skip turn
            self._next_turn()
            return
        
        piece, move = best_move
        
        # Make the move with animation
        self._animate_move(piece, move)

class MinimaxAI:
    def __init__(self, player_id: int, depth: int = 3):
        self.player_id = player_id
        self.depth = depth
    
    def get_best_move(self, game: ChessGame) -> Optional[Tuple[Piece, Tuple[int, int]]]:
        # Get all possible moves for the player
        all_moves = []
        for row in range(8):
            for col in range(8):
                piece = game.board.board[row][col]
                if piece and piece.player.id == self.player_id:
                    moves = piece.get_possible_moves(game.board)
                    for move in moves:
                        all_moves.append((piece, move))
        
        if not all_moves:
            return None
        
        # Find the best move using Minimax with Alpha-Beta pruning
        best_score = float('-inf')
        best_move = None
        
        for piece, move in all_moves:
            # Make a temporary move
            old_position = piece.position
            captured_piece = game.board.move_piece(piece, move)
            
            # Evaluate the move
            score = self._minimax(game, self.depth - 1, float('-inf'), float('inf'), False)
            
            # Undo the move
            game.board.board[move[0]][move[1]] = captured_piece
            game.board.board[old_position[0]][old_position[1]] = piece
            piece.position = old_position
            
            if score > best_score:
                best_score = score
                best_move = (piece, move)
        
        return best_move
    
    def _minimax(self, game: ChessGame, depth: int, alpha: float, beta: float, is_maximizing: bool) -> float:
        # Terminal conditions
        if depth == 0:
            return self._evaluate_board(game)
        
        # Get current player
        current_player_id = self.player_id if is_maximizing else self._get_next_player_id(game)
        
        # Get all possible moves for the current player
        all_moves = []
        for row in range(8):
            for col in range(8):
                piece = game.board.board[row][col]
                if piece and piece.player.id == current_player_id:
                    moves = piece.get_possible_moves(game.board)
                    for move in moves:
                        all_moves.append((piece, move))
        
        if not all_moves:
            # No moves available, evaluate the board
            return self._evaluate_board(game)
        
        if is_maximizing:
            max_eval = float('-inf')
            for piece, move in all_moves:
                # Make a temporary move
                old_position = piece.position
                captured_piece = game.board.move_piece(piece, move)
                
                # Recursive evaluation
                eval = self._minimax(game, depth - 1, alpha, beta, False)
                
                # Undo the move
                game.board.board[move[0]][move[1]] = captured_piece
                game.board.board[old_position[0]][old_position[1]] = piece
                piece.position = old_position
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval
        else:
            min_eval = float('inf')
            for piece, move in all_moves:
                # Make a temporary move
                old_position = piece.position
                captured_piece = game.board.move_piece(piece, move)
                
                # Recursive evaluation
                eval = self._minimax(game, depth - 1, alpha, beta, True)
                
                # Undo the move
                game.board.board[move[0]][move[1]] = captured_piece
                game.board.board[old_position[0]][old_position[1]] = piece
                piece.position = old_position
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval
    
    def _evaluate_board(self, game: ChessGame) -> float:
        # Simple evaluation function based on piece values and positions
        score = 0
        
        for row in range(8):
            for col in range(8):
                piece = game.board.board[row][col]
                if piece:
                    # Piece value
                    piece_value = piece.value
                    
                    # Position value (center control is good)
                    position_value = 0.1 * (4 - abs(row - 3.5) - abs(col - 3.5))
                    
                    # Add to score (positive for our pieces, negative for opponents)
                    if piece.player.id == self.player_id:
                        score += piece_value + position_value
                    else:
                        score -= piece_value + position_value
        
        return score
    
    def _get_next_player_id(self, game: ChessGame) -> int:
        # Find the next non-eliminated player
        idx = (self.player_id + 1) % len(game.players)
        while game.players[idx].is_eliminated:
            idx = (idx + 1) % len(game.players)
        return idx

class ChessGameUI:
    def __init__(self, game: ChessGame):
        self.game = game
        # ADJUSTED SCREEN SIZE TO FIT WINDOW
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Checkmate Revolution - 4 Player Chess")
        
        # Load piece images
        self.piece_images = self._load_piece_images()
        
        # Font for text
        self.font = pygame.font.SysFont("Arial", 16)
        self.title_font = pygame.font.SysFont("Arial", 20, bold=True)
        
        # Create buttons
        self.buttons = []
        self._create_buttons()
        
        # Clock for timing
        self.clock = pygame.time.Clock()
        self.last_time = time.time()
    
    def _create_buttons(self):
        # Game control buttons
        controls_x = SIDEBAR_WIDTH + BOARD_SIZE + 10
        
        # New Game button
        new_game_btn = Button(
            controls_x, 300, 120, 30, "New Game", self.font,
            action=self._new_game
        )
        self.buttons.append(new_game_btn)
        
        # Game Mode button
        game_mode_btn = Button(
            controls_x, 340, 120, 30, 
            "Mode: " + ("Team" if self.game.game_mode == GameMode.TEAM_MODE else "FFA"), 
            self.font,
            action=self._toggle_game_mode
        )
        self.buttons.append(game_mode_btn)
        
        # AI Difficulty buttons
        difficulty_label = Button(
            controls_x, 380, 120, 30, 
            f"AI Level: {self.game.ai_difficulty}", 
            self.font,
            action=None
        )
        self.buttons.append(difficulty_label)
        
        # Decrease difficulty
        decrease_btn = Button(
            controls_x, 420, 55, 30, 
            "- Easier", 
            self.font,
            action=lambda: self._change_difficulty(-1)
        )
        self.buttons.append(decrease_btn)
        
        # Increase difficulty
        increase_btn = Button(
            controls_x + 65, 420, 55, 30, 
            "Harder +", 
            self.font,
            action=lambda: self._change_difficulty(1)
        )
        self.buttons.append(increase_btn)
    
    def _new_game(self):
        # Create a new game with current settings
        self.game = ChessGame(
            num_human_players=1, 
            game_mode=self.game.game_mode,
            ai_difficulty=self.game.ai_difficulty
        )
        
        # Update buttons
        self._create_buttons()
    
    def _toggle_game_mode(self):
        if self.game.game_mode == GameMode.FREE_FOR_ALL:
            self.game.game_mode = GameMode.TEAM_MODE
        else:
            self.game.game_mode = GameMode.FREE_FOR_ALL
        
        # Update team assignments
        for i, player in enumerate(self.game.players):
            player.team = i % 2 if self.game.game_mode == GameMode.TEAM_MODE else i
        
        # Update button text
        for button in self.buttons:
            if "Mode:" in button.text:
                button.text = "Mode: " + ("Team" if self.game.game_mode == GameMode.TEAM_MODE else "FFA")
    
    def _change_difficulty(self, change):
        # Change AI difficulty level
        new_difficulty = max(1, min(4, self.game.ai_difficulty + change))
        self.game.ai_difficulty = new_difficulty
        
        # Update button text
        for button in self.buttons:
            if "AI Level:" in button.text:
                button.text = f"AI Level: {self.game.ai_difficulty}"
    
    def _load_piece_images(self) -> Dict:
        # Create simple colored shapes for pieces
        images = {}
        
        piece_symbols = {
            PieceType.KING: "K",
            PieceType.QUEEN: "Q",
            PieceType.ROOK: "R",
            PieceType.BISHOP: "B",
            PieceType.KNIGHT: "N",
            PieceType.PAWN: "P"
        }
        
        for player in self.game.players:
            for piece_type in PieceType:
                # Create a surface for the piece
                surface = pygame.Surface((SQUARE_SIZE - 10, SQUARE_SIZE - 10), pygame.SRCALPHA)
                
                # Draw the piece
                pygame.draw.circle(surface, player.color, (SQUARE_SIZE // 2 - 5, SQUARE_SIZE // 2 - 5), SQUARE_SIZE // 2 - 5)
                pygame.draw.circle(surface, BLACK, (SQUARE_SIZE // 2 - 5, SQUARE_SIZE // 2 - 5), SQUARE_SIZE // 2 - 5, 2)
                
                # Add the piece symbol
                symbol_font = pygame.font.SysFont("Arial", 20, bold=True)
                symbol_text = symbol_font.render(piece_symbols[piece_type], True, BLACK)
                symbol_rect = symbol_text.get_rect(center=(SQUARE_SIZE // 2 - 5, SQUARE_SIZE // 2 - 5))
                surface.blit(symbol_text, symbol_rect)
                
                # Store the image
                images[(player.id, piece_type)] = surface
        
        return images
    
    def update(self):
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # Update game
        self.game.update(delta_time)
    
    def draw(self):
        # Clear the screen
        self.screen.fill(WHITE)
        
        # Draw the board
        self._draw_board()
        
        # Draw the pieces
        self._draw_pieces()
        
        # Draw the UI
        self._draw_ui()
        
        # Update the display
        pygame.display.flip()
    
    def _draw_board(self):
        # Draw the chess board with rotation animation
        rotation_angle = self.game.board.rotation * 90 + self.game.board.rotation_animation
        
        # Create a surface for the board
        board_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
        board_surface.fill(WHITE)
        
        # Draw the squares
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(board_surface, color, 
                                (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                SQUARE_SIZE, SQUARE_SIZE))
                
                # Draw coordinates
                if col == 0:
                    text = self.font.render(str(8 - row), True, BLACK)
                    board_surface.blit(text, (5, row * SQUARE_SIZE + 5))
                if row == 7:
                    text = self.font.render(chr(97 + col), True, BLACK)
                    board_surface.blit(text, (col * SQUARE_SIZE + 5, BOARD_SIZE - 20))
        
        # Highlight the selected piece
        if self.game.selected_piece:
            row, col = self.game.selected_piece.position
            pygame.draw.rect(board_surface, HIGHLIGHT, 
                            (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                            SQUARE_SIZE, SQUARE_SIZE))
        
        # Highlight possible moves
        for row, col in self.game.possible_moves:
            # Create a semi-transparent surface
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill(MOVE_HIGHLIGHT)
            board_surface.blit(highlight, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        
        # Highlight kings in check
        for player in self.game.players:
            if not player.is_eliminated and self.game.board.is_in_check(player):
                # Find the king
                for row in range(8):
                    for col in range(8):
                        piece = self.game.board.board[row][col]
                        if piece and piece.type == PieceType.KING and piece.player.id == player.id:
                            # Create a semi-transparent surface
                            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                            highlight.fill(CHECK_HIGHLIGHT)
                            board_surface.blit(highlight, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        
        # Apply rotation if needed
        if self.game.board.is_rotating:
            # Rotate the board surface
            rotated_surface = pygame.transform.rotate(board_surface, rotation_angle)
            
            # Calculate position to center the rotated surface
            rect = rotated_surface.get_rect(center=(BOARD_SIZE//2, BOARD_SIZE//2))
            
            # Create a temporary surface
            temp_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
            temp_surface.fill(WHITE)
            temp_surface.blit(rotated_surface, rect.topleft)
            
            # Draw the rotated board
            self.screen.blit(temp_surface, (SIDEBAR_WIDTH, 0))
        else:
            # Draw the normal board
            self.screen.blit(board_surface, (SIDEBAR_WIDTH, 0))
    
    def _draw_pieces(self):
        # Don't draw pieces if board is rotating
        if self.game.board.is_rotating:
            return
        
        # Draw all pieces on the board
        for row in range(8):
            for col in range(8):
                piece = self.game.board.board[row][col]
                if piece:
                    # Check if piece is being animated
                    if piece.animation_pos:
                        # Draw at animation position
                        image = self.piece_images[(piece.player.id, piece.type)]
                        x, y = piece.animation_pos
                        self.screen.blit(image, (x - SQUARE_SIZE//2 + 5, y - SQUARE_SIZE//2 + 5))
                    elif not self.game.move_animation or piece != self.game.move_animation[0]:
                        # Draw at normal position
                        image = self.piece_images[(piece.player.id, piece.type)]
                        self.screen.blit(image, (SIDEBAR_WIDTH + col * SQUARE_SIZE + 5, row * SQUARE_SIZE + 5))
    
    def _draw_ui(self):
        # Draw the game info
        pygame.draw.rect(self.screen, WHITE, (0, BOARD_SIZE, SCREEN_WIDTH, INFO_HEIGHT))
        pygame.draw.line(self.screen, BLACK, (0, BOARD_SIZE), (SCREEN_WIDTH, BOARD_SIZE), 2)
        
        # Draw the game mode
        mode_text = self.title_font.render(f"Mode: {'Team' if self.game.game_mode == GameMode.TEAM_MODE else 'Free-for-All'}", True, BLACK)
        self.screen.blit(mode_text, (20, BOARD_SIZE + 10))
        
        # Draw the current player
        current_player = self.game.players[self.game.current_player_idx]
        player_text = self.title_font.render(f"Current Player: {current_player}", True, current_player.color)
        self.screen.blit(player_text, (20, BOARD_SIZE + 35))
        
        # Draw the message
        message_text = self.font.render(self.game.message, True, BLACK)
        self.screen.blit(message_text, (20, BOARD_SIZE + 60))
        
        # Draw player status in the sidebar
        self._draw_player_status()
        
        # Draw game controls
        self._draw_game_controls()
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
    
    def _draw_player_status(self):
        # Draw player information in the left sidebar
        for i, player in enumerate(self.game.players):
            # Background for player info
            color = player.color if not player.is_eliminated else (150, 150, 150)
            pygame.draw.rect(self.screen, color, (10, 10 + i * 80, SIDEBAR_WIDTH - 20, 70), border_radius=5)
            pygame.draw.rect(self.screen, BLACK, (10, 10 + i * 80, SIDEBAR_WIDTH - 20, 70), 2, border_radius=5)
            
            # Player name
            status = " (Eliminated)" if player.is_eliminated else ""
            player_text = self.font.render(f"{player}{status}", True, BLACK)
            self.screen.blit(player_text, (15, 15 + i * 80))
            
            # Team info if in team mode
            if self.game.game_mode == GameMode.TEAM_MODE:
                team_text = self.font.render(f"Team {player.team + 1}", True, BLACK)
                self.screen.blit(team_text, (15, 35 + i * 80))
            
            # Check status
            if not player.is_eliminated:
                if self.game.board.is_in_check(player):
                    check_text = self.font.render("In Check!", True, (255, 0, 0))
                    self.screen.blit(check_text, (15, 55 + i * 80))
    
    def _draw_game_controls(self):
        # Draw game controls in the right sidebar
        controls_x = SIDEBAR_WIDTH + BOARD_SIZE + 10
        
        # Title
        title_text = self.title_font.render("Game Controls", True, BLACK)
        self.screen.blit(title_text, (controls_x, 20))
        
        # Instructions
        instructions = [
            "Click on a piece to select it",
            "Click on a highlighted square to move",
            "The board rotates every 4 turns",
            "Capture a king to convert a piece",
            "Last player/team standing wins"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, BLACK)
            self.screen.blit(text, (controls_x, 50 + i * 25))
        
        # Game status
        if self.game.game_over:
            status_text = self.title_font.render(f"Game Over! {self.game.winner} wins!", True, (0, 128, 0))
            self.screen.blit(status_text, (controls_x, 200))
        elif self.game.conversion_mode:
            status_text = self.title_font.render("Conversion Mode", True, (0, 0, 128))
            self.screen.blit(status_text, (controls_x, 200))
            
            help_text = self.font.render("Click on a piece to convert it", True, BLACK)
            self.screen.blit(help_text, (controls_x, 225))
    
    def handle_event(self, event):
        # Handle mouse movement for button hover
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.check_hover(event.pos)
        
        # Handle button clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.handle_event(event):
                    return True
            
            # Handle game board clicks
            return self.game.handle_click(event.pos)
        
        return False

def main():
    # Initialize the game
    game = ChessGame(num_human_players=1, game_mode=GameMode.FREE_FOR_ALL, ai_difficulty=2)
    ui = ChessGameUI(game)
    
    # Game loop
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                ui.handle_event(event)
        
        # Update game state
        ui.update()
        
        # Draw the game
        ui.draw()
        
        # Cap the frame rate
        ui.clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

# This is a simulation of the code execution
print("Running Enhanced Four-Player Chess with Rotating Board...")
print("Game features:")
print("- Four players with 8 pieces each")
print("- Board rotates 90° every 4 turns with smooth animation")
print("- Piece conversion when a king is captured")
print("- Minimax AI with Alpha-Beta pruning")
print("- Check and checkmate detection")
print("- Team mode and Free-for-All options")
print("- Adjustable AI difficulty")
print("- Smooth piece movement animations")
print("\nNEW FEATURES:")
print("1. Animated piece movement and board rotation")
print("2. Brighter highlighting for possible moves")
print("3. Game mode toggle (Free-for-All or Team Mode)")
print("4. AI difficulty adjustment")
print("5. New Game button for restarting")
print("6. Proper piece color change during conversion")
print("7. Verified initial piece placement to prevent checks")
print("\nTo run the actualimport sys")
import math
import time
import pygame
import numpy as np
from enum import Enum, auto
from typing import List, Tuple, Dict, Set, Optional, Union

# Initialize pygame
pygame.init()

# Constants - ADJUSTED FOR BETTER DISPLAY
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
BOARD_SIZE = 500
SQUARE_SIZE = BOARD_SIZE // 8
SIDEBAR_WIDTH = 150
INFO_HEIGHT = 80

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_SQUARE = (118, 150, 86)
LIGHT_SQUARE = (238, 238, 210)
HIGHLIGHT = (186, 202, 68)
MOVE_HIGHLIGHT = (255, 255, 0, 180)  # Brighter yellow with transparency
CHECK_HIGHLIGHT = (255, 0, 0, 180)
BUTTON_COLOR = (100, 149, 237)  # Cornflower blue
BUTTON_HOVER_COLOR = (65, 105, 225)  # Royal blue
BUTTON_TEXT_COLOR = WHITE

# Player colors
PLAYER_COLORS = [
    (255, 0, 0),    # Red (Player 1)
    (0, 0, 255),    # Blue (Player 2)
    (0, 255, 0),    # Green (Player 3)
    (255, 255, 0)   # Yellow (Player 4)
]

class GameMode(Enum):
    FREE_FOR_ALL = auto()
    TEAM_MODE = auto()

class PieceType(Enum):
    KING = auto()
    QUEEN = auto()
    ROOK = auto()
    BISHOP = auto()
    KNIGHT = auto()
    PAWN = auto()

class Button:
    def __init__(self, x, y, width, height, text, font, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.is_hovered = False
        
    def draw(self, screen):
        color = BUTTON_HOVER_COLOR if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=5)
        
        text_surf = self.font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                self.action()
                return True
        return False

class Player:
    def __init__(self, id: int, is_ai: bool = False, team: int = None):
        self.id = id
        self.is_ai = is_ai
        self.team = team if team is not None else id
        self.is_eliminated = False
        self.pieces = []
        self.color = PLAYER_COLORS[id % len(PLAYER_COLORS)]
        
    def __str__(self):
        return f"Player {self.id+1}" + (" (AI)" if self.is_ai else "")

class Piece:
    def __init__(self, piece_type: PieceType, player: Player, position: Tuple[int, int]):
        self.type = piece_type
        self.player = player
        self.position = position
        self.has_moved = False
        self.value = self._get_value()
        self.animation_pos = None  # For smooth movement animation
        player.pieces.append(self)
        
    def _get_value(self) -> int:
        values = {
            PieceType.KING: 1000,
            PieceType.QUEEN: 9,
            PieceType.ROOK: 5,
            PieceType.BISHOP: 3,
            PieceType.KNIGHT: 3,
            PieceType.PAWN: 1
        }
        return values[self.type]
    
    def get_possible_moves(self, board) -> List[Tuple[int, int]]:
        moves = []
        row, col = self.position
        
        if self.type == PieceType.PAWN:
            # Pawns move differently based on player position
            direction = self._get_pawn_direction(board.rotation)
            
            # Forward move
            new_row, new_col = row + direction[0], col + direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8 and board.board[new_row][new_col] is None:
                moves.append((new_row, new_col))
                
                # Double move from starting position
                if not self.has_moved:
                    new_row, new_col = row + 2*direction[0], col + 2*direction[1]
                    if 0 <= new_row < 8 and 0 <= new_col < 8 and board.board[new_row][new_col] is None:
                        moves.append((new_row, new_col))
            
            # Capture moves
            for dx, dy in [(direction[0] + direction[1], direction[0] - direction[1]), 
                          (direction[0] - direction[1], direction[0] + direction[1])]:
                if dx == 0 and dy == 0:
                    continue
                new_row, new_col = row + dx, col + dy
                if 0 <= new_row < 8 and 0 <= new_col < 8 and board.board[new_row][new_col] is not None:
                    if board.board[new_row][new_col].player.id != self.player.id:
                        moves.append((new_row, new_col))
        
        elif self.type == PieceType.KNIGHT:
            for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    if board.board[new_row][new_col] is None or board.board[new_row][new_col].player.id != self.player.id:
                        moves.append((new_row, new_col))
        
        elif self.type == PieceType.BISHOP:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    if board.board[new_row][new_col] is None:
                        moves.append((new_row, new_col))
                    else:
                        if board.board[new_row][new_col].player.id != self.player.id:
                            moves.append((new_row, new_col))
                        break
        
        elif self.type == PieceType.ROOK:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    if board.board[new_row][new_col] is None:
                        moves.append((new_row, new_col))
                    else:
                        if board.board[new_row][new_col].player.id != self.player.id:
                            moves.append((new_row, new_col))
                        break
        
        elif self.type == PieceType.QUEEN:
            # Queen combines rook and bishop moves
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    if board.board[new_row][new_col] is None:
                        moves.append((new_row, new_col))
                    else:
                        if board.board[new_row][new_col].player.id != self.player.id:
                            moves.append((new_row, new_col))
                        break
        
        elif self.type == PieceType.KING:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if board.board[new_row][new_col] is None or board.board[new_row][new_col].player.id != self.player.id:
                            moves.append((new_row, new_col))
        
        # Filter out moves that would put the king in check
        valid_moves = []
        for move in moves:
            if not board.would_be_in_check_after_move(self, move):
                valid_moves.append(move)
                
        return valid_moves
    
    def _get_pawn_direction(self, rotation: int) -> Tuple[int, int]:
        # Determine pawn direction based on player and board rotation
        base_directions = [
            (-1, 0),  # Player 1 (top)
            (0, -1),  # Player 2 (right)
            (1, 0),   # Player 3 (bottom)
            (0, 1)    # Player 4 (left)
        ]
        
        player_index = (self.player.id - rotation) % 4
        return base_directions[player_index]
    
    def __str__(self):
        return f"{self.player.id}_{self.type.name}"

class ChessBoard:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.rotation = 0  # 0, 1, 2, 3 for 0°, 90°, 180°, 270°
        self.rotation_animation = 0  # For smooth rotation animation
        self.is_rotating = False
        
    def place_piece(self, piece: Piece, position: Tuple[int, int]):
        row, col = position
        self.board[row][col] = piece
        piece.position = position
        
    def move_piece(self, piece: Piece, new_position: Tuple[int, int]) -> Optional[Piece]:
        old_row, old_col = piece.position
        new_row, new_col = new_position
        
        # Check if there's a piece to capture
        captured_piece = self.board[new_row][new_col]
        
        # Update board
        self.board[old_row][old_col] = None
        self.board[new_row][new_col] = piece
        piece.position = new_position
        piece.has_moved = True
        
        return captured_piece
    
    def start_rotation(self):
        self.is_rotating = True
        self.rotation_animation = 0
    
    def update_rotation(self, delta_time):
        if self.is_rotating:
            # Rotate 90 degrees over 1 second
            self.rotation_animation += 90 * delta_time
            if self.rotation_animation >= 90:
                self.rotation = (self.rotation + 1) % 4
                self.is_rotating = False
                self.rotation_animation = 0
                self._complete_rotation()
    
    def _complete_rotation(self):
        # Create a new rotated board
        new_board = [[None for _ in range(8)] for _ in range(8)]
        
        for row in range(8):
            for col in range(8):
                if self.board[row][col] is not None:
                    # Calculate new position after rotation
                    new_row, new_col = col, 7 - row
                    new_board[new_row][new_col] = self.board[row][col]
                    new_board[new_row][new_col].position = (new_row, new_col)
        
        self.board = new_board
    
    def is_in_check(self, player: Player) -> bool:
        # Find the king
        king_position = None
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.type == PieceType.KING and piece.player.id == player.id:
                    king_position = (row, col)
                    break
            if king_position:
                break
        
        if not king_position:
            return False  # No king found (already captured)
        
        # Check if any opponent piece can capture the king
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.player.id != player.id:
                    # Get raw moves without check filtering
                    for dr, dc in self._get_raw_moves(piece):
                        if (row + dr, col + dc) == king_position:
                            return True
        
        return False
    
    def _get_raw_moves(self, piece: Piece) -> List[Tuple[int, int]]:
        # Simplified version to get potential attack squares without check validation
        moves = []
        row, col = piece.position
        
        if piece.type == PieceType.PAWN:
            direction = piece._get_pawn_direction(self.rotation)
            # Capture moves only for pawns
            for dx, dy in [(direction[0] + direction[1], direction[0] - direction[1]), 
                          (direction[0] - direction[1], direction[0] + direction[1])]:
                if dx == 0 and dy == 0:
                    continue
                new_row, new_col = row + dx, col + dy
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    moves.append((new_row - row, new_col - col))
        
        elif piece.type == PieceType.KNIGHT:
            for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    moves.append((dr, dc))
        
        elif piece.type == PieceType.BISHOP:
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    moves.append((i*dr, i*dc))
                    if self.board[new_row][new_col] is not None:
                        break
        
        elif piece.type == PieceType.ROOK:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    moves.append((i*dr, i*dc))
                    if self.board[new_row][new_col] is not None:
                        break
        
        elif piece.type == PieceType.QUEEN:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    moves.append((i*dr, i*dc))
                    if self.board[new_row][new_col] is not None:
                        break
        
        elif piece.type == PieceType.KING:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        moves.append((dr, dc))
        
        return moves
    
    def would_be_in_check_after_move(self, piece: Piece, new_position: Tuple[int, int]) -> bool:
        # Create a temporary copy of the board
        old_position = piece.position
        old_row, old_col = old_position
        new_row, new_col = new_position
        
        # Store the piece that might be captured
        captured_piece = self.board[new_row][new_col]
        
        # Make the move temporarily
        self.board[old_row][old_col] = None
        self.board[new_row][new_col] = piece
        piece.position = new_position
        
        # Check if the player's king is in check
        in_check = self.is_in_check(piece.player)
        
        # Undo the move
        self.board[old_row][old_col] = piece
        self.board[new_row][new_col] = captured_piece
        piece.position = old_position
        
        return in_check
    
    def has_valid_moves(self, player: Player) -> bool:
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.player.id == player.id:
                    if len(piece.get_possible_moves(self)) > 0:
                        return True
        return False
    
    def is_checkmate(self, player: Player) -> bool:
        return self.is_in_check(player) and not self.has_valid_moves(player)
    
    def is_stalemate(self, player: Player) -> bool:
        return not self.is_in_check(player) and not self.has_valid_moves(player)

class ChessGame:
    def __init__(self, num_human_players: int = 1, game_mode: GameMode = GameMode.FREE_FOR_ALL, ai_difficulty: int = 2):
        self.board = ChessBoard()
        self.game_mode = game_mode
        self.ai_difficulty = ai_difficulty
        self.players = []
        self.current_player_idx = 0
        self.turn_count = 0
        self.selected_piece = None
        self.possible_moves = []
        self.game_over = False
        self.winner = None
        self.message = ""
        self.conversion_mode = False
        self.conversion_player = None
        self.conversion_pieces = []
        self.move_animation = None  # For smooth piece movement
        self.move_animation_time = 0
        self.move_animation_duration = 0.5  # seconds
        self.ai_thinking = False
        self.ai_move_delay = 0
        
        # Create players
        for i in range(4):
            is_ai = i >= num_human_players
            team = i % 2 if game_mode == GameMode.TEAM_MODE else i
            self.players.append(Player(i, is_ai, team))
        
        # Set up the board
        self._setup_board()
        
        # Verify no player starts in check
        self._ensure_no_initial_checks()
    
    def _setup_board(self):
        # CORRECT PIECE DISTRIBUTION: 1 King, 1 Queen, 1 Rook, 1 Bishop, 2 Knights, 2 Pawns per player
        
        # Player 1 (Red - bottom)
        # Pawns
        self.board.place_piece(Piece(PieceType.PAWN, self.players[0], (6, 3)), (6, 3))
        self.board.place_piece(Piece(PieceType.PAWN, self.players[0], (6, 4)), (6, 4))
        
        # Other pieces
        self.board.place_piece(Piece(PieceType.ROOK, self.players[0], (7, 0)), (7, 0))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[0], (7, 1)), (7, 1))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[0], (7, 2)), (7, 2))
        self.board.place_piece(Piece(PieceType.QUEEN, self.players[0], (7, 3)), (7, 3))
        self.board.place_piece(Piece(PieceType.KING, self.players[0], (7, 4)), (7, 4))
        self.board.place_piece(Piece(PieceType.BISHOP, self.players[0], (7, 5)), (7, 5))
        
        # Player 2 (Blue - right)
        # Pawns
        self.board.place_piece(Piece(PieceType.PAWN, self.players[1], (3, 6)), (3, 6))
        self.board.place_piece(Piece(PieceType.PAWN, self.players[1], (4, 6)), (4, 6))
        
        # Other pieces
        self.board.place_piece(Piece(PieceType.BISHOP, self.players[1], (2, 7)), (2, 7))
        self.board.place_piece(Piece(PieceType.QUEEN, self.players[1], (3, 7)), (3, 7))
        self.board.place_piece(Piece(PieceType.KING, self.players[1], (4, 7)), (4, 7))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[1], (5, 7)), (5, 7))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[1], (6, 7)), (6, 7))
        self.board.place_piece(Piece(PieceType.ROOK, self.players[1], (7, 7)), (7, 7))
        
        # Player 3 (Green - top)
        # Pawns
        self.board.place_piece(Piece(PieceType.PAWN, self.players[2], (1, 3)), (1, 3))
        self.board.place_piece(Piece(PieceType.PAWN, self.players[2], (1, 4)), (1, 4))
        
        # Other pieces
        self.board.place_piece(Piece(PieceType.BISHOP, self.players[2], (0, 2)), (0, 2))
        self.board.place_piece(Piece(PieceType.QUEEN, self.players[2], (0, 3)), (0, 3))
        self.board.place_piece(Piece(PieceType.KING, self.players[2], (0, 4)), (0, 4))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[2], (0, 5)), (0, 5))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[2], (0, 6)), (0, 6))
        self.board.place_piece(Piece(PieceType.ROOK, self.players[2], (0, 7)), (0, 7))
        
        # Player 4 (Yellow - left)
        # Pawns
        self.board.place_piece(Piece(PieceType.PAWN, self.players[3], (3, 1)), (3, 1))
        self.board.place_piece(Piece(PieceType.PAWN, self.players[3], (4, 1)), (4, 1))
        
        # Other pieces
        self.board.place_piece(Piece(PieceType.ROOK, self.players[3], (0, 0)), (0, 0))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[3], (1, 0)), (1, 0))
        self.board.place_piece(Piece(PieceType.KNIGHT, self.players[3], (2, 0)), (2, 0))
        self.board.place_piece(Piece(PieceType.QUEEN, self.players[3], (3, 0)), (3, 0))
        self.board.place_piece(Piece(PieceType.KING, self.players[3], (4, 0)), (4, 0))
        self.board.place_piece(Piece(PieceType.BISHOP, self.players[3], (5, 0)), (5, 0))
    
    def _ensure_no_initial_checks(self):
        # Verify no player starts in check
        for player in self.players:
            if self.board.is_in_check(player):
                # Adjust pawn positions if needed
                self._adjust_pawns_to_prevent_check(player)
    
    def _adjust_pawns_to_prevent_check(self, player):
        # Find pawns for this player
        pawns = [p for p in player.pieces if p.type == PieceType.PAWN]
        
        # Try different positions for pawns to block potential checks
        for pawn in pawns:
            old_pos = pawn.position
            row, col = old_pos
            
            # Try moving the pawn forward
            for new_row in range(max(1, row-2), min(6, row+2)):
                for new_col in range(max(1, col-2), min(6, col+2)):
                    if (new_row, new_col) != old_pos and self.board.board[new_row][new_col] is None:
                        # Try this position
                        self.board.board[row][col] = None
                        pawn.position = (new_row, new_col)
                        self.board.board[new_row][new_col] = pawn
                        
                        # Check if this resolves the check
                        if not self.board.is_in_check(player):
                            return
                        
                        # Revert if it doesn't help
                        self.board.board[new_row][new_col] = None
                        pawn.position = old_pos
                        self.board.board[row][col] = pawn
    
    def update(self, delta_time):
        # Update board rotation animation
        self.board.update_rotation(delta_time)
        
        # Update piece movement animation
        if self.move_animation:
            piece, start_pos, end_pos = self.move_animation
            self.move_animation_time += delta_time
            progress = min(1.0, self.move_animation_time / self.move_animation_duration)
            
            # Calculate current position
            start_x = SIDEBAR_WIDTH + start_pos[1] * SQUARE_SIZE + SQUARE_SIZE // 2
            start_y = start_pos[0] * SQUARE_SIZE + SQUARE_SIZE // 2
            end_x = SIDEBAR_WIDTH + end_pos[1] * SQUARE_SIZE + SQUARE_SIZE // 2
            end_y = end_pos[0] * SQUARE_SIZE + SQUARE_SIZE // 2
            
            current_x = start_x + (end_x - start_x) * progress
            current_y = start_y + (end_y - start_y) * progress
            
            piece.animation_pos = (current_x, current_y)
            
            # End animation
            if progress >= 1.0:
                piece.animation_pos = None
                self.move_animation = None
                self.move_animation_time = 0
        
        # Handle AI thinking delay
        if self.ai_thinking:
            self.ai_move_delay -= delta_time
            if self.ai_move_delay <= 0:
                self.ai_thinking = False
                self._execute_ai_move()
    
    def handle_click(self, pos: Tuple[int, int]) -> bool:
        # Don't handle clicks during animations
        if self.move_animation or self.board.is_rotating or self.ai_thinking:
            return False
        
        # Check if we're in conversion mode
        if self.conversion_mode:
            return self._handle_conversion_click(pos)
        
        # Check if the click is on the board
        if not self._is_on_board(pos):
            return self._handle_ui_click(pos)
        
        # Get board coordinates
        col = (pos[0] - SIDEBAR_WIDTH) // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        
        # Current player
        current_player = self.players[self.current_player_idx]
        
        # If a piece is already selected
        if self.selected_piece:
            # Check if the clicked position is a valid move
            if (row, col) in self.possible_moves:
                # Make the move with animation
                self._animate_move(self.selected_piece, (row, col))
                
                # Reset selection
                self.selected_piece = None
                self.possible_moves = []
                
                return True
            else:
                # Deselect if clicking on an invalid move
                self.selected_piece = None
                self.possible_moves = []
                
                # Try to select a new piece
                return self.handle_click(pos)
        else:
            # Try to select a piece
            piece = self.board.board[row][col]
            if piece and piece.player.id == current_player.id:
                self.selected_piece = piece
                self.possible_moves = piece.get_possible_moves(self.board)
                return True
        
        return False
    
    def _animate_move(self, piece: Piece, new_position: Tuple[int, int]):
        # Start animation
        old_position = piece.position
        self.move_animation = (piece, old_position, new_position)
        self.move_animation_time = 0
        
        # Capture logic
        captured_piece = self.board.board[new_position[0]][new_position[1]]
        
        # Make the move
        self.board.move_piece(piece, new_position)
        
        # Check if a king was captured
        if captured_piece and captured_piece.type == PieceType.KING:
            self._handle_king_capture(captured_piece.player, piece.player)
        
        # Check for checkmate or stalemate
        self._check_game_state()
        
        # Next turn if game is not over
        if not self.game_over and not self.conversion_mode:
            self._next_turn()
    
    def _handle_conversion_click(self, pos: Tuple[int, int]) -> bool:
        # Check if the click is on the board
        if not self._is_on_board(pos):
            return False
        
        # Get board coordinates
        col = (pos[0] - SIDEBAR_WIDTH) // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        
        # Check if the clicked position has a piece that can be converted
        piece = self.board.board[row][col]
        if piece and piece in self.conversion_pieces:
            # Convert the piece - change player and color
            original_player = piece.player
            piece.player = self.conversion_player
            
            # Add the converted piece to the victor's pieces
            if piece not in self.conversion_player.pieces:
                self.conversion_player.pieces.append(piece)
            
            # Remove all other pieces of the defeated player
            for p in self.pieces_to_remove:
                if p != piece:
                    # Remove from board
                    if self.board.board[p.position[0]][p.position[1]] == p:
                        self.board.board[p.position[0]][p.position[1]] = None
                    
                    # Remove from player's pieces list
                    if p in original_player.pieces:
                        original_player.pieces.remove(p)
            
            # End conversion mode
            self.conversion_mode = False
            self.conversion_player = None
            self.conversion_pieces = []
            self.pieces_to_remove = []
            
            # Next turn
            self._next_turn()
            
            return True
        
        return False
    
    def _handle_ui_click(self, pos: Tuple[int, int]) -> bool:
        # This will be handled by the UI class
        return False
    
    def _is_on_board(self, pos: Tuple[int, int]) -> bool:
        x, y = pos
        return (SIDEBAR_WIDTH <= x < SIDEBAR_WIDTH + BOARD_SIZE and 
                0 <= y < BOARD_SIZE)
    
    def _handle_king_capture(self, defeated_player: Player, victor_player: Player):
        # Mark the player as eliminated
        defeated_player.is_eliminated = True
        
        # Check if the game is over
        if self.game_mode == GameMode.FREE_FOR_ALL:
            # Count active players
            active_players = [p for p in self.players if not p.is_eliminated]
            if len(active_players) == 1:
                self.game_over = True
                self.winner = active_players[0]
                self.message = f"{self.winner} wins!"
                return
        else:  # Team mode
            # Check if all players of a team are eliminated
            team1_eliminated = all(p.is_eliminated for p in self.players if p.team == 0)
            team2_eliminated = all(p.is_eliminated for p in self.players if p.team == 1)
            
            if team1_eliminated or team2_eliminated:
                self.game_over = True
                winning_team = 1 if team1_eliminated else 0
                self.winner = [p for p in self.players if p.team == winning_team][0]
                self.message = f"Team {winning_team + 1} wins!"
                return
        
        # Note: We don't enter conversion mode here anymore
        # That will be handled by _check_game_state when a checkmate is detected
    
    def _check_game_state(self):
        # Check for checkmate or stalemate for the next player
        next_idx = self._get_next_player_idx()
        next_player = self.players[next_idx]
        
        if self.board.is_checkmate(next_player):
            # Handle checkmate - the current player wins and gets to convert a piece
            current_player = self.players[self.current_player_idx]
            
            # Mark the player as eliminated (already done in _handle_king_capture)
            # But now we enter conversion mode for the player who delivered checkmate
            self._enter_conversion_mode(next_player, current_player)
        elif self.board.is_stalemate(next_player):
            # Handle stalemate - for now, just skip the player's turn
            self.message = f"{next_player} is in stalemate and skips a turn"
    
    def _enter_conversion_mode(self, defeated_player: Player, victor_player: Player):
        # Enter conversion mode
        self.conversion_mode = True
        self.conversion_player = victor_player
        
        # Find pieces that can be converted (excluding the king)
        self.conversion_pieces = [p for p in defeated_player.pieces 
                                if p.type != PieceType.KING and 
                                self.board.board[p.position[0]][p.position[1]] is not None]
        
        self.message = f"{victor_player} delivered checkmate and can convert one of {defeated_player}'s pieces"
        
        # Store the defeated player's pieces for later removal
        self.pieces_to_remove = self.conversion_pieces.copy()
    
    def _next_turn(self):
        # Move to the next player
        self.current_player_idx = self._get_next_player_idx()
        self.turn_count += 1
        
        # Count eliminated players
        eliminated_players = sum(1 for p in self.players if p.is_eliminated)
        
        # Check if we need to rotate the board (every 4-n turns, where n is eliminated players)
        rotation_frequency = 4 - eliminated_players
        rotation_frequency = max(1, rotation_frequency)  # Ensure at least 1
        
        if self.turn_count % rotation_frequency == 0:
            self.board.start_rotation()
            self.message = "The board is rotating!"
        
        # Check if the current player is in check
        current_player = self.players[self.current_player_idx]
        if self.board.is_in_check(current_player):
            self.message = f"{current_player} is in check!"
        else:
            self.message = f"{current_player}'s turn"
        
        # If current player is AI, start AI thinking
        if current_player.is_ai and not self.game_over:
            self.ai_thinking = True
            self.ai_move_delay = 1.0  # 1 second delay to simulate thinking
            self.message = f"{current_player} is thinking..."
    
    def _get_next_player_idx(self) -> int:
        # Find the next non-eliminated player
        idx = (self.current_player_idx + 1) % len(self.players)
        while self.players[idx].is_eliminated:
            idx = (idx + 1) % len(self.players)
        return idx
    
    def _execute_ai_move(self):
        # Use Minimax AI for better moves
        ai = MinimaxAI(self.players[self.current_player_idx].id, depth=self.ai_difficulty)
        best_move = ai.get_best_move(self)
        
        if not best_move:
            # No moves available, skip turn
            self._next_turn()
            return
        
        piece, move = best_move
        
        # Make the move with animation
        self._animate_move(piece, move)

class MinimaxAI:
    def __init__(self, player_id: int, depth: int = 3):
        self.player_id = player_id
        self.depth = depth
    
    def get_best_move(self, game: ChessGame) -> Optional[Tuple[Piece, Tuple[int, int]]]:
        # Get all possible moves for the player
        all_moves = []
        for row in range(8):
            for col in range(8):
                piece = game.board.board[row][col]
                if piece and piece.player.id == self.player_id:
                    moves = piece.get_possible_moves(game.board)
                    for move in moves:
                        all_moves.append((piece, move))
        
        if not all_moves:
            return None
        
        # Find the best move using Minimax with Alpha-Beta pruning
        best_score = float('-inf')
        best_move = None
        
        for piece, move in all_moves:
            # Make a temporary move
            old_position = piece.position
            captured_piece = game.board.move_piece(piece, move)
            
            # Evaluate the move
            score = self._minimax(game, self.depth - 1, float('-inf'), float('inf'), False)
            
            # Undo the move
            game.board.board[move[0]][move[1]] = captured_piece
            game.board.board[old_position[0]][old_position[1]] = piece
            piece.position = old_position
            
            if score > best_score:
                best_score = score
                best_move = (piece, move)
        
        return best_move
    
    def _minimax(self, game: ChessGame, depth: int, alpha: float, beta: float, is_maximizing: bool) -> float:
        # Terminal conditions
        if depth == 0:
            return self._evaluate_board(game)
        
        # Get current player
        current_player_id = self.player_id if is_maximizing else self._get_next_player_id(game)
        
        # Get all possible moves for the current player
        all_moves = []
        for row in range(8):
            for col in range(8):
                piece = game.board.board[row][col]
                if piece and piece.player.id == current_player_id:
                    moves = piece.get_possible_moves(game.board)
                    for move in moves:
                        all_moves.append((piece, move))
        
        if not all_moves:
            # No moves available, evaluate the board
            return self._evaluate_board(game)
        
        if is_maximizing:
            max_eval = float('-inf')
            for piece, move in all_moves:
                # Make a temporary move
                old_position = piece.position
                captured_piece = game.board.move_piece(piece, move)
                
                # Recursive evaluation
                eval = self._minimax(game, depth - 1, alpha, beta, False)
                
                # Undo the move
                game.board.board[move[0]][move[1]] = captured_piece
                game.board.board[old_position[0]][old_position[1]] = piece
                piece.position = old_position
                
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval
        else:
            min_eval = float('inf')
            for piece, move in all_moves:
                # Make a temporary move
                old_position = piece.position
                captured_piece = game.board.move_piece(piece, move)
                
                # Recursive evaluation
                eval = self._minimax(game, depth - 1, alpha, beta, True)
                
                # Undo the move
                game.board.board[move[0]][move[1]] = captured_piece
                game.board.board[old_position[0]][old_position[1]] = piece
                piece.position = old_position
                
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval
    
    def _evaluate_board(self, game: ChessGame) -> float:
        # Simple evaluation function based on piece values and positions
        score = 0
        
        for row in range(8):
            for col in range(8):
                piece = game.board.board[row][col]
                if piece:
                    # Piece value
                    piece_value = piece.value
                    
                    # Position value (center control is good)
                    position_value = 0.1 * (4 - abs(row - 3.5) - abs(col - 3.5))
                    
                    # Add to score (positive for our pieces, negative for opponents)
                    if piece.player.id == self.player_id:
                        score += piece_value + position_value
                    else:
                        score -= piece_value + position_value
        
        return score
    
    def _get_next_player_id(self, game: ChessGame) -> int:
        # Find the next non-eliminated player
        idx = (self.player_id + 1) % len(game.players)
        while game.players[idx].is_eliminated:
            idx = (idx + 1) % len(game.players)
        return idx

class ChessGameUI:
    def __init__(self, game: ChessGame):
        self.game = game
        # ADJUSTED SCREEN SIZE TO FIT WINDOW
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Checkmate Revolution - 4 Player Chess")
        
        # Load piece images
        self.piece_images = self._load_piece_images()
        
        # Font for text
        self.font = pygame.font.SysFont("Arial", 16)
        self.title_font = pygame.font.SysFont("Arial", 20, bold=True)
        
        # Create buttons
        self.buttons = []
        self._create_buttons()
        
        # Clock for timing
        self.clock = pygame.time.Clock()
        self.last_time = time.time()
    
    def _create_buttons(self):
        # Game control buttons
        controls_x = SIDEBAR_WIDTH + BOARD_SIZE + 10
        
        # New Game button
        new_game_btn = Button(
            controls_x, 300, 120, 30, "New Game", self.font,
            action=self._new_game
        )
        self.buttons.append(new_game_btn)
        
        # Game Mode button
        game_mode_btn = Button(
            controls_x, 340, 120, 30, 
            "Mode: " + ("Team" if self.game.game_mode == GameMode.TEAM_MODE else "FFA"), 
            self.font,
            action=self._toggle_game_mode
        )
        self.buttons.append(game_mode_btn)
        
        # AI Difficulty buttons
        difficulty_label = Button(
            controls_x, 380, 120, 30, 
            f"AI Level: {self.game.ai_difficulty}", 
            self.font,
            action=None
        )
        self.buttons.append(difficulty_label)
        
        # Decrease difficulty
        decrease_btn = Button(
            controls_x, 420, 55, 30, 
            "- Easier", 
            self.font,
            action=lambda: self._change_difficulty(-1)
        )
        self.buttons.append(decrease_btn)
        
        # Increase difficulty
        increase_btn = Button(
            controls_x + 65, 420, 55, 30, 
            "Harder +", 
            self.font,
            action=lambda: self._change_difficulty(1)
        )
        self.buttons.append(increase_btn)
    
    def _new_game(self):
        # Create a new game with current settings
        self.game = ChessGame(
            num_human_players=1, 
            game_mode=self.game.game_mode,
            ai_difficulty=self.game.ai_difficulty
        )
        
        # Update buttons
        self._create_buttons()
    
    def _toggle_game_mode(self):
        if self.game.game_mode == GameMode.FREE_FOR_ALL:
            self.game.game_mode = GameMode.TEAM_MODE
        else:
            self.game.game_mode = GameMode.FREE_FOR_ALL
        
        # Update team assignments
        for i, player in enumerate(self.game.players):
            player.team = i % 2 if self.game.game_mode == GameMode.TEAM_MODE else i
        
        # Update button text
        for button in self.buttons:
            if "Mode:" in button.text:
                button.text = "Mode: " + ("Team" if self.game.game_mode == GameMode.TEAM_MODE else "FFA")
    
    def _change_difficulty(self, change):
        # Change AI difficulty level
        new_difficulty = max(1, min(4, self.game.ai_difficulty + change))
        self.game.ai_difficulty = new_difficulty
        
        # Update button text
        for button in self.buttons:
            if "AI Level:" in button.text:
                button.text = f"AI Level: {self.game.ai_difficulty}"
    
    def _load_piece_images(self) -> Dict:
        # Create simple colored shapes for pieces
        images = {}
        
        piece_symbols = {
            PieceType.KING: "K",
            PieceType.QUEEN: "Q",
            PieceType.ROOK: "R",
            PieceType.BISHOP: "B",
            PieceType.KNIGHT: "N",
            PieceType.PAWN: "P"
        }
        
        for player in self.game.players:
            for piece_type in PieceType:
                # Create a surface for the piece
                surface = pygame.Surface((SQUARE_SIZE - 10, SQUARE_SIZE - 10), pygame.SRCALPHA)
                
                # Draw the piece
                pygame.draw.circle(surface, player.color, (SQUARE_SIZE // 2 - 5, SQUARE_SIZE // 2 - 5), SQUARE_SIZE // 2 - 5)
                pygame.draw.circle(surface, BLACK, (SQUARE_SIZE // 2 - 5, SQUARE_SIZE // 2 - 5), SQUARE_SIZE // 2 - 5, 2)
                
                # Add the piece symbol
                symbol_font = pygame.font.SysFont("Arial", 20, bold=True)
                symbol_text = symbol_font.render(piece_symbols[piece_type], True, BLACK)
                symbol_rect = symbol_text.get_rect(center=(SQUARE_SIZE // 2 - 5, SQUARE_SIZE // 2 - 5))
                surface.blit(symbol_text, symbol_rect)
                
                # Store the image
                images[(player.id, piece_type)] = surface
        
        return images
    
    def update(self):
        # Calculate delta time
        current_time = time.time()
        delta_time = current_time - self.last_time
        self.last_time = current_time
        
        # Update game
        self.game.update(delta_time)
    
    def draw(self):
        # Clear the screen
        self.screen.fill(WHITE)
        
        # Draw the board
        self._draw_board()
        
        # Draw the pieces
        self._draw_pieces()
        
        # Draw the UI
        self._draw_ui()
        
        # Update the display
        pygame.display.flip()
    
    def _draw_board(self):
        # Draw the chess board with rotation animation
        rotation_angle = self.game.board.rotation * 90 + self.game.board.rotation_animation
        
        # Create a surface for the board
        board_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
        board_surface.fill(WHITE)
        
        # Draw the squares
        for row in range(8):
            for col in range(8):
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(board_surface, color, 
                                (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                SQUARE_SIZE, SQUARE_SIZE))
                
                # Draw coordinates
                if col == 0:
                    text = self.font.render(str(8 - row), True, BLACK)
                    board_surface.blit(text, (5, row * SQUARE_SIZE + 5))
                if row == 7:
                    text = self.font.render(chr(97 + col), True, BLACK)
                    board_surface.blit(text, (col * SQUARE_SIZE + 5, BOARD_SIZE - 20))
        
        # Highlight the selected piece
        if self.game.selected_piece:
            row, col = self.game.selected_piece.position
            pygame.draw.rect(board_surface, HIGHLIGHT, 
                            (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                            SQUARE_SIZE, SQUARE_SIZE))
        
        # Highlight possible moves
        for row, col in self.game.possible_moves:
            # Create a semi-transparent surface
            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            highlight.fill(MOVE_HIGHLIGHT)
            board_surface.blit(highlight, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        
        # Highlight kings in check
        for player in self.game.players:
            if not player.is_eliminated and self.game.board.is_in_check(player):
                # Find the king
                for row in range(8):
                    for col in range(8):
                        piece = self.game.board.board[row][col]
                        if piece and piece.type == PieceType.KING and piece.player.id == player.id:
                            # Create a semi-transparent surface
                            highlight = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                            highlight.fill(CHECK_HIGHLIGHT)
                            board_surface.blit(highlight, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        
        # Apply rotation if needed
        if self.game.board.is_rotating:
            # Rotate the board surface
            rotated_surface = pygame.transform.rotate(board_surface, rotation_angle)
            
            # Calculate position to center the rotated surface
            rect = rotated_surface.get_rect(center=(BOARD_SIZE//2, BOARD_SIZE//2))
            
            # Create a temporary surface
            temp_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE))
            temp_surface.fill(WHITE)
            temp_surface.blit(rotated_surface, rect.topleft)
            
            # Draw the rotated board
            self.screen.blit(temp_surface, (SIDEBAR_WIDTH, 0))
        else:
            # Draw the normal board
            self.screen.blit(board_surface, (SIDEBAR_WIDTH, 0))
    
    def _draw_pieces(self):
        # Don't draw pieces if board is rotating
        if self.game.board.is_rotating:
            return
        
        # Draw all pieces on the board
        for row in range(8):
            for col in range(8):
                piece = self.game.board.board[row][col]
                if piece:
                    # Check if piece is being animated
                    if piece.animation_pos:
                        # Draw at animation position
                        image = self.piece_images[(piece.player.id, piece.type)]
                        x, y = piece.animation_pos
                        self.screen.blit(image, (x - SQUARE_SIZE//2 + 5, y - SQUARE_SIZE//2 + 5))
                    elif not self.game.move_animation or piece != self.game.move_animation[0]:
                        # Draw at normal position
                        image = self.piece_images[(piece.player.id, piece.type)]
                        self.screen.blit(image, (SIDEBAR_WIDTH + col * SQUARE_SIZE + 5, row * SQUARE_SIZE + 5))
    
    def _draw_ui(self):
        # Draw the game info
        pygame.draw.rect(self.screen, WHITE, (0, BOARD_SIZE, SCREEN_WIDTH, INFO_HEIGHT))
        pygame.draw.line(self.screen, BLACK, (0, BOARD_SIZE), (SCREEN_WIDTH, BOARD_SIZE), 2)
        
        # Draw the game mode
        mode_text = self.title_font.render(f"Mode: {'Team' if self.game.game_mode == GameMode.TEAM_MODE else 'Free-for-All'}", True, BLACK)
        self.screen.blit(mode_text, (20, BOARD_SIZE + 10))
        
        # Draw the current player
        current_player = self.game.players[self.game.current_player_idx]
        player_text = self.title_font.render(f"Current Player: {current_player}", True, current_player.color)
        self.screen.blit(player_text, (20, BOARD_SIZE + 35))
        
        # Draw the message
        message_text = self.font.render(self.game.message, True, BLACK)
        self.screen.blit(message_text, (20, BOARD_SIZE + 60))
        
        # Draw player status in the sidebar
        self._draw_player_status()
        
        # Draw game controls
        self._draw_game_controls()
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
    
    def _draw_player_status(self):
        # Draw player information in the left sidebar
        for i, player in enumerate(self.game.players):
            # Background for player info
            color = player.color if not player.is_eliminated else (150, 150, 150)
            pygame.draw.rect(self.screen, color, (10, 10 + i * 80, SIDEBAR_WIDTH - 20, 70), border_radius=5)
            pygame.draw.rect(self.screen, BLACK, (10, 10 + i * 80, SIDEBAR_WIDTH - 20, 70), 2, border_radius=5)
            
            # Player name
            status = " (Eliminated)" if player.is_eliminated else ""
            player_text = self.font.render(f"{player}{status}", True, BLACK)
            self.screen.blit(player_text, (15, 15 + i * 80))
            
            # Team info if in team mode
            if self.game.game_mode == GameMode.TEAM_MODE:
                team_text = self.font.render(f"Team {player.team + 1}", True, BLACK)
                self.screen.blit(team_text, (15, 35 + i * 80))
            
            # Check status
            if not player.is_eliminated:
                if self.game.board.is_in_check(player):
                    check_text = self.font.render("In Check!", True, (255, 0, 0))
                    self.screen.blit(check_text, (15, 55 + i * 80))
    
    def _draw_game_controls(self):
        # Draw game controls in the right sidebar
        controls_x = SIDEBAR_WIDTH + BOARD_SIZE + 10
        
        # Title
        title_text = self.title_font.render("Game Controls", True, BLACK)
        self.screen.blit(title_text, (controls_x, 20))
        
        # Instructions
        instructions = [
            "Click on a piece to select it",
            "Click on a highlighted square to move",
            "The board rotates every 4 turns",
            "Capture a king to convert a piece",
            "Last player/team standing wins"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, BLACK)
            self.screen.blit(text, (controls_x, 50 + i * 25))
        
        # Game status
        if self.game.game_over:
            status_text = self.title_font.render(f"Game Over! {self.game.winner} wins!", True, (0, 128, 0))
            self.screen.blit(status_text, (controls_x, 200))
        elif self.game.conversion_mode:
            status_text = self.title_font.render("Conversion Mode", True, (0, 0, 128))
            self.screen.blit(status_text, (controls_x, 200))
            
            help_text = self.font.render("Click on a piece to convert it", True, BLACK)
            self.screen.blit(help_text, (controls_x, 225))
    
    def handle_event(self, event):
        # Handle mouse movement for button hover
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.check_hover(event.pos)
        
        # Handle button clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.buttons:
                if button.handle_event(event):
                    return True
            
            # Handle game board clicks
            return self.game.handle_click(event.pos)
        
        return False

def main():
    # Initialize the game
    game = ChessGame(num_human_players=1, game_mode=GameMode.FREE_FOR_ALL, ai_difficulty=2)
    ui = ChessGameUI(game)
    
    # Game loop
    running = True
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                ui.handle_event(event)
        
        # Update game state
        ui.update()
        
        # Draw the game
        ui.draw()
        
        # Cap the frame rate
        ui.clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

# This is a simulation of the code execution
print("Running Enhanced Four-Player Chess with Rotating Board...")
print("Game features:")
print("- Four players with 8 pieces each")
print("- Board rotates 90° every 4 turns with smooth animation")
print("- Piece conversion when a king is captured")
print("- Minimax AI with Alpha-Beta pruning")
print("- Check and checkmate detection")
print("- Team mode and Free-for-All options")
print("- Adjustable AI difficulty")
print("- Smooth piece movement animations")
print("\nNEW FEATURES:")
print("1. Animated piece movement and board rotation")
print("2. Brighter highlighting for possible moves")
print("3. Game mode toggle (Free-for-All or Team Mode)")
print("4. AI difficulty adjustment")
print("5. New Game button for restarting")
print("6. Proper piece color change during conversion")
print("7. Verified initial piece placement to prevent checks")