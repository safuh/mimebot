import ccxt

api_key = 'I3EZLm4Qdo5ORcwQqAOY3y8HzcqnP4Qqr8aySxwunnbQO506WaadbFWb3woFwSxV'
api_secret = 'vUPKX7Hdx7CLuTwTdyYt1R2oUzpW7SebT9T8B4XKEd8noMcIjRT94DXSW2Jtjcy6'

exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True
})
#exchange.set_sandbox_mode(True)
