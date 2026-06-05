# leetcode/solutions/001-two-sum-multilang.py
# LeetCode 1: Two Sum
# Pattern: Hash Map
# Date: 2026-06-05

# ============================================
# TYPESCRIPT VERSION (Primary)
# ============================================
"""
function twoSum(nums: number[], target: number): number[] {
    const seen = new Map<number, number>();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (seen.has(complement)) {
            return [seen.get(complement)!, i];
        }
        seen.set(nums[i], i);
    }
    return [];
}
"""

# ============================================
# JAVASCRIPT VERSION
# ============================================
"""
function twoSum(nums, target) {
    const seen = new Map();
    for (let i = 0; i < nums.length; i++) {
        const complement = target - nums[i];
        if (seen.has(complement)) {
            return [seen.get(complement), i];
        }
        seen.set(nums[i], i);
    }
    return [];
}
"""

# ============================================
# PYTHON VERSION
# ============================================
"""
def twoSum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
"""

# ============================================
# COMPLEXITY (All versions same)
# ============================================
# Time: O(n)
# Space: O(n)

# ============================================
# KEY INSIGHT
# ============================================
# Use hash map to store complements for O(1) lookup