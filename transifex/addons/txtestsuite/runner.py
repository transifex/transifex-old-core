from django.test.simple import DjangoTestSuiteRunner
from django.core import management

fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]

class TxTestSuiteRunner(DjangoTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        super(TxTestSuiteRunner, self).setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super(TxTestSuiteRunner, self).teardown_test_environment(**kwargs)

    def setup_databases(self, **kwargs):
        return_val = super(TxTestSuiteRunner, self).setup_databases(**kwargs)
        management.call_command('loaddata', *fixtures)
        return return_val

