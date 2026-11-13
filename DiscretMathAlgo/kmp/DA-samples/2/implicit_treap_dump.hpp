#pragma once

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

// Include after the definitions of Elem and Treap. Snapshots preserve the physical tree
// and all lazy tags: dump never calls keep_and_deliver_promise().
namespace treap_dump_detail {

struct Node {
    const Elem* elem;
    std::size_t depth;
    std::optional<std::size_t> left;
    std::optional<std::size_t> right;
};

inline std::optional<std::size_t> layout(const Elem* elem, std::size_t depth,
                                       std::vector<Node>& nodes) {
    if (elem == nullptr) {
        return std::nullopt;
    }

    auto left = layout(elem->l, depth + 1, nodes);
    std::size_t index = nodes.size();
    nodes.push_back({elem, depth, left, std::nullopt});
    auto right = layout(elem->r, depth + 1, nodes);
    nodes[index].right = right;
    return index;
}

inline void values(const Elem* elem, int64_t inherited_add,
                   bool inherited_reverse, std::ostream& out) {
    if (elem == nullptr) {
        return;
    }

    int64_t add = inherited_add + elem->promise;
    bool reverse = inherited_reverse != elem->reverse;
    values(reverse ? elem->r : elem->l, add, reverse, out);
    out << ' ' << elem->value + add;
    values(reverse ? elem->l : elem->r, add, reverse, out);
}

} // namespace treap_dump_detail

// With no filename, each call writes a new treap_dumps/snapshot_N.svg.
// Node cards show the stored fields; the header includes all pending lazy tags.
inline void dump(const Elem* root, const std::string& filename = "") {
    static std::size_t next_snapshot = 1;
    std::filesystem::path path = filename.empty()
        ? "treap_dumps/snapshot_" + std::to_string(next_snapshot++) + ".svg"
        : filename;
    if (!path.parent_path().empty()) {
        std::filesystem::create_directories(path.parent_path());
    }

    std::vector<treap_dump_detail::Node> nodes;
    auto root_index = treap_dump_detail::layout(root, 0, nodes);
    std::size_t levels = 0;
    for (const auto& node : nodes) {
        levels = std::max(levels, node.depth + 1);
    }

    constexpr std::size_t card_width = 280;
    constexpr std::size_t card_height = 136;
    const std::size_t width = std::max<std::size_t>(800, nodes.size() * 310 + 60);
    const std::size_t height = std::max<std::size_t>(230, levels * 190 + 140);
    auto x = [](std::size_t index) { return 30 + index * 310; };
    auto y = [&](std::size_t index) { return 140 + nodes[index].depth * 190; };

    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("Cannot open treap dump: " + path.string());
    }
    out.exceptions(std::ios::failbit | std::ios::badbit);
    out << "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"" << width
        << "\" height=\"" << height << "\" viewBox=\"0 0 " << width << ' ' << height
        << "\">\n"
        << "<title>Implicit treap snapshot</title>\n"
        << "<style>text { font: 14px monospace; fill: #172033; }"
           " .heading { font: bold 22px sans-serif; }"
           " .note { fill: #526079; }"
           " line { stroke: #64748b; stroke-width: 2; }</style>\n"
        << "<rect width=\"100%\" height=\"100%\" fill=\"#ffffff\"/>\n"
        << "<text class=\"heading\" x=\"30\" y=\"35\">Implicit treap</text>\n"
        << "<text x=\"30\" y=\"65\">Sequence: [";
    treap_dump_detail::values(root, 0, false, out);
    out << " ]</text>\n"
        << "<text class=\"note\" x=\"30\" y=\"92\">"
           "Cards: stored fields. Sequence: pending tags applied.</text>\n"
        << "<text class=\"note\" x=\"30\" y=\"115\">"
           "L/R: physical children. Amber: pending promise or reverse. Blue border: root.</text>\n";

    // Draw edges first, so the node cards cover their endpoints.
    for (std::size_t index = 0; index < nodes.size(); ++index) {
        auto edge = [&](std::optional<std::size_t> child, const char* label) {
            if (!child) {
                return;
            }
            auto x1 = x(index) + card_width / 2;
            auto y1 = y(index) + card_height;
            auto x2 = x(*child) + card_width / 2;
            auto y2 = y(*child);
            out << "<line x1=\"" << x1 << "\" y1=\"" << y1
                << "\" x2=\"" << x2 << "\" y2=\"" << y2 << "\"/>\n"
                << "<text x=\"" << (x1 + x2) / 2 + 6
                << "\" y=\"" << (y1 + y2) / 2 - 4 << "\">" << label << "</text>\n";
        };
        edge(nodes[index].left, "L");
        edge(nodes[index].right, "R");
    }

    for (std::size_t index = 0; index < nodes.size(); ++index) {
        const Elem& elem = *nodes[index].elem;
        bool pending = elem.promise != 0 || elem.reverse;
        bool is_root = root_index && *root_index == index;
        out << "<g transform=\"translate(" << x(index) << ',' << y(index) << ")\">\n"
            << "<rect width=\"" << card_width << "\" height=\"" << card_height
            << "\" rx=\"8\" fill=\"" << (pending ? "#fff1cc" : "#f1f5f9")
            << "\" stroke=\"" << (is_root ? "#2563eb" : "#94a3b8")
            << "\" stroke-width=\"" << (is_root ? 3 : 1) << "\"/>\n"
            << "<text x=\"12\" y=\"24\">value = " << elem.value << "</text>\n"
            << "<text x=\"12\" y=\"44\">priority = " << elem.priority << "</text>\n"
            << "<text x=\"12\" y=\"64\">count = " << elem.count << "</text>\n"
            << "<text x=\"12\" y=\"84\">agg = " << elem.agg << "</text>\n"
            << "<text x=\"12\" y=\"104\">promise = " << elem.promise << "</text>\n"
            << "<text x=\"12\" y=\"124\">reverse = "
            << (elem.reverse ? "true" : "false") << "</text>\n</g>\n";
    }
    if (root == nullptr) {
        out << "<text x=\"30\" y=\"165\">Empty tree</text>\n";
    }
    out << "</svg>\n";
    out.close();
}

inline void dump(const Treap& tree, const std::string& filename = "") {
    dump(tree.root, filename);
}
