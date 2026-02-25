# 🌳 Flatten Binary Tree to Linked List — Cheatsheet

> LeetCode 114 · `void flatten(TreeNode* root)`  
> Flatten in-place into a pre-order linked list (use `right` pointers, set all `left` to `nullptr`)

---

## 📊 Approach Comparison

| Version | Method | Time | Space | Reentrant | Logic |
|---|---|---|---|---|---|
| **baseline** | Iterative (Morris variant) | O(n) | **O(1)** | ✓ | Each node: find left tail → attach right → promote left |
| **v1** | Recursive reverse post-order | O(n) | O(h) | ✗ | Build from leaf up; `_prev` tracks tail |
| **v2** | Recursive pre-order | O(n) | O(h) | ✗ | Flatten left → connect → flatten right; `_prev` member |
| **v3** | Recursive post-order + while | **O(n²)** | O(h) | ✓ | Flatten subtrees → while loop finds tail → O(size) per node |
| **v4** | Recursive post-order, return tail | O(n) | O(h) | ✓ | Helper returns tail → sub-tree connects directly |
| **v5** | Recursive, `TreeNode*&` | O(n) | O(h) | ✓ | Reference to pointer; node becomes tail after recursion |
| **v6** | Recursive reverse pre-order, pass `next` | O(n) | O(h) | ✓ | Right first → left → connect; each subtree tail → next |

> **h** = tree height (O(log n) balanced, O(n) degenerate)

---

## 🔍 Version Highlights

### baseline — Morris Variant ⭐ Best for Production
```
Amortized O(n): each edge touched ≤ 2 times
O(1) space → zero stack overflow risk
No member state → reentrant
```

### v4 — Best Recursive ⭐ Most Readable
```
Return tail pointer → no while loop to find tail
Clean O(n) without worrying about stack depth
Easy to reason about
```

### v3 — Avoid ❌
```
Intuitive logic but O(n²) — finding tail in already-flattened subtree
```

### v1 / v2 — State Pollution ❌
```
Member variable _prev → not reentrant (cannot call twice on same object)
```

---

## 💡 Quick Pick Guide

| Need | Choice |
|---|---|
| O(1) space, big trees | **baseline** |
| Recursive, readable, O(n) | **v4** |
| Learning & intuition | **v3** (accept O(n²)) |
| Elegant tail-building | **v6** |

---

## 🧠 Tree Traversal Order Matters

- **Pre-order (root-left-right)**: `baseline`, v6 → natural left-to-right linking
- **Post-order (left-right-root)**: v3, v4, v5 → build subtrees first, then connect
- **Reverse post-order (right-left-root)**: v1 → build tail-backwards
- **Pre-order reverse (right first)**: v2, v6 → process right first → easier tail tracking

---

## ⚠️ Reentrancy & Member State

> Using `_prev` as a **member variable** makes the solution **not reentrant**.  
> Calling `flatten()` twice on the same `Solution` object → undefined behavior (state persists).

**Safe alternatives:**
- Use local `_prev` in helper (pass by reference)
- Return tail pointer from recursion
- Pass tail as parameter through recursion

---

## 🎯 One-Line Summary

**baseline**: Morris magic — O(n) time, O(1) space, no recursion.  
**v4**: Classic recursion done right — return the tail, connect directly.
