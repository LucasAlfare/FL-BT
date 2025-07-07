package com.lucasalfare.flbt.client.desktop

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.Button
import androidx.compose.material.Text
import androidx.compose.material.TextField
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.serialization.Serializable
import java.io.File

@Composable
fun App(client: HttpClient) {
  var inputText by remember { mutableStateOf("") }
  val inputs = remember { mutableStateListOf<String>() }
  val scope = rememberCoroutineScope()

  // Map taskId -> Pair(videoId, status)
  val tasksStatus = remember { mutableStateMapOf<String, Pair<String, String>>() }
  val downloadsDir = File("downloads").apply { mkdirs() }

  Column(modifier = Modifier.padding(16.dp)) {
    Row(verticalAlignment = Alignment.CenterVertically) {
      TextField(
        value = inputText,
        label = { Text("ID de vídeo do YouTube:") },
        onValueChange = { inputText = it },
        modifier = Modifier.weight(1f)
      )
      Spacer(Modifier.width(8.dp))
      Button(onClick = {
        if (inputText.isNotBlank()) {
          inputs.add(inputText.trim())
          inputText = ""
        }
      }) {
        Text("Adicionar")
      }
    }

    Spacer(Modifier.height(12.dp))

    Button(
      onClick = {
        scope.launch {
          tasksStatus.clear()
          inputs.forEach { videoId ->
            launch {
              try {
                // Submit job
                val response: SubmitResponse = client.post("http://localhost:8000/api/video/id/$videoId").body()
                val taskId = response.task_id
                tasksStatus[taskId] = videoId to "PENDING"
                pollTask(taskId, videoId, client, tasksStatus, downloadsDir)
              } catch (e: Exception) {
                tasksStatus["error_$videoId"] = videoId to "Erro ao submeter: ${e.message}"
              }
            }
          }
          inputs.clear()
        }
      },
      enabled = inputs.isNotEmpty()
    ) {
      Text("Converter")
    }

    Spacer(Modifier.height(12.dp))

    if (tasksStatus.isNotEmpty()) {
      LazyColumn {
        item { Text("Status das tarefas:") }
        items(tasksStatus.toList()) { (taskId, pair) ->
          val (videoId, status) = pair
          Text("$videoId : $status")
        }
      }
    }
  }
}

suspend fun pollTask(
  taskId: String,
  videoId: String,
  client: HttpClient,
  tasksStatus: MutableMap<String, Pair<String, String>>,
  downloadsDir: File
) {
  while (true) {
    delay(3000) // 3 segundos
    try {
      val statusResponse: TaskStatusResponse = client.get("http://localhost:8000/api/task/status/$taskId").body()
      val status = statusResponse.status
      tasksStatus[taskId] = videoId to status
      when (status) {
        "SUCCESS" -> {
          // Baixar arquivo
          val httpResponse: HttpResponse = client.get("http://localhost:8000/api/task/result/$taskId") {
            timeout { requestTimeoutMillis = 60_000 }
          }
          if (httpResponse.status == HttpStatusCode.OK) {
            val bytes = httpResponse.body<ByteArray>()
            File(downloadsDir, "$videoId.zip").writeBytes(bytes)
            tasksStatus[taskId] = videoId to "Concluído e baixado"
          } else {
            tasksStatus[taskId] = videoId to "Erro no download: HTTP ${httpResponse.status.value}"
          }
          break
        }

        "FAILURE", "REVOKED" -> {
          tasksStatus[taskId] = videoId to "Falha na tarefa"
          break
        }
        // continua aguardando
      }
    } catch (e: Exception) {
      tasksStatus[taskId] = videoId to "Erro ao consultar status: ${e.message}"
      break
    }
  }
}

@Serializable
data class SubmitResponse(val task_id: String)

@Serializable
data class TaskStatusResponse(val task_id: String, val status: String, val result: String?, val error: String?)

fun main() = application {
  val httpClient = HttpClient(CIO) {
    expectSuccess = false

    install(ContentNegotiation) {
      json()
    }

    install(HttpTimeout) {
      requestTimeoutMillis = 120_000L
    }
  }
  Window(onCloseRequest = ::exitApplication) {
    App(httpClient)
  }
}

/*
celery -A celery_app.celery_app worker --loglevel=info

uvicorn main:app --reload
 */

/*
Como viu, meu projeto python usa Spleeter, que por sua vez usa os binários FFMPEG. Eu tenho esses binários no meu windows adicionados no meu PATH.

Sabendo dessa organização, é possível eu criar um app desktop pra eu rodar diretamente com 1 clique e usar? Não quero/posso hospedar a API python externamente. Quero criar algo distribuível para que eu possa usar mesmo num computador que acabou de ser formatado. Me diga exatamente o que devo fazer para ter isso. Pensei em deixar os binários na pasta do projeto, mas não sei se é uma boa opção. Também não sei o que fazer em relação à merda do python. Aceito sugestões com docker se for melhor, se não for, me diga a melhor opção do mundo.
 */