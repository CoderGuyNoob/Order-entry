import csv
import datetime
import time
from typing import Literal

import typer
from rich.progress import track

app = typer.Typer()

# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------

ACCOUNTS_FILE = "accounts.csv"
ORDERS_FILE = "orders.csv"

ACCOUNT_FIELDS = ["username", "password", "status"]
ORDER_FIELDS = ["username", "size", "order_time"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv(path: str) -> list[dict]:
    try:
        with open(path, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def write_csv(path: str, fields: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path: str, fields: list[str], row: dict) -> None:
    exists = bool(read_csv(path))
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def authenticate(username: str, password: str) -> dict:
    accounts = read_csv(ACCOUNTS_FILE)
    for acc in accounts:
        if acc["username"] == username and acc["password"] == password:
            return acc
    typer.echo("❌ Invalid username or password")
    raise typer.Exit()


# ---------------------------------------------------------------------------
# Account Commands
# ---------------------------------------------------------------------------

@app.command()
def create_account(
    username: str,
    password: str,
    status: Literal["USER", "ADMIN"] = "USER",
):
    """Create a new account."""
    accounts = read_csv(ACCOUNTS_FILE)

    if any(a["username"] == username for a in accounts):
        typer.echo("❌ Account already exists")
        raise typer.Exit()

    append_csv(
        ACCOUNTS_FILE,
        ACCOUNT_FIELDS,
        {"username": username, "password": password, "status": status},
    )
    typer.echo(f"✅ Account '{username}' created ({status})")


@app.command()
def delete_account(
    admin_user: str,
    admin_pass: str,
    username: str,
):
    """Delete an account (ADMIN only)."""
    admin = authenticate(admin_user, admin_pass)

    if admin["status"] != "ADMIN":
        typer.echo("❌ Admin privileges required")
        raise typer.Exit()

    accounts = read_csv(ACCOUNTS_FILE)
    accounts = [a for a in accounts if a["username"] != username]
    write_csv(ACCOUNTS_FILE, ACCOUNT_FIELDS, accounts)

    typer.echo(f"✅ Account '{username}' deleted")


# ---------------------------------------------------------------------------
# Order Commands
# ---------------------------------------------------------------------------

@app.command(no_args_is_help=True)
def order(
    username: str,
    password: str,
    size: Literal["small", "medium", "large"] = "medium",
):
    """Place an order."""
    authenticate(username, password)

    now = datetime.datetime.now().strftime("%H:%M")
    typer.echo(f"Placing order for {username}")

    for _ in track(range(100)):
        time.sleep(0.005)

    append_csv(
        ORDERS_FILE,
        ORDER_FIELDS,
        {"username": username, "size": size, "order_time": now},
    )

    typer.echo("✅ Order placed!")


@app.command()
def cancel(
    username: str,
    password: str,
):
    """Cancel one of your orders."""
    account = authenticate(username, password)
    orders = read_csv(ORDERS_FILE)

    user_orders = [(i, o) for i, o in enumerate(orders) if o["username"] == username]

    if not user_orders:
        typer.echo("❌ No orders found")
        raise typer.Exit()

    typer.echo("Your orders:")
    for i, (_, o) in enumerate(user_orders, start=1):
        typer.echo(f"{i}. {o['size']} @ {o['order_time']}")

    choice = typer.prompt("Which order to cancel", type=int)
    idx = user_orders[choice - 1][0]

    del orders[idx]
    write_csv(ORDERS_FILE, ORDER_FIELDS, orders)

    typer.echo("✅ Order cancelled")


@app.command()
def print_orders(username: str, password: str):
    """View orders (ADMIN sees all)."""
    account = authenticate(username, password)
    orders = read_csv(ORDERS_FILE)

    if account["status"] == "ADMIN":
        typer.echo("All orders:")
        for o in orders:
            typer.echo(f"{o['username']} | {o['size']} | {o['order_time']}")
    else:
        typer.echo("Your orders:")
        for o in orders:
            if o["username"] == username:
                typer.echo(f"{o['size']} | {o['order_time']}")


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
