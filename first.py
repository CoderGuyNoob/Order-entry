import typer
import csv
import datetime
from typing import Literal
from rich.progress import track
from rich.console import Console
from rich.table import Table
import time

app = typer.Typer()
console = Console()
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

    console.print(f"[bold green]Hello {customer}![/bold green]")
    for _ in track(range(100), description="Processing order..."):
        time.sleep(0.001)

    write_order(
        data={
            "customer": customer,
            "size": size,
            "order_time": current_time,
            "password": password
        }
    )
    console.print(f"[bold green]✅ Order for {customer} created![/bold green]")


@app.command()
def cancel(customer: str, password: str):
    """Cancel an order by customer name and password (order password or admin password)."""
    orders = read_orders()
    customer_orders = [(i, o) for i, o in enumerate(orders) if o["customer"] == customer]

    if not customer_orders:
        console.print(f"[bold red]No orders found for {customer}.[/bold red]")
        raise typer.Exit()

    # Filter orders matching the password or admin password
    matching_orders = [(idx, o) for idx, o in customer_orders if o.get("password") == password or password == ADMIN_PASSWORD]

    if not matching_orders:
        console.print("[bold red]❌ No order matches the provided password![/bold red]")
        raise typer.Exit()

    # If multiple matching orders, prompt user to select
    if len(matching_orders) > 1 and password != ADMIN_PASSWORD:
        console.print("[bold yellow]Multiple matching orders found:[/bold yellow]")
        for display_idx, (idx, order) in enumerate(matching_orders, start=1):
            console.print(f"{display_idx}: Size: {order['size']}, Time: {order['order_time']}")
        choice = typer.prompt("Enter the number of the order you want to cancel")
        try:
            selected_display_idx = int(choice) - 1
            order_idx, order_to_cancel = matching_orders[selected_display_idx]
        except (ValueError, IndexError):
            console.print("[bold red]Invalid selection. Exiting.[/bold red]")
            raise typer.Exit()
    else:
        order_idx, order_to_cancel = matching_orders[0]

    # Remove only the selected order using its index
    remaining = [o for i, o in enumerate(orders) if i != order_idx]
    with open(orders_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(remaining)

    if password == ADMIN_PASSWORD:
        console.print(f"[bold yellow]✅ Order for {customer} deleted by admin![/bold yellow]")
    else:
        console.print(f"[bold green]✅ Order for {customer} cancelled![/bold green]")


@app.command()
def print_orders(admin_password: str = typer.Argument(None)):
    """Print all orders. Optionally provide admin password to see order passwords."""
    orders = read_orders()
    if not orders:
        console.print("[bold red]No orders found.[/bold red]")
        return

    show_passwords = False
    if admin_password == ADMIN_PASSWORD:
        show_passwords = True
    elif admin_password is not None:
        console.print("[bold red]❌ Incorrect admin password! Showing orders without passwords.[/bold red]")

    table = Table(title="All Orders")
    table.add_column("Customer", style="cyan", no_wrap=True)
    table.add_column("Size", style="magenta")
    table.add_column("Order Time", style="green")
    if show_passwords:
        table.add_column("Password", style="yellow")

    for order in orders:
        if show_passwords:
            table.add_row(order['customer'], order['size'], order['order_time'], order['password'])
        else:
            table.add_row(order['customer'], order['size'], order['order_time'])

    console.print(table)


# ============================================================================

if __name__ == "__main__":
    app()
