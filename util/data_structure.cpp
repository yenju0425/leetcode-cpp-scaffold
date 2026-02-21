#include "data_structure.h"

#include <boost/json/array.hpp>
#include <boost/json/fwd.hpp>
#include <queue>

List::List(const boost::json::value& json_val) {
    if (!json_val.is_array()) {
        return;
    }

    const auto& array = json_val.as_array();
    if (array.empty() || !array.front().is_int64()) {
        return;
    }

    for (auto array_it = array.rbegin(); array_it != array.rend(); ++array_it) {
        if (array_it->is_int64()) {
            head = new ListNode(array_it->as_int64(), head);
        }
    }
}

List::List(ListNode* node) : head(node) {}

List::~List() { release_node(head); }

void List::release_node(ListNode* node) {
    while (node) {
        auto node_ptr = node;
        node          = node->next;

        delete node_ptr;
    }
}

Tree::Tree(const boost::json::value& json_val) {
    if (!json_val.is_array()) {
        return;
    }

    const auto& array = json_val.as_array();
    if (array.empty() || !array.front().is_int64()) {
        return;
    }

    this->root = new TreeNode(array.front().as_int64());

    std::queue<TreeNode*> q;
    q.push(root);

    size_t idx = 1;
    while (!q.empty() && idx < array.size()) {
        auto node = q.front();
        q.pop();

        if (idx < array.size() && array[idx].is_int64()) {
            node->left = new TreeNode(array[idx].as_int64());
            q.push(node->left);
        }
        ++idx;

        if (idx < array.size() && array[idx].is_int64()) {
            node->right = new TreeNode(array[idx].as_int64());
            q.push(node->right);
        }
        ++idx;
    }
}

Tree::Tree(TreeNode* root) : root(root) {}

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

    boost::json::value result = boost::json::array{};
    auto& array               = result.as_array();

    std::queue<TreeNode*> q;
    q.push(this->root);

    while (!q.empty()) {
        auto node = q.front();
        q.pop();

        if (node) {
            array.push_back(node->val);
            q.push(node->left);
            q.push(node->right);
        } else {
            array.push_back(nullptr);
        }
    }

    while (!array.empty() && array.back().is_null()) {
        array.pop_back();
    }

    return result;
}
