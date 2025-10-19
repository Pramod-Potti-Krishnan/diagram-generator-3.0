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
        diagram_type = diagram_type.lower()
        
        # Route to specific validators
        if diagram_type == "gantt":
            return await self._validate_gantt_with_ai(mermaid_code)
        else:
            # Pass-through for other diagram types for now
            logger.debug(f"No validation rules for {diagram_type}, passing through")
            return True, mermaid_code, []
    
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
        
        Args:
            code: Gantt chart code
            
        Returns:
            List of detected issues
        """
        issues = []
        lines = code.split('\n')
        
        # Valid status tags
        valid_status_tags = {'done', 'active', 'crit', 'milestone'}
        
        # Common invalid tags that are actually task IDs
        common_invalid_tags = {'des', 'db', 'int', 'test', 'unit', 'bug', 
                              'stage', 'prep', 'support', 'dev', 'impl'}
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines, comments, and headers
            if not line or line.startswith('%') or line.startswith('gantt'):
                continue
            if line.startswith('title') or line.startswith('dateFormat'):
                continue
            if line.startswith('axisFormat') or line.startswith('excludes'):
                continue
            if line.startswith('section'):
                continue
            
            # Check task lines
            if ':' in line:
                # Extract the part after the colon
                parts = line.split(':', 1)
                if len(parts) == 2:
                    task_def = parts[1].strip()
                    
                    # Split by comma to get components
                    components = [c.strip() for c in task_def.split(',')]
                    
                    if len(components) >= 3:
                        # Could be: statusTag, taskId, dependency, duration
                        # Or: taskId, dependency, duration
                        
                        first_component = components[0]
                        
                        # Check if first component looks like an invalid status tag
                        if first_component in common_invalid_tags:
                            issues.append(f"Line {i}: Invalid status tag '{first_component}' - should be task ID only")
                        
                        # Check for milestone with non-zero duration
                        if 'milestone' in components[0:2]:
                            # Find duration (last component)
                            if len(components) >= 3:
                                duration = components[-1].strip()
                                if duration != '0d' and duration != '0':
                                    issues.append(f"Line {i}: Milestone should have 0d duration, found '{duration}'")
                        
                        # Check for multiple dependencies with comma (might be wrong)
                        for j, comp in enumerate(components):
                            if 'after' in comp and j < len(components) - 1:
                                # Check if next component looks like a task ID (not duration)
                                next_comp = components[j + 1]
                                if not re.match(r'^\d+[dhwms]?$', next_comp):
                                    # Might be wrong comma-separated dependencies
                                    issues.append(f"Line {i}: Possible incorrect multiple dependency syntax")
        
        return issues
    
    def _apply_basic_gantt_fixes(self, code: str) -> str:
        """
        Apply basic regex-based fixes for common Gantt issues.
        
        Args:
            code: Gantt chart code
            
        Returns:
            Fixed code
        """
        lines = code.split('\n')
        fixed_lines = []
        
        # Common invalid status tags to remove
        invalid_tags = {'des', 'db', 'int', 'test', 'unit', 'bug', 
                       'stage', 'prep', 'support', 'dev', 'impl'}
        
        for line in lines:
            original_line = line
            
            # Skip non-task lines
            if not ':' in line or line.strip().startswith('%'):
                fixed_lines.append(line)
                continue
            
            # Try to fix task lines
            parts = line.split(':', 1)
            if len(parts) == 2:
                task_name = parts[0]
                task_def = parts[1].strip()
                
                # Split task definition
                components = [c.strip() for c in task_def.split(',')]
                
                if len(components) >= 3:
                    first = components[0]
                    
                    # Remove invalid status tags
                    if first in invalid_tags:
                        # Remove the invalid tag, making the next component the task ID
                        components = components[1:]
                        task_def = ', '.join(components)
                        line = f"{task_name}:{task_def}"
                        logger.debug(f"Fixed invalid status tag: {first}")
                    
                    # Fix milestone duration
                    if 'milestone' in components[0:2]:
                        # Ensure last component is 0d
                        if len(components) >= 3:
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
        
        # Check for removed invalid status tags
        invalid_tags = {'des', 'db', 'int', 'test', 'unit', 'bug', 
                       'stage', 'prep', 'support', 'dev', 'impl'}
        
        for tag in invalid_tags:
            # Check if tag was in original but not in fixed (as a status position)
            pattern = f':{tag},'
            if pattern in original and pattern not in fixed:
                fixes.append(f"Removed invalid status tag '{tag}'")
        
        # Check for milestone duration fixes
        if ':milestone' in original:
            if '1d' in original and '0d' in fixed:
                fixes.append("Fixed milestone duration from 1d to 0d")
        
        # Generic change detection
        if not fixes:
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