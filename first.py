import csv
import datetime
import time
from typing import Literal

import typer
from rich.progress import track


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

app = typer.Typer()
orders_file = "orders.csv"
fieldnames = ["customer", "size", "order_time", "password"]

# Admin password for printing and deleting orders
ADMIN_PASSWORD = "ADMIN092111"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def write_order(data: dict) -> None:
    """Append an order to the CSV file, writing a header when creating the file."""
    with open(orders_file, "a", newline="") as f:
        csvwriter = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell() == 0:
            csvwriter.writeheader()
        csvwriter.writerow(data)


def read_orders() -> list[dict]:
    """Read all orders from the CSV and return a list of cleaned dicts.

    Keys and values are stripped of surrounding whitespace to be robust
    against malformed CSV headers or user edits.
    """
    try:
        with open(orders_file, newline="") as f:
            reader = csv.DictReader(f)
            orders: list[dict] = []
            for row in reader:
                clean_row = {k.strip(): (v.strip() if v is not None else "") for k, v in row.items() if k is not None}
                orders.append(clean_row)
            return orders
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


@app.command(no_args_is_help=True)
def create(
    customer: str,
    password: str,
    size: Literal["small", "medium", "large"] = "medium",
) -> None:
    """Create a new order and save it to the CSV.

    Args:
        customer: Customer name
        password: Order password used for cancellations
        size: Pizza size
    """
    current = datetime.datetime.now()
    current_time = f"{current:%H:%M}"

    print(f"Hello {customer}")
    for _ in track(range(100)):
        time.sleep(0.001)

    write_order(
        data={
            "customer": customer,
            "size": size,
            "order_time": current_time,
            "password": password,
        }
    )
    print(f"✅ Order for {customer} created!")


@app.command()
def cancel(customer: str, password: str) -> None:
    """Cancel an order by matching customer and password (or admin password)."""
    orders = read_orders()
    customer_orders = [o for o in orders if o.get("customer") == customer]

    if not customer_orders:
        print(f"No orders found for {customer}.")
        raise typer.Exit()

    # Find the first matching order by password or allow admin override
    order_to_cancel = next(
        (o for o in customer_orders if o.get("password") == password or password == ADMIN_PASSWORD),
        None,
    )

    if not order_to_cancel:
        print("❌ No order matches the provided password!")
        raise typer.Exit()

    remaining = [o for o in orders if o != order_to_cancel]
    with open(orders_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining)

    if password == ADMIN_PASSWORD:
        print(f"✅ Order for {customer} deleted by admin!")
    else:
        print(f"✅ Order for {customer} cancelled!")


@app.command()
def print_orders(admin_password: str = typer.Argument(None)) -> None:
    """Display stored orders. Providing the admin password shows order passwords."""
    orders = read_orders()
    if not orders:
        print("No orders found.")
        return

    show_passwords = admin_password == ADMIN_PASSWORD
    if admin_password is not None and not show_passwords:
        print("❌ Incorrect admin password! Showing orders without passwords.")

    print("All orders:")
    for order in orders:
        if show_passwords:
            print(f"{order.get('customer','')} | {order.get('size','')} | {order.get('order_time','')} | {order.get('password','')}")
        else:
            print(f"{order.get('customer','')} | {order.get('size','')} | {order.get('order_time','')}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
