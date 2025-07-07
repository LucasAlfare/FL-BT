package com.lucasalfare.flbt.client.desktop

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.Button
import androidx.compose.material.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.cio.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.File

// Client.kt
val client = HttpClient(CIO) {
  install(ContentNegotiation) {
    json(Json {
      isLenient = true
    })
  }
}
const val server = "http://localhost:8000"

@Serializable
data class Task(
  @SerialName("video_id") val id: String,
  var status: String = "PENDING",
  var error: String? = null
)


@Composable
fun App() {
  var input by remember { mutableStateOf("") }
  val tasks = remember { mutableStateOf(listOf<Task>()) }

  Column(modifier = Modifier.padding(16.dp)) {
    BasicTextField(
      value = input,
      onValueChange = { input = it },
      modifier = Modifier.fillMaxWidth().height(100.dp)
    )
    Spacer(modifier = Modifier.height(8.dp))
    Button(onClick = {
      val ids = input.split("\n").map { it.trim() }.filter { it.isNotEmpty() }
      tasks.value = ids.map { Task(it) }
      ids.forEach { id ->
        CoroutineScope(Dispatchers.IO).launch {
          try {
            client.post("$server/api/request/$id")
          } catch (_: Exception) {
          }
        }
      }
    }) { Text("Enviar IDs") }

    Spacer(modifier = Modifier.height(16.dp))
    tasks.value.forEach { task ->
      Text("${task.id} → ${task.status}" + (task.error?.let { " [Erro: $it]" } ?: ""))
    }

    LaunchedEffect(tasks) {
      while (true) {
        tasks.value = tasks.value.map { task ->
          if (task.status in listOf("SUCCESS", "FAILURE", "EXPIRED")) return@map task
          val resp = client.get("$server/api/status/${task.id}").body<Task>()
          val status = resp.status
          if (status == "SUCCESS") {
            val bytes = client.get("$server/api/download/${task.id}").body<ByteArray>()
            File("downloads/${task.id}.zip").writeBytes(bytes)
          }
          task.copy(status = status)
        }
        delay(2000)
      }
    }
  }
}

fun main() = application {
  Window(onCloseRequest = ::exitApplication, title = "Video Processor") {
    App()
  }
}