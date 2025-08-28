# Use nginx alpine for small size and efficiency
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy static files
COPY . /usr/share/nginx/html/

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# OpenShift compatibility: Set permissions for arbitrary user IDs
# OpenShift runs containers with random user IDs, so we need to make directories writable by group
RUN chmod -R g+rwx /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html /etc/nginx/conf.d && \
    chmod g+rwx /var/cache/nginx /var/run /var/log/nginx

# Create nginx.pid file and make it writable
RUN touch /var/run/nginx.pid && \
    chmod g+rwx /var/run/nginx.pid

# Make the nginx user part of root group (OpenShift requirement)
RUN chgrp -R 0 /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html /etc/nginx/conf.d && \
    chmod -R g+rwX /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html /etc/nginx/conf.d

# OpenShift runs with arbitrary user IDs, so we don't specify a USER
# The container will run with whatever user ID OpenShift assigns

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
