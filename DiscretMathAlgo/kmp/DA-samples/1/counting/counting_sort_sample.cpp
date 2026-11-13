#include <iostream>
#include <limits>
#include <vector>

struct Object {
    int key;
    std::string some_string_field;
};

void countingSort(std::vector<Object*>& objects) {
    size_t n = objects.size();
    int min_ = std::numeric_limits<int>::max();
    int max_ = std::numeric_limits<int>::min();

    for (int i = 0; i < n; ++i) {
        min_ = std::min(min_, objects[i]->key);
        max_ = std::max(max_, objects[i]->key);
    }

    int64_t range = max_ - min_ + 1;
    std::vector<size_t> counter(range, 0);

    for (size_t i = 0; i < n; ++i) {
        ++counter[objects[i]->key - min_];
    }

    for (size_t i = 1; i < counter.size(); ++i) {
        counter[i] += counter[i - 1];
    }

    std::vector<Object*> sortedObjects(n);
    for (size_t i = n; i > 0; --i) {
        int key = objects[i - 1]->key - min_;

        sortedObjects[counter[key] - 1] = objects[i - 1];
        --counter[key];
    }

    objects = std::move(sortedObjects);
}

int main() {
    int n;
    std::cin >> n;
    
    std::vector<Object> objects;
    for (int i = 0; i < n; ++i) {
        int key;
        std::string some_string_field;

        std::cin >> key >> some_string_field;
        objects.push_back(Object{key, some_string_field});
    }

    std::vector<Object*> objectsPtr(n);
    for (int i = 0; i < n; ++i) {
        objectsPtr[i] = &objects[i];
    }

    countingSort(objectsPtr);

    for (int i = 0; i < n; ++i) {
        std::cout << objectsPtr[i]->key << ": " << objectsPtr[i]->some_string_field << "\n";
    }

    return 0;
}
