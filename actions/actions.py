import mysql.connector
from rasa_sdk import Action
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted
import logging
logger = logging.getLogger(__name__)


def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="lokesh123",
        database="restaurant_db"
    )

class ActionCheckIngredients(Action):
    def name(self):
        return "action_check_ingredients"

    def run(self, dispatcher, tracker, domain):
        food_item = tracker.get_slot('food_item')
        logger.info(f"Checking ingredients for {food_item}")
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute("SELECT ingredients, quantity_available FROM menu WHERE food_item = %s", (food_item,))
        result = cursor.fetchone()

        if result and result[1] > 0:
            ingredients = result[0]
            dispatcher.utter_message(text=f"The ingredients of {food_item} are {ingredients}.")
        else:
            dispatcher.utter_message(text=f"Sorry, {food_item} is out of stock. Would you like something else?")

        conn.close()
        return []
class ActionGenerateBill(Action):
    def name(self):
        return "action_generate_order_summary"

    def run(self, dispatcher, tracker, domain):
        # Get the slots (assuming 'food_item' is a single item and 'quantity' is an integer or text convertible to integer)
        food_item = tracker.get_slot('food_item')  # Single food item as text
        customer_name = tracker.get_slot('name')
        phone_number = tracker.get_slot('phone_number')
        quantity = tracker.get_slot('quantity')  # Assuming quantity is fetched from the slot

        # If no food item is provided, handle the error gracefully
        if not food_item:
            dispatcher.utter_message(text="Sorry, I couldn't find any food items in your order. Could you please specify the item?")
            return []

        conn = connect_to_db()
        cursor = conn.cursor()

        # Initialize total bill to 0
        total_bill = 0

        # Fetch the price of the single food item and calculate the total bill based on the quantity
        cursor.execute("SELECT price FROM menu WHERE food_item = %s", (food_item,))
        result = cursor.fetchone()
        if result:
            total_bill = result[0] * int(quantity)  # Multiply by the ordered quantity
        else:
            dispatcher.utter_message(text=f"Sorry, {food_item} is not available on the menu.")
            conn.close()
            return []

        # Insert order details into the 'orders' table
        cursor.execute("INSERT INTO orders (customer_name, phone_number, food_item, quantity, total_price) VALUES (%s, %s, %s, %s, %s)", 
                       (customer_name, phone_number, food_item, quantity, total_bill))

        # Notify the user about the total bill
        dispatcher.utter_message(text=f"Your total bill for {quantity} {food_item}(s) is {total_bill} units.")
        
        conn.commit()  # Commit changes to the database
        conn.close()

        # Set the 'bill' slot with the total bill amount
        return [SlotSet("bill", total_bill)]


class ActionSessionStart(Action):
    def name(self) -> str:
        return "action_session_start"

    async def run(self, dispatcher, tracker, domain):
        events = [SessionStarted(), ActionExecuted("action_listen")]
        dispatcher.utter_message(response="utter_greet")  # Only call the greeting once
        return events
