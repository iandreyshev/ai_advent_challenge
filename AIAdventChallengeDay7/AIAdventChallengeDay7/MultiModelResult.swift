//
//  MultiModelResult.swift
//  AIAdventChallengeDay7
//
//  Created by Ivan Andreyshev on 09.12.2025.
//

import Foundation

enum ModelProvider: String, CaseIterable, Identifiable {
    case openAI
    case yandex

    var id: String { rawValue }

    var displayName: String {
        switch self {
        case .openAI: return "OpenAI"
        case .yandex: return "YandexGPT"
        }
    }

    var badgeColorName: String {
        switch self {
        case .openAI: return "blue"
        case .yandex: return "orange"
        }
    }
}

struct ModelResult: Identifiable {
    let id = UUID()
    let provider: ModelProvider
    let text: String
    let promptTokens: Int
    let completionTokens: Int
    let totalTokens: Int
    let responseTime: TimeInterval
    var rating: Int?
}
