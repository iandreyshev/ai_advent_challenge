//
//  OpenAIClient.swift
//  AIAdventChallengeDay8
//
//  Created by Ivan Andreyshev on 10.12.2025.
//

import Foundation

struct OpenAIRequestBody: Encodable {
    let model: String
    let input: String

    init(model: String, input: String) {
        self.model = model
        self.input = input
    }
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
    // annotations, logprobs нам не нужны — можно не описывать
}

struct Usage: Decodable {
    let input_tokens: Int?
    let output_tokens: Int?
    let total_tokens: Int?
}

struct LLMResult {
    let text: String
    let inputTokens: Int?
    let outputTokens: Int?
    let totalTokens: Int?
    let elapsedSeconds: Double
}

final class OpenAIClient {
    enum OpenAIError: Error, LocalizedError {
        case invalidResponse
        case tokenLimitExceeded(String)
        case serverError(String)

        var errorDescription: String? {
            switch self {
            case .invalidResponse:
                return "Неверный формат ответа от API."
            case let .tokenLimitExceeded(message):
                return "Превышен лимит токенов: \(message)"
            case let .serverError(message):
                return "Ошибка сервера: \(message)"
            }
        }
    }

    func send(prompt: String) async throws -> LLMResult {
        guard let url = URL(string: "https://api.openai.com/v1/responses") else {
            throw OpenAIError.invalidResponse
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(openAIApiKey)", forHTTPHeaderField: "Authorization")

        let body = OpenAIRequestBody(
            model: openAIApiModelName,
            input: prompt
        )

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(body)

        let start = Date()
        let (data, response) = try await URLSession.shared.data(for: request)
        let elapsed = Date().timeIntervalSince(start)

        #if DEBUG
        if let jsonString = String(data: data, encoding: .utf8) {
            print("RAW RESPONSE:\n\(jsonString)")
        }
        #endif

        // Проверяем HTTP-статус
        if let http = response as? HTTPURLResponse,
           !(200 ... 299).contains(http.statusCode)
        {
            if let apiError = try? JSONDecoder().decode(OpenAIAPIError.self, from: data) {
                let message = apiError.error.message
                if message.localizedCaseInsensitiveContains("maximum context length")
                    || message.localizedCaseInsensitiveContains("context length")
                    || message.localizedCaseInsensitiveContains("context window")
                {
                    throw OpenAIError.tokenLimitExceeded(message)
                } else {
                    throw OpenAIError.serverError(message)
                }
            } else {
                throw OpenAIError.serverError("HTTP \(http.statusCode)")
            }
        }

        let decoder = JSONDecoder()

        do {
            let apiResponse = try decoder.decode(OpenAIResponse.self, from: data)
            
            let messages = apiResponse.output ?? []
            let text = messages
                .flatMap { $0.content ?? [] }
                .filter { $0.type == "output_text" }
                .compactMap { $0.text }
                .joined(separator: "\n")
            
            let usage = apiResponse.usage
            
            return LLMResult(
                text: text,
                inputTokens: usage?.input_tokens,
                outputTokens: usage?.output_tokens,
                totalTokens: usage?.total_tokens,
                elapsedSeconds: elapsed
            )
            
        } catch let decodingError as DecodingError {
            print("DECODING ERROR: \(decodingError)")
            throw OpenAIError.invalidResponse
        } catch {
            throw error
        }
    }
}

/// Формат ошибки OpenAI (упрощённый)
struct OpenAIAPIError: Decodable {
    struct InnerError: Decodable {
        let message: String
        let type: String?
    }

    let error: InnerError
}
