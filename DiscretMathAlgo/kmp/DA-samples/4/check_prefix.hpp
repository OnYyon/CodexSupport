#pragma once

#include <vector>

bool check_prefix(const std::string& s, std::vector<size_t> expected_prefix) {
    size_t n = s.size();
    std::vector<size_t> actual_prefix(n);
    for (size_t i = 0; i < n; ++i) {         // index
        for (size_t j = 1; j < i + 1; ++j) { // prefix/suffix size
            bool ok = true;
            for (size_t k = 0; k < j && ok; ++k) {
                ok = (s[k] == s[i - j + 1 + k]);
            }
            if (ok) {
                actual_prefix[i] = j;
            }
        }
    }

    bool ok = true;
    for (size_t i = 0; i < n && ok; ++i) {
        ok = (expected_prefix[i] == actual_prefix[i]);
    }
    return ok;
}
