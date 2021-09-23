# Mind
Mind my thoughts.

## Idea
A 'stack-based' note-taking app.

In other words, things go on the stack, things come off the stack. Stuff that's
way down the stack will probably never be referenced again, but it's there!

  * Not a TODO app (no dates, no GTD).

## Requirements

### 1. Simple.
It must be immediately obvious how to use it.

Some example commands:

```
mind "#shopping beets"
mind "Bring the washing in when I get home!"
mind "#shopping carrots and celery"
mind "Call boss about the thing."
mind
 > 1. [ 1s ago...] -> Call boss about the thing.
 > 2. [ 3s ago...] -> #shopping carrots and celery
 > 3. [ 5s ago...] -> Bring the washing in when I get home!
 > 4. [10s ago...] -> #shopping beets

mind ls shopping
 > 1. carrots and celery
 > 2. beets

mind tick #shopping.2

mind forget #1
 > As you wish, "Call boss..." is gone!

mind
 > 1. [30s ago...] -> #shopping carrots and celery
 > 2. [38s ago...] -> Bring the washing in when I get home!

mind tick 2
 > Awesome! Archiving "Bring the washing in when I get home!"
```

### 2. Bring joy
For example, it replies "Good job!" when you complete something. It doesn't
make me look at all the tasks I never completed from 3 years ago!


### 3. Use anywhere (eventually).
* Offline mode (CLI) for Laptop.
* Web interface for Phone.

## Implementation
* SQLite as storage format.
* Try to keep it to one Python file?
* Markdown support?
* Python script initially.
* Web interface (eventually).
* Hashtags? @ symbol?

## Hair-brained schemes
* Ability to scan text (e.g. sticky notes).
* Connect to Chrome/Firefox bookmarks.
