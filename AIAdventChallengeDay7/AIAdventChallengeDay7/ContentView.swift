//
//  ContentView.swift
//  AIAdventChallengeDay7
//
//  Created by Ivan Andreyshev on 09.12.2025.
//

import Combine
import SwiftUI

struct ContentView: View {
    @StateObject private var vm = MultiModelViewModel()
    @FocusState private var isPromptFocused: Bool

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(spacing: 16) {
                        Text("День 7 — Модели")
                            .font(.title3.bold())
                            .frame(maxWidth: .infinity, alignment: .leading)

                        // Ввод промпта
                        ZStack(alignment: .topLeading) {
                            TextEditor(text: $vm.prompt)
                                .frame(minHeight: 140)
                                .padding(8)
                                .background(
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(Color(.secondarySystemBackground))
                                )
                                .focused($isPromptFocused)

                            if vm.prompt.isEmpty {
                                Text("Введите запрос, который отправим в OpenAI и Яндекс…")
                                    .foregroundColor(.secondary)
                                    .padding(.horizontal, 14)
                                    .padding(.vertical, 12)
                            }
                        }

                        // Выбор моделей
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Модели")
                                .font(.headline)

                            HStack(spacing: 8) {
                                ForEach(ModelProvider.allCases) { provider in
                                    ModelChip(
                                        title: provider.displayName,
                                        isSelected: vm.selectedProviders.contains(provider),
                                        color: provider == .openAI ? .blue : .orange
                                    ) {
                                        vm.toggle(provider)
                                    }
                                }
                            }
                        }

                        // Кнопка отправки
                        Button {
                            Task {
                                isPromptFocused = false
                                await vm.send()
                                withAnimation {
                                    proxy.scrollTo("resultsSection", anchor: .top)
                                }
                            }
                        } label: {
                            HStack {
                                if vm.isLoading {
                                    ProgressView().tint(.white)
                                }
                                Text(vm.isLoading ? "Запрашиваем…" : "Отправить")
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(vm.canSend ? Color.accentColor : Color.gray)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                        }
                        .disabled(!vm.canSend)

                        if let error = vm.errorMessage {
                            Text(error)
                                .font(.footnote)
                                .foregroundColor(.red)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }

                        if !vm.results.isEmpty {
                            Divider()
                            Text("Ответы")
                                .font(.headline)
                                .frame(maxWidth: .infinity, alignment: .leading)

                            VStack(spacing: 12) {
                                ForEach(vm.results) { result in
                                    ResultCard(
                                        result: result,
                                        onRatingChange: { newRating in
                                            vm.setRating(newRating, for: result.id)
                                        }
                                    )
                                }
                            }
                            .id("resultsSection")
                        }
                    }
                    .padding()
                }
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItemGroup(placement: .keyboard) {
                        Spacer()
                        Button("Отправить") {
                            Task {
                                isPromptFocused = false
                                await vm.send()
                                withAnimation {
                                    proxy.scrollTo("resultsSection", anchor: .top)
                                }
                            }
                        }
                        .disabled(!vm.canSend)
                    }
                }
            }
        }
    }
}

// MARK: - Вспомогательные вью

struct ModelChip: View {
    let title: String
    let isSelected: Bool
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Circle()
                    .fill(color)
                    .frame(width: 8, height: 8)
                Text(title)
                    .font(.subheadline)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(
                Capsule()
                    .fill(isSelected ? color.opacity(0.15) : Color(.secondarySystemBackground))
            )
            .overlay(
                Capsule()
                    .stroke(isSelected ? color : Color.clear, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

struct ResultCard: View {
    let result: ModelResult
    let onRatingChange: (Int) -> Void

    var accentColor: Color {
        switch result.provider {
        case .openAI: return .blue
        case .yandex: return .orange
        }
    }

    private var formattedDuration: String {
        if result.responseTime < 1 {
            return String(format: "%.0f мс", result.responseTime * 1000)
        } else {
            return String(format: "%.2f с", result.responseTime)
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(result.provider.displayName)
                    .font(.subheadline.weight(.semibold))
                Spacer()
                Text(formattedDuration)
                    .font(.footnote.monospacedDigit())
                    .foregroundColor(.secondary)
            }

            HStack {
                Text("\(result.totalTokens) токенов")
                    .font(.footnote.monospacedDigit())
                    .foregroundColor(.secondary)
                Spacer()
            }

            Text(result.text)
                .font(.body)

            HStack(spacing: 12) {
                label("prompt", result.promptTokens)
                label("completion", result.completionTokens)
            }

            // ОЦЕНКА 1–5
            HStack(spacing: 6) {
                Text("Оценка:")
                    .font(.caption)
                    .foregroundColor(.secondary)

                ForEach(1...5, id: \.self) { value in
                    Image(systemName: value <= (result.rating ?? 0) ? "star.fill" : "star")
                        .font(.system(size: 24))       // ⭐️⭐️⭐️⭐️⭐️ большие звезды
                        .foregroundColor(.yellow)
                        .onTapGesture {
                            onRatingChange(value)
                        }
                }
            }
            .padding(.top, 4)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 14)
                .fill(Color(.secondarySystemBackground))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 14)
                .stroke(accentColor.opacity(0.3), lineWidth: 1)
        )
    }

    private func label(_ title: String, _ value: Int) -> some View {
        HStack(spacing: 4) {
            Text(title)
            Text("\(value)")
                .monospacedDigit()
        }
        .font(.caption)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(
            Capsule().fill(Color.black.opacity(0.04))
        )
    }
}
