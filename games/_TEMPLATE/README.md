# Game Template

This is a template for creating new games in the TableTime platform.

## How to Use This Template

1. Copy this entire `_TEMPLATE` directory to a new directory with your game name:
   ```bash
   cp -r games/_TEMPLATE games/your_game_name
   ```

2. Replace all instances of `your_game_name` with your actual game name (lowercase, no spaces)

3. Update `app/main.py`:
   - Change `GAME_NAME` to your game name
   - Change `GAME_TITLE` to your game's display name

4. Implement your game logic in `app/endpoints/game.py`

5. Define your game models in `app/models.py`

6. Follow the instructions in `GAME_TEMPLATE.md` in the project root to:
   - Add the service to `docker-compose.yml`
   - Add routes to API Gateway
   - Add to Telegram bot

## Required Endpoints

Your game must implement these endpoints:

- `POST /create` - Create a new game
- `POST /join` - Join an existing game
- `POST /action` - Perform a game action
- `GET /{game_id}/state` - Get current game state
- `GET /{game_id}/status` - Get game status
- `POST /finish` - Finish a game (optional but recommended)

## Important Rules

1. **Invite Codes**: Must use 6-digit codes (100000-999999)
2. **Game ID**: Use invite_code as game_id in GameState
3. **Status Values**: Use "waiting", "playing", "finished"
4. **Service Name**: Use lowercase, no spaces
5. **Port Numbers**: Use next available port (check docker-compose.yml)

## Example

See `games/rps/` for a complete working example.

