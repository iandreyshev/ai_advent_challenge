//
//  ContentView.swift
//  AIAdventChallengeDay3
//
//  Created by Ivan Andreyshev on 03.12.2025.
//
//
//  ContentView.swift
//
//
//  ContentView.swift
//

import SwiftUI
import Combine

// MARK: - Модель сообщения

struct Message: Identifiable {
    let id = UUID()
    let text: String
    let isMe: Bool
}

// MARK: - Модели для API

private struct ChatRequest: Encodable {
    struct Message: Encodable {
        let role: String
        let content: String
    }

    let model: String
    let messages: [Message]
}

private struct ChatResponse: Decodable {
    struct Choice: Decodable {
        struct Message: Decodable {
            let role: String
            let content: String
        }

        let message: Message
    }

    let choices: [Choice]
}

// MARK: - ViewModel

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var isSummarizing = false
    @Published var isFinished = false
    @Published var resultText: String? = nil
    @Published var isLoadingQuestion = false

    private var questions: [String] = []
    private var answers: [String] = []

    private let maxQuestions = 5

    var progressText: String {
        guard !isFinished,
              !questions.isEmpty,
              !messages.isEmpty else { return "" }

        return "Вопрос \(questions.count) из \(maxQuestions)"
    }

    // Старт опроса
    func startSurvey() {
        guard !isSummarizing && !isLoadingQuestion else { return }

        messages.removeAll()
        questions.removeAll()
        answers.removeAll()
        resultText = nil
        isFinished = false
        isSummarizing = false

        Task {
            await generateNextQuestion()
        }
    }

    // Пришёл ответ пользователя
    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        // если уже всё закончили — просто сообщаем
        guard !isFinished else {
            messages.append(.init(
                text: "Опрос завершён. Нажми «Пройти ещё раз», чтобы начать заново.",
                isMe: false
            ))
            return
        }

        // если ещё не было ни одного вопроса — игнорируем ввод
        guard !questions.isEmpty else { return }

        messages.append(.init(text: trimmed, isMe: true))

        // если сейчас считаем итог — новые ответы не учитываем
        guard !isSummarizing else { return }

        answers.append(trimmed)

        Task {
            await generateNextQuestion()
        }
    }

    // MARK: - Генерация следующего вопроса

    private func generateNextQuestion() async {
        // если уже идёт подсчёт финала или всё закончено — не генерируем новые вопросы
        guard !isSummarizing && !isFinished else { return }

        let nextIndex = questions.count + 1

        // если вопросов уже достаточно — идём в финальный вывод
        if nextIndex > maxQuestions {
            await summarizeWithGPT()
            return
        }

        isLoadingQuestion = true
        defer { isLoadingQuestion = false }

        guard let question = await askGPTForNextQuestion(questionNumber: nextIndex) else {
            messages.append(.init(
                text: "Не удалось получить следующий вопрос. Попробуй позже.",
                isMe: false
            ))
            isFinished = true
            return
        }

        // если модель всё-таки решила завершить вопросы раньше лимита
        if question.trimmingCharacters(in: .whitespacesAndNewlines) == "[END]" {
            await summarizeWithGPT()
            return
        }

        questions.append(question)
        messages.append(.init(text: question, isMe: false))
    }

    // Запрос к модели за СЛЕДУЮЩИМ вопросом
    private func askGPTForNextQuestion(questionNumber: Int) async -> String? {
        guard let url = URL(string: "https://api.openai.com/v1/chat/completions") else { return nil }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let qaText = zip(questions, answers).enumerated().map { index, pair in
            let (q, a) = pair
            return "\(index + 1). Вопрос: \(q)\nОтвет: \(a)"
        }.joined(separator: "\n\n")

        let prompt = """
        Ты карьерный консультант. Разбираешься психологии и просто в жизни.

        Ты проводишь диалог-опрос с пользователем для определения его направленности в IT.
        Пользователь ничего не знает про IT и термины использовать не стоит. Стоит задавать вопросы
        которые ассоциативно приведут к правильному определению профессии. Стоит задавать вопросы про
        обычну жизнь чтобы как-то связать существующие навыки с будущей профессией.
        
        На основе уже заданных вопросов и ответов тебе нужно придумать СЛЕДУЮЩИЙ вопрос, который поможет лучше понять человека и его карьерные цели.

        Всего вопросов максимум \(maxQuestions).
        Номер следующего вопроса: \(questionNumber).

        История (может быть пустой):

        \(qaText)

        Если номер следующего вопроса больше \(maxQuestions), верни ровно строку:
        [END]

        Иначе верни только текст одного следующего вопроса на русском языке.
        Без нумерации, без кавычек, без вступлений и пояснений — только сам вопрос.
        """

        let body = ChatRequest(
            model: "gpt-4o-mini",
            messages: [
                .init(
                    role: "system",
                    content: "Ты дружелюбный карьерный консультант по IT. Задаёшь понятные вопросы по одному за раз."
                ),
                .init(role: "user", content: prompt)
            ]
        )

        do {
            request.httpBody = try JSONEncoder().encode(body)
            let (data, _) = try await URLSession.shared.data(for: request)
            let decoded = try JSONDecoder().decode(ChatResponse.self, from: data)
            return decoded.choices.first?.message.content
        } catch {
            print("Next question API error:", error)
            return nil
        }
    }

    // MARK: - Финальный ответ

    private func summarizeWithGPT() async {
        isSummarizing = true

        messages.append(.init(
            text: "Секунду, подведу итоги по твоим ответам…",
            isMe: false
        ))

        guard let summary = await askGPTSummary() else {
            messages.append(.init(
                text: "Не получилось обработать ответы. Попробуй позже.",
                isMe: false
            ))
            isSummarizing = false
            isFinished = true
            return
        }

        messages.append(.init(text: summary, isMe: false))
        resultText = summary
        isSummarizing = false
        isFinished = true
    }

    private func askGPTSummary() async -> String? {
        guard let url = URL(string: "https://api.openai.com/v1/chat/completions") else { return nil }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let qaText = zip(questions, answers).enumerated().map { index, pair in
            let (q, a) = pair
            return "\(index + 1). Вопрос: \(q)\nОтвет: \(a)"
        }.joined(separator: "\n\n")

        let prompt = """
        Ты карьерный консультант. Разбираешься психологии и просто в жизни.

        Пользователь ответил на вопросы:

        \(qaText)

        На основе этих ответов:
        - кратко опиши, что это за человек с точки зрения работы/учёбы;
        - предложи 2–3 возможных направления в IT;
        - дай 2–4 конкретных шага на ближайший месяц.

        Пиши дружелюбно и простым понятным языком, без жаргона и без мата.
        """

        let body = ChatRequest(
            model: "gpt-4o-mini",
            messages: [
                .init(
                    role: "system",
                    content: "Ты карьерный консультант по IT. Объясняешь просто и нейтрально."
                ),
                .init(role: "user", content: prompt)
            ]
        )

        do {
            request.httpBody = try JSONEncoder().encode(body)
            let (data, _) = try await URLSession.shared.data(for: request)
            let decoded = try JSONDecoder().decode(ChatResponse.self, from: data)
            return decoded.choices.first?.message.content
        } catch {
            print("Summary API error:", error)
            return nil
        }
    }
}

