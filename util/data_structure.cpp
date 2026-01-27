#include "data_structure.h"

#include <boost/json/array.hpp>
#include <boost/json/fwd.hpp>
#include <queue>

Tree::Tree(const boost::json::value& val) {
    if (!val.is_array()) {
        return;
    }

    const auto& arr = val.as_array();
    if (arr.empty() || !arr.front().is_int64()) {
        return;
    }

    this->root = new TreeNode(arr.front().as_int64());

    std::queue<TreeNode*> q;
    q.push(root);

    size_t i = 1;
    while (!q.empty() && i < arr.size()) {
        auto node = q.front();
        q.pop();

        if (i < arr.size() && arr[i].is_int64()) {
            node->left = new TreeNode(arr[i].as_int64());
            q.push(node->left);
        }
        i++;

        if (i < arr.size() && arr[i].is_int64()) {
            node->right = new TreeNode(arr[i].as_int64());
            q.push(node->right);
        }
        i++;
    }
}

Tree::~Tree() { release_node(this->root); }

void Tree::release_node(TreeNode* node) {
    if (!node) {
        return;
    }

    release_node(node->left);
    release_node(node->right);

    delete node;
}

boost::json::value Tree::serialize_tree_level_order() {
    if (!this->root) {
        return boost::json::array{};
    }

    boost::json::value out = boost::json::array{};
    auto& arr              = out.as_array();

    std::queue<TreeNode*> q;
    q.push(this->root);

    while (!q.empty()) {
        auto node = q.front();
        q.pop();

        if (node) {
            arr.push_back(node->val);
            q.push(node->left);
            q.push(node->right);
        } else {
            arr.push_back(nullptr);
        }
    }

    while (!arr.empty() && arr.back().is_null()) {
        arr.pop_back();
    }

    return out;
}
