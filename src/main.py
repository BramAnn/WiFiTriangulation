import sys, argparse, socket
from locater import Locator


def main(args):
	lengthArgs = len(args)
	if lengthArgs == 0:
		locator = Locator()
	elif lengthArgs == 3:
		aps = [str(args[0]), str(args[1]), str(args[2])]
		locator = Locator(aps)

	else:
		print("for custom AP's please provide 3 BSSIDs")
		print("no arguments will use 3 default BSSIDs", flush=True)
		sys.exit(2)

	locator.start()
	sys.exit(1)


if __name__ == "__main__":
	main(sys.argv[1:])