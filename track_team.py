import csv
from datetime import datetime, time
import json
import urllib.request
from zoneinfo import ZoneInfo

MEMBERS = {
    "Sanish": "SanishDalvi",
    "Amruta": "amruta_thakare",
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
  recentAcSubmissionList(username: $username, limit: 30) {
    title
    timestamp
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
      total_all_time = 0
      if matched and "submitStats" in matched:
        for item in matched["submitStats"]["acSubmissionNum"]:
          if item["difficulty"] == "All":
            total_all_time = item["count"]

      submissions = data.get("data", {}).get("recentAcSubmissionList", [])
      return total_all_time, submissions
  except Exception:
    return 0, []


# Current IST Time & Today's Midnight Epoch Timestamp
ist_tz = ZoneInfo("Asia/Kolkata")
now_ist = datetime.now(ist_tz)
midnight_ist = datetime.combine(now_ist.date(), time.min, tzinfo=ist_tz)
midnight_epoch = int(midnight_ist.timestamp())

today_str = now_ist.strftime("%d-%m")
today_display = now_ist.strftime("%d %b %Y, %I:%M %p IST")

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

member_stats = []

for name, handle in MEMBERS.items():
  total_all_time, submissions = fetch_leetcode_data(handle)

  # Filter unique problems solved since 12:00 AM IST today
  solved_today_titles = set()
  for sub in submissions:
    sub_time = int(sub.get("timestamp", 0))
    if sub_time >= midnight_epoch and "title" in sub:
      solved_today_titles.add(sub["title"].strip().lower())

  total_solved_today = len(solved_today_titles)

  # Check assigned drive problems
  if not is_holiday and assigned_problems:
    assigned_match_count = 0
    for prob in assigned_problems:
      clean_prob = (
          prob.replace(" (revisit)", "")
          .replace(" (Hard)", "")
          .strip()
          .lower()
      )
      if clean_prob in solved_today_titles:
        assigned_match_count += 1

    total_assigned = len(assigned_problems)
    if assigned_match_count == total_assigned:
      status = f"✅ {assigned_match_count}/{total_assigned} (Complete)"
    elif assigned_match_count > 0:
      status = f"⚠️ {assigned_match_count}/{total_assigned} (Partial)"
    else:
      status = f"❌ 0/{total_assigned} (Pending)"
  else:
    status = f"🌴 {occasion_name}"

  member_stats.append({
      "name": name,
      "handle": handle,
      "total_all_time": total_all_time,
      "total_today": total_solved_today,
      "today_status": status,
  })

# Sort leaderboard by all-time solved count (descending)
member_stats.sort(key=lambda x: x["total_all_time"], reverse=True)

# Generate Markdown table rows
leaderboard_rows = []
for rank, member in enumerate(member_stats, 1):
  profile_link = f"[{member['handle']}](https://leetcode.com/{member['handle']})"
  leaderboard_rows.append(
      f"| #{rank} | **{member['name']}** | {profile_link} | {member['total_today']} | {member['today_status']} | {member['total_all_time']} |"
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
| Rank | Member | LeetCode Profile | Solved Today | Drive Status | Total All-Time Solved |
| :---: | :--- | :--- | :---: | :--- | :---: |
""" + "\n".join(leaderboard_rows)

with open("README.md", "w", encoding="utf-8") as f:
  f.write(readme_content)
