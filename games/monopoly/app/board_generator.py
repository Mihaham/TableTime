from PIL import Image, ImageDraw, ImageFont
import io
from typing import Dict, Optional

# Property groups (streets) - properties that form monopolies
PROPERTY_GROUPS = {
    "brown": [1, 3],      # Brown street (2 properties)
    "light_blue": [6, 8, 9],  # Light blue street (3 properties)
    "pink": [11, 13, 14],  # Pink street (3 properties)
    "orange": [16, 18, 19],  # Orange street (3 properties)
}

# Property colors for each group
GROUP_COLORS = {
    "brown": (139, 69, 19),      # Brown
    "light_blue": (173, 216, 230),  # Light blue
    "pink": (255, 182, 193),     # Pink
    "orange": (255, 165, 0),     # Orange
}

# Board configuration from game.py
PROPERTIES = {
    1: {"name": "Old Kent Road", "price": 60, "rent": 2, "group": "brown"},
    3: {"name": "Whitechapel Road", "price": 60, "rent": 4, "group": "brown"},
    5: {"name": "King's Cross Station", "price": 200, "rent": 25, "group": None},
    6: {"name": "The Angel, Islington", "price": 100, "rent": 6, "group": "light_blue"},
    8: {"name": "Euston Road", "price": 100, "rent": 6, "group": "light_blue"},
    9: {"name": "Pentonville Road", "price": 120, "rent": 8, "group": "light_blue"},
    11: {"name": "Pall Mall", "price": 140, "rent": 10, "group": "pink"},
    13: {"name": "Whitehall", "price": 140, "rent": 10, "group": "pink"},
    14: {"name": "Northumberland Avenue", "price": 160, "rent": 12, "group": "pink"},
    16: {"name": "Bow Street", "price": 180, "rent": 14, "group": "orange"},
    18: {"name": "Marlborough Street", "price": 180, "rent": 14, "group": "orange"},
    19: {"name": "Vine Street", "price": 200, "rent": 16, "group": "orange"},
}

BOARD_SIZE = 20  # 0-19 board

def get_property_group_color(position: int) -> Optional[tuple]:
    """Get color for property group"""
    if position in PROPERTIES:
        group = PROPERTIES[position].get("group")
        if group:
            return GROUP_COLORS.get(group)
    return None

