//
//  Reminder.swift
//  MobileReminderClient
//
//  Created by Ivan Andreyshev on 17.12.2025.
//

import FirebaseFirestore
import Foundation
import SwiftUI

enum Importance: String, CaseIterable, Identifiable {
    case normal
    case medium
    case high

    var id: String { rawValue }

    var title: String {
        switch self {
        case .normal: return "Обычно 🟢"
        case .medium: return "Средне 🟡"
        case .high: return "Важно 🔴"
        }
    }
}

struct Reminder: Identifiable, Equatable {
    let id: String
    var text: String
    var dueAt: Date
    var importance: Importance
    var isActive: Bool
    var createdAt: Date?

    var isOverdue: Bool { dueAt < Date() }

    init(
        id: String,
        text: String,
        dueAt: Date,
        importance: Importance,
        isActive: Bool,
        createdAt: Date?
    ) {
        self.id = id
        self.text = text
        self.dueAt = dueAt
        self.importance = importance
        self.isActive = isActive
        self.createdAt = createdAt
    }

    init?(doc: DocumentSnapshot) {
        let data = doc.data() ?? [:]

        guard
            let text = data["text"] as? String,
            let dueAtTS = data["dueAt"] as? Timestamp,
            let importanceRaw = data["importance"] as? String,
            let importance = Importance(rawValue: importanceRaw),
            let isActive = data["isActive"] as? Bool
        else { return nil }

        let createdAtTS = data["createdAt"] as? Timestamp

        id = doc.documentID
        self.text = text
        dueAt = dueAtTS.dateValue()
        self.importance = importance
        self.isActive = isActive
        createdAt = createdAtTS?.dateValue()
    }
}
