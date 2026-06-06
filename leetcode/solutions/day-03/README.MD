# Day 3: Two Sum (Python)

## Problem
**LeetCode 1. Two Sum** | Easy

Given an array of integers `nums` and an integer `target`, return the indices of two numbers that add up to `target`.

## Example

```python
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: 2 + 7 = 9

Python Solution
```
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        
        for i, num in enumerate(nums):
            complement = target - num
            
            if complement in seen:
                return [seen[complement], i]
            
            seen[num] = i
        
        return []
```

```typescript
function twoSum(nums: number[], target: number): number[] {
    const map = new Map();
    for (let i = 0; i < nums.length; i++) {
        if (map.has(target - nums[i])) 
            return [map.get(target - nums[i]), i];
        map.set(nums[i], i);
    }
    return [];
}
```

```js

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
```