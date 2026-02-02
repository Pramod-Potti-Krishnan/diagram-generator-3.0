"""
GANTT_CHART Planning Service v1.0.0

LLM-based Gantt chart timeline design from natural language prompts.
This service is responsible for:
- Analyzing natural language prompts describing projects/timelines
- Generating appropriate tasks with realistic durations
- Creating logical dependencies and sequencing
- Assigning appropriate dates based on project context

SEPARATION OF CONCERNS:
- Planner (this file): LLM-based timeline reasoning
- Visualizer (gantt_atomic_service.py): Pure rendering, no LLM

USAGE:
    When request has prompt but no tasks:
    1. Planner analyzes prompt and generates timeline plan
    2. Plan is passed to visualizer for HTML rendering
"""

import logging
import json
import uuid
from typing import List, Optional
from dataclasses import dataclass
from datetime import date, timedelta

from models.gantt_atomic_models import GanttTask
from utils.gemini_service import get_gemini_service, optimized_generate

logger = logging.getLogger(__name__)


@dataclass
class GanttPlanRequest:
    """Input for Gantt chart planning."""
    prompt: str
    num_tasks: Optional[int] = None  # Suggested number of tasks (5-10)
    duration_weeks: Optional[int] = None  # Project duration hint


@dataclass
class GanttPlanResult:
    """Output from Gantt chart planning."""
    tasks: List[GanttTask]
    time_unit: str  # "days", "weeks", or "months"
    reasoning: Optional[str] = None  # Optional LLM reasoning explanation


