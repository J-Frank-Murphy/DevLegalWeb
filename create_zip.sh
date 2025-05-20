#!/bin/bash

# This script creates a zip file of the refactored Dev Legal website
# for easy download and deployment

# Create a temporary directory for the zip contents
mkdir -p /tmp/dev-legal-website-refactored

# Copy all files to the temporary directory
cp -r /home/ubuntu/dev_legal_refactor/* /tmp/dev-legal-website-refactored/

# Create empty directories for migrations and uploads if they don't exist
mkdir -p /tmp/dev-legal-website-refactored/migrations/versions
mkdir -p /tmp/dev-legal-website-refactored/src/static/uploads

# Add .gitkeep files to empty directories
touch /tmp/dev-legal-website-refactored/migrations/versions/.gitkeep
touch /tmp/dev-legal-website-refactored/src/static/uploads/.gitkeep

# Create the zip file
cd /tmp
zip -r /home/ubuntu/dev_legal_website/dev-legal-website-refactored.zip dev-legal-website-refactored

# Clean up
rm -rf /tmp/dev-legal-website-refactored

echo "Zip file created at /home/ubuntu/dev_legal_website/dev-legal-website-refactored.zip"
