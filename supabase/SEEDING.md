Seed runner and guidelines
==========================

This project keeps real student/professor/program data out of migrations and the
public git history. Use the small seed runner below to import local JSON files
into your Supabase instance.

1) Create a local environment with SUPABASE_URL and SUPABASE_KEY set.

2) Install dependencies from requirements.txt (supabase-py).

3) Run the seed script from the repository root:

    python3 -m supabase.seed

If you accidentally committed any of the data files (`data/students.json`,
`data/professors.json`, `data/programs.json`) you can remove them from git
history for future commits using:

    git rm --cached data/students.json data/professors.json data/programs.json
    git commit -m "Remove real data from repo"

To scrub from history entirely consider using git-filter-repo or BFG but be
careful as those operations rewrite history.
