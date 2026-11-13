#pragma once

#include "prefix.hpp"

constexpr char sentinel = '$';

std::vector<size_t> kmp(const std::string& text, const std::string& src_pattern) {
    size_t n = text.size();
    size_t m = src_pattern.size();
    std::string pattern = src_pattern + sentinel;

    std::vector<size_t> prefix = calc_prefix(pattern);

    std::vector<size_t> indexes;
    size_t prev_prefix = 0;
    for (size_t i = 0; i < n; ++i) {
        size_t j = prev_prefix;
        while (j > 0 && pattern[j] != text[i]) {
            j = prefix[j - 1];
        }

        if (pattern[j] == text[i]) {
            ++j;
        }
        if (j == m) {
            indexes.push_back(i - j + 1);
        }
        prev_prefix = j;
    }

    return indexes;
}
