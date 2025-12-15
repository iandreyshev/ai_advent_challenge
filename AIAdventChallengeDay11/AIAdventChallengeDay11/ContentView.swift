//
//  ContentView.swift
//  AIAdventChallengeDay11
//
//  Created by Ivan Andreyshev on 15.12.2025.
//

import SwiftUI
import Combine

struct ContentView: View {

    @StateObject private var vm = MCPToolsViewModel()

    var body: some View {
        NavigationView {
            VStack {
                Spacer()

                Button(action: {
                    Task { await vm.connectAndLoadTools() }
                }) {
                    Text(vm.isLoading ? "Connecting..." : "Try connect")
                        .font(.headline)
                        .frame(maxWidth: 220)
                        .padding(.vertical, 14)
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                }
                .disabled(vm.isLoading)

                Spacer()

                if !vm.status.isEmpty {
                    Text(vm.status)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.bottom, 8)
                }

                if !vm.tools.isEmpty {
                    List(vm.tools, id: \.self) { tool in
                        Text(tool)
                    }
                }
            }
            .padding()
            .navigationTitle("День 11 — MCP Tools")
        }
    }
}

#Preview {
    ContentView()
}
