from pathlib import Path
import re, json, html, base64
import markdown
from markdown.extensions.toc import slugify_unicode
root=Path(__file__).resolve().parent; md=root/'OOP_CPP20_Полная_подготовка_к_контрольной.md'
s=md.read_text()
initialization=r'''## 1.6. Инициализация — крайне важная тема

Инициализация задаёт начальное состояние **при создании** объекта. Присваивание меняет уже существующий объект. Сначала найдите в строке объявление нового объекта: знак `=` сам по себе не означает вызов оператора присваивания.

```cpp
int a = 5; // создаём a: инициализация
int b{a};  // создаём b: инициализация
b = 9;     // b уже существует: присваивание
```

### 1.6.1. Формы записи: что именно они означают

| Запись | Название | Для локального int | Особенность для классов |
|---|---|---|---|
| `T x;` | Default-initialization | Значение не задано | Вызывается подходящий конструктор без аргументов |
| `T x = value;` | Copy-initialization | Начальное значение из value | Не использует explicit-конструктор для такого преобразования |
| `T x(value);` | Direct-initialization | Начальное значение из value | Может использовать explicit-конструктор |
| `T x{value};` | Direct-list-initialization | Запрет narrowing | Агрегатная инициализация либо выбор конструктора |
| `T x = {value};` | Copy-list-initialization | Запрет narrowing | Ошибка, если выбран explicit-конструктор |
| `int x{};` | Пустая list-initialization, затем value-initialization | Ноль | Для произвольного T поведение зависит от типа и конструкторов |

Название copy-initialization **не гарантирует фактическое копирование**. Например, `std::string s = "hi";` конструирует строку из C-строки, а `T x = T{};` при подходящих условиях C++17+ создаёт объект сразу на месте без copy/move.

### 1.6.2. Когда получается ноль, а когда значение не задано

```cpp
int global;                 // статическое хранение: 0
int main() {
    int a;                  // автоматический int: неопределённое значение
    int b{};                // 0
    static int c;           // статическое хранение: 0
    int* p = new int;       // выделенный int: неопределённое значение
    int* q = new int{};     // 0
    // Не читаем a и *p до присваивания!
    delete p;
    delete q;
}
```

Для этих `int` чтение неопределённого значения в C++20 приводит к UB. Само объявление `int a;` и последующее присваивание `a = 10;` допустимы. Не следует объяснять это как «всегда случайное число»: определённого результата стандарт не обещает.

**Правило для запоминания:** локальный скаляр без инициализатора не получает автоматически ноль. Объекты со статическим хранением проходят статическую инициализацию; в примере `global` и `c` нулевые. Классы нужно анализировать отдельно: `std::string name;` создаёт корректную пустую строку через конструктор.

### 1.6.3. Фигурные скобки и narrowing

```cpp
int a = 3.14;             // 3: дробная часть отбрасывается
int b(3.14);              // 3
// int c{3.14};           // ошибка компиляции
// int d = {3.14};        // тоже ошибка
unsigned char e{42};      // допустимо: константа представима
int n = 42;
// unsigned char f{n};    // ошибка: n не константное выражение,
                         // а int не весь представим в unsigned char
constexpr int k = 42;
unsigned char g{k};       // допустимо
```

Сужение проверяется по правилам языка, а не только по текущему значению переменной. Поэтому `n` и `k` дают разный результат. Приведение `static_cast` может явно разрешить преобразование, но само по себе не проверяет диапазон.

### 1.6.4. Почему () и {} не взаимозаменяемы

```cpp
#include <vector>
std::vector<int> a(3, 7); // три элемента: 7, 7, 7
std::vector<int> b{3, 7}; // два элемента: 3, 7
std::vector<int> c(3);    // три нуля
std::vector<int> d{3};    // один элемент со значением 3
```

Для такого класса непустой список в `{}` сначала рассматривает конструкторы с `std::initializer_list`. Это причина различий. В `a(3, 7)` выбран конструктор «количество, значение», в `b{3, 7}` — список элементов. Скобки выбирают не стиль оформления, а семантику.

Не смешивайте **список инициализации членов конструктора** (`: x_(x)`) и **тип `std::initializer_list`**: это разные понятия.

### 1.6.5. Класс и explicit: какой конструктор доступен

```cpp
struct Count {
    explicit Count(int) {}
};
void use(Count) {}

int main() {
    Count a(5);           // direct: допустимо
    Count b{5};           // direct-list: допустимо
    // Count c = 5;       // ошибка: неявное преобразование запрещено
    // Count d = {5};     // ошибка: выбран explicit-конструктор
    // use(5);            // ошибка
    use(Count{5});        // явно создаём Count
}
```

`explicit` защищает от непреднамеренного превращения числа в объект. Подробнее конструкторы и специальные методы изучаются в лекции 6; здесь важно различать формы инициализации.

### 1.6.6. Пустые скобки и most vexing parse

```cpp
#include <string>
std::string a;       // объект: пустая строка
std::string b{};     // объект: пустая строка
std::string c();     // объявление функции c, возвращающей string!
```

`T x();` в таком объявлении не создаёт объект. Чтобы создать объект без аргументов и избежать этой неоднозначности, используйте `T x{};`.

### 1.6.7. Массивы и агрегаты

```cpp
int a[4]{1, 2};    // 1, 2, 0, 0
int b[4]{};        // четыре нуля

struct Point {
    int x;
    int y = 9;
};
Point p{2, 3};     // x=2, y=3
Point q{2};        // x=2, y=9: инициализатор поля
Point r{};         // x=0, y=9
Point t;           // x не задан, y=9; не читайте t.x
Point u{.x = 4};   // C++20: x=4, y=9
```

`Point` здесь агрегат: у него нет пользовательски объявленных конструкторов и других признаков, исключающих агрегатность. `struct` сам по себе не гарантирует, что тип является агрегатом. Для designated initializers C++20 имена полей должны следовать порядку их объявления; нельзя произвольно переставить `.y` перед `.x`.

### 1.6.8. auto, const и ссылки

```cpp
#include <initializer_list>
const int x = 10;
auto a = x;            // int: верхний const убран
auto& b = x;           // const int&: ссылка на x
const auto& c = x;     // const int&
auto d{1};             // int
auto e = {1};          // std::initializer_list<int>
// auto f{1, 2};       // ошибка вывода типа
int n = 3;
int& ref = n;          // ref обозначает n
// int& bad = 3;       // неконстантная lvalue-ссылка не связывается с 3
const int& ok = 3;     // допустимо, время жизни временного продлено
```

`auto` — вывод типа, а не динамическая типизация. `auto a = x` создаёт независимую копию значения; `auto& b = x` связывает ссылку. Для данного `x`: `decltype(x)` — `const int`, `decltype((x))` — `const int&`.

### 1.6.9. const и constexpr не равны

```cpp
int read();
const int a = read();      // неизменяемое значение, получаемое при выполнении
constexpr int b = 5 * 5;   // инициализатор обязан быть константным выражением
// constexpr int c = read(); // ошибка: read не constexpr
```

`const` ограничивает изменение объекта. `constexpr` у такой переменной требует константного выражения в инициализаторе и также делает объект константным. Для функции `constexpr` означает возможность вычисления на этапе компиляции при подходящих аргументах и контексте, а не обязательное compile-time исполнение каждого вызова.

### 1.6.10. Осторожно: {} не обнуляет любой класс

```cpp
struct A { int x; };             // агрегат
struct B { int x; B() {} };      // пользовательский конструктор не задаёт x
struct C { int x{}; C() {} };    // поле имеет свой инициализатор

A a{}; // x=0
B b{}; // x не задан! Тело B() не инициализирует int
C c{}; // x=0
```

Запоминать «`{}` всегда всё обнуляет» неверно. Нужно определить, агрегат ли это, какой конструктор вызывается и как инициализируются его поля. Для полей скалярных типов полезно задавать default member initializer: `int x{};`.

### 1.6.11. Инициализация полей и присваивание в теле

```cpp
#include <string>
#include <utility>
class Person {
    const int id_;
    std::string name_;
public:
    Person(int id, std::string name)
        : id_(id), name_(std::move(name)) {} // поля создаются сразу
};
```

До входа в тело конструктора базы и поля уже инициализированы. `const`-поле и ссылочное поле нужно инициализировать, им нельзя «назначить начальное значение потом» обычным присваиванием. Порядок полей задаётся их объявлением в классе. Подробный порядок, включая базы, — в лекциях 6 и 8.

### 1.6.12. Проверь себя перед переходом дальше

Сначала определите, создаётся ли объект или объявляется функция. Затем назовите вид инициализации, проверьте narrowing и `explicit`, выберите конструктор и разберите состояние полей.

| Вопрос | Ответ |
|---|---|
| `int x{};` | Ноль |
| Локальный `int x;` и сразу `std::cout << x;` | UB в C++20 |
| `int x = 3.9;` | Значение 3 |
| `int x{3.9};` | Ошибка компиляции |
| `std::vector<int> v{4, 2};` | Два элемента: 4 и 2 |
| `std::vector<int> v(4, 2);` | Четыре элемента со значением 2 |
| `T object();` | Объявление функции |
| `T b = a;` | Инициализация нового b, не присваивание |

Правила сверены с проектом стандарта C++20 N4861: [инициализация](https://timsong-cpp.github.io/cppwp/n4861/dcl.init), [list-initialization](https://timsong-cpp.github.io/cppwp/n4861/dcl.init.list), [инициализация баз и полей](https://timsong-cpp.github.io/cppwp/n4861/class.base.init).'''
s=re.sub(r'## 1\.6\..*?(?=## 1\.7\.)',initialization+'\n\n',s,flags=re.S)
# Дополнительные разборы помогают связать правила с практикой каждой лекции.
extras={
2:('2.11. Разбор: значение выражения и побочный эффект',r'''В строке `int old = x++;` есть два результата: в `old` попадает старое значение, а `x` увеличивается. Не определяйте порядок вычисления только по приоритету операторов: приоритет задаёт группировку выражения.

```cpp
#include <iostream>
int main() {
    int x = 3;
    int old = x++;
    int now = ++x;
    std::cout << old << ' ' << now << ' ' << x; // 3 5 5
}
```

У встроенных `&&` и `||` правый операнд вычисляется только при необходимости: `p != nullptr && *p > 0` не разыменует нулевой указатель. У перегруженных операторов `&&` и `||` такой короткой схемы нет. Для контрольной безопаснее разбивать изменения одного объекта на отдельные строки и затем считать результат.'''),
3:('3.11. Разбор: объект, ссылка, указатель и время жизни',r'''Ссылка не владеет объектом и не продлевает жизнь произвольного объекта автоматически. Её корректность зависит от того, существует ли объект, к которому она привязана.

```cpp
#include <iostream>
int main() {
    int x = 7;
    int copy = x;
    int& alias = x;
    int* ptr = &x;
    alias = 9;
    std::cout << x << ' ' << copy << ' ' << *ptr; // 9 7 9
}
```

`copy` — отдельный объект, `alias` — другое имя `x`, `ptr` — отдельный объект-указатель, который хранит адрес `x`. `delete ptr` здесь недопустим: `x` не создан через `new`. При разборе всегда отдельно отвечайте: кто владеет ресурсом, кто лишь обращается к нему и когда заканчивается его время жизни.'''),
4:('4.11. Разбор: как выбирать способ передачи параметра',r'''Передача по значению создаёт отдельный параметр. Передача по ссылке позволяет обратиться к исходному объекту; `const T&` запрещает его обычное изменение через эту ссылку.

```cpp
#include <iostream>
#include <string>
void rename(std::string& s) { s = "new"; }
std::size_t length(const std::string& s) { return s.size(); }
int main() {
    std::string name = "old";
    rename(name);
    std::cout << name << ' ' << length(name); // new 3
}
```

Для небольшого `int` обычно подходит значение; для чтения большой строки — `const std::string&`; для изменения аргумента — `std::string&`. Само наличие `const T&` не делает объект владельцем ресурса и не разрешает сохранить ссылку на временный аргумент для использования после окончания его времени жизни.'''),
5:('5.11. Разбор: инвариант важнее набора get/set',r'''Инвариант — условие, которое должен сохранять объект в предусмотренных контрактом состояниях. Например, прямоугольник не должен иметь неположительные размеры. Закрытые поля сами по себе недостаточны: публичные методы тоже обязаны поддерживать условие.

```cpp
#include <stdexcept>
class Rectangle {
    double width_;
    double height_;
public:
    Rectangle(double w, double h) : width_(w), height_(h) {
        if (!(w > 0) || !(h > 0)) throw std::invalid_argument("size");
    }
    double area() const { return width_ * height_; }
    void resize(double w, double h) {
        if (!(w > 0) || !(h > 0)) throw std::invalid_argument("size");
        width_ = w;
        height_ = h;
    }
};
```

Проверка перед присваиванием сохраняет прежнее состояние при неверных размерах. Запись `!(w > 0)` также отклоняет NaN. Если нужен контракт только для конечных размеров, дополнительно проверяют `std::isfinite` из `<cmath>`.''')}
for n,(title,body) in extras.items():
 marker='# Лекция '+str(n+1)+'.'
 if '## '+title not in s:
  s=s.replace(marker,'## '+title+'\n\n'+body+'\n\n---\n\n'+marker,1)
