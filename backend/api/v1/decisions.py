"""
Decision Engine Endpoints

Provides:
- View autonomous decisions
- Approve/reject pending decisions
- Configure decision rules
- Decision history and analytics
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException

router = APIRouter()


from api.schemas.decisions import (
    ApproveDecisionRequest,
    Decision,
    DecisionImpact,
    DecisionListResponse,
    DecisionStatus,
    RejectDecisionRequest,
)

# Mock data
_decisions: dict[str, Decision] = {
    "dec_001": Decision(
        id="dec_001",
        title="Scale Up Database Resources",
        description="Automated recommendation to increase database capacity based on predicted load",
        domain="infrastructure",
        status=DecisionStatus.PENDING,
        impact=DecisionImpact.MEDIUM,
        confidence=0.87,
        reasoning="Analysis shows 85% probability of exceeding current capacity in next 48 hours",
        options=[
            {"name": "Scale to 16GB RAM", "cost": 200, "benefit": 500},
            {"name": "Scale to 32GB RAM", "cost": 400, "benefit": 800}
        ],
        selected_option={"name": "Scale to 16GB RAM", "cost": 200, "benefit": 500},
        cost_estimate=200,
        expected_benefit=500,
        created_at=datetime.now(),
        requires_approval=True
    ),
    "dec_002": Decision(
        id="dec_002",
        title="Activate Promotional Campaign",
        description="Launch targeted promotion for at-risk customers",
        domain="marketing",
        status=DecisionStatus.EXECUTED,
        impact=DecisionImpact.LOW,
        confidence=0.92,
        reasoning="ML model identified 150 high-value customers with elevated churn risk",
        options=[
            {"name": "10% discount", "cost": 1500, "benefit": 8000},
            {"name": "Free month", "cost": 3000, "benefit": 12000}
        ],
        selected_option={"name": "10% discount", "cost": 1500, "benefit": 8000},
        cost_estimate=1500,
        expected_benefit=8000,
        created_at=datetime(2024, 1, 1),
        decided_at=datetime(2024, 1, 1),
        executed_at=datetime(2024, 1, 1),
        requires_approval=False
    )
}


@router.get("", response_model=DecisionListResponse, summary="List decisions")
async def list_decisions(
    status_filter: DecisionStatus | None = None,
    domain: str | None = None,
    page: int = 1,
    page_size: int = 20
):
    """List all decisions with optional filtering."""
    decisions = list(_decisions.values())

    if status_filter:
        decisions = [d for d in decisions if d.status == status_filter]
    if domain:
        decisions = [d for d in decisions if d.domain == domain]

    pending_count = len([d for d in _decisions.values() if d.status == DecisionStatus.PENDING])

    return DecisionListResponse(
        decisions=decisions,
        total=len(decisions),
        pending_count=pending_count
    )


@router.get("/{decision_id}", summary="Get decision details")
async def get_decision(decision_id: str):
    """Get a specific decision by ID."""
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found")
    return _decisions[decision_id]


@router.post("/{decision_id}/approve", summary="Approve decision")
async def approve_decision(decision_id: str, request: ApproveDecisionRequest):
    """Approve a pending decision."""
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision = _decisions[decision_id]
    if decision.status != DecisionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Decision is not pending")

    decision.status = DecisionStatus.APPROVED
    decision.decided_at = datetime.now()

    return {"message": "Decision approved", "decision": decision}


@router.post("/{decision_id}/reject", summary="Reject decision")
async def reject_decision(decision_id: str, request: RejectDecisionRequest):
    """Reject a pending decision."""
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail="Decision not found")

    decision = _decisions[decision_id]
    if decision.status != DecisionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Decision is not pending")

    decision.status = DecisionStatus.REJECTED
    decision.decided_at = datetime.now()

    return {"message": "Decision rejected", "reason": request.reason, "decision": decision}


@router.get("/analytics/summary", summary="Decision analytics")
async def get_decision_analytics():
    """Get decision analytics summary."""
    decisions = list(_decisions.values())

    return {
        "total_decisions": len(decisions),
        "by_status": {
            "pending": len([d for d in decisions if d.status == DecisionStatus.PENDING]),
            "approved": len([d for d in decisions if d.status == DecisionStatus.APPROVED]),
            "rejected": len([d for d in decisions if d.status == DecisionStatus.REJECTED]),
            "executed": len([d for d in decisions if d.status == DecisionStatus.EXECUTED])
        },
        "by_domain": {
            "infrastructure": len([d for d in decisions if d.domain == "infrastructure"]),
            "marketing": len([d for d in decisions if d.domain == "marketing"]),
            "operations": len([d for d in decisions if d.domain == "operations"])
        },
        "average_confidence": sum(d.confidence for d in decisions) / len(decisions) if decisions else 0,
        "total_cost_savings": sum(d.expected_benefit - d.cost_estimate for d in decisions if d.status == DecisionStatus.EXECUTED)
    }
