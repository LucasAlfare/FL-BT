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
import io.ktor.client.request.*
import io.ktor.client.statement.*
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import java.io.File

// simple client for testing (with jetpack compose desktop/kotlin/ktor etc)
fun main() = application {
  val httpClient = HttpClient(CIO)
  Window(onCloseRequest = ::exitApplication) {
    App(httpClient)
  }
}

@Composable
fun App(client: HttpClient) {
  var inputText by remember { mutableStateOf("") }
  val inputs = remember { mutableStateListOf<String>() }
  val scope = rememberCoroutineScope()

  Column(modifier = Modifier.padding(16.dp)) {
    Row(verticalAlignment = Alignment.CenterVertically) {
      TextField(
        value = inputText,
        label = { Text("ID de vídeo do YouTube:") },
        onValueChange = { inputText = it },
        modifier = Modifier.weight(1f)
      )
      Spacer(modifier = Modifier.width(8.dp))
      Button(onClick = {
        if (inputText.isNotBlank()) {
          inputs.add(inputText.trim())
          inputText = ""
        }
      }) {
        Text("Adicionar")
      }
    }

    Spacer(modifier = Modifier.height(12.dp))

    Button(
      onClick = {
        scope.launch {
          processYouTubeIds(inputs.toList(), client)
          inputs.clear()
        }
      },
      enabled = inputs.isNotEmpty()
    ) {
      Text("Converter")
    }

    Spacer(modifier = Modifier.height(12.dp))

    if (inputs.isNotEmpty()) {
      LazyColumn {
        item { Text("IDs adicionados:") }
        items(inputs) { id -> Text(id) }
      }
    }
  }
}

suspend fun processYouTubeIds(ids: List<String>, client: HttpClient) = coroutineScope {
  val downloadsDir = File("downloads")
  downloadsDir.mkdirs()

  ids.map { id ->
    launch {
      try {
        val response: HttpResponse =
          client.post("http://localhost:8000/api/video/id/$id")
        if (response.status.value in 200..299) {
          val bytes = response.body<ByteArray>()
          File(downloadsDir, "$id.zip").writeBytes(bytes)
          println("Download de $id salvo com sucesso.")
        } else {
          println("Erro $id: HTTP ${response.status.value}")
        }
      } catch (e: Exception) {
        println("Falha ao processar $id: ${e.message}")
      }
    }
  }.joinAll()
}

/*
Como viu, meu projeto python usa Spleeter, que por sua vez usa os binários FFMPEG. Eu tenho esses binários no meu windows adicionados no meu PATH.

Sabendo dessa organização, é possível eu criar um app desktop pra eu rodar diretamente com 1 clique e usar? Não quero/posso hospedar a API python externamente. Quero criar algo distribuível para que eu possa usar mesmo num computador que acabou de ser formatado. Me diga exatamente o que devo fazer para ter isso. Pensei em deixar os binários na pasta do projeto, mas não sei se é uma boa opção. Também não sei o que fazer em relação à merda do python. Aceito sugestões com docker se for melhor, se não for, me diga a melhor opção do mundo.
 */