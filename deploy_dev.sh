#!/bin/bash

COMIT_HASH=$1
export PYTHONPATH='/opt/odoo/odoo-server/'
running_user=$(whoami)
cd /opt/odoo/addons
echo "Run pipeline user: $running_user"
echo "Git Fetch latest changes - Odoo"
# git remote update
# git fetch
# echo "Git Checkout to $COMIT_HASH"
# git checkout $COMIT_HASH
git pull
DB=$(/opt/odoo/env/bin/python3 get_odoo_dbs.py)
echo "Stop Odoo"
sudo service odoo-server stop

# not optimised but easier to start - Need to change to exact module to install / update...
for db in ${DB[@]}; do
    echo "\n\n== Upgrading Odoo for DB: $db =="
    /opt/odoo/env/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo-server.conf -d $db -u tlip_base --no-http --stop-after-init --logfile /
done

echo "Restart Odoo"
sudo service odoo-server restart
