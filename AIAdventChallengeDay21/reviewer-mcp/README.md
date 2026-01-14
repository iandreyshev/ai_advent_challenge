# Code Review Tool

Консольное приложение для автоматического code review с помощью Yandex AI Studio.

## Описание

Приложение получает изменения между двумя git ветками и отправляет их на анализ в Yandex AI Agent, который проводит code review и выдает рекомендации.

## Требования

- Java 11+
- Git
- Доступ к Yandex AI Studio (API ключ и Agent ID)

## Настройка

1. Скопируйте `.env.example` в `.env`:
```bash
cp .env.example .env
```

2. Заполните переменные окружения в `.env`:
- `YANDEX_API_KEY` - API ключ от Yandex Cloud
- `YANDEX_AGENT_ID` - ID агента из Yandex AI Studio
- `REPOSITORY_PATH` - абсолютный путь к git репозиторию для проверки

3. Экспортируйте переменные:
```bash
export $(cat .env | xargs)
```

## Использование

Запустите приложение с указанием веток для сравнения:

```bash
./gradlew run --args="<source-branch> <target-branch>"
```

Пример:
```bash
./gradlew run --args="feature/new-feature main"
```

Приложение:
1. Получит diff между ветками
2. Отправит изменения в Yandex AI для анализа
3. Выведет результаты code review

## Пример вывода

```
=== Code Review Tool ===
Source branch: feature/new-feature
Target branch: main
Repository: /path/to/repo

Fetching changes from Git...
Changed files (3):
  - src/main/kotlin/Application.kt
  - src/main/kotlin/GitRepository.kt
  - build.gradle.kts

Sending to Yandex AI for review...

=== Code Review Result ===
[Результаты анализа от AI агента]
```

## Сборка

```bash
./gradlew build
```

