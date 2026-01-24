"""
Tests for Atomic CODE_DISPLAY Endpoint
=======================================

Test suite for the /v1.2/atomic/CODE_DISPLAY endpoint covering:
- Basic code display generation
- Placeholder mode (no LLM required)
- Light/dark theme variants
- Language normalization
- Grid positioning
- Error handling

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
            assert "theme-dark-mode" in data["html"]

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
            assert "theme-light-mode" in data["html"]

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
            # Placeholder code contains def keyword
            assert "def " in data["html"]

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
            # Badge should not be present
            assert "code-lang-badge" not in data["html"]
            # Copy button should not be present
            assert "code-copy-btn" not in data["html"]
            # Font size should be 16px
            assert "font-size: 16px" in data["html"]

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
            assert meta["version"] == "1.0.0"

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

            # Should have token spans for highlighting
            assert "token keyword" in data["html"]


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
            assert "python" in code_display["supported_languages"]
            assert "dark" in code_display["variants"]
            assert "light" in code_display["variants"]


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
