# 🌳 Binary Tree Reconstruction Cheatsheet

## ✅ When Reconstruction Is Unique (node values must be unique)

| Traversals | Unique? |
|------------|----------|
| Inorder + Preorder | ✅ Yes |
| Inorder + Postorder | ✅ Yes |
| Preorder + Postorder | ❌ No (unless Full Binary Tree) |

---

## 🧠 Traversal Patterns

```
Inorder   = [ left | root | right ]
Preorder  = [ root | left | right ]
Postorder = [ left | right | root ]
```

👉 Inorder splits the tree into left/right subtrees  
👉 Preorder/Postorder identifies the root  

---

## 🔑 Core Algorithm

### Inorder + Preorder

- `preorder[pre_l]` = **root**
- Find root index `idx` in `inorder[in_l..in_r)`
- Left subtree size: `left_size = idx - in_l`
- Recurse:
  - Left:  `preorder[pre_l+1]`,        inorder `[in_l, idx)`
  - Right: `preorder[pre_l+1+left_size]`, inorder `[idx+1, in_r)`

> Preorder gives root **first**

**Example:**
```
preorder = [3, 9, 20, 15, 7]
inorder  = [9, 3, 15, 20, 7]

root = 3  (preorder[0])
idx  = 1  (position of 3 in inorder)
left_size = idx - 0 = 1

Left subtree:  preorder[1..1], inorder[0..1)  → root=9
Right subtree: preorder[2..4], inorder[2..5)  → root=20
```

---

### Inorder + Postorder

- `postorder[post_r - 1]` = **root**
- Find root index `idx` in `inorder[in_l..in_r)`
- Left subtree size: `left_size = idx - in_l`
- Recurse:
  - Left:  postorder `[post_l, post_l+left_size)`,   inorder `[in_l, idx)`
  - Right: postorder `[post_l+left_size, post_r-1)`, inorder `[idx+1, in_r)`

> Postorder gives root **last**

**Example:**
```
inorder   = [9, 3, 15, 20, 7]
postorder = [9, 15, 7, 20, 3]

root = 3  (postorder[4])
idx  = 1  (position of 3 in inorder)
left_size = idx - 0 = 1

Left subtree:  postorder[0..1), inorder[0..1)  → root=9
Right subtree: postorder[1..4), inorder[2..5)  → root=20
```

---

## ⚡ Optimization

- Build a hashmap: `value → inorder index` at the start
- Turns O(n) linear search per node into O(1) lookup
- Overall Time Complexity: **O(n)**
- Space Complexity: **O(n)** (hashmap + recursion stack)

Without hashmap: **O(n²)** due to repeated linear search

---

## ❗ Common Pitfalls

- Node values must be **unique** (required for hashmap and unambiguous splitting)
- `auto idx = 0` deduces `int`; use `size_t` to avoid signed/unsigned comparison warnings when indices are `size_t`
- Right subtree preorder start: `pre_l + 1 + left_size`, **not** `pre_l + 1`
- Preorder + Postorder alone is **ambiguous** (cannot distinguish a single child being left or right)

---

## 🎯 One-Line Summary

Inorder splits the tree.  
Preorder/Postorder tells you where the root is.
