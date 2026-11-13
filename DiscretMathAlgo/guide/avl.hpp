#pragma once
#include <algorithm>

struct AVLNode {
    int key, height = 1;
    AVLNode *left = nullptr, *right = nullptr;
    explicit AVLNode(int key) : key(key) {}
};
int height(AVLNode* v) { return v ? v->height : 0; }
int balance(AVLNode* v) { return height(v->left)-height(v->right); }
void pull(AVLNode* v) {
    v->height = 1 + std::max(height(v->left), height(v->right));
}
AVLNode* rotateRight(AVLNode* y) {
    AVLNode* x = y->left;
    y->left = x->right;
    x->right = y;
    pull(y); pull(x);
    return x;
}
AVLNode* rotateLeft(AVLNode* x) {
    AVLNode* y = x->right;
    x->right = y->left;
    y->left = x;
    pull(x); pull(y);
    return y;
}
AVLNode* rebalance(AVLNode* v) {
    if (!v) return nullptr;
    pull(v);
    if (balance(v) > 1) {
        if (balance(v->left) < 0) v->left = rotateLeft(v->left);
        return rotateRight(v);
    }
    if (balance(v) < -1) {
        if (balance(v->right) > 0) v->right = rotateRight(v->right);
        return rotateLeft(v);
    }
    return v;
}
AVLNode* insert(AVLNode* v, int key) {
    if (!v) return new AVLNode(key);
    if (key < v->key) v->left = insert(v->left, key);
    else if (key > v->key) v->right = insert(v->right, key);
    else return v;
    return rebalance(v);
}
AVLNode* erase(AVLNode* v, int key) {
    if (!v) return nullptr;
    if (key < v->key) v->left = erase(v->left, key);
    else if (key > v->key) v->right = erase(v->right, key);
    else {
        if (!v->left || !v->right) {
            AVLNode* child = v->left ? v->left : v->right;
            delete v;
            return child;
        }
        AVLNode* successor = v->right;
        while (successor->left) successor = successor->left;
        v->key = successor->key;
        v->right = erase(v->right, successor->key);
    }
    return rebalance(v);
}