md.write_text(s)

# Карточки: вопросы для активного воспроизведения, не конспект с открытым ответом.
cards=[]
def card(l,q,a): cards.append(dict(id='c'+str(len(cards)+1),lecture=l,q=q,a=a))
card(1,'Чем int a = 5 отличается от a = 5?','В первом случае создаётся объект и выполняется инициализация; во втором изменяется уже существующий объект.')
card(1,'Что произойдёт при чтении локального int x; до присваивания?','Для такого int в C++20 чтение неопределённого значения приводит к UB. Само объявление допустимо.')
card(1,'Чем отличаются int x{} и int x; внутри функции?','Первый получает 0. У второго, если он автоматический, значение не задано.')
card(1,'Почему int x{3.14} не компилируется?','List-initialization запрещает сужающее преобразование double в int.')
card(1,'Что создают vector<int> a(3, 7) и b{3, 7}?','a содержит три семёрки; b содержит два элемента 3 и 7. У b выбран initializer_list-конструктор.')
card(1,'T object(); создаёт объект?','Нет, это объявление функции object, возвращающей T. Для объекта без аргументов используйте T object{};.')
card(1,'Зачем нужен explicit у конструктора?','Он ограничивает неявные преобразования. T x{5} может использовать explicit-конструктор, T x = 5 — нет.')
card(1,'У любого класса T x{} все поля нулевые?','Нет. Например, пользовательский конструктор T() {} может оставить int-поле без инициализации.')
card(1,'Каковы типы auto x{1} и auto y = {1}?','x имеет тип int; y — std::initializer_list<int>.')
card(1,'Почему const не означает compile-time?','const int x = read(); допустим: значение может определяться при выполнении. constexpr-переменная требует константного выражения.')
card(1,'Point { int x; int y=9; }; Point p{}; — значения?','x равен 0, y равен 9: для y действует инициализатор поля, для x — инициализация из пустого списка.')
card(1,'Чем ошибка компиляции отличается от ошибки линковки?','Компилятор проверяет единицу трансляции и типы; компоновщик связывает определения из объектных файлов и библиотек.')
for l,items in {
2:[('Что дают 7 / 2 и 7 / 2.0?','3 и 3.5: в первом выражении целочисленное деление.'),('Чем отличается signed overflow от unsigned overflow?','Переполнение знакового целого — UB, беззнаковая арифметика выполняется по модулю 2^N.'),('Что гарантирует встроенный &&?','Левый операнд вычисляется первым; правый — только если левый истинный.'),('Приоритет задаёт порядок вычисления операндов?','Нет. Он определяет группировку; порядок вычисления нужно смотреть по правилам конкретного оператора.')],
3:[('Чем const T* отличается от T* const?','const T* запрещает менять T через этот указатель. T* const запрещает перенаправлять сам указатель.'),('Что такое dangling pointer?','Указатель на объект, время жизни которого закончилось; обращаться через него к такому объекту нельзя.'),('Что делает std::move?','Преобразует выражение к xvalue. Само по себе не переносит ресурс.'),('Именованная переменная T&& — lvalue или rvalue?','Выражение с её именем — lvalue. Для передачи как xvalue используют std::move.')],
4:[('Когда нужен T&, а когда const T&?','T& — для изменения исходного объекта, const T& — для чтения без обязательного копирования.'),('Можно ли перегрузить функцию только по возвращаемому типу?','Нет, различия только в возвращаемом типе недостаточно.'),('Гарантировано ли NRVO в C++20?','Нет. Для подходящего prvalue есть гарантированная copy elision, но NRVO именованной локальной переменной необязательно.'),('Почему return std::move(local) часто не нужен?','Он может помешать NRVO; возврат подходящего локального объекта и так допускает перемещение.')],
5:[('Чем class отличается от struct?','Доступ к членам и наследование по умолчанию: private у class, public у struct.'),('Что такое инвариант класса?','Условие корректного состояния объекта, которое поддерживают конструкторы и публичные операции.'),('Что означает const после метода?','Метод работает с const-квалифицированным объектом: нельзя менять обычные поля; mutable — исключение.'),('friend — это метод класса?','Нет. Дружественная свободная функция получает доступ к закрытым членам, но не становится методом.')],
6:[('В каком порядке инициализируются поля?','В порядке объявления в классе, независимо от порядка списка инициализации.'),('Что означает Rule of Zero?','Ресурсы принадлежат RAII-полям; свои деструктор и copy/move обычно не нужны.'),('Вызывается ли деструктор объекта, если его конструктор бросил исключение?','Нет. Но уже полностью созданные поля и базы уничтожаются.'),('Почему std::move(constObj) часто копирует?','Результат сохраняет const и обычно не подходит к T&&, но подходит к const T&.'),('Что происходит с генерацией move при пользовательском деструкторе?','Неявные move-операции не объявляются. Даже объявление деструктора с = default влияет на это.')],
7:[('Почему operator+= обычно возвращает T&?','Оператор меняет текущий объект и возвращает *this, позволяя цепочки.'),('Почему operator+ возвращает значение?','Он создаёт результат, не изменяя исходные операнды; ссылка на локальный результат была бы висячей.'),('Зачем int в постфиксном operator++(int)?','Это фиктивный параметр для отличия постфиксной формы от префиксной.'),('Почему operator<< возвращает ostream&?','Чтобы продолжать цепочку вывода в тот же поток.')],
8:[('Чем сокрытие отличается от переопределения?','Сокрытие влияет на поиск имени; переопределение заменяет виртуальную реализацию с подходящей сигнатурой.'),('Что такое срезка?','При создании Base по значению из Derived копируется базовая часть; нового объекта Derived не возникает.'),('Кто инициализирует виртуальную базу?','Наиболее производный класс.'),('Зачем виртуальный деструктор базы?','Для обычного корректного удаления производного объекта через указатель на базу.'),('Откуда берётся default-аргумент виртуального вызова?','Из объявления, выбранного по статическому типу. Тело виртуального метода выбирается по динамическому типу.')]
}.items():
 for q,a in items: card(l,q,a)
