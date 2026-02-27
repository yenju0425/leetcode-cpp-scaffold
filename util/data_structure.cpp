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

template <TreeNodeType NodeType>
TreeBase<NodeType>::TreeBase(const boost::json::value& json_val) {
    if (!json_val.is_array()) {
        return;
    }

    const auto& array = json_val.as_array();
    if (array.empty() || !array.front().is_int64()) {
        return;
    }

    root_ = new NodeType(array.front().as_int64());

    std::queue<NodeType*> q;
    q.push(root_);

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

template <TreeNodeType NodeType>
TreeBase<NodeType>::TreeBase(NodeType* root) : root_(root) {}

template <TreeNodeType NodeType>
TreeBase<NodeType>::~TreeBase() {
    release(root_);
}

template <TreeNodeType NodeType>
void TreeBase<NodeType>::release(NodeType* node) {
    if (!node) {
        return;
    }

    release(node->left);
    release(node->right);

    delete node;
}

template class TreeBase<TreeNode>;
template class TreeBase<Node>;

boost::json::value Tree::serialize() {
    if (!base_.root()) {
        return boost::json::array{};
    }

    boost::json::value result = boost::json::array{};
    auto& array               = result.as_array();

    std::queue<TreeNode*> q;
    q.push(base_.root());

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

boost::json::value ConnectedTree::serialize() {
    boost::json::value result = boost::json::array{};
    auto& array               = result.as_array();

    Node* level_head = base_.root();

    while (level_head) {
        Node* curr      = level_head;
        Node* next_head = nullptr;

        while (curr) {
            array.push_back(curr->val);

            if (!next_head) {
                if (curr->left) {
                    next_head = curr->left;
                } else if (curr->right) {
                    next_head = curr->right;
                }
            }

            curr = curr->next;
        }

        array.push_back(nullptr);  // level sentinel
        level_head = next_head;
    }

    return result;
}
