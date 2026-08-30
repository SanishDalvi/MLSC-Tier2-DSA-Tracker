from datetime import datetime
import json
import urllib.request
import zoneinfo

MEMBERS = {
    "Sanish Dalvi": "SanishDalvi",
    "Veer": "Veer",
}

# Mapping Tier 2 schedule by date (DD-MM)
TIER_2_SCHEDULE = {
    "01-09": ["Two Sum", "Valid Anagram", "Backspace String Compare"],
    "02-09": ["Contains Duplicate", "Best Time to Buy and Sell Stock", "3Sum"],
    "03-09": ["Majority Element", "Move Zeroes", "Container With Most Water"],
    "04-09": ["Single Number", "Intersection of Two Arrays II", "Sort Colors"],
    "05-09": [
        "Plus One",
        "Merge Sorted Array",
        "Longest Substring Without Repeating Characters",
    ],
    "07-09": [
        "Remove Duplicates from Sorted Array",
        "Remove Element",
        "Minimum Size Subarray Sum",
    ],
    "08-09": [
        "Search Insert Position",
        "Valid Palindrome",
        "Longest Repeating Character Replacement",
    ],
    "09-09": ["Reverse String", "Reverse Integer", "Permutation in String"],
    "10-09": [
        "Palindrome Number",
        "Roman to Integer",
        "Find All Anagrams in a String",
    ],
    "11-09": ["Integer to Roman", "Longest Common Prefix", "3Sum Closest"],
    "12-09": [
        "Find the Index of the First Occurrence in a String",
        "Length of Last Word",
        "4Sum",
    ],
    "15-09": ["Add Binary", "Sqrt(x)", "Subarray Product Less Than K"],
    "16-09": [
        "Climbing Stairs",
        "Pascal's Triangle",
        "Max Consecutive Ones III",
    ],
    "17-09": ["Pascal's Triangle II", "Missing Number", "Fruit Into Baskets"],
    "18-09": [
        "Find All Numbers Disappeared in an Array",
        "Third Maximum Number",
        "Boats to Save People",
    ],
    "19-09": [
        "Assign Cookies",
        "Two Sum II - Input Array Is Sorted",
        "Sort an Array",
    ],
    "21-09": [
        "Squares of a Sorted Array",
        "Fibonacci Number",
        "Kth Largest Element in an Array",
    ],
    "22-09": [
        "Ransom Note",
        "First Unique Character in a String",
        "Sliding Window Maximum",
    ],
    "23-09": [
        "Isomorphic Strings",
        "Word Pattern",
        "Minimum Window Substring",
    ],
    "24-09": ["Happy Number", "Excel Sheet Column Title", "Rotate Array"],
    "25-09": [
        "Excel Sheet Column Number",
        "Power of Two",
        "Product of Array Except Self",
    ],
    "26-09": ["Power of Three", "Power of Four", "Trapping Rain Water"],
    "28-09": ["Ugly Number", "Count Primes", "Backspace String Compare"],
    "29-09": ["Add Digits", "Number of 1 Bits", "3Sum"],
    "30-09": [
        "Reverse Bits",
        "Hamming Distance",
        "Container With Most Water",
    ],
    # Remaining October, November, and December dates can be added following the same format
}

GRAPHQL_URL = "https://leetcode.com/graphql"
QUERY = """
query getRecentSubmissions($username: String!) {
  recentAcSubmissionList(username: $username, limit: 15) {
    title
  }
}
"""


def get_recent_accepted_titles(username):
  payload = json.dumps({"query": QUERY, "variables": {"username": username}})
  req = urllib.request.Request(
      GRAPHQL_URL,
      data=payload.encode("utf-8"),
      headers={
          "Content-Type": "application/json",
          "User-Agent": "Mozilla/5.0",
          "Referer": "https://leetcode.com",
      },
  )
  try:
    with urllib.request.urlopen(req, timeout=10) as response:
      data = json.loads(response.read().decode())
      submissions = data.get("data", {}).get("recentAcSubmissionList", [])
      return [sub["title"].strip().lower() for sub in submissions]
  except Exception:
    return []


# Get today's date in Indian Standard Time (IST)
ist_time = datetime.now(zoneinfo.ZoneInfo("Asia/Kolkata"))
today_str = ist_time.strftime("%d-%m")
today_display = ist_time.strftime("%d %b %Y")

assigned_problems = TIER_2_SCHEDULE.get(today_str, None)

table_rows = []

if assigned_problems is None:
  status_header = f"### 🌴 {today_display} is a Rest / Holiday Day! No assigned problems today.\n"
else:
  status_header = f"### 📅 Assigned Problems for Today ({today_display}):\n"
  for p in assigned_problems:
    status_header += f"- **{p}**\n"

  for name, handle in MEMBERS.items():
    recent_solved = get_recent_accepted_titles(handle)
    solved_count = 0

    for prob in assigned_problems:
      # Normalise title check (handles minor formatting differences)
      clean_prob = prob.replace(" (revisit)", "").replace(" (Hard)", "").strip().lower()
      if clean_prob in recent_solved:
        solved_count += 1

    total_assigned = len(assigned_problems)
    if solved_count == total_assigned:
      status = f"✅ {solved_count}/{total_assigned} (Complete)"
    elif solved_count > 0:
      status = f"⚠️ {solved_count}/{total_assigned} (Partial)"
    else:
      status = f"❌ 0/{total_assigned} (Pending)"

    profile_link = f"[{handle}](https://leetcode.com/{handle})"
    table_rows.append(f"| **{name}** | {profile_link} | {status} |")

readme_content = f"""# 🚀 MLSC Tier 2 DSA Tracker

{status_header}

### 📊 Daily Progress Table
| Member | LeetCode Profile | Today's Status |
| :--- | :--- | :--- |
""" + "\n".join(table_rows)

with open("README.md", "w") as f:
  f.write(readme_content)
