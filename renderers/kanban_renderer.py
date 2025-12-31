"""
Kanban Renderer

Renders Kanban boards using custom HTML/Tailwind CSS.
Uses Playwright to screenshot the rendered HTML.

C5 Layout Only - Full-width slide diagrams.
"""

from typing import Dict, Any, Optional, List
import logging

from .playwright_renderer import PlaywrightRenderer

logger = logging.getLogger(__name__)


class KanbanRenderer(PlaywrightRenderer):
    """
    Renders Kanban boards using HTML/Tailwind + Playwright.

    Custom implementation without external Kanban libraries.
    """

    PRIORITY_COLORS = {
        "high": "#EF4444",
        "medium": "#F59E0B",
        "low": "#10B981",
        "": "#9CA3AF"
    }

    DEFAULT_COLUMN_COLORS = [
        "#F3F4F6",  # Gray
        "#DBEAFE",  # Blue
        "#FEF3C7",  # Yellow
        "#D1FAE5",  # Green
        "#FCE7F3",  # Pink
        "#E0E7FF"   # Indigo
    ]

    def __init__(self):
        super().__init__()

    def get_supported_types(self) -> list:
        return ["kanban"]

    async def render(
        self,
        data: Dict[str, Any],
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Render Kanban board to PNG (legacy method)."""
        theme = self.merge_theme(theme)

        columns = data.get("columns", [])
        if not columns or len(columns) < 2:
            raise ValueError("Kanban board requires at least 2 columns")

        title = data.get("title", "")
        html = self._build_html(columns, title, theme, interactive=False)

        return await self._render_html_to_png(
            html=html,
            width=width,
            height=height,
            extra_wait_ms=500  # Wait for Tailwind to process
        )

    def render_interactive_html(
        self,
        data: Dict[str, Any],
        theme: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render Kanban board as interactive HTML with drag-and-drop."""
        theme = self.merge_theme(theme)

        columns = data.get("columns", [])
        if not columns or len(columns) < 2:
            raise ValueError("Kanban board requires at least 2 columns")

        title = data.get("title", "")
        return self._build_html(columns, title, theme, interactive=True)

    def _build_html(
        self,
        columns: List[dict],
        title: str,
        theme: dict,
        interactive: bool = False
    ) -> str:
        """Build the complete HTML for Kanban board."""

        primary_color = theme.get("primary_color", "#8B5CF6")
        background = theme.get("background_color", "#FFFFFF")
        text_color = theme.get("text_color", "#1F2937")

        columns_html = self._build_columns(columns, primary_color, text_color, interactive)

        # Add interactive JavaScript for drag-and-drop
        interactive_js = ""
        interactive_css = ""
        if interactive:
            interactive_css = """
        .kanban-card {
            cursor: grab;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            user-select: none;
        }
        .kanban-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .kanban-card.dragging {
            opacity: 0.5;
            cursor: grabbing;
        }
        .kanban-cards.drag-over {
            background: rgba(59, 130, 246, 0.15) !important;
            outline: 2px dashed #3B82F6;
            outline-offset: -2px;
        }
        .kanban-card-edit {
            display: none;
            position: absolute;
            top: 4px;
            right: 4px;
        }
        .kanban-card:hover .kanban-card-edit {
            display: block;
        }
        .add-card-btn {
            transition: all 0.15s ease;
        }
        .add-card-btn:hover {
            background: rgba(0,0,0,0.05);
        }
"""
            interactive_js = """
    <script>
        // Kanban Drag and Drop
        let draggedCard = null;

        document.addEventListener('DOMContentLoaded', () => {
            initDragAndDrop();
        });

        function initDragAndDrop() {
            const cards = document.querySelectorAll('.kanban-card');
            const cardContainers = document.querySelectorAll('.kanban-cards');

            cards.forEach(card => {
                card.setAttribute('draggable', 'true');

                card.addEventListener('dragstart', (e) => {
                    draggedCard = card;
                    card.classList.add('dragging');
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/plain', ''); // Required for Firefox
                });

                card.addEventListener('dragend', () => {
                    card.classList.remove('dragging');
                    cardContainers.forEach(container => container.classList.remove('drag-over'));
                    draggedCard = null;
                });
            });

            cardContainers.forEach(container => {
                container.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    e.dataTransfer.dropEffect = 'move';
                    container.classList.add('drag-over');
                });

                container.addEventListener('dragleave', (e) => {
                    // Only remove if leaving the container entirely
                    if (!container.contains(e.relatedTarget)) {
                        container.classList.remove('drag-over');
                    }
                });

                container.addEventListener('drop', (e) => {
                    e.preventDefault();
                    container.classList.remove('drag-over');
                    if (draggedCard) {
                        const cardsDiv = container.querySelector('.space-y-2') || container;
                        cardsDiv.appendChild(draggedCard);
                        updateColumnCounts();
                    }
                });
            });
        }

        function updateColumnCounts() {
            document.querySelectorAll('.kanban-column').forEach(col => {
                const count = col.querySelectorAll('.kanban-card').length;
                const countEl = col.querySelector('.kanban-count');
                if (countEl) countEl.textContent = count;
            });
        }

        function editCard(btn, e) {
            if (e) e.stopPropagation();
            const card = btn.closest('.kanban-card');
            const titleEl = card.querySelector('.kanban-title');
            const currentText = titleEl.textContent;
            const newText = prompt('Edit card:', currentText);
            if (newText && newText.trim()) {
                titleEl.textContent = newText.trim();
            }
        }

        function addCard(btn) {
            const column = btn.closest('.kanban-column');
            const cardsContainer = column.querySelector('.space-y-2');
            const newTitle = prompt('Enter card title:');
            if (newTitle && newTitle.trim()) {
                const cardHtml = `
                    <div class="kanban-card bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden relative" draggable="true">
                        <div class="flex">
                            <div class="priority-bar" style="background: #9CA3AF"></div>
                            <div class="flex-1 p-3">
                                <p class="kanban-title text-sm font-medium" style="color: #1F2937">${newTitle.trim()}</p>
                            </div>
                            <button onclick="editCard(this, event)" class="kanban-card-edit p-1 rounded hover:bg-gray-100">
                                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                `;
                cardsContainer.insertAdjacentHTML('beforeend', cardHtml);
                // Re-init drag for new card
                const newCard = cardsContainer.lastElementChild;
                newCard.addEventListener('dragstart', (e) => {
                    draggedCard = newCard;
                    newCard.classList.add('dragging');
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/plain', '');
                });
                newCard.addEventListener('dragend', () => {
                    newCard.classList.remove('dragging');
                    document.querySelectorAll('.kanban-cards').forEach(c => c.classList.remove('drag-over'));
                    draggedCard = null;
                });
                updateColumnCounts();
            }
        }
    </script>
"""

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        * {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }}
        body {{
            background: {background};
            margin: 0;
        }}
        .priority-bar {{
            width: 4px;
            border-radius: 2px;
        }}
        {interactive_css}
    </style>
