import os
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("SPORTYBET_USERNAME")
PASSWORD = os.getenv("SPORTYBET_PASSWORD")
DB_PATH = os.getenv("DB_PATH", "aviator.db")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"

# URLs
LOGIN_URL = "https://www.sportybet.com/ng/login"
GAME_URL = "https://www.sportybet.com/ng/sportygames/turbo-games/aviator"

# API endpoints
WALLET_API_URL = "https://www.sportybet.com/api/ng/pocket/v1/wallet/assetsInfo"
STATEMENTS_API_URL = "https://www.sportybet.com/api/ng/pocket/v1/statements"

# Selectors — SportyBet login page
USERNAME_INPUT_SEL = 'input[name="phone"]'
PASSWORD_INPUT_SEL = 'input[type="password"]'
SUBMIT_BUTTON_SEL = "button.af-button--primary"

# Selector — disconnect banner on main SportyBet shell
DISCONNECT_SEL = "app-disconnect-message .disconn-icon"

# Iframe chain (3 levels deep):
# Main page → iframe.turbo-games-iframe → iframe.d-block.border-0 → game UI
OUTER_IFRAME_SEL = "iframe.turbo-games-iframe"   # on the SportyBet shell page
INNER_IFRAME_SEL = "iframe.d-block.border-0"     # inside launch.spribegaming.com
IFRAME_SEL = "iframe.turbo-games-iframe"         # kept for collector (single hop)
MULTIPLIER_HISTORY_SEL = ""  # TODO: fill after DOM inspection — row of past round results

# Selectors inside the Spribe iframe
AUTO_TAB_SEL = "button.tab:text('Auto')"             # "Auto" tab by text
BET_INPUT_SEL = "div.bet-block input[inputmode='decimal']"
BET_BUTTON_SEL = "button.btn-success.bet"
AUTO_BET_SWITCHER_SEL = ".auto-bet .input-switch"
CASHOUT_BUTTON_SEL = ""                              # TODO: fill after DOM inspection
