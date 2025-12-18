//
//  ContentView.swift
//  MobileReminderClient
//
//  Created by Ivan Andreyshev on 17.12.2025.
//

import SwiftUI
import Combine

struct ContentView: View {
    @StateObject private var store = FirestoreReminderStore()
    @State private var showingAdd = false

    var body: some View {
        NavigationStack {
            Group {
                if let err = store.lastError {
                    VStack(spacing: 12) {
                        Text("Ошибка")
                            .font(.headline)
                        Text(err)
                            .font(.subheadline)
                            .multilineTextAlignment(.center)
                            .foregroundColor(.secondary)
                        Button("Попробовать снова") {
                            store.startListeningActive()
                        }
                    }
                    .padding()
                } else if store.activeReminders.isEmpty {
                    VStack(spacing: 12) {
                        Text("Активных напоминаний нет")
                            .font(.headline)

                        Button {
                            showingAdd = true
                        } label: {
                            Text("Создать напоминание")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderless)
                        .padding(.top, 6)
                        .padding(.horizontal, 24)
                    }
                    .padding()
                } else {
                    List {
                        ForEach(store.activeReminders) { reminder in
                            ReminderRowView(reminder: reminder) {
                                Task { await store.deactivateReminder(id: reminder.id) }
                            }
                        }
                    }
                    .listStyle(.insetGrouped)
                }
            }
            .navigationTitle("Напоминания")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showingAdd = true
                    } label: {
                        Image(systemName: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAdd) {
                AddReminderView { text, dueAt, importance in
                    Task {
                        await store.createReminder(text: text, dueAt: dueAt, importance: importance)
                        showingAdd = false
                    }
                } onCancel: {
                    showingAdd = false
                }
            }
        }
        .onAppear { store.startListeningActive() }
        .onDisappear { store.stopListening() }
    }
}
