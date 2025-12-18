//
//  FirestoreReminderStore.swift
//  MobileReminderClient
//
//  Created by Ivan Andreyshev on 17.12.2025.
//

import Foundation
import FirebaseFirestore
import Combine

@MainActor
final class FirestoreReminderStore: ObservableObject {
    @Published private(set) var activeReminders: [Reminder] = []
    @Published private(set) var lastError: String?

    private let db = Firestore.firestore()
    private var listener: ListenerRegistration?

    private let collectionName = "reminders"

    func startListeningActive() {
        stopListening()

        listener = db.collection(collectionName)
            .whereField("isActive", isEqualTo: true)
            .order(by: "dueAt", descending: false)
            .addSnapshotListener { [weak self] snapshot, error in
                guard let self else { return }

                if let error {
                    self.lastError = error.localizedDescription
                    self.activeReminders = []
                    return
                }

                let docs = snapshot?.documents ?? []
                self.activeReminders = docs.compactMap { Reminder(doc: $0) }
                self.lastError = nil
            }
    }

    func stopListening() {
        listener?.remove()
        listener = nil
    }

    func createReminder(text: String, dueAt: Date, importance: Importance) async {
        let payload: [String: Any] = [
            "text": text,
            "dueAt": Timestamp(date: dueAt),
            "importance": importance.rawValue,
            "isActive": true,
            "createdAt": FieldValue.serverTimestamp()
        ]

        do {
            _ = try await db.collection(collectionName).addDocument(data: payload)
            lastError = nil
        } catch {
            lastError = error.localizedDescription
        }
    }

    func deactivateReminder(id: String) async {
        do {
            try await db.collection(collectionName)
                .document(id)
                .updateData(["isActive": false])
            lastError = nil
        } catch {
            lastError = error.localizedDescription
        }
    }
}
