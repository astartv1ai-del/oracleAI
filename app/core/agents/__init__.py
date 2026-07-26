"""LLM-агенты сервиса.

Агент описывается данными (`AgentSpec`), а исполняется общим кодом. Чтобы завести
нового — допишите спецификацию в `specs.py`: треды, лимиты, tool-use цикл,
переключатель в Mini App и админка подхватят его сами.

    specs.py    — каталог агентов (кто есть в продукте)
    base.py     — структура агента и сборка системного промпта
    runtime.py  — исполнение: контекст, инструменты, офлайн-подстраховка
"""
from .base import SAFETY, AgentSpec, build_system_prompt  # noqa: F401
from .runtime import (agent_list, answer, offline_answer, resolve,  # noqa: F401
                      system_for)
from .specs import DEFAULT_AGENT, REGISTRY, codes, get  # noqa: F401

__all__ = ["AgentSpec", "SAFETY", "build_system_prompt", "REGISTRY", "DEFAULT_AGENT",
           "get", "codes", "resolve", "system_for", "answer", "offline_answer",
           "agent_list"]
