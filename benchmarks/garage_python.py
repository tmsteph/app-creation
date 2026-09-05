from dataclasses import dataclass


@dataclass
class Customer:
    name: str
    email: str
    status: str = "lead"


def customer_created(runtime, customer):
    runtime.action("send welcome email", customer)
    runtime.action("notify sales", customer)


def payment_succeeds(runtime, customer):
    customer.status = "client"
    runtime.action("create project", customer)