class GanttPlanner:
    """
    LLM-based planner for Gantt charts.

    Transforms natural language descriptions into structured
    Gantt chart specifications with tasks and dates.
    """

    def __init__(self):
        """Initialize the planner with GeminiService."""
        self._gemini_service = get_gemini_service()
        self._gemini_service.initialize()

    async def plan(self, request: GanttPlanRequest) -> GanttPlanResult:
        """
        Generate Gantt chart plan from natural language prompt.

        Args:
            request: GanttPlanRequest with prompt and optional hints

        Returns:
            GanttPlanResult with tasks and time unit
        """
        try:
            # Build the planning prompt
            system_prompt = self._build_planning_prompt(request)

            # Debug logging
            logger.info(f"[GANTT_PLANNER] Calling LLM with prompt length: {len(system_prompt)} chars")
            logger.debug(f"[GANTT_PLANNER] User prompt: {request.prompt[:200]}...")

            # Use GeminiService
            response_text = await optimized_generate(prompt=system_prompt, model_type='flash')

            # Handle empty response
            if not response_text:
                logger.error("[GANTT_PLANNER] LLM returned EMPTY response - falling back to prompt-aware timeline")
                return self._generate_fallback_timeline(request.prompt)

            logger.info(f"[GANTT_PLANNER] LLM response length: {len(response_text)} chars")
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
                logger.error(f"[GANTT_PLANNER] JSON parse FAILED: {e}")
                return self._generate_fallback_timeline(request.prompt)

            # Parse tasks
            tasks = []
            for i, task_data in enumerate(data.get("tasks", [])):
                task_id = task_data.get("id", f"task_{i+1}")
                tasks.append(GanttTask(
                    id=task_id,
                    name=task_data.get("name", f"Task {i+1}"),
                    start_date=task_data.get("start_date", date.today().isoformat()),
                    end_date=task_data.get("end_date", (date.today() + timedelta(days=7)).isoformat()),
                    progress=task_data.get("progress", 0),
                    status=task_data.get("status", ""),
                    assignee=task_data.get("assignee")
                ))

            time_unit = data.get("time_unit", "weeks")

            logger.info(
                f"[GANTT_PLANNER] Generated plan: "
                f"{len(tasks)} tasks, time_unit={time_unit}"
            )

            return GanttPlanResult(
                tasks=tasks,
                time_unit=time_unit,
                reasoning=data.get("reasoning")
            )

        except Exception as e:
            logger.error(f"[GANTT_PLANNER] Planning failed: {e}", exc_info=True)
            return self._generate_fallback_timeline(request.prompt)

    def _build_planning_prompt(self, request: GanttPlanRequest) -> str:
        """Build the LLM prompt for Gantt chart planning."""

        today = date.today().isoformat()

        hints = []
        if request.num_tasks:
            hints.append(f"- Create approximately {request.num_tasks} tasks")
        else:
            hints.append("- Create 5-10 tasks as appropriate for the project")
        if request.duration_weeks:
            hints.append(f"- Project should span approximately {request.duration_weeks} weeks")
        hints_text = "\n".join(hints)

        return f"""You are a project manager creating a Gantt chart timeline.

USER REQUEST:
{request.prompt}

TODAY'S DATE: {today}

ADDITIONAL HINTS:
{hints_text}

Generate a JSON response with:

1. "tasks": Array of project tasks with:
   - id: unique task ID (e.g., "task_1", "task_2")
   - name: task name (max 50 chars, clear and actionable)
   - start_date: start date in ISO format "YYYY-MM-DD"
   - end_date: end date in ISO format "YYYY-MM-DD"
   - progress: completion percentage (0-100)
   - status: one of "on_track", "at_risk", "blocked", or "" (empty)
   - assignee: optional 2-letter initials (e.g., "JD", "SK") or null

2. "time_unit": recommended view unit - one of "days", "weeks", or "months"

3. "reasoning": Brief explanation of your timeline design (1-2 sentences)

GANTT CHART DESIGN GUIDELINES:
- Tasks should have realistic durations
- Some tasks should overlap (parallel work)
- Some tasks should be sequential (dependencies implied)
- Start from today's date and plan forward
- Use "on_track" for completed or progressing tasks
- Use "at_risk" for tasks that may need attention
- Use "blocked" for tasks with issues
- Progress should reflect realistic status (0% for not started, 100% for complete)

COMMON PROJECT PATTERNS:
- Product Launch: Research → Design → Development → Testing → Marketing → Launch
- Software Project: Planning → Design → Backend → Frontend → Testing → Deployment
- Construction: Permits → Foundation → Framing → Systems → Finishes → Inspection
- Event Planning: Venue → Catering → Marketing → Logistics → Rehearsal → Event
- Marketing Campaign: Strategy → Content → Design → Development → Launch → Analysis

Return ONLY valid JSON, no markdown or explanation outside the JSON structure."""

    def _generate_fallback_timeline(self, prompt: str) -> GanttPlanResult:
        """
        Generate a prompt-aware fallback timeline when LLM is unavailable.

        Uses keyword detection to select appropriate timeline template.
        """
        prompt_lower = prompt.lower() if prompt else ""

        # Check for specific domain keywords
        if any(kw in prompt_lower for kw in ["product", "launch", "release", "saas", "app"]):
            logger.info("[GANTT_PLANNER] Fallback: Detected PRODUCT LAUNCH keywords")
            return self._create_product_launch_timeline()

        elif any(kw in prompt_lower for kw in ["software", "development", "sprint", "code", "api"]):
            logger.info("[GANTT_PLANNER] Fallback: Detected SOFTWARE keywords")
            return self._create_software_timeline()

        elif any(kw in prompt_lower for kw in ["construction", "building", "renovation", "facility"]):
            logger.info("[GANTT_PLANNER] Fallback: Detected CONSTRUCTION keywords")
            return self._create_construction_timeline()

        elif any(kw in prompt_lower for kw in ["event", "conference", "wedding", "party", "meeting"]):
            logger.info("[GANTT_PLANNER] Fallback: Detected EVENT keywords")
            return self._create_event_timeline()

        elif any(kw in prompt_lower for kw in ["marketing", "campaign", "content", "social"]):
            logger.info("[GANTT_PLANNER] Fallback: Detected MARKETING keywords")
            return self._create_marketing_timeline()

        else:
            logger.info("[GANTT_PLANNER] Fallback: Using GENERIC timeline")
            return self._create_generic_timeline()

    def _create_product_launch_timeline(self) -> GanttPlanResult:
        """Create a product launch Gantt chart."""
        today = date.today()
        tasks = [
            GanttTask(
                id="task_1",
                name="Market Research",
                start_date=today.isoformat(),
                end_date=(today + timedelta(weeks=2)).isoformat(),
                progress=100,
                status="on_track",
                assignee="MR"
            ),
            GanttTask(
                id="task_2",
                name="Product Design",
                start_date=(today + timedelta(weeks=1)).isoformat(),
                end_date=(today + timedelta(weeks=4)).isoformat(),
                progress=75,
                status="on_track",
                assignee="PD"
            ),
            GanttTask(
                id="task_3",
                name="Development Sprint 1",
                start_date=(today + timedelta(weeks=3)).isoformat(),
                end_date=(today + timedelta(weeks=6)).isoformat(),
                progress=40,
                status="on_track",
                assignee="DV"
            ),
            GanttTask(
                id="task_4",
                name="Development Sprint 2",
                start_date=(today + timedelta(weeks=6)).isoformat(),
                end_date=(today + timedelta(weeks=9)).isoformat(),
                progress=0,
                status="",
                assignee="DV"
            ),
            GanttTask(
                id="task_5",
                name="QA Testing",
                start_date=(today + timedelta(weeks=8)).isoformat(),
                end_date=(today + timedelta(weeks=10)).isoformat(),
                progress=0,
                status="",
                assignee="QA"
            ),
            GanttTask(
                id="task_6",
                name="Marketing Prep",
                start_date=(today + timedelta(weeks=7)).isoformat(),
                end_date=(today + timedelta(weeks=11)).isoformat(),
                progress=0,
                status="",
                assignee="MK"
            ),
            GanttTask(
                id="task_7",
                name="Beta Launch",
                start_date=(today + timedelta(weeks=10)).isoformat(),
                end_date=(today + timedelta(weeks=11)).isoformat(),
                progress=0,
                status="",
                assignee="PM"
            ),
            GanttTask(
                id="task_8",
                name="Public Launch",
                start_date=(today + timedelta(weeks=12)).isoformat(),
                end_date=(today + timedelta(weeks=12, days=3)).isoformat(),
                progress=0,
                status="",
                assignee="PM"
            )
        ]

        return GanttPlanResult(
            tasks=tasks,
            time_unit="weeks",
            reasoning="Product launch timeline spanning 12 weeks from research to public launch."
        )

    def _create_software_timeline(self) -> GanttPlanResult:
        """Create a software project Gantt chart."""
        today = date.today()
        tasks = [
            GanttTask(
                id="task_1",
                name="Requirements Gathering",
                start_date=today.isoformat(),
                end_date=(today + timedelta(weeks=1)).isoformat(),
                progress=100,
                status="on_track",
                assignee="BA"
            ),
            GanttTask(
                id="task_2",
                name="System Architecture",
                start_date=(today + timedelta(days=5)).isoformat(),
                end_date=(today + timedelta(weeks=2)).isoformat(),
                progress=80,
                status="on_track",
                assignee="AR"
            ),
            GanttTask(
                id="task_3",
                name="Database Design",
                start_date=(today + timedelta(weeks=1, days=3)).isoformat(),
                end_date=(today + timedelta(weeks=3)).isoformat(),
                progress=50,
                status="on_track",
                assignee="DB"
            ),
            GanttTask(
                id="task_4",
                name="API Development",
                start_date=(today + timedelta(weeks=2)).isoformat(),
                end_date=(today + timedelta(weeks=5)).isoformat(),
                progress=25,
                status="on_track",
                assignee="BE"
            ),
            GanttTask(
                id="task_5",
                name="Frontend Development",
                start_date=(today + timedelta(weeks=3)).isoformat(),
                end_date=(today + timedelta(weeks=6)).isoformat(),
                progress=10,
                status="at_risk",
                assignee="FE"
            ),
            GanttTask(
                id="task_6",
                name="Integration Testing",
                start_date=(today + timedelta(weeks=5)).isoformat(),
                end_date=(today + timedelta(weeks=7)).isoformat(),
                progress=0,
                status="",
                assignee="QA"
            ),
            GanttTask(
                id="task_7",
                name="UAT",
                start_date=(today + timedelta(weeks=6, days=3)).isoformat(),
                end_date=(today + timedelta(weeks=8)).isoformat(),
                progress=0,
                status="",
                assignee="QA"
            ),
            GanttTask(
                id="task_8",
                name="Deployment",
                start_date=(today + timedelta(weeks=8)).isoformat(),
                end_date=(today + timedelta(weeks=8, days=2)).isoformat(),
                progress=0,
                status="",
                assignee="DO"
            )
        ]

        return GanttPlanResult(
            tasks=tasks,
            time_unit="weeks",
            reasoning="Software development timeline spanning 8 weeks with parallel tracks."
        )

    def _create_construction_timeline(self) -> GanttPlanResult:
        """Create a construction project Gantt chart."""
        today = date.today()
        tasks = [
            GanttTask(
                id="task_1",
                name="Permits & Approvals",
                start_date=today.isoformat(),
                end_date=(today + timedelta(weeks=4)).isoformat(),
                progress=100,
                status="on_track",
                assignee="PM"
            ),
            GanttTask(
                id="task_2",
                name="Site Preparation",
                start_date=(today + timedelta(weeks=3)).isoformat(),
                end_date=(today + timedelta(weeks=5)).isoformat(),
                progress=60,
                status="on_track",
                assignee="SC"
            ),
            GanttTask(
                id="task_3",
                name="Foundation Work",
                start_date=(today + timedelta(weeks=5)).isoformat(),
                end_date=(today + timedelta(weeks=8)).isoformat(),
                progress=20,
                status="on_track",
                assignee="FC"
            ),
            GanttTask(
                id="task_4",
                name="Framing",
                start_date=(today + timedelta(weeks=8)).isoformat(),
                end_date=(today + timedelta(weeks=12)).isoformat(),
                progress=0,
                status="",
                assignee="FC"
            ),
            GanttTask(
                id="task_5",
                name="Electrical & Plumbing",
                start_date=(today + timedelta(weeks=10)).isoformat(),
                end_date=(today + timedelta(weeks=14)).isoformat(),
                progress=0,
                status="",
                assignee="ME"
            ),
            GanttTask(
                id="task_6",
                name="Interior Finishes",
                start_date=(today + timedelta(weeks=13)).isoformat(),
                end_date=(today + timedelta(weeks=16)).isoformat(),
                progress=0,
                status="",
                assignee="IF"
            )
        ]

        return GanttPlanResult(
            tasks=tasks,
            time_unit="weeks",
            reasoning="Construction project timeline spanning 16 weeks from permits to finishes."
        )

    def _create_event_timeline(self) -> GanttPlanResult:
        """Create an event planning Gantt chart."""
        today = date.today()
        tasks = [
            GanttTask(
                id="task_1",
                name="Venue Selection",
                start_date=today.isoformat(),
                end_date=(today + timedelta(weeks=2)).isoformat(),
                progress=100,
                status="on_track",
                assignee="EP"
            ),
            GanttTask(
                id="task_2",
                name="Vendor Contracts",
                start_date=(today + timedelta(weeks=1)).isoformat(),
                end_date=(today + timedelta(weeks=3)).isoformat(),
                progress=70,
                status="on_track",
                assignee="EP"
            ),
            GanttTask(
                id="task_3",
                name="Marketing & Invites",
                start_date=(today + timedelta(weeks=2)).isoformat(),
                end_date=(today + timedelta(weeks=5)).isoformat(),
                progress=40,
                status="on_track",
                assignee="MK"
            ),
            GanttTask(
                id="task_4",
                name="Catering Finalization",
                start_date=(today + timedelta(weeks=3)).isoformat(),
                end_date=(today + timedelta(weeks=4, days=3)).isoformat(),
                progress=30,
                status="at_risk",
                assignee="EP"
            ),
            GanttTask(
                id="task_5",
                name="AV & Tech Setup",
                start_date=(today + timedelta(weeks=4)).isoformat(),
                end_date=(today + timedelta(weeks=5, days=3)).isoformat(),
                progress=0,
                status="",
                assignee="TC"
            ),
            GanttTask(
                id="task_6",
                name="Rehearsal",
                start_date=(today + timedelta(weeks=5, days=4)).isoformat(),
                end_date=(today + timedelta(weeks=5, days=5)).isoformat(),
                progress=0,
                status="",
                assignee="EP"
            ),
            GanttTask(
                id="task_7",
                name="Event Day",
                start_date=(today + timedelta(weeks=6)).isoformat(),
                end_date=(today + timedelta(weeks=6)).isoformat(),
                progress=0,
                status="",
                assignee="EP"
            )
        ]

        return GanttPlanResult(
            tasks=tasks,
            time_unit="weeks",
            reasoning="Event planning timeline spanning 6 weeks from venue to event day."
        )

    def _create_marketing_timeline(self) -> GanttPlanResult:
        """Create a marketing campaign Gantt chart."""
        today = date.today()
        tasks = [
            GanttTask(
                id="task_1",
                name="Campaign Strategy",
                start_date=today.isoformat(),
                end_date=(today + timedelta(weeks=1)).isoformat(),
                progress=100,
                status="on_track",
                assignee="SM"
            ),
            GanttTask(
                id="task_2",
                name="Content Creation",
                start_date=(today + timedelta(days=5)).isoformat(),
                end_date=(today + timedelta(weeks=3)).isoformat(),
                progress=60,
                status="on_track",
                assignee="CW"
            ),
            GanttTask(
                id="task_3",
                name="Design Assets",
                start_date=(today + timedelta(weeks=1)).isoformat(),
                end_date=(today + timedelta(weeks=3)).isoformat(),
                progress=45,
                status="on_track",
                assignee="DS"
            ),
            GanttTask(
                id="task_4",
                name="Landing Page Dev",
                start_date=(today + timedelta(weeks=2)).isoformat(),
                end_date=(today + timedelta(weeks=4)).isoformat(),
                progress=20,
                status="at_risk",
                assignee="WD"
            ),
            GanttTask(
                id="task_5",
                name="Email Sequences",
                start_date=(today + timedelta(weeks=2, days=3)).isoformat(),
                end_date=(today + timedelta(weeks=4)).isoformat(),
                progress=10,
                status="",
                assignee="EM"
            ),
            GanttTask(
                id="task_6",
                name="Campaign Launch",
                start_date=(today + timedelta(weeks=4)).isoformat(),
                end_date=(today + timedelta(weeks=4, days=2)).isoformat(),
                progress=0,
                status="",
                assignee="SM"
            ),
            GanttTask(
                id="task_7",
                name="Performance Analysis",
                start_date=(today + timedelta(weeks=5)).isoformat(),
                end_date=(today + timedelta(weeks=6)).isoformat(),
                progress=0,
                status="",
                assignee="AN"
            )
        ]

        return GanttPlanResult(
            tasks=tasks,
            time_unit="weeks",
            reasoning="Marketing campaign timeline spanning 6 weeks from strategy to analysis."
        )

    def _create_generic_timeline(self) -> GanttPlanResult:
        """Create a generic project Gantt chart (default fallback)."""
        today = date.today()
        tasks = [
            GanttTask(
                id="task_1",
                name="Project Planning",
                start_date=today.isoformat(),
                end_date=(today + timedelta(weeks=1)).isoformat(),
                progress=100,
                status="on_track",
                assignee="PM"
            ),
            GanttTask(
                id="task_2",
                name="Research & Analysis",
                start_date=(today + timedelta(days=4)).isoformat(),
                end_date=(today + timedelta(weeks=2)).isoformat(),
                progress=70,
                status="on_track",
                assignee="AN"
            ),
            GanttTask(
                id="task_3",
                name="Phase 1 Execution",
                start_date=(today + timedelta(weeks=1, days=3)).isoformat(),
                end_date=(today + timedelta(weeks=3)).isoformat(),
                progress=30,
                status="on_track",
                assignee="TM"
            ),
            GanttTask(
                id="task_4",
                name="Phase 2 Execution",
                start_date=(today + timedelta(weeks=3)).isoformat(),
                end_date=(today + timedelta(weeks=4, days=3)).isoformat(),
                progress=0,
                status="",
                assignee="TM"
            ),
            GanttTask(
                id="task_5",
                name="Review & Finalize",
                start_date=(today + timedelta(weeks=4)).isoformat(),
                end_date=(today + timedelta(weeks=5)).isoformat(),
                progress=0,
                status="",
                assignee="PM"
            )
        ]

        return GanttPlanResult(
            tasks=tasks,
            time_unit="weeks",
            reasoning="Generic project timeline spanning 5 weeks with planning, execution, and review phases."
        )
