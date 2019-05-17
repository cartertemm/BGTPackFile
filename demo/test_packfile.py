import os
import sys
sys.path.append("..")
import pack_file
sys.path.remove("..")


p=pack_file.pack_file()
if not os.path.isfile("pack.dat"):
	print("Non-existent pack.dat. Creating one...")
	p.create("pack.dat")
	p.add_file("test1.txt", "t1")
	p.add_file("test2.txt", "t2")
	p.close()
else:
	p.open("pack.dat")
	print(f"number of files: {p.file_count}")
	for i in p.list_files():
		print(i)
