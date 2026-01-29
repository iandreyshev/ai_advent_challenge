# День 7: Сравнение моделей (OpenAI vs Yandex)

iOS-приложение для сравнения ответов от разных LLM провайдеров.

## Возможности

- Одновременная отправка запроса в OpenAI и Yandex
- Сравнение времени ответа
- Подсчёт использованных токенов
- Система рейтинга качества (1-5 звёзд)

## Технологии

- **SwiftUI** — пользовательский интерфейс
- **OpenAI Chat Completions API**
- **Yandex Cloud GenerativeAI API**
- **Swift Concurrency** — параллельные Task

## Метрики сравнения

| Метрика | Описание |
|---------|----------|
| Время ответа | Секунды от запроса до ответа |
| Prompt tokens | Токены входного сообщения |
| Completion tokens | Токены ответа |
| Total tokens | Общее количество токенов |

## Структура

```
AIAdventChallengeDay7/
├── ContentView.swift    # UI сравнения
├── Secrets.swift        # API ключи (gitignored)
└── Assets/
```

## Запуск

1. Добавьте API ключи в `Secrets.swift`:
```swift
enum Secrets {
    static let openAIKey = "sk-..."
    static let yandexKey = "..."
    static let yandexFolderId = "..."
}
```
2. Откройте в Xcode и запустите

## Особенности

- Визуальное разделение провайдеров: OpenAI (синий) vs Yandex (оранжевый)
- Параллельное выполнение запросов через Task
- Вычисление времени через `Date().timeIntervalSince()`
