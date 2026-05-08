from langgraph.graph import StateGraph, END
from src.models import AgentState, EscalationStage
from src.agent import nodes

def build_agent_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("ingest", nodes.ingest_node)
    workflow.add_node("classify", nodes.classify_node)
    workflow.add_node("generate", nodes.generate_email_node)
    workflow.add_node("send", nodes.send_email_node)
    workflow.add_node("flag_legal", nodes.flag_legal_node)
    workflow.add_node("audit", nodes.audit_node)
    workflow.add_node("update_count", nodes.update_follow_up_count_node)
    
    # Entry
    workflow.set_entry_point("ingest")
    
    # Edges
    workflow.add_edge("ingest", "classify")
    workflow.add_conditional_edges("classify", _route_by_stage, {
        "generate": "generate",
        "flag_legal": "flag_legal",
        "skip": END,
    })
    workflow.add_edge("generate", "send")
    workflow.add_edge("send", "audit")
    workflow.add_edge("flag_legal", "audit")
    workflow.add_edge("audit", "update_count")
    workflow.add_edge("update_count", END)
    
    return workflow.compile()

def _route_by_stage(state: AgentState) -> str:
    record = state.current_record
    if not record or record.stage == EscalationStage.NOT_DUE:
        return "skip"
    elif record.stage == EscalationStage.LEGAL:
        return "flag_legal"
    else:
        return "generate"
