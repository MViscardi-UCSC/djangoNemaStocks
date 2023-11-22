"""
Converters for URL patterns in my djangoNemaStocks project.

This is taken from chatGPT as a way to convert the WJA number from a string to an integer.
"""

class WJAConverter:
    regex = r'\d+'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return '%04d' % value