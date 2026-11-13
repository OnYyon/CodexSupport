#include <concepts>
#include <string>
#include <cassert>
#include <optional>

template<typename T>
concept Comparable = requires(const T& a, const T& b) {
    { a < b } -> std::convertible_to<bool>;
    { a == b } -> std::convertible_to<bool>;
};

template<Comparable Key, typename Value>
class Tree {
public:
    Tree() {
        null_node = create_node(Node());
        null_node->color = Color::Black;
    }

    void insert(const Key& key, const Value& value) {
        Node* child = create_node(Node(key, value, nullptr));
        if (root == nullptr) {
            root = child;
            root->color = Color::Black;
            return;
        }

        Node* parent = root->find_parent(key);
        assert(parent != nullptr);
        parent->adopt(child);
        Node* new_root = child->balancing_insert();
        if (new_root != nullptr) {
            root = new_root;
        }
    }

    std::optional<Value> erase(const Key& key) {
        if (root == nullptr) {
            return std::nullopt;
        }

        Node* node_erased = root->find(key);
        if (node_erased == nullptr) {
            return std::nullopt;
        }
        Node* node_for_balancing = nullptr;

        if (node_erased->l != null_node && node_erased->r != null_node) {
            Node* next_node = node_erased->r->get_left();
            std::swap(node_erased->key, next_node->key);
            std::swap(node_erased->value, next_node->value);
            node_erased = next_node;
        }

        assert(node_erased->l == null_node || node_erased->r == null_node);
        if (node_erased->l == null_node && node_erased->r == null_node) {
            node_for_balancing = null_node;
        } else if (node_erased->l == null_node) {
            node_for_balancing = node_erased->r;
        } else if (node_erased->r == null_node) {
            node_for_balancing = node_erased->l;
        }

        if (node_erased->parent == nullptr) {
            root = nullptr;
            if (node_for_balancing != null_node) {
                root = node_for_balancing;
            } else {
                return erase_node(node_erased);
            }
        } else {
            node_erased->parent->replace_child(node_erased, node_for_balancing);
        }
        node_for_balancing->parent = node_erased->parent;

        if (node_erased->color == Color::Red) {
            return erase_node(node_erased);
        }

        Node* new_root = node_for_balancing->balancing_erase();
        if (new_root != nullptr) {
            root = new_root;
        }

        return erase_node(node_erased);
    }

private:
    enum Color {
        Red = 0,
        Black = 1,
    };

    class Node {
    public:
        Key key;
        Value value;

        Node* l = nullptr;
        Node* r = nullptr;
        Node* parent = nullptr;
        Color color = Color::Red;

        Node() = default;
        Node(const Key& key, const Value& value, Node* parent) : key(key), value(value), parent(parent) {}

        Node* find_parent(const Key& target_key) {
            if (target_key < key) {
                if (l->l == nullptr) {
                    return this;
                }
                return l->find_parent(target_key);
            } else {
                if (r->l == nullptr) {
                    return this;
                }
                return r->find_parent(target_key);
            }
        }

        Node* find(const Key& target_key) {
            if (l == nullptr) {
                return nullptr;
            }

            if (target_key == key) {
                return this;
            } else if (target_key < key) {
                return l->find(target_key);
            } else {
                return r->find(target_key);
            }
        }

        Node* get_left() {
            if (l->l != nullptr) {
                return l->get_left();
            }
            return this;
        }

        void adopt(Node* child) {
            if (child->key < key) {
                l = child;
            } else {
                r = child;
            }
            child->parent = this;
        }

        Node* get_brother() {
            assert(this->parent != nullptr);
            return this->parent->l == this ? this->parent->r : this->parent->l;
        }

        void swap_colors() {
            assert(
                this->color == Color::Black
                && this->l != nullptr && this->l->color == Color::Red
                && this->r != nullptr && this->r->color == Color::Red
            );
            this->color = Color::Red;
            this->l->color = Color::Black;
            this->r->color = Color::Black;
        }

