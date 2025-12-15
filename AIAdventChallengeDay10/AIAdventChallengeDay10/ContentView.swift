//
//  ContentView.swift
//  AIAdventChallengeDay10
//
//  Created by Ivan Andreyshev on 12.12.2025.
//
import SwiftUI

struct ContentView: View {
    private let client = YandexAIClient()

    // UI input/output
    @State private var prompt: String = ""
    @State private var responseText: String = ""
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?
    @State private var tokenLimitError: Bool = false

    // Metrics (last request)
    @State private var inputTokens: Int?
    @State private var outputTokens: Int?
    @State private var totalTokens: Int?
    @State private var promptWordCount: Int = 0
    @State private var responseWordCount: Int = 0
    @State private var elapsedSeconds: Double?

    // Chat + Compression
    @State private var isCompressionEnabled: Bool = true
    @State private var messages: [ChatMessage] = []
    @State private var compressedSummary: String = ""
    @State private var sinceSummary: [ChatMessage] = []

    private let summaryChunkSize: Int = 4
    private let keepLast: Int = 3

    // Token comparison (rough – по total_tokens каждого ответа)
    @State private var tokensNoCompressionTotal: Int = 0
    @State private var tokensWithCompressionTotal: Int = 0
    @State private var lastRequestUsedCompression: Bool = false

    // Keyboard focus
    @FocusState private var isPromptFocused: Bool

    private let placeholder = "Введите ваш запрос..."
    private let hardcodedInsertText =
        """
        Сделай план реализации “сжатия истории диалога” в iOS SwiftUI приложении.
        Укажи: модель данных, алгоритм summary каждые 10 сообщений, как сравнить токены и как тестировать качество.
        """

    @State private var isDemoRunning: Bool = false
    @State private var demoIndex: Int = 0

    // Retry настройки демо
    private let demoMaxRetriesPerStep: Int = 3
    private let demoRetryDelayMs: UInt64 = 600

    private let demoScript: [String] = [
        "Запомни, пожалуйста: меня зовут Иван, я разрабатываю учебное iOS-приложение на SwiftUI.",
        "Цель приложения: общение с языковой моделью, подсчёт токенов запроса и ответа, слов и времени ответа.",
        "Важно: приложение должно корректно работать при длинных диалогах и не превышать лимит токенов.",
        "Добавь требование: история диалога должна автоматически сжиматься с помощью summary.",
        "Механизм сжатия: каждые несколько сообщений делать summary и хранить его вместо полной истории.",
        "При этом последние несколько сообщений нужно оставлять без сжатия, чтобы сохранить локальный контекст.",
        "Также важно уметь сравнивать использование токенов с компрессией и без неё.",
        "Скажи, пожалуйста, какие ключевые требования к приложению ты сейчас помнишь.",
        "Теперь представь, что я прошу продолжить разработку этого приложения.",
        "Не забудь, что мы используем SwiftUI и Responses API, а ключи храним в отдельном файле.",
        "Добавь краткий план следующих шагов разработки, исходя из всей истории диалога.",
        "Повтори все основные требования к приложению и текущую цель проекта."
    ]

    // Persistence helpers
    @State private var didLoadPersistedState: Bool = false
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("День 9 — Сжатие диалога")
                        .font(.largeTitle).bold()

