#ifndef UTIL_DATA_STRUCTURE_H
#define UTIL_DATA_STRUCTURE_H

#include <boost/json.hpp>

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
    explicit Tree(const boost::json::value& val);
    ~Tree();
    Tree(const Tree&)            = delete;
    Tree& operator=(const Tree&) = delete;

    void release_node(TreeNode* node);
    boost::json::value serialize_tree_level_order();
};

#endif /* UTIL_DATA_STRUCTURE_H */
