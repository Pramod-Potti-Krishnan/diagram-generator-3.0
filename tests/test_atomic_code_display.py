"""
Tests for Atomic CODE_DISPLAY Endpoint v1.2.0
==============================================

Test suite for the /v1.2/atomic/CODE_DISPLAY endpoint covering:
- Basic code display generation
- Placeholder mode (no LLM required)
- 5 color themes (github_dark, github_light, monokai, solarized_dark, dracula)
- Language normalization
- Grid positioning with position presets
- External margin configuration
- Border radius configuration (v1.2.0)
- Line highlighting
- Header options
- Error handling
- Inline styles (v1.2.0 - for Layout Service compatibility)

Run with: pytest tests/test_atomic_code_display.py -v
"""

import pytest
from httpx import AsyncClient, ASGITransport

# Import the app for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rest_server import app


@pytest.fixture
def async_client():
    """Create async test client."""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


class TestCodeDisplayAtomic:
    """Tests for the atomic CODE_DISPLAY endpoint."""

    @pytest.mark.asyncio
    async def test_basic_code_display_dark(self, async_client):
        """Test basic code display generation with dark theme."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "print('Hello, World!')",
                    "language": "python",
                    "gridWidth": 28,
                    "gridHeight": 12,
                    "variant": "dark"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["component_type"] == "code_display"
            assert data["instance_count"] == 1
            assert data["arrangement"] == "single"
            assert "dark" in data["variants_used"]
            assert data["language"] == "python"
            assert data["line_count"] == 1
            assert "html" in data
            # v1.2.0: Check for inline background color (github_dark)
            assert "#0d1117" in data["html"]

    @pytest.mark.asyncio
    async def test_basic_code_display_light(self, async_client):
        """Test basic code display generation with light theme."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "const x = 42;",
                    "language": "javascript",
                    "gridWidth": 28,
                    "gridHeight": 12,
                    "variant": "light"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "light" in data["variants_used"]
            assert data["language"] == "javascript"
            # v1.2.0: Check for inline background color (github_light)
            assert "#faf9f7" in data["html"]

    @pytest.mark.asyncio
    async def test_placeholder_mode(self, async_client):
        """Test placeholder mode generates sample code."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "",
                    "language": "python",
                    "gridWidth": 28,
                    "gridHeight": 12,
                    "placeholder_mode": True
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["line_count"] > 0
            assert data["character_counts"]["code"] > 0
            # v1.2.0: Check for inline keyword color (github_dark theme)
            assert "#ff7b72" in data["html"]
            # And contains function content
            assert "calculate_total" in data["html"]

    @pytest.mark.asyncio
    async def test_language_normalization(self, async_client):
        """Test language alias normalization."""
        test_cases = [
            ("py", "python"),
            ("js", "javascript"),
            ("ts", "typescript"),
            ("golang", "go"),
            ("sh", "bash"),
        ]

        async with async_client as client:
            for alias, expected in test_cases:
                response = await client.post(
                    "/v1.2/atomic/CODE_DISPLAY",
                    json={
                        "code": "test code",
                        "language": alias,
                        "gridWidth": 28,
                        "gridHeight": 12
                    }
                )

                assert response.status_code == 200
                data = response.json()
                assert data["language"] == expected, f"Expected {expected} for alias {alias}"

    @pytest.mark.asyncio
    async def test_grid_positioning(self, async_client):
        """Test grid position calculation."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "gridWidth": 20,
                    "gridHeight": 10,
                    "start_col": 5,
                    "start_row": 6
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["grid_position"] is not None
            pos = data["grid_position"]
            assert pos["start_col"] == 5
            assert pos["start_row"] == 6
            assert pos["width"] == 20
            assert pos["height"] == 10
            assert pos["grid_row"] == "6/16"
            assert pos["grid_column"] == "5/25"

    @pytest.mark.asyncio
    async def test_styling_options(self, async_client):
        """Test custom styling options."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "gridWidth": 28,
                    "gridHeight": 12,
                    "show_line_numbers": False,
                    "show_copy_button": False,
                    "show_language_badge": False,
                    "font_size": 16
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            # v1.2.0: Check inline styles - no badge should be present
            # When show_language_badge=False, no badge span is generated
            assert "PYTHON" not in data["html"]
            # Copy button element should not be present when show_copy_button=False
            assert "Copy</button>" not in data["html"]
            # Font size should be 16px in inline style
            assert "font-size:16px" in data["html"]

    @pytest.mark.asyncio
    async def test_empty_code_error(self, async_client):
        """Test error when code is empty and not in placeholder mode."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "",
                    "language": "python",
                    "gridWidth": 28,
                    "gridHeight": 12,
                    "placeholder_mode": False
                }
            )

            # Should return 422 validation error
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_character_counts(self, async_client):
        """Test character count tracking."""
        test_code = "def hello():\n    return 'world'"
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": test_code,
                    "language": "python",
                    "gridWidth": 28,
                    "gridHeight": 12
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["character_counts"]["code"] == len(test_code)
            assert data["line_count"] == 2

    @pytest.mark.asyncio
    async def test_metadata_structure(self, async_client):
        """Test metadata is properly structured."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "gridWidth": 28,
                    "gridHeight": 12
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["metadata"] is not None
            meta = data["metadata"]
            assert "generation_time_ms" in meta
            assert "grid_dimensions" in meta
            assert meta["grid_dimensions"]["width"] == 28
            assert meta["grid_dimensions"]["height"] == 12
            assert "pixel_dimensions" in meta
            assert meta["pixel_dimensions"]["width"] == 28 * 60
            assert meta["pixel_dimensions"]["height"] == 12 * 60
            assert meta["version"] == "1.2.0"

    @pytest.mark.asyncio
    async def test_syntax_highlighting(self, async_client):
        """Test syntax highlighting is applied."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "def test():\n    return True",
                    "language": "python",
                    "gridWidth": 28,
                    "gridHeight": 12
                }
            )

            assert response.status_code == 200
            data = response.json()

            # v1.2.0: Check for inline keyword color (github_dark theme)
            assert "#ff7b72" in data["html"]


