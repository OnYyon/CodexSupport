#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <limits>
#include <string>
#include <vector>

namespace kmp_z {

// z[0] = 0; окно совпадения [l, r) имеет исключённую правую границу.
std::vector<std::size_t> z_function(const std::string& pattern) {
    const std::size_t m = pattern.size();
    std::vector<std::size_t> z(m, 0);
    std::size_t l = 0;
    std::size_t r = 0;
    for (std::size_t i = 1; i < m; ++i) {
        if (i < r) {
            z[i] = std::min(r - i, z[i - l]);
        }
        while (i + z[i] < m && pattern[z[i]] == pattern[i + z[i]]) {
            ++z[i];
        }
        if (i + z[i] > r) {
            l = i;
            r = i + z[i];
        }
    }
    return z;
}

// Линейное преобразование Z-функции образца в префикс-функцию.
// Предусловие: z — корректная Z-функция некоторой строки, z[0] = 0.
std::vector<std::size_t> strong_prefix(const std::vector<std::size_t>& z) {
    std::vector<std::size_t> prefix(z.size(), 0);
    for (std::size_t i = 1; i < z.size(); ++i) {
        for (std::size_t length = z[i]; length > 0; --length) {
            const std::size_t end = i + length - 1;
            if (prefix[end] != 0) {
                break;
            }
            prefix[end] = length;
        }
    }
    return prefix;
}

// Поиск по байтам, позиции с нуля, включая перекрывающиеся вхождения.
// Пустой образец совпадает на всех text.size() + 1 границах текста.
std::vector<std::size_t> kmp(const std::string& text, const std::string& pattern) {
    std::vector<std::size_t> positions;
    if (pattern.empty()) {
        positions.push_back(0);
        for (std::size_t i = 0; i < text.size(); ++i) {
            positions.push_back(i + 1);
        }
        return positions;
    }

    const auto prefix = strong_prefix(z_function(pattern));
    std::size_t matched = 0;
    for (std::size_t i = 0; i < text.size(); ++i) {
        while (matched > 0 && pattern[matched] != text[i]) {
            matched = prefix[matched - 1];
        }
        if (pattern[matched] == text[i]) {
            ++matched;
        }
        if (matched == pattern.size()) {
            positions.push_back(i + 1 - pattern.size());
            matched = prefix[matched - 1];
        }
    }
    return positions;
}

// Контракт как у find_all. Подготовка O(m * alphabet_size),
// память O((m + 1) * alphabet_size), один переход на каждый байт текста.
// Расширение vector ответов может выделять память; гарантия O(1)
// относится к переходу автомата, а не к сбору результата.
inline std::vector<std::size_t> kmp_realtime(const std::string& text, const std::string& pattern) {
    const std::size_t m = pattern.size();
    std::vector<std::size_t> positions;
    if (pattern.empty()) {
        positions.push_back(0);
        for (std::size_t i = 0; i < text.size(); ++i) {
            positions.push_back(i + 1);
        }
        return positions;
    }

    constexpr std::size_t alphabet_size = std::numeric_limits<unsigned char>::max() + 1;
    const auto prefix = strong_prefix(z_function(pattern));
    std::vector<std::array<std::size_t, alphabet_size>> go(m + 1);
    go[0][pattern[0]] = 1;
    for (std::size_t state = 1; state <= m; ++state) {
        go[state] = go[prefix[state - 1]];
        if (state < m) {
            go[state][pattern[state]] = state + 1;
        }
    }

    std::size_t matched = 0;
    for (std::size_t i = 0; i < text.size(); ++i) {
        matched = go[matched][text[i]];
        if (matched == m) {
            positions.push_back(i + 1 - m);
        }
    }
    return positions;
}

}  // namespace kmp_z
