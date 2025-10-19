"""
Color Utilities for Smart SVG Theming

Provides color manipulation, palette generation, and intelligent color mapping
for SVG diagram templates.
"""

import colorsys
from typing import Dict, List, Tuple, Optional, Any
import re


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color"""
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert RGB to HSL (0-360, 0-100, 0-100)"""
    r, g, b = r/255.0, g/255.0, b/255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, l * 100


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """Convert HSL (0-360, 0-100, 0-100) to RGB"""
    h, s, l = h/360.0, s/100.0, l/100.0
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def adjust_lightness(hex_color: str, percent: float) -> str:
    """Adjust lightness of a color by percentage (-100 to 100)"""
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    l = max(0, min(100, l + percent))
    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r, g, b)


def adjust_saturation(hex_color: str, percent: float) -> str:
    """Adjust saturation of a color by percentage (-100 to 100)"""
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    s = max(0, min(100, s + percent))
    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r, g, b)


def generate_shades(base_color: str, count: int = 5) -> List[str]:
    """Generate shades from a base color"""
    shades = []
    step = 60 / (count - 1)  # Distribute from light to dark
    
    for i in range(count):
        lightness_adjust = 30 - (i * step)  # From +30 to -30
        shades.append(adjust_lightness(base_color, lightness_adjust))
    
    return shades


def get_complementary(hex_color: str) -> str:
    """Get complementary color (opposite on color wheel)"""
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    h = (h + 180) % 360
    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r, g, b)


def get_analogous(hex_color: str) -> Tuple[str, str]:
    """Get two analogous colors (adjacent on color wheel)"""
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    
    h1 = (h + 30) % 360
    h2 = (h - 30) % 360
    
    r1, g1, b1 = hsl_to_rgb(h1, s, l)
    r2, g2, b2 = hsl_to_rgb(h2, s, l)
    
    return rgb_to_hex(r1, g1, b1), rgb_to_hex(r2, g2, b2)


def get_triadic(hex_color: str) -> Tuple[str, str]:
    """Get two triadic colors (120 degrees apart on color wheel)"""
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    
    h1 = (h + 120) % 360
    h2 = (h + 240) % 360
    
    r1, g1, b1 = hsl_to_rgb(h1, s, l)
    r2, g2, b2 = hsl_to_rgb(h2, s, l)
    
    return rgb_to_hex(r1, g1, b1), rgb_to_hex(r2, g2, b2)


