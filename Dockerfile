FROM registry.gitlab.com/portcitiesidealis/odoo-enterprise:18.0

USER root
COPY --chown=odoo:odoo ./entrypoint.sh /init.sh
COPY --chown=odoo:odoo ./odoo.conf /etc/odoo/odoo.conf
RUN chmod +x /init.sh

# Install system dependencies for pyodbc
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        libreoffice-calc \
        fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --break-system-packages -r /tmp/requirements.txt

# Fix permissions for Odoo data directory and sessions
RUN mkdir -p /var/lib/odoo/sessions && \
    chown -R odoo:odoo /var/lib/odoo && \
    chmod -R 755 /var/lib/odoo

# RUN pip install a2wsgi starlette fastapi

USER odoo

ENTRYPOINT ["/init.sh"]
