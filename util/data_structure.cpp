#include "data_structure.h"

#include <boost/json/array.hpp>
#include <boost/json/fwd.hpp>
#include <queue>
#include <string>

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

// --- TreeBase: shared construct / destruct / release ---

template <typename NodeType>
TreeBase<NodeType>::TreeBase(const boost::json::value& json_val) {
    if (!json_val.is_array()) {
        return;
    }

    const auto& array = json_val.as_array();
    if (array.empty() || !array.front().is_int64()) {
        return;
    }

    this->root = new NodeType(array.front().as_int64());

    std::queue<NodeType*> q;
    q.push(root);

    size_t idx = 1;
    while (!q.empty() && idx < array.size()) {
        auto node = q.front();
        q.pop();

        if (idx < array.size() && array[idx].is_int64()) {
            node->left = new NodeType(array[idx].as_int64());
            q.push(node->left);
        }
        ++idx;

        if (idx < array.size() && array[idx].is_int64()) {
            node->right = new NodeType(array[idx].as_int64());
            q.push(node->right);
        }
        ++idx;
    }
}

template <typename NodeType>
TreeBase<NodeType>::TreeBase(NodeType* root) : root(root) {}

template <typename NodeType>
TreeBase<NodeType>::~TreeBase() {
    release_node(this->root);
}

template <typename NodeType>
void TreeBase<NodeType>::release_node(NodeType* node) {
    if (!node) {
        return;
    }

    release_node(node->left);
    release_node(node->right);

    delete node;
}

// Explicit instantiations
template struct TreeBase<TreeNode>;
template struct TreeBase<Node>;

// --- Tree: level-order serialization ---

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

// --- ConnectedTree: next-pointer level-order serialization ---

std::string ConnectedTree::serialize_next_level_order() {
    if (!this->root) {
        return "[]";
    }

    std::string result = "[";
    Node* level_head   = this->root;

    while (level_head) {
        Node* curr = level_head;
        level_head = nullptr;

        while (curr) {
            if (result.size() > 1) {
                result += ',';
            }
            result += std::to_string(curr->val);

            if (!level_head) {
                if (curr->left) {
                    level_head = curr->left;
                } else if (curr->right) {
                    level_head = curr->right;
                }
            }

            curr = curr->next;
        }

        result += ",#";
    }

    result += ']';
    return result;
}
