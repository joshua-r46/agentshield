from sqlalchemy.orm import Session

from app.models.execution_trace import ExecutionTrace


class ExecutionTraceService:
    def record_execution(
        self,
        db: Session,
        agent_id: int,
        tool: str,
        arguments: dict,
        execution_status: str,
        result: dict | None = None,
    ) -> ExecutionTrace:
        trace = ExecutionTrace(
            agent_id=agent_id,
            tool=tool,
            arguments=arguments,
            execution_status=execution_status,
            result=result,
        )

        db.add(trace)
        db.commit()
        db.refresh(trace)

        return trace

    def get_trace(
        self,
        db: Session,
        trace_id: int,
    ) -> ExecutionTrace:
        trace = db.get(ExecutionTrace, trace_id)

        if trace is None:
            raise ValueError("Execution trace not found")

        return trace