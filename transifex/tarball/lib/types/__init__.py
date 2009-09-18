def need_codebase(fn):
    def codebase_fn(self, *args, **kw):
        if not self.codebase:
            self.init_codebase()
        return fn(self, *args, **kw)
    return codebase_fn
