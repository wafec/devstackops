## Helpers for Testing OpenStack using Devstack

OpenStack is a cloud management system and is used to manage resources like storage, images, processors, and RAMs. It virtualizes these resources oferring to users to create its own instances (virtual computers).

We are testing OpenStack using its services. In our tests, we simulate the services serving wrong inputs and outputs to their dependencies. For instance, suppose that service A depends on service B and service B is faulty, what happens to service A in case of a failure? We know that OpenStack has many services that are visible to users, and also it has many services (subservices) which are not visible to users. One example is the conductor service, that is part of the services of Nova (in other words, the Compute service of OpenStack).

To start testing OpenStack we need some steps to go before. So, this guide documents the steps and the helpers (scripts or binaries) that helped us to prepare OpenStack for our tests.

### Understanding the Environment 

