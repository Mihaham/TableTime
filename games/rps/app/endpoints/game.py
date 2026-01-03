from fastapi import APIRouter, HTTPException
from app.models import (
    GameState, 
    GameAction, 
    GameActionResponse, 
    Choice,
    CreateGameRequest,
    JoinGameRequest,
    FinishGameRequest
)
from app.utils import log_game_creation, log_game_join, log_game_action, log_game_finish
from typing import Dict, Optional
import random

router = APIRouter()

# In-memory game storage (in production, use a database)
games: Dict[int, GameState] = {}  # Key is invite_code (6-digit number)

def determine_winner(choice1: Choice, choice2: Choice) -> Optional[int]:
    """Determine winner of a round. Returns 1 if player1 wins, 2 if player2 wins, None if tie."""
    if choice1 == choice2:
        return None  # Tie
    
    winning_rules = {
        Choice.ROCK: Choice.SCISSORS,
        Choice.PAPER: Choice.ROCK,
        Choice.SCISSORS: Choice.PAPER
    }
    
    if winning_rules[choice1] == choice2:
        return 1
    else:
        return 2

@router.post("/create", response_model=GameState)
async def create_game(request: CreateGameRequest):
    """Create a new rock-paper-scissors game"""
    # Generate 6-digit invite code (same format as other games: 100000-999999)
    invite_code = random.randint(100000, 999999)
    
    # Ensure unique invite code
    while invite_code in games:
        invite_code = random.randint(100000, 999999)
    
    game = GameState(
        game_id=invite_code,  # Use invite_code as game_id
        player1_id=request.player1_id,
        status="waiting"
    )
    
    games[invite_code] = game
    
    # Log game creation
    log_game_creation(invite_code, request.player1_id, invite_code)
    
    return game

@router.post("/join", response_model=GameState)
async def join_game(request: JoinGameRequest):
    """Join an existing game as player 2"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    if game.player2_id is not None:
        raise HTTPException(status_code=400, detail="Game is already full")
    
    if game.player1_id == request.player2_id:
        raise HTTPException(status_code=400, detail="Player cannot join their own game")
    
    game.player2_id = request.player2_id
    game.status = "playing"
    
    # Log game join
    log_game_join(request.game_id, request.player2_id)
    
    return game

@router.post("/action", response_model=GameActionResponse)
async def make_move(action: GameAction):
    """Make a move (rock, paper, or scissors)"""
    if action.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[action.game_id]
    
    # Validate player is in the game
    if action.user_id not in [game.player1_id, game.player2_id]:
        raise HTTPException(status_code=403, detail="Player not in this game")
    
    # Validate game status
    if game.status != "playing":
        raise HTTPException(status_code=400, detail=f"Game is not in playing status. Current status: {game.status}")
    
    # Set the player's choice
    is_player1 = action.user_id == game.player1_id
    
    if is_player1:
        if game.player1_choice is not None:
            raise HTTPException(status_code=400, detail="Player 1 has already made their choice for this round")
        game.player1_choice = action.choice
        log_game_action(action.game_id, action.user_id, "player1_move", {"choice": action.choice.value})
    else:
        if game.player2_choice is not None:
            raise HTTPException(status_code=400, detail="Player 2 has already made their choice for this round")
        game.player2_choice = action.choice
        log_game_action(action.game_id, action.user_id, "player2_move", {"choice": action.choice.value})
    
    message = f"Player {1 if is_player1 else 2} chose {action.choice.value}"
    round_result = None
    
    # Check if both players have made their choices
    if game.player1_choice is not None and game.player2_choice is not None:
        # Determine winner of this round
        winner = determine_winner(game.player1_choice, game.player2_choice)
        # Log round completion with detailed info
        round_winner_info = None
        if winner == 1:
            round_winner_info = "player1"
        elif winner == 2:
            round_winner_info = "player2"
        else:
            round_winner_info = "tie"
        
        log_game_action(
            action.game_id, 
            action.user_id, 
            "round_complete",
            {
                "round_number": game.round_number,
                "player1_choice": game.player1_choice.value,
                "player2_choice": game.player2_choice.value,
                "player1_id": game.player1_id,
                "player2_id": game.player2_id,
                "winner": round_winner_info,
                "player1_score": game.player1_score,
                "player2_score": game.player2_score
            }
        )
        game.last_round_winner = winner
        
        if winner == 1:
            game.player1_score += 1
            round_result = f"Player 1 wins! {game.player1_choice.value} beats {game.player2_choice.value}"
        elif winner == 2:
            game.player2_score += 1
            round_result = f"Player 2 wins! {game.player2_choice.value} beats {game.player1_choice.value}"
        else:
            round_result = f"It's a tie! Both chose {game.player1_choice.value}"
        
        # Prepare for next round (reset choices but keep scores)
        game.round_number += 1
        game.player1_choice = None
        game.player2_choice = None
    
    return GameActionResponse(
        success=True,
        message=message,
        new_state=game,
        round_result=round_result
    )

@router.get("/{game_id}/state", response_model=GameState)
async def get_game_state(game_id: int):
    """Get current game state"""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return games[game_id]

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
        "player1_score": game.player1_score,
        "player2_score": game.player2_score,
        "round_number": game.round_number
    }

@router.post("/finish", response_model=GameState)
async def finish_game(request: FinishGameRequest):
    """Finish/end an RPS game"""
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game = games[request.game_id]
    
    # Validate player is in the game
    if request.user_id not in [game.player1_id, game.player2_id]:
        raise HTTPException(status_code=403, detail="Player not in this game")
    
    # Set game status to finished
    game.status = "finished"
    
    # Determine final winner based on scores
    if game.player1_score > game.player2_score:
        game.winner = game.player1_id
    elif game.player2_score > game.player1_score:
        game.winner = game.player2_id
    else:
        game.winner = None  # Tie
    
    # Log game finish
    final_state = {
        "player1_score": game.player1_score,
        "player2_score": game.player2_score,
        "winner": game.winner
    }
    log_game_finish(request.game_id, request.user_id, game.winner, final_state)
    
    return game

@router.get("/")
async def list_games():
    """List all available games (waiting for player 2)"""
    waiting_games = [
        {
            "game_id": game.game_id,
            "player1_id": game.player1_id,
            "status": game.status
        }
        for game in games.values()
        if game.status == "waiting"
    ]
    return {"games": waiting_games}

