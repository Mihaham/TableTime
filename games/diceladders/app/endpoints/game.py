from fastapi import APIRouter, HTTPException, Response
from app.models import (
    GameState,
    RollDiceRequest,
    MoveRequest,
    CreateGameRequest,
    JoinGameRequest,
    FinishGameRequest,
    GameActionResponse
)
from app.utils import log_game_creation, log_game_join, log_game_action, log_game_finish
from app.board_generator import generate_board_image
from typing import Dict, Optional
import random
from loguru import logger

router = APIRouter()

# In-memory game storage (key is invite_code which is 6-digit number)
games: Dict[int, GameState] = {}

# Board configuration: ladders and snakes
# Format: {start_position: end_position}
# Positive values = ladders (move up), Negative values = snakes/chutes (move down)
BOARD_LADDERS = {
    3: 22,   # Ladder: +19
    5: 8,    # Ladder: +3
    11: 26,  # Ladder: +15
    20: 29,  # Ladder: +9
    17: 4,   # Snake: -13
    19: 7,   # Snake: -12
    21: 9,   # Snake: -12
    27: 1,   # Snake: -26
    35: 28,  # Snake: -7
    39: 32,  # Snake: -7
    51: 67,  # Ladder: +16
    54: 34,  # Snake: -20
    62: 19,  # Snake: -43
    64: 60,  # Snake: -4
    71: 91,  # Ladder: +20
    87: 24,  # Snake: -63
    93: 73,  # Snake: -20
    95: 75,  # Snake: -20
    99: 80,  # Snake: -19
}

def get_player_number(game: GameState, user_id: int) -> Optional[int]:
    """Get player number (1, 2, or 3) from user_id"""
    if user_id == game.player1_id:
        return 1
    if game.player2_id and user_id == game.player2_id:
        return 2
    if game.player3_id and user_id == game.player3_id:
        return 3
    return None

def get_current_player_id(game: GameState) -> Optional[int]:
    """Get the user_id of the player whose turn it is"""
    if game.current_turn == 1:
        return game.player1_id
    elif game.current_turn == 2:
        return game.player2_id
    elif game.current_turn == 3:
        return game.player3_id
    return None

def apply_ladder(position: int) -> tuple[int, bool, Optional[int]]:
    """Apply ladder/snake if player is on a special position. Returns (new_position, ladder_used, delta)"""
    if position in BOARD_LADDERS:
        new_position = BOARD_LADDERS[position]
        delta = new_position - position
        return new_position, True, delta
    return position, False, None

def get_player_count(game: GameState) -> int:
    """Get number of players in the game"""
    count = 1
    if game.player2_id:
        count += 1
    if game.player3_id:
        count += 1
    return count

def next_turn(game: GameState):
    """Move to the next player's turn"""
    player_count = get_player_count(game)
    if game.current_turn is None:
        game.current_turn = 1
    else:
        game.current_turn = (game.current_turn % player_count) + 1

def check_winner(game: GameState) -> Optional[int]:
    """Check if any player has won (reached the end)"""
    for player_id, position in game.player_positions.items():
        if position >= game.board_size:
            return player_id
    return None

@router.post("/create", response_model=GameState)
async def create_game(request: CreateGameRequest):
    """Create a new dice and ladders game"""
    logger.info(f"Creating dice-ladders game for player {request.player1_id}")
    # Generate 6-digit invite code (same format as all games: 100000-999999)
    invite_code = random.randint(100000, 999999)
    
    # Ensure unique invite code
    while invite_code in games:
        invite_code = random.randint(100000, 999999)
    
    # Initialize player positions
    player_positions = {request.player1_id: 0}
    
    # Create game state
    game = GameState(
        game_id=invite_code,
        player1_id=request.player1_id,
        status="waiting",
        player_positions=player_positions
    )
    
    games[invite_code] = game
    logger.info(f"Dice-ladders game {invite_code} created successfully")
    
    # Log game creation
    log_game_creation(invite_code, request.player1_id, invite_code)
    
    return game

