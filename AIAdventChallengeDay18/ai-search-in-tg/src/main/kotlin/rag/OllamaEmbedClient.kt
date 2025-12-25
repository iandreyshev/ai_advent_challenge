package ru.iandreyshev.rag

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.registerKotlinModule
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

class OllamaEmbedClient(
    private val embedUrl: String,
    private val model: String
) {
    private val http = OkHttpClient()
    private val mapper = ObjectMapper().registerKotlinModule()
    private val json = "application/json".toMediaType()

    fun embed(text: String): FloatArray {
        val payload = mapOf(
            "model" to model,
            "prompt" to text
        )
        val body = mapper.writeValueAsString(payload)
            .toRequestBody(json)
        val req = Request.Builder()
            .url(embedUrl)
            .post(body)
            .build()

        http.newCall(req)
            .execute()
            .use { resp ->
                if (!resp.isSuccessful) {
                    error("Ollama embeddings failed: HTTP ${resp.code} ${resp.body?.string()}")
                }

                val node = mapper.readTree(resp.body!!.string())
                val arr = node["embedding"] ?: error("No 'embedding' in Ollama response")
                val out = FloatArray(arr.size())
                for (i in 0 until arr.size()) out[i] = arr[i].asDouble().toFloat()
                return out
            }
    }
}
