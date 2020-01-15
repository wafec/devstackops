## Helpers for Testing OpenStack using Devstack

OpenStack is a cloud management system and is used to manage resources like storage, images, processors, and RAMs. It virtualizes these resources oferring to users to create its own instances (virtual computers).

We are testing OpenStack using its services. In our tests, we simulate the services serving wrong inputs and outputs to their dependencies. For instance, suppose that service A depends on service B and service B is faulty, what happens to service A in case of a failure? We know that OpenStack has many services that are visible to users, and also it has many services (subservices) which are not visible to users. One example is the conductor service, that is part of the services of Nova (in other words, the Compute service of OpenStack).

To start testing OpenStack we need some steps to go before. So, this guide documents the steps and the helpers (scripts or binaries) that helped us to prepare OpenStack for our tests.

### Understanding the Environment 

We are using a machine with 22GB RAM and a SSD with 480GB. We created an Ubuntu 18.04 LTS instance as the base for the creation of the others instances we need for our tests. Controller instance we set with 8GB RAM and 2 processors, 2 Compute hosts with 4GB RAM each and 2 processors, and a client virtual machine with 2GB and 2 processors. Of course, the physical machine where these virtual machines are on haven't 8 processors. VirtualBox was used to create the virtual machines, and it virtualizes the resources, the storage, RAM and processors. Virtual machines were connected using a virtual network created by virtual box and all were connected to the internet. 
