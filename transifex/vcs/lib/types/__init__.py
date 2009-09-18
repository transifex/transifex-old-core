def need_repo(fn):
    def repo_fn(self, *args, **kw):
        try:
            self.repo
        except AttributeError:
            self.init_repo()
        return fn(self, *args, **kw)
    return repo_fn
