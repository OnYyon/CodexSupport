#pragma once

#include <vector>

std::vector<size_t> calc_prefix(const std::string& s) {
    size_t n = s.size();
    std::vector<size_t> prefix(n);
    size_t size = 0;
    for (size_t i = 0; i < n; ++i) {                              // index
        for (size_t j = std::min(i, size + 1); j > 0; --j) { // prefix/suffix size
            bool ok = true;
            for (size_t k = 0; k < j && ok; ++k) {
                ok = (s[k] == s[i - j + 1 + k]);
            }
            if (ok) {
                prefix[i] = j;
                break;
            }
        }
        size = prefix[i];
    }
    return prefix;
}