</head>
<body class="antialiased">
    <div class="flex gap-4 overflow-x-auto w-full" style="padding: 40px 16px 30px 16px;">
        {columns_html}
    </div>
    {interactive_js}
</body>
</html>
"""

    def _build_columns(
        self,
        columns: List[dict],
        primary_color: str,
        text_color: str,
        interactive: bool = False
    ) -> str:
        """Build HTML for all columns."""
        html_parts = []
        num_columns = len(columns)
        # Calculate column width to fill container evenly
        col_width_class = "flex-1 min-w-[200px]" if interactive else "flex-shrink-0 w-64"

        for i, column in enumerate(columns):
            name = column.get("name", f"Column {i+1}")
            color = column.get("color", self.DEFAULT_COLUMN_COLORS[i % len(self.DEFAULT_COLUMN_COLORS)])
            items = column.get("items", [])

            cards_html = self._build_cards(items, primary_color, text_color, interactive)

            # Add card button for interactive mode
            add_card_btn = ""
            if interactive:
                add_card_btn = f"""
        <button onclick="addCard(this)" class="add-card-btn w-full mt-2 p-2 rounded-lg border-2 border-dashed border-gray-300 text-gray-400 text-sm font-medium flex items-center justify-center gap-1 hover:border-gray-400 hover:text-gray-500">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Add Card
        </button>
"""

            html_parts.append(f"""
<div class="{col_width_class} kanban-column" data-column="{i}">
    <div class="flex items-center justify-between mb-3 px-1">
        <span class="text-sm font-semibold uppercase tracking-wide" style="color: {text_color}">{name}</span>
        <span class="kanban-count text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">{len(items)}</span>
    </div>
    <div class="rounded-xl p-2 kanban-cards" style="background: {color}; min-height: 280px;">
        <div class="space-y-2">
            {cards_html}
        </div>
        {add_card_btn}
    </div>
</div>
""")

        return "\n".join(html_parts)

    def _build_cards(
        self,
        items: List[dict],
        primary_color: str,
        text_color: str,
        interactive: bool = False
    ) -> str:
        """Build HTML for cards in a column."""
        if not items:
            return '<div class="text-center text-gray-400 text-sm py-4">No items</div>'

        html_parts = []

        for i, item in enumerate(items):
            title = item.get("title", "Untitled")
            priority = item.get("priority", "").lower()
            assignee = item.get("assignee", "")

            priority_color = self.PRIORITY_COLORS.get(priority, self.PRIORITY_COLORS[""])

            assignee_html = ""
            if assignee:
                initials = assignee[:2].upper()
                assignee_html = f"""
<div class="mt-2">
    <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium text-white"
         style="background: {primary_color}">{initials}</div>
</div>
"""

            # Add edit button for interactive mode
            edit_btn = ""
            if interactive:
                edit_btn = """
<button onclick="editCard(this, event)" class="kanban-card-edit p-1 rounded hover:bg-gray-100">
    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>
    </svg>
</button>
"""

            html_parts.append(f"""
<div class="kanban-card bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden relative" data-card="{i}">
    <div class="flex">
        <div class="priority-bar" style="background: {priority_color}"></div>
        <div class="flex-1 p-3">
            <p class="kanban-title text-sm font-medium" style="color: {text_color}">{title}</p>
            {assignee_html}
        </div>
        {edit_btn}
    </div>
</div>
""")

        return "\n".join(html_parts)
