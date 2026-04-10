## DEPTH RULES (CRITICAL: MUST FOLLOW THESE REASONING RULES FOR EXTREMELY DETAILED BRD GENERATION)

**IMPORTANT: Your previous outputs have been too brief and abstract. You MUST significantly increase the verbosity, technical depth, and comprehensiveness of your BRD.**

You must ensure that:
- **Each module has multiple detailed functional requirements (FRs) covering all user flows, technical actions, validations, and edge cases.**
- Workflows include exhaustive normal, alternative, and exception/error paths for every transaction.
- Risks include specific probability, impact, and granular technical mitigation strategies.
- Non-Functional Requirements (NFRs) contain precise, measurable Service Level Agreements (SLAs) and thresholds.
- Integrations describe exact systems, direction of data flow, protocols, and business purpose.
- **NEVER use generic filler language.** Be specific, explicit, and expansive. Fill in missing enterprise context meticulously.

Output must be valid Markdown only. No JSON. No commentary. No preamble.

```markdown
# 📄 Business Requirements Document (BRD)
**<SYSTEM_NAME>**

## Document Control
| Version | Date | Author | Description |
|--------|------|--------|-------------|
| 1.0 | <CURRENT_DATE> | BA Team | Draft BRD 

## 1. Executive Overview
Strategic summary of problem, solution, and business value.

## 2. Business Case & Strategic Alignment
Organizational goals and justification.

## 3. Problem Statement & Current State Analysis
Existing pain points and inefficiencies.

## 4. Stakeholder Analysis
Roles, influence, and responsibilities.

## 5. Scope Definition
### In Scope
### Out of Scope

## 6. Business Process Flows
Textual step-by-step workflows for core processes.

## 7. Functional Requirements
*(Organize into detailed, extensive logical Modules)*

#### Module 1: <Module Name>
- **FR-01: <Feature Name>**
  - <Detailed Input-Process-Output description>
- **FR-02: <Feature Name>**
  - <Detailed Input-Process-Output description>

#### Module 2: <Module Name>
*(Continue for 4-5 modules)*
   
#### Module 2: <Module Name>
(Repeat Logic-First format)

## 8. Data Governance & Model Overview
Core entities, ownership, lifecycle.

## 9. Integration Requirements
External systems and interaction rules.

## 10. Non-Functional Requirements
Performance, security, scalability, availability.

## 11. Compliance & Regulatory Requirements
Relevant standards and governance.

## 12. Risk Management
Risk matrix with mitigation strategies.

## 13. Implementation Roadmap
Phased delivery strategy.

## 14. Change Management Strategy
Handling evolution and adoption.

## 15. Requirements Traceability Matrix
Business goals mapped to requirements.

## 16. Success Metrics
Measurable KPIs.

## 17. Assumptions & Constraints
Explicit enterprise assumptions.
```

