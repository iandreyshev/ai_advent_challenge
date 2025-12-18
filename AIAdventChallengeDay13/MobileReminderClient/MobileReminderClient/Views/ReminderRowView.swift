//
//  ReminderRowView.swift
//  MobileReminderClient
//
//  Created by Ivan Andreyshev on 17.12.2025.
//

import SwiftUI

struct ReminderRowView: View {
    let reminder: Reminder
    let onDeactivate: () -> Void

    private var importanceBadge: String {
        switch reminder.importance {
        case .high: return "🔴"
        case .medium: return "🟡"
        case .normal: return "🟢"
        }
    }

    private var mskFormatter: DateFormatter {
        let df = DateFormatter()
        df.locale = Locale(identifier: "ru_RU")
        df.timeZone = TimeZone(identifier: "Europe/Moscow")
        df.dateStyle = .medium
        df.timeStyle = .short
        return df
    }

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text(importanceBadge)
                .font(.title3)
                .frame(width: 24, alignment: .leading)

            VStack(alignment: .leading, spacing: 6) {
                Text(reminder.text)
                    .font(.body)
                    .lineLimit(3)

                Text(mskFormatter.string(from: reminder.dueAt) + (reminder.isOverdue ? " • ПРОСРОЧЕНО" : ""))
                    .font(.caption)
                    .foregroundColor(reminder.isOverdue ? .red : .secondary)
            }

            Spacer()

            Button {
                onDeactivate()
            } label: {
                Image(systemName: "checkmark.circle")
            }
            .buttonStyle(.borderless)
            .accessibilityLabel("Деактивировать")
        }
        .padding(.vertical, 4)
    }
}
