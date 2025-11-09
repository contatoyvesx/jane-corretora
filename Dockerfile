# Use a lightweight NGINX image to serve the static site
FROM nginx:stable-alpine

# Copy static assets to the NGINX html directory
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css

# Expose the default HTTP port
EXPOSE 80

# Start NGINX (default CMD provided by base image)