class MonochromaticTheme:
    """Monochromatic color theme using shades of a single color"""
    
    def __init__(self, primary_color: str):
        """
        Initialize with a single color
        
        Args:
            primary_color: Base color for generating shades
        """
        self.primary = primary_color.lower()
        self.secondary = None  # Not used in monochromatic
        self.accent = None     # Not used in monochromatic
        self.palette = self._generate_palette()
        self.color_map = self._create_color_map()
    
    def _generate_palette(self) -> Dict[str, List[str]]:
        """Generate monochromatic palette with various shades"""
        palette = {}
        
        # Generate 7 shades from very light to very dark
        # BUT ensure minimum saturation and avoid near-white colors
        palette['primary'] = []
        
        # First ensure the base color has sufficient saturation
        r, g, b = hex_to_rgb(self.primary)
        h, s, l = rgb_to_hsl(r, g, b)
        
        # Ensure minimum saturation of 30%
        if s < 30:
            s = 30
            r, g, b = hsl_to_rgb(h, s, l)
            base_color = rgb_to_hex(r, g, b)
        else:
            base_color = self.primary
        
        # Use better distributed lightness values for more variety
        lightness_values = [88, 72, 58, 44, 30, 18, 10]
        for i, target_lightness in enumerate(lightness_values):
            # Adjust from current lightness
            r, g, b = hex_to_rgb(base_color)
            h, s, l = rgb_to_hsl(r, g, b)
            
            # Vary saturation slightly based on lightness for better visual distinction
            adjusted_s = s
            if target_lightness > 70:
                adjusted_s = max(25, s - 15)  # Lighter shades less saturated
            elif target_lightness < 25:
                adjusted_s = min(90, s + 10)  # Darker shades more saturated
            else:
                adjusted_s = max(30, s)  # Middle shades maintain saturation
            
            r, g, b = hsl_to_rgb(h, adjusted_s, target_lightness)
            shade = rgb_to_hex(r, g, b)
            palette['primary'].append(shade)
        
        # Also generate slightly desaturated versions for variety (labeled as secondary)
        palette['secondary'] = []
        for i in range(5):
            target_lightness = 70 - (i * 40 / 4)
            # Use base color but reduce saturation slightly
            r, g, b = hex_to_rgb(base_color)
            h, s, l = rgb_to_hsl(r, g, b)
            # Reduce saturation but keep minimum of 20%
            r, g, b = hsl_to_rgb(h, max(20, s - 20), target_lightness)
            shade = rgb_to_hex(r, g, b)
            palette['secondary'].append(shade)
        
        # Even more desaturated for accents
        palette['accent'] = []
        for i in range(3):
            target_lightness = 60 - (i * 30 / 2)
            r, g, b = hex_to_rgb(base_color)
            h, s, l = rgb_to_hsl(r, g, b)
            # Further reduce saturation but keep minimum of 15%
            r, g, b = hsl_to_rgb(h, max(15, s - 30), target_lightness)
            shade = rgb_to_hex(r, g, b)
            palette['accent'].append(shade)
        
        # Neutral grays for text and borders
        gray_base = adjust_saturation(self.primary, -95)
        palette['neutral'] = generate_shades(gray_base, 5)
        
        return palette
    
    def _create_color_map(self) -> Dict[str, str]:
        """Map template colors to monochromatic shades with better distribution"""
        color_map = {}
        
        # All template colors
        template_colors = [
            '#ffffff', '#fafafa', '#f8f8f8', '#f5f5f5', '#f0f0f0',
            '#e5e5e5', '#e0e0e0', '#dbeafe', '#d1fae5', '#dcfce7',
            '#cbd5e1', '#bfdbfe', '#bbf7d0', '#93c5fd', '#86efac',
            '#64748b', '#60a5fa', '#3b82f6', '#22c55e', '#1e293b',
            '#2563eb', '#10b981', '#059669', '#0891b2', '#06b6d4',
            '#0e7490', '#14b8a6', '#0d9488', '#f59e0b', '#d97706',
            '#dc2626', '#b91c1c', '#991b1b', '#7f1d1d', '#fbbf24',
            '#f97316', '#fb923c', '#ef4444', '#f87171', '#fca5a5',
            '#fed7aa', '#fde68a', '#fef3c7', '#eff6ff', '#f0f9ff',
            '#475569', '#334155', '#1f2937', '#111827', '#0f172a',
            '#94a3b8', '#e2e8f0', '#f1f5f9', '#f3f4f6', '#e5e7eb',
            '#d1d5db', '#9ca3af', '#6b7280', '#4b5563', '#374151',
            '#1f2937'
        ]
        
        # Group colors by lightness for better distribution
        color_groups = {'very_light': [], 'light': [], 'medium': [], 'dark': [], 'very_dark': []}
        
        for color in template_colors:
            r, g, b = hex_to_rgb(color)
            h, s, l = rgb_to_hsl(r, g, b)
            
            if l > 85:
                color_groups['very_light'].append(color)
            elif l > 65:
                color_groups['light'].append(color)
            elif l > 45:
                color_groups['medium'].append(color)
            elif l > 25:
                color_groups['dark'].append(color)
            else:
                color_groups['very_dark'].append(color)
        
        # Distribute colors across the palette more evenly
        group_indices = {
            'very_light': 0,
            'light': 0,
            'medium': 0,
            'dark': 0,
            'very_dark': 0
        }
        
        # Map very light colors
        for i, color in enumerate(color_groups['very_light']):
            if color == '#ffffff':
                color_map[color] = '#ffffff'
            else:
                # Cycle through lightest shades
                idx = i % 2
                if idx == 0:
                    color_map[color] = self.palette['primary'][0]
                else:
                    color_map[color] = self.palette['secondary'][0]
        
        # Map light colors
        for i, color in enumerate(color_groups['light']):
            # Cycle through light shades
            idx = i % 3
            if idx == 0:
                color_map[color] = self.palette['primary'][1]
            elif idx == 1:
                color_map[color] = self.palette['secondary'][1]
            else:
                color_map[color] = self.palette['neutral'][1]
        
        # Map medium colors
        for i, color in enumerate(color_groups['medium']):
            # Cycle through medium shades
            idx = i % 3
            if idx == 0:
                color_map[color] = self.palette['primary'][2]
            elif idx == 1:
                color_map[color] = self.palette['primary'][3]
            else:
                color_map[color] = self.palette['secondary'][2]
        
        # Map dark colors
        for i, color in enumerate(color_groups['dark']):
            # Cycle through dark shades
            idx = i % 3
            if idx == 0:
                color_map[color] = self.palette['primary'][4]
            elif idx == 1:
                color_map[color] = self.palette['primary'][5]
            else:
                color_map[color] = self.palette['neutral'][3]
        
        # Map very dark colors
        for i, color in enumerate(color_groups['very_dark']):
            # Use darkest shades
            idx = i % 2
            if idx == 0:
                color_map[color] = self.palette['primary'][6]
            else:
                color_map[color] = self.palette['neutral'][4]
        
        return color_map
    
    def apply_to_svg(self, svg_content: str) -> str:
        """Apply monochromatic theme to SVG content with unique color enforcement"""
        import re
        
        # Apply general color theme
        result = svg_content
        
        # Sort by length to avoid partial replacements
        sorted_colors = sorted(self.color_map.keys(), key=len, reverse=True)
        
        # Apply general theme replacements
        for old_color in sorted_colors:
            if old_color in result:
                new_color = self.color_map[old_color]
                result = result.replace(old_color, new_color)
                result = result.replace(old_color.upper(), new_color.upper())
        
        # Note: Element-specific colors are now applied in SVGAgent._apply_final_element_colors()
        # to ensure they are applied after all other processing
        
        return result
    
    def _apply_element_specific_colors(self, svg_content: str) -> str:
        """Apply specific colors based on element IDs for better distribution"""
        import re
        
        result = svg_content
        
        # Matrix quadrant-specific coloring
        if 'id="q1_fill"' in svg_content and 'id="q4_fill"' in svg_content:
            # Q1 (top-right) - Lightest shade
            color_q1 = self.palette["primary"][1]
            result = re.sub(
                r'(id="q1_fill"[^>]*fill=")[^"]*(")',
                rf'\1{color_q1}\2',
                result
            )
            result = re.sub(
                r'(id="q1_fill"[^>]*stroke=")[^"]*(")',
                rf'\1{color_q1}\2',
                result
            )
            
            # Q2 (top-left) - Medium light
            color_q2 = self.palette["primary"][2]
            result = re.sub(
                r'(id="q2_fill"[^>]*fill=")[^"]*(")',
                rf'\1{color_q2}\2',
                result
            )
            result = re.sub(
                r'(id="q2_fill"[^>]*stroke=")[^"]*(")',
                rf'\1{color_q2}\2',
                result
            )
            
            # Q3 (bottom-left) - Very light neutral for contrast
            color_q3 = self.palette["neutral"][0]
            result = re.sub(
                r'(id="q3_fill"[^>]*fill=")[^"]*(")',
                rf'\1{color_q3}\2',
                result
            )
            result = re.sub(
                r'(id="q3_fill"[^>]*stroke=")[^"]*(")',
                rf'\1{color_q3}\2',
                result
            )
            
            # Q4 (bottom-right) - Darker shade for diagonal contrast with Q1
            color_q4 = self.palette["primary"][4]
            result = re.sub(
                r'(id="q4_fill"[^>]*fill=")[^"]*(")',
                rf'\1{color_q4}\2',
                result
            )
            result = re.sub(
                r'(id="q4_fill"[^>]*stroke=")[^"]*(")',
                rf'\1{color_q4}\2',
                result
            )
        
        # Hub & Spoke specific coloring
        if 'id="hub_fill"' in svg_content:
            # Hub gets the primary base color (darker/prominent)
            hub_color = self.palette["primary"][4]
            result = re.sub(
                r'(id="hub_fill"[^>]*fill=")[^"]*(")',
                rf'\1{hub_color}\2',
                result
            )
            result = re.sub(
                r'(id="hub_fill"[^>]*stroke=")[^"]*(")',
                rf'\1{hub_color}\2',
                result
            )
            
            # Distribute spoke colors evenly, avoiding the hub color
            spoke_colors = [
                self.palette['primary'][1],  # Light
                self.palette['primary'][2],  # Medium light  
                self.palette['primary'][3],  # Medium
                self.palette['primary'][5],  # Dark (skip 4 which is hub)
            ]
            
            for i in range(1, 7):  # Support up to 6 spokes
                spoke_id = f'spoke_{i}_fill'
                if f'id="{spoke_id}"' in svg_content:
                    color_idx = (i - 1) % len(spoke_colors)
                    spoke_color = spoke_colors[color_idx]
                    result = re.sub(
                        rf'(id="{spoke_id}"[^>]*fill=")[^"]*(")',
                        rf'\1{spoke_color}\2',
                        result
                    )
                    result = re.sub(
                        rf'(id="{spoke_id}"[^>]*stroke=")[^"]*(")',
                        rf'\1{spoke_color}\2',
                        result
                    )
        
        return result
    
    def get_theme_dict(self) -> Dict[str, Any]:
        """Get theme as dictionary for API response"""
        return {
            "primary": self.primary,
            "secondary": None,  # No secondary in monochromatic
            "accent": None,  # No accent in monochromatic
            "colorScheme": "monochromatic",
            "primaryShades": self.palette['primary'],
            "secondaryShades": self.palette['secondary'],
            "neutralShades": self.palette['neutral'],
            "colorMap": self.color_map
        }


