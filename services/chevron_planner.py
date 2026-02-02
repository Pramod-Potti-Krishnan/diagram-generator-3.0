"""
CHEVRON_MATURITY Planning Service v1.0.0

LLM-based maturity model design from natural language prompts.
This service is responsible for:
- Analyzing natural language prompts describing capability/maturity assessments
- Generating appropriate rows (work streams, domains, capabilities)
- Creating chevron progression content with relevant bullet points
- Selecting appropriate stage labels and time units

SEPARATION OF CONCERNS:
- Planner (this file): LLM-based maturity model reasoning
- Visualizer (chevron_atomic_service.py): Pure rendering, no LLM

USAGE:
    When request has prompt but no rows:
    1. Planner analyzes prompt and generates maturity model plan
    2. Plan is passed to visualizer for HTML rendering
"""

import logging
import json
import uuid
from typing import List, Optional
from dataclasses import dataclass

from models.chevron_atomic_models import (
    MaturityRow,
    ChevronContent,
)
from utils.gemini_service import get_gemini_service, optimized_generate

logger = logging.getLogger(__name__)


@dataclass
class ChevronPlanRequest:
    """Input for chevron maturity planning."""
    prompt: str
    num_rows: Optional[int] = None  # Suggested number of rows (3-6)
    num_stages: Optional[int] = None  # Suggested number of stages (3-6)


@dataclass
class ChevronPlanResult:
    """Output from chevron maturity planning."""
    rows: List[MaturityRow]
    stage_labels: List[str]
    time_unit: str  # "quarters", "months", "years", or "stages"
    row_terminology: str  # "Domains", "Work Streams", "Capabilities", etc.
    reasoning: Optional[str] = None  # Optional LLM reasoning explanation


