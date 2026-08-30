import csv
from datetime import datetime
import json
import urllib.request
from zoneinfo import ZoneInfo

# Add all team members here
MEMBERS = {
    "Sanish Dalvi": "SanishDalvi",
    "Veer": "Veer",
}

CSV_FILE = "schedule.csv"
GRAPHQL_URL = "https://leetcode.com/graphql"

USER_DATA_QUERY = """
query getUserData($username: String!) {
  matchedUser(username: $username) {
    submitStats {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
  recentAcSubmissionList(username: $username, limit: 25) {
    title
  }
}
"""


def load_schedule_from_csv(filename):
  schedule = {}
  with open(filename, mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
      date_key = row["Date"].strip()
      occasion = row["Occasion"].strip()
      problems_raw = row["Problems"].strip()

      if problems_raw.upper() == "HOLIDAY":
        schedule[date_key] = {"type": "holiday", "occasion": occasion}
      else:
        problems = [p.strip() for p in problems_raw.split(";") if p.strip()]
        schedule[date_key] = {
            "type": "practice",
            "occasion": occasion,
            "problems": problems,
        }
  return schedule


def fetch_leetcode_data(username):
  payload = json.dumps(
      {"query": USER_DATA_QUERY, "variables": {"username": username}}
  )
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
      matched = data.get("data", {}).get("matchedUser")
      total_solved = 0
      if matched and "submitStats" in matched:
        for item in matched["submitStats"]["acSubmissionNum"]:
          if item["difficulty"] == "All":
            total_solved = item["count"]

      submissions = data.get("data", {}).get("recentAcSubmissionList", [])
      recent_titles = [
          sub["title"].strip().lower() for sub in submissions if "title" in sub
      ]
      return total_solved, recent_titles
  except Exception:
    return 0, []


# Load current date in IST
ist_time = datetime.now(ZoneInfo("Asia/Kolkata"))
today_str = ist_time.strftime("%d-%m")
today_display = ist_time.strftime("%d %b %Y, %I:%M %p IST")

schedule = load_schedule_from_csv(CSV_FILE)
today_entry = schedule.get(today_str, None)

is_holiday = False
occasion_name = ""
assigned_problems = []

if today_entry is None or today_entry["type"] == "holiday":
  is_holiday = True
  occasion_name = today_entry["occasion"] if today_entry else "Rest Day"
else:
  occasion_name = today_entry["occasion"]
  assigned_problems = today_entry["problems"]

# Process members
member_stats = []
for name, handle in MEMBERS.items():
  total_solved, recent_titles = fetch_leetcode_data(handle)
  solved_count = 0

  if not is_holiday and assigned_problems:
    for prob in assigned_problems:
      clean_prob = (
          prob.replace(" (revisit)", "")
          .replace(" (Hard)", "")
          .strip()
          .lower()
      )
      if clean_prob in recent_titles:
        solved_count += 1

    total_assigned = len(assigned_problems)
    if solved_count == total_assigned:
      status = f"✅ {solved_count}/{total_assigned} (Complete)"
    elif solved_count > 0:
      status = f"⚠️ {solved_count}/{total_assigned} (Partial)"
    else:
      status = f"❌ 0/{total_assigned} (Pending)"
  else:
    status = f"🌴 {occasion_name}"

  member_stats.append({
      "name": name,
      "handle": handle,
      "total_solved": total_solved,
      "today_status": status,
  })

# Sort leaderboard by total problems solved (descending)
member_stats.sort(key=lambda x: x["total_solved"], reverse=True)

# Build Markdown rows
leaderboard_rows = []
for rank, member in enumerate(member_stats, 1):
  profile_link = f"[{member['handle']}](https://leetcode.com/{member['handle']})"
  leaderboard_rows.append(
      f"| #{rank} | **{member['name']}** | {profile_link} | {member['total_solved']} | {member['today_status']} |"
  )

# Header generation
if is_holiday:
  schedule_header = (
      f"### 🌴 Rest / Holiday Day ({occasion_name})\nNo mandatory problems"
      " scheduled for today."
  )
else:
  schedule_header = (
      f"### 📅 Assigned Problems for {occasion_name} ({today_str}):\n"
      + "\n".join([f"- **{p}**" for p in assigned_problems])
  )

readme_content = f"""# 🚀 MLSC Tier 2 DSA Tracker

> **Last Updated:** {today_display} (Auto-syncs every 2 hours)

{schedule_header}

---

### 🏆 Team Leaderboard
| Rank | Member | LeetCode Profile | Total Solved | Today's Status |
| :---: | :--- | :--- | :---: | :--- |
""" + "\n".join(leaderboard_rows)

with open("README.md", "w", encoding="utf-8") as f:
  f.write(readme_content)
