#!/bin/bash

# Output the connection string to a configuration file
echo "connectionString: \"$MONGO_CONN_STR\"" > /docker-entrypoint-initdb.d/connection-string.conf

# Output a success message
echo "Connection string configured successfully!"