class SmartColorTheme:
    """Smart color theme generator for SVG diagrams (complementary scheme)"""
    
    def __init__(self, primary_color: str, secondary_color: str = None, accent_color: str = None, color_scheme: str = "complementary"):
        """
        Initialize with 1-3 colors
        
        Args:
            primary_color: Main brand color
            secondary_color: Optional secondary color
            accent_color: Optional accent color
            color_scheme: "monochromatic" or "complementary"
        """
        self.primary = primary_color.lower()
        self.color_scheme = color_scheme.lower()
        
        if self.color_scheme == "monochromatic":
            # For monochromatic, ignore secondary and accent
            self.secondary = None
            self.accent = None
        else:
            # For complementary, use provided or generate
            self.secondary = secondary_color.lower() if secondary_color else None
            self.accent = accent_color.lower() if accent_color else None
        
        # Generate full palette
        self.palette = self._generate_palette()
        
        # Create mapping for all template colors
        self.color_map = self._create_color_map()
    
    def _generate_palette(self) -> Dict[str, List[str]]:
        """Generate complete color palette from provided colors"""
        palette = {}
        
        if self.color_scheme == "monochromatic":
            # For monochromatic, generate various shades of primary
            palette['primary'] = []
            for i in range(7):
                lightness_adjust = 40 - (i * 80 / 6)
                shade = adjust_lightness(self.primary, lightness_adjust)
                palette['primary'].append(shade)
            
            # Muted versions for variety
            palette['secondary'] = []
            for i in range(5):
                lightness_adjust = 30 - (i * 60 / 4)
                desaturated = adjust_saturation(self.primary, -30)
                shade = adjust_lightness(desaturated, lightness_adjust)
                palette['secondary'].append(shade)
            
            # Even more muted for accents
            palette['accent'] = []
            for i in range(3):
                lightness_adjust = 20 - (i * 40 / 2)
                desaturated = adjust_saturation(self.primary, -50)
                shade = adjust_lightness(desaturated, lightness_adjust)
                palette['accent'].append(shade)
        else:
            # For complementary, use multiple colors
            palette['primary'] = generate_shades(self.primary, 5)
            
            # Secondary (use complementary if not provided)
            if self.secondary:
                palette['secondary'] = generate_shades(self.secondary, 5)
            else:
                self.secondary = get_complementary(self.primary)
                palette['secondary'] = generate_shades(self.secondary, 5)
            
            # Accent (use triadic if not provided)
            if self.accent:
                palette['accent'] = generate_shades(self.accent, 3)
            else:
                triadic1, triadic2 = get_triadic(self.primary)
                self.accent = triadic1
                palette['accent'] = generate_shades(self.accent, 3)
        
        # Neutral grays (derived from primary with low saturation)
        gray_base = adjust_saturation(self.primary, -90)
        palette['neutral'] = generate_shades(gray_base, 7)
        
        # Success, warning, error colors (adjusted from base colors)
        palette['success'] = generate_shades(adjust_lightness("#22c55e", 0), 3)
        palette['warning'] = generate_shades(adjust_lightness("#f59e0b", 0), 3)
        palette['error'] = generate_shades(adjust_lightness("#ef4444", 0), 3)
        
        return palette
    
    def _create_color_map(self) -> Dict[str, str]:
        """Map all template colors to theme colors with better distribution"""
        
        # All unique colors found in templates
        template_colors = [
            '#ffffff', '#fafafa', '#f8f8f8', '#f5f5f5', '#f0f0f0',
            '#e5e5e5', '#e0e0e0', '#dbeafe', '#d1fae5', '#dcfce7',
            '#cbd5e1', '#bfdbfe', '#bbf7d0', '#93c5fd', '#86efac',
            '#64748b', '#60a5fa', '#3b82f6', '#22c55e', '#1e293b',
            '#2563eb', '#10b981', '#059669', '#0891b2', '#06b6d4',
            '#0e7490', '#14b8a6', '#0d9488', '#f59e0b', '#d97706',
            '#dc2626', '#b91c1c', '#991b1b', '#7f1d1d', '#fbbf24',
            '#f97316', '#fb923c', '#ef4444', '#f87171', '#fca5a5',
            '#fed7aa', '#fde68a', '#fef3c7', '#eff6ff', '#f0f9ff',
            '#475569', '#334155', '#1f2937', '#111827', '#0f172a',
            '#94a3b8', '#e2e8f0', '#f1f5f9', '#f3f4f6', '#e5e7eb',
            '#d1d5db', '#9ca3af', '#6b7280', '#4b5563', '#374151',
            '#1f2937'
        ]
        
        color_map = {}
        
        # Build extensive color pool for better variety
        all_colors = []
        if self.color_scheme == "complementary":
            # Use all palette colors for maximum variety
            all_colors.extend(self.palette['primary'])
            all_colors.extend(self.palette['secondary'])
            all_colors.extend(self.palette['accent'])
            # Remove duplicates while preserving order
            seen = set()
            all_colors = [c for c in all_colors if not (c in seen or seen.add(c))]
        else:
            # For monochromatic, use primary shades
            all_colors = list(self.palette['primary'])
        
        # Group template colors by characteristics
        color_groups = {
            'white': [],
            'very_light_gray': [],
            'light_gray': [],
            'medium_gray': [],
            'dark_gray': [],
            'very_dark': [],
            'light_color': [],
            'medium_color': [],
            'dark_color': [],
            'vibrant_color': []
        }
        
        for color in template_colors:
            r, g, b = hex_to_rgb(color)
            h, s, l = rgb_to_hsl(r, g, b)
            
            if color == '#ffffff':
                color_groups['white'].append(color)
            elif l > 95 and s < 10:
                color_groups['very_light_gray'].append(color)
            elif l > 85 and s < 20:
                color_groups['light_gray'].append(color)
            elif l > 60 and s < 25:
                color_groups['medium_gray'].append(color)
            elif l > 30 and s < 25:
                color_groups['dark_gray'].append(color)
            elif l < 20:
                color_groups['very_dark'].append(color)
            elif s > 50 and l > 70:
                color_groups['light_color'].append(color)
            elif s > 50 and l > 40:
                color_groups['medium_color'].append(color)
            elif s > 40 and l <= 40:
                color_groups['dark_color'].append(color)
            else:
                color_groups['vibrant_color'].append(color)
        
        # Map colors with variety
        color_indices = {}
        
        # White stays white
        for color in color_groups['white']:
            color_map[color] = '#ffffff'
        
        # Very light grays - use lightest neutrals
        for i, color in enumerate(color_groups['very_light_gray']):
            color_map[color] = self.palette['neutral'][min(i, len(self.palette['neutral'])-1)]
        
        # Light grays
        for i, color in enumerate(color_groups['light_gray']):
            color_map[color] = self.palette['neutral'][min(1 + i % 2, len(self.palette['neutral'])-1)]
        
        # Medium grays
        for i, color in enumerate(color_groups['medium_gray']):
            color_map[color] = self.palette['neutral'][min(2 + i % 2, len(self.palette['neutral'])-1)]
        
        # Dark grays
        for i, color in enumerate(color_groups['dark_gray']):
            color_map[color] = self.palette['neutral'][min(4 + i % 2, len(self.palette['neutral'])-1)]
        
        # Very dark colors
        for i, color in enumerate(color_groups['very_dark']):
            if i < len(all_colors):
                # Use darkest shades from color palette
                color_map[color] = all_colors[-(i+1) % len(all_colors)]
            else:
                color_map[color] = self.palette['neutral'][-1]
        
        # Light colors - distribute across light shades
        for i, color in enumerate(color_groups['light_color']):
            if self.color_scheme == "complementary":
                # Cycle through different palettes
                idx = i % len(all_colors)
                color_map[color] = all_colors[min(idx, len(all_colors)-1)]
            else:
                idx = i % len(self.palette['primary'])
                color_map[color] = self.palette['primary'][idx]
        
        # Medium colors - use middle shades
        for i, color in enumerate(color_groups['medium_color']):
            if self.color_scheme == "complementary":
                # Ensure variety by cycling through available colors
                idx = (i + 2) % len(all_colors)
                color_map[color] = all_colors[idx]
            else:
                idx = min(2 + (i % 2), len(self.palette['primary'])-1)
                color_map[color] = self.palette['primary'][idx]
        
        # Dark colors - use darker shades
        for i, color in enumerate(color_groups['dark_color']):
            if self.color_scheme == "complementary":
                idx = (i + 4) % len(all_colors)
                color_map[color] = all_colors[idx]
            else:
                idx = min(3 + (i % 2), len(self.palette['primary'])-1)
                color_map[color] = self.palette['primary'][idx]
        
        # Vibrant colors - distribute remaining
        for i, color in enumerate(color_groups['vibrant_color']):
            if self.color_scheme == "complementary":
                idx = (i * 3) % len(all_colors)
                color_map[color] = all_colors[idx]
            else:
                idx = (i + 1) % len(self.palette['primary'])
                color_map[color] = self.palette['primary'][idx]
        
        return color_map
    
    def apply_to_svg(self, svg_content: str) -> str:
        """Apply theme colors to SVG content with unique color enforcement"""
        import re
        
        # Apply general color theme
        result = svg_content
        
        # Sort by length to avoid partial replacements
        sorted_colors = sorted(self.color_map.keys(), key=len, reverse=True)
        
        # Apply general theme replacements
        for old_color in sorted_colors:
            if old_color in result:
                new_color = self.color_map[old_color]
                result = result.replace(old_color, new_color)
                result = result.replace(old_color.upper(), new_color.upper())
        
        # Note: Element-specific colors are now applied in SVGAgent._apply_final_element_colors()
        # to ensure they are applied after all other processing
        
        return result
    
    def _apply_element_specific_colors(self, svg_content: str) -> str:
        """Apply specific colors based on element IDs for better distribution"""
        import re
        
        result = svg_content
        
        # Matrix quadrant-specific coloring
        if 'id="q1_fill"' in svg_content and 'id="q4_fill"' in svg_content:
            # Use different palette colors for each quadrant
            colors = [
                self.palette["primary"][1],
                self.palette["secondary"][1],
                self.palette["accent"][0],
                self.palette["primary"][3]
            ]
            
            for i, color in enumerate(colors, 1):
                quad_id = f'q{i}_fill'
                result = re.sub(
                    rf'(id="{quad_id}"[^>]*fill=")[^"]*(")',
                    rf'\1{color}\2',
                    result
                )
                result = re.sub(
                    rf'(id="{quad_id}"[^>]*stroke=")[^"]*(")',
                    rf'\1{color}\2',
                    result
                )
        
        # Hub & Spoke specific coloring
        if 'id="hub_fill"' in svg_content:
            # Hub gets primary color
            hub_color = self.palette["primary"][2]
            result = re.sub(
                r'(id="hub_fill"[^>]*fill=")[^"]*(")',
                rf'\1{hub_color}\2',
                result
            )
            result = re.sub(
                r'(id="hub_fill"[^>]*stroke=")[^"]*(")',
                rf'\1{hub_color}\2',
                result
            )
            
            # Distribute spoke colors across different palettes
            spoke_colors = [
                self.palette['secondary'][1],
                self.palette['accent'][0],
                self.palette['secondary'][2],
                self.palette['primary'][3],
            ]
            
            for i in range(1, 7):
                spoke_id = f'spoke_{i}_fill'
                if f'id="{spoke_id}"' in svg_content:
                    color_idx = (i - 1) % len(spoke_colors)
                    spoke_color = spoke_colors[color_idx]
                    result = re.sub(
                        rf'(id="{spoke_id}"[^>]*fill=")[^"]*(")',
                        rf'\1{spoke_color}\2',
                        result
                    )
                    result = re.sub(
                        rf'(id="{spoke_id}"[^>]*stroke=")[^"]*(")',
                        rf'\1{spoke_color}\2',
                        result
                    )
        
        return result
    
    def get_theme_dict(self) -> Dict[str, str]:
        """Get theme as dictionary for API response"""
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "primaryShades": self.palette['primary'],
            "secondaryShades": self.palette['secondary'],
            "accentShades": self.palette['accent'],
            "neutralShades": self.palette['neutral'],
            "colorMap": self.color_map
        }


