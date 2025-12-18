package ru.iandreyshev

fun main() {
//    val summary = YandexAgentClient.getSummary()
//    FirebasePushSender.sendPush(summary)

    // Временная реализация так как есть трудности
    // с отправкой пушей в Firebase
    while (true) {
        val summary = YandexAgentClient.getSummary()
        println("${summary}\n")
        Thread.sleep(7_000L)
    }
}