@router.post("/join", response_model=GameState)
async def join_game(request: JoinGameRequest):
    """Join an existing game as player 2 or player 3"""
    logger.info(f"Player {request.player_id} attempting to join dice-ladders game {request.game_id}")
    if request.game_id not in games:
        logger.warning(f"Dice-ladders game {request.game_id} not found")
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate player is not already in the game
    if request.player_id in [game.player1_id, game.player2_id, game.player3_id]:
        logger.warning(f"Player {request.player_id} is already in dice-ladders game {request.game_id}")
        raise HTTPException(status_code=400, detail="Player is already in this game")
    
    # Check if game is full
    if game.player2_id and game.player3_id:
        logger.warning(f"Dice-ladders game {request.game_id} is already full")
        raise HTTPException(status_code=400, detail="Game is already full (max 3 players)")
    
    # Add player 2 or player 3
    if game.player2_id is None:
        game.player2_id = request.player_id
        game.player_positions[request.player_id] = 0
        logger.info(f"Player {request.player_id} joined as player 2 in game {request.game_id}")
    elif game.player3_id is None:
        game.player3_id = request.player_id
        game.player_positions[request.player_id] = 0
        logger.info(f"Player {request.player_id} joined as player 3 in game {request.game_id}")
    
    # Start the game if we have at least 2 players
    player_count = get_player_count(game)
    if player_count >= 2 and game.status == "waiting":
        game.status = "playing"
        game.current_turn = 1  # Start with player 1
        logger.info(f"Dice-ladders game {request.game_id} started with {player_count} players")
    
    # Log game join
    log_game_join(request.game_id, request.player_id)
    
    return game

@router.post("/start", response_model=GameState)
async def start_game(request: JoinGameRequest):
    """Explicitly start a game (if it has at least 2 players)"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate player is in the game
    if request.player_id not in [game.player1_id, game.player2_id, game.player3_id]:
        raise HTTPException(status_code=403, detail="Player not in this game")
    
    # Check if game can be started
    player_count = get_player_count(game)
    if player_count < 2:
        raise HTTPException(status_code=400, detail=f"Cannot start game with only {player_count} player(s). Need at least 2 players.")
    
    if game.status != "waiting":
        raise HTTPException(status_code=400, detail=f"Game cannot be started. Current status: {game.status}")
    
    # Start the game
    game.status = "playing"
    game.current_turn = 1  # Start with player 1
    logger.info(f"Dice-ladders game {request.game_id} started with {player_count} players")
    
    return game

@router.post("/roll_dice", response_model=GameActionResponse)
async def roll_dice(request: RollDiceRequest):
    """Roll dice for the current player"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate player is in the game
    player_num = get_player_number(game, request.user_id)
    if player_num is None:
        raise HTTPException(status_code=403, detail="Player not in this game")
    
    # Validate game status
    if game.status != "playing":
        raise HTTPException(status_code=400, detail=f"Game is not in playing status. Current status: {game.status}")
    
    # Validate it's this player's turn
    if game.current_turn != player_num:
        raise HTTPException(status_code=400, detail=f"It's not your turn. Current turn: Player {game.current_turn}")
    
    # Validate player hasn't already rolled
    if game.last_dice_roll is not None:
        raise HTTPException(status_code=400, detail="You have already rolled. Please move now.")
    
    # Roll dice (1-6)
    dice_roll = random.randint(1, 6)
    game.last_dice_roll = dice_roll
    
    # Log dice roll
    log_game_action(
        request.game_id,
        request.user_id,
        "roll_dice",
        {"dice_roll": dice_roll, "player_number": player_num}
    )
    
    return GameActionResponse(
        success=True,
        message=f"You rolled a {dice_roll}!",
        new_state=game,
        dice_roll=dice_roll
    )

