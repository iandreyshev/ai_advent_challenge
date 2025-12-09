//
//  YandexChatService.swift
//  AIAdventChallengeDay7
//
//  Created by Ivan Andreyshev on 09.12.2025.
//

import Foundation

struct YandexChatService {
    private let baseURL = URL(string: "https://llm.api.cloud.yandex.net/foundationModels/v1/completion")!

    private var modelUri: String {
        "gpt://\(yandexFolderId)/yandexgpt/latest"
    }
    
    struct Message: Encodable {
        let role: String
        let text: String
    }

    struct CompletionOptions: Encodable {
        let stream: Bool
        let maxTokens: Int
    }

    struct RequestBody: Encodable {
        let modelUri: String
        let completionOptions: CompletionOptions
        let messages: [Message]
    }

    struct ResponseBody: Decodable {
        struct Alternative: Decodable {
            struct Message: Decodable {
                let text: String?
            }
            let message: Message
            let status: String?
        }

        struct Usage: Decodable {
            let inputTextTokens: String?
            let completionTokens: String?
            let totalTokens: String?
        }

        struct Result: Decodable {
            let alternatives: [Alternative]
            let usage: Usage?
            let modelVersion: String?
        }

        let result: Result
    }

    func send(prompt: String) async throws -> ModelResult {
        var request = URLRequest(url: baseURL)
        request.httpMethod = "POST"
        request.addValue("Bearer \(yandexApiKey)", forHTTPHeaderField: "Authorization")
        request.addValue(yandexFolderId, forHTTPHeaderField: "x-folder-id")
        request.addValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = RequestBody(
            modelUri: modelUri,
            completionOptions: .init(
                stream: false,
                maxTokens: 512   // можно вынести в конфиг/поставить больше
            ),
            messages: [
                .init(role: "user", text: prompt)
            ]
        )
        request.httpBody = try JSONEncoder().encode(body)

        let start = Date()
        let (data, response) = try await URLSession.shared.data(for: request)
        let duration = Date().timeIntervalSince(start)

        print("Yandex raw:", String(data: data, encoding: .utf8) ?? "no utf8")

        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let text = String(data: data, encoding: .utf8) ?? ""
            throw NSError(domain: "YandexChatService", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "Yandex error: \(text)"])
        }

        let decoded = try JSONDecoder().decode(ResponseBody.self, from: data)
        guard let alt = decoded.result.alternatives.first else {
            throw NSError(domain: "YandexChatService", code: 2,
                          userInfo: [NSLocalizedDescriptionKey: "Yandex: no alternatives"])
        }

        let usage = decoded.result.usage
        let promptTokens = Int(usage?.inputTextTokens ?? "") ?? 0
        let completionTokens = Int(usage?.completionTokens ?? "") ?? 0
        let totalTokens = Int(usage?.totalTokens ?? "") ?? 0

        return ModelResult(
            provider: .yandex,
            text: alt.message.text ?? "",
            promptTokens: promptTokens,
            completionTokens: completionTokens,
            totalTokens: totalTokens,
            responseTime: duration,
            rating: nil
        )
    }
}
