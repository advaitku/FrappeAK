#!/bin/bash
###############################################################################
# Frappe + ERPNext v16 — Production Install Script for Ubuntu 22.04 / 24.04
#
# Usage:
#   chmod +x install_frappe_production.sh
#   sudo ./install_frappe_production.sh --domain erp.yourcompany.com --db-password YOUR_MARIADB_ROOT_PASS --admin-password YOUR_ERPNEXT_ADMIN_PASS
#
# Optional flags:
#   --email admin@yourcompany.com   (for Let's Encrypt SSL certificate)
#   --skip-ssl                      (skip SSL setup, useful if DNS isn't ready yet)
#   --frappe-branch version-16      (default: version-16)
#   --erpnext-branch version-16     (default: version-16)
#
# Requirements:
#   - Fresh Ubuntu 22.04 or 24.04 server (2+ vCPU, 4+ GB RAM recommended)
#   - Root or sudo access
#   - Domain DNS A record pointing to this server (for SSL)
#   - Ports 80, 443, 8000 open in AWS Security Group
#
# What this script does:
#   1. Installs system dependencies (Python 3.11, Node 18, MariaDB, Redis, etc.)
#   2. Creates a 'frappe' system user
#   3. Installs bench CLI
#   4. Creates a production bench with Frappe + ERPNext
#   5. Creates your site
#   6. Configures Nginx + Supervisor for production
#   7. Optionally sets up SSL via Let's Encrypt
###############################################################################

set -euo pipefail

# ─── Color helpers ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ─── Parse arguments ────────────────────────────────────────────────────────
SITE_DOMAIN=""
DB_ROOT_PASSWORD=""
ADMIN_PASSWORD=""
LETSENCRYPT_EMAIL=""
SKIP_SSL=false
FRAPPE_BRANCH="version-16"
ERPNEXT_BRANCH="version-16"
BENCH_USER="frappe"
BENCH_DIR="frappe-bench"

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)          SITE_DOMAIN="$2";       shift 2 ;;
        --db-password)     DB_ROOT_PASSWORD="$2";  shift 2 ;;
        --admin-password)  ADMIN_PASSWORD="$2";    shift 2 ;;
        --email)           LETSENCRYPT_EMAIL="$2"; shift 2 ;;
        --skip-ssl)        SKIP_SSL=true;          shift   ;;
        --frappe-branch)   FRAPPE_BRANCH="$2";     shift 2 ;;
        --erpnext-branch)  ERPNEXT_BRANCH="$2";    shift 2 ;;
        *) error "Unknown option: $1" ;;
    esac
done

# ─── Validate inputs ────────────────────────────────────────────────────────
[[ -z "$SITE_DOMAIN" ]]      && error "Missing --domain. Usage: sudo ./install_frappe_production.sh --domain erp.example.com --db-password PASS --admin-password PASS"
[[ -z "$DB_ROOT_PASSWORD" ]] && error "Missing --db-password (MariaDB root password)"
[[ -z "$ADMIN_PASSWORD" ]]   && error "Missing --admin-password (ERPNext Administrator password)"

if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Frappe + ERPNext v16 Production Installer                 ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Domain:        $SITE_DOMAIN"
echo "║  Frappe branch: $FRAPPE_BRANCH"
echo "║  ERPNext branch:$ERPNEXT_BRANCH"
echo "║  SSL:           $(if $SKIP_SSL; then echo 'Skipped'; else echo 'Yes (Let'\''s Encrypt)'; fi)"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ─── Step 1: System updates and locale ───────────────────────────────────────
log "Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq

log "Setting locale to en_US.UTF-8..."
locale-gen en_US.UTF-8 > /dev/null 2>&1 || true
update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# ─── Step 2: Install system dependencies ─────────────────────────────────────
log "Installing system dependencies..."
apt-get install -y -qq \
    python3 python3-dev python3-pip python3-venv python3-setuptools \
    build-essential gcc g++ make \
    git curl wget \
    software-properties-common \
    libffi-dev libssl-dev libmysqlclient-dev \
    libjpeg-dev libpng-dev libtiff-dev \
    libxrender1 libxext6 xfonts-75dpi xfonts-base \
    redis-server \
    supervisor \
    nginx \
    certbot python3-certbot-nginx \
    fail2ban \
    cron

# ─── Step 3: Install Python 3.11 (if not default) ────────────────────────────
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
log "Detected Python $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.11" ]]; then
    log "Installing Python 3.11..."
    add-apt-repository ppa:deadsnakes/ppa -y
    apt-get update -qq
    apt-get install -y -qq python3.11 python3.11-dev python3.11-venv
    PYTHON_BIN="python3.11"
