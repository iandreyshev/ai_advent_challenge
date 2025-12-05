//
//  ContentView.swift
//  AIAdventChallengeDay5
//
//  Created by Ivan Andreyshev on 05.12.2025.
//
import Combine
import SwiftUI
import UIKit

// MARK: - Персоны (роли)

enum ChatPersona: String, CaseIterable, Identifiable {
    case hardcoreDev
    case funnyDriver
    case girlfriend

    var id: String { rawValue }

    var title: String {
        switch self {
        case .hardcoreDev: return "Программист"
        case .funnyDriver: return "Весёлый водитель"
        case .girlfriend: return "Моя девушка"
        }
    }

    var prompt: String {
        switch self {
        case .hardcoreDev:
            return """
            Ты опытный и очень увлечённый программист, который обожает вникать в детали.
            Характер:
            - говоришь по-русски, но технически точно;
            - любишь объяснять через глубину: архитектура, паттерны, производительность;
            - не ленишься расписать шаги по пунктам;
            - можешь слегка шутить в стиле “задротского” юмора, но без грубости и токсичности.

            Стиль ответа:
            - сначала короткий итог в 1–2 предложения;
            - затем чёткие шаги/пункты (списком), можно с кодом;
            - если даёшь код — он должен компилироваться и быть современным (актуальный Swift/SwiftUI);
            - если вопрос не про программирование, всё равно объясняй логично и структурированно.

            Избегай:
            - оскорблений, снобизма и токсичных шуток;
            - чрезмерной воды — лучше чётко по делу.
            """

        case .funnyDriver:
            return """
            Ты весёлый, общительный водитель (такси/дальнобой/автобус — неважно), который многое видел в жизни.
            Характер:
            - говоришь простым, разговорным русским языком;
            - иногда используешь метафоры из вождения: дороги, пробки, повороты, маршрут;
            - можешь чуть-чуть шутить, но остаёшься доброжелательным и уважительным.

            Стиль ответа:
            - сначала короткий ответ по сути, без лишней философии;
            - затем можешь привести простое сравнение или историю “с дороги”, чтобы было понятнее;
            - объяснения должны оставаться полезными и понятными даже новичку.

            Избегай:
            - грубостей, мата, грубого стёба;
            - сленга, который может показаться оскорбительным или дискриминирующим.
            """

        case .girlfriend:
            return """
            Ты играешь роль заботливой, поддерживающей девушки пользователя.
            Характер:
            - ты тёплая, внимательная, эмпатичная;
            - важно, чтобы человек почувствовал поддержку и принятие;
            - можешь использовать мягкие обращения вроде “слушай”, “давай подумаем”, но не перегибай с уменьшительно-ласкательными.

            Стиль ответа:
            - сначала отзеркаль эмоции пользователя и покажи, что ты его понимаешь;
            - затем дай спокойный, рациональный совет или взгляд со стороны;
            - если вопрос сложный — предложи несколько вариантов действий и поддержи любое взвешенное решение.

            Избегай:
            - ревности, пассивной агрессии, манипуляций;
            - токсичных сообщений (типа “сам виноват”);
            - откровенно интимного или сексуального содержания — держимся в рамках безопасного, поддерживающего общения.
            """
        }
    }
}

// MARK: - Модель сообщения для UI

struct Message: Identifiable {
    let id = UUID()
    let text: String
    let isMe: Bool
}

// MARK: - Модели для Responses API

private struct ResponsesRequest: Encodable {
    let model: String
    let input: String
    let instructions: String
    let previous_response_id: String?
}

private struct ResponsesResponse: Decodable {
    struct OutputItem: Decodable {
        struct ContentItem: Decodable {
            let type: String
            let text: String?
        }

        let type: String
        let role: String?
        let content: [ContentItem]?
    }

    let id: String
    let output: [OutputItem]
}

