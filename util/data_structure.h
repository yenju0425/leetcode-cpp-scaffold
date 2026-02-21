#ifndef UTIL_DATA_STRUCTURE_H
#define UTIL_DATA_STRUCTURE_H

#include <boost/json.hpp>

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

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode* left, TreeNode* right) : val(x), left(left), right(right) {}
};

struct Tree {
    TreeNode* root = nullptr;
    Tree(const boost::json::value& val);
    Tree(TreeNode* root);
    ~Tree();
    Tree(const Tree&)            = delete;
    Tree& operator=(const Tree&) = delete;

    void release_node(TreeNode* node);
    boost::json::value serialize_tree_level_order();
};

#endif /* UTIL_DATA_STRUCTURE_H */