def calculate_luminance(hex_color: str) -> float:
    """
    Calculate relative luminance of a color (0.0 = black, 1.0 = white)
    Uses the WCAG formula for relative luminance
    """
    r, g, b = hex_to_rgb(hex_color)
    
    # Convert to 0-1 range
    r, g, b = r/255.0, g/255.0, b/255.0
    
    # Apply gamma correction
    r = r/12.92 if r <= 0.03928 else ((r + 0.055)/1.055) ** 2.4
    g = g/12.92 if g <= 0.03928 else ((g + 0.055)/1.055) ** 2.4
    b = b/12.92 if b <= 0.03928 else ((b + 0.055)/1.055) ** 2.4
    
    # Calculate luminance
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def get_contrast_color(background_color: str, light_color: str = "#ffffff", dark_color: str = "#000000") -> str:
    """
    Get contrasting text color (black or white) based on background luminance
    
    Args:
        background_color: Background color in hex format
        light_color: Color to use on dark backgrounds (default white)
        dark_color: Color to use on light backgrounds (default black)
        
    Returns:
        Either light_color or dark_color based on background luminance
    """
    luminance = calculate_luminance(background_color)
    # Use 0.5 as threshold (can be adjusted for preference)
    return light_color if luminance < 0.5 else dark_color