                    // Compression toggle + stats
                    VStack(alignment: .leading, spacing: 8) {
                        Toggle("Компрессия истории", isOn: $isCompressionEnabled)
                            .onChange(of: isCompressionEnabled) { _ in
                                savePersistedState()
                            }

                        HStack {
                            Button(isDemoRunning ? "Демо выполняется..." : "Запустить демо") {
                                Task { await runDemo() }
                            }
                            .buttonStyle(.bordered)
                            .disabled(isDemoRunning || isLoading)

                            Button("Сброс") {
                                resetAll()
                            }
                            .buttonStyle(.bordered)
                            .disabled(isDemoRunning || isLoading)
                        }

                        if isDemoRunning {
                            Text("Демо: шаг \(demoIndex)/\(demoScript.count)")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        HStack(spacing: 10) {
                            Text("Summary:")
                                .font(.caption)
                                .foregroundColor(.secondary)

                            Text(compressedSummary.isEmpty ? "нет" : "есть")
                                .font(.caption)
                                .foregroundColor(compressedSummary.isEmpty ? .secondary : .green)
                        }

                        VStack(alignment: .leading, spacing: 2) {
                            Text("Токены суммарно (без компрессии): \(tokensNoCompressionTotal)")
                            Text("Токены суммарно (с компрессией): \(tokensWithCompressionTotal)")
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                    }

                    Divider()

                    // Prompt input
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Запрос к модели")
                            .font(.headline)

                        ZStack(alignment: .topLeading) {
                            if prompt.isEmpty {
                                Text(placeholder)
                                    .foregroundColor(.gray.opacity(0.6))
                                    .padding(.horizontal, 14)
                                    .padding(.vertical, 12)
                            }

                            TextEditor(text: $prompt)
                                .frame(minHeight: 140)
                                .padding(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color.gray.opacity(0.3))
                                )
                                .focused($isPromptFocused)
                                .onChange(of: prompt) { newValue in
                                    promptWordCount = wordCount(newValue)
                                }
                                .disabled(isDemoRunning)
                        }

                        HStack {
                            Spacer()

                            Button("Очистить") {
                                prompt = ""
                                promptWordCount = 0
                            }
                            .font(.caption)

                            // При желании верни кнопку вставки примера
                            // Button("Вставить пример") { prompt = hardcodedInsertText; promptWordCount = wordCount(prompt) }
                        }

                        Text("Слов в запросе: \(promptWordCount)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    // Send button
                    Button {
                        send()
                    } label: {
                        HStack {
                            if isLoading { ProgressView() }
                            Text("Отправить")
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(isLoading || isDemoRunning || prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

                    // Error block
                    if let errorMessage {
                        Text(errorMessage)
                            .foregroundColor(tokenLimitError ? .red : .orange)
                            .font(.footnote)
                            .padding(8)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(tokenLimitError ? Color.red.opacity(0.12) : Color.orange.opacity(0.12))
                            )
                    }

                    // Response text
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Ответ модели")
                            .font(.headline)

                        Text(responseText.isEmpty ? "Ответа пока нет" : responseText)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(10)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.gray.opacity(0.3))
                            )

                        Text("Слов в ответе: \(responseWordCount)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    // Metrics
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Метрики последнего запроса")
                            .font(.headline)

                        VStack(alignment: .leading, spacing: 2) {
                            Text("Токены запроса: \(inputTokens ?? 0)")
                            Text("Токены ответа: \(outputTokens ?? 0)")
                            Text("Всего токенов: \(totalTokens ?? 0)")
                            if let elapsedSeconds {
                                Text(String(format: "Время ответа: %.2f сек", elapsedSeconds))
                            }
                            Text("Контекст: \(lastRequestUsedCompression ? "summary + хвост" : "полная история")")
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                    }

                    Divider()

                    // Chat log (for debugging / quality check)
                    VStack(alignment: .leading, spacing: 8) {
                        Text("История (UI)")
                            .font(.headline)

                        ForEach(messages) { msg in
                            VStack(alignment: .leading, spacing: 4) {
                                Text(msg.role == .user ? "USER" : "ASSISTANT")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                                Text(msg.text)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                            .padding(10)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.gray.opacity(0.2))
                            )
                        }
                    }

                    Spacer(minLength: 24)
                }
                .padding()
            }
            .ignoresSafeArea(.keyboard, edges: .bottom)
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button {
                        send()
                    } label: {
                        if isLoading {
                            ProgressView()
                        } else {
                            Text("Отправить").bold()
                        }
                    }
                    .disabled(isLoading || isDemoRunning || prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
        .task {
            // Загружаем один раз при старте
            guard !didLoadPersistedState else { return }
            didLoadPersistedState = true
            loadPersistedStateIfExists()
        }
        .onChange(of: scenePhase) { newPhase in
            // Сохраняем, когда приложение уходит в фон/неактивность
            if newPhase == .inactive || newPhase == .background {
                savePersistedState()
            }
        }
    }

