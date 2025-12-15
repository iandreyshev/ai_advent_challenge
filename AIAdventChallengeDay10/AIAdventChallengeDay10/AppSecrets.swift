//
//  AppSecrets.swift
//  AIAdventChallengeDay10
//
//  Created by Ivan Andreyshev on 12.12.2025.
//

import Foundation

enum AppSecrets {
    static let yandexAPIKey: String = ""
    static let yandexFolderID: String = ""
    static let baseURL = URL(string: "https://llm.api.cloud.yandex.net/foundationModels/v1/completion")!
    static let yandexModelUri: String = "gpt://\(yandexFolderID)/yandexgpt-lite"
}
