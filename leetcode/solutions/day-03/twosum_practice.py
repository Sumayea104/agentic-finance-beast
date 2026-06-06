class Solution:
    def twoSum(self, nums, target):
        seen = {}
        
        for i, num in enumerate(nums):
            complement = target - num
            
            if complement in seen:
                return [seen[complement], i]
            
            seen[num] = i
        
        return []


#         function twoSum(nums, target) {
#     const seen = new Map(); // value -> index
    
#     for (let i = 0; i < nums.length; i++) {
#         const complement = target - nums[i];
        
#         if (seen.has(complement)) {
#             return [seen.get(complement), i];
#         }
        
#         seen.set(nums[i], i);
#     }
# }----javascript version


# function twoSum(nums: number[], target: number): number[] {
#     const seen = new Map<number, number>();
#     for (let i = 0; i < nums.length; i++) {
#         const currentNum = nums[i];
#         const complement = target - currentNum;
#         if (seen.has(complement)) {
#             return [seen.get(complement)!, i];
#         }
#         seen.set(currentNum, i);
#     }
#     return [];
# }----typescript version