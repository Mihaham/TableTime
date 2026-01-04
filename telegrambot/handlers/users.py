from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from utils.keyboard import start_keyboard, games_keyboard, game_start_keyboard
from utils.buttons import create_button, join_button, games_buttons, start_button, rps_button
from utils.texts import start_text, games_placeholder, join_text, game_creation_text, success_join, game_is_starting, user_joined_text
from utils.utils import create_game, join_game, check_button, send_seq_messages, start_game, get_rps_game_state, get_diceladders_game_state, get_monopoly_game_state, get_monopoly_game_by_user
import requests
from loguru import logger

router = Router()

class UserStates(StatesGroup):
    WaitingInviteCode = State()
    InGame = State()
    PlayingGame = State()



@router.message(Command("start"))
async def start(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    await message.reply(f"Привет, {message.from_user.username}!\n{start_text}", reply_markup=start_keyboard(user_id))

@router.message(Command("create_game"))


@router.message(Command("join"))
@router.message(F.text == join_button)
async def join(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    await message.reply(join_text, reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserStates.WaitingInviteCode)


@router.message(Command("create"))
@router.message(F.text == create_button)
async def create(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    await message.reply(games_placeholder, reply_markup=games_keyboard(user_id))

@router.message(lambda message: message.text and message.text in games_buttons and message.text != rps_button)
async def game_creation(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    invite_code = create_game(user_id, message.text)

    await message.reply(f"{game_creation_text} {invite_code}", reply_markup=game_start_keyboard(user_id))
    await state.set_state(UserStates.InGame)

@router.message(UserStates.WaitingInviteCode)
async def games_joining(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    try:
        invite_code = message.text.strip()
        # Validate it's a number
        try:
            code_int = int(invite_code)
        except ValueError:
            await message.reply("Код приглашения должен быть числом")
            return
        
        result = join_game(user_id, invite_code)
        logger.info(f"Join game result: {result}")
        
        # Check if this is a service-specific game
        if isinstance(result, dict) and "service" in result:
            service_name = result["service"]
            player_ids = result.get("player_ids", [])
            game_data = result.get("game_data", {})
            game_name = result.get("game_name")
            logger.info(f"Service: {service_name}, game_name: {game_name}, player_ids: {player_ids}")
            
            if service_name == "rps":
                # RPS game - switch to RPS handler flow
                try:
                    from handlers.rps import RPSStates, rps_move_keyboard_inline
                    from utils.texts import rps_game_started
                    
                    player1_id = game_data.get("player1_id")
                    player2_id = game_data.get("player2_id")
                    all_player_ids = [pid for pid in [player1_id, player2_id] if pid]
                    
                    await state.update_data(game_id=code_int, player_number=2)
                    await send_seq_messages(bot, all_player_ids, f"{user_joined_text} {message.from_user.username}")
                    await send_seq_messages(bot, all_player_ids, rps_game_started, reply_markup=rps_move_keyboard_inline(show_finish=True))
                    await state.set_state(RPSStates.Playing)
                    return
                except Exception as e:
                    # Fallback to normal flow if RPS handler fails
                    await message.reply(f"Ошибка при присоединении к игре RPS: {str(e)}")
                    return
            
            elif service_name == "game_engine":
                # Game engine managed game (Monopoly, Dice-Ladders, etc.)
                # game_name tells us which game it is
                await state.update_data(game_id=code_int, game_name=game_name)
                await send_seq_messages(bot, player_ids, f"{user_joined_text} {message.from_user.username}")
                await message.reply(success_join)
                await state.set_state(UserStates.InGame)
                return
        
        # Fallback - should not reach here
        await message.reply("Ошибка: не удалось присоединиться к игре")
        await state.set_state(UserStates.WaitingInviteCode)
    except ValueError as err:
        await message.reply(str(err))
        return

@router.message(F.text == start_button)
async def start_game_handler(message : Message, bot : Bot, state: FSMContext):
    user_id = message.from_user.id
    try:
        data = await state.get_data()
        game_name = data.get("game_name")
        game_id = data.get("game_id")
        logger.info(f"Start game handler called by user {user_id}, game_name: {game_name}, game_id: {game_id}, data: {data}")
        
        # If state is empty, try to get game info from game engine by user_id
        if not game_name or not game_id:
            logger.info(f"State is incomplete (game_name={game_name}, game_id={game_id}), trying to retrieve from game engine for user_id: {user_id}")
            from utils.utils import get_game_info_by_user, get_game_type_by_code
            game_info = get_game_info_by_user(user_id)
            if game_info:
                game_id = game_info.get("invite_code")
                game_name = game_info.get("game_name")
                logger.info(f"Retrieved game info: game_id={game_id}, game_name={game_name}")
                await state.update_data(game_id=game_id, game_name=game_name)
            elif game_id:
                # If we have game_id but not game_name, try to get game_name by code
                logger.info(f"game_name not in state, trying to retrieve from game engine for game_id: {game_id}")
                game_name = get_game_type_by_code(game_id)
                if game_name:
                    await state.update_data(game_name=game_name)
                    logger.info(f"Retrieved and stored game_name: {game_name}")
        
        # Handle dice-ladders game start
        if game_name == "Кости и Лестницы 🎲":
            # Use the game_id we already have (from state or retrieved from game engine)
            if not game_id:
                game_id = data.get("game_id")  # Fallback to state if not set
            logger.info(f"Dice-ladders game detected, game_id: {game_id}")
            if game_id:
                # Get all player IDs from game engine
                from utils.urls import game_engine_url
                info_response = requests.get(f"{game_engine_url}/game/{game_id}/info")
                if info_response.status_code != 200:
                    await message.reply("Ошибка: не удалось получить информацию об игре")
                    return
                
                game_info = info_response.json()
                all_player_ids = game_info.get("player_ids", [])
                
                if not all_player_ids or user_id not in all_player_ids:
                    await message.reply("Ошибка: вы не являетесь участником этой игры")
                    return
                
                # Create game in dice-ladders service with the first player (host)
                from utils.urls import diceladders_service_url
                payload = {"player1_id": all_player_ids[0]}  # Host is first player
                logger.info(f"Creating diceladders game with payload: {payload}")
                response = requests.post(f"{diceladders_service_url}/create", json=payload)
                logger.info(f"Diceladders create response: {response.status_code}, {response.text}")
                if response.status_code == 200:
                    game_data = response.json()
                    service_game_id = game_data.get("game_id")
                    await state.update_data(diceladders_game_id=service_game_id)
                    
                    # Join all other players to the diceladders service game
                    for player_id in all_player_ids[1:]:
                        join_payload = {"player_id": player_id, "game_id": service_game_id}
                        join_response = requests.post(f"{diceladders_service_url}/join", json=join_payload)
                        if join_response.status_code != 200:
                            logger.warning(f"Failed to join player {player_id} to diceladders game {service_game_id}")
                    
                    # Explicitly start the game after all players have joined
                    start_payload = {"player_id": all_player_ids[0], "game_id": service_game_id}
                    start_response = requests.post(f"{diceladders_service_url}/start", json=start_payload)
                    if start_response.status_code != 200:
                        logger.warning(f"Failed to start diceladders game {service_game_id}: {start_response.status_code}, {start_response.text}")
                        # Game might have auto-started on join, so continue anyway
                    
                    # Import dice-ladders handler
                    from handlers.diceladders import diceladders_keyboard, send_board_image
                    from utils.texts import diceladders_game_started
                    
                    # Update state for all players and send board
                    # Get current player's turn from game state
                    state_response = requests.get(f"{diceladders_service_url}/{service_game_id}/state")
                    logger.info(f"Getting game state, response: {state_response.status_code}")
                    if state_response.status_code == 200:
                        game_state = state_response.json()
                        logger.info(f"Game state: {game_state}")
                        current_turn_num = game_state.get("current_turn", 1)
                        current_turn_player_id = game_state.get(f"player{current_turn_num}_id")
                        logger.info(f"Current turn: {current_turn_num}, player_id: {current_turn_player_id}")
                        
                        # Send board to all players
                        for pid in all_player_ids:
                            try:
                                if pid == current_turn_player_id:
                                    logger.info(f"Sending board to player {pid} (current turn) with keyboard")
                                    result = await send_board_image(bot, pid, service_game_id, diceladders_game_started, reply_markup=diceladders_keyboard(show_finish=True))
                                    if not result:
                                        logger.error(f"Failed to send board image to player {pid}")
                                else:
                                    logger.info(f"Sending board to player {pid}")
                                    result = await send_board_image(bot, pid, service_game_id, diceladders_game_started)
                                    if not result:
                                        logger.error(f"Failed to send board image to player {pid}")
                            except Exception as e:
                                logger.error(f"Error sending board to player {pid}: {e}", exc_info=True)
                    else:
                        logger.error(f"Failed to get game state: {state_response.status_code}, {state_response.text}")
                        await message.reply("Ошибка: не удалось получить состояние игры")
                        return
                    
                    # Start the game in game engine and notify other players
                    ids = start_game(user_id)
                    await send_seq_messages(bot, ids, game_is_starting, reply_markup=ReplyKeyboardRemove())
                    logger.info(f"Dice-ladders game started successfully for players: {all_player_ids}")
                    return
                else:
                    error_msg = f"Ошибка: не удалось создать игру в сервисе Кости и Лестницы (status: {response.status_code})"
                    logger.error(error_msg)
                    await message.reply(error_msg)
                    return
            else:
                logger.warning(f"game_id is None for dice-ladders game, user_id: {user_id}")
                await message.reply("Ошибка: не найден код игры")
                return
        
        # Handle Monopoly game start
        if game_name == "Монополия 🏦":
            # Use the game_id we already have (from state or retrieved from game engine)
            if not game_id:
                game_id = data.get("game_id")  # Fallback to state if not set
            logger.info(f"Monopoly game detected, game_id: {game_id}")
            if game_id:
                # Get all player IDs from game engine
                from utils.urls import game_engine_url
                info_response = requests.get(f"{game_engine_url}/game/{game_id}/info")
                if info_response.status_code != 200:
                    await message.reply("Ошибка: не удалось получить информацию об игре")
                    return
                
                game_info = info_response.json()
                all_player_ids = game_info.get("player_ids", [])
                
                if not all_player_ids or user_id not in all_player_ids:
                    await message.reply("Ошибка: вы не являетесь участником этой игры")
                    return
                
                # Create game in monopoly service with the first player (host)
                from utils.urls import monopoly_service_url
                payload = {"player1_id": all_player_ids[0]}  # Host is first player
                logger.info(f"Creating monopoly game with payload: {payload}")
                response = requests.post(f"{monopoly_service_url}/create", json=payload)
                logger.info(f"Monopoly create response: {response.status_code}, {response.text}")
                if response.status_code == 200:
                    game_data = response.json()
                    service_game_id = game_data.get("game_id")
                    await state.update_data(monopoly_game_id=service_game_id)
                    
                    # Join all other players to the monopoly service game
                    for player_id in all_player_ids[1:]:
                        join_payload = {"player_id": player_id, "game_id": service_game_id}
                        join_response = requests.post(f"{monopoly_service_url}/join", json=join_payload)
                        if join_response.status_code != 200:
                            logger.warning(f"Failed to join player {player_id} to monopoly game {service_game_id}")
                    
                    # Explicitly start the game after all players have joined
                    start_payload = {"player_id": all_player_ids[0], "game_id": service_game_id}
                    start_response = requests.post(f"{monopoly_service_url}/start", json=start_payload)
                    if start_response.status_code != 200:
                        logger.warning(f"Failed to start monopoly game {service_game_id}: {start_response.status_code}, {start_response.text}")
                        # Game might have auto-started on join, so continue anyway
                    
                    # Import monopoly handler
                    from handlers.monopoly import monopoly_keyboard, send_board_image
                    from utils.texts import monopoly_game_started
                    
                    # Get game state to send board to players
                    state_response = requests.get(f"{monopoly_service_url}/{service_game_id}/state")
                    logger.info(f"Getting monopoly game state, response: {state_response.status_code}")
                    if state_response.status_code == 200:
                        game_state = state_response.json()
                        logger.info(f"Monopoly game state: {game_state}")
                        current_turn_num = game_state.get("current_turn", 1)
                        current_turn_player_id = game_state.get(f"player{current_turn_num}_id")
                        logger.info(f"Current turn: {current_turn_num}, player_id: {current_turn_player_id}")
                        
                        # Send board to all players
                        for pid in all_player_ids:
                            try:
                                if pid == current_turn_player_id:
                                    await send_board_image(bot, pid, service_game_id, monopoly_game_started,
                                                          reply_markup=monopoly_keyboard(show_finish=True))
                                else:
                                    await send_board_image(bot, pid, service_game_id, monopoly_game_started)
                            except Exception as e:
                                logger.error(f"Error sending board to player {pid}: {e}", exc_info=True)
                    else:
                        logger.error(f"Failed to get monopoly game state: {state_response.status_code}, {state_response.text}")
                        # Fallback to text message
                        for pid in all_player_ids:
                            try:
                                await bot.send_message(pid, monopoly_game_started)
                            except Exception as e:
                                logger.error(f"Error sending message to player {pid}: {e}", exc_info=True)
                    
                    # Start the game in game engine and notify other players
                    ids = start_game(user_id)
                    await send_seq_messages(bot, ids, game_is_starting, reply_markup=ReplyKeyboardRemove())
                    logger.info(f"Monopoly game started successfully for players: {all_player_ids}")
                    return
                else:
                    error_msg = f"Ошибка: не удалось создать игру в сервисе Монополия (status: {response.status_code})"
                    logger.error(error_msg)
                    await message.reply(error_msg)
                    return
            else:
                logger.warning(f"game_id is None for monopoly game, user_id: {user_id}")
                await message.reply("Ошибка: не найден код игры")
                return
        
        # Default game engine start (for games that don't need special handling)
        logger.info(f"Using default game engine start for user {user_id}, game_name: {game_name}")
        try:
            ids = start_game(user_id)
            await send_seq_messages(bot, ids, game_is_starting, reply_markup=ReplyKeyboardRemove())
        except ValueError as err:
            await message.reply(str(err))
            return
    except ValueError as err:
        logger.error(f"ValueError in start_game_handler: {err}")
        await message.reply(str(err))
        return
    except Exception as e:
        logger.error(f"Exception in start_game_handler: {e}", exc_info=True)
        await message.reply(f"Ошибка: {str(e)}")
        return

    #for id in ids:
    #    await bot.set_state(UserStates.PlayingGame)

