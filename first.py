import csv
import datetime
import uuid
import typer
from typing import Literal
print("hi")
app = typer.Typer()

ACCOUNTS_FILE = "accounts.csv"
ORDERS_FILE = "orders.csv"

ACCOUNT_FIELDS = ["username", "password", "status"]
ORDER_FIELDS = ["id", "username", "size", "order_time"]

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def read_csv(file: str) -> list[dict]:
    try:
        with open(file, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def write_csv(file: str, fields: list[str], rows: list[dict]) -> None:
    with open(file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def authenticate(username: str, password: str) -> dict:
    accounts = read_csv(ACCOUNTS_FILE)
    for acc in accounts:
        if acc["username"] == username and acc["password"] == password:
            return acc
    typer.echo("❌ Invalid credentials")
    raise typer.Exit()


# ------------------------------------------------------------------
# Account Commands
# ------------------------------------------------------------------

@app.command()
def create_account(username: str, password: str):
    """Create a USER account."""
    accounts = read_csv(ACCOUNTS_FILE)

    if any(a["username"] == username for a in accounts):
        typer.echo("❌ Username already exists")
        raise typer.Exit()

    accounts.append({
        "username": username,
        "password": password,
        "status": "USER",
    })

    write_csv(ACCOUNTS_FILE, ACCOUNT_FIELDS, accounts)
    typer.echo("✅ Account created")


@app.command()
def delete_account(
    username: str,
    password: str,
    target: str,
):
    """Delete an account (ADMIN only unless deleting self)."""
    user = authenticate(username, password)
    accounts = read_csv(ACCOUNTS_FILE)

    if target != username and user["status"] != "ADMIN":
        typer.echo("❌ Admin required to delete other accounts")
        raise typer.Exit()

    if target == username and user["status"] == "ADMIN":
        typer.echo("❌ Admins cannot delete themselves")
        raise typer.Exit()

    remaining = [a for a in accounts if a["username"] != target]

    if len(remaining) == len(accounts):
        typer.echo("❌ Account not found")
        raise typer.Exit()

    write_csv(ACCOUNTS_FILE, ACCOUNT_FIELDS, remaining)
    typer.echo(f"✅ Account '{target}' deleted")


@app.command()
def promote(
    admin_user: str,
    admin_pass: str,
    target: str,
):
    """Promote a USER to ADMIN (ADMIN only)."""
    admin = authenticate(admin_user, admin_pass)

    if admin["status"] != "ADMIN":
        typer.echo("❌ Admin privileges required")
        raise typer.Exit()

    if target == admin_user:
        typer.echo("❌ Cannot promote yourself")
        raise typer.Exit()

    accounts = read_csv(ACCOUNTS_FILE)

    for acc in accounts:
        if acc["username"] == target:
            if acc["status"] == "ADMIN":
                typer.echo("ℹ️ User already ADMIN")
                return
            acc["status"] = "ADMIN"
            write_csv(ACCOUNTS_FILE, ACCOUNT_FIELDS, accounts)
            typer.echo(f"✅ {target} promoted to ADMIN")
            return

    typer.echo("❌ User not found")


# ------------------------------------------------------------------
# Order Commands
# ------------------------------------------------------------------

@app.command()
def order(
    username: str,
    password: str,
    size: Literal["small", "medium", "large"] = "medium",
):
    """Place an order."""
    authenticate(username, password)

    orders = read_csv(ORDERS_FILE)
    orders.append({
        "id": str(uuid.uuid4())[:8],
        "username": username,
        "size": size,
        "order_time": datetime.datetime.now().strftime("%H:%M"),
    })

    write_csv(ORDERS_FILE, ORDER_FIELDS, orders)
    typer.echo("✅ Order placed")


@app.command()
def cancel(
    username: str,
    password: str,
):
    """Cancel one of your orders (explicit selection)."""
    user = authenticate(username, password)
    orders = read_csv(ORDERS_FILE)

    owned = [o for o in orders if o["username"] == username]

    if not owned:
        typer.echo("❌ No orders found")
        raise typer.Exit()

    typer.echo("Your orders:")
    for i, o in enumerate(owned, 1):
        typer.echo(f"{i}. {o['size']} at {o['order_time']} (ID {o['id']})")

    choice = typer.prompt("Select order number", type=int)

    if not (1 <= choice <= len(owned)):
        typer.echo("❌ Invalid selection")
        raise typer.Exit()

    target_id = owned[choice - 1]["id"]
    remaining = [o for o in orders if o["id"] != target_id]

    write_csv(ORDERS_FILE, ORDER_FIELDS, remaining)
    typer.echo("✅ Order cancelled")


@app.command()
def list_orders(username: str, password: str):
    """List orders (ADMIN sees all, USER sees own)."""
    user = authenticate(username, password)
    orders = read_csv(ORDERS_FILE)

    visible = orders if user["status"] == "ADMIN" else [
        o for o in orders if o["username"] == username
    ]

    if not visible:
        typer.echo("No orders found")
        return

    for o in visible:
        typer.echo(f"{o['username']} | {o['size']} | {o['order_time']} | {o['id']}")


# ------------------------------------------------------------------
# Entry
# ------------------------------------------------------------------

if __name__ == "__main__":
    app()
