# Installing AutomationAK on a Frappe Site

Step-by-step guide for installing AutomationAK on an existing Frappe/ERPNext bench.

## Prerequisites

- A working Frappe bench (v14 or v15)
- A site already created (`bench new-site` done)
- Git access to this repository

## Step 1: Get the app

From your bench directory:

```bash
cd ~/frappe-bench
bench get-app https://github.com/YOUR_USERNAME/FrappeAK.git
```

> **If `bench get-app` fails with a directory naming error**, the repo name (`FrappeAK`) doesn't match the app name (`automation_ak`). In that case, install manually:
>
> ```bash
> cd ~/frappe-bench/apps
> git clone https://github.com/YOUR_USERNAME/FrappeAK.git automation_ak
> cd ~/frappe-bench
> bench setup requirements --apps automation_ak
> ```
>
> Then add `automation_ak` to `sites/apps.txt` (on its own line, after `frappe`).

## Step 2: Install on your site

```bash
bench --site YOUR_SITE install-app automation_ak
```

This creates all the database tables for the 6 DocTypes (AK Automation, AK Automation Condition, AK Automation Action, AK Field Update, AK Automation Log, AK Automation Settings).

## Step 3: Build frontend assets

```bash
bench build --app automation_ak
```

This compiles the `ak_buttons.bundle.js` which injects macro buttons on forms.

## Step 4: Run migrations

```bash
bench --site YOUR_SITE migrate
```

This syncs the DocType schemas to the database and registers hooks.

## Step 5: Restart

If running in production (Supervisor/systemd):

```bash
bench restart
```

If running in development:

```bash
bench start
```

## Step 6: Verify

1. Open your site in a browser
2. Log in as Administrator
3. Go to the URL bar and type **AK Automation** -- you should see the DocType in search results
4. Go to **AK Automation Settings** to configure logging and WhatsApp credentials (optional)

## Creating Your First Automation

1. Go to **AK Automation > New**
2. Set a **Title** (e.g. "Set priority on new ToDos")
3. Pick a **Reference DocType** (e.g. `ToDo`)
4. Choose a **Trigger Type** (e.g. `On Create`)
5. Add a condition: Field = `status`, Operator = `is`, Value = `Open`
6. Add an action: Type = `Update Fields`, set `priority` to `High`
7. Save and enable
8. Create a new ToDo with status "Open" -- the priority should auto-set to "High"
9. Check **AK Automation Log** to see the execution record

## Updating

When you pull new code:

```bash
cd ~/frappe-bench/apps/automation_ak
git pull

cd ~/frappe-bench
bench --site YOUR_SITE migrate
bench build --app automation_ak
bench restart  # if production
```

## Uninstalling

```bash
bench --site YOUR_SITE uninstall-app automation_ak
bench remove-app automation_ak
```

This drops the app's database tables and removes it from the bench.

## Troubleshooting

### "No module named 'automation_ak.automationak'"

The `modules.txt` file must contain `Automation AK` (with a space). Frappe's `scrub()` converts this to `automation_ak` to find the Python module. If it says `AutomationAK` (no space), it looks for `automationak` which doesn't exist.

### "App automation_ak not in apps.txt"

Add `automation_ak` on its own line in `~/frappe-bench/sites/apps.txt`:

```
frappe
automation_ak
```

Make sure there's a newline after `frappe` -- otherwise the entries get concatenated.

### Redis not running / Services not running

Bench manages its own Redis instances. Run `bench start` in development mode, or ensure Supervisor/systemd services are running in production. The `bench migrate` command requires Redis to be available.

### "FileNotFoundError: ./apps/automation_ak/automation_ak/__init__.py"

The app directory name must be `automation_ak`, not the git repo name. If you cloned as `FrappeAK`, rename or symlink it:

```bash
cd ~/frappe-bench/apps
mv FrappeAK automation_ak
# or
ln -s /path/to/FrappeAK automation_ak
```
