//
//  AppSecrets.swift
//  AIAdventChallengeDay9
//
//  Created by Ivan Andreyshev on 12.12.2025.
//

import Foundation

enum AppSecrets {
    // ⚠️ Учебный вариант. Для продакшена вынести на backend / xcconfig.
    static let openAIAPIKey: String = ""
    static let openAIModel: String = "gpt-4o-mini"
    
    static let yandexAPIKey: String = ""
    static let yandexFolderID: String = ""
    static let baseURL = URL(string: "https://llm.api.cloud.yandex.net/foundationModels/v1/completion")!
    static let yandexModelUri: String = "gpt://\(yandexFolderID)/yandexgpt-lite"
}