class TestAtomicHealth:
    """Tests for the atomic health endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client):
        """Test atomic health check endpoint."""
        async with async_client as client:
            response = await client.get("/v1.2/atomic/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert data["service"] == "atomic-components"
            assert "endpoints" in data
            assert "CODE_DISPLAY" in data["endpoints"]
            assert "grid_system" in data

    @pytest.mark.asyncio
    async def test_components_endpoint(self, async_client):
        """Test atomic components listing endpoint."""
        async with async_client as client:
            response = await client.get("/v1.2/atomic/components")

            assert response.status_code == 200
            data = response.json()

            assert "components" in data
            assert len(data["components"]) > 0

            # Find CODE_DISPLAY component
            code_display = None
            for comp in data["components"]:
                if comp["type"] == "CODE_DISPLAY":
                    code_display = comp
                    break

            assert code_display is not None
            assert code_display["component_id"] == "code_display"
            assert code_display["version"] == "1.2.0"
            assert "python" in code_display["supported_languages"]
            assert "github_dark" in code_display["color_themes"]
            assert "monokai" in code_display["color_themes"]
            assert "dracula" in code_display["color_themes"]


class TestLanguageSupport:
    """Tests for different programming language support."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("language,keyword", [
        ("python", "def"),
        ("javascript", "const"),
        ("typescript", "interface"),
        ("go", "func"),
        ("rust", "fn"),
        ("java", "public"),
        ("sql", "SELECT"),
        ("bash", "echo"),
    ])
    async def test_language_placeholder(self, async_client, language, keyword):
        """Test placeholder code contains language-specific keywords."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "",
                    "language": language,
                    "gridWidth": 28,
                    "gridHeight": 12,
                    "placeholder_mode": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            # Language badge should show the language
            assert language.upper() in data["html"]


# =============================================================================
# v1.1.0 Feature Tests
# =============================================================================

class TestPositionPresets:
    """Tests for position preset feature (v1.1.0)."""

    @pytest.mark.asyncio
    async def test_left_half_preset(self, async_client):
        """Test left_half position preset applies correct grid values."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "language": "python",
                    "position_preset": "left_half",
                    "placeholder_mode": True
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["preset_used"] == "left_half"
            assert data["grid_position"]["start_col"] == 2
            assert data["grid_position"]["start_row"] == 4
            assert data["grid_position"]["width"] == 15
            assert data["grid_position"]["height"] == 14

    @pytest.mark.asyncio
    async def test_right_half_preset(self, async_client):
        """Test right_half position preset."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "position_preset": "right_half"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["preset_used"] == "right_half"
            assert data["grid_position"]["start_col"] == 17
            assert data["grid_position"]["width"] == 15

    @pytest.mark.asyncio
    async def test_full_content_preset(self, async_client):
        """Test full_content position preset."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "position_preset": "full_content"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["preset_used"] == "full_content"
            assert data["grid_position"]["width"] == 30
            assert data["grid_position"]["height"] == 14

    @pytest.mark.asyncio
    async def test_preset_with_override(self, async_client):
        """Test that explicit values override preset values."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "position_preset": "left_half",
                    "gridHeight": 10  # Override height
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Width from preset, height overridden
            assert data["grid_position"]["width"] == 15
            assert data["grid_position"]["height"] == 10


class TestColorThemes:
    """Tests for color theme feature (v1.1.0)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("theme", [
        "github_dark",
        "github_light",
        "monokai",
        "solarized_dark",
        "dracula"
    ])
    async def test_color_themes(self, async_client, theme):
        """Test all 5 color themes generate proper CSS."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "print('test')",
                    "language": "python",
                    "color_theme": theme
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["color_theme"] == theme
            # v1.2.0: Theme colors should be in inline styles
            # Check for background colors based on theme
            theme_colors = {
                "github_dark": "#0d1117",
                "github_light": "#faf9f7",
                "monokai": "#272822",
                "solarized_dark": "#002b36",
                "dracula": "#282a36"
            }
            assert theme_colors[theme] in data["html"]

    @pytest.mark.asyncio
    async def test_monokai_theme_colors(self, async_client):
        """Test Monokai theme has correct colors in CSS."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "def test(): pass",
                    "language": "python",
                    "color_theme": "monokai"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Monokai background color
            assert "#272822" in data["html"]
            # Monokai keyword color (pink)
            assert "#f92672" in data["html"]

    @pytest.mark.asyncio
    async def test_variant_maps_to_color_theme(self, async_client):
        """Test variant field maps correctly to color_theme."""
        async with async_client as client:
            # Light variant should use github_light
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "variant": "light"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["color_theme"] == "github_light"


