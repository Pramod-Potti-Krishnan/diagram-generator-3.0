"""
v3.0 Integration Tests

Tests for the new structured diagram generation agents:
- PlotlyAgent (timeline, quadrant, journey)
- D2Agent (flowchart, er_diagram, architecture)
- FrappeGanttAgent (gantt)
- MarkmapAgent (mindmap)
- KanbanAgent (kanban)
"""

import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImports:
    """Test that all v3.0 components can be imported"""

    def test_import_generation_methods(self):
        """Test new GenerationMethod enum values exist"""
        from models import GenerationMethod

        assert hasattr(GenerationMethod, 'PLOTLY')
        assert hasattr(GenerationMethod, 'D2')
        assert hasattr(GenerationMethod, 'FRAPPE_GANTT')
        assert hasattr(GenerationMethod, 'MARKMAP')
        assert hasattr(GenerationMethod, 'KANBAN')

        # Check values
        assert GenerationMethod.PLOTLY.value == "plotly"
        assert GenerationMethod.D2.value == "d2"
        assert GenerationMethod.FRAPPE_GANTT.value == "frappe_gantt"
        assert GenerationMethod.MARKMAP.value == "markmap"
        assert GenerationMethod.KANBAN.value == "kanban"

    def test_import_agents(self):
        """Test all v3.0 agents can be imported"""
        from agents import (
            PlotlyAgent,
            D2Agent,
            FrappeGanttAgent,
            MarkmapAgent,
            KanbanAgent,
            StructuredBaseAgent
        )

        assert PlotlyAgent is not None
        assert D2Agent is not None
        assert FrappeGanttAgent is not None
        assert MarkmapAgent is not None
        assert KanbanAgent is not None
        assert StructuredBaseAgent is not None

    def test_import_renderers(self):
        """Test all v3.0 renderers can be imported"""
        from renderers import (
            BaseRenderer,
            PlaywrightRenderer,
            PlotlyRenderer,
            D2Renderer,
            FrappeGanttRenderer,
            MarkmapRenderer,
            KanbanRenderer
        )

        assert BaseRenderer is not None
        assert PlaywrightRenderer is not None
        assert PlotlyRenderer is not None
        assert D2Renderer is not None
        assert FrappeGanttRenderer is not None
        assert MarkmapRenderer is not None
        assert KanbanRenderer is not None


class TestRouting:
    """Test conductor routing for v3.0 diagram types"""

    def test_v3_routing_table_exists(self):
        """Test v3 routing table is properly configured"""
        from config.settings import get_settings
        from core.conductor import DiagramConductor

        settings = get_settings()
        conductor = DiagramConductor(settings)

        assert hasattr(conductor, 'v3_routing')
        assert isinstance(conductor.v3_routing, dict)

        # Check all expected diagram types are routed
        expected_types = [
            'gantt', 'kanban', 'timeline', 'quadrant', 'journey',
            'journey_map', 'flowchart', 'er_diagram', 'architecture',
            'mindmap', 'mind_map'
        ]
        for dtype in expected_types:
            assert dtype in conductor.v3_routing, f"Missing routing for {dtype}"

    def test_routing_methods(self):
        """Test diagram types route to correct methods"""
        from config.settings import get_settings
        from core.conductor import DiagramConductor
        from models import GenerationMethod

        settings = get_settings()
        conductor = DiagramConductor(settings)

        # Test C5-only types
        method, layouts = conductor.v3_routing['gantt']
        assert method == GenerationMethod.FRAPPE_GANTT
        assert layouts == ['C5']

        method, layouts = conductor.v3_routing['kanban']
        assert method == GenerationMethod.KANBAN
        assert layouts == ['C5']

        # Test Plotly types (V3 layout)
        for dtype in ['timeline', 'quadrant', 'journey', 'journey_map']:
            method, layouts = conductor.v3_routing[dtype]
            assert method == GenerationMethod.PLOTLY
            assert layouts == ['V3']

        # Test D2 types (V3 layout)
        for dtype in ['flowchart', 'er_diagram', 'architecture']:
            method, layouts = conductor.v3_routing[dtype]
            assert method == GenerationMethod.D2
            assert layouts == ['V3']

        # Test Markmap types (V3 layout)
        for dtype in ['mindmap', 'mind_map']:
            method, layouts = conductor.v3_routing[dtype]
            assert method == GenerationMethod.MARKMAP
            assert layouts == ['V3']

    def test_routing_info_method(self):
        """Test get_v3_routing_info helper method"""
        from config.settings import get_settings
        from core.conductor import DiagramConductor

        settings = get_settings()
        conductor = DiagramConductor(settings)

        info = conductor.get_v3_routing_info()

        assert isinstance(info, dict)
        assert 'gantt' in info
        assert info['gantt']['method'] == 'frappe_gantt'
        assert info['gantt']['layouts'] == ['C5']


