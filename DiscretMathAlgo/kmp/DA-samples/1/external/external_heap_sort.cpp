#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

struct HeapItem {
    // Конструктор, чтобы работал emplace_back
    HeapItem(std::int64_t value, std::size_t runIndex) : value(value), runIndex(runIndex) {}

    std::int64_t value;
    std::size_t runIndex;
};
bool operator>(const HeapItem& a, const HeapItem& b) {
    return a.value > b.value;
}
bool heapComparator(const HeapItem& a, const HeapItem& b) {
    return a > b;
}

bool createRuns(const std::string& inputName,
                const std::string& outputName,
                std::size_t blockSize,
                std::vector<std::string>& runNames) {
    std::ifstream input(inputName);
    if (!input.is_open()) {
        return false;
    }

    while (true) {
        std::vector<std::int64_t> block;
        std::int64_t value;

        // В плюсах с помощью `>>` читаем сразу один int из файла
        // потому что переменная value имеет тип int.
        // Также `>>` вернет `false`, если не сможет прочитать.
        while (block.size() < blockSize && input >> value) {
            block.push_back(value);
        }

        // Если ничего не смогли прочитать -- значит файл кончился,
        // сортировать пустой блок не надо.
        if (block.empty()) {
            break;
        }

        std::sort(block.begin(), block.end());

        std::string runName = outputName + ".run."
                            + std::to_string(runNames.size()) + ".tmp";
        std::ofstream run(runName);
        if (!run.is_open()) {
            return false;
        }
        runNames.push_back(runName);

        for (std::size_t i = 0; i < block.size(); ++i) {
            run << block[i] << '\n';
        }

        // Выходной поток файла закроется сам после
        // уничтожения локальной переменной run
    }

    return input.eof();
}

bool mergeRuns(const std::vector<std::string>& runNames,
               const std::string& outputName) {
    // Поток для чтения файла
    std::vector<std::ifstream> runs(runNames.size());
    // В плюсах нет отдельного класса Кучи,
    // но ее можно поддерживать на обычном векторе
    std::vector<HeapItem> heap;

    for (std::size_t i = 0; i < runNames.size(); ++i) {
        runs[i].open(runNames[i]);
        if (!runs[i].is_open()) {
            return false;
        }

        std::int64_t value;
        if (runs[i] >> value) {
            // Почитайте, чем emplace_back отличается от push_back
            heap.emplace_back(value, i);
        }
    }

    // По дефолту куча максимальная.
    // Передав свой компаратор (функцию для сравнения элементов),
    // сделаем ее минимальной.
    std::make_heap(heap.begin(), heap.end(), heapComparator);

    std::ofstream output(outputName);
    if (!output.is_open()) {
        return false;
    }

    while (!heap.empty()) {
        // Перемещаем минимальный элемент в конец вектора
        // и восстанавливаем свойства кучи
        std::pop_heap(heap.begin(), heap.end(), heapComparator);
        // Получаем этот минимальный элемент
        HeapItem minimum = heap.back();
        // Удаляем его
        heap.pop_back();
        output << minimum.value << '\n';

        std::int64_t nextValue;
        if (runs[minimum.runIndex] >> nextValue) {
            heap.emplace_back(nextValue, minimum.runIndex);
            std::push_heap(heap.begin(), heap.end(), heapComparator);
        }
    }

    return true;
}

void removeRuns(const std::vector<std::string>& runNames) {
    for (std::size_t i = 0; i < runNames.size(); ++i) {
        std::remove(runNames[i].c_str());
    }
}

bool externalHeapSort(const std::string& inputName,
                      const std::string& outputName,
                      std::size_t blockSize) {
    std::vector<std::string> runNames;
    if (!createRuns(inputName, outputName, blockSize, runNames)) {
        removeRuns(runNames);
        return false;
    }

    bool merged = mergeRuns(runNames, outputName);
    removeRuns(runNames);
    return merged;
}

// Запуск (в test.txt предварительно кладем числа через пробел или перенос строки):
// g++ external_heap_sort.cpp
// ./a.out test.txt sorted.txt 5
int main(int argc, char* argv[]) {
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0]
                  << " <input file> <output file> <block size>\n";
        return 1;
    }

    std::size_t blockSize = std::stoi(argv[3]);

    return !externalHeapSort(argv[1], argv[2], blockSize);
}