@router.post("/move", response_model=GameActionResponse)
async def move(request: MoveRequest):
    """Move the player after rolling dice"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate player is in the game
    player_num = get_player_number(game, request.user_id)
    if player_num is None:
        raise HTTPException(status_code=403, detail="Player not in this game")
    
    # Validate game status
    if game.status != "playing":
        raise HTTPException(status_code=400, detail=f"Game is not in playing status. Current status: {game.status}")
    
    # Validate it's this player's turn
    if game.current_turn != player_num:
        raise HTTPException(status_code=400, detail=f"It's not your turn. Current turn: Player {game.current_turn}")
    
    # Validate player has rolled dice
    if game.last_dice_roll is None:
        raise HTTPException(status_code=400, detail="You must roll the dice first")
    
    # Get current position
    current_position = game.player_positions.get(request.user_id, 0)
    
    # Calculate new position
    new_position = current_position + game.last_dice_roll
    
    # Don't exceed board size
    if new_position > game.board_size:
        new_position = game.board_size
    
    # Apply ladder/snake if applicable
    ladder_used = False
    ladder_delta = None
    final_position, ladder_used, ladder_delta = apply_ladder(new_position)
    
    # Update player position
    game.player_positions[request.user_id] = final_position
    
    # Build message
    message = f"Moved from {current_position} to {new_position}"
    if ladder_used:
        if ladder_delta and ladder_delta > 0:
            message += f" and climbed a ladder! (+{ladder_delta} to {final_position})"
        else:
            message += f" and slid down a snake! ({ladder_delta} to {final_position})"
    else:
        message += f" (now at {final_position})"
    
    # Log move action
    log_game_action(
        request.game_id,
        request.user_id,
        "move",
        {
            "player_number": player_num,
            "from_position": current_position,
            "to_position": new_position,
            "final_position": final_position,
            "dice_roll": game.last_dice_roll,
            "ladder_used": ladder_used,
            "ladder_delta": ladder_delta
        }
    )
    
    # Check for winner
    winner_id = check_winner(game)
    if winner_id:
        game.status = "finished"
        game.winner_id = winner_id
        message += f"\n🎉 Player {player_num} wins! Reached position {final_position}!"
        
        # Log game finish
        final_state = {
            "player_positions": game.player_positions,
            "winner_id": winner_id,
            "final_position": final_position
        }
        log_game_finish(request.game_id, request.user_id, winner_id, final_state)
    else:
        # Reset dice roll and move to next turn
        game.last_dice_roll = None
        next_turn(game)
    
    return GameActionResponse(
        success=True,
        message=message,
        new_state=game,
        new_position=final_position,
        ladder_used=ladder_used,
        ladder_delta=ladder_delta
    )

@router.get("/{game_id}/state", response_model=GameState)
async def get_game_state(game_id: int):
    """Get current game state"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id]

@router.get("/{game_id}/board")
async def get_board_image(game_id: int):
    """Get board image for the game"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[game_id]
    # Get current player ID from current_turn number
    current_player_id = get_current_player_id(game)
    image_bytes = generate_board_image(game.player_positions, current_player_id)
    return Response(content=image_bytes, media_type="image/png")

@router.get("/{game_id}/status")
async def get_game_status(game_id: int):
    """Get game status"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    game = games[game_id]
    return {
        "game_id": game_id,
        "status": game.status,
        "player1_id": game.player1_id,
        "player2_id": game.player2_id,
        "player3_id": game.player3_id,
        "current_turn": game.current_turn,
        "player_positions": game.player_positions,
        "winner_id": game.winner_id
    }

@router.get("/user/{user_id}/game")
async def get_game_by_user(user_id: int):
    """Get game information by user_id"""
    for game_id, game in games.items():
        if (game.player1_id == user_id or 
            game.player2_id == user_id or 
            game.player3_id == user_id):
            return {
                "game_id": game_id,
                "status": game.status,
                "player1_id": game.player1_id,
                "player2_id": game.player2_id,
                "player3_id": game.player3_id,
                "current_turn": game.current_turn,
                "player_positions": game.player_positions,
                "winner_id": game.winner_id
            }
    raise HTTPException(status_code=404, detail="User is not in any game")

@router.post("/finish", response_model=GameState)
async def finish_game(request: FinishGameRequest):
    """Finish/end a game"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate player is in the game
    player_num = get_player_number(game, request.user_id)
    if player_num is None:
        raise HTTPException(status_code=403, detail="Player not in this game")
    
    # Set game status to finished
    game.status = "finished"
    
    # Determine winner if not already set (player with highest position)
    if game.winner_id is None:
        max_position = -1
        for player_id, position in game.player_positions.items():
            if position > max_position:
                max_position = position
                game.winner_id = player_id
    
    # Log game finish
    final_state = {
        "player_positions": game.player_positions,
        "winner_id": game.winner_id
    }
    log_game_finish(request.game_id, request.user_id, game.winner_id, final_state)
    
    return game

