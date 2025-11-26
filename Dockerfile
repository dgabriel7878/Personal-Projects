FROM nginx:alpine

# Copy all files from current directory to nginx's default serving directory
COPY . /usr/share/nginx/html/

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
