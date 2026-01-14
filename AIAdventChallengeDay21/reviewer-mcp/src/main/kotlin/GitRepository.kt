package ru.iandreyshev

import java.io.File

class GitRepository(private val repositoryPath: String) {

    fun getDiff(sourceBranch: String, targetBranch: String): String {
        val command = listOf("git", "diff", "$targetBranch...$sourceBranch")
        return executeCommand(command)
    }

    fun getChangedFiles(sourceBranch: String, targetBranch: String): List<String> {
        val command = listOf("git", "diff", "--name-only", "$targetBranch...$sourceBranch")
        val output = executeCommand(command)
        return output.lines().filter { it.isNotBlank() }
    }

    fun getFileContent(filePath: String, branch: String): String {
        val command = listOf("git", "show", "$branch:$filePath")
        return executeCommand(command)
    }

    private fun executeCommand(command: List<String>): String {
        val processBuilder = ProcessBuilder(command)
            .directory(File(repositoryPath))
            .redirectErrorStream(true)

        val process = processBuilder.start()
        val output = process.inputStream.bufferedReader().readText()
        val exitCode = process.waitFor()

        if (exitCode != 0) {
            throw RuntimeException("Git command failed: ${command.joinToString(" ")}\n$output")
        }

        return output
    }
}
