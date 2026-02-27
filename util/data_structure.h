#ifndef UTIL_DATA_STRUCTURE_H
#define UTIL_DATA_STRUCTURE_H

#include <boost/json.hpp>
#include <concepts>

struct ListNode {
    int val;
    ListNode* next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
    ListNode(int x, ListNode* next) : val(x), next(next) {}
};

struct List {
    ListNode* head = nullptr;
    List(const boost::json::value& val);
    List(ListNode* head);
    ~List();
    List(const List&)            = delete;
    List& operator=(const List&) = delete;

    void release_node(ListNode* node);
};

struct Node {
    int val;
    Node* left;
    Node* right;
    Node* next;

    Node() : val(0), left(nullptr), right(nullptr), next(nullptr) {}
    Node(int val) : val(val), left(nullptr), right(nullptr), next(nullptr) {}
    Node(int val, Node* left, Node* right, Node* next) : val(val), left(left), right(right), next(next) {}
};

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode* left, TreeNode* right) : val(x), left(left), right(right) {}
};

template <typename T>
concept TreeNodeType = std::same_as<T, TreeNode> || std::same_as<T, Node>;

template <TreeNodeType NodeType>
class TreeBase {
    NodeType* root_ = nullptr;
    void release(NodeType* node);

public:
    TreeBase() = default;
    explicit TreeBase(const boost::json::value& json_val);
    explicit TreeBase(NodeType* root);
    ~TreeBase();

    TreeBase(const TreeBase&)            = delete;
    TreeBase& operator=(const TreeBase&) = delete;

    NodeType* root() const { return root_; }
};

class ITree {
public:
    virtual boost::json::value serialize() = 0;
    virtual ~ITree()                       = default;
};

class Tree : public ITree {
    TreeBase<TreeNode> base_;

public:
    Tree() = default;
    explicit Tree(const boost::json::value& json_val) : base_(json_val) {}
    explicit Tree(TreeNode* root) : base_(root) {}

    TreeNode* root() const { return base_.root(); }
    boost::json::value serialize() override;
};

class ConnectedTree : public ITree {
    TreeBase<Node> base_;

public:
    ConnectedTree() = default;
    explicit ConnectedTree(const boost::json::value& json_val) : base_(json_val) {}
    explicit ConnectedTree(Node* root) : base_(root) {}

    Node* root() const { return base_.root(); }
    boost::json::value serialize() override;
};

#endif /* UTIL_DATA_STRUCTURE_H */
