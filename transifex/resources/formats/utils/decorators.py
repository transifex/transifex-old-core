from transifex.resources.formats import FormatsError

def need_resource(fn):
    def resource_fn(self, *args, **kw):
        if not self.resource:
            raise FormatsError("Resource not specified.")
        return fn(self, *args, **kw)
    return resource_fn

def need_content(fn):
    def content_fn(self, *args, **kw):
        if self.content is None:
            raise FormatsError("No content given.")
        return fn(self, *args, **kw)
    return content_fn

def need_file(fn):
    def file_fn(self, *args, **kw):
        if not self.filename:
            raise FormatsError("File not specified.")
        return fn(self, *args, **kw)
    return file_fn

def need_language(fn):
    def language_fn(self, *args, **kw):
        if not self.language:
            raise FormatsError("Language not specified")
        return fn(self, *args, **kw)
    return language_fn

def need_stringset(fn):
    def stringset_fn(self, *args, **kw):
        if not self.stringset:
            raise FormatsError("No strings found. Either bind a resource or a file"
                " to load strings into the handler.")
        return fn(self, *args, **kw)
    return stringset_fn

def need_compiled(fn):
    def compiled_fn(self, *args, **kw):
        if not self.compiled_template:
            raise FormatsError("No template found. Use compile to generate the"
                 " template first")
        return fn(self, *args, **kw)
    return compiled_fn