def is_dark_color(hex_color: str) -> bool:
    """Check if a color is considered dark (luminance < 0.5)"""
    return calculate_luminance(hex_color) < 0.5


def extract_colors_from_svg(svg_content: str) -> List[str]:
    """Extract all color values from SVG content"""
    colors = set()
    
    # Find hex colors
    hex_pattern = r'#[0-9a-fA-F]{6}'
    colors.update(re.findall(hex_pattern, svg_content))
    
    # Find rgb colors
    rgb_pattern = r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)'
    for match in re.finditer(rgb_pattern, svg_content):
        r, g, b = match.groups()
        colors.add(rgb_to_hex(int(r), int(g), int(b)))
    
    return list(colors)


def validate_color_contrast(color1: str, color2: str, min_ratio: float = 1.5) -> bool:
    """
    Validate that two colors have sufficient contrast
    
    Args:
        color1: First color in hex format
        color2: Second color in hex format
        min_ratio: Minimum contrast ratio required (default 1.5)
    
    Returns:
        True if contrast is sufficient, False otherwise
    """
    lum1 = calculate_luminance(color1)
    lum2 = calculate_luminance(color2)
    
    # Calculate contrast ratio
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    # Avoid division by zero
    if darker == 0:
        darker = 0.001
    
    ratio = (lighter + 0.05) / (darker + 0.05)
    return ratio >= min_ratio


