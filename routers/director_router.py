"""
Director Coordination Router
============================

Exposes endpoints for Director Agent service coordination:
- GET /capabilities - Service discovery
- POST /can-handle - Content negotiation
- POST /recommend-diagram - Diagram type recommendation

These endpoints follow SERVICE_CAPABILITIES_SPEC.md for Strawman integration.
"""

from fastapi import APIRouter
from typing import List, Tuple, Optional

from models.director_models import (
    CapabilitiesResponse, Capabilities, ContentSignals, DiagramTypeSignal, Endpoints,
    CanHandleRequest, CanHandleResponse, SpaceUtilization, ContentHints,
    RecommendDiagramRequest, RecommendDiagramResponse,
    DiagramRecommendation, NotRecommended, SpaceRequirement
)
from config.constants import DIAGRAM_TYPE_SIGNALS, DIAGRAM_CONTENT_SIGNALS

router = APIRouter(tags=["Director Coordination"])


# ============ Helper Functions ============

def _calculate_confidence(request: CanHandleRequest) -> Tuple[bool, float, str, Optional[str]]:
    """
    Calculate whether this service can handle the content and with what confidence.

    Returns:
        Tuple of (can_handle, confidence, reason, suggested_approach)
    """
    content = request.slide_content
    hints = request.content_hints or ContentHints()

    # Combine all text for analysis
    combined_text = (content.title + " " + " ".join(content.topics)).lower()

    # Check for negative signals (content we handle poorly)
    negative_keywords = ["chart", "graph", "percentage", "pie", "bar", "scatter", "plot", "data visualization"]
    if any(kw in combined_text for kw in negative_keywords):
        return (False, 0.2, "Content appears to be data/chart focused - better suited for analytics service", None)

    # Check for bullet list patterns (we don't handle well)
    bullet_patterns = ["compare", "comparison", "versus", "vs.", "pros and cons"]
    if any(pattern in combined_text for pattern in bullet_patterns) and "flow" not in combined_text:
        return (False, 0.3, "Content appears to be comparison/bullet focused - better suited for text service", None)

    # Score each diagram type
    best_score = 0.0
    best_type = None
    best_matched_keywords: List[str] = []

    for dtype, signals in DIAGRAM_TYPE_SIGNALS.items():
        score = 0.0
        matched_keywords = [kw for kw in signals["keywords"] if kw in combined_text]

        if matched_keywords:
            # Base score from keyword matches
            score = min(0.9, 0.3 + (len(matched_keywords) * 0.12))

            # Boost for detected_keywords from hints (Director already analyzed)
            if hints.detected_keywords:
                hint_matches = [kw for kw in hints.detected_keywords if kw in signals["keywords"]]
                score += len(hint_matches) * 0.08

            # Boost for topic count fit
            ideal = signals.get("ideal_topic_count", {"min": 2, "max": 10})
            if ideal["min"] <= content.topic_count <= ideal["max"]:
                score += 0.1

            score = min(0.95, score)  # Cap at 0.95

        if score > best_score:
            best_score = score
            best_type = dtype
            best_matched_keywords = matched_keywords

    # Determine result based on score
    if best_score >= 0.5:
        reason = f"Content matches {best_type} patterns (keywords: {', '.join(best_matched_keywords[:3])})"
        return (True, round(best_score, 2), reason, best_type)
    elif best_score >= 0.3:
        reason = f"Weak match for {best_type} - diagram possible but may not be optimal"
        return (True, round(best_score, 2), reason, best_type)
    else:
        return (False, round(best_score, 2), "Content doesn't fit diagram patterns well", None)


