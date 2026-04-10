"""
BRD Generator Tool for AURA
Generates Business Requirements Document from user ideas
Based on enterprise analyst prompt structure
"""

BRD_TEMPLATE = """
# Business Requirements Document (BRD)

## 1. Project Overview
[Brief description of the project]

## 2. Business Objectives
- Primary goal:
- Secondary goals:
- Expected outcomes:

## 3. Stakeholders
- Primary users:
- Decision makers:
- External parties:

## 4. Functional Requirements
### 4.1 Core Features
- Feature 1:
- Feature 2:
- Feature 3:

### 4.2 User Interactions
- User action 1:
- User action 2:

### 4.3 Data Requirements
- Input data:
- Output data:
- Storage needs:

## 5. Non-Functional Requirements
- Performance:
- Security:
- Scalability:
- Reliability:

## 6. Assumptions & Constraints
- Assumptions:
- Constraints:
- Dependencies:

## 7. Success Metrics
- KPI 1:
- KPI 2:
- KPI 3:

## 8. Timeline & Budget (Optional)
- Estimated duration:
- Budget range:
- Resource requirements:
"""


def generate_brd(user_idea: str) -> str:
    """
    Generate a BRD from user idea.

    Usage:
    - "create brd for e-commerce website"
    - "generate BRD for inventory management system"
    - "I want to build a food delivery app"
    """
    if not user_idea or len(user_idea.strip()) < 5:
        return "Please provide more details about your project idea."

    prompt = f"""You are a Senior Enterprise Business Analyst.
Generate a professional Business Requirements Document (BRD) for this project idea.

USER'S IDEA:
{user_idea}

Generate a complete BRD using this structure:

{BRD_TEMPLATE}

Be specific and detailed. Fill in realistic content based on the user's idea.
Write in professional business language.
"""
    return prompt