class TestAgentTypes:
    """Test agent supported types"""

    def test_plotly_agent_types(self):
        """Test PlotlyAgent supports correct types"""
        from config.settings import get_settings
        from agents import PlotlyAgent

        settings = get_settings()
        agent = PlotlyAgent(settings)

        assert 'timeline' in agent.supported_types
        assert 'quadrant' in agent.supported_types
        assert 'journey' in agent.supported_types

    def test_d2_agent_types(self):
        """Test D2Agent supports correct types"""
        from config.settings import get_settings
        from agents import D2Agent

        settings = get_settings()
        agent = D2Agent(settings)

        assert 'flowchart' in agent.supported_types
        assert 'er_diagram' in agent.supported_types
        assert 'architecture' in agent.supported_types

    def test_frappe_gantt_agent_types(self):
        """Test FrappeGanttAgent supports correct types"""
        from config.settings import get_settings
        from agents import FrappeGanttAgent

        settings = get_settings()
        agent = FrappeGanttAgent(settings)

        assert 'gantt' in agent.supported_types

    def test_markmap_agent_types(self):
        """Test MarkmapAgent supports correct types"""
        from config.settings import get_settings
        from agents import MarkmapAgent

        settings = get_settings()
        agent = MarkmapAgent(settings)

        assert 'mindmap' in agent.supported_types

    def test_kanban_agent_types(self):
        """Test KanbanAgent supports correct types"""
        from config.settings import get_settings
        from agents import KanbanAgent

        settings = get_settings()
        agent = KanbanAgent(settings)

        assert 'kanban' in agent.supported_types


class TestConstants:
    """Test configuration constants"""

    def test_supported_diagram_types(self):
        """Test SUPPORTED_DIAGRAM_TYPES includes v3.0 methods"""
        from config.constants import SUPPORTED_DIAGRAM_TYPES

        assert 'plotly' in SUPPORTED_DIAGRAM_TYPES
        assert 'd2' in SUPPORTED_DIAGRAM_TYPES
        assert 'frappe_gantt' in SUPPORTED_DIAGRAM_TYPES
        assert 'markmap' in SUPPORTED_DIAGRAM_TYPES
        assert 'kanban' in SUPPORTED_DIAGRAM_TYPES

    def test_method_priorities(self):
        """Test METHOD_PRIORITIES includes v3.0 methods"""
        from config.constants import METHOD_PRIORITIES

        assert 'plotly' in METHOD_PRIORITIES
        assert 'd2' in METHOD_PRIORITIES
        assert 'frappe_gantt' in METHOD_PRIORITIES
        assert 'markmap' in METHOD_PRIORITIES
        assert 'kanban' in METHOD_PRIORITIES

        # v3.0 methods should have highest priority
        assert METHOD_PRIORITIES['plotly'] < METHOD_PRIORITIES['mermaid']
        assert METHOD_PRIORITIES['d2'] < METHOD_PRIORITIES['mermaid']

    def test_generation_timeouts(self):
        """Test GENERATION_TIMEOUTS includes v3.0 methods"""
        from config.constants import GENERATION_TIMEOUTS

        assert 'plotly' in GENERATION_TIMEOUTS
        assert 'd2' in GENERATION_TIMEOUTS
        assert 'frappe_gantt' in GENERATION_TIMEOUTS
        assert 'markmap' in GENERATION_TIMEOUTS
        assert 'kanban' in GENERATION_TIMEOUTS


class TestSchemas:
    """Test JSON schemas exist and are valid"""

    def test_schemas_exist(self):
        """Test all v3.0 schemas exist"""
        import json
        from pathlib import Path

        schemas_dir = Path(__file__).parent.parent / 'schemas'

        expected_schemas = [
            'gantt_schema.json',
            'timeline_schema.json',
            'quadrant_schema.json',
            'journey_schema.json',
            'flowchart_schema.json',
            'er_schema.json',
            'architecture_schema.json',
            'mindmap_schema.json',
            'kanban_schema.json'
        ]

        for schema_file in expected_schemas:
            schema_path = schemas_dir / schema_file
            assert schema_path.exists(), f"Missing schema: {schema_file}"

            # Verify it's valid JSON
            with open(schema_path) as f:
                schema = json.load(f)
            assert '$schema' in schema or 'type' in schema


class TestTemplates:
    """Test HTML templates exist"""

    def test_templates_exist(self):
        """Test all v3.0 templates exist"""
        from pathlib import Path

        templates_dir = Path(__file__).parent.parent / 'templates'

        expected_templates = [
            'frappe_gantt.html',
            'markmap.html',
            'kanban.html'
        ]

        for template_file in expected_templates:
            template_path = templates_dir / template_file
            assert template_path.exists(), f"Missing template: {template_file}"

            # Verify it's valid HTML (basic check)
            with open(template_path) as f:
                content = f.read()
            assert '<!DOCTYPE html>' in content or '<html' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
