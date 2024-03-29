# Mind Implementation

## Implementation goals: KISS (Keep It Simple Stupid)
1. *Small*. Goal is under one thousand lines of Python.
2. *Simple*. Installation involves copying a single file.
3. *Robust*. No dependencies outside the standard library.
 
## Lifecycle of stuff

```
    Operation   Old State       New State
    add         BLANK(-1)       -> ACTIVE(0)
    tick        ACTIVE(0)       -> DONE(1)
    forget      ACTIVE(0)       -> FORGOTTEN(2)
    untick      TICKED(1)       -> ACTIVE(0)
    restore     FORGOTTEN(2)    -> ACTIVE(0)
    purge?      FORGOTEN(2)     -> BLANK(-1)
```

## Dealing with Integrity Errors
These shouldn't happen if everything is transactional.

A potential solution is to delete the latest entry in the log. If the error
is occurring on the latest entry in the log, you can try to delete it.

First, make a backup copy of the db.

To get the latest log entry:
```sql
SELECT * FROM log ORDER BY sn DESC LIMIT 1;
```
To delete it:
```sql
DELETE FROM log WHERE sn = {num};
```


## SQLite things

### Avoiding extra rowid column
> Rowid tables are distinguished by the fact that they all have a unique,
> non-NULL, signed 64-bit integer rowid that is used as the access key for the
> data in the underlying B-tree storage engine.
>    [sqlite.org](https://www.sqlite.org/rowidtable.html)

Based on my testing, SQLite will alias `a` to `rowid` column even if you do
either of:
```sqlite
CREATE TABLE t1(a INTEGER NOT NULL, b TEXT, PRIMARY KEY (a));
CREATE TABLE t1(a INTEGER PRIMARY KEY, b TEXT);
```