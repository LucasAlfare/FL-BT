import org.jetbrains.compose.desktop.application.dsl.TargetFormat

plugins {
  alias(libs.plugins.kotlinJvm)
  alias(libs.plugins.kotlinxSerialization)
  alias(libs.plugins.compose)
  alias(libs.plugins.composeCompiler)
}

repositories {
  // Use Maven Central for resolving dependencies.
  mavenCentral()
  maven { url = uri("https://plugins.gradle.org/m2/") }
  google()
  maven { url = uri("https://jitpack.io") }
}

dependencies {
  implementation(compose.desktop.currentOs)
  implementation(libs.flBase)
}

// Apply a specific Java toolchain to ease working on different environments.
java {
  toolchain {
    languageVersion = JavaLanguageVersion.of(21)
  }
}

compose.desktop {
  application {
    mainClass = "com.lucasalfare.flbt.client.desktop.MainKt"

    nativeDistributions {
      targetFormats(TargetFormat.Dmg, TargetFormat.Msi, TargetFormat.Deb)
      packageName = "FLBTClient"
      packageVersion = "1.0.0"

      buildTypes.release.proguard {
        isEnabled = false
      }
    }
  }
}

tasks.named<Test>("test") {
  // Use JUnit Platform for unit tests.
  useJUnitPlatform()
}
