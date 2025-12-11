//
//  ContentView.swift
//  AIAdventChallengeDay8
//
//  Created by Ivan Andreyshev on 10.12.2025.
//

import SwiftUI

struct ContentView: View {
    private let openAIClient = OpenAIClient()
    
    @State private var prompt: String = ""
    @State private var responseText: String = ""
    
    @State private var inputTokens: Int?
    @State private var outputTokens: Int?
    @State private var totalTokens: Int?
    
    @State private var promptWordCount: Int = 0
    @State private var responseWordCount: Int = 0
    
    @State private var elapsedSeconds: Double?
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?
    @State private var tokenLimitError: Bool = false
    
    @FocusState private var isPromptFocused: Bool   // 👈 добавили
    
    var body: some View {
        NavigationStack {
            ScrollView { // 👈 всё содержимое в ScrollView
                VStack(alignment: .leading, spacing: 16) {
                    
                    // 👇 Заголовок теперь часть скролла, он тоже "уезжает"
                    Text("LLM Token Monitor")
                        .font(.largeTitle)
                        .bold()
                        .padding(.bottom, 4)
                    
                    // Ввод запроса
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Запрос к модели")
                            .font(.headline)

                        ZStack(alignment: .topLeading) {
                            if prompt.isEmpty {
                                Text("Введите ваш запрос...")
                                    .foregroundColor(.gray.opacity(0.6))
                                    .padding(.horizontal, 14)
                                    .padding(.vertical, 12)
                            }

                            TextEditor(text: $prompt)
                                .frame(minHeight: 120)
                                .padding(8)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 8)
                                        .stroke(Color.gray.opacity(0.3))
                                )
                                .focused($isPromptFocused)
                                .onChange(of: prompt) { newValue in
                                    promptWordCount = wordCount(newValue)
                                }
                        }

                        HStack {
                            Spacer()

                            Button("Вставить пример") {
                                prompt = hardcodedLongPrompt
                            }
                            .font(.caption)

                            Button("Очистить") {
                                prompt = ""
                            }
                            .font(.caption)
                        }

                        Text("Слов в запросе: \(promptWordCount)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    // Основная кнопка отправки (на экране)
                    Button {
                        send()
                    } label: {
                        HStack {
                            if isLoading {
                                ProgressView()
                            }
                            Text("Отправить запрос")
                        }
                        .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(isLoading || prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                    
                    // Ошибка
                    if let errorMessage {
                        Text(errorMessage)
                            .foregroundColor(tokenLimitError ? .red : .orange)
                            .font(.footnote)
                            .padding(6)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(tokenLimitError ? Color.red.opacity(0.1) : Color.orange.opacity(0.1))
                            )
                    }
                    
                    // Ответ
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Ответ модели")
                            .font(.headline)
                        
                        ScrollView {
                            Text(responseText.isEmpty ? "Ответа пока нет" : responseText)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(8)
                        }
                        .frame(minHeight: 120, maxHeight: 220)
                        .overlay(
                            RoundedRectangle(cornerRadius: 8)
                                .stroke(Color.gray.opacity(0.3))
                        )
                        
                        Text("Слов в ответе: \(responseWordCount)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                    
                    // Статистика токенов и времени
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Статистика")
                            .font(.headline)
                        
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Токены запроса: \(inputTokens ?? 0)")
                                Text("Токены ответа: \(outputTokens ?? 0)")
                                Text("Всего токенов: \(totalTokens ?? 0)")
                            }
                            Spacer()
                        }
                        .font(.caption)
                        
                        if let elapsedSeconds {
                            Text(String(format: "Время ответа: %.2f сек", elapsedSeconds))
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }
                    
                    Spacer(minLength: 20)
                }
                .padding()
            }
            // Чтобы контент не ужимался при появлении клавиатуры,
            // а уходил под неё и скроллился:
            .ignoresSafeArea(.keyboard, edges: .bottom)
            
            // Кнопка над клавиатурой (iOS toolbar над клавой)
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button {
                        send()
                    } label: {
                        if isLoading {
                            ProgressView()
                        } else {
                            Text("Отправить")
                                .bold()
                        }
                    }
                    .disabled(isLoading || prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }
    
    // MARK: - Actions
    
    private func send() {
        guard !prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        isPromptFocused = false
        
        Task {
            await callModel()
        }
    }
    
    private func callModel() async {
        isLoading = true
        errorMessage = nil
        tokenLimitError = false
        
        do {
            let result = try await openAIClient.send(prompt: prompt)
            
            responseText = result.text
            responseWordCount = wordCount(responseText)
            
            inputTokens = result.inputTokens
            outputTokens = result.outputTokens
            totalTokens = result.totalTokens
            elapsedSeconds = result.elapsedSeconds
            
        } catch let error as OpenAIClient.OpenAIError {
            errorMessage = error.localizedDescription
            if case .tokenLimitExceeded = error {
                tokenLimitError = true
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
}
