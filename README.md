# Python Exercise Auto-Grader

A web application for automated grading of Python programming exercises.
Built for educational use, it gives students immediate feedback on
correctness, code quality and security, and provides instructors with
tools to manage exercises and track student progress.

**Live demo:** https://avaliador-python.streamlit.app/

> This is a public demo of an educational project. The hosted instance
> uses shared test accounts and a shared database — do not submit
> sensitive code or use real credentials.

## Demo Accounts

| Role       | Username  | Password |
|------------|-----------|----------|
| Instructor | professor | admin123 |
| Student    | aluno1    | teste123 |

## Features

**For students**
- Browse and submit solutions to 19 Python exercises
- Sandboxed execution with timeout protection
- Immediate feedback: test results, contextual error hints, style and
  security warnings
- Personal submission history and statistics
- Per-submission PDF report export

**For instructors**
- Class-wide dashboard with per-student progress
- View and filter all submissions by student or exercise
- Add new exercises through the interface

## Tech Stack

- **Application:** Python 3, Streamlit
- **Editor:** streamlit-ace
- **Database:** Supabase (PostgreSQL)
- **PDF generation:** fpdf2
- **Hosting:** Streamlit Community Cloud

## Local Setup

Requires Python 3.10 or newer.

```bash
git clone https://github.com/josemalves/avaliador-python.git
cd avaliador-python
pip install -r requirements.txt
streamlit run app.py
```

Supabase credentials are read from `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
```

## Project Structure

```
avaliador-python/
├── app.py            # Main Streamlit application
├── exercises/        # One JSON file per exercise
├── requirements.txt
└── .streamlit/
    └── config.toml
```

## Adding Exercises

Each exercise is a JSON file under `exercises/`:

```json
{
  "title": "Exercise Title",
  "description": "What the function should do.",
  "function": "function_name",
  "tests": [
    { "input": [1, 2], "output": 3 },
    { "input": [4, 5], "output": 9 }
  ]
}
```

## Status

Educational demo. Not intended for production use with untrusted users.

## License

Released under the MIT License — see [LICENSE](LICENSE).

## Author

José Alves
