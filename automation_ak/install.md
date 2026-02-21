# Installing AutomationAK + Doc Designer AK

Step-by-step guide for installing both apps on an existing Frappe/ERPNext bench (v16+).

Both apps live in the same repository. One clone gives you both.

## Prerequisites

- A working Frappe bench (v16)
- A site already created (`bench new-site` done)
- Git installed on the server

---

## Step 1: Clone the repository

From your bench directory, clone into `apps/` under the name `automation_ak`:

```bash
cd ~/frappe-bench/apps
git clone https://github.com/advaitku/FrappeAK.git automation_ak
```

Then create a symlink so bench can also see `doc_designer_ak` (which lives as a subdirectory of the same repo):

```bash
ln -s ~/frappe-bench/apps/automation_ak/doc_designer_ak ~/frappe-bench/apps/doc_designer_ak
```

---

## Step 2: Install Python packages

Register both apps in the bench virtualenv:

```bash
cd ~/frappe-bench
./env/bin/pip install -e apps/automation_ak
./env/bin/pip install -e apps/doc_designer_ak
```

---

## Step 3: Install apps on your site

```bash
bench --site YOUR_SITE install-app automation_ak
bench --site YOUR_SITE install-app doc_designer_ak
```

This creates all database tables for both apps.

---

## Step 4: Build frontend assets

```bash
bench build --app automation_ak
bench build --app doc_designer_ak
```

---

## Step 5: Restart

Production (Supervisor/systemd):

```bash
bench restart
```

Development:

```bash
bench start
```

---

## Verify

1. Log in as Administrator
2. Search for **AK Automation** — the DocType should appear
3. Search for **AK Doc Template** — the Doc Designer DocType should appear
4. Open **AK Automation Settings** to configure logging and optional WhatsApp credentials

---

## Updating

```bash
cd ~/frappe-bench/apps/automation_ak
git pull

cd ~/frappe-bench
bench --site YOUR_SITE migrate
bench build --app automation_ak
bench build --app doc_designer_ak
bench restart  # if production
```

The `doc_designer_ak` symlink picks up changes automatically since it points inside the same repo.

---

## Uninstalling

```bash
bench --site YOUR_SITE uninstall-app doc_designer_ak
bench --site YOUR_SITE uninstall-app automation_ak

# Remove the symlink and the cloned repo
unlink ~/frappe-bench/apps/doc_designer_ak
bench remove-app automation_ak
```

---

## Troubleshooting

### "No module named 'automation_ak'"

The virtualenv pip install was skipped or failed. Run:

```bash
./env/bin/pip install -e apps/automation_ak
./env/bin/pip install -e apps/doc_designer_ak
```

### "No module named 'doc_designer_ak'"

The symlink is missing. Recreate it:

```bash
ln -s ~/frappe-bench/apps/automation_ak/doc_designer_ak ~/frappe-bench/apps/doc_designer_ak
./env/bin/pip install -e apps/doc_designer_ak
```

### "App not in apps.txt"

Run `bench --site YOUR_SITE install-app <app_name>` — bench manages `apps.txt` automatically, do not edit it by hand.

### PackageLoader / Jinja template errors

Usually means the symlink is broken or pip install was not run after moving files. Re-run Steps 2 and then:

```bash
bench --site YOUR_SITE migrate
```