// MARK: - ViewModel

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []
    @Published var selectedPersona: ChatPersona = .hardcoreDev

    /// ID последнего ответа модели — используется для продолжения диалога на стороне OpenAI
    private var lastResponseId: String?

    var currentPrompt: String {
        selectedPersona.prompt
    }

    func selectPersona(_ persona: ChatPersona) {
        selectedPersona = persona
        // по желанию можно сбрасывать диалог при смене роли:
        // resetConversation()
        // сейчас оставляем историю, просто дальше ответы будут уже с новым промптом
    }

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        messages.append(.init(text: trimmed, isMe: true))

        Task {
            let reply = await askGPT(userText: trimmed) ?? "Не получилось ответить."
            messages.append(.init(text: reply, isMe: false))
        }
    }

    func resetConversation() {
        lastResponseId = nil
        messages.removeAll()
    }

    private func askGPT(userText: String) async -> String? {
        guard let url = URL(string: "https://api.openai.com/v1/responses") else { return nil }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ResponsesRequest(
            model: "gpt-4o-mini",
            input: userText,
            instructions: currentPrompt, // 👈 выбранная роль
            previous_response_id: lastResponseId // 👈 продолжаем диалог
        )

        do {
            request.httpBody = try JSONEncoder().encode(body)

            let (data, response) = try await URLSession.shared.data(for: request)

            if let http = response as? HTTPURLResponse {
                print("STATUS:", http.statusCode)
            }

            if let jsonString = String(data: data, encoding: .utf8) {
                print("RAW RESPONSE:", jsonString)
            }

            let decoded = try JSONDecoder().decode(ResponsesResponse.self, from: data)

            // сохраняем id ответа, чтобы связать следующий запрос
            lastResponseId = decoded.id

            if let messageItem = decoded.output.first(where: { $0.type == "message" }),
               let textItem = messageItem.content?.first(where: { $0.type == "output_text" }),
               let text = textItem.text
            {
                return text
            } else {
                return nil
            }
        } catch {
            print("API error:", error)
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

            HStack(alignment: .top, spacing: 8) {
                Text(message.text)
                    .multilineTextAlignment(message.isMe ? .trailing : .leading)

                Button {
                    UIPasteboard.general.string = message.text
                } label: {
                    Image(systemName: "doc.on.doc")
                        .font(.system(size: 12, weight: .semibold))
                        .opacity(0.7)
                }
                .buttonStyle(.plain)
            }
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
        VStack(spacing: 0) {
            personaSelectorBar

            Divider()

            ZStack {
                if viewModel.messages.isEmpty {
                    Text("Выбери роль сверху и напиши сообщение.")
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
        }
        .ignoresSafeArea(.keyboard, edges: .bottom)
        .safeAreaInset(edge: .bottom) {
            inputBar
        }
    }

    // MARK: - Панель выбора роли

    private var personaSelectorBar: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Роль собеседника")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Spacer()
                Button("Сбросить диалог") {
                    viewModel.resetConversation()
                }
                .font(.caption)
            }

            HStack(spacing: 8) {
                ForEach(ChatPersona.allCases) { persona in
                    Button {
                        viewModel.selectPersona(persona)
                    } label: {
                        Text(persona.title)
                            .font(.caption)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 8)
                            .frame(maxWidth: .infinity)
                            .lineLimit(2)
                    }
                    .buttonStyle(.borderedProminent)
                    .tint(viewModel.selectedPersona == persona ? .blue : .gray.opacity(0.6))
                }
            }
        }
        .padding(.horizontal)
        .padding(.top)
        .padding(.bottom)
    }

    // MARK: - Инпут-бар

    private var inputBar: some View {
        HStack(spacing: 8) {
            TextField("Введите сообщение", text: $input, axis: .vertical)
                .lineLimit(1...4)
                .textFieldStyle(.plain)

            Button {
                let text = input
                input = ""
                viewModel.send(text)
            } label: {
                Image(systemName: "paperplane.fill")
                    .font(.system(size: 18, weight: .semibold))
            }
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

#Preview {
    ContentView()
}
