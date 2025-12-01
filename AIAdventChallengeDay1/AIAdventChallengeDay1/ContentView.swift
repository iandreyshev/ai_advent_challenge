//
//  ContentView.swift
//  AIAdventChallengeDay1
//
//  Created by Ivan Andreyshev on 02.12.2025.
//

import Combine
import SwiftUI

struct Message: Identifiable {
    let id = UUID()
    let text: String
    let isMe: Bool
}

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

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var messages: [Message] = []

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        // добавляем своё сообщение
        messages.append(.init(text: trimmed, isMe: true))

        Task {
            let reply = await askGPT(userText: trimmed) ?? "Не получилось ответить, брат."
            messages.append(.init(text: reply, isMe: false))
        }
    }

    private func askGPT(userText: String) async -> String? {
        guard let url = URL(string: "https://api.openai.com/v1/chat/completions") else { return nil }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.addValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ChatRequest(
            model: "gpt-4o-mini",
            messages: [
                .init(role: "system", content: "Ты друг-программист, который отвечает в стиле фильмов Брат 2 и Жмурки"),
                .init(role: "user", content: userText)
            ]
        )
        
        do {
            request.httpBody = try JSONEncoder().encode(body)
            
            let (data, response) = try await URLSession.shared.data(for: request)
            
            // 👉 Посмотрим статус
            if let http = response as? HTTPURLResponse {
                print("STATUS:", http.statusCode)
            }
            
            // 👉 Посмотрим сырой JSON
            if let jsonString = String(data: data, encoding: .utf8) {
                print("RAW RESPONSE:", jsonString)
            }
            
            // Пробуем декодить как нормальный ответ
            let decoded = try JSONDecoder().decode(ChatResponse.self, from: data)
            return decoded.choices.first?.message.content
            
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
        ZStack {
            // Плейсхолдер по центру
            if viewModel.messages.isEmpty {
                Text("В чате ещё нет сообщений")
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding()
            }

            // Чат
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
        .ignoresSafeArea(.keyboard, edges: .bottom)
        .safeAreaInset(edge: .bottom) {
            inputBar
        }
    }

    private var inputBar: some View {
        HStack(spacing: 8) {
            TextField("Введите сообщение", text: $input)
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
