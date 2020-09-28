FatJira
=======

This is a fat Jira client inspired by:
- How SLOW it is to use a thin web client to find an issue and log some work.
- How fast incremental search is AWESOME and changes your way of doing things
  (like fzf, helm, ivy).
- How keyboard based interfaces can be discoverable for beginners and
  muscle-memory building for advanced users (like magit).
- How switching to a browser to find an issue can be distracting and time
  consuming (and how a simple CLI is still insufficient).

If you've never used incremental search, for eg. in Emacs with Helm/Ivy to
search through commands, buffers, file names, file contents (ripgrep) you might
not appreciate fatjira.

I want to find and alter the issue as fast and effortlessly as I can commit
code, move the commit to a feature branch (because I forgot earlier), amend it
(cause I forgot to include a changelog) and push it in Magit.

TODO: ttygif with censored issues.

State and benchmarks
--------------------

Work in progress. :P And I probably won't be able to push it to be useful by
myself (time :/), but maybe showcasing the concept will inspire someone? Pretty
please?

Testing with 5500 jira issues, each loaded with 333 custom fields (not filtered
yet). Current PoC searches them by 6 fields in unnoticeable time even in a
synchronous way. It does take 400MB RAM and loading from disc takes around 2
seconds. On disc, local cache takes 110MB. Synchronisation (depends on many
factors) of local cache takes around 10 minutes, and further daily resync up to
30 seconds (most time was taken by logging in).

I considered combining it with orgassist project as it scratches a similar itch.


Usage
-----

Currently from the GIT, no install over PIP available
