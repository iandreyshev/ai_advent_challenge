//
//  ChatPersistence.swift
//  AIAdventChallengeDay10
//
//  Created by Ivan Andreyshev on 15.12.2025.
//

import Foundation

enum ChatPersistence {
    private static let fileName = "chat_state_v1.json"

    private static var fileURL: URL {
        let fm = FileManager.default
        let dir = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let bundleID = Bundle.main.bundleIdentifier ?? "AIAdventChallengeDay10"
        let appDir = dir.appendingPathComponent(bundleID, isDirectory: true)

        if !fm.fileExists(atPath: appDir.path) {
            try? fm.createDirectory(at: appDir, withIntermediateDirectories: true)
        }

        return appDir.appendingPathComponent(fileName)
    }

    static func save(_ state: PersistedAppState) {
        do {
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted]
            let data = try encoder.encode(state)
            try data.write(to: fileURL, options: [.atomic])
        } catch {
            print("ChatPersistence.save error: \(error)")
        }
    }

    static func load() -> PersistedAppState? {
        do {
            let data = try Data(contentsOf: fileURL)
            let decoded = try JSONDecoder().decode(PersistedAppState.self, from: data)
            return decoded
        } catch {
            // Если файла нет — это нормальная ситуация при первом запуске
            return nil
        }
    }

    static func clear() {
        let fm = FileManager.default
        try? fm.removeItem(at: fileURL)
    }
}
