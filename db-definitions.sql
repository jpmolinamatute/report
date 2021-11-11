PRAGMA foreign_keys = ON;
PRAGMA optimize;
DROP VIEW IF EXISTS portfolio;
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
    name TEXT NOT NULL PRIMARY KEY
);

CREATE TABLE actions(
    id TEXT NOT NULL PRIMARY KEY,
    utc_date TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_id TEXT NOT NULL,
    coin TEXT NOT NULL,
    amount REAL NOT NULL,
    investment REAL NOT NULL DEFAULT 0.0,
    wallet TEXT NOT NULL,
    FOREIGN KEY(coin) REFERENCES coins(name),
    FOREIGN KEY(wallet) REFERENCES wallets(name)
    FOREIGN KEY(action_type) REFERENCES action_type(name)
);

CREATE VIEW portfolio AS
SELECT coin, ROUND(SUM(amount),8) AS amount, SUM(investment) AS investment
FROM actions
GROUP BY coin
HAVING ROUND(SUM(amount),8) > 0.00
ORDER BY coin;

INSERT INTO action_type(name)
VALUES
("ADJUSTMENT"), -- this will be used when we don't know why we get a given balance
("DEPOSIT"), -- Thit cancel out withdraw, this affect investment
("WITHDRAW"), -- Thit cancel out deposit, this affect investment
("FEE"), -- this should affect assets amount
("INTEREST"), -- this should affect assets amount
("SWAP"), -- this should affect assets amount
("TRANSFER_IN"), -- this should affect wallet balance
("TRANSFER_OUT"), -- this should affect wallet balance
("LOSSES"), -- Thit cancel out gains, this affect investment
("GAINS"); -- Thit cancel out losses, this affect investment

INSERT INTO coins(name)
VALUES
("ADA"),
("ATOM"),
("AXS"),
("BNB"),
("BTC"),
("BUSD"),
("DOGE"),
("DOT"),
("ETH"),
("LTC"),
("LUNA"),
("SLP"),
("SOL"),
("UNI"),
("USDT"),
("XMR"),
("XRP");

INSERT INTO wallets(name)
VALUES
("BINANCE"),
("TREZOR"),
("DAEDALUS"),
("PHANTOM");
