# BGT pack_file

A full-featured python implementation of the BGT pack_file algorithm

## What?

Those who have ever played with [the blastbay game toolkit](https://www.blastbay.com/bgt.php) have undoubtedly seen or heard of the pack_file object.
From the docs:

> The pack_file object is used to package several files into one.
> A pack file is generally useful if you have a lot of files that you wish to distribute as one file on disk. This most commonly applies to sounds, but can include other data such as game level layouts etc.

This is my attempt to pythonically mirror the format in it's entirety. While precise information from the author has never been published, a bit of guessing and fooling around was enough to figure it out. If you're interested, have a look at [my notes on the format](https://github.com/cartertemm/BGTPackFile/blob/master/format.md)

## Why?

I was bored and happened to have a couple packs lying around.

## Usage

I've made sure to keep the API's entirely identical, that way those familiar with it's use can jump right in if they wish. For those that aren't, the code has been thoroughly commented.

Suppose you have files named music1.ogg, music2.ogg and music3.ogg located in your current working directory. Throwing them into one is as simple as

```
import pack_file

p=pack_file.pack_file()
p.create("music.dat")
p.add_file("music1.ogg", "m1")
p.add_file("music2.ogg", "m2")
p.add_file("music3.ogg", "m3")
```

And to work with each file:

```
import pack_file

p=pack_file.pack_file()
p.open("music.dat")
#extract to disk
p.extract_file("m1", "music1_from_pack.ogg")
#music1.ogg and music1_from_pack.ogg should now be completely identical
#Or to get a file object with data stored in memory
obj=p.get_file("m1")
#from here you can perform standard I/O calls on obj
content=obj.read()
obj.seek(0)
#etc etc
```

## notes

This was a product stemming from complete bordom. As a result, little more than minimal testing has been performed to ensure cross compatibility and full functionality.
My point here is merely a simple demonstration. If you make improvements, feel free to submit a pull request. If you find an issue, please do let me know either through email or the issue tracker. I certainly care about bug fixes and enhancements. That being said, I won't be making frequent updates by any stretch of the imagination.
In short, milage may very if you do happen to try imbedding such a POC in your application. I'm not to be held responsible if something blows up.
