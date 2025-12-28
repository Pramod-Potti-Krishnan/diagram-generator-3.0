"""
Mermaid Syntax Validator using Gemini-2.5-Flash
==============================================

Intelligently validates and fixes Mermaid diagram syntax issues,
with initial focus on Gantt chart problems.

Uses Gemini-2.5-Flash for intelligent syntax correction.
"""

import re
import asyncio
from typing import Dict, Any, List, Tuple, Optional
import google.generativeai as genai
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MermaidValidator:
    """
    Validates and fixes Mermaid diagram syntax using Gemini AI.
    
    Initially focused on Gantt chart validation, extensible to other diagram types.
    """
    
    def __init__(self, settings):
        """
        Initialize the validator with Gemini model.
        
        Args:
            settings: Application settings with Google API key
        """
        self.settings = settings
        self.model = None
        
        # Initialize Gemini if API key is available
        if settings.google_api_key:
            try:
                genai.configure(api_key=settings.google_api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
                logger.info("✅ MermaidValidator initialized with Gemini-2.5-Flash")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini for validation: {e}")
                self.model = None
        else:
            logger.warning("No Google API key - MermaidValidator running in basic mode")
    
    async def validate_and_fix(
        self,
        diagram_type: str,
        mermaid_code: str
    ) -> Tuple[bool, str, List[str]]:
        """
        Validates and fixes Mermaid code based on diagram type.

        Args:
            diagram_type: Type of Mermaid diagram (gantt, flowchart, etc.)
            mermaid_code: The Mermaid code to validate

        Returns:
            Tuple of (is_valid, fixed_code, issues_found)
        """

        # Normalize diagram type
        diagram_type_lower = diagram_type.lower()

        # Route to specific validators
        validators = {
            "gantt": self._validate_gantt_with_ai,
            "journey": self._validate_journey,
            "flowchart": self._validate_flowchart,
            "quadrantchart": self._validate_quadrant,
        }

        if diagram_type_lower in validators:
            return await validators[diagram_type_lower](mermaid_code)

        # Pass-through for other diagram types
        logger.debug(f"No validation rules for {diagram_type}, passing through")
        return True, mermaid_code, []

    async def _validate_journey(self, mermaid_code: str) -> Tuple[bool, str, List[str]]:
        """
        Validate and fix journey diagram scores.

        Journey scores MUST be 0-5, but LLM sometimes generates 6, 7, 8, 10, etc.

        Args:
            mermaid_code: Journey diagram code

        Returns:
            Tuple of (is_valid, fixed_code, issues_found)
        """
        issues = []
        fixed_code = mermaid_code

        # Pattern: "task description: SCORE: Actor"
        # Example: "Search for product: 5: Customer"
        score_pattern = r':\s*(\d+)\s*:'

        for match in re.finditer(score_pattern, mermaid_code):
            score = int(match.group(1))
            if score > 5:
                issues.append(f"Score {score} exceeds maximum of 5 - clamping")
                # Map scores > 5 to valid range
                # 10 -> 5, 8-9 -> 4, 6-7 -> 3
                if score >= 9:
                    new_score = 5
                elif score >= 7:
                    new_score = 4
                else:
                    new_score = 3
                # Replace the score in the code
                old_text = f": {score}:"
                new_text = f": {new_score}:"
                fixed_code = fixed_code.replace(old_text, new_text, 1)
                logger.debug(f"Fixed journey score: {score} -> {new_score}")

        if issues:
            logger.info(f"Journey validator fixed {len(issues)} score issues")

        return len(issues) == 0, fixed_code, issues

    async def _validate_flowchart(self, mermaid_code: str) -> Tuple[bool, str, List[str]]:
        """
        Validate and fix flowchart reserved word issues.

        The word 'end' is reserved for closing subgraphs, so it can't be used
        as bare node text. Fix by capitalizing to 'End'.

        Args:
            mermaid_code: Flowchart diagram code

        Returns:
            Tuple of (is_valid, fixed_code, issues_found)
        """
        issues = []
        fixed_code = mermaid_code

        # Fix bare "end" as node text (not end of subgraph)
        # Pattern: node[end] or node(end) or node{end}
        # But NOT "    end" (subgraph close) which is just "end" on its own line

        # Pattern for node with "end" as text
        patterns = [
            (r'(\w+)\[end\]', r'\1[End]', 'end in square brackets'),
            (r'(\w+)\(end\)', r'\1(End)', 'end in rounded brackets'),
            (r'(\w+)\{end\}', r'\1{End}', 'end in curly brackets'),
            (r'(\w+)\[\(end\)\]', r'\1[(End)]', 'end in stadium'),
        ]

        for pattern, replacement, desc in patterns:
            if re.search(pattern, fixed_code, re.IGNORECASE):
                issues.append(f'Reserved word "end" used as node text ({desc})')
                fixed_code = re.sub(pattern, replacement, fixed_code, flags=re.IGNORECASE)
                logger.debug(f"Fixed flowchart reserved word: {desc}")

        if issues:
            logger.info(f"Flowchart validator fixed {len(issues)} reserved word issues")

        return len(issues) == 0, fixed_code, issues

    async def _validate_quadrant(self, mermaid_code: str) -> Tuple[bool, str, List[str]]:
        """
        Validate quadrant chart coordinate uniqueness.

        LLM sometimes generates points with duplicate or very close coordinates,
        which causes rendering issues. Nudge overlapping points apart.

        Args:
            mermaid_code: QuadrantChart diagram code

        Returns:
            Tuple of (is_valid, fixed_code, issues_found)
        """
        issues = []
        fixed_code = mermaid_code

        # Pattern: "Point Name: [x, y]"
        point_pattern = r'([^:\n]+):\s*\[(\d+\.?\d*),\s*(\d+\.?\d*)\]'

        points = []
        for match in re.finditer(point_pattern, mermaid_code):
            name = match.group(1).strip()
            x = float(match.group(2))
            y = float(match.group(3))
            points.append({
                'name': name,
                'x': x,
                'y': y,
                'original': match.group(0)
            })

        # Check for coordinate conflicts (within 0.08)
        MIN_DISTANCE = 0.08
        used_coords = []
        adjustments_made = []

        for point in points:
            x, y = point['x'], point['y']
            conflict = True
            nudge_count = 0

            while conflict and nudge_count < 10:
                conflict = False
                for (ux, uy) in used_coords:
                    if abs(x - ux) < MIN_DISTANCE and abs(y - uy) < MIN_DISTANCE:
                        conflict = True
                        issues.append(f"Point '{point['name']}' too close to another point")
                        # Nudge the coordinate slightly
                        x = min(0.95, x + 0.1)
                        y = min(0.95, y + 0.1)
                        nudge_count += 1
                        break

            used_coords.append((x, y))

            if x != point['x'] or y != point['y']:
                adjustments_made.append({
                    'old': point['original'],
                    'new': f"{point['name']}: [{x:.2f}, {y:.2f}]"
                })

        # Apply adjustments
        for adj in adjustments_made:
            fixed_code = fixed_code.replace(adj['old'], adj['new'], 1)
            logger.debug(f"Fixed quadrant coordinates: {adj['old']} -> {adj['new']}")

        if issues:
            logger.info(f"Quadrant validator fixed {len(adjustments_made)} coordinate conflicts")

        return len(issues) == 0, fixed_code, issues
    
    async def _validate_gantt_with_ai(self, code: str) -> Tuple[bool, str, List[str]]:
        """
        Use Gemini to intelligently fix Gantt chart syntax issues.
        
        Args:
            code: Gantt chart Mermaid code
            
        Returns:
            Tuple of (is_valid, fixed_code, issues_found)
        """
        
        # First, try basic validation
        basic_issues = self._detect_gantt_issues(code)
        
        if not basic_issues and not self.model:
            # No issues detected and no AI available
            return True, code, []
        
        if not self.model:
            # Issues detected but no AI to fix them
            logger.warning("Issues detected but Gemini not available for fixing")
            # Try basic regex fixes
            fixed_code = self._apply_basic_gantt_fixes(code)
            return False, fixed_code, basic_issues
        
        # Use Gemini to fix the code
        try:
            prompt = self._build_gantt_fix_prompt(code, basic_issues)
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            fixed_code = self._extract_mermaid_from_response(response.text)
            
            if not fixed_code:
                logger.warning("Gemini didn't return valid Mermaid code")
                # Fall back to basic fixes
                fixed_code = self._apply_basic_gantt_fixes(code)
            
            # Detect what was actually fixed
            final_issues = self._compare_and_list_fixes(code, fixed_code)
            
            # Check if fixed code still has issues
            remaining_issues = self._detect_gantt_issues(fixed_code)
            
            if remaining_issues:
                logger.warning(f"Some issues remain after fix: {remaining_issues}")
                return False, fixed_code, final_issues + remaining_issues
            
            return len(final_issues) == 0, fixed_code, final_issues
            
        except Exception as e:
            logger.error(f"Gemini validation failed: {e}")
            # Fall back to basic fixes
            fixed_code = self._apply_basic_gantt_fixes(code)
            return False, fixed_code, basic_issues
    
    def _build_gantt_fix_prompt(self, code: str, detected_issues: List[str]) -> str:
        """
        Build a prompt for Gemini to fix Gantt chart syntax.
        
        Args:
            code: The Mermaid code to fix
            detected_issues: List of detected issues
            
        Returns:
            Prompt string for Gemini
        """
        
        issues_text = "\n".join(f"- {issue}" for issue in detected_issues) if detected_issues else "Check for any syntax issues"
        
        prompt = f"""Fix this Gantt chart Mermaid syntax. 

CRITICAL RULES FOR GANTT CHARTS:

1. VALID STATUS TAGS (only these 4 are allowed):
   - done: Completed tasks
   - active: Currently in progress
   - crit: Critical path tasks
   - milestone: Zero-duration milestones
   
   INVALID tags that must be removed or fixed:
   des, db, int, test, unit, bug, stage, prep, support, etc.

2. CORRECT TASK SYNTAX:
   Without status: "Task Name :taskId, dependency, duration"
   With status: "Task Name :statusTag, taskId, dependency, duration"
   
   Examples:
   ✅ CORRECT: "Design :design1, after req, 10d"
   ✅ CORRECT: "Backend :crit, back1, after design1, 14d"
   ❌ WRONG: "Design :des, design1, after req, 10d" (des is NOT a valid status!)

3. MULTIPLE DEPENDENCIES:
   Use SPACE separation (not comma): "after task1 task2 task3"
   ✅ CORRECT: "Integration :int1, after front back, 5d"
   ❌ WRONG: "Integration :int1, after front, back, 5d"

4. MILESTONES:
   Must have 0d duration
   ✅ CORRECT: "Release :milestone, rel1, after test, 0d"
   ❌ WRONG: "Release :milestone, rel1, after test, 1d"

DETECTED ISSUES:
{issues_text}

INPUT CODE:
```mermaid
{code}
```

Fix all syntax errors and return ONLY the corrected Mermaid code.
Do not add any explanations or markdown formatting.
Just return the fixed gantt chart code starting with 'gantt'."""
        
        return prompt
    
    def _detect_gantt_issues(self, code: str) -> List[str]:
        """
        Detect common Gantt chart syntax issues.

        SIMPLIFIED to reduce false positives. Only checks for:
        1. Milestone with non-zero duration (definite error)
        2. Title line when slide already has title (remove it)

        Does NOT check for "invalid status tags" as this causes too many false positives
        when task IDs happen to be short (des, db, int, test, etc.)

        Args:
            code: Gantt chart code

        Returns:
            List of detected issues
        """
        issues = []
        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            line = line.strip()

            # Skip empty lines, comments
            if not line or line.startswith('%'):
                continue

            # Check for title line (should be removed - slide has its own title)
            if line.startswith('title ') or line == 'title':
                issues.append(f"Line {i}: Title line should be removed - slide already has title")
                continue

            # Skip header lines
            if line.startswith('gantt') or line.startswith('dateFormat'):
                continue
            if line.startswith('axisFormat') or line.startswith('excludes'):
                continue
            if line.startswith('section'):
                continue

            # Check task lines for milestone duration issue
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    task_def = parts[1].strip()
                    components = [c.strip() for c in task_def.split(',')]

                    # Check for milestone with non-zero duration
                    # Milestone can be in first or second position
                    if 'milestone' in components[:2]:
                        # Find duration (last component)
                        if len(components) >= 3:
                            duration = components[-1].strip()
                            # Valid durations for milestone: 0d, 0
                            if duration != '0d' and duration != '0':
                                issues.append(f"Line {i}: Milestone must have 0d duration, found '{duration}'")

        return issues
    
    def _apply_basic_gantt_fixes(self, code: str) -> str:
        """
        Apply basic regex-based fixes for common Gantt issues.

        SIMPLIFIED to only fix definite issues:
        1. Remove title lines
        2. Fix milestone durations to 0d

        Args:
            code: Gantt chart code

        Returns:
            Fixed code
        """
        lines = code.split('\n')
        fixed_lines = []

        for line in lines:
            stripped = line.strip()

            # Remove title lines
            if stripped.startswith('title ') or stripped == 'title':
                logger.debug("Removed title line from Gantt chart")
                continue

            # Skip non-task lines
            if ':' not in line or stripped.startswith('%'):
                fixed_lines.append(line)
                continue

            # Try to fix task lines
            parts = line.split(':', 1)
            if len(parts) == 2:
                task_name = parts[0]
                task_def = parts[1].strip()

                # Split task definition
                components = [c.strip() for c in task_def.split(',')]

                # Fix milestone duration
                if len(components) >= 3 and 'milestone' in components[:2]:
                    # Ensure last component is 0d
                    if components[-1] not in ('0d', '0'):
                        components[-1] = '0d'
                        task_def = ', '.join(components)
                        line = f"{task_name}:{task_def}"
                        logger.debug("Fixed milestone duration to 0d")

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)
    
    def _extract_mermaid_from_response(self, response_text: str) -> Optional[str]:
        """
        Extract Mermaid code from Gemini response.
        
        Args:
            response_text: Response from Gemini
            
        Returns:
            Extracted Mermaid code or None
        """
        # Remove any markdown formatting
        text = response_text.strip()
        
        # Remove ```mermaid and ``` if present
        if '```mermaid' in text:
            text = text.split('```mermaid')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        # Ensure it starts with a diagram type
        text = text.strip()
        if text.startswith('gantt') or text.startswith('flowchart') or text.startswith('graph'):
            return text
        
        # Try to find the diagram in the text
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('gantt'):
                return '\n'.join(lines[i:])
        
        return None
    
    def _compare_and_list_fixes(self, original: str, fixed: str) -> List[str]:
        """
        Compare original and fixed code to list what was changed.

        Args:
            original: Original code
            fixed: Fixed code

        Returns:
            List of fixes applied
        """
        if original.strip() == fixed.strip():
            return []

        fixes = []

        # Check for removed title line
        if 'title ' in original.lower() and 'title ' not in fixed.lower():
            fixes.append("Removed title line")

        # Check for milestone duration fixes
        if ':milestone' in original or 'milestone,' in original:
            # Check if any non-zero duration was fixed to 0d
            import re
            orig_milestones = re.findall(r'milestone.*?,\s*(\d+[dhwm]?)', original)
            for dur in orig_milestones:
                if dur not in ('0d', '0'):
                    fixes.append(f"Fixed milestone duration from {dur} to 0d")
                    break

        # Generic change detection
        if not fixes and original.strip() != fixed.strip():
            fixes.append("Applied syntax corrections")

        return fixes


# Utility function for standalone validation
async def validate_mermaid_code(
    diagram_type: str, 
    code: str, 
    api_key: Optional[str] = None
) -> Tuple[bool, str, List[str]]:
    """
    Standalone function to validate Mermaid code.
    
    Args:
        diagram_type: Type of diagram
        code: Mermaid code to validate
        api_key: Optional Google API key
        
    Returns:
        Tuple of (is_valid, fixed_code, issues)
    """
    from config.settings import Settings
    
    settings = Settings()
    if api_key:
        settings.google_api_key = api_key
    
    validator = MermaidValidator(settings)
    return await validator.validate_and_fix(diagram_type, code)