#include <iostream>
#include <random>

#include "z.hpp"

bool check_z(const std::string& s, const std::vector<size_t>& z) {
    size_t n = s.size();
    if (n == 0) { return z.size() == 0; }
    if (n == 1) { return z.size() == 1 && z[0] == 0; }

    bool ok = true;
    for (size_t i = 1; i < n; ++i) {
        for (size_t j = 0; j < z[i]; ++j) {
            if (i + j >= n || s[j] != s[i + j]) {
                ok = false;
                break;
            }
        }
        if (i + z[i] < n) {
            ok = (s[z[i]] != s[i + z[i]]);
        }

        if (!ok) {
            break;
        }
    }

    return ok;
}

int main() {
    std::mt19937 generator(42);
    std::uniform_int_distribution<uint8_t> chars(67, 69);
    std::uniform_int_distribution<size_t> sizes(3, 1000);

    for (int i = 0; i < 1000; ++i) {
        size_t n = sizes(generator);
        std::vector<char> s_vec(n);
        for (size_t i = 0; i < n; ++i) {
            s_vec[i] = static_cast<char>(chars(generator));
        }
        std::string s(s_vec.begin(), s_vec.end());
        std::vector<size_t> z = calc_z(s);
        std::cout << s << ": [0";
        for (size_t i = 1; i < n; ++i) {
            std::cout << ", " << z[i];
        }
        std::cout << "]";
        if (!check_z(s, z)) {
            std::cout << " -- This is not a z-function!" << std::endl;
            return 1;
        }
        std::cout << std::endl;
    }

    std::cout << "Done!" << std::endl;
}
