# DJ-Speedwagon
A simple youtube-dl driven python music bot.

To run the script you need to install some pyhton libraries (listed on the top of the ```bot.py``` file) and the ```ffmpeg``` binary.
Create a new bot on the Discord Developer Portal, fetch Key onto the ```.env``` file and you're ready to go.

## Commands:

Currently supported commands are:

``` .play url \ file```: Downloads the given url and adds the file to the queue (beware of the download time) or searches the top directory for files with matching names and adds them to the queue.

``` .fs .skip ```: Skips the song.

``` .repeat ```: Puts the current song on repeat.

``` .prd ```: Appends ALL downloaded songs onto the queue.