else
    PYTHON_BIN="python3"
fi

# ─── Step 4: Install Node.js 20 LTS via NodeSource ───────────────────────────
if ! command -v node &> /dev/null || [[ $(node -v | cut -d. -f1 | tr -d 'v') -lt 20 ]]; then
    log "Installing Node.js 20 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y -qq nodejs
fi
log "Node.js $(node -v) installed"

# Install Yarn globally
log "Installing Yarn..."
npm install -g yarn > /dev/null 2>&1

# ─── Step 5: Install MariaDB ─────────────────────────────────────────────────
if ! command -v mariadb &> /dev/null; then
    log "Installing MariaDB 10.6+..."
    apt-get install -y -qq mariadb-server mariadb-client
fi

log "Configuring MariaDB..."
cat > /etc/mysql/mariadb.conf.d/99-frappe.cnf <<EOF
[mysqld]
innodb-file-format=barracuda
innodb-file-per-table=1
innodb-large-prefix=1
character-set-client-handshake=FALSE
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
innodb_buffer_pool_size=2G
innodb_log_file_size=256M
innodb_flush_log_at_trx_commit=1
innodb_flush_method=O_DIRECT

[mysql]
default-character-set=utf8mb4
EOF

systemctl restart mariadb
systemctl enable mariadb

# Secure MariaDB — set root password
log "Setting MariaDB root password..."
mariadb -u root <<EOF || true
ALTER USER 'root'@'localhost' IDENTIFIED BY '${DB_ROOT_PASSWORD}';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF

# ─── Step 6: Install wkhtmltopdf (for PDF generation) ────────────────────────
if ! command -v wkhtmltopdf &> /dev/null; then
    log "Installing wkhtmltopdf..."
    ARCH=$(dpkg --print-architecture)
    WKHTML_VERSION="0.12.6.1-3"

    if [[ "$ARCH" == "amd64" ]]; then
        WKHTML_URL="https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTML_VERSION}/wkhtmltox_${WKHTML_VERSION}.jammy_amd64.deb"
    elif [[ "$ARCH" == "arm64" ]]; then
        WKHTML_URL="https://github.com/wkhtmltopdf/packaging/releases/download/${WKHTML_VERSION}/wkhtmltox_${WKHTML_VERSION}.jammy_arm64.deb"
    else
        warn "Unsupported architecture for wkhtmltopdf: $ARCH — skipping"
        WKHTML_URL=""
    fi

    if [[ -n "$WKHTML_URL" ]]; then
        wget -q "$WKHTML_URL" -O /tmp/wkhtmltox.deb
        apt-get install -y -qq /tmp/wkhtmltox.deb || true
        rm -f /tmp/wkhtmltox.deb
    fi
fi

# ─── Step 7: Create frappe user ──────────────────────────────────────────────
if ! id "$BENCH_USER" &>/dev/null; then
    log "Creating '$BENCH_USER' system user..."
    adduser --system --group --home /home/$BENCH_USER --shell /bin/bash $BENCH_USER
    usermod -aG sudo $BENCH_USER
    echo "${BENCH_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$BENCH_USER
fi

# ─── Step 8: Install bench CLI ───────────────────────────────────────────────
log "Installing bench CLI..."
pip3 install frappe-bench --break-system-packages 2>/dev/null || pip3 install frappe-bench

# ─── Step 9: Initialize bench as frappe user ─────────────────────────────────
log "Initializing bench (this may take a few minutes)..."
su - $BENCH_USER -c "
    cd /home/$BENCH_USER
    if [ ! -d '$BENCH_DIR' ]; then
        bench init $BENCH_DIR --frappe-branch $FRAPPE_BRANCH --python $PYTHON_BIN --verbose
    else
        echo 'Bench directory already exists, skipping init'
    fi
"

# ─── Step 10: Install ERPNext app ────────────────────────────────────────────
log "Installing ERPNext (this may take several minutes)..."
su - $BENCH_USER -c "
    cd /home/$BENCH_USER/$BENCH_DIR
    if [ ! -d 'apps/erpnext' ]; then
        bench get-app erpnext --branch $ERPNEXT_BRANCH
    else
        echo 'ERPNext already installed, skipping'
    fi
"

# Also install HRMS (separated from ERPNext in v15+)
log "Installing HRMS..."
su - $BENCH_USER -c "
    cd /home/$BENCH_USER/$BENCH_DIR
    if [ ! -d 'apps/hrms' ]; then
        bench get-app hrms --branch $ERPNEXT_BRANCH || echo 'HRMS install skipped (may not have matching branch)'
    fi
