# Checkmate Revolution: 4-Player Chess with a Twist 🔄 ♟️

A dynamic, strategic, and chaotic spin on the classic game of chess, built using Python and Pygame. **Checkmate Revolution** brings up to 4 players together on a single 8x8 battlefield where the board rotates, alliances are formed or shattered, and fallen armies can be partially conscripted into your own!

---

## 🚀 Features

### 👥 1. 4-Player Chaos & Teams
- Plays with **4 unique factions**: Red (Player 1, Bottom), Blue (Player 2, Right), Green (Player 3, Top), and Yellow (Player 4, Left).
- **Two Game Modes**:
  - **Free-for-All (FFA):** Every player for themselves. Last commander standing wins.
  - **Team Mode:** 2v2 tactical warfare where Players 1 & 3 team up against Players 2 & 4.

### 🔄 2. Dynamic Board Rotation
- The battlefield is never static! Every few turns (scaled according to active players), the entire board **rotates 90 degrees clockwise**.
- **Adapting Pawn Direction:** As the board rotates, the orientation changes, and pawn advance vectors automatically adjust relative to the new board perspective.

### 👑 3. King Capture & Conscription (Piece Conversion)
- Unlike traditional chess where checkmate immediately ends the whole game, capturing an opponent's King eliminates *that specific player*.
- **The Conscription Twist:** Upon capturing a King, the victor enters **Conversion Mode** and gets to claim **one** surviving piece from the defeated player's army to join their side! The remaining pieces of that eliminated army are cleared from the board.

### 🤖 4. Minimax AI with Alpha-Beta Pruning
- Out of human friends? Play against built-in AI commanders.
- Powered by a customizable **Minimax engine** optimized with **Alpha-Beta Pruning** for forward-looking move analysis.
- **Adjustable Difficulty:** Shift difficulty fluidly between Level 1 (Casual) to Level 4 (Tactician) using in-game UI buttons.

### 🎨 5. Modern UI & Animations
- Full-featured dashboard panel showing game statuses, active check alerts, and current player turns.
- Smooth piece movement transitions and fluid board-rotation animations.
- Clear move indicators highlighting legal squares, check alerts, and active selections.

---

## 🛠️ Installation & Setup

### Prerequisites
Make sure you have Python 3.x installed on your machine. You will also need `pygame` and `numpy`.

### Step 1: Install Dependencies
Open your terminal or command prompt and run:
```bash
pip install pygame numpy
```

### Step 2: Download and Run the Game
Save the code file as `Check-mate Revolution.py` and run it:
```bash
python "Check-mate Revolution.py"
```

---

## 🎮 How to Play

1. **Selecting a Piece:** Click on any of your colored pieces during your turn. Legal moves will be highlighted in **bright yellow**.
2. **Moving:** Click on any highlighted yellow square to execute your move. If your king is under threat, you will see a **red highlight** and a status alert indicating you are in check.
3. **Conscripting a Piece:** When you capture an opponent's king, the screen will switch to **Conversion Mode**. Select any remaining piece belonging to that player's faction to make it yours, changing it to your team's color.
4. **UI Panel Controls:**
   - **New Game:** Reset the board and launch a fresh match.
   - **Mode Toggle:** Dynamically flip between Free-For-All and Team Modes.
   - **AI Level Adjusters:** Use `- Easier` and `Harder +` buttons to change the complexity of computer moves.

---

## ♟️ Piece Distribution per Player
To fit the 8x8 layout for a high-intensity 4-player format, each faction starts with a streamlined, specialized **8-piece layout**:
- 👑 **1 King**
- ♕ **1 Queen**
- ♖ **1 Rook**
- ♗ **1 Bishop**
- ♘ **2 Knights**
- ♙ **2 Pawns**

---

## 📂 Codebase Architecture
The game follows a robust object-oriented layout:
- `PieceType` & `GameMode`: Enums representing the core states and rules.
- `Player`: Manages individual faction states, elimination status, colors, and alliance teams.
- `Piece`: Implements specific behavioral logic and valid move calculation for Pawns, Knights, Bishops, Rooks, Queens, and Kings.
- `ChessBoard`: Handles underlying 2D array board representation, cell states, rotation logic, check/checkmate validations, and temporary evaluations.
- `ChessGame`: The central controller managing game turns, AI execution, conversion state flow, and player transitions.
- `MinimaxAI`: Brains behind the AI, evaluating positional scores and optimal move branching using alpha-beta cutoffs.
- `ChessGameUI`: Draws interactive widgets, animations, fonts, layouts, and converts board logic into user events.

---

## 📜 License
This project is open-source and free to modify, expand, or customize for your own chess revolutions!
