#!/usr/bin/env bash

echo "DEBUG_FLAGS: $DEBUG_FLAGS"

export PATH="/var/lib/odoo/.local/bin:$PATH"
echo $PATH

INSTALL_MODULES=$(/mnt/extra-addons/get-modules-to-install.sh)
find /mnt/extra-addons/ -name 'requirements.txt' -exec echo {} \;
find /mnt/extra-addons/ -name 'requirements.txt' -exec pip3 install -r {} \;

/usr/bin/odoo --db_host $HOST --db_port 5432 --db_user $USER --db_password $PASSWORD -d erp --init $INSTALL_MODULES --update $INSTALL_MODULES --without-demo=all $DEBUG_FLAGS
