#ifndef UTIL_DATA_STRUCTURE_H
#define UTIL_DATA_STRUCTURE_H

#include <boost/json.hpp>
#include <string>

struct ListNode {
    int val;
    ListNode* next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode* next) : val(x), next(next) {}
};

struct List {
    ListNode* head = nullptr;
    List(const boost::json::value& val);
    List(ListNode* head);
    ~List();
    List(const List&)            = delete;
    List& operator=(const List&) = delete;

    void release_node(ListNode* node);
};

struct Node {
    int val;
    Node* left;
    Node* right;
    Node* next;

    Node() : val(0), left(nullptr), right(nullptr), next(nullptr) {}
    Node(int val) : val(val), left(nullptr), right(nullptr), next(nullptr) {}
    Node(int val, Node* left, Node* right, Node* next) : val(val), left(left), right(right), next(next) {}
};

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode* left, TreeNode* right) : val(x), left(left), right(right) {}
};

// --- TreeBase: shared RAII wrapper for tree node types ---
// Requires NodeType to have: (int) constructor, left/right pointers

template <typename NodeType>
struct TreeBase {
    NodeType* root = nullptr;

    TreeBase() = default;
    explicit TreeBase(const boost::json::value& json_val);
    explicit TreeBase(NodeType* root);
    ~TreeBase();

    TreeBase(const TreeBase&)            = delete;
    TreeBase& operator=(const TreeBase&) = delete;

    void release_node(NodeType* node);
};

struct Tree : TreeBase<TreeNode> {
    using TreeBase::TreeBase;
    boost::json::value serialize_tree_level_order();
};

struct ConnectedTree : TreeBase<Node> {
    using TreeBase::TreeBase;
    std::string serialize_next_level_order();
};

#endif /* UTIL_DATA_STRUCTURE_H */