def _rank_diagram_types(request: RecommendDiagramRequest) -> RecommendDiagramResponse:
    """
    Score all diagram types and return ranked recommendations.
    """
    content = request.slide_content
    combined_text = (content.title + " " + " ".join(content.topics)).lower()

    recommendations: List[DiagramRecommendation] = []
    not_recommended: List[NotRecommended] = []

    for dtype, signals in DIAGRAM_TYPE_SIGNALS.items():
        matched = [kw for kw in signals["keywords"] if kw in combined_text]

        # Base score
        score = 0.2 if matched else 0.1

        if matched:
            score += len(matched) * 0.12

        # Check topic count fit
        ideal = signals.get("ideal_topic_count", {"min": 2, "max": 10})
        if ideal["min"] <= content.topic_count <= ideal["max"]:
            score += 0.1
        elif content.topic_count < ideal["min"]:
            score -= 0.1

        score = min(0.95, max(0.1, score))  # Clamp between 0.1 and 0.95

        if score >= 0.35:
            # Build reason
            if matched:
                reason = f"Matched keywords: {', '.join(matched[:3])}"
            else:
                reason = "Structural fit based on topic count"

            # Estimate space requirements
            space = SpaceRequirement(width=1600, height=600)
            if dtype in ["gantt", "timeline"]:
                space = SpaceRequirement(width=1800, height=400)
            elif dtype in ["erDiagram", "flowchart"]:
                space = SpaceRequirement(width=1600, height=700)
            elif dtype == "kanban":
                space = SpaceRequirement(width=1800, height=600)

            recommendations.append(DiagramRecommendation(
                diagram_type=dtype,
                confidence=round(score, 2),
                reason=reason,
                requires_space=space
            ))
        else:
            not_recommended.append(NotRecommended(
                diagram_type=dtype,
                reason=f"No matching patterns for {dtype}" if not matched else f"Low confidence ({score:.2f})"
            ))

    # Sort by confidence descending
    recommendations.sort(key=lambda x: x.confidence, reverse=True)

    return RecommendDiagramResponse(
        recommended_diagrams=recommendations[:5],  # Top 5
        not_recommended=not_recommended
    )


# ============ Endpoints ============

@router.get("/capabilities", response_model=CapabilitiesResponse)
async def get_capabilities():
    """
    Phase 1: Service Discovery

    Returns complete service capabilities for Director Agent's Strawman Service.
    This enables intelligent service routing at strawman generation time.
    """
    return CapabilitiesResponse(
        service="diagram-service",
        version="3.0.0",
        status="healthy",
        capabilities=Capabilities(
            slide_types=["diagram", "flowchart", "architecture"],
            diagram_types=list(DIAGRAM_TYPE_SIGNALS.keys()),
            supports_themes=True,
            mermaid_output=True
        ),
        content_signals=ContentSignals(**DIAGRAM_CONTENT_SIGNALS),
        diagram_type_signals={
            k: DiagramTypeSignal(best_for=v["best_for"], keywords=v["keywords"])
            for k, v in DIAGRAM_TYPE_SIGNALS.items()
        },
        endpoints=Endpoints()
    )


@router.post("/can-handle", response_model=CanHandleResponse)
async def can_handle(request: CanHandleRequest):
    """
    Phase 2: Content Negotiation

    Answers "Can this service handle this specific content?"
    Returns confidence score (0-1) to help Director choose between services.

    Confidence score guidelines:
    - 0.90+ : Excellent fit, high confidence
    - 0.70-0.89 : Good fit, can handle well
    - 0.50-0.69 : Acceptable, but other services might be better
    - < 0.50 : Poor fit, prefer other service
    """
    can_handle, confidence, reason, suggested_approach = _calculate_confidence(request)

    # Build space utilization if we can handle it
    space_util = None
    if can_handle:
        space_util = SpaceUtilization(
            fits_well=True,
            estimated_fill_percent=80 if confidence >= 0.7 else 65
        )

    return CanHandleResponse(
        can_handle=can_handle,
        confidence=confidence,
        reason=reason,
        suggested_approach=suggested_approach,
        space_utilization=space_util
    )


@router.post("/recommend-diagram", response_model=RecommendDiagramResponse)
async def recommend_diagram(request: RecommendDiagramRequest):
    """
    Phase 3: Diagram Type Recommendation

    Returns ranked list of recommended diagram types for the given content.
    Used by Director to select the best diagram variant.

    Response includes:
    - recommended_diagrams: Ranked list with confidence scores
    - not_recommended: Types that don't fit this content
    """
    return _rank_diagram_types(request)
