## How to Use

File *preparation.sh* contains the credentials and parameters of the RabbitMQ connection. It is important to ensure these parameters are correct.
User *stackrabbit* is the default user on Devstack. The *devstack-installation* directory has scripts to install our OpenStack instance. By default, it sets the RabbitMQ user password as *supersecret*.

1. **source** preparation.sh
2. ./bindings.sh
3. ./names.py
4. ./builder.py
5. ./bindings.sh
6. ./names.py
7. ./interceptor.py