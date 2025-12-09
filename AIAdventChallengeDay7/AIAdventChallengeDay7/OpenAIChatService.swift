//
//  OpenAIChatService.swift
//  AIAdventChallengeDay7
//
//  Created by Ivan Andreyshev on 09.12.2025.
//

import Foundation

struct OpenAIChatService {
    private let baseURL = URL(string: "https://api.openai.com/v1/chat/completions")!
    private let model = "gpt-4.1-mini" // можно поменять на любой поддерживаемый

    // MARK: - Request models

    struct Message: Encodable {
        let role: String   // "user", "system", "assistant"
        let content: String
    }

    struct RequestBody: Encodable {
        let model: String
        let messages: [Message]
        let temperature: Double?
    }

    // MARK: - Response models

    struct ResponseBody: Decodable {
        struct Choice: Decodable {
            struct Message: Decodable {
                let role: String
                let content: String
            }
            let message: Message
        }

        struct Usage: Decodable {
            let prompt_tokens: Int
            let completion_tokens: Int
            let total_tokens: Int
        }

        let choices: [Choice]
        let usage: Usage?
    }

    // MARK: - Public API

    func send(prompt: String) async throws -> ModelResult {
        var request = URLRequest(url: baseURL)
        request.httpMethod = "POST"
        request.addValue("Bearer \(openAIApiKey)", forHTTPHeaderField: "Authorization")
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = RequestBody(
            model: model,
            messages: [
                .init(role: "user", content: prompt)
            ],
            temperature: 1.0   // можешь сделать параметром, если нужно
        )
        request.httpBody = try JSONEncoder().encode(body)

        let start = Date()
        let (data, response) = try await URLSession.shared.data(for: request)
        let duration = Date().timeIntervalSince(start)

        guard let http = response as? HTTPURLResponse,
              (200...299).contains(http.statusCode) else {
            let text = String(data: data, encoding: .utf8) ?? ""
            throw NSError(
                domain: "OpenAIChatService",
                code: 1,
                userInfo: [NSLocalizedDescriptionKey: "OpenAI error: \(text)"]
            )
        }

        let decoded = try JSONDecoder().decode(ResponseBody.self, from: data)
        guard let choice = decoded.choices.first else {
            throw NSError(
                domain: "OpenAIChatService",
                code: 2,
                userInfo: [NSLocalizedDescriptionKey: "OpenAI: no choices"]
            )
        }

        let usage = decoded.usage

        return ModelResult(
            provider: .openAI,
            text: choice.message.content,
            promptTokens: usage?.prompt_tokens ?? 0,
            completionTokens: usage?.completion_tokens ?? 0,
            totalTokens: usage?.total_tokens ?? 0,
            responseTime: duration,
            rating: nil
        )
    }
}
