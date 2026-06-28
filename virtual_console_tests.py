import virtual_console

#import inspect

console = virtual_console.VirtualConsole(120, 25)

console.open(80, 25)

console.print("Hello, world!")

console.print("Hello, world!")

console.display()

console.close()

#print(f"\n\nScanning members for {console.__class__}")

#for name, value in inspect.getmembers(console):
#	if name.startswith("__"): continue

#	print(f"{name} = {value}")