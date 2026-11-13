#include <iostream>
#include <random>
#include <numeric>

#include "prefix_sample.hpp"
#include "check_prefix.hpp"

int main() {
    std::mt19937 generator(52);
    std::uniform_int_distribution<uint8_t> chars(67, 69);
    std::uniform_int_distribution<size_t> sizes(3, 100);

    for (int i = 0; i < 1000; ++i) {
        size_t n = sizes(generator);
        std::vector<char> s_vec(n);
        for (size_t i = 0; i < n; ++i) {
            s_vec[i] = static_cast<char>(chars(generator));
        }
        std::string s(s_vec.begin(), s_vec.end());

        const std::vector<size_t> prefix = calc_prefix(s);
        bool is_prefix = check_prefix(s, prefix);

        if (std::accumulate(prefix.begin(), prefix.end(), 0)) {
            std::cout
                << "s:      " << s << "\n"
                << "prefix: ";
            for (size_t i = 0; i < n; ++i) {
                std::cout << prefix[i] << " ";
            }
            std::cout << "\n" << std::endl;
        }

        if (!is_prefix) {
            std::cout << "This is not a prefix!" << std::endl;
            return 1;
        }
    }

    std::cout << "Done!" << std::endl;
}
