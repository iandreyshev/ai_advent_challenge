//
//  ContentView.swift
//  AIAdventChallengeDay6
//
//  Created by Ivan Andreyshev on 08.12.2025.
//

import MessageUI
import SwiftUI

import SwiftUI
import MessageUI
import UIKit
import Combine

// MARK: - Модели

struct TemperatureConfig: Identifiable, Hashable {
    let id = UUID()
    var value: Double
}

struct ChatResultItem: Identifiable {
    let id = UUID()
    let temperature: Double
    let text: String
}

// MARK: - OpenAI сервис

struct ChatCompletionRequest: Encodable {
    struct Message: Encodable {
        let role: String
        let content: String
    }

    let model: String
    let messages: [Message]
    let temperature: Double
}

struct ChatCompletionResponse: Decodable {
    struct Choice: Decodable {
        struct Message: Decodable {
            let role: String
            let content: String
        }

        let index: Int
        let message: Message
    }

    let choices: [Choice]
}

enum OpenAIError: Error, LocalizedError {
    case emptyResponse
    case badStatus(code: Int)

    var errorDescription: String? {
        switch self {
        case .emptyResponse: return "Пустой ответ от модели."
        case let .badStatus(code): return "Сервер вернул код \(code)."
        }
    }
}

final class OpenAIService {
    func sendChat(prompt: String, temperature: Double) async throws -> String {
        guard let url = URL(string: "https://api.openai.com/v1/chat/completions") else {
            throw URLError(.badURL)
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(openAIAPIKey)", forHTTPHeaderField: "Authorization")

        let body = ChatCompletionRequest(
            model: openAIModel,
            messages: [
                .init(role: "user", content: prompt),
            ],
            temperature: temperature
        )

        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)

        if let http = response as? HTTPURLResponse, !(200 ... 299).contains(http.statusCode) {
            throw OpenAIError.badStatus(code: http.statusCode)
        }

        let decoded = try JSONDecoder().decode(ChatCompletionResponse.self, from: data)
        guard let choice = decoded.choices.first else {
            throw OpenAIError.emptyResponse
        }
        return choice.message.content
    }
}

// MARK: - ViewModel

@MainActor
final class ChatViewModel: ObservableObject {
    @Published var prompt: String = ""
    @Published var temperatures: [TemperatureConfig] = [
        .init(value: 0.0),
        .init(value: 0.5),
        .init(value: 1.0),
    ]

    @Published var results: [ChatResultItem] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let service = OpenAIService()

    func runRequests() async {
        guard !prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            errorMessage = "Введите запрос."
            return
        }

        let temps = temperatures.map { $0.value }.sorted()

        results = []
        errorMessage = nil
        isLoading = true
        defer { isLoading = false }

        for temp in temps {
            do {
                let text = try await service.sendChat(prompt: prompt, temperature: temp)
                let item = ChatResultItem(temperature: temp, text: text)
                results.append(item)
            } catch {
                errorMessage = error.localizedDescription
                break
            }
        }
    }

    func addTemperature() {
        temperatures.append(.init(value: 1.0))
    }

    func remove(_ config: TemperatureConfig) {
        if let idx = temperatures.firstIndex(of: config) {
            temperatures.remove(at: idx)
        }
    }
}

// MARK: - Кастомный вертикальный слайдер (в стиле Control Center)

struct VerticalTemperatureSlider: View {
    @Binding var value: Double
    let range: ClosedRange<Double>

    private var normalized: Double {
        guard range.upperBound > range.lowerBound else { return 0 }
        return (value - range.lowerBound) / (range.upperBound - range.lowerBound)
    }

    // Цвет в зависимости от температуры: от синего к оранжевому
    private var fillColor: Color {
        let t = max(0, min(1, normalized))      // 0...1
        let hueCold = 0.60                      // синий
        let hueHot  = 0.08                      // оранжевый
        let hue = hueCold + (hueHot - hueCold) * t
        return Color(hue: hue, saturation: 0.9, brightness: 0.95)
    }

    // Эмодзи по смыслу LLM-температуры
    private var temperatureEmoji: String {
        switch value {
        case ..<0.2:
            return "🎯"   // максимально точные, детерминированные ответы
        case ..<0.7:
            return "📚"   // аккуратный, больше про факты
        case ..<1.3:
            return "💡"   // креатив, идеи, варианты
        default:
            return "🎲"   // хаос, много вариативности
        }
    }

