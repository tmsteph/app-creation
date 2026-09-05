import unittest

from compiler import HumanSyntaxError, compile_source


SOURCE = '''\
app GarageCRM

data Customer:
    name
    email
    status = "lead"

when Customer is created:
    send welcome email
    notify sales

when payment succeeds:
    Customer.status = "client"
    create project
'''


class CompilerTests(unittest.TestCase):
    def test_compiled_program_runs(self):
        namespace = {}
        exec(compile_source(SOURCE), namespace)
        customer = namespace["Customer"]("Ada", "ada@example.com")
        runtime = namespace["emit"]("Customer is created", Customer=customer)
        self.assertEqual([a["action"] for a in runtime.actions], ["send welcome email", "notify sales"])
        namespace["emit"]("payment succeeds", runtime=runtime, Customer=customer)
        self.assertEqual(customer.status, "client")
        self.assertEqual(runtime.actions[-1]["action"], "create project")

    def test_bad_indentation_is_rejected(self):
        with self.assertRaises(HumanSyntaxError):
            compile_source("app Demo\nwhen go:\n  do thing\n")


if __name__ == "__main__":
    unittest.main()
