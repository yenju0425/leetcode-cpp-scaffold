#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
    void connect_helper(Node* const curr, Node* const next) {
        if (!curr) {
            return;
        }

        connect_helper(curr->left, curr->right);
        connect_helper(curr->right, next ? next->left : nullptr);

        curr->next = next;
    }

public:
    Node* connect(Node* root) {
        connect_helper(root, nullptr);
        return root;
    }
};

}  // namespace baseline

namespace iterative_v1 {

class Solution {
public:
    Node* connect(Node* root) {
        if (!root) {
            return root;
        }

        std::queue<Node*> current_level;
        current_level.push(root);

        while (!current_level.empty()) {
            std::queue<Node*> next_level;

            Node* prev_node = nullptr;
            while (!current_level.empty()) {
                auto* node = current_level.front();
                current_level.pop();

                node->next = prev_node;
                prev_node  = node;

                if (node->right) next_level.push(node->right);
                if (node->left) next_level.push(node->left);
            }

            std::swap(current_level, next_level);
        }

        return root;
    }
};

}  // namespace iterative_v1

namespace iterative_v2 {

class Solution {
public:
    Node* connect(Node* root) {
        if (!root) {
            return root;
        }

        auto* level_head = root;
        while (level_head && level_head->left) {
            auto* curr = level_head;
            while (curr) {
                curr->left->next  = curr->right;
                curr->right->next = curr->next ? curr->next->left : nullptr;
                curr              = curr->next;
            }

            level_head = level_head->left;
        }

        return root;
    }
};

}  // namespace iterative_v2

}  // anonymous namespace
