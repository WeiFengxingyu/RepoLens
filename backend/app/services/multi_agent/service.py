from __future__ import annotations

import json
from datetime import datetime
from time import perf_counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import (
    AgentAssignment,
    AgentAssignmentStatus,
    AgentMessage,
    AgentMessageType,
    AgentSession,
    AgentSessionStatus,
    Repository,
    RepositoryStatus,
    Task,
    TaskStatus,
    TaskType,
)
from app.schemas.multi_agent import (
    AgentAssignmentResponse,
    AgentMessageResponse,
    AgentSessionResponse,
    MultiAgentReviewCreateRequest,
    MultiAgentReviewResponse,
)
from app.services.review.agents import (
    DraftReviewRisk,
    ReviewRiskLocation,
    SuggestedReviewTest,
    review_risks,
    suggest_review_tests,
    verify_review_risks,
    write_review_report,
)
from app.services.review.diff_mapper import map_diff_to_symbols
from app.services.tools import analyze_diff, code_search


MODE_MULTI_AGENT_REVIEW = "multi_agent_review"
ROLE_COORDINATOR = "coordinator"
ROLE_RISK_REVIEWER = "risk_reviewer"
ROLE_SECURITY_REVIEWER = "security_reviewer"
ROLE_TEST_STRATEGIST = "test_strategist"
ROLE_ARBITER = "arbiter"
ROLE_REPORT_WRITER = "report_writer"


