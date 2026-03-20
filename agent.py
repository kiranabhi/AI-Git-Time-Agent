import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_1.git.models import GitQueryCommitsCriteria
from logger import log_entry
from openai import AzureOpenAI, OpenAI
#from trio_client import TrioClient
from trio_browser import log_time_to_trio
import json
import csv

load_dotenv()

# ── Azure DevOps Setup ───────────────────────────────────────────────
ORG      = os.getenv("AZURE_DEVOPS_ORG")
PROJECT  = os.getenv("AZURE_DEVOPS_PROJECT")
REPO     = os.getenv("AZURE_DEVOPS_REPO")
PAT      = os.getenv("AZURE_DEVOPS_PAT")

# ── OpenAI Setup ─────────────────────────────────────────────────────
if os.getenv("OPENAI_BASE_URL"):
    openai_client = AzureOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        azure_endpoint=os.getenv("OPENAI_BASE_URL"),
        api_version=os.getenv("OPENAI_API_VERSION", "2025-01-01-preview"),
    )
else:
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = os.getenv("OPENAI_DEPLOYMENT", "gpt-4.1")


def get_todays_commits(author_email: str = None, days_back: int = 1) -> list[dict]:
    """Fetch commits from Azure DevOps for the past N days, filtered to a specific author email."""
    credentials = BasicAuthentication("", PAT)
    connection = Connection(
        base_url=f"{ORG}",
        creds=credentials
    )
    git_client = connection.clients.get_git_client()

    now = datetime.now().astimezone()
    from_date = now - timedelta(days=days_back)

    search_criteria = GitQueryCommitsCriteria()
    search_criteria.from_date = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    search_criteria.to_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    commits_response = git_client.get_commits(
        repository_id=REPO,
        search_criteria=search_criteria,
        project=PROJECT,
    )

    # ── Filter strictly by your email ────────────────────────────────
    results = []
    for commit in commits_response:
        commit_email = (commit.author.email or "").strip().lower()
        if author_email and commit_email != author_email.strip().lower():
            continue  # Skip commits not belonging to you

        results.append({
            "commit_id":     commit.commit_id,
            "author":        commit.author.name,
            "email":         commit.author.email,
            "date":          commit.author.date.strftime("%Y-%m-%d"),
            "message":       commit.comment,
            "changed_files": commit.change_counts,
        })

    return results


def build_summary_with_llm(commits: list[dict]) -> tuple[str, float]:
    """
    Send commit messages to an LLM and get back:
    - A short plain-English work summary
    - An estimated hours worked as 8 hours for a full day of work
    Returns (summary_text, estimated_hours).
    """
    if not commits:
        return "No commits found for today.", 0.0

    commit_text = "\n".join(
        f"- [{c['date']}] {c['message']} (files changed: {c['changed_files']})"
        for c in commits
    )

    prompt = f"""You are a developer productivity assistant.

Below are today's git commit messages from Azure DevOps:

{commit_text}

Please provide:
1. A concise 2-4 sentence summary of the work done today, suitable for a timesheet.
2. An estimated number of hours worked, as a decimal (e.g. 4.5), based on the volume and nature of the commits. Be reasonable — typical dev work is 4–8 hours.

Respond in this exact format:
SUMMARY: <your summary here>
HOURS: <number only, e.g. 6.0>
"""

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    # Parse structured response
    summary = ""
    hours = 4.0  # default fallback

    for line in raw.splitlines():
        if line.startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()
        elif line.startswith("HOURS:"):
            try:
                hours = float(line.replace("HOURS:", "").strip())
            except ValueError:
                hours = 4.0

    return summary, hours


def run_agent(author_email: str = None, target_date: str = None):
    """
    Main agent entrypoint.
    - author_email: filter commits by a specific user (optional, for team use)
    - target_date: override today's date string (YYYY-MM-DD)
    """
    date_str = target_date or datetime.now().astimezone().strftime("%Y-%m-%d")
    print(f"\n🤖 Git Time Agent — processing commits for {date_str}")

    # Step 1: Fetch commits
    print("📥 Fetching commits from Azure DevOps...")
    commits = get_todays_commits(author_email=author_email, days_back=1)

    if not commits:
        print("⚠️  No commits found for today. Nothing logged.")
        return

    print(f"✅ Found {len(commits)} commit(s):")
    for c in commits:
        print(f"   • {c['message'][:80]}")

    # Step 2: Generate summary via LLM
    print("\n🧠 Generating summary with LLM...")
    summary, hours = build_summary_with_llm(commits)
    print(f"\n📝 Summary: {summary}")
    print(f"⏱️  Estimated hours: {hours}")

    # Step 3: Log to file
    print("\n💾 Logging to file...")
    log_entry(
        date=date_str,
        hours=hours,
        summary=summary,
        author=author_email or commits[0]["author"],
        commits=commits,
    )

    # Step 4: Log to Trio via browser automation
    print("\n🌐 Logging to Trio via browser...")
    log_time_to_trio(date=date_str, hours=hours, summary=summary)


if __name__ == "__main__":
    # Each team member sets their own AUTHOR_EMAIL in .env,
    # or it can be passed as an arg/env variable
    author_email = os.getenv("AUTHOR_EMAIL")  # Optional: filter by user

    if not author_email:
        print("❌ ERROR: AUTHOR_EMAIL is not set in your .env file.")
        print("   Add:  AUTHOR_EMAIL=your.email@yourcompany.com")
        exit(1)
    run_agent(author_email=author_email)
