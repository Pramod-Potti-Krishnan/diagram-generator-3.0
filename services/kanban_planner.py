"""
KANBAN_BOARD Planning Service v1.0.0

LLM-based Kanban board design from natural language prompts.
This service is responsible for:
- Analyzing natural language prompts describing workflows/processes
- Generating appropriate columns with intuitive names
- Creating sample cards with relevant content
- Selecting appropriate colors for columns

SEPARATION OF CONCERNS:
- Planner (this file): LLM-based board reasoning
- Visualizer (kanban_atomic_service.py): Pure rendering, no LLM

USAGE:
    When request has prompt but no columns:
    1. Planner analyzes prompt and generates board plan
    2. Plan is passed to visualizer for HTML rendering
"""

import logging
import json
import uuid
from typing import List, Optional
from dataclasses import dataclass

from models.atomic_models import (
    KanbanColumn,
    KanbanCard,
)
from utils.gemini_service import get_gemini_service, optimized_generate

logger = logging.getLogger(__name__)


@dataclass
class KanbanPlanRequest:
    """Input for Kanban board planning."""
    prompt: str
    num_columns: Optional[int] = None  # Suggested number of columns (3-5)


@dataclass
class KanbanPlanResult:
    """Output from Kanban board planning."""
    columns: List[KanbanColumn]
    reasoning: Optional[str] = None  # Optional LLM reasoning explanation


