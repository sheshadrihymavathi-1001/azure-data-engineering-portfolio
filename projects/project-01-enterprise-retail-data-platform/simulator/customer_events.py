"""Controlled customer INSERT/UPDATE/DELETE event simulator.

Implementation is maintained with the local Project 01 source-system code.
This file is intentionally tracked as part of the repository structure so
source-change scenarios are visible and testable.
"""

# TODO: add the validated local implementation.
from datetime import datetime

from config.database import get_connection


def create_customer(
    first_name,
    last_name,
    email,
    phone,
    city,
    state,
    country="India",
    customer_status="ACTIVE"
):
    """
    Simulate a new customer arriving in the source system.
    """

    now = datetime.now()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO dbo.customers
            (
                first_name,
                last_name,
                email,
                phone,
                city,
                state,
                country,
                customer_status,
                created_at,
                updated_at
            )
            OUTPUT INSERTED.customer_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            first_name,
            last_name,
            email,
            phone,
            city,
            state,
            country,
            customer_status,
            now,
            now
        )

        customer_id = cursor.fetchone()[0]

        conn.commit()

        print("Customer created successfully")
        print("Customer ID:", customer_id)
        print("Updated at:", now)

        return customer_id

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

def update_customer(customer_id, city, state):
    now = datetime.now()

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE dbo.customers
            SET city = ?,
                state = ?,
                updated_at = ?
            WHERE customer_id = ?
        """, city, state, now, customer_id)

        if cursor.rowcount == 0:
            raise ValueError(f"Customer {customer_id} not found")

        conn.commit()

        print("Customer updated successfully")
        print("Customer ID:", customer_id)
        print("New city:", city)
        print("New state:", state)
        print("Updated at:", now)

        return now

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

# def create_delete_test_customer():
#     return create_customer(
#         first_name="Delete",
#         last_name="Test",
#         email="delete.test@example.com",
#         phone="9876500030",
#         city="Chennai",
#         state="Tamil Nadu"
#     )

def delete_customer(customer_id):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM dbo.customers
            WHERE customer_id = ?
        """, customer_id)

        if cursor.rowcount == 0:
            raise ValueError(f"Customer {customer_id} not found")

        conn.commit()

        print("Customer deleted successfully")
        print("Customer ID:", customer_id)

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

# if __name__ == "__main__":

#     create_customer(
#         first_name="Priya",
#         last_name="Nair",
#         email="priya.failure.commit@example.com",
#         phone="9876500020",
#         city="Hyderabad",
#         state="Telangana"
#     )

# if __name__ == "__main__":
#     update_customer(
#         customer_id=20,
#         city="Bengaluru",
#         state="Karnataka"
#     )

# if __name__ == "__main__":
#     create_delete_test_customer()

# if __name__ == "__main__":
#     delete_customer(22)

# if __name__ == "__main__":
#     create_customer(
#         first_name="CDC",
#         last_name="Test",
#         email="cdc.test@example.com",
#         phone="9876500040",
#         city="Hyderabad",
#         state="Telangana"
#     )

# if __name__ == "__main__":
#     update_customer(
#         customer_id=23,
#         city="Bengaluru",
#         state="Karnataka"
#     )

# if __name__ == "__main__":
#     delete_customer(23)

# if __name__ == "__main__":
    # create_customer(
    #     first_name="CDC",
    #     last_name="Pipeline",
    #     email="cdc.pipeline@example.com",
    #     phone="9876500050",
    #     city="Hyderabad",
    #     state="Telangana"
    # )

#     update_customer(
#     customer_id=24,
#     city="Bengaluru",
#     state="Karnataka"
# )
#    delete_customer(24)

# if __name__ == "__main__":
#     create_customer(
#         first_name="Recovery",
#         last_name="Test",
#         email="recovery.test@example.com",
#         phone="9876500099",
#         city="Hyderabad",
#         state="Telangana"
#     )

# if __name__ == "__main__":
#     create_customer(
#         first_name="Idempotency",
#         last_name="Test",
#         email="idempotency.test@example.com",
#         phone="9876500026",
#         city="Hyderabad",
#         state="Telangana"
#     )

# if __name__ == "__main__":
#     create_customer(
#         first_name="Delete",
#         last_name="Replay",
#         email="delete.replay@example.com",
#         phone="9876500027",
#         city="Hyderabad",
#         state="Telangana"
#     )

if __name__ == "__main__":
    delete_customer(27)
