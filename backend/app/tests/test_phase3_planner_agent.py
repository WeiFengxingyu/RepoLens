import pytest

from app.services.agent import QAQuestionType, plan_question


def test_planner_classifies_feature_location_question() -> None:
    plan = plan_question("Where is repository import implemented?")

    assert plan.question_type == QAQuestionType.FEATURE_LOCATION.value
    assert plan.answer_style == "locate_implementation"
    assert plan.retrieval_queries[0] == "Where is repository import implemented?"
    assert len(plan.retrieval_queries) <= 3


def test_planner_classifies_architecture_question() -> None:
    plan = plan_question("Explain the overall architecture and module flow.")

    assert plan.question_type == QAQuestionType.ARCHITECTURE.value
    assert plan.answer_style == "architecture_summary"
    assert any("architecture" in query.lower() for query in plan.retrieval_queries)


def test_planner_classifies_function_explanation_question() -> None:
    plan = plan_question("What does RepositoryService.import_repository do?")

    assert plan.question_type == QAQuestionType.FUNCTION_EXPLANATION.value
    assert plan.answer_style == "explain_symbol"
    assert any("RepositoryService.import_repository" in query for query in plan.retrieval_queries)


def test_planner_enables_graph_for_call_relation_question() -> None:
    plan = plan_question("How does main call helper?")

    assert plan.question_type == QAQuestionType.CALL_RELATION.value
    assert plan.use_graph is True
    assert any("caller" in query for query in plan.retrieval_queries)


def test_planner_enables_graph_for_impact_scope_question() -> None:
    plan = plan_question("What is impacted if parser output changes?")

    assert plan.question_type == QAQuestionType.IMPACT_SCOPE.value
    assert plan.use_graph is True
    assert any("affected" in query for query in plan.retrieval_queries)


def test_planner_rejects_empty_question() -> None:
    with pytest.raises(ValueError, match="Question is required"):
        plan_question("   ")
