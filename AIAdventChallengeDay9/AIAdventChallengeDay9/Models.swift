//
//  Models.swift
//  AIAdventChallengeDay9
//
//  Created by Ivan Andreyshev on 12.12.2025.
//

import Foundation

enum ChatRole: String, Codable {
    case user
    case assistant
}

struct ChatMessage: Identifiable, Codable, Hashable {
    let id: UUID
    let role: ChatRole
    let text: String
    let createdAt: Date

    init(role: ChatRole, text: String) {
        self.id = UUID()
        self.role = role
        self.text = text
        self.createdAt = Date()
    }
}

struct LLMResult {
    let text: String
    let inputTokens: Int?
    let outputTokens: Int?
    let totalTokens: Int?
    let elapsedSeconds: Double
}
