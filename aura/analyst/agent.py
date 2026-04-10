from pathlib import Path
import uuid
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import ToolContext, FunctionTool
from google.adk.skills import load_skill_from_dir
from google.adk.tools import skill_toolset

from agents.analyst.knowledge_base import knowledge_base
from agents.lite_llm import get_llm
from agents.workflow_state.agent import validate_project_state_tool
from agents.workflow_state.step_signal_tools import notify_step_waiting, notify_step_completed
from agents.workflow_state.artifact_registry import record_artifact_to_session
from api.routes.models import Project, ProjectArtifact, ProjectTopic
from api.routes.database import SessionLocal
from api.routes.context import current_request_context

load_dotenv()

BASE_DIR = Path(__file__).parent
llm_model = "gemini-2.5-flash"  # Using a specific Gemini model for better performance on structured tasks
# llm_model = get_llm("ANALYST_MODEL")






def create_brd_document(brd_content: str, tool_context: ToolContext) -> str:
    """
    Saves the finalized BRD document to disk and syncs the record to the database.

    AUTOMATIC TRIGGER: Call this tool automatically IMMEDIATELY after outputting
    the full BRD response to the user. Do NOT wait for user permission.

    DO NOT call this tool for:
    - BRD section edits or refinements
    - General questions or clarifications
    - Greeting messages or out-of-scope requests

    Path (with API context): docs/<user_id>/<project_uuid>/<session_uuid>/BRD.md
    Path (ADK web UI / no context): docs/BRD.md
    """
    try:
        ctx = current_request_context.get()
        PROJECT_ROOT = Path(__file__).resolve().parents[2]

        # --- Session-scoped path (API flow) ---
        if ctx and ctx.get("user_id") and ctx.get("project_id") and ctx.get("session_id"):
            user_id = ctx.get("user_id")
            project_uuid = ctx.get("project_id")
            session_uuid = ctx.get("session_id")

            relative_path = Path("docs") / str(user_id) / str(project_uuid) / str(session_uuid) / "BRD.md"
            file_path = PROJECT_ROOT / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(brd_content, encoding="utf-8")

            # DB sync
            try:
                with SessionLocal() as db:
                    topic = db.query(ProjectTopic).join(Project).filter(
                        ProjectTopic.project_topic_uuid == session_uuid,
                        Project.project_uuid == project_uuid
                    ).first()
                    if topic:
                        existing = db.query(ProjectArtifact).filter(
                            ProjectArtifact.topic_id == topic.id,
                            ProjectArtifact.file_name == "BRD.md"
                        ).first()
                        if not existing:
                            db.add(ProjectArtifact(
                                project_artifact_uuid=str(uuid.uuid4()),
                                project_id=topic.project_id,
                                topic_id=topic.id,
                                file_name="BRD.md",
                                file_path=relative_path.as_posix()
                            ))
                        else:
                            existing.file_path = str(file_path)
                        db.commit()
                        print(f" DB Record synced: ID {topic.id}")
            except Exception as db_err:
                print(f"[BRD] DB sync skipped: {db_err}")

        else:
            # --- Fallback path (ADK web UI / no context) ---
            relative_path = Path("docs") / "BRD.md"
            file_path = PROJECT_ROOT / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(brd_content, encoding="utf-8")

        # Register in session.state via ToolContext (ADK persists automatically)
        record_artifact_to_session(
            artifact_name="brd.md",
            produced_by="AnalystAgent",
            tool_context=tool_context,
            file_path=relative_path.as_posix(),
            action="create_brd",
        )

        return f"✅ BRD saved to {file_path}."

    except Exception as e:
        return f"Error saving BRD: {str(e)}"
   
def return_to_orchestrator(tool_context: ToolContext) -> str:
    """
    Returns conversational control back to the main workflow orchestrator.
    Call this tool immediately after completing your work when you are in [AUTOMATED PLAN] mode.
    """
    tool_context.actions.transfer_to_agent = "workflowOrchestration"
    return "Transferred control to workflowOrchestration."


brd_generation_skill = load_skill_from_dir(BASE_DIR / "skills" / "brd-generation")
analyst_skill_toolset = skill_toolset.SkillToolset(skills=[brd_generation_skill])

analyst_agent = Agent(
    name="AnalystAgent",
    model=llm_model,
    description="Senior Business Analyst – BRD Generator",
    instruction=(BASE_DIR / "prompts/analyst_new_prompt.md").read_text(),
    tools=[
        analyst_skill_toolset,
        FunctionTool(func=knowledge_base),
        FunctionTool(func=create_brd_document),
        validate_project_state_tool,
        FunctionTool(func=return_to_orchestrator),
        FunctionTool(func=notify_step_waiting),
        FunctionTool(func=notify_step_completed),
    ],
    output_key="analyst_output",
)

root_agent = analyst_agent
