plugins {
    kotlin("jvm") version "2.2.21"
}

group = "ru.iandreyshev"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    implementation("com.google.firebase:firebase-admin:9.7.0")
    implementation("org.slf4j:slf4j-simple:2.0.16")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("org.json:json:20240303")
    implementation("com.fasterxml.jackson.core:jackson-databind:2.17.2")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.17.2")
    testImplementation(kotlin("test"))
}

kotlin {
    jvmToolchain(24)
}
