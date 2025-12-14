import typer
import csv
import datetime
from typing import Literal
from rich.progress import track
import time

app = typer.Typer()
orders_file = "orders.csv"
fieldnames = ["customer", "size", "order_time", "password"]

# Admin password for printing and deleting orders
ADMIN_PASSWORD = "ADMIN092111"


def write_order(data: dict):
    with open(orders_file, "a", newline="") as f:
        csvwriter = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell() == 0:
            csvwriter.writeheader()
        csvwriter.writerow(data)


def read_orders() -> list[dict]:
    try:
        with open(orders_file, newline="") as f:
            reader = csv.DictReader(f)
            orders = []
            for row in reader:
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None}
                orders.append(clean_row)
            return orders
    except FileNotFoundError:
        return []


@app.command(no_args_is_help=True)
def create(
    customer: str,
    password: str,  # required argument
    size: Literal["small", "medium", "large"] = "medium"
):
    """Create a new order with a password."""
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
            "password": password
        }
    )
    print(f"✅ Order for {customer} created!")


@app.command()
def cancel(customer: str, password: str):
    """Cancel an order by customer name and password (order password or admin password)."""
    orders = read_orders()
    customer_orders = [o for o in orders if o["customer"] == customer]

    if not customer_orders:
        print(f"No orders found for {customer}.")
        raise typer.Exit()

    # Cancel the first order that matches either the order's password or the admin password
    order_to_cancel = next(
        (o for o in customer_orders if o.get("password") == password or password == ADMIN_PASSWORD),
        None
    )

    if not order_to_cancel:
        print("❌ No order matches the provided password!")
        raise typer.Exit()

    # Remove the order
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
def print_orders(admin_password: str = typer.Argument(None)):
    """Print all orders. Optionally provide admin password to see order passwords."""
    orders = read_orders()
    if not orders:
        print("No orders found.")
        return

    show_passwords = False
    if admin_password == ADMIN_PASSWORD:
        show_passwords = True
    elif admin_password is not None:
        print("❌ Incorrect admin password! Showing orders without passwords.")

    print("All orders:")
    for order in orders:
        if show_passwords:
            print(f"{order['customer']} | {order['size']} | {order['order_time']} | {order['password']}")
        else:
            print(f"{order['customer']} | {order['size']} | {order['order_time']}")


# ============================================================================

if __name__ == "__main__":
    app()
