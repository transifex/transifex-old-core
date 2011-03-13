def need_resource(fn):
    def resource_fn(self, *args, **kw):
        if not self.resource:
            raise Exception("Resource not specified.")
        return fn(self, *args, **kw)
    return resource_fn

def need_file(fn):
    def file_fn(self, *args, **kw):
        if not self.filename:
            raise Exception("File not specified.")
        return fn(self, *args, **kw)
    return file_fn

def need_language(fn):
    def language_fn(self, *args, **kw):
        if not self.language:
            raise Exception("Language not specified")
        return fn(self, *args, **kw)
    return language_fn

def need_stringset(fn):
    def stringset_fn(self, *args, **kw):
        if not self.stringset:
            raise Exception("No strings found. Either bind a resource or a file"
                " to load strings into the handler.")
        return fn(self, *args, **kw)
    return stringset_fn

def need_compiled(fn):
    def compiled_fn(self, *args, **kw):
        if not self.compiled_template:
            raise Exception("No template found. Use compile to generate the"
                 " template first")
        return fn(self, *args, **kw)
    return compiled_fn