quizzes=[]
def quiz(l,q,code,options,correct,why): quizzes.append(dict(id='q'+str(len(quizzes)+1),lecture=l,q=q,code=code,options=options,correct=correct,why=why))
quiz(1,'Какое значение у x?', 'int x{};', ['0','Неопределённое значение','Ошибка компиляции'],0,'Пустой список для int приводит к value-initialization и нулевому значению.')
quiz(1,'Что будет при выполнении в C++20?', 'int main() { int x; std::cout << x; }',['Всегда 0','UB','Ошибка компиляции'],1,'Неинициализированный автоматический int нельзя читать. Конкретный вывод не обещан.')
quiz(1,'Компилируется ли эта строка?', 'int x{3.14};',['Да, x = 3','Да, x = 4','Нет'],2,'List-initialization запрещает narrowing double → int.')
quiz(1,'Какие элементы в v?', 'std::vector<int> v{3, 7};',['7, 7, 7','3, 7','0, 0, 0'],1,'Непустой список выбирает здесь initializer_list-конструктор.')
quiz(1,'Какие элементы в v?', 'std::vector<int> v(3, 7);',['3, 7','7, 7, 7','3, 3, 3, 3, 3, 3, 3'],1,'Скобки () выбирают конструктор «количество, значение».')
quiz(1,'Что объявлено?', 'std::string name();',['Пустая строка','Функция, возвращающая string','Указатель'],1,'Это объявление функции. Для объекта используйте std::string name{};.')
quiz(1,'Какой тип у x?', 'auto x = {1};',['int','std::initializer_list<int>','int&'],1,'Copy-list-initialization с auto и таким списком выводит initializer_list<int>.')
quiz(1,'Задано ли нулевое значение b.x?', 'struct B { int x; B() {} };\nB b{};',['Да, всегда','Нет, поле не инициализировано','Код не компилируется'],1,'Пользовательский B() не инициализирует x. Фигурные скобки не обнуляют любой класс.')
quiz(1,'Компилируется ли создание a?', 'struct T { explicit T(int) {} };\nT a = {3};',['Да','Нет'],1,'При copy-list-initialization выбор explicit-конструктора делает программу некорректной.')
quiz(1,'Чему равны поля p?', 'struct P { int x; int y = 9; };\nP p{};',['0 и 0','Не заданы','0 и 9'],2,'x инициализируется из пустого списка, y получает свой default member initializer.')
quiz(2,'Что выведет код?', 'int x=4; int y=x++; int z=++x;\nstd::cout << x << y << z;',['645','646','545'],1,'y получает 4, x становится 5; затем ++x даёт 6, z=6. Вывод без пробелов: 646.')
quiz(2,'Чему равно выражение?', '7 / 2',['3','3.5','4'],0,'Оба операнда целые, дробная часть отбрасывается.')
quiz(3,'Какая строка запрещена?', 'int x=1, y=2;\nconst int* p=&x;',['p = &y;','*p = 3;','p = nullptr;'],1,'p можно перенаправлять, менять объект через const int* нельзя.')
quiz(3,'Что напечатает перегрузка?', 'void f(int&) { std::cout << "L"; }\nvoid f(int&&) { std::cout << "R"; }\nint&& r = 1;\nf(r);',['L','R','Ошибка компиляции'],0,'Именованная r в выражении — lvalue, даже если её объявленный тип int&&.')
quiz(4,'Какую перегрузку выбирает f(1)?', 'void f(int);\nvoid f(double);',['f(int)','f(double)','Неоднозначно'],0,'Точное совпадение int лучше преобразования в double.')
quiz(4,'Что изменится?', 'void f(int x) { x=9; }\nint a=1; f(a);',['a станет 9','a останется 1'],1,'Параметр передан по значению: изменяется копия.')
quiz(5,'Что доступно снаружи?', 'class C { int x{}; public: int get() const { return x; } };\nC c;',['c.x','c.get()','Оба'],1,'Поля class по умолчанию private; get явно public.')
quiz(5,'Можно ли вызвать метод?', 'struct C { int get() { return 1; } };\nconst C c{};\nc.get();',['Да','Нет'],1,'get не имеет const-квалификатора и не вызывается для const-объекта.')
quiz(6,'Каким будет вывод?', 'struct A { ~A(){std::cout<<"A";} };\nstruct B { ~B(){std::cout<<"B";} };\nint main(){ A a; B b; }',['AB','BA','Не определён'],1,'Локальные объекты уничтожаются в обратном порядке конструирования.')
quiz(6,'Какой порядок инициализации полей?', 'struct C { int x; int y; C(): y(2), x(1) {} };',['y, затем x','x, затем y'],1,'Порядок задаётся объявлением полей, а не списком после двоеточия.')
quiz(6,'Что напечатает код?', 'struct T {\n T()=default;\n T(const T&) { std::cout<<"C"; }\n T(T&&) { std::cout<<"M"; }\n};\nconst T a; T b=std::move(a);',['C','M','CM'],0,'std::move сохраняет const, поэтому T&& не подходит, а const T& подходит.')
quiz(7,'Что возвращает канонический префиксный ++?', 'T& operator++();',['Старую копию','Ссылку на изменённый объект','void'],1,'Префиксная форма обычно меняет *this и возвращает *this по ссылке.')
quiz(7,'Какая сигнатура обычно подходит для вывода?', 'std::cout << object << "!";',['void operator<<(T, ostream);','std::ostream& operator<<(std::ostream&, const T&);'],1,'Поток слева, объект справа; возврат ссылки на поток поддерживает цепочку.')
quiz(8,'Что выведет код?', 'struct B { virtual int f() const {return 1;} };\nstruct D:B { int f() const override {return 2;} };\nD d; B b=d; std::cout<<b.f();',['1','2','UB'],0,'b — отдельный объект B, произошла срезка. Удаления через базовый указатель здесь нет.')
quiz(8,'Что выведет код?', 'struct B { virtual int f() const {return 1;} };\nstruct D:B { int f() const override {return 2;} };\nD d; const B& b=d; std::cout<<b.f();',['1','2','Ошибка'],1,'Ссылка сохраняет обращение к D; виртуальный вызов выбирает D::f.')
quiz(8,'Что произойдёт с вызовом d.f(2.5)?', 'struct B { void f(double); };\nstruct D:B { void f(int); };\nD d; d.f(2.5);',['Выбран D::f(int)','Выбран B::f(double)','Всегда ошибка'],0,'Имя f в D скрывает перегрузки базы. using B::f возвращает их в набор поиска.')
# Рендерим весь конспект в один переносимый файл.
rendered=markdown.markdown(s,extensions=['fenced_code','tables','toc','sane_lists'],extension_configs={'toc':{'slugify':slugify_unicode}})
def inline_image(m):
 path=root/m.group(1)
 return 'src="data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode()+'"'
