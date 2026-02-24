# LeetCode C++ Scaffold

Fetch problems, solve in C++ with multiple approaches, test locally with Google Test, and auto-submit to LeetCode — from the command line or CI.

## Quick Start

```bash
# Prerequisites (Ubuntu/Debian)
sudo apt-get install -y cmake g++ cppcheck libgtest-dev libboost-all-dev
cd /usr/src/gtest && sudo cmake . && sudo make && sudo cp lib/*.a /usr/lib/
pip install -r requirements.txt

# Clone & build
git clone https://github.com/<you>/leetcode-cpp-scaffold.git && cd leetcode-cpp-scaffold
cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build --parallel

# Fetch a problem
python fetch.py two-sum   # → src/1_TwoSum/{solution.h, test.cpp, test_cases.json}

# Test & submit
./build/unit_test --gtest_filter="*TwoSum*"
python scripts/submit_to_leetcode.py --problem-slug two-sum --file src/1_TwoSum/solution.h
```

## Writing Solutions

### `solution.h`

Each approach lives in its own namespace:

```cpp
#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    std::vector<int> twoSum(std::vector<int>& nums, int target) {
        std::unordered_map<int, int> m;
        for (int i = 0; i < nums.size(); ++i) {
            auto it = m.find(target - nums[i]);
            if (it != m.end()) return {it->second, i};
            m[nums[i]] = i;
        }
        return {};
    }
};

}  // namespace baseline

namespace brute_force {

class Solution {
public:
    std::vector<int> twoSum(std::vector<int>& nums, int target) {
        for (int i = 0; i < nums.size(); ++i)
            for (int j = i + 1; j < nums.size(); ++j)
                if (nums[i] + nums[j] == target) return {i, j};
        return {};
    }
};

}  // namespace brute_force

}  // anonymous namespace
```

> The closing comment `}  // namespace <name>` is required — the extraction logic uses it to find namespace boundaries.

### `test.cpp`

Wire up two things — the **adapter** and the **solver list**:

```cpp
struct Adapter {
    template <class Solver>
    static boost::json::value invoke(Solver& s, const boost::json::value& case_json) {
        const auto& c     = case_json.as_object();
        const auto& input = c.at("input").as_object();

        auto nums   = boost::json::value_to<std::vector<int>>(input.at("nums"));
        auto target = input.at("target").to_number<int>();
        return boost::json::value_from(s.twoSum(nums, target));
    }
};

static inline const std::vector<io::CaseParam> kParams =
    io::build_params_from_file(__FILE__, "test_cases.json",
                               {{"Baseline", io::make_runner<baseline::Solution, Adapter>()},
                                {"BruteForce", io::make_runner<brute_force::Solution, Adapter>()}});
```

### `test_cases.json`

```json
{"test_cases": [
    {"name": "Example1", "input": {"nums": [2,7,11,15], "target": 9}, "output": [0,1]},
    {"name": "Duplicates", "input": {"nums": [3,3], "target": 6}, "output": [0,1]}
]}
```

## Submitting to LeetCode

### Save Session (first time)

```bash
python scripts/submit_to_leetcode.py --save-session
```

Opens a browser → log in to LeetCode → press Enter. Session + base64 output printed for CI.

### Submit Locally

```bash
# One file (slug derived by shell, or pass explicitly)
python scripts/submit_to_leetcode.py --problem-slug two-sum --file src/1_TwoSum/solution.h

# With visible browser
python scripts/submit_to_leetcode.py --problem-slug two-sum --file src/1_TwoSum/solution.h --show-browser

# Specific namespace only
python scripts/submit_to_leetcode.py --problem-slug two-sum --file src/1_TwoSum/solution.h --ns baseline
```

### Submit Changed Files (Git-aware)

```bash
bash scripts/submit_to_leetcode.sh $(bash scripts/get_changed_files.sh)
```

The shell script derives the problem slug from the directory name (`1_TwoSum` → `two-sum`) and calls the Python script once per file.

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`): **build → cppcheck → test → submit**.

Runs on push to main/master, PRs, and manual dispatch. Only changed `solution.h` files are submitted.

### Secrets

| Secret | Purpose |
|---|---|
| `LEETCODE_STORAGE_STATE` | Base64-encoded session (required) |
| `GH_USERNAME` / `GH_PASSWORD` | GitHub OAuth fallback (optional) |

```bash
python scripts/submit_to_leetcode.py --save-session
# The base64 output → GitHub repo → Settings → Secrets → LEETCODE_STORAGE_STATE
```

## Project Structure

```
├── fetch.py                    # Fetch problem + generate boilerplate
├── src/<N>_<Name>/             # One folder per problem
│   ├── solution.h              #   Your solution(s) in namespaces
│   ├── test.cpp                #   GTest adapter + solver registration
│   └── test_cases.json         #   Test data (JSON)
├── util/                       # Shared C++ (TreeNode, ListNode, IO)
├── templates/                  # Jinja2 templates for code generation
├── scripts/
│   ├── submit_to_leetcode.py   # Playwright submitter (one file per run)
│   ├── submit_to_leetcode.sh   # Shell wrapper (loops files, derives slugs)
│   ├── get_changed_files.sh    # Git diff → changed solution.h paths
│   └── extract_solution.py     # Standalone namespace extractor
└── .github/workflows/ci.yml   # CI pipeline
```
