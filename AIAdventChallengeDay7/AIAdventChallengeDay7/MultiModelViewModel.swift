//
//  MultiModelViewModel.swift
//  AIAdventChallengeDay7
//
//  Created by Ivan Andreyshev on 09.12.2025.
//

import Combine
import Foundation
import SwiftUI

@MainActor
final class MultiModelViewModel: ObservableObject {
    @Published var prompt: String = ""
    @Published var selectedProviders: Set<ModelProvider> = [.openAI, .yandex]
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    @Published var results: [ModelResult] = []

    private let openAIService = OpenAIChatService()
    private let yandexService = YandexChatService()

    var canSend: Bool {
        !isLoading
            && !prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            && !selectedProviders.isEmpty
    }

    func toggle(_ provider: ModelProvider) {
        if selectedProviders.contains(provider) {
            selectedProviders.remove(provider)
        } else {
            selectedProviders.insert(provider)
        }
    }

    func setRating(_ rating: Int, for id: UUID) {
        if let index = results.firstIndex(where: { $0.id == id }) {
            results[index].rating = rating
        }
    }

    @MainActor
    func send() async {
        let trimmed = prompt.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        isLoading = true
        errorMessage = nil
        results = []

        var collectedErrors: [String] = []
        var collectedResults: [ModelResult] = []

        // список задач
        var tasks: [Task<ModelResult?, Never>] = []

        if selectedProviders.contains(.openAI) {
            tasks.append(
                Task {
                    do {
                        return try await openAIService.send(prompt: trimmed)
                    } catch {
                        collectedErrors.append("OpenAI: \(error.localizedDescription)")
                        return nil
                    }
                }
            )
        }

        if selectedProviders.contains(.yandex) {
            tasks.append(
                Task {
                    do {
                        return try await yandexService.send(prompt: trimmed)
                    } catch {
                        collectedErrors.append("Yandex: \(error.localizedDescription)")
                        return nil
                    }
                }
            )
        }

        // дождаться выполнения всех задач
        for task in tasks {
            if let result = await task.value {
                collectedResults.append(result)
            }
        }

        // сортировка, как раньше
        results = collectedResults.sorted { $0.provider.rawValue < $1.provider.rawValue }

        // объединяем ошибки
        if !collectedErrors.isEmpty {
            errorMessage = collectedErrors.joined(separator: "\n")
            print(errorMessage ?? "")
        }

        isLoading = false
    }
}
