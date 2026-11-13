#pragma once

#include <vector>

std::vector<size_t> calc_z(const std::string& s) {
    size_t n = s.size();
    if (n == 0) { return {}; }
    if (n == 1) { return {0}; }

    std::vector<size_t> z(s.size());
    size_t l = 0, r = 0;
    for (size_t i = 1; i < n; ++i) {
        if (i <= r) {
            z[i] = std::min(z[i - l], r - i + 1);
        }
        while (i + z[i] < n && s[z[i]] == s[i + z[i]]) {
            ++z[i];
        }
        if (i + z[i] - 1 > r) {
            l = i;
            r = i + z[i] - 1;
        }
    }

    return z;
}