"

# ─── Step 11: Create the site ────────────────────────────────────────────────
log "Creating site: $SITE_DOMAIN..."
su - $BENCH_USER -c "
    cd /home/$BENCH_USER/$BENCH_DIR
    if [ ! -d 'sites/$SITE_DOMAIN' ]; then
        bench new-site $SITE_DOMAIN \
            --db-root-password '$DB_ROOT_PASSWORD' \
            --admin-password '$ADMIN_PASSWORD' \
            --install-app erpnext
    else
        echo 'Site already exists, skipping creation'
    fi
    bench --site $SITE_DOMAIN install-app hrms 2>/dev/null || true
    bench use $SITE_DOMAIN
"

# ─── Step 12: Configure production ───────────────────────────────────────────
log "Setting up production (Nginx + Supervisor)..."
su - $BENCH_USER -c "
    cd /home/$BENCH_USER/$BENCH_DIR
    bench set-config -g dns_multitenant 1
    bench config http_timeout 120
"

# Setup Supervisor and Nginx
cd /home/$BENCH_USER/$BENCH_DIR
bench setup supervisor --yes
bench setup nginx --yes

# Link config files
ln -sf /home/$BENCH_USER/$BENCH_DIR/config/supervisor.conf /etc/supervisor/conf.d/frappe-bench.conf
ln -sf /home/$BENCH_USER/$BENCH_DIR/config/nginx.conf /etc/nginx/conf.d/frappe-bench.conf

# Remove default nginx site if it conflicts
rm -f /etc/nginx/sites-enabled/default

# Test and reload
nginx -t && systemctl reload nginx
supervisorctl reread
supervisorctl update

log "Enabling services on boot..."
systemctl enable supervisor
systemctl enable nginx
systemctl enable redis-server
systemctl enable mariadb

# ─── Step 13: SSL via Let's Encrypt ──────────────────────────────────────────
if ! $SKIP_SSL; then
    if [[ -n "$LETSENCRYPT_EMAIL" ]]; then
        log "Setting up SSL with Let's Encrypt..."
        certbot --nginx -d "$SITE_DOMAIN" --non-interactive --agree-tos --email "$LETSENCRYPT_EMAIL" --redirect
        log "SSL certificate installed!"

        # Auto-renewal cron
        (crontab -l 2>/dev/null; echo "0 2 * * * /usr/bin/certbot renew --quiet") | crontab -
        log "SSL auto-renewal configured (daily at 2 AM)"
    else
        warn "Skipping SSL — no --email provided for Let's Encrypt"
        warn "Run later: sudo certbot --nginx -d $SITE_DOMAIN --email admin@example.com"
    fi
else
    warn "SSL setup skipped (--skip-ssl flag)"
fi

# ─── Step 14: Basic security hardening ───────────────────────────────────────
log "Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# ─── Step 15: Set production mode on bench ───────────────────────────────────
log "Enabling production mode..."
su - $BENCH_USER -c "
    cd /home/$BENCH_USER/$BENCH_DIR
    bench set-config -g developer_mode 0
    bench set-config -g maintenance_mode 0
    bench --site $SITE_DOMAIN set-config mute_emails 0
    bench clear-cache
"

supervisorctl restart all

# ─── Done ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              Installation Complete!                         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                            ║"
echo "║  Site URL:     http://$SITE_DOMAIN"
if ! $SKIP_SSL && [[ -n "$LETSENCRYPT_EMAIL" ]]; then
echo "║  Secure URL:   https://$SITE_DOMAIN"
fi
echo "║                                                            ║"
echo "║  Login:        Administrator                               ║"
echo "║  Password:     (the --admin-password you provided)         ║"
echo "║                                                            ║"
echo "║  Bench path:   /home/$BENCH_USER/$BENCH_DIR"
echo "║  Bench user:   $BENCH_USER                                ║"
echo "║                                                            ║"
echo "║  Useful commands (run as '$BENCH_USER' user):              ║"
echo "║    su - $BENCH_USER"
echo "║    cd $BENCH_DIR"
echo "║    bench --site $SITE_DOMAIN migrate"
echo "║    bench --site $SITE_DOMAIN console"
echo "║    bench update                                            ║"
echo "║    bench --site $SITE_DOMAIN backup                       ║"
echo "║    supervisorctl status                                    ║"
echo "║                                                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "If you see any errors above, check the logs:"
echo "  /home/$BENCH_USER/$BENCH_DIR/logs/"
echo "  /var/log/supervisor/"
echo "  /var/log/nginx/"
echo ""