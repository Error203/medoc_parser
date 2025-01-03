#!/usr/bin/python3
import requests
import bs4
import qlogger
import os
import argparse
import time

ap = argparse.ArgumentParser(description="script for parsing medoc.ua for new versions")

ap.add_argument("-v", "--verbose", action="store_true", help="for debugging")
ap.add_argument("-n", "--nocolor", action="store_false", help="disable coloring")
ap.add_argument("-D", "--daemon", action="store_true", help="start a daemon with interval")
ap.add_argument("-i", "--interval", type=int, default=3600, help="set interval to parse a site in seconds, default: once an hour (3600)")
ap.add_argument("-V", "--set-version", type=str, help="set initial version to write to a file to compare with")

args = ap.parse_args()

level = "verbose" if args.verbose else "info"
color = args.nocolor


class FileHandler:
	# to work with file stuff
	def __init__(self):
		self.version_file = "version"
		self.log = qlogger.Logger(level=level, color=color).get_logger("FileHandler")

		if self.version_file in os.listdir("."):
			self.overwrite()

		else:
			self.create_file()


	def overwrite(self):
		if os.path.isdir(self.version_file):
			self.log.warning("%s is a directory, removing and creating a file" % self.version_file)
			os.removedirs(self.version_file)

			self.create_file()


	def set_version(self, version):
		with open(self.version_file, "w") as file:
			file.write(version)


	def read_version(self):
		with open(self.version_file, "r") as file:
			return file.read()
			

	def create_file(self):
			
		with open(self.version_file, "w") as file:
			file.write("")

	
	def write(self, version):
		if not version:
			if args.set_version:
				self.log.info("setting version to: %s" % args.set_version)
				self.set_version(args.set_version)
				# fetch for version
			else:
				version = Parser().get_version()
				self.log.info("automatically setting 'version' file to: %s" % version)
				self.set_version(version)

		else:
			self.set_version(version)


	def read(self):
		try:

			version = self.read_version()

			if not version:
				self.write(None)

			return self.read_version()

		except Exception as e:

			self.log.exception(e)


class Parser:


	def __init__(self):
		self.medoc_page = "https://medoc.ua/download"
		self.headers = {
		"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4703.0 Safari/537.36",
		}
		self.log = qlogger.Logger(level=level, color=color).get_logger("Parser")


	def parse_version(self, page):
		soup = bs4.BeautifulSoup(page, "html.parser")
		spans = soup.find_all("span", {"class": "js-update-num"})

		self.version = spans[0].text


	def get_version(self):
		page = requests.get(self.medoc_page)
		self.log.debug("status code: %d" % page.status_code)

		if page.status_code == 200:
			self.parse_version(page.content)

			return self.version


class Daemon:
	# daemon that will compare versions and execute functions
	def __init__(self, interval, function):
		self.interval = interval
		self.function = function # function to execute when version from site differs from the one that's in the 'version' file
		self.fh = FileHandler()
		self.parser = Parser()
		self.log = qlogger.Logger(level=level, color=color).get_logger("Daemon")

		self.log.debug("interval is set to: %d" % interval)


	def start(self):

		try:

			while True:
				version = self.parser.get_version()
				local_version = self.fh.read().strip()
				if local_version != version:
					self.log.debug("found difference: (local ver) %s vs. (online ver) %s" % (local_version, version))
					self.fh.write(version)

					self.function()
				
				time.sleep(self.interval)

		except KeyboardInterrupt:

			self.log.info("\rinterrupted by user")

			exit()


def test_func():
	print("<test_func>")


def main():
	d = Daemon(args.interval, test_func)
	d.start()


if __name__ == '__main__':
	main()
