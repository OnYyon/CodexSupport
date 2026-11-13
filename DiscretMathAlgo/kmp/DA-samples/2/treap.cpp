#include <cstddef>
#include <stdexcept>
#include <string>
#include <optional>
#include <unordered_set>
#include <random>

struct Elem;
std::pair<Elem*, Elem*> split(Elem* t, int key);
Elem* merge(Elem* l, Elem* r);

struct Elem {
    int key;
    int priority;
    std::string value;

    Elem* l;
    Elem* r;

    std::optional<std::string> get(int target_key) {
        if (target_key == key) {
            return value;
        }

        if (target_key < key) {
            if (l != nullptr) {
                return l->get(target_key);
            }
        } else {
            if (r != nullptr) {
                return r->get(target_key);
            }
        }

        return std::nullopt;
    }
};

class Treap {
public:
    Treap(int n) : n(n), distribution(std::uniform_int_distribution<int>(1, 10 * n)) {}

    std::optional<std::string> get(int target_key) {
        if (root == nullptr) {
            return std::nullopt;
        }

        return root->get(target_key);
    }

    bool insert_simple(int target_key, std::string target_value) {
        Elem* new_elem = create_elem(target_key, target_value);
        if (new_elem == nullptr) {
            return false;
        }

        auto [root_l, root_r] = split(root, target_key);
        root_l = merge(root_l, new_elem);
        root = merge(root_l, root_r);

        return true;
    }
    bool insert_cool(int target_key, std::string target_value) {
        Elem* new_elem = create_elem(target_key, target_value);
        if (new_elem == nullptr) {
            return false;
        }

        if (root == nullptr) {
            root = new_elem;
            return true;
        }

        Elem* elem = root;
        Elem* parent = nullptr;
        char branch;
        while (true) {
            if (elem == nullptr) {
                if (branch == 'l') {
                    parent->l = new_elem;
                } else {
                    parent->r = new_elem;
                }
                return true;
            }

            if (new_elem->priority > elem->priority) {
                break;
            }

            parent = elem;
            if (new_elem->key < elem->key) {
                elem = elem->l;
                branch = 'l';
            } else {
                elem = elem->r;
                branch = 'r';
            }
        }

        auto [l, r] = split(elem, target_key);
        new_elem->l = l;
        new_elem->r = r;

        if (parent != nullptr) {
            if (branch == 'l') {
                parent->l = new_elem;
            } else {
                parent->r = new_elem;
            }
        } else {
            root = new_elem;
        }

        return true;
    }

    std::optional<std::string> erase_simple(int target_key) {
        auto [l, r] = split(root, target_key);
        auto [ll, erased] = split(l, target_key - 1);
        root = merge(ll, r);

        if (erased == nullptr) {
            return std::nullopt;
        }

        std::string value = erased->value;
        erase(erased);
        return value;
    }
    std::optional<std::string> erase_cool(int target_key) {
        Elem* elem = root;
        Elem* parent = nullptr;
        char branch;
        while (true) {
            if (elem == nullptr) {
                return std::nullopt;
            }

            if (elem->key == target_key) {
                break;
            }

            parent = elem;
            if (target_key <= elem->key) {
                elem = elem->l;
                branch = 'l';
            } else {
                elem = elem->r;
                branch = 'r';
            }
        }

        Elem* new_elem = merge(elem->l, elem->r);
        if (parent != nullptr) {
            if (branch == 'l') {
                parent->l = new_elem;
            } else {
                parent->r = new_elem;
            }
        } else {
            root = new_elem;
        }

        std::string value = elem->value;
        erase(elem);
        return value;
    }

private:
    Elem* root = nullptr;
    int n;
    std::unordered_set<int> priorities;
    std::mt19937 generator = std::mt19937(std::random_device{}());
    std::uniform_int_distribution<int> distribution;

    int gen_priority() {
        int priority;
        do {
            priority = distribution(generator);
        } while (priorities.count(priority) > 0);

        priorities.insert(priority);
        return priority;
    }

    Elem* create_elem(int key, std::string value) {
        if (get(key).has_value()) {
            return nullptr;
        }

        if (priorities.size() == n) {
            throw(std::out_of_range{"buffer overflow"});
        }

        int priority = gen_priority();
        return new Elem{key, priority, value};
    }

    void erase(Elem* elem) {
        priorities.erase(elem->priority);
        delete elem;
    }
};

std::pair<Elem*, Elem*> split(Elem* t, int key) {
    if (t == nullptr) {
        return {nullptr, nullptr};
    }

    if (key < t->key) {
        auto [ll, lr] = split(t->l, key);
        t->l = lr;
        return {ll, t};
    }

    auto [rl, rr] = split(t->r, key);
    t->r = rl;
    return {t, rr};
}

Elem* merge(Elem* l, Elem* r) {
    if (l == nullptr) {
        return r;
    }
    if (r == nullptr) {
        return l;
    }

    if (l->priority < r->priority) {
        r->l = merge(l, r->l);
        return r;
    }
    l->r = merge(l->r, r);
    return l;
}
