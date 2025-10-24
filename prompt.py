"""
PRDBench CodeAgent Development and Debug Prompts
This file contains prompt templates for developing and debugging code agents.
"""

# Development prompt for initial task understanding and planning
DEVELOPMENT_PROMPT = """
Please develop a complete Python project (ID:{ID}) located at {project_path} according to the requirements specified in the project documentation (src/PRD.md), and with reference to the expected test metrics (evaluation/detailed_test_plan_en.json).

### Requirements
1. Strictly implement all functional requirements described in PRD.md, ensuring that every feature is fully realized and that no requirements are omitted.
2. Closely follow the testing schemes defined in detailed_test_plan.json, ensuring that your implementation process and interfaces fully comply with the testing specifications, so that QA testing can be carried out directly using detailed_test_plan.
3. Submit all project code and related files completely under the src/ directory, ensuring that the project structure is clear and maintainable.
4. Do not ask any intermediate questions during the development process. Complete the entire project and submit directly.
"""

# Debug prompt for troubleshooting and optimization
DEBUG_PROMPT = """
You are provided with the following resources at the {project_path}:
- The project requirements and code in src/ (including PRD. md and source code)
- The evaluation criteria and related files in evaluation/
- The development score report of code in src/ is in reports/
Please analyze the items in the score report where points were deducted, and modify the code to address these issues.  Ensure that your revised code fully complies with both the evaluation criteria and the requirements specified in PRD.md.
"""
