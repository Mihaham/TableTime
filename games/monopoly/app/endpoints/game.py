from fastapi import APIRouter, HTTPException, Response
from app.models import (
    GameState,
    RollDiceRequest,
    BuyPropertyRequest,
    EndTurnRequest,
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

# Starting money for each player
STARTING_MONEY = 1500

# Board configuration: Property positions and their prices/rent
# Format: position: {"name": str, "price": int, "rent": int}
PROPERTIES = {
    1: {"name": "Old Kent Road", "price": 60, "rent": 2},
    3: {"name": "Whitechapel Road", "price": 60, "rent": 4},
    5: {"name": "King's Cross Station", "price": 200, "rent": 25},
    6: {"name": "The Angel, Islington", "price": 100, "rent": 6},
    8: {"name": "Euston Road", "price": 100, "rent": 6},
    9: {"name": "Pentonville Road", "price": 120, "rent": 8},
    11: {"name": "Pall Mall", "price": 140, "rent": 10},
    13: {"name": "Whitehall", "price": 140, "rent": 10},
    14: {"name": "Northumberland Avenue", "price": 160, "rent": 12},
    16: {"name": "Bow Street", "price": 180, "rent": 14},
    18: {"name": "Marlborough Street", "price": 180, "rent": 14},
    19: {"name": "Vine Street", "price": 200, "rent": 16},
}

BOARD_SIZE = 20  # 0-19 board (20 spaces total, starting at 0)

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

def check_bankruptcy(game: GameState) -> Optional[int]:
    """Check if any player is bankrupt (money <= 0)"""
    for player_id, money in game.player_money.items():
        if money <= 0:
            return player_id
    return None

def get_property_info(position: int) -> Optional[dict]:
    """Get property information for a position"""
    return PROPERTIES.get(position)

def can_buy_property(game: GameState, player_id: int, position: int) -> bool:
    """Check if player can buy the property at this position"""
    # Check if it's a property space
    prop_info = get_property_info(position)
    if prop_info is None:
        return False
    
    # Check if property is already owned
    if position in game.property_owners and game.property_owners[position] is not None:
        return False
    
    # Check if player has enough money
    if game.player_money.get(player_id, 0) < prop_info["price"]:
        return False
    
    return True

@router.post("/create", response_model=GameState)
async def create_game(request: CreateGameRequest):
    """Create a new monopoly game"""
    logger.info(f"Creating monopoly game for player {request.player1_id}")
    # Generate 6-digit invite code (same format as all games: 100000-999999)
    invite_code = random.randint(100000, 999999)
    
    # Ensure unique invite code
    while invite_code in games:
        invite_code = random.randint(100000, 999999)
    
    # Initialize player positions and money
    player_positions = {request.player1_id: 0}
    player_money = {request.player1_id: STARTING_MONEY}
    player_properties = {request.player1_id: []}
    
    # Initialize property owners (all unowned)
    property_owners = {pos: None for pos in PROPERTIES.keys()}
    
    # Create game state
    game = GameState(
        game_id=invite_code,
        player1_id=request.player1_id,
        status="waiting",
        player_positions=player_positions,
        player_money=player_money,
        player_properties=player_properties,
        property_owners=property_owners
    )
    
    games[invite_code] = game
    logger.info(f"Monopoly game {invite_code} created successfully")
    
    # Log game creation
    log_game_creation(invite_code, request.player1_id, invite_code)
    
    return game

@router.post("/join", response_model=GameState)
async def join_game(request: JoinGameRequest):
    """Join an existing game as player 2 or player 3"""
    logger.info(f"Player {request.player_id} attempting to join monopoly game {request.game_id}")
    if request.game_id not in games:
        logger.warning(f"Monopoly game {request.game_id} not found")
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate player is not already in the game
    if request.player_id in [game.player1_id, game.player2_id, game.player3_id]:
        logger.warning(f"Player {request.player_id} is already in monopoly game {request.game_id}")
        raise HTTPException(status_code=400, detail="Player is already in this game")
    
    # Check if game is full
    if game.player2_id and game.player3_id:
        logger.warning(f"Monopoly game {request.game_id} is already full")
        raise HTTPException(status_code=400, detail="Game is already full (max 3 players)")
    
    # Add player 2 or player 3
    if game.player2_id is None:
        game.player2_id = request.player_id
        game.player_positions[request.player_id] = 0
        game.player_money[request.player_id] = STARTING_MONEY
        game.player_properties[request.player_id] = []
        logger.info(f"Player {request.player_id} joined as player 2 in game {request.game_id}")
    elif game.player3_id is None:
        game.player3_id = request.player_id
        game.player_positions[request.player_id] = 0
        game.player_money[request.player_id] = STARTING_MONEY
        game.player_properties[request.player_id] = []
        logger.info(f"Player {request.player_id} joined as player 3 in game {request.game_id}")
    
    # Start the game if we have at least 2 players
    player_count = get_player_count(game)
    if player_count >= 2 and game.status == "waiting":
        game.status = "playing"
        game.current_turn = 1  # Start with player 1
        logger.info(f"Monopoly game {request.game_id} started with {player_count} players")
    
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
    logger.info(f"Monopoly game {request.game_id} started with {player_count} players")
    
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
        raise HTTPException(status_code=400, detail="You have already rolled. Please move or end your turn.")
    
    # Roll dice (1-6)
    dice_roll = random.randint(1, 6)
    game.last_dice_roll = dice_roll
    
    # Get current position
    current_position = game.player_positions.get(request.user_id, 0)
    
    # Calculate new position (wrap around if exceeds board size)
    new_position = (current_position + dice_roll) % BOARD_SIZE
    
    # Update player position
    game.player_positions[request.user_id] = new_position
    
    # Check if player passed GO (position 0)
    passed_go = (current_position + dice_roll) >= BOARD_SIZE
    if passed_go:
        game.player_money[request.user_id] += 200  # Collect $200 for passing GO
        message = f"You rolled a {dice_roll}! Moved to position {new_position}. You passed GO and collected $200!"
    else:
        message = f"You rolled a {dice_roll}! Moved to position {new_position}."
    
    # Check property
    prop_info = get_property_info(new_position)
    can_buy = can_buy_property(game, request.user_id, new_position)
    
    if prop_info:
        if can_buy:
            message += f" You landed on {prop_info['name']} (${prop_info['price']}). You can buy it!"
        elif new_position in game.property_owners and game.property_owners[new_position] is not None:
            owner_id = game.property_owners[new_position]
            if owner_id != request.user_id:
                # Pay rent
                rent = prop_info["rent"]
                game.player_money[request.user_id] -= rent
                game.player_money[owner_id] += rent
                message += f" You landed on {prop_info['name']} (owned by Player {get_player_number(game, owner_id)}). Paid ${rent} rent."
                
                # Check for bankruptcy
                if game.player_money[request.user_id] <= 0:
                    game.status = "finished"
                    game.winner_id = owner_id
                    message += f" You went bankrupt! Player {get_player_number(game, owner_id)} wins!"
                    log_game_finish(request.game_id, request.user_id, owner_id, {
                        "final_money": game.player_money,
                        "final_positions": game.player_positions
                    })
            else:
                message += f" You landed on your own property {prop_info['name']}."
    else:
        message += " (No property here)"
    
    # Log dice roll
    log_game_action(
        request.game_id,
        request.user_id,
        "roll_dice",
        {
            "dice_roll": dice_roll,
            "player_number": player_num,
            "from_position": current_position,
            "to_position": new_position,
            "passed_go": passed_go
        }
    )
    
    return GameActionResponse(
        success=True,
        message=message,
        new_state=game,
        dice_roll=dice_roll,
        new_position=new_position,
        can_buy=can_buy if prop_info else None
    )

@router.post("/buy_property", response_model=GameActionResponse)
async def buy_property(request: BuyPropertyRequest):
    """Buy the property at the current position"""
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
    
    # Get current position
    position = game.player_positions.get(request.user_id, 0)
    
    # Check if player can buy this property
    if not can_buy_property(game, request.user_id, position):
        raise HTTPException(status_code=400, detail="Cannot buy this property (already owned, not a property, or insufficient funds)")
    
    prop_info = get_property_info(position)
    price = prop_info["price"]
    
    # Deduct money and assign property
    game.player_money[request.user_id] -= price
    game.property_owners[position] = request.user_id
    game.player_properties[request.user_id].append(position)
    
    message = f"Bought {prop_info['name']} for ${price}!"
    
    # Log buy action
    log_game_action(
        request.game_id,
        request.user_id,
        "buy_property",
        {
            "player_number": player_num,
            "property_name": prop_info["name"],
            "property_position": position,
            "price": price
        }
    )
    
    return GameActionResponse(
        success=True,
        message=message,
        new_state=game,
        property_cost=price
    )

@router.post("/end_turn", response_model=GameActionResponse)
async def end_turn(request: EndTurnRequest):
    """End the current player's turn"""
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
    
    # Reset dice roll and move to next turn
    game.last_dice_roll = None
    next_turn(game)
    
    message = f"Turn ended. It's now Player {game.current_turn}'s turn."
    
    # Log end turn
    log_game_action(
        request.game_id,
        request.user_id,
        "end_turn",
        {"player_number": player_num}
    )
    
    return GameActionResponse(
        success=True,
        message=message,
        new_state=game
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
    image_bytes = generate_board_image(
        game.player_positions,
        game.player_money,
        game.property_owners,
        current_player_id
    )
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
        "player_money": game.player_money,
        "property_owners": game.property_owners,
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
                "player_money": game.player_money,
                "property_owners": game.property_owners,
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
    
    # Determine winner if not already set (player with most money)
    if game.winner_id is None:
        max_money = -1
        for player_id, money in game.player_money.items():
            if money > max_money:
                max_money = money
                game.winner_id = player_id
    
    # Log game finish
    final_state = {
        "player_money": game.player_money,
        "player_positions": game.player_positions,
        "property_owners": game.property_owners,
        "winner_id": game.winner_id
    }
    log_game_finish(request.game_id, request.user_id, game.winner_id, final_state)
    
    return game
