//
//  Utils.swift
//  AIAdventChallengeDay9
//
//  Created by Ivan Andreyshev on 12.12.2025.
//

import Foundation

func wordCount(_ text: String) -> Int {
    text.split { $0.isWhitespace || $0.isNewline }.count
}
