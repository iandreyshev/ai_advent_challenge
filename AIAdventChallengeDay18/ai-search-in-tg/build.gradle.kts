plugins {
    kotlin("jvm") version "2.2.21"
}

group = "ru.iandreyshev"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.fasterxml.jackson.core:jackson-databind:2.17.2")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.17.2")
    implementation("org.json:json:20240303")
}

kotlin {
    jvmToolchain(24)
}
