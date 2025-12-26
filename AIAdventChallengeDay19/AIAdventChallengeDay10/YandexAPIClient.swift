//
//  YandexAIClient.swift
//  AIAdventChallengeDay10
//
//  Created by Ivan Andreyshev on 12.12.2025.
//
import Foundation

/// Клиент для Yandex AI Studio (Foundation Models / TextGeneration.Completion)
final class YandexAIClient {

    // MARK: - Errors

    enum YandexAIError: Error, LocalizedError {
        case invalidResponse
        case serverError(String)
        case tokenLimitExceeded(String)

        var errorDescription: String? {
            switch self {
            case .invalidResponse:
                return "Неверный формат ответа от Yandex AI Studio API."
            case .serverError(let msg):
                return "Ошибка сервера: \(msg)"
            case .tokenLimitExceeded(let msg):
                return "Превышен лимит токенов: \(msg)"
            }
        }
    }

    // MARK: - Public API

    /// model: сюда передавай modelUri (например "gpt://<FOLDER_ID>/yandexgpt-lite")
    func send(
        prompt: String,
        model: String,
        maxOutputTokens: Int? = 800,
        temperature: Double = 1.0
    ) async throws -> LLMResult {

        var request = URLRequest(url: AppSecrets.baseURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Api-Key \(AppSecrets.yandexAPIKey)", forHTTPHeaderField: "Authorization")

        let body = YandexCompletionRequest(
            modelUri: model,
            completionOptions: .init(
                stream: false,
                temperature: temperature,
                maxTokens: maxOutputTokens.map { String($0) }
            ),
            messages: [
                .init(role: "user", text: prompt)
            ]
        )

        request.httpBody = try JSONEncoder().encode(body)

        let start = Date()
        let (data, response) = try await URLSession.shared.data(for: request)
        let elapsed = Date().timeIntervalSince(start)

        #if DEBUG
        if let raw = String(data: data, encoding: .utf8) {
            print("YANDEX RAW RESPONSE:\n\(raw)")
        }
        #endif

        // HTTP errors
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            let message = (try? decodeYandexErrorMessage(from: data)) ?? "HTTP \(http.statusCode)"

            if message.localizedCaseInsensitiveContains("token")
                && (message.localizedCaseInsensitiveContains("limit")
                    || message.localizedCaseInsensitiveContains("too large")
                    || message.localizedCaseInsensitiveContains("context")) {
                throw YandexAIError.tokenLimitExceeded(message)
            }

            throw YandexAIError.serverError(message)
        }

        // ✅ У Яндекса полезные поля лежат внутри result
        do {
            let decoded = try JSONDecoder().decode(YandexCompletionEnvelope.self, from: data)
            let result = decoded.result

            let text = result.alternatives.first?.message?.text ?? ""

            let inputTokens = result.usage?.inputTextTokens.flatMap(Int.init)
            let outputTokens = result.usage?.completionTokens.flatMap(Int.init)
            let totalTokens = result.usage?.totalTokens.flatMap(Int.init)

            return LLMResult(
                text: text,
                inputTokens: inputTokens,
                outputTokens: outputTokens,
                totalTokens: totalTokens,
                elapsedSeconds: elapsed
            )
        } catch let decodingError as DecodingError {
            #if DEBUG
            print("YANDEX DECODING ERROR: \(decodingError)")
            #endif
            throw YandexAIError.invalidResponse
        } catch {
            throw YandexAIError.invalidResponse
        }
    }

    // MARK: - Error decoding (best-effort)

    private func decodeYandexErrorMessage(from data: Data) throws -> String {
        if let obj = try? JSONDecoder().decode([String: String].self, from: data),
           let msg = obj["message"] {
            return msg
        }
        if let env = try? JSONDecoder().decode(YandexAPIErrorEnvelope.self, from: data) {
            return env.message
        }
        return "Unknown error"
    }
}

// MARK: - Request models

private struct YandexCompletionRequest: Encodable {
    let modelUri: String
    let completionOptions: CompletionOptions
    let messages: [Message]

    struct CompletionOptions: Encodable {
        let stream: Bool
        let temperature: Double?
        /// maxTokens — string (int64)
        let maxTokens: String?
    }

    struct Message: Encodable {
        let role: String   // "system" | "assistant" | "user"
        let text: String
    }
}

// MARK: - Response models (✅ envelope -> result)

private struct YandexCompletionEnvelope: Decodable {
    let result: YandexCompletionResult
}

private struct YandexCompletionResult: Decodable {
    let alternatives: [Alternative]
    let usage: Usage?
    let modelVersion: String?

    struct Alternative: Decodable {
        let message: Message?
        let status: String?
    }

    struct Message: Decodable {
        let role: String?
        let text: String?
    }

    struct Usage: Decodable {
        let inputTextTokens: String?
        let completionTokens: String?
        let totalTokens: String?
    }
}

// MARK: - Simple error envelope

private struct YandexAPIErrorEnvelope: Decodable {
    let message: String
}
