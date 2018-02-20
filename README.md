Thycotic Secret Server Ansible lookup plugin
============================================

Description
-----------

A custom Ansible lookup plugin to retrieve secret information from Thycotic Secret Server via the REST API.

It currently supports retrieving the following secret information:
- id
- username
- password
- notes

More information about Thycotic Secret Server can be found on their website: https://thycotic.com/products/secret-server/

Dependencies
------------

Ansible 2.x

Python libraries:
- os
- sys
- urlparse
- json
- requests

Usage
-----

The syntax for looking up specific secret information is

```
lookup('secretserver', '<secret_name>.<type>')
```

**Example usage playbook:**

```
- hosts: local
  vars:
    searchitems:
      - my_first_secret_name
      - my_second_secret_name
  tasks:
    - debug: msg="id:       {{ lookup('secretserver', 'my_secret_name.id') }}"
    - debug: msg="username: {{ lookup('secretserver', 'my_secret_name.username') }}"
    - debug: msg="password: {{ lookup('secretserver', 'my_secret_name.password') }}"
    - debug: msg="notes:    {{ lookup('secretserver', 'my_secret_name.notes') }}"
```

License Information
-------------------

This plugin was created by [Sven meeus](https://framed.be/)

The MIT License (MIT)

Copyright (c) 2018 [Sven Meeus / Framed](https://framed.be/)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
