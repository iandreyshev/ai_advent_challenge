//
//  Utils.swift
//  AIAdventChallengeDay8
//
//  Created by Ivan Andreyshev on 10.12.2025.
//

func wordCount(_ text: String) -> Int {
    // Простейший вариант: делим по пробелам и переводам строки
    text
        .split { $0.isWhitespace || $0.isNewline }
        .count
}
