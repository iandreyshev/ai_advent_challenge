package ru.iandreyshev

fun main(args: Array<String>) {
    println("=== Code Review Tool ===")

    // Чтение конфигурации из переменных окружения
    val apiKey = System.getenv("YANDEX_API_KEY")
        ?: error("YANDEX_API_KEY environment variable is not set")

    val folderId = System.getenv("YANDEX_FOLDER_ID")
        ?: error("YANDEX_FOLDER_ID environment variable is not set")

    val agentId = System.getenv("YANDEX_AGENT_ID")
        ?: error("YANDEX_AGENT_ID environment variable is not set")

    val repoPath = System.getenv("REPOSITORY_PATH")
        ?: error("REPOSITORY_PATH environment variable is not set")

    // Парсинг аргументов
    if (args.size != 2) {
        println("Usage: ./gradlew run --args=\"<source-branch> <target-branch>\"")
        println("Example: ./gradlew run --args=\"feature/new-feature main\"")
        return
    }

    val sourceBranch = args[0]
    val targetBranch = args[1]

    println("Source branch: $sourceBranch")
    println("Target branch: $targetBranch")
    println("Repository: $repoPath")
    println()

    try {
        // Получаем изменения из Git
        println("Fetching changes from Git...")
        val gitRepo = GitRepository(repoPath)
        val diff = gitRepo.getDiff(sourceBranch, targetBranch)
        val changedFiles = gitRepo.getChangedFiles(sourceBranch, targetBranch)

        if (diff.isBlank()) {
            println("No changes found between $sourceBranch and $targetBranch")
            return
        }

        println("Changed files (${changedFiles.size}):")
        changedFiles.forEach { println("  - $it") }
        println()

        // Отправляем на review в Yandex Agent
        println("Sending to Yandex AI for review...")
        val agent = YandexAgentClient(folderId, apiKey, agentId)

        val review = agent.reviewCode(diff, changedFiles)
        agent.close()

        println()
        println("=== Code Review Result ===")
        println(review)

    } catch (e: Exception) {
        println("Error: ${e.message}")
        e.printStackTrace()
    }
}
