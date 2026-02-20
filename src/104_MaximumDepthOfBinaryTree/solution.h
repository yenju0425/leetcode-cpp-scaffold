#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    int maxDepth(TreeNode* root) {
        if (!root) {
            return 0;
        }

        return std::max(maxDepth(root->left), maxDepth(root->right)) + 1;
    }
};
}  // namespace baseline

}  // anonymous namespace
