import json
import re


def tuplify_lists(obj):
	if isinstance(obj, list):
		for i, element in enumerate(obj):
			obj[i] = tuplify_lists(element)
		obj = tuple(obj)
	return obj



class JSONSerializer(object):
	"""
	Uses the builtin `json` package to create and read textual entries in the
	file format used by PersistentOrderedDict and its derivatives.
	"""

	_ESCAPE_TAB_PATTERN = re.compile('\t')
	_UNESCAPE_TAB_PATTERN = re.compile(r'(?P<prefix>^|[^\\])\\t')
	_ESCAPE_SLASH_PATTERN = re.compile(r'\\')
	_UNESCAPE_SLASH_PATTERN = re.compile(r'\\\\')

	@classmethod
	def read_items(cls, lines):
		# Yield entries deserialized from a file.
		for line in lines:

			# skip blank lines
			if line=='':
				continue

			# Deserialize one key-value pair per line
			serialized_key, serialized_value = line[:-1].split('\t', 1)
			key = cls.deserialize_key(serialized_key)
			value = cls.deserialize_value(serialized_value)

			yield key, value


	@classmethod
	def dump_items(cls, items):
		for key, value in items:
			serialized_key = cls.serialize_key(key)
			serialized_value = cls.serialize_value(value)
			yield '%s\t%s\n' % (serialized_key, serialized_value)


	@classmethod
	def serialize_key(cls, key, recursed=False):

		# Recursively ensure that strings are encoded
		if isinstance(key, tuple):
			temp_key = []
			for item in key:
				temp_key.append(serialize_key(item, recursed=True))
			key = tuple(temp_key)

		# Base call for recursion
		elif isinstance(key, basestring):
			key = key.encode('utf8')

		# Do the actual serialization in the root call
		if not recursed:
			key = json.dumps(key)
			key = cls._ESCAPE_SLASH_PATTERN.sub(r'\\\\', key)
			key = cls._ESCAPE_TAB_PATTERN.sub(r'\\t', key)

		return key


	@classmethod
	def deserialize_key(cls, serialized_key):
		key = cls._UNESCAPE_TAB_PATTERN.sub('\g<prefix>\t', serialized_key)
		key = cls._UNESCAPE_SLASH_PATTERN.sub(r'\\', key)
		key = json.loads(key)
		key = tuplify_lists(key)
		return key


	@classmethod
	def serialize_value(cls, value):
		return json.dumps(value)


	@classmethod
	def deserialize_value(cls, serialized_value):
		return json.loads(serialized_value)