class TestExternalMargin:
    """Tests for external margin feature (v1.1.0)."""

    @pytest.mark.asyncio
    async def test_default_margin(self, async_client):
        """Test default external margin is 10px."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # v1.2.0: Default margin in inline style
            assert "padding:10px" in data["html"]

    @pytest.mark.asyncio
    async def test_custom_margin(self, async_client):
        """Test custom external margin value."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "external_margin": 20
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "padding:20px" in data["html"]

    @pytest.mark.asyncio
    async def test_zero_margin(self, async_client):
        """Test zero margin is allowed."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "external_margin": 0
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "padding:0px" in data["html"]


class TestHeaderOptions:
    """Tests for header options (v1.1.0)."""

    @pytest.mark.asyncio
    async def test_hide_header(self, async_client):
        """Test show_header=False hides entire header."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "show_header": False
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            # v1.2.0: With inline styles, header_bg color shouldn't be present
            # Header background colors for github_dark theme
            assert "#161b22" not in data["html"]

    @pytest.mark.asyncio
    async def test_custom_header_text(self, async_client):
        """Test custom header text."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "header_text": "My Custom Header"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "My Custom Header" in data["html"]
            # Default language badge should not show
            assert "PYTHON" not in data["html"]

    @pytest.mark.asyncio
    async def test_filename_in_header(self, async_client):
        """Test filename displayed in header."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "filename": "app.py"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # v1.2.0: Filename should be present in the HTML
            assert "app.py" in data["html"]
            # Monospace font for filename
            assert "JetBrains Mono" in data["html"]


