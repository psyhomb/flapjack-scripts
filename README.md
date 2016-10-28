flapjack scripts
================

  - Added flapjack-sched-maint.py script


About
-----

`flapjack-sched-maint.py`

  - Used to create/delete schedule maintenance periods


Requirements
------------

`flapjack-sched-maint.py`

  - `requests` module


Usage
-----

`flapjack-sched-maint.py`

  Create schedule maintenance period which begins at 17:00 on 24.10.2016 that will last for one hour (3600s) for all hosts with `CPU` check, reason `weekly maintenance`
  ```
  flapjack-sched-maint.py -c cpu -d 3600 -t '2016-10-24T17:00:00' -S 'weekly maintenance'
  ```

  Create schedule maintenance period which begins at 17:00 on 24.10.2016 that will last for one hour (3600s) for hosts test1.example.com and test2.example.com with `CPU` and `Memory` checks, reason `weekly maintenance`
  ```
  flapjack-sched-maint.py -c cpu,memory -d 3600 -e test1.example.com,test2.example.com -t '2016-10-24T17:00:00' -S 'weekly maintenance'
  ```

  Create schedule maintenance period on host basis that will be activated instantly (now) and it will last for a week
  ```
  flapjack-sched-maint.py -d 604800 -e test1.example.com -S 'weekly maintenance'
  ```

  Delete schedule maintenance period that was created on 2016-10-24T17:00:00 (`--star-time` is used as a primary key in this case)
  ```
  flapjack-sched-maint.py -c cpu,memory -e test1.example.com,test2.example.com -D -t '2016-10-24T17:00:00'
  ```


License and Authors
-------------------
**Author**: Milos Buncic
