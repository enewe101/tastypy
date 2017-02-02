# Define Exceptions for this module
class PersistentOrderedDictException(Exception):
	pass
class DuplicateKeyError(PersistentOrderedDictException):
	pass
class PersistentOrderedDictIntegrityError(PersistentOrderedDictException):
	pass
class CalledClosedTrackerError(PersistentOrderedDictException):
	pass




