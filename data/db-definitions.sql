PRAGMA foreign_keys = ON;
PRAGMA optimize;
DROP VIEW IF EXISTS portfolio;
DROP VIEW IF EXISTS actual_investment;
DROP TABLE IF EXISTS actions;
DROP TABLE IF EXISTS coins;
DROP TABLE IF EXISTS wallets;
DROP TABLE IF EXISTS action_type;

CREATE TABLE action_type(
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE wallets (
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE coins(
    coin_token TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE actions(
    id TEXT NOT NULL PRIMARY KEY,
    utc_date TEXT NOT NULL,
    action_type TEXT NOT NULL,
    coin TEXT NOT NULL,
    amount REAL NOT NULL,
    investment REAL NOT NULL DEFAULT 0.0,
    wallet TEXT NOT NULL,
    FOREIGN KEY(coin) REFERENCES coins(coin_token),
    FOREIGN KEY(wallet) REFERENCES wallets(name),
    FOREIGN KEY(action_type) REFERENCES action_type(name)
);

CREATE VIEW portfolio AS
SELECT coin, ROUND(SUM(amount),8) AS amount, ROUND(SUM(investment), 3) AS investment
FROM actions
GROUP BY coin
HAVING ROUND(SUM(amount),8) > 0.00
ORDER BY coin;


CREATE VIEW actual_investment AS
SELECT ROUND(SUM(investment), 3) AS investment
FROM actions
WHERE action_type = "DEPOSIT"
ORDER BY utc_date;

INSERT INTO action_type(name)
VALUES
("ADJUSTMENT"), -- this will be used when we don't know why we get a given balance
("DEPOSIT"), -- Thit cancel out withdraw, this affect investment
("WITHDRAW"), -- Thit cancel out deposit, this affect investment
("FEE"), -- this should affect assets amount
("INTEREST"), -- this should affect ONLY assets amount
("MINING"), -- this should affect ONLY assets amount
("SWAP"), -- this should affect assets amount
("TRANSFER"), -- this should affect wallet balance
("LOSS"), -- Thit cancel out gains, this affect investment
("GAIN"); -- Thit cancel out losses, this affect investment

INSERT INTO coins(coin_token, name)
VALUES
("ADA", "Cardano"),
("ATOM", "Cosmos"),
("AXS", "Axie Infinity"),
("BNB", "Binance Coin"),
("BTC", "Bitcoin"),
("BUSD", "Binance USD"),
("DOGE", "Dogecoin"),
("DOT", "Polkadot"),
("ETH", "Ethereum"),
("LTC", "Litecoin"),
("LUNA", "Terra"),
("SLP", "Smooth Love Potion"),
("SOL", "Solana"),
("UNI", "Uniswap"),
("USDT", "Tether"),
("XMR", "Monero"),
("XRP", "XRP"),
("NA", "NA");

INSERT INTO wallets(name)
VALUES
("BINANCE"),
("TREZOR"),
("METAMASK"),
("YOROI"),
("PHANTOM");