// MARK: - Вьюшки

struct MessageBubble: View {
    let message: Message

    var body: some View {
        HStack {
            if message.isMe { Spacer() }

            Text(message.text)
                .padding(12)
                .background(message.isMe ? Color.blue : Color.gray.opacity(0.2))
                .foregroundColor(message.isMe ? .white : .black)
                .cornerRadius(16)
                .frame(maxWidth: 260, alignment: message.isMe ? .trailing : .leading)

            if !message.isMe { Spacer() }
        }
        .padding(.horizontal)
        .padding(.vertical, 2)
    }
}

struct ContentView: View {
    @StateObject private var viewModel = ChatViewModel()
    @State private var input = ""

    var body: some View {
        Group {
            if viewModel.messages.isEmpty && !viewModel.isFinished {
                prestartView
            } else {
                mainSurveyView
            }
        }
        .ignoresSafeArea(.keyboard, edges: .bottom)
        .safeAreaInset(edge: .bottom) {
            if !viewModel.messages.isEmpty && !viewModel.isFinished {
                inputBar
            }
        }
    }

    // MARK: - Стартовый экран

    private var prestartView: some View {
        VStack(spacing: 16) {
            Spacer()

            Text("Сейчас мы определим, кто ты в IT")
                .font(.title.bold())
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            Button {
                viewModel.startSurvey()
            } label: {
                Text("Начать опрос")
                    .font(.headline)
                    .padding(.horizontal, 32)
                    .padding(.vertical, 14)
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isLoadingQuestion)

            if viewModel.isLoadingQuestion {
                ProgressView("Готовлю первый вопрос…")
                    .padding(.top, 8)
            }

            Spacer()
        }
        .padding()
    }

