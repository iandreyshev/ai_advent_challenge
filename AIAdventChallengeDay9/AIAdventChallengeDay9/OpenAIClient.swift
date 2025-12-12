//
//  OpenAIClient.swift
//  AIAdventChallengeDay9
//
//  Created by Ivan Andreyshev on 12.12.2025.
//

import Foundation

// MARK: - Request/Response Models (Responses API)

struct OpenAIRequestBody: Encodable {
    let model: String
    let input: String
    let max_output_tokens: Int?
}

struct OpenAIResponse: Decodable {
    let output: [OpenAIMessage]?
    let usage: Usage?
}

struct OpenAIMessage: Decodable {
    let id: String?
    let type: String?
    let status: String?
    let content: [OpenAIContent]?
    let role: String?
}

struct OpenAIContent: Decodable {
    let type: String?
    let text: String?
}

struct Usage: Decodable {
    let input_tokens: Int?
    let output_tokens: Int?
    let total_tokens: Int?
}

struct OpenAIAPIError: Decodable {
    struct InnerError: Decodable {
        let message: String
        let type: String?
    }
    let error: InnerError
}

// MARK: - Client

final class OpenAIClient {
    private let apiKey: String

    init(apiKey: String) {
        self.apiKey = apiKey
    }

    enum OpenAIError: Error, LocalizedError {
        case invalidResponse
        case tokenLimitExceeded(String)
        case serverError(String)

        var errorDescription: String? {
            switch self {
            case .invalidResponse:
                return "Неверный формат ответа от API."
            case .tokenLimitExceeded(let msg):
                return "Превышен лимит токенов: \(msg)"
            case .serverError(let msg):
                return "Ошибка сервера: \(msg)"
            }
        }
    }

    func send(prompt: String,
              model: String,
              maxOutputTokens: Int? = 800) async throws -> LLMResult {

        guard let url = URL(string: "https://api.openai.com/v1/responses") else {
            throw OpenAIError.invalidResponse
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")

        let body = OpenAIRequestBody(
            model: model,
            input: prompt,
            max_output_tokens: maxOutputTokens
        )

        request.httpBody = try JSONEncoder().encode(body)

        let start = Date()
        let (data, response) = try await URLSession.shared.data(for: request)
        let elapsed = Date().timeIntervalSince(start)

        #if DEBUG
        if let raw = String(data: data, encoding: .utf8) {
            print("RAW RESPONSE:\n\(raw)")
        }
        #endif

        if let http = response as? HTTPURLResponse,
           !(200...299).contains(http.statusCode) {

            if let apiError = try? JSONDecoder().decode(OpenAIAPIError.self, from: data) {
                let message = apiError.error.message

                if message.localizedCaseInsensitiveContains("maximum context length")
                    || message.localizedCaseInsensitiveContains("context length")
                    || message.localizedCaseInsensitiveContains("context window") {
                    throw OpenAIError.tokenLimitExceeded(message)
                } else {
                    throw OpenAIError.serverError(message)
                }
            } else {
                throw OpenAIError.serverError("HTTP \(http.statusCode)")
            }
        }

        do {
            let decoded = try JSONDecoder().decode(OpenAIResponse.self, from: data)

            let text = (decoded.output ?? [])
                .flatMap { $0.content ?? [] }
                .filter { $0.type == "output_text" }
                .compactMap { $0.text }
                .joined(separator: "\n")

            return LLMResult(
                text: text,
                inputTokens: decoded.usage?.input_tokens,
                outputTokens: decoded.usage?.output_tokens,
                totalTokens: decoded.usage?.total_tokens,
                elapsedSeconds: elapsed
            )
        } catch {
            throw OpenAIError.invalidResponse
        }
    }
}
