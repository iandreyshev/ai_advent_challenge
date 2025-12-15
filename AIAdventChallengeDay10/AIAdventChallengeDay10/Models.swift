//
//  Models.swift
//  AIAdventChallengeDay10
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

/// То, что сохраняем на диск, чтобы восстановиться после перезапуска.
struct PersistedAppState: Codable {
    var version: Int = 1
    
    var isCompressionEnabled: Bool
    var messages: [ChatMessage]
    var compressedSummary: String
    var sinceSummary: [ChatMessage]
    
    var tokensNoCompressionTotal: Int
    var tokensWithCompressionTotal: Int
}
