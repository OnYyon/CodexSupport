#pragma once

#include <vector>

std::vector<size_t> calc_prefix(const std::string& s) {
    size_t n = s.size();
    std::vector<size_t> prefix(n);
    for (size_t i = 1; i < n; ++i) {
        size_t j = prefix[i - 1];
        while (j > 0 && s[j] != s[i]) {
            j = prefix[j - 1];
        }

        if (s[j] == s[i]) {
            ++j;
        }
        prefix[i] = j;
    }

    return prefix;
}
