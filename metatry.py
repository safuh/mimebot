import MetaTrader5 as mt5

# Define your stop-loss and take-profit thresholds
STOP_LOSS_AMOUNT = -50.0  # Loss in monetary value
TAKE_PROFIT_AMOUNT = 100.0  # Profit in monetary value

def initialize_mt5():
    """Initialize connection to MetaTrader 5."""
    if not mt5.initialize():
        print("Failed to initialize MT5:", mt5.last_error())
        quit()
    print("MT5 initialized successfully")

def get_open_positions():
    """Fetch all open positions."""
    positions = mt5.positions_get()
    if positions is None:
        print("Failed to retrieve open positions:", mt5.last_error())
        return []
    return positions

def close_order(position):
    """Close an open order."""
    symbol = position.symbol
    ticket = position.ticket
    lot = position.volume
    action_type = mt5.ORDER_BUY if position.type == mt5.ORDER_SELL else mt5.ORDER_SELL

    # Get the current price for the symbol
    price = mt5.symbol_info_tick(symbol).ask if action_type == mt5.ORDER_SELL else mt5.symbol_info_tick(symbol).bid

    # Create a close request
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": action_type,
        "price": price,
        "deviation": 10,
        "magic": 123456,  # Optional: Use an identifier for the order
        "comment": "Closed by bot",
    }

    # Send the request
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to close order {ticket}:", result.retcode)
    else:
        print(f"Order {ticket} closed successfully")

def manage_positions():
    """Fetch open positions and close them based on stop-loss or take-profit conditions."""
    positions = get_open_positions()
    if not positions:
        print("No open positions to manage.")
        return

    for position in positions:
        ticket = position.ticket
        symbol = position.symbol
        entry_price = position.price_open
        volume = position.volume
        current_price = mt5.symbol_info_tick(symbol).bid if position.type == mt5.ORDER_BUY else mt5.symbol_info_tick(symbol).ask

        # Calculate unrealized profit or loss
        profit_loss = (current_price - entry_price) * volume if position.type == mt5.ORDER_BUY else (entry_price - current_price) * volume

        print(f"Ticket {ticket} | Symbol: {symbol} | PnL: {profit_loss}")

        # Check for stop-loss or take-profit conditions
        if profit_loss <= STOP_LOSS_AMOUNT:
            print(f"Closing ticket {ticket} due to stop-loss.")
            close_order(position)
        elif profit_loss >= TAKE_PROFIT_AMOUNT:
            print(f"Closing ticket {ticket} due to take-profit.")
            close_order(position)

if __name__ == "__main__":
    initialize_mt5()
    manage_positions()
    mt5.shutdown()



import brokerapi  # Replace with the actual API library for your broker.

# Initialize the broker API client
api = brokerapi.Client(
    api_key="your_api_key",
    api_secret="your_api_secret",
    base_url="https://api.broker.com"  # Replace with your broker's API base URL
)

# Define stop-loss and take-profit thresholds
STOP_LOSS_AMOUNT = -50.0  # Loss in monetary value or percentage
TAKE_PROFIT_AMOUNT = 100.0  # Profit in monetary value or percentage

def manage_positions():
    try:
        # Fetch open positions
        open_orders = api.get_open_positions()
        print("Open positions fetched:", open_orders)

        for order in open_orders:
            order_id = order['id']
            symbol = order['symbol']
            entry_price = float(order['entry_price'])
            quantity = float(order['quantity'])

            # Fetch current market price for the symbol
            current_price = float(api.get_current_price(symbol))
            print(f"Current price for {symbol}: {current_price}")

            # Calculate unrealized profit or loss
            profit_loss = (current_price - entry_price) * quantity
            print(f"Order ID: {order_id}, Profit/Loss: {profit_loss}")

            # Check stop-loss or take-profit conditions
            if profit_loss <= STOP_LOSS_AMOUNT:
                print(f"Closing order {order_id} due to stop-loss trigger.")
                api.close_order(order_id)
            elif profit_loss >= TAKE_PROFIT_AMOUNT:
                print(f"Closing order {order_id} due to take-profit trigger.")
                api.close_order(order_id)

    except Exception as e:
        print("Error managing positions:", str(e))

# Run the function
manage_positions()