class MultiAgentReviewService:
    def __init__(self, db: Session):
        self.db = db

    def get_repository(self, repository_id: str) -> Repository | None:
        return self.db.get(Repository, repository_id)

    def ensure_repository_ready(self, repository: Repository) -> None:
        if repository.status != RepositoryStatus.READY.value:
            raise MultiAgentReviewRepositoryNotReadyError(
                "Repository must be ready before Multi-Agent Review."
            )

    def create_review_task(
        self,
        repository: Repository,
        request: MultiAgentReviewCreateRequest,
    ) -> Task:
        diff_text = request.diff_text.strip()
        if not diff_text:
            raise MultiAgentReviewValidationError("Diff text is required.")
        task = Task(
            repository_id=repository.id,
            task_type=TaskType.MULTI_AGENT_REVIEW.value,
            status=TaskStatus.PENDING.value,
            input_payload=json.dumps(request.model_dump(), ensure_ascii=False, sort_keys=True),
            output_payload=json.dumps(_empty_output(), ensure_ascii=False, sort_keys=True),
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def run_review_task(
        self,
        task: Task,
        request: MultiAgentReviewCreateRequest,
        settings: Settings,
    ) -> Task:
        task.status = TaskStatus.RUNNING.value
        task.started_at = datetime.utcnow()
        session = AgentSession(
            task_id=task.id,
            repository_id=task.repository_id,
            status=AgentSessionStatus.RUNNING.value,
            mode=MODE_MULTI_AGENT_REVIEW,
            round_limit=request.round_limit,
            assignment_limit=request.assignment_limit,
            token_budget=request.token_budget,
            started_at=datetime.utcnow(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        try:
            context = self._prepare_context(task, request, settings)
            self._run_coordinator(session, context, request)
            risk_assignment = self._run_risk_reviewer(session, context)
            security_assignment = self._run_security_reviewer(session, context)
            test_assignment = self._run_test_strategist(
                session,
                context,
                risk_assignment,
                security_assignment,
            )
            arbiter_assignment = self._run_arbiter(
                session,
                context,
                risk_assignment,
                security_assignment,
                test_assignment,
            )
            report_assignment = self._run_report_writer(
                session,
                context,
                arbiter_assignment,
                test_assignment,
            )
            final_report = _load_json_object(report_assignment.output_payload)
            output = {
                **final_report,
                "agent_session_id": session.id,
                "comparison": _comparison_payload(session, final_report),
            }
            session.status = AgentSessionStatus.COMPLETED.value
            session.summary = _optional_str(final_report.get("summary"))
            session.final_report = json.dumps(final_report, ensure_ascii=False, sort_keys=True)
            session.completed_at = datetime.utcnow()
            task.status = TaskStatus.COMPLETED.value
            task.output_payload = json.dumps(output, ensure_ascii=False, sort_keys=True)
            task.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)
            return task
        except Exception as exc:
            session.status = AgentSessionStatus.FAILED.value
            session.error_message = str(exc)
            session.completed_at = datetime.utcnow()
            task.status = TaskStatus.FAILED.value
            task.error_message = str(exc)
            task.output_payload = json.dumps(_empty_output(), ensure_ascii=False, sort_keys=True)
            task.completed_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(task)
            return task

    def get_task(self, task_id: str) -> Task | None:
        return self.db.get(Task, task_id)

    def get_session(self, session_id: str) -> AgentSession | None:
        return self.db.get(AgentSession, session_id)

    def build_task_response(self, task: Task) -> MultiAgentReviewResponse:
        session = self.db.scalar(
            select(AgentSession)
            .where(AgentSession.task_id == task.id)
            .order_by(AgentSession.created_at.desc(), AgentSession.id.desc())
        )
        if session is None:
            raise MultiAgentReviewValidationError("Multi-Agent session not found.")
        return self.build_session_response(session, task=task)

    def build_session_response(
        self,
        session: AgentSession,
        *,
        task: Task | None = None,
    ) -> MultiAgentReviewResponse:
        task = task or session.task
        output = _load_json_object(task.output_payload or "{}")
        final_report = _load_json_object(session.final_report)
        report_payload = final_report or output
        assignments = self._load_assignments(session.id)
        messages = self._load_messages(session.id)
        arbiter_decision = _load_dict(report_payload.get("arbiter_decision"))
        return MultiAgentReviewResponse(
            task_id=task.id,
            repository_id=task.repository_id,
            status=task.status,
            session=_session_response(session),
            assignments=[_assignment_response(item) for item in assignments],
            messages=[_message_response(item) for item in messages],
            summary=_optional_str(report_payload.get("summary")),
            risk_level=_optional_str(report_payload.get("risk_level")),
            risks=_load_dict_list(report_payload.get("risks")),
            suggested_tests=_load_dict_list(report_payload.get("suggested_tests")),
            citations=_load_dict_list(report_payload.get("citations")),
            markdown=_optional_str(report_payload.get("markdown")),
            arbiter_decision=arbiter_decision,
            dissent=_load_dict_list(report_payload.get("dissent")),
            comparison=_load_dict(output.get("comparison")),
            warnings=_load_str_list(report_payload.get("warnings")),
            error_message=task.error_message,
            created_at=task.created_at,
            completed_at=task.completed_at,
        )

    def _prepare_context(
        self,
        task: Task,
        request: MultiAgentReviewCreateRequest,
        settings: Settings,
    ) -> dict[str, Any]:
        diff_analysis = analyze_diff(request.diff_text.strip())
        mapping = map_diff_to_symbols(self.db, task.repository_id, diff_analysis)
        query = _review_search_query(diff_analysis, mapping)
        search_result = code_search(
            self.db,
            task.repository_id,
            query,
            settings,
            top_k=request.top_k,
            use_bm25=request.use_bm25,
            use_vector=request.use_vector,
            use_graph=request.use_graph,
        )
        return {
            "diff_analysis": diff_analysis,
            "mapping": mapping,
            "query": query,
            "evidences": search_result.evidences,
            "warnings": search_result.warnings,
        }

    def _run_coordinator(
        self,
        session: AgentSession,
        context: dict[str, Any],
        request: MultiAgentReviewCreateRequest,
    ) -> AgentAssignment:
        output = {
            "rounds": [
                {
                    "round_index": 1,
                    "roles": [
                        ROLE_RISK_REVIEWER,
                        ROLE_SECURITY_REVIEWER,
                        ROLE_TEST_STRATEGIST,
                    ],
                },
                {"round_index": 2, "roles": [ROLE_ARBITER, ROLE_REPORT_WRITER]},
            ],
            "changed_files": _changed_files(context["diff_analysis"]),
            "query": context["query"],
            "limits": {
                "round_limit": request.round_limit,
                "assignment_limit": request.assignment_limit,
                "token_budget": request.token_budget,
            },
        }
        assignment = self._complete_assignment(
            session=session,
            agent_name="CoordinatorAgent",
            role=ROLE_COORDINATOR,
            round_index=1,
            input_payload={"diff_files": output["changed_files"]},
            output_payload=output,
            evidence_ids=[],
            confidence=90,
        )
        self._add_message(
            session=session,
            assignment=assignment,
            sender=ROLE_COORDINATOR,
            recipient="all",
            message_type=AgentMessageType.ASSIGNMENT.value,
            round_index=1,
            content="Coordinator assigned risk, security, and test review roles.",
            claims=["Review work is split into independent role assignments."],
            evidence_ids=[],
            confidence=90,
            requires_arbitration=False,
        )
        return assignment

    def _run_risk_reviewer(
        self,
        session: AgentSession,
        context: dict[str, Any],
    ) -> AgentAssignment:
        started = perf_counter()
        result = review_risks(
            diff_analysis=context["diff_analysis"],
            mapping=context["mapping"],
            evidences=context["evidences"],
        )
        evidence_ids = _evidence_ids_from_risks(result.risks)
        output = {
            "risks": [risk.to_dict() for risk in result.risks],
            "impacted_symbols": result.impacted_symbols,
            "warnings": result.warnings,
            "mode": result.mode,
        }
        assignment = self._complete_assignment(
            session=session,
            agent_name="RiskReviewerAgent",
            role=ROLE_RISK_REVIEWER,
            round_index=1,
            input_payload={"focus": "functional and behavioral review risks"},
            output_payload=output,
            evidence_ids=evidence_ids,
            confidence=_confidence_from_support(result.risks),
            latency_ms=_elapsed_ms(started),
        )
        self._add_message(
            session=session,
            assignment=assignment,
            sender=ROLE_RISK_REVIEWER,
            recipient=ROLE_ARBITER,
            message_type=AgentMessageType.ANALYSIS.value,
            round_index=1,
            content=f"Risk reviewer drafted {len(result.risks)} functional risk(s).",
            claims=[risk.title for risk in result.risks],
            evidence_ids=evidence_ids,
            confidence=assignment.confidence,
            requires_arbitration=True,
        )
        return assignment

    def _run_security_reviewer(
        self,
        session: AgentSession,
        context: dict[str, Any],
    ) -> AgentAssignment:
        started = perf_counter()
        risks = _security_risks(context["diff_analysis"], context["evidences"])
        evidence_ids = _evidence_ids_from_risks(risks)
        dissent = None
        requires_arbitration = False
        if risks and not evidence_ids:
            requires_arbitration = True
            dissent = {
                "reason": "Security signal is diff-supported but lacks retrieved evidence.",
                "risk_titles": [risk.title for risk in risks],
            }
        output = {
            "risks": [risk.to_dict() for risk in risks],
            "warnings": []
            if risks
            else ["No explicit security-sensitive changes were detected."],
        }
        assignment = self._complete_assignment(
            session=session,
            agent_name="SecurityReviewerAgent",
            role=ROLE_SECURITY_REVIEWER,
            round_index=1,
            input_payload={"focus": "security, secrets, auth, path traversal, unsafe execution"},
            output_payload=output,
            evidence_ids=evidence_ids,
            dissent=dissent,
            confidence=65 if risks else 55,
            latency_ms=_elapsed_ms(started),
        )
        self._add_message(
            session=session,
            assignment=assignment,
            sender=ROLE_SECURITY_REVIEWER,
            recipient=ROLE_ARBITER,
            message_type=AgentMessageType.DISSENT.value
            if requires_arbitration
            else AgentMessageType.ANALYSIS.value,
            round_index=1,
            content=(
                f"Security reviewer drafted {len(risks)} security risk(s)."
                if risks
                else "Security reviewer found no explicit security-sensitive changes."
            ),
            claims=[risk.title for risk in risks],
            evidence_ids=evidence_ids,
            confidence=assignment.confidence,
            requires_arbitration=requires_arbitration,
        )
        return assignment

    def _run_test_strategist(
        self,
        session: AgentSession,
        context: dict[str, Any],
        risk_assignment: AgentAssignment,
        security_assignment: AgentAssignment,
    ) -> AgentAssignment:
        started = perf_counter()
        draft_risks = [
            *_risks_from_assignment(risk_assignment),
            *_risks_from_assignment(security_assignment),
        ]
        result = suggest_review_tests(
            verified_risks=draft_risks,
            impacted_symbols=_impacted_symbols(draft_risks),
            diff_analysis=context["diff_analysis"],
        )
        output = {
            "suggested_tests": [test.to_dict() for test in result.suggested_tests],
            "warnings": result.warnings,
        }
        assignment = self._complete_assignment(
            session=session,
            agent_name="TestStrategistAgent",
            role=ROLE_TEST_STRATEGIST,
            round_index=1,
            input_payload={"focus": "test gaps and regression coverage"},
            output_payload=output,
            evidence_ids=[],
            confidence=70 if result.suggested_tests else 50,
            latency_ms=_elapsed_ms(started),
        )
        self._add_message(
            session=session,
            assignment=assignment,
            sender=ROLE_TEST_STRATEGIST,
            recipient=ROLE_ARBITER,
            message_type=AgentMessageType.ANALYSIS.value,
            round_index=1,
            content=f"Test strategist proposed {len(result.suggested_tests)} focused test(s).",
            claims=[test.target for test in result.suggested_tests],
            evidence_ids=[],
            confidence=assignment.confidence,
            requires_arbitration=False,
        )
        return assignment

    def _run_arbiter(
        self,
        session: AgentSession,
        context: dict[str, Any],
        risk_assignment: AgentAssignment,
        security_assignment: AgentAssignment,
        test_assignment: AgentAssignment,
    ) -> AgentAssignment:
        started = perf_counter()
        draft_risks = [
            *_risks_from_assignment(risk_assignment),
            *_risks_from_assignment(security_assignment),
        ]
        verifier = verify_review_risks(
            risks=draft_risks,
            diff_analysis=context["diff_analysis"],
            evidences=context["evidences"],
        )
        accepted = verifier.verified_risks
        rejected = verifier.missing_risks
        downgraded = [
            risk
            for risk in accepted
            if any(original.title == risk.title and original.severity != risk.severity for original in draft_risks)
        ]
        dissent = _dissent_payload(security_assignment, rejected, downgraded)
        output = {
            "accepted_risks": [risk.to_dict() for risk in accepted],
            "rejected_risks": [risk.to_dict() for risk in rejected],
            "downgraded_risks": [risk.to_dict() for risk in downgraded],
            "dissent": dissent,
            "warnings": verifier.warnings,
            "risk_level": verifier.risk_level,
            "test_assignment_id": test_assignment.id,
        }
        assignment = self._complete_assignment(
            session=session,
            agent_name="ArbiterAgent",
            role=ROLE_ARBITER,
            round_index=2,
            input_payload={"draft_risk_count": len(draft_risks)},
            output_payload=output,
            evidence_ids=_evidence_ids_from_risks(accepted),
            dissent={"items": dissent} if dissent else None,
            confidence=80 if accepted or rejected else 60,
            latency_ms=_elapsed_ms(started),
        )
        self._add_message(
            session=session,
            assignment=assignment,
            sender=ROLE_ARBITER,
            recipient="all",
            message_type=AgentMessageType.ARBITRATION.value,
            round_index=2,
            content=(
                f"Arbiter accepted {len(accepted)} risk(s), rejected {len(rejected)}, "
                f"and recorded {len(dissent)} dissent item(s)."
            ),
            claims=[risk.title for risk in accepted],
            evidence_ids=_evidence_ids_from_risks(accepted),
            confidence=assignment.confidence,
            requires_arbitration=False,
        )
        return assignment

    def _run_report_writer(
        self,
        session: AgentSession,
        context: dict[str, Any],
        arbiter_assignment: AgentAssignment,
        test_assignment: AgentAssignment,
    ) -> AgentAssignment:
        started = perf_counter()
        arbiter_payload = _load_json_object(arbiter_assignment.output_payload)
        risks = _risk_payloads_to_objects(arbiter_payload.get("accepted_risks"))
        tests = _test_payloads_to_objects(_load_json_object(test_assignment.output_payload).get("suggested_tests"))
        report = write_review_report(
            verified_risks=risks,
            suggested_tests=tests,
            evidences=context["evidences"],
            warnings=[
                *context["warnings"],
                *_load_str_list(arbiter_payload.get("warnings")),
            ],
            risk_level=_optional_str(arbiter_payload.get("risk_level")),
        )
        output = {
            **report.to_dict(),
            "arbiter_decision": {
                "accepted": len(_load_list(arbiter_payload.get("accepted_risks"))),
                "rejected": len(_load_list(arbiter_payload.get("rejected_risks"))),
                "downgraded": len(_load_list(arbiter_payload.get("downgraded_risks"))),
                "dissent_count": len(_load_list(arbiter_payload.get("dissent"))),
                "reason": "Arbiter retained evidence-grounded risks and preserved dissent.",
            },
            "dissent": _load_dict_list(arbiter_payload.get("dissent")),
            "source_agents": _source_agents(session.id),
        }
        assignment = self._complete_assignment(
            session=session,
            agent_name="ReportWriterAgent",
            role=ROLE_REPORT_WRITER,
            round_index=2,
            input_payload={"arbiter_assignment_id": arbiter_assignment.id},
            output_payload=output,
            evidence_ids=[citation["evidence_id"] for citation in output["citations"]],
            confidence=85,
            latency_ms=_elapsed_ms(started),
        )
        self._add_message(
            session=session,
            assignment=assignment,
            sender=ROLE_REPORT_WRITER,
            recipient="all",
            message_type=AgentMessageType.FINAL.value,
            round_index=2,
            content=output["summary"],
            claims=[risk["title"] for risk in output["risks"]],
            evidence_ids=[citation["evidence_id"] for citation in output["citations"]],
            confidence=assignment.confidence,
            requires_arbitration=False,
        )
        return assignment

    def _complete_assignment(
        self,
        *,
        session: AgentSession,
        agent_name: str,
        role: str,
        round_index: int,
        input_payload: dict[str, object],
        output_payload: dict[str, object],
        evidence_ids: list[str],
        confidence: int,
        latency_ms: int | None = None,
        dissent: dict[str, object] | None = None,
    ) -> AgentAssignment:
        _enforce_limits(session, self._load_assignments(session.id), round_index=round_index)
        assignment = AgentAssignment(
            session_id=session.id,
            agent_name=agent_name,
            role=role,
            status=AgentAssignmentStatus.COMPLETED.value,
            round_index=round_index,
            input_payload=json.dumps(input_payload, ensure_ascii=False, sort_keys=True),
            output_payload=json.dumps(output_payload, ensure_ascii=False, sort_keys=True),
            evidence_ids=json.dumps(evidence_ids, ensure_ascii=False, sort_keys=True),
            dissent=json.dumps(dissent, ensure_ascii=False, sort_keys=True) if dissent else None,
            confidence=max(0, min(confidence, 100)),
            token_estimate=_estimate_tokens(input_payload, output_payload),
            latency_ms=latency_ms,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def _add_message(
        self,
        *,
        session: AgentSession,
        assignment: AgentAssignment,
        sender: str,
        recipient: str,
        message_type: str,
        round_index: int,
        content: str,
        claims: list[str],
        evidence_ids: list[str],
        confidence: int,
        requires_arbitration: bool,
    ) -> AgentMessage:
        message = AgentMessage(
            session_id=session.id,
            assignment_id=assignment.id,
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            round_index=round_index,
            content=content,
            evidence_ids=json.dumps(evidence_ids, ensure_ascii=False, sort_keys=True),
            claims=json.dumps(claims, ensure_ascii=False, sort_keys=True),
            confidence=max(0, min(confidence, 100)),
            requires_arbitration=requires_arbitration,
        )
        self.db.add(message)
        self.db.flush()
        return message

    def _load_assignments(self, session_id: str) -> list[AgentAssignment]:
        return list(
            self.db.scalars(
                select(AgentAssignment)
                .where(AgentAssignment.session_id == session_id)
                .order_by(AgentAssignment.round_index, AgentAssignment.created_at, AgentAssignment.id)
            ).all()
        )

    def _load_messages(self, session_id: str) -> list[AgentMessage]:
        return list(
            self.db.scalars(
                select(AgentMessage)
                .where(AgentMessage.session_id == session_id)
                .order_by(AgentMessage.round_index, AgentMessage.created_at, AgentMessage.id)
            ).all()
        )


class MultiAgentReviewRepositoryNotReadyError(ValueError):
    pass


class MultiAgentReviewValidationError(ValueError):
    pass


def _empty_output() -> dict[str, object]:
    return {
        "summary": None,
        "risk_level": None,
        "risks": [],
        "suggested_tests": [],
        "citations": [],
        "markdown": None,
        "arbiter_decision": {},
        "dissent": [],
        "warnings": [],
    }


def _security_risks(diff_analysis, evidences: list[object]) -> list[DraftReviewRisk]:
    security_terms = (
        "auth",
        "authorization",
        "token",
        "secret",
        "password",
        "permission",
        "path",
        "traversal",
        "eval",
        "exec",
        "subprocess",
        "sql",
        "request",
    )
    risks: list[DraftReviewRisk] = []
    for diff_file in diff_analysis.files:
        file_path = diff_file.new_path or diff_file.old_path or ""
        for hunk_index, hunk in enumerate(diff_file.hunks, start=1):
            lines = [*hunk.added_lines, *hunk.removed_lines]
            matched_lines = [
                line
                for line in lines
                if any(term in line.content.lower() or term in file_path.lower() for term in security_terms)
            ]
            if not matched_lines:
                continue
            first_line = matched_lines[0].line
            risks.append(
                DraftReviewRisk(
                    title=f"Security review required for {file_path}",
                    severity="medium",
                    location=ReviewRiskLocation(
                        file_path=file_path,
                        start_line=first_line,
                        end_line=first_line,
                    ),
                    reason=(
                        f"Security-sensitive term found near hunk {hunk_index}; "
                        "confirm authorization, secret handling, and unsafe execution boundaries."
                    ),
                    evidence_ids=_evidence_ids_for_file(evidences, file_path),
                    impacted_symbols=[],
                    suggestion="Add focused tests for the security boundary touched by this diff.",
                    diff_refs=[
                        {
                            "file_path": file_path,
                            "line": line.line,
                            "line_type": "changed",
                            "hunk_index": hunk_index,
                            "change_type": diff_file.change_type,
                        }
                        for line in matched_lines[:3]
                    ],
                )
            )
            break
    return risks[:3]


def _review_search_query(diff_analysis, mapping) -> str:
    symbols = _deduplicate([match.symbol_name for match in mapping.matches])
    files = _changed_files(diff_analysis)
    query_parts = [*symbols[:8], *files[:8]]
    return " ".join(query_parts) if query_parts else "multi agent review changed code"


def _changed_files(diff_analysis) -> list[str]:
    return _deduplicate(
        [
            file_path
            for diff_file in diff_analysis.files
            for file_path in [diff_file.new_path or diff_file.old_path]
            if file_path
        ]
    )


def _evidence_ids_for_file(evidences: list[object], file_path: str, *, limit: int = 3) -> list[str]:
    evidence_ids: list[str] = []
    for evidence in evidences:
        if getattr(evidence, "file_path", None) != file_path:
            continue
        evidence_id = getattr(evidence, "evidence_id", "")
        if isinstance(evidence_id, str) and evidence_id:
            evidence_ids.append(evidence_id)
    return _deduplicate(evidence_ids)[:limit]


def _evidence_ids_from_risks(risks: list[DraftReviewRisk]) -> list[str]:
    return _deduplicate([evidence_id for risk in risks for evidence_id in risk.evidence_ids])


def _confidence_from_support(risks: list[DraftReviewRisk]) -> int:
    if not risks:
        return 55
    with_evidence = sum(1 for risk in risks if risk.evidence_ids)
    with_diff = sum(1 for risk in risks if risk.diff_refs)
    return min(90, 55 + with_evidence * 10 + with_diff * 5)


def _risks_from_assignment(assignment: AgentAssignment) -> list[DraftReviewRisk]:
    output = _load_json_object(assignment.output_payload)
    return _risk_payloads_to_objects(output.get("risks"))


def _risk_payloads_to_objects(value: object) -> list[DraftReviewRisk]:
    risks = []
    for item in _load_dict_list(value):
        location = _load_dict(item.get("location"))
        risks.append(
            DraftReviewRisk(
                title=str(item.get("title") or "Review risk"),
                severity=str(item.get("severity") or "low"),
                location=ReviewRiskLocation(
                    file_path=str(location.get("file_path") or ""),
                    start_line=_int_or_default(location.get("start_line"), 1),
                    end_line=_int_or_default(location.get("end_line"), 1),
                ),
                reason=str(item.get("reason") or ""),
                evidence_ids=_load_str_list(item.get("evidence_ids")),
                impacted_symbols=_load_str_list(item.get("impacted_symbols")),
                suggestion=str(item.get("suggestion") or ""),
                diff_refs=_load_dict_list(item.get("diff_refs")),
            )
        )
    return risks


def _test_payloads_to_objects(value: object) -> list[SuggestedReviewTest]:
    tests = []
    for item in _load_dict_list(value):
        tests.append(
            SuggestedReviewTest(
                target=str(item.get("target") or "Focused test"),
                reason=str(item.get("reason") or ""),
                test_type=str(item.get("test_type") or "regression"),
                related_risk_titles=_load_str_list(item.get("related_risk_titles")),
                file_path=_optional_str(item.get("file_path")),
            )
        )
    return tests


def _impacted_symbols(risks: list[DraftReviewRisk]) -> list[str]:
    return _deduplicate([symbol for risk in risks for symbol in risk.impacted_symbols])


def _dissent_payload(
    security_assignment: AgentAssignment,
    rejected: list[DraftReviewRisk],
    downgraded: list[DraftReviewRisk],
) -> list[dict[str, object]]:
    dissent = []
    if security_assignment.dissent:
        dissent.append(
            {
                "source_agent": security_assignment.agent_name,
                "type": "security_evidence_gap",
                "detail": _load_json_object(security_assignment.dissent),
            }
        )
    for risk in rejected:
        dissent.append(
            {
                "source_agent": "ArbiterAgent",
                "type": "rejected",
                "title": risk.title,
                "reason": "Risk lacked evidence or diff support under the Phase 8 policy.",
            }
        )
    for risk in downgraded:
        dissent.append(
            {
                "source_agent": "ArbiterAgent",
                "type": "downgraded",
                "title": risk.title,
                "reason": "High severity was downgraded because support was incomplete.",
            }
        )
    return dissent


def _source_agents(session_id: str) -> list[str]:
    _ = session_id
    return [
        "RiskReviewerAgent",
        "SecurityReviewerAgent",
        "TestStrategistAgent",
        "ArbiterAgent",
    ]


def _comparison_payload(session: AgentSession, final_report: dict[str, object]) -> dict[str, object]:
    assignments = session.assignments
    messages = session.messages
    return {
        "baseline": "single_main_review",
        "variant": "multi_agent_review",
        "assignment_count": len(assignments),
        "message_count": len(messages),
        "dissent_count": len(_load_dict_list(final_report.get("dissent"))),
        "arbiter_resolution": _load_dict(final_report.get("arbiter_decision")),
        "token_estimate": sum(assignment.token_estimate for assignment in assignments),
    }


def _enforce_limits(
    session: AgentSession,
    assignments: list[AgentAssignment],
    *,
    round_index: int,
) -> None:
    if round_index > session.round_limit:
        raise MultiAgentReviewValidationError("Multi-Agent round limit exceeded.")
    if len(assignments) >= session.assignment_limit:
        raise MultiAgentReviewValidationError("Multi-Agent assignment limit exceeded.")
    token_budget = session.token_budget
    if token_budget is not None and sum(item.token_estimate for item in assignments) > token_budget:
        raise MultiAgentReviewValidationError("Multi-Agent token budget exceeded.")


def _estimate_tokens(*payloads: dict[str, object]) -> int:
    text = "".join(json.dumps(payload, ensure_ascii=False, sort_keys=True) for payload in payloads)
    return max(len(text) // 4, 1)


def _session_response(session: AgentSession) -> AgentSessionResponse:
    return AgentSessionResponse(
        id=session.id,
        task_id=session.task_id,
        repository_id=session.repository_id,
        status=session.status,
        mode=session.mode,
        round_limit=session.round_limit,
        assignment_limit=session.assignment_limit,
        token_budget=session.token_budget,
        summary=session.summary,
        final_report=_load_json_object(session.final_report),
        error_message=session.error_message,
        created_at=session.created_at,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )


def _assignment_response(assignment: AgentAssignment) -> AgentAssignmentResponse:
    return AgentAssignmentResponse(
        id=assignment.id,
        session_id=assignment.session_id,
        agent_name=assignment.agent_name,
        role=assignment.role,
        status=assignment.status,
        round_index=assignment.round_index,
        input_payload=_load_json_object(assignment.input_payload),
        output_payload=_load_json_object(assignment.output_payload),
        evidence_ids=_load_str_list_from_json(assignment.evidence_ids),
        dissent=_load_json_object(assignment.dissent),
        confidence=assignment.confidence,
        token_estimate=assignment.token_estimate,
        latency_ms=assignment.latency_ms,
        error_message=assignment.error_message,
        created_at=assignment.created_at,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
    )


def _message_response(message: AgentMessage) -> AgentMessageResponse:
    return AgentMessageResponse(
        id=message.id,
        session_id=message.session_id,
        assignment_id=message.assignment_id,
        sender=message.sender,
        recipient=message.recipient,
        message_type=message.message_type,
        round_index=message.round_index,
        content=message.content,
        evidence_ids=_load_str_list_from_json(message.evidence_ids),
        claims=_load_str_list_from_json(message.claims),
        confidence=message.confidence,
        requires_arbitration=message.requires_arbitration,
        created_at=message.created_at,
    )


def _load_json_object(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _load_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _load_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _load_dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _load_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _load_str_list_from_json(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return _load_str_list(value)


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _int_or_default(value: object, default: int) -> int:
    return value if isinstance(value, int) else default


def _deduplicate(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduplicated.append(value)
    return deduplicated


def _elapsed_ms(started: float) -> int:
    return max(int((perf_counter() - started) * 1000), 0)
