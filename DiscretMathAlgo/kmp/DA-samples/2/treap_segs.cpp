#include <cstddef>
#include <stdexcept>
#include <string>
#include <optional>
#include <unordered_set>
#include <random>

int64_t op(int64_t a, int64_t b) {
    return a + b;
}
int64_t op(int64_t a, uint count) {
    return a * count;
}

int64_t op(int64_t agg, int64_t promise, uint count) {
    return op(agg, op(promise, count));
}

struct Elem;
std::pair<Elem*, Elem*> split(Elem* t, int key, bool persistent = false);
Elem* merge(Elem* l, Elem* r);

struct Elem {
    int key;
    int priority;
    int64_t value;

    Elem* l = nullptr;
    Elem* r = nullptr;

    uint count = 1;
    int64_t agg;
    int64_t promise = 0;

    Elem(int key, int priority, int64_t value): key(key), priority(priority), value(value), agg(value) {}

    void recalc() {
        count = 1;
        if (l != nullptr) {
            count += l->count;
        }
        if (r != nullptr) {
            count += r->count;
        }

        agg = value;
        if (l != nullptr) {
            agg = op(agg, op(l->agg, l->promise, l->count));
        }
        if (r != nullptr) {
            agg = op(agg, op(r->agg, r->promise, r->count));
        }
    }

    void keep_and_deliver_promise() {
        value = op(value, promise);
        agg = op(agg, promise, count);
        if (l != nullptr) {
            l->promise = op(l->promise, promise);
        }
        if (r != nullptr) {
            r->promise = op(r->promise, promise);
        }
        promise = 0;
    }

    std::optional<int64_t> get(int target_key) {
        keep_and_deliver_promise();

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

    std::optional<int64_t> get_k_order_statistic(uint k) {
        keep_and_deliver_promise();

        uint l_count = 0;
        if (l != nullptr) {
            l_count = l->count;
            if (k < l_count) {
                return l->get_k_order_statistic(k);
            }
        }
        if (k == l_count) {
            return value;
        }
        if (r != nullptr && k < l_count + 1 + r->count) {
            return r->get_k_order_statistic(k - (l_count + 1));
        }

        return std::nullopt;
    }
};

class Treap {
public:
    Treap(int n) : n(n), distribution(std::uniform_int_distribution<int>(1, 10 * n)) {}

    std::optional<int64_t> get(int target_key) {
        if (root == nullptr) {
            return std::nullopt;
        }

        return root->get(target_key);
    }

    std::optional<int64_t> get_k_order_statistic(uint k) {
        if (root == nullptr) {
            return std::nullopt;
        }

        return root->get_k_order_statistic(k);
    }

    bool insert(int target_key, int64_t target_value) {
        Elem* new_elem = create_elem(target_key, target_value);
        if (new_elem == nullptr) {
            return false;
        }

        auto [root_l, root_r] = split(root, target_key);
        root_l = merge(root_l, new_elem);
        root = merge(root_l, root_r);

        return true;
    }

    std::optional<int64_t> erase(int target_key) {
        auto [l, r] = split(root, target_key);
        auto [erased, rr] = split(r, target_key + 1);
        root = merge(l, rr);

        if (erased == nullptr) {
            return std::nullopt;
        }

        int64_t value = erased->value;
        erase(erased);
        return value;
    }

    // [lk, rk)
    std::optional<int64_t> get_agg(int lk, int rk) {
        auto [_, r] = split(root, lk, true);
        if (r == nullptr) {
            return std::nullopt;
        }

        auto [l, __] = split(r, rk, true);
        if (l == nullptr) {
            return std::nullopt;
        }

        return op(l->agg, l->promise, l->count);
    }

    // [lk, rk)
    bool perform_op_on_seg(int lk, int rk, int64_t value) {
        auto [l, r] = split(root, lk);
        auto [rl, rr] = split(r, rk);
        if (rl != nullptr) {
            rl->promise = value;
        }
        merge(rl, rr);
        merge(l, r);
        return rl != nullptr;
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

    Elem* create_elem(int key, int64_t value) {
        if (get(key).has_value()) {
            return nullptr;
        }

        if (priorities.size() == n) {
            throw(std::out_of_range{"buffer overflow"});
        }

        int priority = gen_priority();
        return new Elem(key, priority, value);
    }

    void erase(Elem* elem) {
        priorities.erase(elem->priority);
        delete elem;
    }
};

// l = (-inf; key); r = [key; +inf)
std::pair<Elem*, Elem*> split(Elem* t, int key, bool persistent) {
    if (t == nullptr) {
        return {nullptr, nullptr};
    }

    t->keep_and_deliver_promise();

    Elem* new_t = t;
    if (persistent) {
        new_t = new Elem(*t);
    }

    std::pair<Elem*, Elem*> res;
    if (new_t->key < key) {
        auto [rl, rr] = split(new_t->r, key, persistent);
        new_t->r = rl;
        res = {new_t, rr};
    } else {
        auto [ll, lr] = split(new_t->l, key, persistent);
        new_t->l = lr;
        res = {ll, new_t};
    }

    new_t->recalc();
    return res;
}

Elem* merge(Elem* l, Elem* r) {
    if (l == nullptr) {
        return r;
    }
    if (r == nullptr) {
        return l;
    }

    Elem* t;
    if (l->priority < r->priority) {
        r->keep_and_deliver_promise();
        r->l = merge(l, r->l);
        t = r;
    } else {
        l->keep_and_deliver_promise();
        l->r = merge(l->r, r);
        t = l;
    }

    t->recalc();
    return t;
}
