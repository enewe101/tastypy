import operator

class DeepProxyMeta(type):
	def __new__(meta_class, class_name, class_parents, class_attrs):

		skip =  {
			'__class__', '__getattribute__', '__getitem__', '__subclasshook__'}

		# Builds the function to be used as a method, and binds it's name
		# to the method's scope.
		def arm_call_callback(method_name):
			def call_callback(self, *args, **kwargs):
				return self.method_callback(
					self.parent_keys, method_name, *args, **kwargs)
			return call_callback

		# Add all of the operator methods
		for method in dir(operator):
			if not method.startswith('__') or method in skip:
				continue
			class_attrs[method] = arm_call_callback(method)

		# Build the class normally
		return type(class_name, class_parents, class_attrs)


class DeepProxy(object):

	__metaclass__ = DeepProxyMeta

	def __init__(
		self, 
		#setitem_callback=None,
		method_callback=None,
		parent_keys=()
	):
		#self.setitem_callback = (
		#	setitem_callback or self.default_setitem_callback)
		self.method_callback = (
			method_callback or self.default_method_callback)
		self.parent_keys = parent_keys

	def default_setitem_callback(self, key_tuple, val):
		print key_tuple, '<--', val

	def default_method_callback(self, key_tuple, method, *args, **kwargs):
		print key_tuple, '.%s()'%method, args, kwargs
		return self

	def __getattr__(self, attr):
		def call_method_callback(*args, **kwargs):
			return_val = self.method_callback(
				self.parent_keys, attr, *args, **kwargs)
			return return_val
		return call_method_callback

	def __getitem__(self, key):
		return DeepProxy(
			#setitem_callback=self.setitem_callback,
			method_callback=self.method_callback,
			parent_keys=self.parent_keys + (key,)
		)

	#def __setitem__(self, key, val):
	#	print key_tuple, '<--', val
	#	self.setitem_callback(self.parent_keys + (key,), val)
	