def ensure_color_visibility(color: str, background: str = "#ffffff") -> str:
    """
    Ensure a color is visible against a background
    
    Args:
        color: Color to validate/adjust
        background: Background color (default white)
    
    Returns:
        Adjusted color if needed, or original if already visible
    """
    if not validate_color_contrast(color, background, 1.3):
        # Color is too similar to background, adjust it
        r, g, b = hex_to_rgb(color)
        h, s, l = rgb_to_hsl(r, g, b)
        
        # If color is too light, darken it
        if l > 85:
            l = 60
            s = max(30, s)  # Ensure some saturation
        # If color is too dark for dark background
        elif l < 15 and calculate_luminance(background) < 0.5:
            l = 40
            s = max(30, s)
        
        r, g, b = hsl_to_rgb(h, s, l)
        return rgb_to_hex(r, g, b)
    
    return color


def interpolate_color(color1: str, color2: str, factor: float) -> str:
    """
    Interpolate between two colors
    
    Args:
        color1: Start color (hex)
        color2: End color (hex)
        factor: Interpolation factor (0.0 = color1, 1.0 = color2)
    
    Returns:
        Interpolated color (hex)
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    # Linear interpolation in RGB space
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    
    return rgb_to_hex(r, g, b)


def generate_2d_gradient(primary_color: str, width: int = 2, height: int = 2) -> List[List[str]]:
    """
    Generate a 2D color gradient for grid layouts
    
    Args:
        primary_color: Base color
        width: Grid width 
        height: Grid height
    
    Returns:
        2D list of hex colors
    """
    r, g, b = hex_to_rgb(primary_color)
    h, s, l = rgb_to_hsl(r, g, b)
    
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            # X-axis: vary lightness (left to right: light to dark)
            x_factor = x / max(1, width - 1)
            target_lightness = 75 - (x_factor * 40)  # 75% to 35%
            
            # Y-axis: vary saturation (top to bottom: vivid to muted)
            y_factor = y / max(1, height - 1)
            target_saturation = s - (y_factor * 30)  # Full saturation to 30% less
            target_saturation = max(20, target_saturation)
            
            r_new, g_new, b_new = hsl_to_rgb(h, target_saturation, target_lightness)
            row.append(rgb_to_hex(r_new, g_new, b_new))
        grid.append(row)
    
    return grid


def generate_radial_colors(center_color: str, num_spokes: int = 4) -> Dict[str, str]:
    """
    Generate colors for hub & spoke with radial/circular progression
    
    Args:
        center_color: Hub color
        num_spokes: Number of spoke nodes
    
    Returns:
        Dictionary with 'hub' and 'spoke_N' colors
    """
    r, g, b = hex_to_rgb(center_color)
    h, s, l = rgb_to_hsl(r, g, b)
    
    colors = {}
    
    # Hub: darker, more saturated version
    hub_lightness = max(15, l - 30)
    hub_saturation = min(90, s + 20)
    r_hub, g_hub, b_hub = hsl_to_rgb(h, hub_saturation, hub_lightness)
    colors['hub'] = rgb_to_hex(r_hub, g_hub, b_hub)
    
    # Spokes: create variations of the primary color
    # Keep hue close to primary, vary lightness and saturation
    for i in range(num_spokes):
        # Small hue variation (±30 degrees max instead of full rotation)
        hue_shift = (i - num_spokes/2) * (60 / num_spokes)  # ±30 degrees spread
        spoke_hue = (h + hue_shift) % 360
        
        # Vary lightness systematically
        lightness_range = [65, 50, 55, 70]  # Different lightness values
        spoke_lightness = lightness_range[i % len(lightness_range)]
        
        # Vary saturation slightly
        saturation_range = [s, s-10, s+10, s-5]
        spoke_saturation = max(30, min(90, saturation_range[i % len(saturation_range)]))
        
        r_spoke, g_spoke, b_spoke = hsl_to_rgb(spoke_hue, spoke_saturation, spoke_lightness)
        colors[f'spoke_{i+1}'] = rgb_to_hex(r_spoke, g_spoke, b_spoke)
    
    return colors


def blend_colors(color1: str, color2: str, opacity1: float = 0.5, opacity2: float = 0.5) -> str:
    """
    Blend two colors with opacity (for Venn intersection)
    
    Args:
        color1: First color (hex)
        color2: Second color (hex)
        opacity1: Opacity of first color
        opacity2: Opacity of second color
    
    Returns:
        Blended color (hex)
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    # Simulate alpha blending
    r = int((r1 * opacity1 + r2 * opacity2) / (opacity1 + opacity2))
    g = int((g1 * opacity1 + g2 * opacity2) / (opacity1 + opacity2))
    b = int((b1 * opacity1 + b2 * opacity2) / (opacity1 + opacity2))
    
    # Make it darker for intersection
    r = int(r * 0.7)
    g = int(g * 0.7)
    b = int(b * 0.7)
    
    return rgb_to_hex(r, g, b)