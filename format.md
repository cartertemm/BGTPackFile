The following describes my rough understanding of the BGT pack_file algorithm, missing information in all.

# Notes

* I'm not completely sure of everything listed here. These are merely the results of examination through hex editing and a bit of guessing. Using the information found here along with a file or two, one should have enough to recreate the algorithm if they wish.
* Byteorder is little-endian
* An unsigned int is four bytes

# Format

* SFPv: initial header
* uint representing something, starts with 0x1. I guess version number.
* int representing number of files in pack
* four nulls
* SFPv again representing beginning of data
* uint representing length of internal name.
* four nulls
* uint representing length of content.
* Seeking to (nameLength + content length) far forward will get you to the end, this much+1 is either end of data ("") or on to the next file.
* start back at the second SFPv, beginning of data if there is another file