class ChevronPlanner:
    """
    LLM-based planner for chevron maturity charts.

    Transforms natural language descriptions into structured
    maturity model specifications with rows, stages, and content.
    """

    def __init__(self):
        """Initialize the planner with GeminiService."""
        self._gemini_service = get_gemini_service()
        self._gemini_service.initialize()

    async def plan(self, request: ChevronPlanRequest) -> ChevronPlanResult:
        """
        Generate chevron maturity plan from natural language prompt.

        Args:
            request: ChevronPlanRequest with prompt and optional hints

        Returns:
            ChevronPlanResult with rows, stages, and content
        """
        try:
            # Build the planning prompt
            system_prompt = self._build_planning_prompt(request)

            # Debug logging
            logger.info(f"[CHEVRON_PLANNER] Calling LLM with prompt length: {len(system_prompt)} chars")
            logger.debug(f"[CHEVRON_PLANNER] User prompt: {request.prompt[:200]}...")

            # Use GeminiService
            response_text = await optimized_generate(prompt=system_prompt, model_type='flash')

            # Handle empty response
            if not response_text:
                logger.error("[CHEVRON_PLANNER] LLM returned EMPTY response - falling back to prompt-aware maturity model")
                return self._generate_fallback_maturity(request.prompt)

            logger.info(f"[CHEVRON_PLANNER] LLM response length: {len(response_text)} chars")
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
                logger.error(f"[CHEVRON_PLANNER] JSON parse FAILED: {e}")
                return self._generate_fallback_maturity(request.prompt)

            # Parse rows
            rows = []
            for i, row_data in enumerate(data.get("rows", [])):
                row_id = row_data.get("id", f"row_{i+1}")
                chevrons = []
                for chev_data in row_data.get("chevrons", []):
                    chevrons.append(ChevronContent(
                        bullets=chev_data.get("bullets", []),
                        left_pct=chev_data.get("left_pct"),
                        width_pct=chev_data.get("width_pct")
                    ))

                rows.append(MaturityRow(
                    id=row_id,
                    label=row_data.get("label", f"Row {i+1}"),
                    chevrons=chevrons
                ))

            stage_labels = data.get("stage_labels", ["Initial", "Developing", "Defined", "Managed", "Optimized"])
            time_unit = data.get("time_unit", "stages")
            row_terminology = data.get("row_terminology", "Capabilities")

            logger.info(
                f"[CHEVRON_PLANNER] Generated plan: "
                f"{len(rows)} rows, {len(stage_labels)} stages"
            )

            return ChevronPlanResult(
                rows=rows,
                stage_labels=stage_labels,
                time_unit=time_unit,
                row_terminology=row_terminology,
                reasoning=data.get("reasoning")
            )

        except Exception as e:
            logger.error(f"[CHEVRON_PLANNER] Planning failed: {e}", exc_info=True)
            return self._generate_fallback_maturity(request.prompt)

    def _build_planning_prompt(self, request: ChevronPlanRequest) -> str:
        """Build the LLM prompt for chevron maturity planning."""

        hints = []
        if request.num_rows:
            hints.append(f"- Create exactly {request.num_rows} rows/capabilities")
        else:
            hints.append("- Create 3-6 rows as appropriate for the assessment")
        if request.num_stages:
            hints.append(f"- Use exactly {request.num_stages} maturity stages")
        else:
            hints.append("- Use 4-5 maturity stages (typical)")
        hints_text = "\n".join(hints)

        return f"""You are a maturity assessment expert designing a chevron maturity progression chart.

USER REQUEST:
{request.prompt}

ADDITIONAL HINTS:
{hints_text}

Generate a JSON response with:

1. "rows": Array of capability/domain rows with:
   - id: unique row ID (e.g., "row_1", "row_2")
   - label: row name (max 50 chars, e.g., "Data Management", "Process Automation")
   - chevrons: array of maturity stage content with:
     - bullets: array of 1-3 bullet points (each max 100 chars) describing the capability at that stage
     - left_pct: optional left position percentage (0-100), defaults to even distribution
     - width_pct: optional width percentage (5-100), defaults to even distribution

2. "stage_labels": Array of maturity stage names (e.g., ["Initial", "Developing", "Defined", "Managed", "Optimized"])

3. "time_unit": header display preference - one of "quarters", "months", "years", or "stages"

4. "row_terminology": what rows represent - e.g., "Capabilities", "Domains", "Work Streams", "Functions"

5. "reasoning": Brief explanation of your maturity model design (1-2 sentences)

MATURITY MODEL DESIGN GUIDELINES:
- Each row represents a capability dimension being assessed
- Stages progress from low maturity (left) to high maturity (right)
- Bullet points should describe concrete characteristics at each level
- Earlier stages (left) = reactive, ad-hoc, manual
- Later stages (right) = proactive, optimized, automated
- Keep bullets concise but meaningful

COMMON MATURITY PATTERNS:
- DevOps: CI/CD, Infrastructure as Code, Monitoring, Security, Deployment
- Data: Collection, Storage, Processing, Analytics, AI/ML
- Security: Access Control, Data Protection, Network Security, Compliance
- Agile: Planning, Delivery, Feedback, Culture, Continuous Improvement
- Cloud: Migration, Optimization, Governance, Innovation, Cost Management
- Digital: Customer Experience, Operations, Technology, Culture

EXAMPLE STAGE PROGRESSIONS:
- CMMI Style: ["Initial", "Developing", "Defined", "Managed", "Optimizing"]
- Custom: ["Ad-hoc", "Repeatable", "Standardized", "Measured", "Optimized"]
- Simple: ["Basic", "Intermediate", "Advanced", "Expert"]

Return ONLY valid JSON, no markdown or explanation outside the JSON structure."""

    def _generate_fallback_maturity(self, prompt: str) -> ChevronPlanResult:
        """
        Generate a prompt-aware fallback maturity model when LLM is unavailable.

        Uses keyword detection to select appropriate maturity template.
        """
        prompt_lower = prompt.lower() if prompt else ""

        # Check for specific domain keywords
        if any(kw in prompt_lower for kw in ["devops", "ci/cd", "cicd", "deployment", "infrastructure"]):
            logger.info("[CHEVRON_PLANNER] Fallback: Detected DEVOPS keywords")
            return self._create_devops_maturity()

        elif any(kw in prompt_lower for kw in ["security", "compliance", "risk", "cyber", "infosec"]):
            logger.info("[CHEVRON_PLANNER] Fallback: Detected SECURITY keywords")
            return self._create_security_maturity()

        elif any(kw in prompt_lower for kw in ["data", "analytics", "ml", "ai", "machine learning"]):
            logger.info("[CHEVRON_PLANNER] Fallback: Detected DATA keywords")
            return self._create_data_maturity()

        elif any(kw in prompt_lower for kw in ["agile", "scrum", "team", "delivery", "sprint"]):
            logger.info("[CHEVRON_PLANNER] Fallback: Detected AGILE keywords")
            return self._create_agile_maturity()

        elif any(kw in prompt_lower for kw in ["cloud", "aws", "azure", "gcp", "migration"]):
            logger.info("[CHEVRON_PLANNER] Fallback: Detected CLOUD keywords")
            return self._create_cloud_maturity()

        elif any(kw in prompt_lower for kw in ["digital", "transformation", "customer", "experience"]):
            logger.info("[CHEVRON_PLANNER] Fallback: Detected DIGITAL keywords")
            return self._create_digital_maturity()

        else:
            logger.info("[CHEVRON_PLANNER] Fallback: Using GENERIC maturity model")
            return self._create_generic_maturity()

    def _create_devops_maturity(self) -> ChevronPlanResult:
        """Create a DevOps maturity model."""
        stage_labels = ["Initial", "Developing", "Defined", "Managed", "Optimizing"]
        rows = [
            MaturityRow(
                id="row_1",
                label="CI/CD Pipeline",
                chevrons=[
                    ChevronContent(bullets=["Manual builds", "No automation"]),
                    ChevronContent(bullets=["Basic CI setup", "Nightly builds"]),
                    ChevronContent(bullets=["Full CI/CD", "Automated tests"]),
                    ChevronContent(bullets=["Multi-env deploys", "Feature flags"]),
                    ChevronContent(bullets=["Progressive delivery", "Canary releases"])
                ]
            ),
            MaturityRow(
                id="row_2",
                label="Infrastructure",
                chevrons=[
                    ChevronContent(bullets=["Manual provisioning", "Click-ops"]),
                    ChevronContent(bullets=["Basic scripts", "Some automation"]),
                    ChevronContent(bullets=["IaC adoption", "Version control"]),
                    ChevronContent(bullets=["Immutable infra", "GitOps"]),
                    ChevronContent(bullets=["Self-service", "Policy as code"])
                ]
            ),
            MaturityRow(
                id="row_3",
                label="Monitoring",
                chevrons=[
                    ChevronContent(bullets=["Reactive alerts", "Basic logs"]),
                    ChevronContent(bullets=["Centralized logs", "Basic metrics"]),
                    ChevronContent(bullets=["APM tools", "Dashboards"]),
                    ChevronContent(bullets=["Distributed tracing", "SLOs"]),
                    ChevronContent(bullets=["AIOps", "Predictive alerts"])
                ]
            ),
            MaturityRow(
                id="row_4",
                label="Security",
                chevrons=[
                    ChevronContent(bullets=["Ad-hoc scans", "Manual reviews"]),
                    ChevronContent(bullets=["SAST in pipeline", "Dependency checks"]),
                    ChevronContent(bullets=["DAST integrated", "Secret scanning"]),
                    ChevronContent(bullets=["Security gates", "Container scanning"]),
                    ChevronContent(bullets=["DevSecOps culture", "Shift-left security"])
                ]
            ),
            MaturityRow(
                id="row_5",
                label="Culture",
                chevrons=[
                    ChevronContent(bullets=["Siloed teams", "Blame culture"]),
                    ChevronContent(bullets=["Cross-team comms", "Shared goals"]),
                    ChevronContent(bullets=["Blameless postmortems", "Shared ownership"]),
                    ChevronContent(bullets=["SRE practices", "Error budgets"]),
                    ChevronContent(bullets=["Continuous learning", "Innovation time"])
                ]
            )
        ]

        return ChevronPlanResult(
            rows=rows,
            stage_labels=stage_labels,
            time_unit="stages",
            row_terminology="Capabilities",
            reasoning="DevOps maturity model covering CI/CD, Infrastructure, Monitoring, Security, and Culture."
        )

    def _create_security_maturity(self) -> ChevronPlanResult:
        """Create a security maturity model."""
        stage_labels = ["Ad-hoc", "Repeatable", "Defined", "Managed", "Optimized"]
        rows = [
            MaturityRow(
                id="row_1",
                label="Access Control",
                chevrons=[
                    ChevronContent(bullets=["Shared accounts", "No MFA"]),
                    ChevronContent(bullets=["Individual accounts", "Basic MFA"]),
                    ChevronContent(bullets=["RBAC implemented", "SSO"]),
                    ChevronContent(bullets=["Zero trust model", "PAM"]),
                    ChevronContent(bullets=["Adaptive auth", "Continuous verification"])
                ]
            ),
            MaturityRow(
                id="row_2",
                label="Data Protection",
                chevrons=[
                    ChevronContent(bullets=["No classification", "Unencrypted"]),
                    ChevronContent(bullets=["Basic classification", "Encryption at rest"]),
                    ChevronContent(bullets=["DLP tools", "Key management"]),
                    ChevronContent(bullets=["Full data lifecycle", "Tokenization"]),
                    ChevronContent(bullets=["Privacy by design", "Automated compliance"])
                ]
            ),
            MaturityRow(
                id="row_3",
                label="Threat Detection",
                chevrons=[
                    ChevronContent(bullets=["Reactive response", "Basic AV"]),
                    ChevronContent(bullets=["SIEM deployed", "Alert rules"]),
                    ChevronContent(bullets=["24/7 SOC", "Threat intel"]),
                    ChevronContent(bullets=["Automated response", "SOAR"]),
                    ChevronContent(bullets=["ML detection", "Threat hunting"])
                ]
            ),
            MaturityRow(
                id="row_4",
                label="Compliance",
                chevrons=[
                    ChevronContent(bullets=["Manual audits", "Reactive"]),
                    ChevronContent(bullets=["Documented controls", "Annual audits"]),
                    ChevronContent(bullets=["Control monitoring", "Gap analysis"]),
                    ChevronContent(bullets=["Continuous compliance", "Automated evidence"]),
                    ChevronContent(bullets=["Risk-based approach", "Predictive compliance"])
                ]
            )
        ]

        return ChevronPlanResult(
            rows=rows,
            stage_labels=stage_labels,
            time_unit="stages",
            row_terminology="Domains",
            reasoning="Security maturity model covering Access Control, Data Protection, Threat Detection, and Compliance."
        )

    def _create_data_maturity(self) -> ChevronPlanResult:
        """Create a data maturity model."""
        stage_labels = ["Initial", "Developing", "Defined", "Quantified", "Optimizing"]
        rows = [
            MaturityRow(
                id="row_1",
                label="Data Collection",
                chevrons=[
                    ChevronContent(bullets=["Manual data entry", "Inconsistent formats"]),
                    ChevronContent(bullets=["Basic integrations", "Some automation"]),
                    ChevronContent(bullets=["ETL pipelines", "Standardized schemas"]),
                    ChevronContent(bullets=["Real-time streaming", "Data contracts"]),
                    ChevronContent(bullets=["Self-service ingestion", "Auto-discovery"])
                ]
            ),
            MaturityRow(
                id="row_2",
                label="Data Storage",
                chevrons=[
                    ChevronContent(bullets=["Spreadsheets", "Siloed databases"]),
                    ChevronContent(bullets=["Central database", "Basic warehouse"]),
                    ChevronContent(bullets=["Data lake", "Cataloged assets"]),
                    ChevronContent(bullets=["Lakehouse", "Partitioned storage"]),
                    ChevronContent(bullets=["Multi-cloud", "Intelligent tiering"])
                ]
            ),
            MaturityRow(
                id="row_3",
                label="Analytics",
                chevrons=[
                    ChevronContent(bullets=["Excel reports", "Manual analysis"]),
                    ChevronContent(bullets=["BI dashboards", "SQL queries"]),
                    ChevronContent(bullets=["Self-service BI", "Data modeling"]),
                    ChevronContent(bullets=["Advanced analytics", "Predictive models"]),
                    ChevronContent(bullets=["Embedded analytics", "Real-time insights"])
                ]
            ),
            MaturityRow(
                id="row_4",
                label="AI/ML",
                chevrons=[
                    ChevronContent(bullets=["No ML", "Experimental"]),
                    ChevronContent(bullets=["POC models", "Manual training"]),
                    ChevronContent(bullets=["MLOps basics", "Model registry"]),
                    ChevronContent(bullets=["Automated ML", "A/B testing"]),
                    ChevronContent(bullets=["AI-first products", "Continuous learning"])
                ]
            ),
            MaturityRow(
                id="row_5",
                label="Governance",
                chevrons=[
                    ChevronContent(bullets=["No governance", "Tribal knowledge"]),
                    ChevronContent(bullets=["Basic metadata", "Data owners"]),
                    ChevronContent(bullets=["Data catalog", "Quality rules"]),
                    ChevronContent(bullets=["Lineage tracking", "Access policies"]),
                    ChevronContent(bullets=["Data mesh", "Federated governance"])
                ]
            )
        ]

        return ChevronPlanResult(
            rows=rows,
            stage_labels=stage_labels,
            time_unit="stages",
            row_terminology="Capabilities",
            reasoning="Data maturity model covering Collection, Storage, Analytics, AI/ML, and Governance."
        )

    def _create_agile_maturity(self) -> ChevronPlanResult:
        """Create an Agile maturity model."""
        stage_labels = ["Initial", "Emerging", "Defined", "Managed", "Business Agility"]
        rows = [
            MaturityRow(
                id="row_1",
                label="Planning",
                chevrons=[
                    ChevronContent(bullets=["Waterfall planning", "Fixed scope"]),
                    ChevronContent(bullets=["Sprint planning", "Basic backlog"]),
                    ChevronContent(bullets=["Refined backlog", "Story points"]),
                    ChevronContent(bullets=["Predictable velocity", "Capacity planning"]),
                    ChevronContent(bullets=["Continuous planning", "OKR alignment"])
                ]
            ),
            MaturityRow(
                id="row_2",
                label="Delivery",
                chevrons=[
                    ChevronContent(bullets=["Big bang releases", "Long cycles"]),
                    ChevronContent(bullets=["2-4 week sprints", "Demo sessions"]),
                    ChevronContent(bullets=["Consistent delivery", "Definition of Done"]),
                    ChevronContent(bullets=["Continuous delivery", "Feature flags"]),
                    ChevronContent(bullets=["Multiple daily deploys", "Experimentation"])
                ]
            ),
            MaturityRow(
                id="row_3",
                label="Feedback",
                chevrons=[
                    ChevronContent(bullets=["Delayed feedback", "End-of-project"]),
                    ChevronContent(bullets=["Sprint reviews", "Basic metrics"]),
                    ChevronContent(bullets=["Customer involvement", "A/B testing"]),
                    ChevronContent(bullets=["Continuous feedback", "Analytics-driven"]),
                    ChevronContent(bullets=["Real-time insights", "Hypothesis testing"])
                ]
            ),
            MaturityRow(
                id="row_4",
                label="Team Culture",
                chevrons=[
                    ChevronContent(bullets=["Command & control", "Individual work"]),
                    ChevronContent(bullets=["Cross-functional teams", "Daily standups"]),
                    ChevronContent(bullets=["Self-organizing", "Retrospectives"]),
                    ChevronContent(bullets=["High-performing", "Psychological safety"]),
                    ChevronContent(bullets=["Learning culture", "Innovation time"])
                ]
            )
        ]

        return ChevronPlanResult(
            rows=rows,
            stage_labels=stage_labels,
            time_unit="stages",
            row_terminology="Dimensions",
            reasoning="Agile maturity model covering Planning, Delivery, Feedback, and Team Culture."
        )

    def _create_cloud_maturity(self) -> ChevronPlanResult:
        """Create a cloud maturity model."""
        stage_labels = ["On-Prem", "Cloud Ready", "Cloud Native", "Cloud Optimized", "Cloud Mastery"]
        rows = [
            MaturityRow(
                id="row_1",
                label="Migration",
                chevrons=[
                    ChevronContent(bullets=["All on-premises", "Legacy systems"]),
                    ChevronContent(bullets=["Lift and shift", "IaaS adoption"]),
                    ChevronContent(bullets=["Re-platform", "Managed services"]),
                    ChevronContent(bullets=["Re-architect", "Microservices"]),
                    ChevronContent(bullets=["Cloud-born apps", "Serverless-first"])
                ]
            ),
            MaturityRow(
                id="row_2",
                label="Operations",
                chevrons=[
                    ChevronContent(bullets=["Manual ops", "Ticket-based"]),
                    ChevronContent(bullets=["Basic automation", "Cloud console"]),
                    ChevronContent(bullets=["IaC", "GitOps workflows"]),
                    ChevronContent(bullets=["SRE practices", "Self-healing"]),
                    ChevronContent(bullets=["AIOps", "Autonomous ops"])
                ]
            ),
            MaturityRow(
                id="row_3",
                label="Cost Management",
                chevrons=[
                    ChevronContent(bullets=["No visibility", "Over-provisioned"]),
                    ChevronContent(bullets=["Cost monitoring", "Basic budgets"]),
                    ChevronContent(bullets=["Tagging strategy", "Right-sizing"]),
                    ChevronContent(bullets=["FinOps practices", "Reserved capacity"]),
                    ChevronContent(bullets=["Predictive costs", "Unit economics"])
                ]
            ),
            MaturityRow(
                id="row_4",
                label="Governance",
                chevrons=[
                    ChevronContent(bullets=["Shadow IT", "No policies"]),
                    ChevronContent(bullets=["Basic policies", "Manual review"]),
                    ChevronContent(bullets=["Landing zones", "Guardrails"]),
                    ChevronContent(bullets=["Policy as code", "Automated compliance"]),
                    ChevronContent(bullets=["Self-service", "Federated governance"])
                ]
            )
        ]

        return ChevronPlanResult(
            rows=rows,
            stage_labels=stage_labels,
            time_unit="stages",
            row_terminology="Domains",
            reasoning="Cloud maturity model covering Migration, Operations, Cost Management, and Governance."
        )

    def _create_digital_maturity(self) -> ChevronPlanResult:
        """Create a digital transformation maturity model."""
        stage_labels = ["Traditional", "Emerging", "Integrating", "Optimizing", "Transforming"]
        rows = [
            MaturityRow(
                id="row_1",
                label="Customer Experience",
                chevrons=[
                    ChevronContent(bullets=["Single channel", "Reactive support"]),
                    ChevronContent(bullets=["Multi-channel", "Basic digital"]),
                    ChevronContent(bullets=["Omnichannel", "Personalization"]),
                    ChevronContent(bullets=["Seamless journeys", "Predictive support"]),
                    ChevronContent(bullets=["Hyper-personalized", "Proactive engagement"])
                ]
            ),
            MaturityRow(
                id="row_2",
                label="Operations",
                chevrons=[
                    ChevronContent(bullets=["Manual processes", "Paper-based"]),
                    ChevronContent(bullets=["Basic digitization", "Some automation"]),
                    ChevronContent(bullets=["End-to-end digital", "Workflow automation"]),
                    ChevronContent(bullets=["Intelligent automation", "RPA at scale"]),
                    ChevronContent(bullets=["Autonomous operations", "AI-driven decisions"])
                ]
            ),
            MaturityRow(
                id="row_3",
                label="Technology",
                chevrons=[
                    ChevronContent(bullets=["Legacy systems", "Siloed data"]),
                    ChevronContent(bullets=["Cloud exploration", "API development"]),
                    ChevronContent(bullets=["Cloud-first", "Integrated platforms"]),
                    ChevronContent(bullets=["API economy", "Real-time data"]),
                    ChevronContent(bullets=["Ecosystem platform", "AI-native"])
                ]
            ),
            MaturityRow(
                id="row_4",
                label="Culture & Skills",
                chevrons=[
                    ChevronContent(bullets=["Change resistant", "Skills gaps"]),
                    ChevronContent(bullets=["Digital awareness", "Training programs"]),
                    ChevronContent(bullets=["Digital mindset", "Cross-functional teams"]),
                    ChevronContent(bullets=["Data-driven culture", "Innovation hubs"]),
                    ChevronContent(bullets=["Digital-first DNA", "Continuous reinvention"])
                ]
            )
        ]

        return ChevronPlanResult(
            rows=rows,
            stage_labels=stage_labels,
            time_unit="stages",
            row_terminology="Dimensions",
            reasoning="Digital transformation maturity model covering Customer Experience, Operations, Technology, and Culture."
        )

    def _create_generic_maturity(self) -> ChevronPlanResult:
        """Create a generic capability maturity model (default fallback)."""
        stage_labels = ["Initial", "Developing", "Defined", "Managed", "Optimizing"]
        rows = [
            MaturityRow(
                id="row_1",
                label="Process",
                chevrons=[
                    ChevronContent(bullets=["Ad-hoc processes", "Undocumented"]),
                    ChevronContent(bullets=["Basic documentation", "Some repeatability"]),
                    ChevronContent(bullets=["Standardized processes", "Consistent execution"]),
                    ChevronContent(bullets=["Measured outcomes", "Continuous monitoring"]),
                    ChevronContent(bullets=["Optimized for efficiency", "Continuous improvement"])
                ]
            ),
            MaturityRow(
                id="row_2",
                label="Technology",
                chevrons=[
                    ChevronContent(bullets=["Manual tools", "Spreadsheets"]),
                    ChevronContent(bullets=["Basic tooling", "Some integration"]),
                    ChevronContent(bullets=["Integrated systems", "Automation"]),
                    ChevronContent(bullets=["Advanced analytics", "AI assistance"]),
                    ChevronContent(bullets=["Intelligent automation", "Predictive capabilities"])
                ]
            ),
            MaturityRow(
                id="row_3",
                label="People",
                chevrons=[
                    ChevronContent(bullets=["Individual expertise", "No formal training"]),
                    ChevronContent(bullets=["Team knowledge", "Basic training"]),
                    ChevronContent(bullets=["Defined roles", "Skill development"]),
                    ChevronContent(bullets=["Cross-functional teams", "Mentorship"]),
                    ChevronContent(bullets=["Learning culture", "Innovation mindset"])
                ]
            )
        ]

        return ChevronPlanResult(
            rows=rows,
            stage_labels=stage_labels,
            time_unit="stages",
            row_terminology="Capabilities",
            reasoning="Generic capability maturity model covering Process, Technology, and People dimensions."
        )