    var body: some View {
        VStack(spacing: 6) {
            // ЭМОДЗИ СВЕРХУ КОНТРОЛА
            Text(temperatureEmoji)
                .font(.title2)

            GeometryReader { geo in
                ZStack(alignment: .bottom) {
                    Capsule()
                        .fill(.thinMaterial)

                    Capsule()
                        .fill(fillColor)
                        .frame(height: geo.size.height * normalized)

                    VStack {
                        Spacer(minLength: 8)
                        // можно убрать иконку пламени, но я оставлю маленькой
                        Image(systemName: "flame.fill")
                            .font(.caption2)
                            .foregroundStyle(.white)
                            .padding(.bottom, 4)
                    }
                    .frame(maxHeight: .infinity, alignment: .top)
                }
                .clipShape(RoundedRectangle(cornerRadius: geo.size.width / 2))
                .overlay(
                    Text(String(format: "%.1f", value))
                        .font(.caption2.monospacedDigit())
                        .padding(4)
                        .background(.ultraThinMaterial, in: Capsule())
                        .padding(4),
                    alignment: .bottom
                )
                .gesture(
                    DragGesture(minimumDistance: 0)
                        .onChanged { gesture in
                            let h = geo.size.height
                            let y = max(0, min(h, h - gesture.location.y))
                            let progress = y / h

                            let raw = range.lowerBound + Double(progress) * (range.upperBound - range.lowerBound)
                            let clamped = min(max(raw, range.lowerBound), range.upperBound)

                            // шаг 0.1
                            let step = 0.1
                            let stepped = (clamped / step).rounded() * step

                            self.value = stepped
                        }
                )
            }
        }
        .frame(width: 52, height: 230) // чуть выше, чтобы влезло эмодзи
    }
}


struct MailView: UIViewControllerRepresentable {
    @Environment(\.dismiss) private var dismiss

    let subject: String
    let body: String

    class Coordinator: NSObject, MFMailComposeViewControllerDelegate {
        let parent: MailView

        init(parent: MailView) {
            self.parent = parent
        }

        func mailComposeController(_ controller: MFMailComposeViewController,
                                   didFinishWith _: MFMailComposeResult,
                                   error _: Error?)
        {
            controller.dismiss(animated: true) {
                self.parent.dismiss()
            }
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    func makeUIViewController(context: Context) -> MFMailComposeViewController {
        let vc = MFMailComposeViewController()
        vc.setSubject(subject)
        vc.setMessageBody(body, isHTML: false)
        vc.mailComposeDelegate = context.coordinator
        return vc
    }

    func updateUIViewController(_: MFMailComposeViewController,
                                context _: Context) {}
}

// MARK: - Основной экран

struct ContentView: View {
    @StateObject private var vm = ChatViewModel()
    @FocusState private var isPromptFocused: Bool

    @State private var isShowingMail = false
    @State private var mailBody = ""
    @State private var showMailError = false

    let temperatureRange: ClosedRange<Double> = 0.0...2.0

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(spacing: 16) {

                        Text("День 6 — Температуры")
                            .font(.title3.bold())
                            .multilineTextAlignment(.leading)
                            .frame(maxWidth: .infinity, alignment: .leading)

                        // -------- TextEditor + плейсхолдер
                        ZStack(alignment: .topLeading) {
                            TextEditor(text: $vm.prompt)
                                .frame(minHeight: 120)
                                .padding(8)
                                .background(
                                    RoundedRectangle(cornerRadius: 12)
                                        .fill(Color(.secondarySystemBackground))
                                )
                                .focused($isPromptFocused)

                            if vm.prompt.isEmpty {
                                Text("Введите запрос к ChatGPT…")
                                    .foregroundColor(.secondary)
                                    .padding(.horizontal, 14)
                                    .padding(.vertical, 12)
                            }
                        }

                        // -------- Температуры
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text("Температуры")
                                    .font(.headline)
                                Spacer()
                                Button {
                                    vm.addTemperature()
                                } label: {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.title2)
                                        .padding(6)
                                }
                                .buttonStyle(.plain)
                                .contentShape(Rectangle())
                            }

