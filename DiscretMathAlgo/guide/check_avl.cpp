#include "avl.hpp"
#include <cassert>
#include <climits>
#include <random>
#include <set>
#include <vector>
#include <iostream>
int check(AVLNode* v, long long lo, long long hi, std::vector<int>& keys) {
    if (!v) return 0;
    assert(lo < v->key && v->key < hi);
    int l = check(v->left,lo,v->key,keys);
    keys.push_back(v->key);
    int r = check(v->right,v->key,hi,keys);
    assert(std::abs(l-r)<=1);
    assert(v->height==1+std::max(l,r));
    return v->height;
}
void release(AVLNode* v) {
    if (!v) return;
    release(v->left); release(v->right); delete v;
}
int main() {
    for (unsigned seed: {1u,42u,2026u}) {
        std::mt19937 rng(seed);
        AVLNode* root=nullptr; std::set<int> reference;
        for (int i=0;i<20000;i++) {
            int key=int(rng()%500)-250;
            if (rng()%2) { root=insert(root,key); reference.insert(key); }
            else { root=erase(root,key); reference.erase(key); }
            std::vector<int> keys;
            check(root,LLONG_MIN,LLONG_MAX,keys);
            assert(keys==std::vector<int>(reference.begin(),reference.end()));
        }
        while (!reference.empty()) {
            int key=*reference.begin(); reference.erase(key);
            root=erase(root,key);
            std::vector<int> keys; check(root,LLONG_MIN,LLONG_MAX,keys);
            assert(keys==std::vector<int>(reference.begin(),reference.end()));
        }
        assert(root==nullptr); release(root);
    }
    std::cout << "PASS: 60000 random operations, complete deletion, AVL and BST invariants\n";
}
