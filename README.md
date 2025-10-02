<div align=center>

# Finance Dashboard
</div>

Privacy-first personal finance tracker built with Django. This project follows the MoSCoW requirements outlined in the project brief.

## Features

- Email/password authentication with per-user data isolation.
- CRUD for transactions, categories, tags, and budgets.
- Monthly dashboard with summaries, charts, and recent activity.
- CSV import/export with mapping preview.
- REST API powered by Django REST Framework with JWT auth.
- Reporting endpoints and pages for monthly and category breakdowns.

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Node.js (optional, for future React frontend)

### Startup TODO
- A computer running Windows, macOS, or Linux with administrator access
- [Git](https://git-scm.com/) – used to clone the repository
- [Python 3.12+](https://www.python.org/downloads/) – installs `python` and `pip`
- PostgreSQL 14+ (instructions below cover both Docker and native installation)
- Node.js (optional, for future React frontend work)
	```bash
### Step-by-Step Startup Guide
	source .venv/bin/activate  # On Windows with bash.exe
- [ ] **Clone the project and open a terminal in the project folder**

	```bash
	git clone <YOUR_FORK_OR_THIS_REPO_URL>
	cd "Finance Dashboard"
	```

- [ ] **Create and activate a Python virtual environment**

	```bash
	python -m venv .venv
	source .venv/bin/activate  # Windows Git Bash
	.\.venv\Scripts\activate  # Windows PowerShell / cmd
	```

- [ ] **Install Python dependencies**
	```

- [ ] Copy the example environment file and update secrets/database settings as needed

	```bash
- [ ] **Install or start PostgreSQL** (choose **one** of the two options)

	**Option A – Docker (easiest to start)**

	```bash
	docker run --name finance-postgres -e POSTGRES_DB=finance_db -e POSTGRES_USER=finance_user -e POSTGRES_PASSWORD=finance_pass -p 5432:5432 -d postgres:14
	```

	This launches PostgreSQL in the background. To stop it later run `docker stop finance-postgres` and `docker start finance-postgres` when you need it again.

	**Option B – Native install**

	1. Download PostgreSQL 14 from the [official site](https://www.postgresql.org/download/) and run the installer.
	2. During setup choose a password for the default `postgres` superuser and make note of it.
	3. Open **pgAdmin** (installed with PostgreSQL) or a terminal and create a database user and database:

		 ```sql
		 -- run inside psql or pgAdmin query tool
		 CREATE USER finance_user WITH PASSWORD 'finance_pass';
		 CREATE DATABASE finance_db OWNER finance_user;
		 ```

- [ ] **Copy environment variables file and configure database credentials**
	```

### Step-by-Step Startup Guide

- [ ] **Clone the project and change into its directory**
	```bash
	git clone <YOUR_FORK_OR_THIS_REPO_URL>
	cd "Finance Dashboard"
	```

- [ ] **Create and activate a Python virtual environment**
	```bash
	python -m venv .venv
	source .venv/bin/activate        # Windows Git Bash / macOS / Linux
	.\.venv\Scripts\activate       # Windows PowerShell / Command Prompt
	```

- [ ] **Install Python dependencies**
	```bash
	pip install -r requirements.txt
	```

- [ ] **Install or start PostgreSQL** — choose **one** option

	**Option A – Docker (recommended for beginners)**
	```bash
	docker run --name finance-postgres \
		-e POSTGRES_DB=finance_db \
		-e POSTGRES_USER=finance_user \
		-e POSTGRES_PASSWORD=finance_pass \
		-p 5432:5432 -d postgres:14
	```
	This command runs PostgreSQL in the background. Later you can stop it with `docker stop finance-postgres` and restart with `docker start finance-postgres`.

	**Option B – Native installation**
	1. Download PostgreSQL 14 from the [official site](https://www.postgresql.org/download/) and follow the installer prompts.
	2. Choose a password for the default `postgres` superuser and write it down.
	3. Open the **SQL Shell (psql)** or **pgAdmin** and create a dedicated user and database:
		 ```sql
		 -- run inside psql or pgAdmin query tool
		 CREATE USER finance_user WITH PASSWORD 'finance_pass';
		 CREATE DATABASE finance_db OWNER finance_user;
		 ```

- [ ] **Copy the environment file and configure database credentials**
	```bash
	cp .env.example .env
	```
	Open `.env` in a text editor and update the values to match the credentials you configured above. For the commands shown, use:
	```env
	DATABASE_URL=postgres://finance_user:finance_pass@localhost:5432/finance_db
	SECRET_KEY=replace-me-with-a-long-random-string
	DEBUG=True
	```

- [ ] **Enable the `pg_trgm` PostgreSQL extension** (required for fast text search)

	**Docker**
	```bash
	docker exec -it finance-postgres psql -U finance_user -d finance_db -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
	```

	**Native install**
	```sql
	-- run inside psql or pgAdmin while connected as the postgres superuser
	CREATE EXTENSION IF NOT EXISTS pg_trgm;
	```

- [ ] **Apply database migrations** (creates all tables inside PostgreSQL)
	```bash
	python manage.py migrate
	```

- [ ] **Create an admin (superuser) account** so you can log in locally
	```bash
	python manage.py createsuperuser
	```

- [ ] **Start the development server and open the app**
	```bash
	python manage.py runserver
	```
	Visit http://127.0.0.1:8000/ in your browser and sign in with the superuser credentials you just created.