                            if vm.temperatures.isEmpty {
                                Text("Добавьте температуры")
                                    .foregroundColor(.secondary)
                                    .padding(.vertical, 40)
                                    .frame(maxWidth: .infinity, alignment: .center)
                            } else {
                                ScrollView(.horizontal, showsIndicators: false) {
                                    HStack(spacing: 16) {
                                        ForEach($vm.temperatures) { $config in
                                            VStack(spacing: 8) {
                                                VerticalTemperatureSlider(
                                                    value: $config.value,
                                                    range: temperatureRange
                                                )

                                                Button(role: .destructive) {
                                                    vm.remove(config)
                                                } label: {
                                                    Image(systemName: "trash")
                                                        .font(.title3)
                                                        .padding(8)
                                                }
                                                .buttonStyle(.plain)
                                                .contentShape(Rectangle())
                                            }
                                        }
                                    }
                                    .padding(.horizontal, 4)
                                }
                            }
                        }

                        // -------- Кнопка отправки
                        Button {
                            Task { await send() }
                        } label: {
                            HStack {
                                if vm.isLoading {
                                    ProgressView().tint(.white)
                                }
                                Text(vm.isLoading ? "Запрашиваем…" : "Отправить запросы")
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(vm.isLoading ? Color.gray : Color.accentColor)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                        }
                        .disabled(sendDisabled)

                        // -------- Ошибка
                        if let error = vm.errorMessage {
                            Text(error)
                                .font(.footnote)
                                .foregroundColor(.red)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }

                        // -------- Результаты + "Поделиться"
                        if !vm.results.isEmpty {
                            Divider()
                            HStack {
                                Text("Результаты")
                                    .font(.headline)
                                Spacer()
                                Button {
                                    shareResults()
                                } label: {
                                    Label("Поделиться", systemImage: "square.and.arrow.up")
                                        .font(.subheadline)
                                }
                            }
                            .frame(maxWidth: .infinity)

                            LazyVStack(alignment: .leading, spacing: 12) {
                                ForEach(vm.results) { item in
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(String(format: "Температура: %.1f", item.temperature))
                                            .font(.subheadline.weight(.semibold))
                                        Text(item.text)
                                            .font(.body)
                                    }
                                    .padding(10)
                                    .background(
                                        RoundedRectangle(cornerRadius: 12)
                                            .fill(Color(.secondarySystemBackground))
                                    )
                                }
                            }
                            .id("resultsSection")   // ⬅ сюда будем скроллить
                        }
                    }
                    .padding()
                }
                // автоскролл к результатам, когда они обновились
                .onChange(of: vm.results.count) { count in
                    guard count > 0 else { return }
                    withAnimation {
                        proxy.scrollTo("resultsSection", anchor: .top)
                    }
                }
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItemGroup(placement: .keyboard) {
                        Spacer()
                        Button("Отправить") {
                            Task { await send() }
                        }
                        .disabled(sendDisabled)
                    }
                }
                .sheet(isPresented: $isShowingMail) {
                    MailView(
                        subject: "Результаты — День 6: Температуры",
                        body: mailBody
                    )
                }
                .alert("Не удалось открыть Почту", isPresented: $showMailError) {
                    Button("OK", role: .cancel) { }
                } message: {
                    Text("На устройстве не настроена отправка писем.")
                }
            }
        }
    }

    private var sendDisabled: Bool {
        vm.isLoading ||
        vm.temperatures.isEmpty ||
        vm.prompt.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    private func send() async {
        // 1. сразу прячем клавиатуру
        isPromptFocused = false
        hideKeyboard()

        // 2. лёгкий хаптик "успешное действие"
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.success)

        // 3. отправка запросов
        await vm.runRequests()
    }

    // ------- Формирование тела письма для "Поделиться"

    private func buildMailBody() -> String {
        var lines: [String] = []

        lines.append("Эксперимент: День 6 — Температуры")
        lines.append("")
        lines.append("Запрос:")
        lines.append(vm.prompt)
        lines.append("")
        lines.append(String(repeating: "═", count: 40))
        lines.append("")

        for item in vm.results {
            lines.append(String(format: "Температура: %.1f", item.temperature))
            lines.append(String(repeating: "─", count: 40))
            lines.append(item.text)
            lines.append("")
        }

        return lines.joined(separator: "\n")
    }

    private func shareResults() {
        let body = buildMailBody()
        if MFMailComposeViewController.canSendMail() {
            mailBody = body
            isShowingMail = true
        } else {
            showMailError = true
        }
    }
}

// утилита для скрытия клавиатуры
private func hideKeyboard() {
    UIApplication.shared.sendAction(
        #selector(UIResponder.resignFirstResponder),
        to: nil,
        from: nil,
        for: nil
    )
}

// MARK: - Точка входа

struct TemperatureChatApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

#Preview {
    ContentView()
}