    // MARK: - Persistence

    private func savePersistedState() {
        let state = PersistedAppState(
            isCompressionEnabled: isCompressionEnabled,
            messages: messages,
            compressedSummary: compressedSummary,
            sinceSummary: sinceSummary,
            tokensNoCompressionTotal: tokensNoCompressionTotal,
            tokensWithCompressionTotal: tokensWithCompressionTotal
        )
        ChatPersistence.save(state)
    }

    private func loadPersistedStateIfExists() {
        guard let loaded = ChatPersistence.load() else { return }
        isCompressionEnabled = loaded.isCompressionEnabled
        messages = loaded.messages
        compressedSummary = loaded.compressedSummary
        sinceSummary = loaded.sinceSummary
        tokensNoCompressionTotal = loaded.tokensNoCompressionTotal
        tokensWithCompressionTotal = loaded.tokensWithCompressionTotal
    }

    // MARK: - Actions

    private func send() {
        let text = prompt.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        isPromptFocused = false
        Task { _ = await callModel(userText: text) }
    }

    /// Возвращает true если запрос успешен, иначе false.
    /// Важно: если ошибка — откатываем добавленное USER сообщение, чтобы ретраи не засоряли историю.
    private func callModel(userText: String) async -> Bool {
        isLoading = true
        errorMessage = nil
        tokenLimitError = false

        // 1) Add user message (optimistic)
        let userMsg = ChatMessage(role: .user, text: userText)
        messages.append(userMsg)
        sinceSummary.append(userMsg)

        // На случай ошибки: запомним ID и откатим эту вставку
        let insertedUserId = userMsg.id

        // 2) Maybe compress before sending (if chunk reached)
        await maybeCompressHistory()

        // 3) Build input (summary+tail or full history)
        let input = buildConversationInput(currentUserPrompt: userText)
        lastRequestUsedCompression = isCompressionEnabled && !compressedSummary.isEmpty

        do {
            let result = try await client.send(
                prompt: input,
                model: AppSecrets.yandexModelUri
            )

            // 4) Save response
            responseText = result.text
            responseWordCount = wordCount(result.text)

            inputTokens = result.inputTokens
            outputTokens = result.outputTokens
            totalTokens = result.totalTokens
            elapsedSeconds = result.elapsedSeconds

            // 5) Add assistant message
            let assistantMsg = ChatMessage(role: .assistant, text: result.text)
            messages.append(assistantMsg)
            sinceSummary.append(assistantMsg)

            // 6) Compare total tokens sums
            let used = result.totalTokens ?? 0
            if lastRequestUsedCompression {
                tokensWithCompressionTotal += used
            } else {
                tokensNoCompressionTotal += used
            }

            // 7) Maybe compress after response too
            await maybeCompressHistory()

            isLoading = false

            // ✅ сохранить на диск после успешного шага
            savePersistedState()

            return true

        } catch let error as YandexAIClient.YandexAIError {
            errorMessage = error.localizedDescription
            if case .tokenLimitExceeded = error {
                tokenLimitError = true
            }
        } catch {
            errorMessage = error.localizedDescription
        }

        // ❗ Откатим добавленное USER сообщение (чтобы при ретрае не дублировалось)
        messages.removeAll { $0.id == insertedUserId }
        sinceSummary.removeAll { $0.id == insertedUserId }

        isLoading = false

        // ✅ всё равно сохраним (на случай, если summary обновился до отправки)
        savePersistedState()

        return false
    }

    // MARK: - Conversation building