def generate_board_image(
    player_positions: Dict[int, int],
    player_money: Dict[int, int],
    property_owners: Dict[int, Optional[int]],
    current_turn: Optional[int] = None
) -> bytes:
    """
    Generate a Monopoly-style board image with rectangular border layout
    Returns image as bytes (PNG format)
    """
    # Image dimensions
    width = 1000
    height = 1000
    
    # Create image with light gray background
    img = Image.new('RGB', (width, height), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts (use default if not available)
    try:
        font_large = ImageFont.truetype("arial.ttf", 20)
        font_medium = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 12)
    except:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
    
    # Board layout: rectangular border
    # Positions arranged clockwise: 0-4 (bottom), 5-9 (right), 10-14 (top), 15-19 (left)
    board_margin = 80
    board_width = width - 2 * board_margin
    board_height = height - 2 * board_margin
    
    # Corner size (larger for GO and special spaces)
    corner_size = 120
    side_cell_width = (board_width - 2 * corner_size) // 5  # 5 cells per side
    side_cell_height = (board_height - 2 * corner_size) // 5
    
    player_colors = {
        1: (255, 80, 80),    # Red
        2: (80, 80, 255),    # Blue
        3: (80, 255, 80),    # Green
    }
    
    # Function to get position coordinates
    def get_position_coords(pos):
        """Get coordinates for a position on the board (clockwise layout)"""
        if pos == 0:  # GO (bottom-left corner)
            return (board_margin, height - board_margin - corner_size, 
                   board_margin + corner_size, height - board_margin)
        elif 1 <= pos <= 4:  # Bottom row (left to right)
            x = board_margin + corner_size + (pos - 1) * side_cell_width
            return (x, height - board_margin - side_cell_height,
                   x + side_cell_width, height - board_margin)
        elif pos == 5:  # Bottom-right corner
            return (width - board_margin - corner_size, height - board_margin - corner_size,
                   width - board_margin, height - board_margin)
        elif 6 <= pos <= 9:  # Right side (bottom to top)
            y = height - board_margin - corner_size - (pos - 5) * side_cell_height
            return (width - board_margin - side_cell_width, y,
                   width - board_margin, y + side_cell_height)
        elif pos == 10:  # Top-right corner
            return (width - board_margin - corner_size, board_margin,
                   width - board_margin, board_margin + corner_size)
        elif 11 <= pos <= 14:  # Top row (right to left)
            x = width - board_margin - corner_size - (pos - 10) * side_cell_width
            return (x, board_margin, x + side_cell_width, board_margin + side_cell_height)
        elif pos == 15:  # Top-left corner
            return (board_margin, board_margin, board_margin + corner_size, board_margin + corner_size)
        else:  # 16-19: Left side (top to bottom)
            y = board_margin + corner_size + (pos - 15) * side_cell_height
            return (board_margin, y, board_margin + side_cell_width, y + side_cell_height)
    
    # Draw all positions
    for pos in range(BOARD_SIZE):
        x1, y1, x2, y2 = get_position_coords(pos)
        cell_width = x2 - x1
        cell_height = y2 - y1
        
        # Determine if it's a property
        is_property = pos in PROPERTIES
        prop_info = PROPERTIES.get(pos)
        is_owned = pos in property_owners and property_owners[pos] is not None
        
        # Get cell background color
        if pos == 0:  # GO
            cell_color = (255, 255, 200)  # Yellow
        elif is_property:
            # Use property group color if available
            group_color = get_property_group_color(pos)
            if is_owned:
                owner_id = property_owners[pos]
                owner_num = None
                for i, pid in enumerate(player_positions.keys(), 1):
                    if pid == owner_id:
                        owner_num = i
                        break
                if owner_num and owner_num in player_colors:
                    owner_color = player_colors[owner_num]
                    if group_color:
                        # Blend group color with owner color
                        cell_color = tuple((gc + oc) // 2 for gc, oc in zip(group_color, owner_color))
                    else:
                        cell_color = tuple(c // 2 + 127 for c in owner_color)
                else:
                    cell_color = (200, 200, 200)
            else:
                cell_color = group_color if group_color else (255, 255, 255)
        else:
            cell_color = (220, 220, 220)  # Gray for non-property
        
        # Draw cell rectangle
        draw.rectangle([x1, y1, x2, y2], fill=cell_color, outline='black', width=2)
        
        # Draw position number
        draw.text((x1 + 5, y1 + 5), str(pos), fill='black', font=font_small)
        
        # Draw property name if it's a property
        if is_property and prop_info:
            prop_name = prop_info["name"]
            # Truncate name if too long
            max_chars = 15 if cell_width > 100 else 8
            if len(prop_name) > max_chars:
                prop_name = prop_name[:max_chars-2] + ".."
            
            # Center text
            text_bbox = draw.textbbox((0, 0), prop_name, font=font_small)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = x1 + (cell_width - text_width) // 2
            text_y = y1 + 20
            
            draw.text((text_x, text_y), prop_name, fill='black', font=font_small)
            
            # Draw price
            price_text = f"${prop_info['price']}"
            price_bbox = draw.textbbox((0, 0), price_text, font=font_small)
            price_width = price_bbox[2] - price_bbox[0]
            price_x = x1 + (cell_width - price_width) // 2
            price_y = y1 + 35
            draw.text((price_x, price_y), price_text, fill='blue', font=font_small)
        elif pos == 0:
            # GO text
            go_bbox = draw.textbbox((0, 0), "GO", font=font_large)
            go_width = go_bbox[2] - go_bbox[0]
            go_x = x1 + (cell_width - go_width) // 2
            go_y = y1 + (cell_height - 20) // 2
            draw.text((go_x, go_y), "GO", fill='black', font=font_large)
        
        # Draw player positions
        player_offsets = {1: (-15, -15), 2: (0, -15), 3: (15, -15)}
        for player_num, player_id in enumerate(player_positions.keys(), 1):
            if player_positions.get(player_id) == pos:
                color = player_colors.get(player_num, (128, 128, 128))
                offset_x, offset_y = player_offsets.get(player_num, (0, -15))
                center_x = x1 + cell_width // 2 + offset_x
                center_y = y1 + cell_height - 25 + offset_y
                
                # Draw player circle
                circle_radius = 12
                draw.ellipse([
                    center_x - circle_radius,
                    center_y - circle_radius,
                    center_x + circle_radius,
                    center_y + circle_radius
                ], fill=color, outline='black', width=2)
                
                # Draw player number
                p_text = str(player_num)
                p_bbox = draw.textbbox((0, 0), p_text, font=font_small)
                p_width = p_bbox[2] - p_bbox[0]
                p_height = p_bbox[3] - p_bbox[1]
                draw.text((center_x - p_width // 2, center_y - p_height // 2), 
                         p_text, fill='white', font=font_small)
    
    # Draw player info panel (center of board)
    center_x = width // 2
    center_y = height // 2
    panel_width = 300
    panel_height = 120
    panel_x = center_x - panel_width // 2
    panel_y = center_y - panel_height // 2
    
    # Draw panel background
    draw.rectangle([panel_x, panel_y, panel_x + panel_width, panel_y + panel_height],
                  fill='white', outline='black', width=2)
    
    # Draw player info
    info_x = panel_x + 15
    info_y = panel_y + 15
    line_height = 30
    
    draw.text((info_x, info_y), "Players:", fill='black', font=font_medium)
    
    for player_num, player_id in enumerate(player_positions.keys(), 1):
        color = player_colors.get(player_num, (128, 128, 128))
        money = player_money.get(player_id, 0)
        position = player_positions.get(player_id, 0)
        
        # Draw player color indicator
        draw.ellipse([info_x, info_y + 20 + (player_num-1)*line_height, 
                     info_x + 15, info_y + 35 + (player_num-1)*line_height],
                    fill=color, outline='black', width=1)
        
        # Draw player info text (English to avoid encoding issues)
        turn_indicator = " *" if current_turn == player_id else ""
        player_text = f"P{player_num}: ${money} | Pos: {position}{turn_indicator}"
        
        draw.text((info_x + 20, info_y + 22 + (player_num-1)*line_height), 
                 player_text, fill='black', font=font_small)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()
