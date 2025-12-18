package ru.iandreyshev

import com.google.auth.oauth2.GoogleCredentials
import com.google.auth.oauth2.ServiceAccountCredentials
import com.google.firebase.FirebaseApp
import com.google.firebase.FirebaseOptions
import com.google.firebase.cloud.FirestoreClient
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.Message
import com.google.firebase.messaging.Notification
import java.io.FileInputStream

object FirebasePushSender {

    fun sendPush(text: String) {
        initFirebase()

        val projectId = FirebaseApp.getInstance().options.projectId
        println("Firebase projectId = $projectId")

        val firestore = FirestoreClient.getFirestore()

        // 1) читаем FCM token (1 пользователь)
        val deviceDoc = firestore.collection("settings").document("device").get().get()
        val fcmToken = deviceDoc.getString("fcmToken")
            ?: error("FCM token not found in settings/device")

        // 2) читаем активные напоминания
        val reminders = firestore.collection("reminders")
            .whereEqualTo("isActive", true)
            .orderBy("dueAt")
            .get()
            .get()
            .documents

        sendPush(
            token = fcmToken,
            title = "Сводка напоминаний",
            body = text
        )
    }

    private fun initFirebase() {
        if (FirebaseApp.getApps().isNotEmpty()) return

        val credPath = System.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            ?: error("GOOGLE_APPLICATION_CREDENTIALS not set")

        val saCreds = FileInputStream(credPath).use { stream ->
            GoogleCredentials.fromStream(stream)
        } as? ServiceAccountCredentials ?: error("Not a service account JSON")

        // ВАЖНО: получить токен прямо сейчас
        saCreds.refresh() // <-- вместо refreshIfExpired()

        val options = FirebaseOptions.builder()
            .setCredentials(saCreds)
            .build()

        if (FirebaseApp.getApps().isEmpty()) {
            FirebaseApp.initializeApp(options)
        }
        FirebaseApp.initializeApp(options)

        println("Firebase projectId = ${FirebaseApp.getInstance().options.projectId}")
        println("Service account = ${saCreds.clientEmail}")
    }

    private fun sendPush(token: String, title: String, body: String) {
        val notification = Notification.builder()
            .setTitle("Уведомление")
            .setBody(body)
            .build()

        val message = Message.builder()
            .setToken(token)
            .setNotification(notification)
            .build()

        FirebaseMessaging.getInstance().send(message)
    }


}