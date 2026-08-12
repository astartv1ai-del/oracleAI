"""Регрессии политики краткосрочного контекста агентного чата."""
from app.core.agents.context import build_bounded_history


def test_bounded_history_keeps_question_once_when_already_saved():
    question = "Стоит ли мне менять работу?"
    messages = build_bounded_history(
        [{"role": "user", "content": question}], question, recent_limit=6)
    assert messages == [{"role": "user", "content": question}]


def test_bounded_history_adds_question_once_when_not_persisted_yet():
    question = "Что мне важно сегодня?"
    messages = build_bounded_history(
        [{"role": "user", "content": "Я устала"},
         {"role": "assistant", "content": "Давай бережно посмотрим."}],
        question,
        recent_limit=6,
    )
    assert messages[-1] == {"role": "user", "content": question}
    assert sum(m["content"] == question for m in messages) == 1


def test_bounded_history_summarises_earlier_user_topics_only():
    history = [
        {"role": "user", "content": "Первая тема — работа"},
        {"role": "assistant", "content": "Ранний вывод агента не должен стать фактом"},
        {"role": "user", "content": "Вторая тема — отношения"},
        {"role": "assistant", "content": "Ответ про отношения"},
        {"role": "user", "content": "Третья тема — отдых"},
        {"role": "assistant", "content": "Ответ про отдых"},
    ]
    messages = build_bounded_history(history, "Что объединяет эти темы?", recent_limit=3)
    assert messages[0]["role"] == "user"
    assert "работа" in messages[0]["content"]
    assert "Ранний вывод агента" not in messages[0]["content"]
    assert messages[-1]["content"] == "Что объединяет эти темы?"
    assert len(messages) == 4


def test_bounded_history_has_no_state_between_threads():
    first = build_bounded_history(
        [{"role": "user", "content": "Тема первого чата"}],
        "Продолжим?", recent_limit=4)
    second = build_bounded_history([], "Новый разговор", recent_limit=4)
    assert any("первого чата" in m["content"] for m in first)
    assert all("первого чата" not in m["content"] for m in second)
