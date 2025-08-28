# Use a simple Alpine base and install nginx manually to avoid user creation issues
FROM alpine:3.18

# Install nginx and required packages
RUN apk add --no-cache nginx wget

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Create required directories for nginx
RUN mkdir -p /var/log/nginx /var/cache/nginx /var/tmp/nginx /var/run/nginx /usr/share/nginx/html \
    /var/lib/nginx /var/lib/nginx/logs /var/lib/nginx/tmp /var/lib/nginx/tmp/client_body \
    /var/lib/nginx/tmp/proxy /var/lib/nginx/tmp/fastcgi /var/lib/nginx/tmp/uwsgi \
    /var/lib/nginx/tmp/scgi

# Copy static files
COPY . /usr/share/nginx/html/

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# OpenShift compatibility: Set proper permissions for arbitrary user IDs
RUN chgrp -R 0 /var/log/nginx /var/cache/nginx /var/tmp/nginx /var/run/nginx /usr/share/nginx/html /etc/nginx /var/lib/nginx && \
    chmod -R g+rwX /var/log/nginx /var/cache/nginx /var/tmp/nginx /var/run/nginx /usr/share/nginx/html /etc/nginx /var/lib/nginx && \
    touch /var/run/nginx/nginx.pid && \
    chmod g+rwx /var/run/nginx/nginx.pid

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