rendered=re.sub(r'src="(assets/[^\"]+\.svg)"',inline_image,rendered)
chunks=re.split(r'(?=<h1\b)',rendered)
sections=[]; nav=[]
for i,ch in enumerate(chunks):
 if not ch.strip(): continue
 title_match=re.search(r'<h1[^>]*>(.*?)</h1>',ch,re.S)
 if not title_match: continue
 title=re.sub('<[^>]+>','',title_match.group(1))
 lm=re.search(r'Лекция (\d)',title); l=int(lm.group(1)) if lm else 0
 if i<=1 and not lm: continue
 ident='lecture-'+str(l) if l else 'extra-'+str(i)
 # Секции второго уровня раскрываются независимо, задания не показывают ответы до открытия.
 parts=re.split(r'(?=<h2\b)',ch)
 out=parts[0]
 for part in parts[1:]:
  hm=re.match(r'<h2([^>]*)>(.*?)</h2>(.*)',part,re.S)
  if hm:
   attrs,heading,body=hm.groups(); is_init='1.6.' in heading
   out+=f'<details class="topic" {attrs}'+(' open' if is_init else '')+f'><summary><span>{heading}</span><b aria-hidden="true">+</b></summary><div class="topic-body">{body}</div></details>'
  else: out+=part
 if l: nav.append(f'<a href="#{ident}" data-lesson="{l}"><span>0{l}</span>{html.escape(title.split(". ",1)[-1])}</a>')
 sections.append(f'<section class="lesson" id="{ident}" data-lecture="{l}">{out}</section>')
