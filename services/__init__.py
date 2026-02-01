"""
HTML-based Diagram Services

LLM-powered generators for creating HTML diagram content:
- GanttGenerator: Project timeline Gantt charts
- KanbanGenerator: Task management boards
- CodeDisplayGenerator: Syntax-highlighted code displays (legacy)
- ChevronGenerator: Strategic roadmaps with chevron milestones

Atomic component generators:
- AtomicCodeDisplayGenerator: Atomic CODE_DISPLAY endpoint generator
- KanbanAtomicGenerator: Atomic KANBAN_BOARD endpoint generator
- GanttAtomicGenerator: Atomic GANTT_CHART endpoint generator
- CloudArchitectureGenerator: Atomic CLOUD_ARCHITECTURE endpoint generator
- LogicalArchitectureGenerator: Atomic LOGICAL_ARCHITECTURE endpoint generator
- DataArchitectureGenerator: Atomic DATA_ARCHITECTURE endpoint generator (ER diagrams)
"""

from .gantt_generator import GanttGenerator
from .kanban_generator import KanbanGenerator
from .code_generator import CodeDisplayGenerator
from .chevron_generator import ChevronGenerator
from .code_display_service import CodeDisplayGenerator as AtomicCodeDisplayGenerator
from .kanban_atomic_service import KanbanAtomicGenerator
from .gantt_atomic_service import GanttAtomicGenerator
from .cloud_architecture_atomic_service import CloudArchitectureGenerator
from .logical_architecture_atomic_service import LogicalArchitectureGenerator
from .data_architecture_atomic_service import DataArchitectureGenerator

__all__ = [
    "GanttGenerator",
    "KanbanGenerator",
    "CodeDisplayGenerator",
    "ChevronGenerator",
    "AtomicCodeDisplayGenerator",
    "KanbanAtomicGenerator",
    "GanttAtomicGenerator",
    "CloudArchitectureGenerator",
    "LogicalArchitectureGenerator",
    "DataArchitectureGenerator",
]
