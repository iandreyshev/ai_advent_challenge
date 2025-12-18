//
//  AppDelegate.swift
//  MobileReminderClient
//
//  Created by Ivan Andreyshev on 17.12.2025.
//

import FirebaseCore
import FirebaseFirestore
import FirebaseMessaging
import UIKit
import UserNotifications

final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions _: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        FirebaseApp.configure()

        UNUserNotificationCenter.current().delegate = self
        Messaging.messaging().delegate = self

        requestNotificationPermission(application)
        return true
    }

    private func requestNotificationPermission(_ application: UIApplication) {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .badge, .sound]) { granted, error in
            if let error = error {
                print("Notification permission error:", error)
                return
            }
            print("Notification permission granted:", granted)

            // Регистрация в APNs должна быть на главном потоке
            DispatchQueue.main.async {
                application.registerForRemoteNotifications()
            }
        }
    }

    // APNs token -> Firebase Messaging
    func application(_: UIApplication,
                     didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data)
    {
        Messaging.messaging().apnsToken = deviceToken
    }

    func application(_: UIApplication,
                     didFailToRegisterForRemoteNotificationsWithError error: Error)
    {
        print("APNs registration failed:", error)
    }
}

extension AppDelegate: UNUserNotificationCenterDelegate {
    // Чтобы уведомление показывалось, когда приложение открыто
    func userNotificationCenter(_: UNUserNotificationCenter,
                                willPresent _: UNNotification,
                                withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void)
    {
        completionHandler([.banner, .sound])
    }
}

extension AppDelegate: MessagingDelegate {
    // FCM registration token
    func messaging(_: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let fcmToken else { return }
        print("FCM token:", fcmToken)

        // Раз у нас 1 пользователь — сохраняем в Firestore в фиксированное место
        // settings/device
        let db = Firestore.firestore()
        db.collection("settings").document("device").setData([
            "fcmToken": fcmToken,
            "updatedAt": FieldValue.serverTimestamp(),
        ], merge: true)
    }
}