page=r'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>C++ / Вспомнить и написать</title>
<style>
:root{--paper:#f7f7f4;--ink:#202220;--muted:#71756d;--line:#dcdfd6;--accent:#dc562f;--soft:#f1e6dc;--green:#416345}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:100px}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}button,input,select{font:inherit}button,a,input,select{touch-action:manipulation}a{color:inherit;text-decoration-color:#a9afa0;text-underline-offset:4px}button{cursor:pointer}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:4px}header{position:sticky;top:0;background:#f7f7f4ed;backdrop-filter:blur(16px);border-bottom:1px solid var(--line);z-index:10}.bar{max-width:1400px;margin:auto;padding:15px 32px;display:flex;align-items:center;gap:26px}.logo{font-size:24px;font-weight:850;text-decoration:none;letter-spacing:-1px}.logo em{font-style:normal;color:var(--accent)}.topnav{display:flex;gap:8px;margin-left:auto}.topnav button,.pill{border:1px solid var(--line);border-radius:30px;background:transparent;padding:8px 18px}.topnav button.active{background:var(--ink);color:white;border-color:var(--ink)}.shell{max-width:1340px;margin:0 auto;padding:0 32px}.hero{padding:70px 0 56px;display:grid;grid-template-columns:1.1fr 1fr;gap:64px;align-items:center}.eyebrow{font:12px ui-monospace,monospace;letter-spacing:2px;color:var(--accent);text-transform:uppercase}h1,h2,h3,p{margin-top:0}.hero h1{font-size:clamp(42px,5.5vw,74px);line-height:1.04;letter-spacing:-3px;margin:18px 0 24px}.hero h1 em{font-style:normal;color:var(--accent)}.hero p{max-width:540px;color:var(--muted);font-size:18px}.primary{background:var(--accent);color:white;border:0;padding:13px 22px;border-radius:8px}.secondary{background:white;border:1px solid var(--line);padding:11px 19px;border-radius:8px}.hero-actions{display:flex;gap:10px;flex-wrap:wrap}.editor{background:#202720;color:#eef1e8;border-radius:14px;overflow:hidden;box-shadow:0 25px 50px #20272018;transform:rotate(1deg)}.editor-bar{padding:12px 20px;border-bottom:1px solid #ffffff20;display:flex;gap:8px;font:12px ui-monospace,monospace;color:#b3bdad}.dot{width:8px;height:8px;border-radius:50%;background:#7d8e73;align-self:center}.editor pre{background:transparent;padding:26px;margin:0;font-size:14px;line-height:1.9;color:#edf0e8}.editor footer{padding:14px 22px;border-top:1px solid #ffffff20;font-size:13px;color:#c8d0c1}.orange{color:#f2a47f}.stats{display:grid;grid-template-columns:repeat(3,1fr);border-block:1px solid var(--line);margin-bottom:42px}.stat{padding:18px 22px;border-right:1px solid var(--line)}.stat:last-child{border:0}.stat strong{font-size:26px;letter-spacing:-1px}.stat span{font-size:13px;color:var(--muted);margin-left:12px}.layout{display:grid;grid-template-columns:245px minmax(0,1fr);gap:55px;align-items:start}.sidebar{position:sticky;top:94px;max-height:calc(100vh - 110px);overflow:auto;padding-bottom:24px}.side-title{font:11px ui-monospace,monospace;color:var(--muted);letter-spacing:2px;margin-bottom:16px}.sidebar nav a{display:flex;gap:12px;text-decoration:none;font-size:13px;line-height:1.4;padding:12px 9px;border-radius:7px}.sidebar a:hover,.sidebar a.current{background:#e9ece3}.sidebar a span{font:12px ui-monospace,monospace;color:var(--accent);padding-top:2px}.meter{margin:24px 0 8px;height:5px;border-radius:5px;background:var(--line);overflow:hidden}.meter i{display:block;height:100%;background:var(--green)}.small{font-size:12px;color:var(--muted)}.toolbar{display:flex;gap:10px;align-items:center;margin-bottom:24px;flex-wrap:wrap}.toolbar input{flex:1;min-width:180px;background:white;border:1px solid var(--line);border-radius:8px;padding:10px 14px}.toolbar select{max-width:100%;border:1px solid var(--line);border-radius:8px;padding:10px;background:white}.toolbar button{border:0;color:var(--muted);background:transparent;font-size:13px}.lesson{margin-bottom:50px;scroll-margin-top:100px}.lesson>h1{font-size:30px;line-height:1.2;letter-spacing:-1px;margin-bottom:24px}.topic{background:white;border:1px solid var(--line);border-radius:10px;margin-bottom:12px;scroll-margin-top:100px}.topic>summary{list-style:none;cursor:pointer;padding:20px 22px;display:flex;justify-content:space-between;align-items:center;gap:16px;font-size:17px;font-weight:650;line-height:1.4}.topic>summary::-webkit-details-marker{display:none}.topic>summary b{font-size:22px;font-weight:400;color:var(--muted)}.topic[open]>summary b{transform:rotate(45deg)}.topic[open]>summary{border-bottom:1px solid var(--line)}.topic-body{padding:24px;overflow-wrap:anywhere}.topic-body h3{font-size:20px;margin:30px 0 12px}.topic-body h3:first-child{margin-top:0}.topic-body p{margin-bottom:16px}.topic-body img{max-width:100%;height:auto;border-radius:8px}pre{background:#202720;color:#edf0e8;padding:20px;border-radius:9px;overflow:auto;font:13px/1.8 ui-monospace,SFMono-Regular,Consolas,monospace;tab-size:4}code{font:0.87em ui-monospace,SFMono-Regular,Consolas,monospace}p code,li code,td code{background:#eff0e9;padding:2px 5px;border-radius:4px}pre code{font:inherit}table{border-collapse:collapse;display:block;max-width:100%;overflow:auto;font-size:14px;margin:18px 0 24px}th,td{text-align:left;padding:12px;border:1px solid var(--line);vertical-align:top;min-width:110px}th{background:#f1f3eb}blockquote{margin:20px 0;border-left:3px solid var(--accent);padding-left:18px;color:var(--muted)}hr{border:0;border-top:1px solid var(--line);margin:28px 0}.study-panel{min-height:480px;background:white;border:1px solid var(--line);border-radius:16px;padding:32px;margin-bottom:32px}.study-panel h2{font-size:30px;line-height:1.25;letter-spacing:-1px}.study-panel .label{font:12px ui-monospace,monospace;color:var(--accent);margin-bottom:24px}.study-panel .answer{border-top:1px solid var(--line);padding-top:24px;margin-top:28px}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:26px}.choice{display:block;width:100%;text-align:left;margin:10px 0;border:1px solid var(--line);border-radius:8px;padding:14px 18px;background:#fafbf7}.choice:disabled{cursor:default;color:inherit;opacity:1}.choice.good{border-color:#60805d;background:#eef5e9}.choice.bad{border-color:#bb603c;background:#fff0e9}.feedback{background:#f0f3ea;padding:18px;border-radius:8px;margin-top:20px}.counter{color:var(--muted);margin-bottom:20px;font-size:13px}.empty{padding:40px;border:1px dashed var(--line);border-radius:10px;text-align:center}.page-footer{border-top:1px solid var(--line);padding:30px 0;margin-top:50px;color:var(--muted);font-size:12px}.status{min-height:22px;color:var(--muted);font-size:12px}.mode-desc{color:var(--muted);margin-bottom:20px}[hidden]{display:none!important}.end-links{margin:20px 0;font-size:13px}.progress-line{display:flex;justify-content:space-between;gap:8px}.print-title{display:none}@media(max-width:950px){.hero{gap:30px}.layout{grid-template-columns:200px minmax(0,1fr);gap:24px}.bar,.shell{padding-inline:20px}.hero h1{letter-spacing:-2px}}@media(max-width:700px){.bar{gap:12px;flex-wrap:wrap;padding:12px 16px}.logo{font-size:20px}.topnav{gap:4px}.topnav button{padding:6px 10px;font-size:12px}.shell{padding:0 16px}.hero{grid-template-columns:1fr;padding:36px 0;gap:28px}.hero h1{font-size:48px}.editor{transform:none}.layout{display:block}.sidebar{position:static;max-height:none}.sidebar nav{display:flex;overflow:auto;gap:6px;padding-bottom:12px}.sidebar nav a{flex:0 0 190px;background:#edf0e7}.side-title,.sidebar .meter,.sidebar .progress-line{display:none}.stats{margin-bottom:20px}.stat{padding:12px 8px}.stat strong{font-size:21px}.stat span{display:block;margin:0;font-size:11px}.topic>summary{padding:16px;font-size:15px}.topic-body{padding:16px}.study-panel{padding:22px}.study-panel h2{font-size:25px}.hero p{font-size:16px}.toolbar{gap:8px}.toolbar select{flex:1;min-width:180px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{header,.hero,.stats,.sidebar,.toolbar,.page-footer,#training{display:none!important}.layout{display:block}.shell{max-width:none;padding:0}details{break-inside:avoid}details:not([open])>.topic-body{display:block}summary b{display:none}.topic{border:0}pre{white-space:pre-wrap;background:#eee;color:#111}.lesson{display:block!important}#reading{display:block!important}}
</style></head><body id="top">
<header><div class="bar"><a class="logo" href="#top">C<em>++</em> / study</a><span class="small">ООП · C++20</span><nav class="topnav" aria-label="Режим обучения"><button data-mode="read" class="active" aria-pressed="true">Конспект</button><button data-mode="cards" aria-pressed="false">Карточки</button><button data-mode="quiz" aria-pressed="false">Проверка</button></nav></div></header>
<div class="shell"><section class="hero"><div><div class="eyebrow">Контрольная / лекции 01–08</div><h1>Понять.<br>Вспомнить.<br><em>Написать.</em></h1><p>ООП и особенности C++ — по порядку, от первого объявления до наследования. Сначала ответь сам, затем открой объяснение.</p><div class="hero-actions"><button class="primary" id="start-init">Разобрать инициализацию</button><button class="secondary" data-mode="quiz">Проверить себя</button></div></div><div class="editor"><div class="editor-bar"><i class="dot"></i><i class="dot"></i><i class="dot"></i><span style="margin-left:auto">initialization.cpp</span></div><pre><span style="color:#9eaf92">// Похожая запись. Разный результат.</span>
std::vector&lt;int&gt; a<span class="orange">(3, 7)</span>;
std::vector&lt;int&gt; b<span class="orange">{3, 7}</span>;

<span style="color:#9eaf92">// Сколько элементов в каждом?</span>
<span style="color:#9eaf92">// Объясни, какой конструктор выбран.</span></pre><footer>Не угадывай вывод. Найди правило, которое его определяет.</footer></div></section>
<div class="stats"><div class="stat"><strong>08</strong><span>лекций по порядку</span></div><div class="stat"><strong>__CARDS__</strong><span>карточек для повторения</span></div><div class="stat"><strong>__QUIZZES__</strong><span>вопросов по коду</span></div></div>
<div class="layout"><aside class="sidebar"><div class="side-title">МАРШРУТ ПОДГОТОВКИ</div><nav aria-label="Лекции">__NAV__</nav><div class="end-links"><a href="#extra-10" id="summary-link">Сводка и тренировочная работа</a></div><div class="meter"><i id="progress-bar" style="width:0%"></i></div><div class="progress-line"><span class="small">Запомнил карточек</span><span class="small" id="progress-text">0</span></div></aside><main id="workspace"><div class="toolbar"><input id="search" type="search" aria-label="Поиск по материалу" placeholder="Найти: explicit, const, RAII…"><select id="lecture-filter" aria-label="Выбор лекции"><option value="all">Все лекции</option>__OPTIONS__</select><button id="expand">Раскрыть всё</button><button id="collapse">Свернуть всё</button></div><p class="status" id="status" role="status" aria-live="polite"></p><div id="reading">__CONTENT__</div><p class="empty" id="no-results" hidden>Ничего не найдено. Попробуй другое слово или выбери все лекции.</p><section id="training" hidden><p class="mode-desc" id="mode-description"></p><div id="study" aria-live="polite"></div></section></main></div>
<footer class="page-footer">Основа: восемь презентаций из docs. Стандарт C++20. Интерфейс вдохновлён <a href="https://socium.fun/ya#go" target="_blank" rel="noopener">Socium</a>: темы, самостоятельное решение, разбор и повторение. Прогресс хранится в этом браузере, если локальное хранилище доступно.<br><button class="pill" id="reset" style="margin-top:14px">Сбросить учебный прогресс</button></footer></div>
<script>
'use strict';
const CARDS=__CARD_DATA__, QUESTIONS=__QUIZ_DATA__;
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KEY='oop-study-v1'; let progress={known:{},repeat:{},wrong:{}}; let storageOK=true;
try{const saved=JSON.parse(localStorage.getItem(KEY)||'null');if(saved&&typeof saved==='object'){for(const k of ['known','repeat','wrong'])if(saved[k]&&typeof saved[k]==='object'&&!Array.isArray(saved[k]))progress[k]=saved[k]}}catch(e){storageOK=false}
let mode='read', queue=[], pos=0, shown=false, answered=false, score=0, repeatOnly=false, lastResult='';
function save(){try{localStorage.setItem(KEY,JSON.stringify(progress))}catch(e){storageOK=false}updateProgress()}
function updateProgress(){const n=CARDS.filter(c=>progress.known[c.id]).length;$('#progress-text').textContent=n+' / '+CARDS.length;$('#progress-bar').style.width=(n/CARDS.length*100)+'%';if(!storageOK)$('#status').textContent='Сохранение недоступно: прогресс действует до закрытия страницы.'}
function matches(item){const l=$('#lecture-filter').value,q=$('#search').value.trim().toLocaleLowerCase('ru');return(l==='all'||item.lecture===Number(l))&&(!q||(item.q+' '+(item.a||item.why||'')+' '+(item.code||'')).toLocaleLowerCase('ru').includes(q))}
function shuffle(items){const a=items.slice();for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function filterReading(){const l=$('#lecture-filter').value,q=$('#search').value.trim().toLocaleLowerCase('ru');let count=0;$$('.lesson').forEach(lesson=>{let any=false;const eligible=l==='all'||lesson.dataset.lecture===l;const topics=Array.from(lesson.querySelectorAll('.topic'));topics.forEach(t=>{const match=!q||t.textContent.toLocaleLowerCase('ru').includes(q);t.hidden=!match;if(match){any=true;if(q)t.open=true}});if(!topics.length)any=!q||lesson.textContent.toLocaleLowerCase('ru').includes(q);lesson.hidden=!eligible||!any;if(!lesson.hidden)count++});$('#no-results').hidden=count>0||mode!=='read'}
function startSession(){const source=mode==='cards'?CARDS:QUESTIONS;let items=source.filter(matches);if(repeatOnly)items=items.filter(c=>mode==='cards'?progress.repeat[c.id]:progress.wrong[c.id]);queue=shuffle(items);if(mode==='quiz')queue=queue.slice(0,10);pos=0;score=0;shown=false;answered=false;lastResult='';renderTraining()}
function setMode(next){mode=next;repeatOnly=false;$$('[data-mode]').forEach(b=>{b.classList.toggle('active',b.dataset.mode===mode);b.setAttribute('aria-pressed',String(b.dataset.mode===mode))});$('#reading').hidden=mode!=='read';$('#training').hidden=mode==='read';$('#expand').hidden=mode!=='read';$('#collapse').hidden=mode!=='read';$('#no-results').hidden=true;if(mode==='read')filterReading();else startSession()}
function renderTraining(){const box=$('#study');$('#mode-description').textContent=mode==='cards'?'Сформулируй ответ вслух. Затем открой объяснение и оцени, смог ли вспомнить правило.':'До 10 вопросов за попытку. Вопросы идут в случайном порядке; ошибочные можно повторить отдельно.';if(!queue.length){box.innerHTML='<div class="empty"><h2>В этой подборке нет вопросов</h2><p>Измени поиск или лекцию. Для повторения сначала ответь на вопросы.</p><button class="secondary" data-action="all">Все вопросы</button></div>';return}if(pos>=queue.length){box.innerHTML='<div class="study-panel"><div class="label">ПОДХОД ЗАВЕРШЁН</div><h2>'+(mode==='quiz'?score+' из '+queue.length+' верно':'Все '+queue.length+' карточек просмотрены')+'</h2><p>Вернись к правилам, в которых сомневался, и объясни их на новом примере.</p><div class="actions"><button class="primary" data-action="restart">Ещё один подход</button><button class="secondary" data-action="repeat">'+(mode==='quiz'?'Повторить ошибки':'Повторить сложные')+'</button></div></div>';return}const item=queue[pos];let content='<div class="study-panel"><div class="counter">'+(pos+1)+' / '+queue.length+' · лекция '+item.lecture+(repeatOnly?' · повторение':'')+'</div><div class="label">'+(mode==='cards'?'ВСПОМНИ ПРАВИЛО':'РАЗБЕРИ КОД')+'</div><h2>'+escapeHTML(item.q)+'</h2>';if(mode==='cards'){content+=shown?'<div class="answer">'+escapeHTML(item.a)+'</div><div class="actions"><button class="secondary" data-action="hard">Нужно повторить</button><button class="primary" data-action="known">Запомнил</button></div>':'<p class="small">Не открывай ответ, пока не попробовал объяснить своими словами.</p><div class="actions"><button class="primary" data-action="reveal">Показать ответ</button></div>'}else{content+='<pre><code>'+escapeHTML(item.code)+'</code></pre>';item.options.forEach((o,i)=>{const cls=answered?(i===item.correct?' good':i===Number(lastResult)?' bad':''):'';content+='<button class="choice'+cls+'" data-choice="'+i+'" '+(answered?'disabled':'')+'>'+escapeHTML(o)+'</button>'});if(answered)content+='<div class="feedback">'+(Number(lastResult)===item.correct?'Верно. ':'Нужно повторить. ')+escapeHTML(item.why)+'</div><div class="actions"><button class="primary" data-action="next">'+(pos===queue.length-1?'Результат':'Следующий вопрос')+'</button></div>'}box.innerHTML=content+'</div>'}
$('#study').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;const a=b.dataset.action;if(b.dataset.choice!==undefined&&!answered){answered=true;lastResult=b.dataset.choice;const item=queue[pos];if(Number(lastResult)===item.correct){score++;delete progress.wrong[item.id]}else progress.wrong[item.id]=true;save()}else if(a==='reveal')shown=true;else if(a==='known'||a==='hard'){const id=queue[pos].id;if(a==='known'){progress.known[id]=true;delete progress.repeat[id]}else{delete progress.known[id];progress.repeat[id]=true}save();pos++;shown=false}else if(a==='next'){pos++;answered=false}else if(a==='restart'||a==='all'){repeatOnly=false;startSession();return}else if(a==='repeat'){repeatOnly=true;startSession();return}renderTraining()});
$$('[data-mode]').forEach(b=>b.addEventListener('click',()=>{setMode(b.dataset.mode);if(b.closest('.hero'))$('#workspace').scrollIntoView({block:'start'})}));
function refresh(){if(mode==='read')filterReading();else startSession()}
$('#search').addEventListener('input',refresh);$('#lecture-filter').addEventListener('change',refresh);
$('#expand').addEventListener('click',()=>$$('.lesson:not([hidden]) .topic:not([hidden])').forEach(t=>t.open=true));$('#collapse').addEventListener('click',()=>$$('.topic').forEach(t=>t.open=false));
function navigateHash(){const hash=decodeURIComponent(location.hash.slice(1));let target=document.getElementById(hash);if(!target)return;$('#lecture-filter').value='all';$('#search').value='';setMode('read');target.hidden=false;if(target.matches('details'))target.open=true;const ancestor=target.closest('details');if(ancestor)ancestor.open=true;target.scrollIntoView({block:'start'});$$('.sidebar a').forEach(a=>a.classList.toggle('current',a.hash===location.hash))}
window.addEventListener('hashchange',navigateHash);$('#start-init').addEventListener('click',()=>{const t=$$('.topic').find(t=>t.querySelector('summary').textContent.includes('1.6.'));if(t){location.hash=t.id;navigateHash()}});
const extra=$$('.lesson').find(x=>x.dataset.lecture==='0');if(extra)$('#summary-link').href='#'+extra.id;
$('#reset').addEventListener('click',()=>{if(confirm('Сбросить отметки карточек и список ошибок?')){progress={known:{},repeat:{},wrong:{}};save();if(mode!=='read')startSession()}});
updateProgress();filterReading();if(location.hash)navigateHash();
</script></body></html>'''
options=''.join(f'<option value="{i}">Лекция {i}</option>' for i in range(1,9))
for k,v in {'__CARDS__':str(len(cards)),'__QUIZZES__':str(len(quizzes)),'__NAV__':''.join(nav),'__OPTIONS__':options,'__CONTENT__':''.join(sections),'__CARD_DATA__':json.dumps(cards,ensure_ascii=False),'__QUIZ_DATA__':json.dumps(quizzes,ensure_ascii=False)}.items():page=page.replace(k,v)
(root/'OOP_CPP20_Тренажёр.html').write_text(page)
# Сохраняем генератор: после правок Markdown HTML можно воспроизвести.
# Генератор запускается из папки проекта; зависит от Python-пакета markdown.
print('Updated Markdown; created HTML:',len(page),'characters;',len(cards),'cards;',len(quizzes),'questions;',len(sections),'sections')