class KanbanPlanner:
    """
    LLM-based planner for Kanban boards.

    Transforms natural language descriptions into structured
    Kanban board specifications with columns and cards.
    """

    def __init__(self):
        """Initialize the planner with GeminiService."""
        self._gemini_service = get_gemini_service()
        self._gemini_service.initialize()

    async def plan(self, request: KanbanPlanRequest) -> KanbanPlanResult:
        """
        Generate Kanban board plan from natural language prompt.

        Args:
            request: KanbanPlanRequest with prompt and optional hints

        Returns:
            KanbanPlanResult with columns and cards
        """
        try:
            # Build the planning prompt
            system_prompt = self._build_planning_prompt(request)

            # Debug logging
            logger.info(f"[KANBAN_PLANNER] Calling LLM with prompt length: {len(system_prompt)} chars")
            logger.debug(f"[KANBAN_PLANNER] User prompt: {request.prompt[:200]}...")

            # Use GeminiService
            response_text = await optimized_generate(prompt=system_prompt, model_type='flash')

            # Handle empty response
            if not response_text:
                logger.error("[KANBAN_PLANNER] LLM returned EMPTY response - falling back to prompt-aware board")
                return self._generate_fallback_board(request.prompt)

            logger.info(f"[KANBAN_PLANNER] LLM response length: {len(response_text)} chars")
            response_text = response_text.strip()

            # Clean up response if wrapped in markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"[KANBAN_PLANNER] JSON parse FAILED: {e}")
                return self._generate_fallback_board(request.prompt)

            # Parse columns
            columns = []
            for col_data in data.get("columns", []):
                cards = []
                for card_data in col_data.get("items", col_data.get("cards", [])):
                    cards.append(KanbanCard(
                        title=card_data.get("title", "Task"),
                        priority=card_data.get("priority", ""),
                        assignee=card_data.get("assignee"),
                        status=card_data.get("status", "")
                    ))

                columns.append(KanbanColumn(
                    name=col_data.get("name", "Column"),
                    color=col_data.get("color"),
                    items=cards
                ))

            logger.info(
                f"[KANBAN_PLANNER] Generated plan: "
                f"{len(columns)} columns, {sum(len(c.items) for c in columns)} cards"
            )

            return KanbanPlanResult(
                columns=columns,
                reasoning=data.get("reasoning")
            )

        except Exception as e:
            logger.error(f"[KANBAN_PLANNER] Planning failed: {e}", exc_info=True)
            return self._generate_fallback_board(request.prompt)

    def _build_planning_prompt(self, request: KanbanPlanRequest) -> str:
        """Build the LLM prompt for Kanban board planning."""

        hints = []
        if request.num_columns:
            hints.append(f"- Use exactly {request.num_columns} columns")
        else:
            hints.append("- Use 3-5 columns as appropriate for the workflow")
        hints_text = "\n".join(hints)

        return f"""You are a project management expert designing a Kanban board.

USER REQUEST:
{request.prompt}

ADDITIONAL HINTS:
{hints_text}

Generate a JSON response with:

1. "columns": Array of Kanban columns with:
   - name: column name (max 30 chars, e.g., "To Do", "In Progress", "Done")
   - color: hex color for column header (choose from: #3B82F6 blue, #10B981 green, #F59E0B amber, #8B5CF6 purple, #EF4444 red, #EC4899 pink, #6B7280 gray)
   - items: array of cards with:
     - title: card title (max 100 chars, concise task description)
     - priority: one of "high", "medium", "low", or "" (empty for no priority)
     - assignee: optional 2-letter initials (e.g., "JD", "SK") or null
     - status: one of "green", "amber", "red", or "" (empty for no status indicator)

2. "reasoning": Brief explanation of your board design (1-2 sentences)

KANBAN DESIGN GUIDELINES:
- Column names should reflect workflow stages
- First column is typically work to be started
- Last column is typically completed work
- Middle columns represent work in progress stages
- Include 2-4 realistic sample cards per column
- Distribute cards across columns (don't put all in one)
- Use appropriate priorities and status indicators
- Card titles should be specific and actionable

COMMON WORKFLOW PATTERNS:
- Software: Backlog → In Progress → Review → Done
- Hiring: Applied → Screening → Interview → Offer → Hired
- Support: New → Triaging → In Progress → Resolved
- Content: Ideas → Drafting → Review → Published
- Sales: Lead → Qualified → Proposal → Negotiation → Won

Return ONLY valid JSON, no markdown or explanation outside the JSON structure."""

    def _generate_fallback_board(self, prompt: str) -> KanbanPlanResult:
        """
        Generate a prompt-aware fallback board when LLM is unavailable.

        Uses keyword detection to select appropriate board template.
        """
        prompt_lower = prompt.lower() if prompt else ""

        # Check for specific domain keywords
        if any(kw in prompt_lower for kw in ["sprint", "agile", "scrum", "development", "software", "code", "bug", "feature"]):
            logger.info("[KANBAN_PLANNER] Fallback: Detected SOFTWARE DEVELOPMENT keywords")
            return self._create_software_board()

        elif any(kw in prompt_lower for kw in ["hiring", "recruit", "candidate", "interview", "onboard", "hr"]):
            logger.info("[KANBAN_PLANNER] Fallback: Detected HIRING keywords")
            return self._create_hiring_board()

        elif any(kw in prompt_lower for kw in ["support", "ticket", "issue", "bug", "incident", "customer"]):
            logger.info("[KANBAN_PLANNER] Fallback: Detected SUPPORT keywords")
            return self._create_support_board()

        elif any(kw in prompt_lower for kw in ["content", "blog", "social", "marketing", "campaign", "article"]):
            logger.info("[KANBAN_PLANNER] Fallback: Detected CONTENT keywords")
            return self._create_content_board()

        elif any(kw in prompt_lower for kw in ["sales", "lead", "deal", "pipeline", "crm", "opportunity"]):
            logger.info("[KANBAN_PLANNER] Fallback: Detected SALES keywords")
            return self._create_sales_board()

        else:
            logger.info("[KANBAN_PLANNER] Fallback: Using GENERIC board")
            return self._create_generic_board()

    def _create_software_board(self) -> KanbanPlanResult:
        """Create a software development Kanban board."""
        columns = [
            KanbanColumn(
                name="Backlog",
                color="#6B7280",
                items=[
                    KanbanCard(title="Add user authentication", priority="high", status=""),
                    KanbanCard(title="Improve search performance", priority="medium", status=""),
                    KanbanCard(title="Update dependencies", priority="low", status="")
                ]
            ),
            KanbanColumn(
                name="In Progress",
                color="#3B82F6",
                items=[
                    KanbanCard(title="Implement REST API endpoints", priority="high", assignee="JD", status="green"),
                    KanbanCard(title="Design database schema", priority="medium", assignee="SK", status="amber")
                ]
            ),
            KanbanColumn(
                name="Code Review",
                color="#8B5CF6",
                items=[
                    KanbanCard(title="Fix login page styling", priority="medium", assignee="MK", status="green"),
                    KanbanCard(title="Add unit tests for auth", priority="high", assignee="JD", status="")
                ]
            ),
            KanbanColumn(
                name="Done",
                color="#10B981",
                items=[
                    KanbanCard(title="Set up CI/CD pipeline", priority="high", status="green"),
                    KanbanCard(title="Create project documentation", priority="low", status="")
                ]
            )
        ]

        return KanbanPlanResult(
            columns=columns,
            reasoning="Software development board with Backlog, In Progress, Code Review, and Done stages."
        )

    def _create_hiring_board(self) -> KanbanPlanResult:
        """Create a hiring pipeline Kanban board."""
        columns = [
            KanbanColumn(
                name="Applied",
                color="#6B7280",
                items=[
                    KanbanCard(title="Sarah Chen - Frontend Dev", priority="high", status=""),
                    KanbanCard(title="Mike Brown - Backend Dev", priority="medium", status=""),
                    KanbanCard(title="Lisa Park - Full Stack", priority="medium", status="")
                ]
            ),
            KanbanColumn(
                name="Phone Screen",
                color="#3B82F6",
                items=[
                    KanbanCard(title="James Wilson - DevOps", priority="high", assignee="HR", status="green"),
                    KanbanCard(title="Emma Davis - UX Designer", priority="medium", assignee="HR", status="")
                ]
            ),
            KanbanColumn(
                name="Technical Interview",
                color="#8B5CF6",
                items=[
                    KanbanCard(title="Alex Kim - Senior Dev", priority="high", assignee="TL", status="green"),
                    KanbanCard(title="Ryan Lee - Junior Dev", priority="medium", assignee="TL", status="amber")
                ]
            ),
            KanbanColumn(
                name="Offer",
                color="#F59E0B",
                items=[
                    KanbanCard(title="Chris Taylor - Lead Dev", priority="high", status="green")
                ]
            ),
            KanbanColumn(
                name="Hired",
                color="#10B981",
                items=[
                    KanbanCard(title="Jordan Smith - QA Engineer", priority="", status="green")
                ]
            )
        ]

        return KanbanPlanResult(
            columns=columns,
            reasoning="Hiring pipeline board tracking candidates from application to hire."
        )

    def _create_support_board(self) -> KanbanPlanResult:
        """Create a support ticket Kanban board."""
        columns = [
            KanbanColumn(
                name="New Tickets",
                color="#EF4444",
                items=[
                    KanbanCard(title="Login not working on mobile", priority="high", status="red"),
                    KanbanCard(title="Payment failed - refund request", priority="high", status=""),
                    KanbanCard(title="Feature request: dark mode", priority="low", status="")
                ]
            ),
            KanbanColumn(
                name="Triaging",
                color="#F59E0B",
                items=[
                    KanbanCard(title="Account sync issues", priority="medium", assignee="L1", status="amber"),
                    KanbanCard(title="Slow page load times", priority="medium", assignee="L1", status="")
                ]
            ),
            KanbanColumn(
                name="In Progress",
                color="#3B82F6",
                items=[
                    KanbanCard(title="API rate limit errors", priority="high", assignee="L2", status="green"),
                    KanbanCard(title="Email notifications delayed", priority="medium", assignee="L2", status="green")
                ]
            ),
            KanbanColumn(
                name="Resolved",
                color="#10B981",
                items=[
                    KanbanCard(title="Password reset email fixed", priority="", status="green"),
                    KanbanCard(title="Dashboard crash resolved", priority="", status="green")
                ]
            )
        ]

        return KanbanPlanResult(
            columns=columns,
            reasoning="Support queue board with ticket lifecycle from new to resolved."
        )

    def _create_content_board(self) -> KanbanPlanResult:
        """Create a content pipeline Kanban board."""
        columns = [
            KanbanColumn(
                name="Ideas",
                color="#EC4899",
                items=[
                    KanbanCard(title="AI trends for 2026", priority="high", status=""),
                    KanbanCard(title="Customer success story", priority="medium", status=""),
                    KanbanCard(title="Product tutorial series", priority="medium", status="")
                ]
            ),
            KanbanColumn(
                name="Drafting",
                color="#8B5CF6",
                items=[
                    KanbanCard(title="Q1 market analysis", priority="high", assignee="JW", status="green"),
                    KanbanCard(title="How-to guide: Getting started", priority="medium", assignee="MK", status="amber")
                ]
            ),
            KanbanColumn(
                name="Review",
                color="#F59E0B",
                items=[
                    KanbanCard(title="Benefits of automation", priority="medium", assignee="ED", status="green"),
                    KanbanCard(title="Case study: Enterprise client", priority="high", assignee="JW", status="")
                ]
            ),
            KanbanColumn(
                name="Published",
                color="#10B981",
                items=[
                    KanbanCard(title="2025 year in review", priority="", status="green"),
                    KanbanCard(title="Feature spotlight: Analytics", priority="", status="green")
                ]
            )
        ]

        return KanbanPlanResult(
            columns=columns,
            reasoning="Content pipeline board tracking articles from ideation to publication."
        )

    def _create_sales_board(self) -> KanbanPlanResult:
        """Create a sales pipeline Kanban board."""
        columns = [
            KanbanColumn(
                name="Lead",
                color="#6B7280",
                items=[
                    KanbanCard(title="Acme Corp - Enterprise", priority="high", status=""),
                    KanbanCard(title="StartupXYZ - SMB", priority="medium", status=""),
                    KanbanCard(title="TechGlobal - Mid-Market", priority="medium", status="")
                ]
            ),
            KanbanColumn(
                name="Qualified",
                color="#3B82F6",
                items=[
                    KanbanCard(title="BigRetail Inc - $50K", priority="high", assignee="SR", status="green"),
                    KanbanCard(title="HealthTech Co - $25K", priority="medium", assignee="JM", status="")
                ]
            ),
            KanbanColumn(
                name="Proposal",
                color="#8B5CF6",
                items=[
                    KanbanCard(title="FinanceFirst - $100K", priority="high", assignee="SR", status="green"),
                    KanbanCard(title="EduLearn - $30K", priority="medium", assignee="KL", status="amber")
                ]
            ),
            KanbanColumn(
                name="Won",
                color="#10B981",
                items=[
                    KanbanCard(title="CloudServ - $75K", priority="", status="green"),
                    KanbanCard(title="DataDriven - $45K", priority="", status="green")
                ]
            )
        ]

        return KanbanPlanResult(
            columns=columns,
            reasoning="Sales pipeline board tracking deals from lead generation to close."
        )

    def _create_generic_board(self) -> KanbanPlanResult:
        """Create a generic 3-column Kanban board (default fallback)."""
        columns = [
            KanbanColumn(
                name="To Do",
                color="#6B7280",
                items=[
                    KanbanCard(title="Review project requirements", priority="high", status=""),
                    KanbanCard(title="Schedule team meeting", priority="medium", status=""),
                    KanbanCard(title="Update documentation", priority="low", status="")
                ]
            ),
            KanbanColumn(
                name="In Progress",
                color="#3B82F6",
                items=[
                    KanbanCard(title="Prepare presentation", priority="high", assignee="JD", status="green"),
                    KanbanCard(title="Analyze data reports", priority="medium", assignee="SK", status="amber")
                ]
            ),
            KanbanColumn(
                name="Done",
                color="#10B981",
                items=[
                    KanbanCard(title="Complete initial research", priority="", status="green"),
                    KanbanCard(title="Set up project workspace", priority="", status="")
                ]
            )
        ]

        return KanbanPlanResult(
            columns=columns,
            reasoning="Generic 3-column Kanban board with To Do, In Progress, and Done stages."
        )
