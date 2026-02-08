#include <util/leetcode.h>

namespace baseline {

using namespace std;

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
