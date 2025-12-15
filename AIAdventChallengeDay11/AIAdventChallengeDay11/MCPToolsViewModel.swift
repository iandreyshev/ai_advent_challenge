//
//  MCPToolsViewModel.swift
//  AIAdventChallengeDay11
//
//  Created by Ivan Andreyshev on 15.12.2025.
//

import Foundation
import MCP
import Combine

@MainActor
final class MCPToolsViewModel: ObservableObject {

    @Published var tools: [String] = []
    @Published var status: String = "Not connected"
    @Published var isLoading = false

    private let client = Client(
        name: "MCPToolsIOS",
        version: "1.0.0"
    )

    func connectAndLoadTools() async {
        isLoading = true
        defer { isLoading = false }

        do {
            var config = URLSessionConfiguration.default
            config.httpAdditionalHeaders = [
                "Authorization": "Bearer \(Secrets.authToken)"
            ]

            let transport = HTTPClientTransport(
                endpoint: Secrets.mcpEndpoint,
                configuration: config,
                streaming: true
            )

            let initResult = try await client.connect(
                transport: transport
            )

            guard initResult.capabilities.tools != nil else {
                status = "Connected, but no tools capability"
                tools = []
                return
            }

            let (tools, _) = try await client.listTools()
            self.tools = tools.map { $0.name }.sorted()
            status = "Connected. Tools: \(tools.count)"

        } catch {
            print(error.localizedDescription)
            status = "Error: \(error.localizedDescription)"
            tools = []
        }
    }
}
