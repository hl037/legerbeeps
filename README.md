# LEGERBEEPS
This tool has been developped to generate audio tracks for the Léger test (and derivates) to estimate the maximal aerobic speed.

# Description
Provided with recording of the level advancement annoucement audio samples, the intermediate time annoucements (15s, 30s, 45s etc.), and an introduction, it ca generate a full track with the beeps.

Everything is customizable to allow further research (distance between the markers, duration of a level, speed increment between levels, length of the beeps etc.).

In addition to generate the .wav audio output, it also prints the table of all the beeps of the sample, their timestamp in the recording, and the speed associated.


It is also easily extansible to generate other kind of recording (for example interval training audio track) even though other specific algorithm are not implemented.


The defaults of the cli correspound to the official VAMEVAL test.

# State of development

Most feature seems OK, but I want to add unit tests before v1.0

You should check the output recording with Audacity

# Documentation

Thiw is also a work in progress before v1.0

For now, install it and run the cli (`legerbeep` without argument to get a list of the params).

...Or check the source. Some functions are not implemented in a very clean way, but the overall architecture is clean enougth to remain legible and being maintainable.

If you have questions, don't hesitate to open a ticket on github.

I will be espcially happy to help if you are a researcher and have special needs.
