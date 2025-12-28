#!/usr/bin/env python3
"""
Unit tests for Mermaid validators.
Tests the new validators added in the plan:
- Journey score validator
- Flowchart reserved word validator
- QuadrantChart coordinate validator
- Simplified gantt validator
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mermaid_validator import MermaidValidator
from config.settings import Settings


async def test_journey_validator():
    """Test journey score validation - scores > 5 should be clamped."""
    print("\n=== Testing Journey Score Validator ===")

    settings = Settings()
    validator = MermaidValidator(settings)

    # Test case 1: Scores > 5 should be fixed
    journey_with_high_scores = """journey
    section Discovery
        Search product: 10: Customer
        Browse categories: 8: Customer
        Read reviews: 7: Customer

    section Purchase
        Add to cart: 5: Customer
        Checkout: 6: Customer"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("journey", journey_with_high_scores)

    print(f"  Input has scores: 10, 8, 7, 6")
    print(f"  Is valid (no issues): {is_valid}")
    print(f"  Issues found: {len(issues)}")
    for issue in issues:
        print(f"    - {issue}")

    # Verify scores were fixed
    assert ": 10:" not in fixed_code, "Score 10 should be fixed"
    assert ": 8:" not in fixed_code, "Score 8 should be fixed"
    assert ": 7:" not in fixed_code, "Score 7 should be fixed"
    assert ": 6:" not in fixed_code, "Score 6 should be fixed"
    assert ": 5:" in fixed_code, "Score 5 should remain"

    print("  PASSED: High scores were clamped to valid range")

    # Test case 2: Valid scores should pass through unchanged
    valid_journey = """journey
    section Test
        Good task: 5: User
        Okay task: 3: User
        Bad task: 1: User"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("journey", valid_journey)

    print(f"\n  Valid journey with scores 5, 3, 1:")
    print(f"  Is valid: {is_valid}")
    print(f"  Issues: {len(issues)}")
    assert is_valid, "Valid journey should pass"
    assert len(issues) == 0, "No issues should be found"
    print("  PASSED: Valid scores passed through unchanged")


async def test_flowchart_validator():
    """Test flowchart reserved word validation - 'end' should be capitalized."""
    print("\n=== Testing Flowchart Reserved Word Validator ===")

    settings = Settings()
    validator = MermaidValidator(settings)

    # Test case 1: Bare 'end' in node text
    flowchart_with_end = """flowchart TD
    A[Start] --> B[Process]
    B --> C[end]
    C --> D(end)
    D --> E{end}"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("flowchart", flowchart_with_end)

    print(f"  Input has 'end' in brackets: [end], (end), {{end}}")
    print(f"  Is valid (no issues): {is_valid}")
    print(f"  Issues found: {len(issues)}")
    for issue in issues:
        print(f"    - {issue}")

    # Verify 'end' was fixed to 'End' (capitalized)
    # The pattern [end] should become [End]
    assert "[end]" not in fixed_code, "Lowercase '[end]' should be replaced"
    assert "(end)" not in fixed_code, "Lowercase '(end)' should be replaced"
    assert "{end}" not in fixed_code, "Lowercase '{end}' should be replaced"
    # Check that capitalized versions exist
    assert "[End]" in fixed_code, "'[end]' should be capitalized to '[End]'"
    assert "(End)" in fixed_code, "'(end)' should be capitalized to '(End)'"
    assert "{End}" in fixed_code, "'{end}' should be capitalized to '{End}'"

    print("  PASSED: Reserved word 'end' was capitalized")

    # Test case 2: Subgraph 'end' should NOT be touched
    valid_flowchart = """flowchart TD
    subgraph Sub[Subgraph]
        A --> B
    end
    B --> C[Finish]"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("flowchart", valid_flowchart)

    print(f"\n  Flowchart with subgraph 'end' keyword:")
    print(f"  Is valid: {is_valid}")
    print(f"  Issues: {len(issues)}")
    # The standalone 'end' keyword for subgraph should remain
    assert "end" in fixed_code, "Subgraph 'end' keyword should remain"
    print("  PASSED: Subgraph 'end' keyword preserved")


async def test_quadrant_validator():
    """Test quadrant coordinate uniqueness validation."""
    print("\n=== Testing QuadrantChart Coordinate Validator ===")

    settings = Settings()
    validator = MermaidValidator(settings)

    # Test case 1: Overlapping coordinates
    quadrant_with_overlap = """quadrantChart
    x-axis Low --> High
    y-axis Low --> High
    quadrant-1 Q1
    quadrant-2 Q2
    quadrant-3 Q3
    quadrant-4 Q4
    Point A: [0.5, 0.5]
    Point B: [0.5, 0.5]
    Point C: [0.51, 0.52]"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("quadrantchart", quadrant_with_overlap)

    print(f"  Input has overlapping coordinates at [0.5, 0.5]")
    print(f"  Is valid (no issues): {is_valid}")
    print(f"  Issues found: {len(issues)}")
    for issue in issues:
        print(f"    - {issue}")

    # Verify coordinates were adjusted
    assert not is_valid or len(issues) > 0, "Overlapping coordinates should be detected"
    print("  PASSED: Overlapping coordinates were detected")

    # Test case 2: Well-spaced coordinates
    valid_quadrant = """quadrantChart
    x-axis Low --> High
    y-axis Low --> High
    quadrant-1 Q1
    quadrant-2 Q2
    quadrant-3 Q3
    quadrant-4 Q4
    Point A: [0.2, 0.2]
    Point B: [0.8, 0.8]
    Point C: [0.2, 0.8]
    Point D: [0.8, 0.2]"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("quadrantchart", valid_quadrant)

    print(f"\n  QuadrantChart with well-spaced coordinates:")
    print(f"  Is valid: {is_valid}")
    print(f"  Issues: {len(issues)}")
    assert is_valid, "Well-spaced coordinates should pass"
    print("  PASSED: Well-spaced coordinates passed")


async def test_gantt_validator():
    """Test simplified gantt validator - only checks milestone duration and title."""
    print("\n=== Testing Simplified Gantt Validator ===")

    settings = Settings()
    validator = MermaidValidator(settings)

    # Test case 1: Valid gantt with short task IDs (previously caused false positives)
    gantt_with_short_ids = """gantt
    dateFormat YYYY-MM-DD
    axisFormat %b
    section Planning
    Design: des, 2024-01-01, 10d
    Database: db, after des, 14d
    Integration: int, after db, 7d
    Testing: test, after int, 5d"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("gantt", gantt_with_short_ids)

    print(f"  Gantt with short task IDs: des, db, int, test")
    print(f"  Is valid (no issues): {is_valid}")
    print(f"  Issues found: {len(issues)}")
    for issue in issues:
        print(f"    - {issue}")

    # Should NOT flag short task IDs as false positives
    # Note: When Gemini API fails, is_valid may be False but issues should be empty
    # The key thing is that NO issues are detected for these valid task IDs
    assert len(issues) == 0, "Short task IDs should not generate any issues"
    # Code should be unchanged (no fixes needed)
    assert "des" in fixed_code, "Task ID 'des' should remain in code"
    assert "db" in fixed_code, "Task ID 'db' should remain in code"
    assert "int" in fixed_code, "Task ID 'int' should remain in code"
    assert "test" in fixed_code, "Task ID 'test' should remain in code"
    print("  PASSED: Short task IDs not flagged as invalid (no false positives)")

    # Test case 2: Milestone with wrong duration
    gantt_with_bad_milestone = """gantt
    dateFormat YYYY-MM-DD
    section Launch
    Release: milestone, rel, 2024-04-01, 5d"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("gantt", gantt_with_bad_milestone)

    print(f"\n  Milestone with 5d duration (should be 0d):")
    print(f"  Is valid: {is_valid}")
    print(f"  Issues found: {len(issues)}")
    for issue in issues:
        print(f"    - {issue}")

    # Should detect the milestone duration issue
    # The basic detection should flag milestone with non-zero duration
    milestone_issue_found = any("milestone" in issue.lower() and "duration" in issue.lower() for issue in issues)
    assert milestone_issue_found or "0d" in fixed_code, "Bad milestone duration should be detected or fixed"
    print("  PASSED: Invalid milestone duration detected/fixed")

    # Test case 3: Gantt with title line (should be removed)
    gantt_with_title = """gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Work
    Task: task1, 2024-01-01, 10d"""

    is_valid, fixed_code, issues = await validator.validate_and_fix("gantt", gantt_with_title)

    print(f"\n  Gantt with title line (should be flagged):")
    print(f"  Is valid: {is_valid}")
    print(f"  Issues found: {len(issues)}")
    for issue in issues:
        print(f"    - {issue}")

    # Title line should be flagged or removed from the fixed code
    title_issue_found = any("title" in issue.lower() for issue in issues)
    title_removed = "title Project Timeline" not in fixed_code
    assert title_issue_found or title_removed, "Title line should be flagged or removed"
    print("  PASSED: Title line detected/removed")


async def test_playbook_types():
    """Test that playbook has all expected diagram types."""
    print("\n=== Testing Playbook Diagram Types ===")

    from playbooks.mermaid_playbook_v3 import get_supported_types, get_diagram_spec

    supported = get_supported_types()
    print(f"  Supported types: {supported}")

    expected_types = [
        "flowchart", "erDiagram", "journey", "gantt",
        "quadrantChart", "timeline", "kanban", "pie", "mindmap"
    ]

    for dtype in expected_types:
        spec = get_diagram_spec(dtype)
        assert spec is not None, f"Missing spec for {dtype}"
        assert "complete_example" in spec, f"Missing complete_example for {dtype}"
        assert "generation_rules" in spec, f"Missing generation_rules for {dtype}"
        print(f"  {dtype}: OK (has example and rules)")

    print("  PASSED: All expected diagram types have specs")


async def main():
    print("=" * 60)
    print("  Mermaid Validator Unit Tests")
    print("=" * 60)

    try:
        await test_journey_validator()
        await test_flowchart_validator()
        await test_quadrant_validator()
        await test_gantt_validator()
        await test_playbook_types()

        print("\n" + "=" * 60)
        print("  ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n  TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