        void replace_child(Node* old_child, Node* new_child) {
            if (l == old_child) {
                l = new_child;
            } else {
                r = new_child;
            }
        }

        Node* right_rotate() {
            bool is_root = true;
            if (parent != nullptr) {
                parent->replace_child(this, l);
                is_root = false;
            }

            Node* b = l;
            b->parent = parent;
            parent = b;
            l = b->r;
            if (b->r->l != nullptr) {
                b->r->parent = this;
            }
            b->r = this;

            Node* root = nullptr;
            if (is_root) {
                root = b;
            }
            return root;
        }

        Node* left_rotate() {
            bool is_root = true;
            if (parent != nullptr) {
                parent->replace_child(this, r);
                is_root = false;
            }

            Node* b = r;
            b->parent = parent;
            parent = b;
            r = b->l;
            if (b->l->l != nullptr) {
                b->l->parent = this;
            }
            b->l = this;

            Node* root = nullptr;
            if (is_root) {
                root = b;
            }
            return root;
        }

        Node* balancing_insert() {
            if (parent == nullptr) {
                color = Color::Black;
                return nullptr;
            }

            if (parent->color == Color::Black) {
                return nullptr;
            }

            Node* uncle = parent->get_brother();
            assert(uncle != nullptr);
            if (uncle->color == Color::Red) {
                parent->parent->swap_colors();
                return parent->parent->balancing_insert();
            }

            if (parent == parent->parent->l) {
                if (parent->r == this) {
                    Node* parent_old = parent;
                    parent->left_rotate();
                    return parent_old->balancing_insert();
                }

                std::swap(parent->parent->color, parent->color);
                return parent->parent->right_rotate();
            } else {
                if (parent->l == this) {
                    Node* parent_old = parent;
                    parent->right_rotate();
                    return parent_old->balancing_insert();
                }

                std::swap(parent->parent->color, parent->color);
                return parent->parent->left_rotate();
            }
        }

        Node* balancing_erase() {
            if (this->color == Color::Red) {
                this->color = Color::Black;
                return nullptr;
            }

            if (parent == nullptr) {
                return nullptr;
            }

            Node* brother = this->get_brother();
            Node* new_root = nullptr;
            if (brother->color == Color::Red) {
                std::swap(parent->color, brother->color);
                if (brother == parent->r) {
                    new_root = parent->left_rotate();
                } else {
                    new_root = parent->right_rotate();
                }
            }

            brother = this->get_brother();

            Node* new_root2 = nullptr;
            if (brother->l->color == Color::Black && brother->r->color == Color::Black) {
                brother->color = Color::Red;
                new_root2 = parent->balancing_erase();
                return new_root2 != nullptr ? new_root2 : new_root;
            }

            if (this == parent->l) {
                if (brother->r->color == Color::Black) {
                    std::swap(brother->color, brother->l->color);
                    brother->right_rotate();
                    brother = this->get_brother();
                }

                assert(brother->r->color == Color::Red);
                brother->color = parent->color;
                parent->color = Color::Black;
                brother->r->color = Color::Black;
                new_root2 = parent->left_rotate();
            } else {
                if (brother->l->color == Color::Black) {
                    std::swap(brother->color, brother->r->color);
                    brother->left_rotate();
                    brother = this->get_brother();
                }

                assert(brother->l->color == Color::Red);
                brother->color = parent->color;
                parent->color = Color::Black;
                brother->l->color = Color::Black;
                new_root2 = parent->right_rotate();
            }

            return new_root2 != nullptr ? new_root2 : new_root;
        }
    };

    Node* root = nullptr;
    Node* null_node = nullptr;

    Node* create_node(const Node& node) {
        Node* new_node = new Node(node);
        new_node->l = null_node;
        new_node->r = null_node;
        return new_node;
    }

    Value erase_node(Node* node) {
        Value value = node->value;
        delete node;
        return value;
    }
};

template class Tree<int, std::string>;
