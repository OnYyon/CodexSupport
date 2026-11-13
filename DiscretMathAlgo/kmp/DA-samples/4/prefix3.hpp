#pragma once

#include <vector>

std::vector<size_t> calc_prefix(const std::string& s) {
    size_t n = s.size();
    std::vector<size_t> prefix(n);
    for (size_t i = 0; i < n; ++i) {         // index
        for (size_t j = 1; j < i + 1; ++j) { // prefix/suffix size
            bool ok = true;
            for (size_t k = 0; k < j && ok; ++k) {
                ok = (s[k] == s[i - j + 1 + k]);
            }
            if (ok) {
                prefix[i] = j;
            }
        }
    }
    return prefix;
}