class TestVerticalScrolling:
    """Tests for vertical scrolling (v1.1.0)."""

    @pytest.mark.asyncio
    async def test_scrolling_css_present(self, async_client):
        """Test scrolling CSS is in generated HTML."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "line1\nline2\nline3",
                    "language": "python"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # v1.2.0: Scroll in inline styles (no spaces)
            assert "overflow-y:auto" in data["html"]
            assert "overflow-x:hidden" in data["html"]


class TestLineHighlighting:
    """Tests for line highlighting (v1.1.0)."""

    @pytest.mark.asyncio
    async def test_highlight_lines(self, async_client):
        """Test line highlighting adds proper spans."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "line1\nline2\nline3",
                    "language": "python",
                    "highlight_lines": [2]
                }
            )

            assert response.status_code == 200
            data = response.json()

            # v1.2.0: Line highlight with inline background color
            # github_dark line highlight color
            assert "rgba(56,139,253,0.15)" in data["html"]


# =============================================================================
# v1.2.0 Feature Tests
# =============================================================================

class TestBorderRadius:
    """Tests for border radius feature (v1.2.0)."""

    @pytest.mark.asyncio
    async def test_default_border_radius(self, async_client):
        """Test default border radius is 12px."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Default border radius should be 12px
            assert "border-radius:12px" in data["html"]

    @pytest.mark.asyncio
    async def test_custom_border_radius(self, async_client):
        """Test custom border radius value."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "border_radius": 8
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "border-radius:8px" in data["html"]

    @pytest.mark.asyncio
    async def test_zero_border_radius(self, async_client):
        """Test zero border radius for square corners."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "border_radius": 0
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "border-radius:0px" in data["html"]

    @pytest.mark.asyncio
    async def test_corner_style_square(self, async_client):
        """Test corner_style='square' sets border_radius to 0."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "corner_style": "square"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "border-radius:0px" in data["html"]

    @pytest.mark.asyncio
    async def test_corner_style_rounded(self, async_client):
        """Test corner_style='rounded' keeps default 12px."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "corner_style": "rounded"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "border-radius:12px" in data["html"]

    @pytest.mark.asyncio
    async def test_explicit_border_radius_overrides_corner_style(self, async_client):
        """Test explicit border_radius overrides corner_style."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "corner_style": "square",
                    "border_radius": 20  # Explicit override
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Explicit value should win
            assert "border-radius:20px" in data["html"]


class TestInlineStyles:
    """Tests for inline styles (v1.2.0)."""

    @pytest.mark.asyncio
    async def test_no_style_tag(self, async_client):
        """Test that HTML doesn't contain <style> tags."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # v1.2.0: No <style> tags, all inline
            assert "<style>" not in data["html"]

    @pytest.mark.asyncio
    async def test_inline_background_color(self, async_client):
        """Test background color is inline in monokai theme."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "color_theme": "monokai"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Monokai background color in inline style
            assert "background:#272822" in data["html"]

    @pytest.mark.asyncio
    async def test_inline_keyword_color(self, async_client):
        """Test keyword highlighting uses inline color."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "def foo(): pass",
                    "language": "python",
                    "color_theme": "dracula"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Dracula keyword color (pink)
            assert "#ff79c6" in data["html"]

    @pytest.mark.asyncio
    async def test_data_code_container_attribute(self, async_client):
        """Test data-code-container attribute for copy button."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "show_copy_button": True
                }
            )

            assert response.status_code == 200
            data = response.json()

            # v1.2.0: data-code-container attribute for copy functionality
            assert "data-code-container" in data["html"]


class TestResponseFields:
    """Tests for new response fields (v1.1.0)."""

    @pytest.mark.asyncio
    async def test_new_response_fields(self, async_client):
        """Test new response fields are present."""
        async with async_client as client:
            response = await client.post(
                "/v1.2/atomic/CODE_DISPLAY",
                json={
                    "code": "test",
                    "language": "python",
                    "color_theme": "dracula",
                    "position_preset": "left_half"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # New v1.1.0 fields
            assert "code_generated" in data
            assert data["code_generated"] is False
            assert "prompt_used" in data
            assert data["prompt_used"] is None
            assert "color_theme" in data
            assert data["color_theme"] == "dracula"
            assert "preset_used" in data
            assert data["preset_used"] == "left_half"
