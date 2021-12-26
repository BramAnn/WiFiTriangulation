class Rectangle:
	n = 5.5
	name = "het kolenkot"
	lefttop, rightTop, leftBottom, rightBottom = 0, 0, 0, 0

	def __init__(self, name, n, leftTop, rightTop, leftBottom, rightBottom):
		self.n = n
		self.name = name
		self.leftTop = leftTop
		self.rightTop = rightTop
		self.leftBottom = leftBottom
		self.rightBottom = rightBottom

	def does_it_fit(self, x, y):
		itDoesFit = True
		if not (x >= self.leftTop[0] and x <= self.rightTop[0]):
			return False
		if not (y >= self.leftTop[1] and y <= self.leftBottom[1]):
			return False
		return itDoesFit

