# senior-engineer — index

## [DISCOVERED] — подключение к существующему проекту mid-project

## Принципы
- Feature: final-polish (2026-08-12). Полный 6-фазный цикл не требовался: это
  полировочный пасс в зрелой кодовой базе (см. status.md).

## Cross-cutting
- Компоненты Оракула: miniapp (Vanilla JS, window.app), FastAPI+aiogram, SQLite, LLM-провайдеры
- Паттерны: pending-виджеты (код считает — модель трактует), data-act делегирование, DEV_MODE
- Решения, меняющие архитектуру: ADR-001 (контекст инструмента в шапке виджета)
