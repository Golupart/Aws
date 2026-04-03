#!/bin/bash

# C engine compile karna
gcc net_driver.c -o sys_lib -lpthread

# Sirf existing files ko permission dena
chmod +x sys_lib setup.sh

echo "✅ PRIMEXARMY Engine is ready."
