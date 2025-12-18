//
//  AddReminderView.swift
//  MobileReminderClient
//
//  Created by Ivan Andreyshev on 17.12.2025.
//

import SwiftUI

struct AddReminderView: View {
    @State private var text: String = ""
    @State private var dueAt: Date = Date().addingTimeInterval(3600) // +1 час
    @State private var importance: Importance = .normal

    let onCreate: (_ text: String, _ dueAt: Date, _ importance: Importance) -> Void
    let onCancel: () -> Void

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Текст")) {
                    TextField("Например: созвон в 18:00", text: $text)
                        .lineLimit(4)
                }

                Section(header: Text("Дедлайн")) {
                    DatePicker("Дата и время", selection: $dueAt, displayedComponents: [.date, .hourAndMinute])
                }

                Section(header: Text("Важность")) {
                    Picker("Важность", selection: $importance) {
                        ForEach(Importance.allCases) { item in
                            Text(item.title)
                                .tag(item)
                                .background(Color.red)
                        }
                    }
                    .pickerStyle(.segmented)
                }
            }
            .navigationTitle("Новое")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Отмена") { onCancel() }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Создать") {
                        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
                        guard !trimmed.isEmpty else { return }
                        onCreate(trimmed, dueAt, importance)
                    }
                    .disabled(text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                }
            }
        }
    }
}
