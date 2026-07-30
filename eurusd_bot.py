from market_data import get_market_data


def main():
    print("EUR/USD trading analysis bot started")
    
    data = get_market_data(
        symbol="EUR/USD",
        interval="15min",
        outputsize=100
    )

    print(f"Symbol: {data['meta']['symbol']}")
    print(f"Interval: {data['meta']['interval']}")
    print("\nLatest candle:")
    print(data["values"][0])


if __name__ == "__main__":
    main()