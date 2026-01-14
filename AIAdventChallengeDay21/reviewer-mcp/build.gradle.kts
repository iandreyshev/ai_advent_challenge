val kotlin_version: String by project
val logback_version: String by project

plugins {
    kotlin("jvm") version "2.2.21"
    application
}

group = "ru.iandreyshev"
version = "0.0.1"

application {
    mainClass.set("ru.iandreyshev.ApplicationKt")
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.fasterxml.jackson.core:jackson-databind:2.15.3")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.15.3")
    implementation("org.json:json:20231013")
    implementation("ch.qos.logback:logback-classic:$logback_version")
}
