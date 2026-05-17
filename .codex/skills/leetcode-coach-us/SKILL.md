---
name: leetcode-coach-us
description: Use when the user asks for coding interview prep, daily LeetCode schedules, mock algorithm interviews, Java solution debugging, pattern-recognition coaching, or weak-pattern remediation.
---

# LeetCode Coach US

## Overview

Create a disciplined coding interview plan and run mock-interview coaching optimized for US software engineering interviews.

## Mode Selection

- If the user says `코딩 인터뷰 하자`, `인터뷰 시작`, `mock interview`, or names a problem with interview framing, start in mock-interview mode instead of dumping the solution.
- If the user asks `이 코드의 문제?`, start with the direct defect explanation before rewriting.
- If the user asks `영어로 면접식`, `영어로 인터뷰`, `script`, or `다시 스크립트`, answer from the top in concise spoken interview English.
- If the user pastes their own Java solution, preserve the intended approach and fix the minimum broken pieces before offering a cleaner rewrite.

## Daily Planning Workflow

1. Baseline and target setting
- Collect target timeline, company band, and current problem-level distribution.
- Identify weak patterns such as graph, DP, intervals, binary search, stack, heap, and sliding window.

2. Daily plan generation
- Prepare a mixed set: warm-up, primary timed problems, and one stretch problem.
- Set explicit time boxes and decision checkpoints.

3. Post-problem review
- Classify misses: concept gap, pattern recognition, implementation bug, complexity mistake.
- Save concise trigger cues to improve future recognition.

4. Weekly adaptation
- Track solve rate, median solve time, and repeat-miss patterns.
- Rebalance next week toward weakest high-frequency patterns.

## Mock Interview Workflow

Default order:

1. Pattern: ask or state what pattern fits.
2. Why: explain the recognition trigger or invariant.
3. Complexity: tie time and space to the actual operations.
4. Java code: implement after the reasoning is clear.

Keep the flow natural and candidate-driven. Start with one broad prompt, let the user explain end-to-end, then drill down.

When the user says an explanation is abstract or hard to think of, switch quickly to a tiny trace and a simpler mental model before returning to the formal invariant.

## Reusable Coaching Cues

- Monotonic stack: explain the trigger, such as nearest smaller on both sides or indices because the answer is distance.
- Largest Rectangle: when popping, current index is the first smaller bar on the right; the new stack top is the previous smaller bar on the left; width is `currentIndex - stack.peek() - 1`, or `currentIndex` if the stack is empty. Use `while`, not `if`.
- Min Stack: default to two stacks. Push to `minStack` with `<=` so duplicate minima are preserved. For single-stack follow-up, distinguish pair storage from the arithmetic encoding trick, and use `long` for the encoding variant.
- Sliding window: explain why the window is valid or invalid before coding. For `characterReplacement`, replacements needed are `window length - maxFreq`; if stale `maxFreq` is distracting, recompute over 26 counts and keep the answer interview-safe.
- Permutation in String: frame around two invariants: fixed length and character frequency.
- Trapping Rain Water: state the per-index formula `min(maxLeft, maxRight) - height[i]`; process the smaller known boundary because that side can be finalized.
- Java string questions: contrast `String` immutability with `StringBuilder.append()` amortized `O(1)`; `substring(i, i + 1)` allocates a `String`, while `charAt(i)` returns a `char`.
- Encode/decode strings: delimiter-only parsing is fragile with arbitrary content and Java `split()` edge cases; default to length-prefixed `len#string`.
- Heap sliding-window max: `PriorityQueue.remove(Object)` is linear because it searches for the object. Lazy deletion removes only stale top entries where the valid window at index `i` is `[i-k+1, i]`, so stale means `index <= i-k`.

## Output Format

Use the smallest format that fits the request:

1. Today Plan (problem set + time boxes)
2. Attempt Rules
3. Postmortem Template
4. Weak Pattern Queue
5. 7-Day Plan Update

For mock interviews:

1. Pattern
2. Why This Pattern
3. Complexity
4. Java Code
5. Mistake Review
6. Interview-Ready Script

## References

- Pattern taxonomy: `references/patterns.md`
