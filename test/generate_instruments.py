import json

def create_instrument_file():
    """
    Filters NSE data to create a Python module with F&O stock instrument keys.
    """
    # Step 1: Read the list of F&O trading symbols
    try:
        with open('nse_fo_stock_symbols.txt', 'r') as f:
            symbols_raw = f.read()
            # Clean and split the symbols, removing any empty strings
            fo_symbols = {s.strip().replace('"', '') for s in symbols_raw.split(',') if s.strip()}
            print(f"Loaded {len(fo_symbols)} F&O symbols.")
    except FileNotFoundError:
        print("Error: `nse_fo_stock_symbols.txt` not found.")
        return

    # Step 2: Load the main NSE instrument data
    try:
        with open('NSE.json', 'r') as f:
            all_instruments = json.load(f)
        print(f"Loaded {len(all_instruments)} total instruments from NSE.json.")
    except FileNotFoundError:
        print("Error: `NSE.json` not found.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode NSE.json.")
        return

    # Step 3: Filter for NSE_EQ stocks that are also in the F&O list
    instrument_list = []
    for inst in all_instruments:
        if (inst.get('segment') == 'NSE_EQ' and 
            inst.get('trading_symbol') in fo_symbols):
            instrument_list.append({
                "symbol": inst.get('trading_symbol'),
                "instrument_key": inst.get('instrument_key'),
                "name": inst.get('name'),
                "isin": inst.get('isin')
            })
    
    print(f"Found {len(instrument_list)} matching instruments.")

    # Step 4: Write the data to a new Python file
    try:
        with open('app/instruments.py', 'w') as f:
            f.write("# This file is auto-generated. Do not edit manually.\n\n")
            f.write("STOCKS_LIST = ")
            # Use json.dumps for pretty printing the list
            json.dump(instrument_list, f, indent=4)
            f.write("\n")
        print("Successfully created `app/instruments.py`")
    except IOError as e:
        print(f"Error writing to file: {e}")


if __name__ == "__main__":
    create_instrument_file() 