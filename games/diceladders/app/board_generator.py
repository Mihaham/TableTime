from PIL import Image, ImageDraw, ImageFont
import io
from typing import Dict, Optional

# Board configuration
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

BOARD_SIZE = 100  # 0-100 board

def generate_board_image(player_positions: Dict[int, int], current_turn: Optional[int] = None) -> bytes:
    """
    Generate a board image showing player positions
    Returns image as bytes (PNG format)
    """
    # Image dimensions
    width = 800
    height = 800
    cell_size = width // 10  # 10x10 grid
    
    # Create image with white background
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 20)
        font_small = ImageFont.truetype("arial.ttf", 14)
    except:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Draw grid
    for i in range(11):
        # Vertical lines
        x = i * cell_size
        draw.line([(x, 0), (x, height)], fill='black', width=2)
        # Horizontal lines
        y = i * cell_size
        draw.line([(0, y), (width, y)], fill='black', width=2)
    
    # Draw numbers and player positions (snake pattern: left to right, then right to left)
    player_colors = {
        1: 'red',
        2: 'blue', 
        3: 'green'
    }
    
    for pos in range(BOARD_SIZE + 1):
        row = 9 - (pos // 10)  # Start from top
        col = pos % 10 if (pos // 10) % 2 == 0 else 9 - (pos % 10)  # Snake pattern
        
        x = col * cell_size + cell_size // 2
        y = row * cell_size + cell_size // 2
        
        # Draw number
        text = str(pos)
        bbox = draw.textbbox((x, y), text, font=font_small)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text((x - text_width//2, y - text_height//2), text, fill='black', font=font_small)
        
        # Draw player positions
        for player_num, player_id in enumerate(player_positions.keys(), 1):
            if player_positions[player_id] == pos:
                color = player_colors.get(player_num, 'gray')
                # Draw circle for player
                offset = (player_num - 1) * 15 - 15  # Offset multiple players
                circle_radius = 12
                draw.ellipse([
                    x - circle_radius + offset,
                    y - circle_radius - 15,
                    x + circle_radius + offset,
                    y + circle_radius - 15
                ], fill=color, outline='black', width=2)
                # Draw player number
                draw.text((x + offset - 5, y - 30), f"P{player_num}", fill='black', font=font_small)
    
    # Draw ladders (green lines going up)
    for start, end in BOARD_LADDERS.items():
        if end > start:  # Ladder
            row_start = 9 - (start // 10)
            col_start = start % 10 if (start // 10) % 2 == 0 else 9 - (start % 10)
            x_start = col_start * cell_size + cell_size // 2
            y_start = row_start * cell_size + cell_size // 2
            
            row_end = 9 - (end // 10)
            col_end = end % 10 if (end // 10) % 2 == 0 else 9 - (end % 10)
            x_end = col_end * cell_size + cell_size // 2
            y_end = row_end * cell_size + cell_size // 2
            
            draw.line([(x_start, y_start), (x_end, y_end)], fill='green', width=4)
            # Draw ladder symbol
            draw.text((x_start, y_start - 20), "🪜", font=font_small)
    
    # Draw snakes (red lines going down)
    for start, end in BOARD_LADDERS.items():
        if end < start:  # Snake
            row_start = 9 - (start // 10)
            col_start = start % 10 if (start // 10) % 2 == 0 else 9 - (start % 10)
            x_start = col_start * cell_size + cell_size // 2
            y_start = row_start * cell_size + cell_size // 2
            
            row_end = 9 - (end // 10)
            col_end = end % 10 if (end // 10) % 2 == 0 else 9 - (end % 10)
            x_end = col_end * cell_size + cell_size // 2
            y_end = row_end * cell_size + cell_size // 2
            
            draw.line([(x_start, y_start), (x_end, y_end)], fill='red', width=4)
            # Draw snake symbol
            draw.text((x_start, y_start - 20), "🐍", font=font_small)
    
    # Highlight current turn player
    if current_turn:
        for player_num, player_id in enumerate(player_positions.keys(), 1):
            if player_id == current_turn:
                color = player_colors.get(player_num, 'gray')
                # Draw border around board to indicate turn
                draw.rectangle([5, 5, width-5, height-5], outline=color, width=5)
                break
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