    private func buildConversationInput(currentUserPrompt: String) -> String {
        var parts: [String] = []

        if isCompressionEnabled, !compressedSummary.isEmpty {
            parts.append("""
            SYSTEM: Ты помощник. Ниже сжатая память диалога (summary). Считай её истинной и используй как контекст.
            SUMMARY:
            \(compressedSummary)
            """)

            let tail = sinceSummary.suffix(keepLast)
            for m in tail {
                parts.append("\(m.role == .user ? "USER" : "ASSISTANT"): \(m.text)")
            }
        } else {
            for m in messages {
                parts.append("\(m.role == .user ? "USER" : "ASSISTANT"): \(m.text)")
            }
        }

        parts.append("USER: \(currentUserPrompt)")
        return parts.joined(separator: "\n\n")
    }

    // MARK: - Compression

    private func maybeCompressHistory() async {
        guard isCompressionEnabled else { return }
        guard sinceSummary.count >= summaryChunkSize else { return }

        var chunk = ""
        if !compressedSummary.isEmpty {
            chunk += "Текущее summary:\n\(compressedSummary)\n\n"
        }

        chunk += "Новые сообщения:\n"
        for m in sinceSummary.prefix(summaryChunkSize) {
            chunk += "\(m.role == .user ? "USER" : "ASSISTANT"): \(m.text)\n"
        }

        let summarizerPrompt =
            """
            Сожми историю диалога в компактное summary на русском языке.

            Требования:
            - Сохрани факты, имена, требования пользователя, принятые решения, ограничения, незавершённые задачи.
            - Не добавляй выдумок.
            - Формат:
              1) Буллеты "Факты и решения"
              2) Буллеты "Требования/ограничения"
              3) Блок "Текущая цель"

            Данные:
            \(chunk)
            """

        do {
            let result = try await client.send(
                prompt: summarizerPrompt,
                model: AppSecrets.yandexModelUri
            )

            compressedSummary = result.text.trimmingCharacters(in: .whitespacesAndNewlines)

            // Remove compressed chunk from sinceSummary
            sinceSummary = Array(sinceSummary.dropFirst(summaryChunkSize))

            // ✅ сохранить новое summary
            savePersistedState()

        } catch {
            print("Summary failed: \(error)")
        }
    }

    @MainActor
    private func resetAll() {
        prompt = ""
        responseText = ""
        errorMessage = nil
        tokenLimitError = false

        inputTokens = nil
        outputTokens = nil
        totalTokens = nil
        promptWordCount = 0
        responseWordCount = 0
        elapsedSeconds = nil

        messages = []
        compressedSummary = ""
        sinceSummary = []

        tokensNoCompressionTotal = 0
        tokensWithCompressionTotal = 0
        lastRequestUsedCompression = false

        demoIndex = 0
        isDemoRunning = false

        // ✅ очистить файл и сохранить пустое состояние
        ChatPersistence.clear()
        savePersistedState()
    }

    private func runDemo() async {
        if isDemoRunning { return }

        await MainActor.run {
            isDemoRunning = true
            demoIndex = 0
            errorMessage = nil
            tokenLimitError = false
        }

        for (i, msg) in demoScript.enumerated() {
            var attempt = 0
            var success = false

            while attempt <= demoMaxRetriesPerStep && !success {
                attempt += 1

                await MainActor.run {
                    demoIndex = i + 1
                    prompt = msg
                    promptWordCount = wordCount(msg)
                    isPromptFocused = false
                }

                success = await callModel(userText: msg)

                if !success {
                    try? await Task.sleep(nanoseconds: demoRetryDelayMs * 1_000_000)

                    if attempt > demoMaxRetriesPerStep {
                        await MainActor.run { isDemoRunning = false }
                        return
                    }
                }
            }

            try? await Task.sleep(nanoseconds: 250_000_000)
        }

        await MainActor.run {
            isDemoRunning = false
        }
    }
}
