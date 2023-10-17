#!/bin/bash

# Navigate to the frontend directory
cd ../frontend

# Run the npm build command
npm run build

# Move the dist folder to the static folder in the backend
mv ./dist/* ../backend/static/

# Delete the dist folder in the frontend directory
rm -rf dist

echo "Build and move completed!"