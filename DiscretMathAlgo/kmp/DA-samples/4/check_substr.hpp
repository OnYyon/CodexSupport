#pragma once

#include <vector>

bool check_substr(const std::string& text, const std::string& pattern,
                  const std::vector<size_t>& expected_indexes) {
    size_t n = text.size(), m = pattern.size();
    std::vector<size_t> actual_indexes;
    for (size_t i = 0; i + m - 1 < n; ++i) {
        bool substr = true;
        for (size_t j = 0; j < m && substr; ++j) {
            substr = (text[i + j] == pattern[j]);
        }
        if (substr) {
            actual_indexes.push_back(i);
        }
    }

    bool ok = expected_indexes.size() == actual_indexes.size();
    for (size_t i = 0; i < expected_indexes.size() && ok; ++i) {
        ok = (expected_indexes[i] == actual_indexes[i]);
    }
    return ok;
}
