"""
Diagram Conductor - Orchestrates diagram generation

This is the main orchestrator that:
1. Receives diagram requests
2. Routes to appropriate generation method
3. Handles fallbacks
4. Returns generated diagrams
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from models import DiagramRequest, GenerationStrategy, GenerationMethod
from utils.logger import setup_logger
from .unified_playbook import UnifiedPlaybook
from agents import (
    # Legacy agents
    SVGAgent, MermaidAgent, PythonChartAgent,
    # v3.0 structured agents
    PlotlyAgent, D2Agent, FrappeGanttAgent, MarkmapAgent, KanbanAgent
)
from storage import DiagramStorage, DiagramOperations, CacheManager, DiagramSessionManager

logger = setup_logger(__name__)


class DiagramConductor:
    """
    Main conductor for diagram generation
    
    Orchestrates the entire generation process following Phase 1 patterns
    for minimal context passing and efficient routing.
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.playbook = UnifiedPlaybook(settings)
        
        # Initialize agents - legacy and v3.0 structured
        self.agents = {
            # Legacy agents
            GenerationMethod.SVG_TEMPLATE: SVGAgent(settings),
            GenerationMethod.MERMAID: MermaidAgent(settings),
            GenerationMethod.PYTHON_CHART: PythonChartAgent(settings),
            # v3.0 structured agents
            GenerationMethod.PLOTLY: PlotlyAgent(settings),
            GenerationMethod.D2: D2Agent(settings),
            GenerationMethod.FRAPPE_GANTT: FrappeGanttAgent(settings),
            GenerationMethod.MARKMAP: MarkmapAgent(settings),
            GenerationMethod.KANBAN: KanbanAgent(settings),
        }

        # v3.0 Routing table: diagram_type -> (method, allowed_layouts)
        self.v3_routing = {
            # C5 layout only (full-width diagrams)
            "gantt": (GenerationMethod.FRAPPE_GANTT, ["C5"]),
            "kanban": (GenerationMethod.KANBAN, ["C5"]),
            # V3 layout only (content diagrams for split layouts)
            "timeline": (GenerationMethod.PLOTLY, ["V3"]),
            "quadrant": (GenerationMethod.PLOTLY, ["V3"]),
            "journey": (GenerationMethod.PLOTLY, ["V3"]),
            "journey_map": (GenerationMethod.PLOTLY, ["V3"]),
            "flowchart": (GenerationMethod.D2, ["V3"]),
            "er_diagram": (GenerationMethod.D2, ["V3"]),
            "architecture": (GenerationMethod.D2, ["V3"]),
            "mindmap": (GenerationMethod.MARKMAP, ["V3"]),
            "mind_map": (GenerationMethod.MARKMAP, ["V3"]),
        }
        
        # Initialize storage components
        self.storage = DiagramStorage(settings)
        self.db_ops = DiagramOperations(self.storage.client)
        self.cache = CacheManager(
            ttl_seconds=getattr(settings, 'cache_ttl', 3600),
            max_size=100
        )
        self.session_manager = DiagramSessionManager(
            storage_client=self.storage,
            db_operations=self.db_ops
        )
        
        # Metrics
        self.generation_count = 0
        self.fallback_count = 0
        self.error_count = 0
    
    async def initialize(self):
        """Initialize conductor and agents"""
        logger.info("Initializing Diagram Conductor...")
        
        # Initialize playbook
        await self.playbook.initialize()
        
        # Initialize agents
        for method, agent in self.agents.items():
            try:
                await agent.initialize()
                logger.info(f"Initialized agent: {method}")
            except Exception as e:
                logger.error(f"Failed to initialize {method} agent: {e}")
        
        # Start cache and session manager
        await self.cache.start()
        await self.session_manager.start()
        
        logger.info("Diagram Conductor initialized")
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        logger.info("Shutting down Diagram Conductor...")
        
        # Shutdown agents
        for method, agent in self.agents.items():
            try:
                await agent.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {method} agent: {e}")
        
        # Stop cache and session manager
        await self.cache.stop()
        await self.session_manager.stop()
        
        logger.info("Diagram Conductor shut down")
    
    async def generate(self, request: DiagramRequest) -> Dict[str, Any]:
        """
        Generate diagram based on request
        
        Args:
            request: Diagram generation request
            
        Returns:
            Generated diagram with metadata
        """
        
        start_time = time.time()
        self.generation_count += 1
        
        try:
            # Create or get session (optional - for tracking)
            try:
                await self.session_manager.create_session(
                    request.session_id,
                    request.user_id,
                    {"request_id": request.request_id}
                )
            except Exception as e:
                logger.debug(f"Session tracking unavailable (non-critical): {e}")
            
            # Check cache first
            cached = self.cache.get(request.dict())
            if cached:
                logger.info("Cache hit - returning cached diagram")
                cached["metadata"]["cache_hit"] = True
                return cached

            # v3.0 Direct routing for new structured agents
            diagram_type_lower = request.diagram_type.lower()
            if diagram_type_lower in self.v3_routing:
                method, allowed_layouts = self.v3_routing[diagram_type_lower]
                logger.info(f"v3.0 routing: {diagram_type_lower} -> {method.value}")

                strategy = GenerationStrategy(
                    method=method,
                    confidence=0.95,
                    reasoning=f"v3.0 structured agent for {diagram_type_lower}",
                    fallback_chain=[GenerationMethod.MERMAID],  # Mermaid as fallback
                    estimated_time_ms=self._estimate_v3_time(method),
                    quality_estimate="high"
                )
            else:
                # Get generation strategy from playbook (legacy routing)
                strategy = await self.playbook.get_strategy(request)
            logger.info(
                f"Selected strategy: {strategy.method} "
                f"(confidence: {strategy.confidence:.2f})"
            )
            
            # Try primary method
            result = await self._try_generation(request, strategy)
            
            if result:
                # Success with primary method
                generation_time = int((time.time() - start_time) * 1000)
                result["metadata"]["generation_time_ms"] = generation_time
                
                # Upload to storage and save metadata
                result = await self._save_to_storage(request, result)
                
                # Cache the result
                self.cache.set(request.dict(), result)

                # Update session (optional - for tracking)
                try:
                    await self.session_manager.update_session(
                        request.session_id,
                        result["diagram_id"],
                        request.diagram_type,
                        strategy.method.value,
                        generation_time,
                        cache_hit=False
                    )
                except Exception as e:
                    logger.debug(f"Session update unavailable (non-critical): {e}")

                # Mark as successful
                result["success"] = True
                return result
            
            # Try fallback methods
            if self.settings.enable_fallback and strategy.fallback_chain:
                logger.info("Primary method failed, trying fallbacks...")
                self.fallback_count += 1
                
                for _ in range(len(strategy.fallback_chain)):
                    strategy = strategy.use_fallback()
                    logger.info(f"Trying fallback: {strategy.method}")
                    
                    result = await self._try_generation(request, strategy)
                    if result:
                        generation_time = int((time.time() - start_time) * 1000)
                        result["metadata"]["generation_time_ms"] = generation_time
                        result["metadata"]["fallback_used"] = True
                        
                        # Upload to storage and save metadata
                        result = await self._save_to_storage(request, result)
                        
                        # Cache the result
                        self.cache.set(request.dict(), result)

                        # Update session (optional - for tracking)
                        try:
                            await self.session_manager.update_session(
                                request.session_id,
                                result["diagram_id"],
                                request.diagram_type,
                                strategy.method.value,
                                generation_time,
                                cache_hit=False
                            )
                        except Exception as e:
                            logger.debug(f"Session update unavailable (non-critical): {e}")

                        # Mark as successful
                        result["success"] = True
                        return result
            
            # All methods failed
            self.error_count += 1
            raise ValueError("All generation methods failed")
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Generation failed: {e}", exc_info=True)
            raise
    
    async def _try_generation(
        self,
        request: DiagramRequest,
        strategy: GenerationStrategy
    ) -> Optional[Dict[str, Any]]:
        """
        Try generating with specific method
        
        Args:
            request: Diagram request
            strategy: Generation strategy
            
        Returns:
            Generated diagram or None if failed
        """
        
        try:
            # Get appropriate agent
            agent = self.agents.get(strategy.method)
            if not agent:
                logger.error(f"No agent for method: {strategy.method}")
                return None
            
            # Check if agent supports this diagram type
            if not await agent.supports(request.diagram_type):
                logger.info(
                    f"Agent {strategy.method} does not support {request.diagram_type}"
                )
                return None
            
            # Generate diagram with timeout
            timeout = self.settings.request_timeout
            result = await asyncio.wait_for(
                agent.generate(request),
                timeout=timeout
            )

            # Check if generation was successful
            if not result.get("success", False):
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Agent {strategy.method} generation failed: {error_msg}")
                return None

            # Verify content exists
            if not result.get("content"):
                logger.error(f"Agent {strategy.method} returned empty content")
                return None

            # Add metadata
            result["metadata"] = result.get("metadata", {})
            result["metadata"]["generation_method"] = strategy.method.value
            result["metadata"]["quality_score"] = self._calculate_quality_score(
                result,
                strategy
            )

            return result
        
        except asyncio.TimeoutError:
            logger.error(f"Generation timeout for {strategy.method}")
            return None
        except Exception as e:
            logger.error(f"Generation error with {strategy.method}: {e}")
            return None
    
    def _calculate_quality_score(
        self,
        result: Dict[str, Any],
        strategy: GenerationStrategy
    ) -> float:
        """
        Calculate quality score for generated diagram
        
        Args:
            result: Generation result
            strategy: Used strategy
            
        Returns:
            Quality score between 0 and 1
        """
        
        # Base score from strategy confidence
        score = strategy.confidence
        
        # Adjust based on content
        if result.get("content"):
            content_length = len(result["content"])
            if content_length > 1000:  # Substantial content
                score = min(1.0, score + 0.1)
            elif content_length < 100:  # Too small
                score = max(0.0, score - 0.2)
        
        # Adjust based on metadata
        if result.get("metadata", {}).get("cache_hit"):
            score = min(1.0, score + 0.1)  # Cached results are proven good
        
        return round(score, 2)
    
    async def _save_to_storage(self, request: DiagramRequest, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save diagram to storage and database.

        Args:
            request: Original request
            result: Generation result

        Returns:
            Updated result with URL and diagram ID
        """

        url = ""
        diagram_id = str(uuid.uuid4())

        # Determine content type from result (v3.0 agents set this)
        content_type = result.get("content_type", "svg")

        # Debug logging for storage upload
        content = result.get("content", "")
        logger.info(f"Storage upload debug: content_type={content_type}, content_size={len(content) if content else 0}, result_keys={list(result.keys())}")

        # Try to upload to storage
        try:
            if not content:
                logger.error("No content in result to upload!")
            else:
                url = await self.storage.upload_diagram(
                    svg_content=content,
                    diagram_type=request.diagram_type,
                    session_id=request.session_id or "default",
                    user_id=request.user_id or "anonymous",
                    metadata=result.get("metadata", {}),
                    content_type=content_type
                )
                logger.info(f"Uploaded diagram to storage: {url}")
        except Exception as e:
            logger.error(f"Failed to upload to storage: {e}", exc_info=True)
            # Continue without URL - will use inline content

        # Try to save metadata to database (optional)
        if url:
            try:
                diagram_id = await self.db_ops.save_diagram_metadata(
                    session_id=request.session_id or "default",
                    user_id=request.user_id or "anonymous",
                    diagram_type=request.diagram_type,
                    url=url,
                    generation_method=result["metadata"]["generation_method"],
                    request_params=request.dict(),
                    metadata=result["metadata"]
                )
                logger.info(f"Saved diagram metadata: {diagram_id}")
            except Exception as e:
                logger.warning(f"Failed to save diagram metadata (non-critical): {e}")
                # Keep the URL even if metadata save fails

        # Update result with storage information
        result["url"] = url
        result["diagram_id"] = diagram_id
        result["content_delivery"] = "url" if url else "inline"

        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get conductor metrics"""
        return {
            "generation_count": self.generation_count,
            "fallback_count": self.fallback_count,
            "error_count": self.error_count,
            "fallback_rate": (
                self.fallback_count / self.generation_count
                if self.generation_count > 0 else 0
            ),
            "error_rate": (
                self.error_count / self.generation_count
                if self.generation_count > 0 else 0
            ),
            "cache_stats": self.cache.get_statistics(),
            "session_stats": self.session_manager.get_global_statistics()
        }

    def _estimate_v3_time(self, method: GenerationMethod) -> int:
        """Estimate generation time for v3.0 methods in milliseconds"""
        estimates = {
            GenerationMethod.PLOTLY: 1500,         # Python + Kaleido rendering
            GenerationMethod.D2: 800,              # D2 CLI subprocess
            GenerationMethod.FRAPPE_GANTT: 2000,   # HTML + Playwright screenshot
            GenerationMethod.MARKMAP: 1500,        # HTML + Playwright screenshot
            GenerationMethod.KANBAN: 1500,         # Tailwind HTML + Playwright screenshot
        }
        return estimates.get(method, 1500)

    def get_v3_routing_info(self) -> Dict[str, Any]:
        """Get v3.0 routing table for debugging"""
        return {
            diagram_type: {
                "method": method.value,
                "layouts": layouts
            }
            for diagram_type, (method, layouts) in self.v3_routing.items()
        }