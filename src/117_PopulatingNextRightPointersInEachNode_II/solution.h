#include <util/leetcode.h>

namespace {

namespace baseline {

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

}  // namespace baseline

namespace optimized {

class Solution {
public:
    Node* connect(Node* root) {
        Node* level_head = root;

        while (level_head) {
            Node* curr      = level_head;
            Node* next_head = nullptr;
            Node* tail      = nullptr;

            while (curr) {
                if (curr->left) {
                    if (!next_head) next_head = curr->left;

                    if (tail) {
                        tail->next = curr->left;
                    }
                    tail = curr->left;
                }
                if (curr->right) {
                    if (!next_head) next_head = curr->right;

                    if (tail) {
                        tail->next = curr->right;
                    }
                    tail = curr->right;
                }
                curr = curr->next;
            }

            level_head = next_head;
        }

        return root;
    }
};

}  // namespace optimized

namespace recursive {

class Solution {
public:
    Node* connect(Node* root) {
        if (!root) {
            return nullptr;
        }

        Node* curr = root;

        Node* next_head = nullptr;
        Node* tail      = nullptr;
        while (curr) {
            if (curr->left) {
                if (!next_head) next_head = curr->left;

                if (!tail) {
                    tail = curr->left;
                } else {
                    tail->next = curr->left;
                    tail       = curr->left;
                }
            }

            if (curr->right) {
                if (!next_head) next_head = curr->right;

                if (!tail) {
                    tail = curr->right;
                } else {
                    tail->next = curr->right;
                    tail       = curr->right;
                }
            }

            curr = curr->next;
        }

        connect(next_head);
        return root;
    }
};

}  // namespace recursive

// namespace wrong_answer_v1 {

// class Solution {
//     void connect_helper(Node* const curr, Node* const next) {
//         if (!curr) {
//             return;
//         }

//         curr->next = next;

//         if (curr->left) {
//             if (curr->right) {
//                 connect_helper(curr->left, curr->right);
//             } else if (next) {
//                 if (next->left) {
//                     connect_helper(curr->left, next->left);
//                 } else if (next->right) {
//                     connect_helper(curr->left, next->right);
//                 }
//             }
//         }

//         if (curr->right) {
//             if (next) {
//                 if (next->left) {
//                     connect_helper(curr->right, next->left);
//                 } else if (next->right) {
//                     connect_helper(curr->right, next->right);
//                 }
//             } else {
//                 connect_helper(curr->right, nullptr);
//             }
//         }
//     }

// public:
//     Node* connect(Node* root) {
//         connect_helper(root, nullptr);
//         return root;
//     }
// };

// }  // namespace wrong_answer_v1

// namespace wrong_answer_v2 {

// class Solution {
//     void connect_helper(Node* const curr, Node* const next) {
//         if (!curr) {
//             return;
//         }

//         Node* ptr = nullptr;
//         if (next) {
//             ptr = next->left ? next->left : next->right;
//         }

//         if (curr->right) {
//             connect_helper(curr->right, ptr);
//             ptr = curr->right;
//         }

//         if (curr->left) {
//             connect_helper(curr->left, ptr);
//         }

//         curr->next = next;
//     }

// public:
//     Node* connect(Node* root) {
//         connect_helper(root, nullptr);
//         return root;
//     }
// };

// }  // namespace wrong_answer_v2

}  // anonymous namespace
