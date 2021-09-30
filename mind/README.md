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
