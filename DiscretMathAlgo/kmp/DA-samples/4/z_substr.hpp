#pragma once

#include "z_sample.hpp"

constexpr char sentinel = '$';

std::vector<size_t> find_substr(const std::string& text, const std::string& pattern) {
    const size_t n = text.size();
    const size_t m = pattern.size();
    const std::string s = pattern + sentinel + text;
    const std::vector<size_t> z = calc_z(s);

    std::vector<size_t> indexes;
    for (size_t i = 0; i < n; ++i) {
        if (z[m + 1 + i] == m) {
            indexes.push_back(i);
        }
    }

    return indexes;
}
