import yfinance as yf


def get_audusd_rate():
    try:
        data = yf.download('AUDUSD=X', period="1d")
        audusd = data['Close'].iloc[-1,0]
    except:
        audusd = 0.7
    return audusd


if __name__ == '__main__':
    audusd = get_audusd_rate()