    // MARK: - Основной экран с чатом и результатом

    private var mainSurveyView: some View {
        VStack(spacing: 0) {
            headerAfterStart
            Divider()

            if let result = viewModel.resultText, viewModel.isFinished {
                // После завершения показываем только результат, со скроллом
                ScrollView {
                    resultView(result)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            } else {
                // Во время опроса показываем чат
                chatArea
            }
        }
    }

    private var headerAfterStart: some View {
        VStack(spacing: 8) {
            if viewModel.isFinished {
                Text("Опрос завершён")
                    .font(.headline)

                Button("Пройти ещё раз") {
                    viewModel.startSurvey()
                }
                .buttonStyle(.borderedProminent)
            } else {
                if !viewModel.progressText.isEmpty {
                    Text(viewModel.progressText)
                        .font(.title3.weight(.semibold))
                        .frame(maxWidth: .infinity)
                        .multilineTextAlignment(.center)
                }

                if viewModel.isLoadingQuestion {
                    Text("Формулирую следующий вопрос…")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
    }

    private var chatArea: some View {
        ZStack {
            if viewModel.messages.isEmpty {
                Text("Ожидаю вопрос…")
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding()
            }

            ScrollViewReader { proxy in
                ScrollView {
                    VStack {
                        ForEach(viewModel.messages) { msg in
                            MessageBubble(message: msg)
                                .id(msg.id)
                        }
                    }
                    .padding(.vertical)
                }
                .onChange(of: viewModel.messages.count) { _ in
                    if let last = viewModel.messages.last?.id {
                        withAnimation {
                            proxy.scrollTo(last, anchor: .bottom)
                        }
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
    }

    private func resultView(_ text: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Результат")
                .font(.title2.bold())

            Text(text)
                .font(.body)
        }
        .padding()
    }

    // MARK: - Input Bar

    private var inputBar: some View {
        let inputDisabled =
            viewModel.isSummarizing ||
            viewModel.isLoadingQuestion ||
            viewModel.isFinished ||
            viewModel.messages.isEmpty

        return VStack(spacing: 4) {
            HStack(spacing: 8) {
                // Многострочный TextField (iOS 17+, axis: .vertical)
                TextField(
                    "Напиши ответ",
                    text: $input,
                    axis: .vertical
                )
                .lineLimit(1...4)
                .textFieldStyle(.plain)
                .disabled(inputDisabled)

                Button {
                    let text = input
                    input = ""
                    viewModel.send(text)
                } label: {
                    Image(systemName: "paperplane.fill")
                        .font(.system(size: 18, weight: .semibold))
                }
                .disabled(inputDisabled)
                .opacity(inputDisabled ? 0.4 : 1.0)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .background(.ultraThinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            .shadow(radius: 4)
            .padding(.horizontal)
            .padding(.bottom, 8)
        }
    }
}

#Preview {
    ContentView()
}
