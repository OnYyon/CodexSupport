#include <cstddef>
#include <stdexcept>
#include <string>
#include <optional>
#include <unordered_set>
#include <random>
#include <iostream>

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
std::pair<Elem*, Elem*> split(Elem* t, uint pos, bool persistent = false);
Elem* merge(Elem* l, Elem* r);

struct Elem {
    int priority;
    int64_t value;

    Elem* l = nullptr;
    Elem* r = nullptr;

    uint count = 1;
    int64_t agg;
    int64_t promise = 0;
    bool reverse = false;

    Elem(int priority, int64_t value): priority(priority), value(value), agg(value) {}

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
            if (reverse) {
                l->reverse = !l->reverse;
            }
        }
        if (r != nullptr) {
            r->promise = op(r->promise, promise);
            if (reverse) {
                r->reverse = !r->reverse;
            }
        }
        promise = 0;
        if (reverse) {
            reverse = false;
            std::swap(l, r);
        }
    }
};

class Treap {
    friend void dump(const Treap&, const std::string&);

public:
    Treap(int n) : n(n), distribution(std::uniform_int_distribution<int>(1, 10 * n)) {}

    bool insert(uint pos, int64_t target_value) {
        Elem* new_elem = create_elem(target_value);
        if (new_elem == nullptr) {
            return false;
        }

        auto [root_l, root_r] = split(root, pos);
        root_l = merge(root_l, new_elem);
        root = merge(root_l, root_r);

        return true;
    }

    std::optional<int64_t> erase(uint pos) {
        auto [l, r] = split(root, pos);
        auto [erased, rr] = split(r, 1);
        root = merge(l, rr);

        if (erased == nullptr) {
            return std::nullopt;
        }

        int64_t value = erased->value;
        erase(erased);
        return value;
    }

    // [lp, rp)
    std::optional<int64_t> get_agg(uint lp, uint rp) {
        if (!check_correct_range(lp, rp)) {
            return std::nullopt;
        }

        auto [_, r] = split(root, lp, true);
        auto [l, __] = split(r, rp - lp, true);
        if (l == nullptr) {
            return std::nullopt;
        }

        return op(l->agg, l->promise, l->count);
    }

    bool perform_op_on_seg(uint lp, uint rp, int64_t value) {
        return perform_op_on_seg(lp, rp, [&value](Elem* rl) {
            rl->promise = value;
        });
    }

    bool reverse(uint lp, uint rp) {
        return perform_op_on_seg(lp, rp, [](Elem* rl) {
            rl->reverse = true;
        });
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

    Elem* create_elem(int64_t value) {
        if (priorities.size() == n) {
            throw(std::out_of_range{"buffer overflow"});
        }

        int priority = gen_priority();
        return new Elem(priority, value);
    }

    void erase(Elem* elem) {
        priorities.erase(elem->priority);
        delete elem;
    }

    bool check_correct_range(uint lp, uint rp) {
        return lp <= rp && root != nullptr && rp <= root->count;
    }

    bool perform_op_on_seg(uint lp, uint rp, std::function<void(Elem*)> op) {
        if (!check_correct_range(lp, rp)) {
            return false;
        }

        auto [l, r] = split(root, lp);
        auto [rl, rr] = split(r, rp - lp);
        if (rl != nullptr) {
            op(rl);
        }

        merge(rl, rr);
        merge(l, r);
        return rl != nullptr;
    }
};

// l = (-inf; pos); r = [pos; +inf)
std::pair<Elem*, Elem*> split(Elem* t, uint pos, bool persistent) {
    if (t == nullptr) {
        return {nullptr, nullptr};
    }

    t->keep_and_deliver_promise();

    Elem* new_t = t;
    if (persistent) {
        new_t = new Elem(*t);
    }

    std::pair<Elem*, Elem*> res;
    uint l_count = 0;
    if (new_t->l != nullptr) {
        l_count = new_t->l->count;
    }
    if (l_count < pos) {
        auto [rl, rr] = split(new_t->r, pos - (l_count + 1), persistent);
        new_t->r = rl;
        res = {new_t, rr};
    } else {
        auto [ll, lr] = split(new_t->l, pos, persistent);
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

#include "implicit_treap_dump.hpp"

int main() {
    Treap tree(32);
    dump(tree, "treap_dumps/00_empty.svg");

    uint pos = 0;
    for (int64_t value : {10, 20, 30, 40, 50}) {
        tree.insert(pos++, value);
    }
    dump(tree, "treap_dumps/01_insertions.svg"); // [10, 20, 30, 40, 50]

    tree.insert(2, 25);
    dump(tree, "treap_dumps/02_insert_middle.svg"); // [10, 20, 25, 30, 40, 50]

    std::cout << "erase(4) = " << tree.erase(4).value() << '\n'; // 40
    dump(tree, "treap_dumps/03_erase.svg"); // [10, 20, 25, 30, 50]

    // All ranges are half-open: [lp, rp).
    tree.perform_op_on_seg(1, 4, 7);
    dump(tree, "treap_dumps/04_add.svg"); // [10, 27, 32, 37, 50]

    tree.reverse(1, 5);
    dump(tree, "treap_dumps/05_reverse.svg"); // [10, 50, 37, 32, 27]

    std::cout << "sum[1, 4) = " << tree.get_agg(1, 4).value() << '\n'; // 119
    dump(tree, "treap_dumps/06_sum.svg");

    tree.reverse(0, 5);
    dump(tree, "treap_dumps/07_reverse_all.svg"); // [27, 32, 37, 50, 10]

    std::cout << "erase(0) = " << tree.erase(0u).value() << '\n'; // 27
    tree.insert(0, -5);
    dump(tree, "treap_dumps/08_erase_insert.svg"); // [-5, 32, 37, 50, 10]

    std::cout << "sum[0, 5) = " << tree.get_agg(0, 5).value() << '\n'; // 124
    dump(tree, "treap_dumps/09_final.svg");
    std::cout << "Snapshots saved to treap_dumps/*.svg\n";
}
