#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
private:
    TreeNode* build(ListNode*& head, size_t len) {
        if (len == 0) {
            return nullptr;
        }

        size_t left_len = len / 2;
        auto* left      = build(head, left_len);

        auto* node = new TreeNode(head->val);

        head        = head->next;
        auto* right = build(head, len - left_len - 1);

        node->left  = left;
        node->right = right;
        return node;
    }

public:
    TreeNode* sortedListToBST(ListNode* head) {
        auto current_node = head;

        size_t len = 0;
        while (current_node) {
            ++len;
            current_node = current_node->next;
        }

        return build(head, len);
    }
};

}  // namespace baseline

}  // anonymous namespace
