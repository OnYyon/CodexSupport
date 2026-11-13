#include <iostream>
#include <random>

#include "z.hpp"
#include "check_substr.hpp"

constexpr char sentinel = '$';

std::vector<size_t> find_substr(const std::string& text, const std::string& pattern) {
    const size_t m = pattern.size();
    const std::string s = pattern + std::string{sentinel} + text;
    const std::vector<size_t> z = calc_z(s);
    std::vector<size_t> result;
    for (size_t i = m; i < s.size(); ++i) {
        if (z[i] == m) {
            result.push_back(i - (m + 1));
        }
    }

    return result;
}

int main() {
    std::mt19937 generator(52);
    std::uniform_int_distribution<uint8_t> chars(67, 69);
    std::uniform_int_distribution<size_t> sizes(3, 50);

    for (int i = 0; i < 1000; ++i) {
        size_t n1 = sizes(generator);
        std::vector<char> s1_vec(n1);
        for (size_t i = 0; i < n1; ++i) {
            s1_vec[i] = static_cast<char>(chars(generator));
        }
        std::string s1(s1_vec.begin(), s1_vec.end());
        size_t n2 = sizes(generator);
        std::vector<char> s2_vec(n2);
        for (size_t i = 0; i < n2; ++i) {
            s2_vec[i] = static_cast<char>(chars(generator));
        }
        std::string s2(s2_vec.begin(), s2_vec.end());

        std::string text;
        std::string pattern;
        if (s1.size() > s2.size()) {
            text = std::move(s1);
            pattern = std::move(s2);
        } else {
            text = std::move(s2);
            pattern = std::move(s1);
        }
        std::vector<size_t> indexes = find_substr(text, pattern);
        bool substr = check_substr(text, pattern, indexes);

        if (indexes.size() > 0) {
            std::cout
                << "text:    " << text << "\n"
                << "pattern: " << pattern << "\n"
                << "indexes: ";
            for (size_t i = 0; i < indexes.size(); ++i) {
                std::cout << indexes[i] << " ";
            }
            std::cout << "\n" << std::endl;
        }

        if (!substr) {
            std::cout << "This is not a substring!" << std::endl;
            return 1;
        }
    }

    std::cout << "Done!" << std::endl;
}
