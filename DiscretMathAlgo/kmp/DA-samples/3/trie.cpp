#include <cstddef>
#include <memory>
#include <string>
#include <unordered_map>

class Trie {
private:
    struct Node {
        std::unordered_map<char, std::unique_ptr<Node>> children;
        bool is_word = false;
    };

    Node root;

public:
    // Возвращает false, если слово уже есть в боре.
    bool insert(const std::string& word) {
        Node* node = &root;
        for (char c : word) {
            auto& child = node->children[c];
            if (child == nullptr) {
                child = std::make_unique<Node>();
            }
            node = child.get();
        }

        if (node->is_word) {
            return false;
        }
        node->is_word = true;
        return true;
    }

    bool contains(const std::string& word) const {
        const Node* node = find_node(word);
        return node != nullptr && node->is_word;
    }

    bool starts_with(const std::string& prefix) const {
        return find_node(prefix) != nullptr;
    }

    // Возвращает false, если слова нет в боре.
    bool erase(const std::string& word) {
        return erase(root, word, 0);
    }

private:
    const Node* find_node(const std::string& text) const {
        const Node* node = &root;
        for (char c : text) {
            auto it = node->children.find(c);
            if (it == node->children.end()) {
                return nullptr;
            }
            node = it->second.get();
        }
        return node;
    }

    bool erase(Node& node, const std::string& word, std::size_t pos) {
        if (pos == word.size()) {
            if (!node.is_word) {
                return false;
            }
            node.is_word = false;
            return true;
        }

        auto it = node.children.find(word[pos]);
        if (it == node.children.end() || !erase(*it->second, word, pos + 1)) {
            return false;
        }

        // Убираем узел, если через него больше не проходит ни одно слово.
        if (!it->second->is_word && it->second->children.empty()) {
            node.children.erase(it);
        }
        return true;
    }
};
